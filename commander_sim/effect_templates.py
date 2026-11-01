"""Reusable, explicitly reviewed effect templates for broad deck simulation.

These are typed *descriptions*, not a separate game engine. A card maps to a
template plus overrides; the existing kernel owns zones, sources and payment.
Unknown cards never acquire behavior from an inferred role or string match.
Use Mode.HYBRID and a review record before accepting simplified behavior.
"""
from dataclasses import dataclass, replace
from typing import Mapping


MANA_COLORS = frozenset("WUBRGC")
SEARCH_KINDS = frozenset({"any", "creature", "artifact", "enchantment",
                          "instant", "sorcery", "land"})
DESTINATIONS = frozenset({"hand", "battlefield", "graveyard", "library_top"})
TEMPLATE_KINDS = frozenset({"mana_source", "library_search"})


@dataclass(frozen=True)
class ManaMode:
    """One ability activation, output pips, and optional funding/side costs.

    Example Sol Ring: output=('C','C'). A Signet needs activation_generic=1,
    and cannot fund itself. Life/damage/tap/sacrifice have different semantics.
    A template does not itself authorize activation or add mana.
    """
    output: tuple[str, ...]
    activation_generic: int = 0
    activation_colors: tuple[str, ...] = ()
    tap: bool = True
    sacrifice: bool = False
    life: int = 0
    damage: int = 0

    def __post_init__(self):
        if not isinstance(self.output, tuple) or not self.output:
            raise ValueError("Mana mode must produce one or more pips")
        for symbol in self.output + self.activation_colors:
            if type(symbol) is not str or len(symbol) != 1 or symbol not in MANA_COLORS:
                raise ValueError("Invalid mana pip")
        if any(type(x) is not int or x < 0 for x in
               (self.activation_generic, self.life, self.damage)):
            raise ValueError("Invalid mana activation cost")
        if type(self.tap) is not bool or type(self.sacrifice) is not bool:
            raise ValueError("Invalid activation flag")


@dataclass(frozen=True)
class EffectTemplate:
    """Card-independent default effect. Variations override named fields."""
    kind: str
    mana_modes: tuple[ManaMode, ...] = ()
    search_types: frozenset[str] = frozenset()
    max_mana_value: int | None = None
    destination: str = "hand"
    enter_tapped: bool = False
    reveal: bool = False
    shuffle: bool = False

    def __post_init__(self):
        if self.kind not in TEMPLATE_KINDS:
            raise ValueError("Unsupported generic effect")
        if type(self.enter_tapped) is not bool or type(self.reveal) is not bool or type(self.shuffle) is not bool:
            raise ValueError("Invalid template flag")
        if self.kind == "mana_source":
            if not self.mana_modes or not all(isinstance(x, ManaMode) for x in self.mana_modes):
                raise ValueError("Mana source needs typed activation modes")
            if self.search_types or self.max_mana_value is not None:
                raise ValueError("Mana source cannot also search")
        else:
            if self.mana_modes or not self.search_types or not self.search_types <= SEARCH_KINDS:
                raise ValueError("Search requires reviewed card types")
            if self.destination not in DESTINATIONS:
                raise ValueError("Unknown tutor destination")
            if self.max_mana_value is not None and (type(self.max_mana_value) is not int or self.max_mana_value < 0):
                raise ValueError("Invalid tutor mana-value threshold")


@dataclass(frozen=True)
class ReviewedEffect:
    """Exact Oracle+text tied to an explicitly reviewed effect composition."""
    oracle_id: str
    oracle_text: str
    template: str
    overrides: tuple[tuple[str, object], ...] = ()
    fidelity: str = "simplified"
    assumptions: tuple[str, ...] = ()
    ignored_abilities: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.oracle_id or not isinstance(self.oracle_text, str) or not self.oracle_text:
            raise ValueError("Missing pinned printed identity/text")
        if self.fidelity not in {"exact", "simplified"}:
            raise ValueError("Unknown fidelity")
        if self.fidelity == "simplified" and not self.assumptions:
            raise ValueError("Simplified card template needs explicit assumptions")
        if len(dict(self.overrides)) != len(self.overrides):
            raise ValueError("Duplicate override fields")


TEMPLATES = {
    "rock_colorless_one": EffectTemplate("mana_source", (ManaMode(("C",)),)),
    "rock_colorless_two": EffectTemplate("mana_source", (ManaMode(("C", "C")),)),
    "rock_commander_identity": EffectTemplate("mana_source", (ManaMode(("W",)),)),
    "rock_black_tapped": EffectTemplate("mana_source", (ManaMode(("B",)),), enter_tapped=True),
    "signet_ur": EffectTemplate("mana_source", (ManaMode(("U", "R"), activation_generic=1),)),
    "tutor_to_hand": EffectTemplate("library_search", search_types=frozenset({"any"}),
                                    destination="hand", shuffle=True),
}


def compose_effect(review: ReviewedEffect, *, templates=TEMPLATES):
    """Validate and apply only typed dataclass field overrides.

    Overrides contain full replacement fields (including mana_modes), not
    executable conditions or arbitrary callbacks. Reviewed source and
    conditions must be checked again against pinned Oracle text at admission.
    """
    if not isinstance(review, ReviewedEffect):
        raise TypeError("Expected reviewed effect")
    if review.template not in templates:
        raise ValueError("Unknown effect template")
    base = templates[review.template]
    permitted = ({"mana_modes", "enter_tapped"} if base.kind == "mana_source"
                 else {"search_types", "max_mana_value", "destination", "reveal", "shuffle"})
    overrides = dict(review.overrides)
    if not overrides.keys() <= permitted:
        raise ValueError("Invalid override for this effect category")
    return replace(base, **overrides)


def admit_reviewed_effect(card: Mapping, review: ReviewedEffect):
    """No speculative automatic parsing from Oracle text or familiar name."""
    if not isinstance(card, Mapping) or not isinstance(review, ReviewedEffect):
        raise TypeError("Expected pinned printed card and reviewed descriptor")
    if card.get("oracle_id") != review.oracle_id or card.get("oracle_text") != review.oracle_text:
        raise ValueError("Pinned Oracle identity/text no longer matches review")
    if card.get("layout") != "normal":
        raise ValueError("Unreviewed multi-face effect")
    return compose_effect(review)


def tutor_matches(template: EffectTemplate, identity: Mapping):
    """Conservative metadata predicate, NOT a cast, tutor activation or search."""
    if template.kind != "library_search":
        raise ValueError("Not a search template")
    if not isinstance(identity, Mapping) or not isinstance(identity.get("type_line"), str):
        return False
    if "any" not in template.search_types:
        head = identity["type_line"].split(" — ", 1)[0].lower().split()
        if not any(kind in head for kind in template.search_types):
            return False
    if template.max_mana_value is not None:
        mv = identity.get("cmc")
        if type(mv) not in (int, float) or mv > template.max_mana_value:
            return False
    return True
