"""Conservative shared predicates over live kernel objects.

A positive match concerns only the requested characteristics. It is not a
claim that targeting or an object's unsupported abilities are implemented.
Missing characteristics and restrictions produce UNKNOWN, never a guess.
"""
from dataclasses import dataclass
from enum import Enum

class Match(Enum):
    YES = 'yes'
    NO = 'no'
    UNKNOWN = 'unknown'

@dataclass(frozen=True)
class ObjectView:
    object_id: int
    owner: int
    controller: int
    zone: str
    types: frozenset
    subtypes: frozenset
    colors: frozenset | None
    mana_value: int | float | None
    power: int | None
    toughness: int | None
    keywords: frozenset
    token: bool

    @classmethod
    def from_kernel(cls, kernel, object_id, *, mana_value=None, power_verified=False):
        obj = kernel.get(object_id)
        creature = 'creature' in obj.types and power_verified
        return cls(obj.object_id, obj.owner, obj.controller, obj.zone,
                   frozenset(obj.types), frozenset(kernel.subtypes(object_id)),
                   None if obj.card.colors is None else frozenset(obj.card.colors),
                   mana_value, obj.power if creature else None,
                   obj.toughness if creature else None, frozenset(obj.keywords), obj.token)

@dataclass(frozen=True)
class Query:
    zones: frozenset | None = None
    types_any: frozenset | None = None
    types_all: frozenset = frozenset()
    subtypes_all: frozenset = frozenset()
    color: str | None = None
    controller: int | None = None
    max_mana_value: int | None = None
    max_power: int | None = None
    token: bool | None = None

    def matches(self, view):
        if self.zones is not None and view.zone not in self.zones: return Match.NO
        if self.types_any is not None and not self.types_any & view.types: return Match.NO
        if not self.types_all <= view.types or not self.subtypes_all <= view.subtypes: return Match.NO
        if self.controller is not None and view.controller != self.controller: return Match.NO
        if self.token is not None and view.token != self.token: return Match.NO
        unknown = False
        for expected, actual, test in ((self.color, view.colors, lambda a,b:a in b),
                                       (self.max_mana_value, view.mana_value, lambda a,b:b <= a),
                                       (self.max_power, view.power, lambda a,b:b <= a)):
            if expected is not None:
                if actual is None: unknown = True
                elif not test(expected, actual): return Match.NO
        return Match.UNKNOWN if unknown else Match.YES

    def matches_kernel(self, kernel, object_id, *, mana_value=None, power_verified=False):
        """Evaluate only requested characteristics against the live kernel."""
        obj = kernel.get(object_id)
        if self.zones is not None and obj.zone not in self.zones: return Match.NO
        if self.types_any is not None and not self.types_any & obj.types: return Match.NO
        if not self.types_all <= obj.types: return Match.NO
        if self.subtypes_all and not self.subtypes_all <= kernel.subtypes(object_id): return Match.NO
        if self.controller is not None and obj.controller != self.controller: return Match.NO
        if self.token is not None and obj.token != self.token: return Match.NO
        unknown = False
        if self.color is not None:
            if obj.card.colors is None: unknown = True
            elif self.color not in obj.card.colors: return Match.NO
        if self.max_mana_value is not None:
            if mana_value is None: unknown = True
            elif mana_value > self.max_mana_value: return Match.NO
        if self.max_power is not None:
            if 'creature' not in obj.types or not power_verified: return Match.UNKNOWN
            if obj.power > self.max_power: return Match.NO
        return Match.UNKNOWN if unknown else Match.YES

def target_legality(view, *, source_controller, restrictions_complete=False):
    """Return only restriction-level status, not complete spell legality.

    A caller can assert completeness only after its rules/metadata layer has
    reviewed applicable restrictions. Ward/protection remain conditional.
    """
    keywords = {word.lower() for word in view.keywords}
    if 'shroud' in keywords or ('hexproof' in keywords and source_controller != view.controller):
        return Match.NO
    if any(word.startswith(('ward', 'protection', 'hexproof from')) for word in keywords):
        return Match.UNKNOWN
    return Match.YES if restrictions_complete else Match.UNKNOWN
