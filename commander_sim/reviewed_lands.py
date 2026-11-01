"""Oracle-pinned reusable land mana/entry descriptors.

These are reviewed *partial* land abilities, independent of the deck. All
mana comes from existing physical land IDs through TemplateManaService.
Unknown ETB or activated slots are explicitly omitted, never invented.
"""
from dataclasses import dataclass
from .effect_templates import ManaMode

@dataclass(frozen=True)
class LandReview:
    oracle_id: str
    oracle_text: str
    mana_colors: tuple[str,...]
    entry: str="normal"   # normal, tapped, two_other_lands
    commander_identity: bool=False
    ignored: tuple[str,...]=()
    def __post_init__(self):
        if not self.oracle_id or not self.oracle_text or not self.mana_colors:
            raise ValueError("Incomplete reviewed land descriptor")
        if self.entry not in {"normal","tapped","two_other_lands"}:
            raise ValueError("Unreviewed land entry condition")
        if any(c not in "WUBRGC" for c in self.mana_colors):
            raise ValueError("Invalid land mana option")
    def modes(self,commander_colors):
        modes=tuple(c for c in "WUBRG" if c in commander_colors) if self.commander_identity else self.mana_colors
        return tuple(ManaMode((c,)) for c in modes)
    def enters_tapped(self,other_land_count):
        return self.entry=="tapped" or (
            self.entry=="two_other_lands" and other_land_count<2)

# Every admitted printing is pinned to its complete Oracle text. For Shivan
# Reef only the harmless C mode is exposed: damaging U/R modes require
# a separate damage-payment implementation.
LANDS={
    "Great Hall of the Biblioplex":LandReview(
        "a8c70dab-1e27-4a9c-bd2d-910d5720d02d",
        '{T}: Add {C}.\n{T}, Pay 1 life: Add one mana of any color. Spend this mana only to cast an instant or sorcery spell.\n{5}: If this land isn\'t a creature, it becomes a 2/4 Wizard creature with "Whenever you cast an instant or sorcery spell, this creature gets +1/+0 until end of turn." It\'s still a land.',
        ("C",),ignored=("Conditional life-paid mana and animation not implemented",)),
    "Hidden Grotto":LandReview(
        "382d18a2-438e-4ae7-a83f-1658ef1f9b07",
        "When this land enters, surveil 1. (Look at the top card of your library. You may put it into your graveyard.)\n{T}: Add {C}.\n{1}, {T}: Add one mana of any color.",
        ("C",),ignored=("Mandatory surveil 1 omitted","Funded any-color mana omitted")),
    "Path of Ancestry":LandReview(
        "b473e293-59e3-4e04-acf2-622604aeb25f",
        "This land enters tapped.\n{T}: Add one mana of any color in your commander's color identity. When that mana is spent to cast a creature spell that shares a creature type with your commander, scry 1. (Look at the top card of your library. You may put that card on the bottom.)",
        ("U",),entry="tapped",commander_identity=True,
        ignored=("Conditional scry trigger omitted",)),
    "Shivan Reef":LandReview(
        "0fe16212-66c3-4e45-a641-7391e9b2e304",
        "{T}: Add {C}.\n{T}: Add {U} or {R}. This land deals 1 damage to you.",
        ("C",),ignored=("U/R mana modes that deal damage are not activated",)),
    "Stormcarved Coast":LandReview(
        "4722105b-0085-4bb8-bca1-9de0d3eb5600",
        "This land enters tapped unless you control two or more other lands.\n{T}: Add {U} or {R}.",
        ("U","R"),entry="two_other_lands"),
    "Swiftwater Cliffs":LandReview(
        "2f4ad084-2062-44c0-9975-15f100204531",
        "This land enters tapped.\nWhen this land enters, you gain 1 life.\n{T}: Add {U} or {R}.",
        ("U","R"),entry="tapped",
        ignored=("Mandatory enters-the-battlefield 1 life gain omitted",)),
    "Tyrite Sanctum":LandReview(
        "38c83332-2d21-450c-ae97-34109b565f59",
        "{T}: Add {C}.\n{2}, {T}: Target legendary creature becomes a God in addition to its other types. Put a +1/+1 counter on it.\n{4}, {T}, Sacrifice this land: Put an indestructible counter on target God.",
        ("C",),ignored=("Activated God and indestructibility counters omitted",)),
}

def reviewed_land(name,raw,commander_colors):
    rule=LANDS.get(name)
    if (rule is None or not isinstance(raw,dict)
            or raw.get("oracle_id")!=rule.oracle_id
            or raw.get("oracle_text")!=rule.oracle_text
            or raw.get("layout")!="normal"
            or raw.get("type_line","").split(" — ",1)[0]!="Land"):
        return None
    if not rule.modes(commander_colors):
        return None
    return rule
