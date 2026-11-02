"""Reusable death-event predicates and ordered, typed trigger effect steps.

A trigger recipe is a data declaration, never permission to alter game state.
The host must observe actual kernel battlefield->graveyard moves with LKI,
source-pinned identity, paid costs, and bounded timing. Recognized import
phrases are intentionally narrow and omit ambiguous targets/replacements.
"""
from dataclasses import dataclass
import re

from .reviewed_token_spells import TokenBlueprint


@dataclass(frozen=True)
class DeathPredicate:
    relation: str = "any"  # self / own / opponent / any
    types_any: frozenset[str] = frozenset({"creature"})
    subtype: str = ""
    exclude_source: bool = False
    nontoken_only: bool = False

    def __post_init__(self):
        if (self.relation not in {"self", "own", "opponent", "any"}
                or not isinstance(self.types_any, frozenset)
                or not self.types_any
                or any(type(t) is not str or not t for t in self.types_any)
                or type(self.subtype) is not str
                or type(self.exclude_source) is not bool
                or type(self.nontoken_only) is not bool
                or (self.relation == "self" and self.exclude_source)):
            raise ValueError("Invalid death-trigger predicate")

    def matches(self, source, dead):
        if not bool(self.types_any.intersection(dead.types)):
            return False
        if self.subtype and self.subtype not in dead.subtypes:
            return False
        if self.nontoken_only and dead.token:
            return False
        if self.exclude_source and source.object_id == dead.object_id:
            return False
        if self.relation == "self":
            return source.object_id == dead.object_id
        if self.relation == "own":
            return source.controller == dead.controller
        if self.relation == "opponent":
            return source.controller != dead.controller
        return True


@dataclass(frozen=True)
class DeathEffectStep:
    kind: str
    count: int = 1
    token: TokenBlueprint | None = None

    def __post_init__(self):
        if (self.kind not in {"draw", "lose_life", "damage_self",
                              "gain_life", "opponents_lose", "token",
                              "counter_self"}
                or type(self.count) is not int or not 1 <= self.count <= 20
                or (self.kind == "token") != (self.token is not None)
                or (self.token is not None
                    and not isinstance(self.token, TokenBlueprint))):
            raise ValueError("Invalid ordered death effect step")


@dataclass(frozen=True)
class ProvisionalDeathRecipe:
    excerpt: str
    predicate: DeathPredicate
    steps: tuple[DeathEffectStep, ...]


# Exact complete triggered ability sentences only. Additional printed
# mandatory ETBs or alternative casting costs fail in provisional_profile.
# These patterns authorize physical movement-trigger effects only when the
# existing import fallback has already authorized the source's basic body.
_PROVISIONAL_PATTERNS = (
    (
        re.compile(r"Whenever a nontoken creature you control dies, "
                   r"this creature deals 1 damage to you and you draw a card\."),
        DeathPredicate("own", nontoken_only=True),
        (DeathEffectStep("damage_self"), DeathEffectStep("draw")),
    ),
    (
        re.compile(r"Whenever a nontoken creature you control dies, "
                   r"you draw a card and lose 1 life\."),
        DeathPredicate("own", nontoken_only=True),
        (DeathEffectStep("draw"), DeathEffectStep("lose_life")),
    ),
    (
        re.compile(r"Whenever another creature you control dies, "
                   r"each opponent loses 1 life\."),
        DeathPredicate("own", exclude_source=True),
        (DeathEffectStep("opponents_lose"),),
    ),
    (
        re.compile(r"Whenever a creature you control dies, "
                   r"each opponent loses 1 life\."),
        DeathPredicate("own"),
        (DeathEffectStep("opponents_lose"),),
    ),
    (
        re.compile(r"When this creature dies, (?:you may )?draw a card\."),
        DeathPredicate("self"),
        (DeathEffectStep("draw"),),
    ),
)


def provisional_death_recipe(oracle_text):
    """Recognize at most one standalone simple death trigger on a card.

    A source with two or more death-trigger-looking lines is ambiguous until
    reviewed, to avoid silently dropping required multi-trigger ordering.
    """
    if not isinstance(oracle_text, str):
        return None
    lines = [line.strip() for line in oracle_text.splitlines() if line.strip()]
    candidates = [line for line in lines
                  if re.search(r"\b(?:whenever|when)\b.*\bdies\b", line, re.I)]
    if len(candidates) != 1:
        return None
    line = candidates[0]
    for pattern, match, steps in _PROVISIONAL_PATTERNS:
        if pattern.fullmatch(line):
            return ProvisionalDeathRecipe(line, match, steps)
    return None
