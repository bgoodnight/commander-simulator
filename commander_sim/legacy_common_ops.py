"""Reusable typed operations for historical card effects.

Effects are data-only declarations; the existing table continues to own
zones, life, stack, priority, tokens and triggers. This module never creates
a second card registry or game state. Cards supply parameters, not handlers.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class DrawDiscard:
    draw: int
    discard: int = 0
    discard_kind: str = "discard"

    def __post_init__(self):
        if (type(self.draw) is not int or type(self.discard) is not int
                or self.draw < 0 or self.discard < 0
                or not isinstance(self.discard_kind, str) or not self.discard_kind):
            raise ValueError("Invalid draw/discard operation")


@dataclass(frozen=True)
class TokenBatch:
    count: int
    power: int
    toughness: int
    name: str
    definition: object = None

    def __post_init__(self):
        if (type(self.count) is not int or self.count < 0
                or type(self.power) is not int or type(self.toughness) is not int
                or not isinstance(self.name, str) or not self.name):
            raise ValueError("Invalid token batch")


@dataclass(frozen=True)
class GenericDiscount:
    amount: int
    printed_color: str
    source_name: str

    def __post_init__(self):
        if (type(self.amount) is not int or self.amount < 0
                or self.printed_color not in "WUBRG" or len(self.printed_color) != 1
                or not isinstance(self.source_name, str) or not self.source_name):
            raise ValueError("Invalid generic discount")


def apply_draw_discard(table, seat, effect: DrawDiscard, *, selection=None):
    """Draw and optional discard using existing player and selection services.

    Caller owns mandatory timing, discard choice legality and empty-library
    consequences. The existing player.draw()/selection.discard() enforce those.
    """
    if not isinstance(effect, DrawDiscard):
        raise TypeError("Expected DrawDiscard")
    player = table.players[seat]
    if effect.discard and selection is None:
        raise ValueError("Discard needs authoritative selection service")
    if effect.draw:
        player.draw(effect.draw)
    if effect.discard:
        selection.discard(seat, effect.discard, effect.discard_kind)


def apply_token_batch(table, seat, effect: TokenBatch):
    """Create physical tokens with existing add_creature, preserving order."""
    if not isinstance(effect, TokenBatch):
        raise TypeError("Expected TokenBatch")
    player = table.players[seat]
    return tuple(table.add_creature(player, effect.power, effect.toughness,
                                   effect.name, token=True,
                                   **({"definition": effect.definition}
                                      if effect.definition is not None else {}))
                 for _ in range(effect.count))


def apply_generic_discount(action, controlled, effect: GenericDiscount,
                           printed_colors):
    """Reduce only generic portion, preserve the action's existing colored floor.

    No mutation of objects or printed colors. The existing table still
    determines whose sources count, final action structure and timing.
    """
    if not isinstance(effect, GenericDiscount):
        raise TypeError("Expected GenericDiscount")
    if effect.printed_color not in printed_colors.get(action.source, ()):
        return action
    count = sum(o.card.name == effect.source_name for o in controlled)
    floor = action.parameters.get("U", 0) + action.parameters.get("R", 0)
    action.cost = max(floor, action.cost - count * effect.amount)
    return action


@dataclass(frozen=True)
class SacrificeRequirement:
    """Reusable validated source/victim restriction, not a sacrifice trigger."""
    source_types: frozenset[str]
    victim_types: frozenset[str]
    allow_token: bool = True
    tap_source: bool = False

    def __post_init__(self):
        if (not isinstance(self.source_types, frozenset) or not self.source_types
                or not isinstance(self.victim_types, frozenset) or not self.victim_types
                or any(not isinstance(t, str) or not t for t in
                       self.source_types | self.victim_types)
                or type(self.allow_token) is not bool or type(self.tap_source) is not bool):
            raise ValueError("Invalid reviewed sacrifice restriction")


def legal_sacrifice_victims(kernel, seat, source_id, requirement: SacrificeRequirement):
    """Return legal physical victims for any reviewed sacrifice source.

    This verifies object/controller/type/tap prerequisites, not game priority,
    replacement effects, costs, or 'can't be sacrificed' continuous effects.
    Those must be handled by the authoritative host before activation.
    """
    if not isinstance(requirement, SacrificeRequirement):
        raise TypeError("Expected SacrificeRequirement")
    source = kernel.objects.get(source_id)
    if (source is None or source.zone != "battlefield"
            or source.controller != seat
            or not requirement.source_types <= source.types
            or (requirement.tap_source and source.tapped)):
        return ()
    return tuple(obj.object_id for obj in kernel.on_battlefield()
                 if obj.object_id != source_id
                 and obj.controller == seat
                 and requirement.victim_types <= obj.types
                 and (requirement.allow_token or not obj.token))


def sacrifice_physical_object(table, seat, source_id, victim_id, requirement):
    """Commit a legal physical sacrifice via the existing world/zone owner."""
    if victim_id not in legal_sacrifice_victims(table.rules, seat, source_id, requirement):
        raise ValueError("Sacrifice object is not eligible")
    return table.world.move(victim_id, "graveyard", "sacrifice")
