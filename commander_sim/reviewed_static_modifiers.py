"""Source-verified declarations for reusable continuously recomputed creature stats.

The effects are data on physical CardDefinitions; the kernel owns the query.
Only a bounded additive P/T subset is implemented (not all MTG layers).
"""
from dataclasses import dataclass

from .reviewed_token_spells import TokenBlueprint, create_reviewed_token_batches


@dataclass(frozen=True)
class StaticCreatureRule:
    oracle_id: str
    oracle_text: str
    mana_cost: str
    card_type: str
    scope: str
    subtype: str = ""
    color: str = ""
    power: int = 1
    toughness: int = 1
    entry_tokens: int = 0
    requires_choice: bool = False

    def __post_init__(self):
        if (self.scope not in {"all","controller"}
                or self.card_type not in {"Enchantment","Artifact"}
                or type(self.power) is not int or type(self.toughness) is not int
                or self.entry_tokens < 0
                or (self.requires_choice and self.subtype != "chosen")):
            raise ValueError("Invalid typed static creature effect")


RULES = {
    "Bad Moon": StaticCreatureRule(
        "fc5d3341-cbce-49e5-93cc-8add92479dca",
        "Black creatures get +1/+1.", "{1}{B}", "Enchantment", "all",
        color="B"),
    "Liliana's Mastery": StaticCreatureRule(
        "bd104c7e-311e-4b03-98d3-5f20f3a99d26",
        "Zombies you control get +1/+1.\nWhen this enchantment enters, create two 2/2 black Zombie creature tokens.",
        "{3}{B}{B}", "Enchantment", "controller",
        subtype="Zombie", entry_tokens=2),
    "Patchwork Banner": StaticCreatureRule(
        "4fb00dbe-1f82-4ba6-b18c-97e816d10d3a",
        "As this artifact enters, choose a creature type.\nCreatures you control of the chosen type get +1/+1.\n{T}: Add one mana of any color.",
        "{3}", "Artifact", "controller", subtype="chosen",
        requires_choice=True),
}


def reviewed_static_rule(name, raw):
    rule=RULES.get(name)
    return (rule if rule is not None and isinstance(raw,dict)
            and raw.get("oracle_id")==rule.oracle_id
            and raw.get("oracle_text")==rule.oracle_text
            and raw.get("mana_cost")==rule.mana_cost
            and raw.get("type_line")==rule.card_type else None)


def static_abilities(name, raw):
    """Declared reusable stat operation attached to original physical card."""
    rule=reviewed_static_rule(name,raw)
    if rule is None:return ()
    from .early_game_runner import _load_live_kernel
    # Import the current physical Ability definition, never a second ruleset.
    from pathlib import Path
    import sys
    root=Path(__file__).resolve().parents[1]
    legacy=str(root/"simulator"/"v7_rules")
    if legacy not in sys.path:sys.path.insert(0,legacy)
    from rules import Ability
    args=(("scope",rule.scope),("power",rule.power),
          ("toughness",rule.toughness))
    if rule.color:args+=(("color",rule.color),)
    if rule.subtype:args+=(("subtype",rule.subtype),)
    return (Ability(kind="static",op="creature_stat_modifier",args=args),)


def choose_creature_subtype(kernel, source_id, subtype):
    """Record an explicit as-enters choice on the same physical source ID."""
    source=kernel.get(source_id)
    if (source.zone!="battlefield" or
            not any(a.kind=="static" and a.op=="creature_stat_modifier"
                    and a.arg("subtype")=="chosen" for a in source.card.abilities)):
        raise ValueError("Physical chosen-type static source required")
    if not isinstance(subtype,str) or not subtype or not subtype.isalpha():
        raise ValueError("Explicit creature subtype required")
    if not hasattr(kernel,"static_choices"):
        kernel.static_choices={}
    kernel.static_choices[source_id]=subtype
    kernel._dirty()
    kernel.check_state_based()


def resolve_static_entry(zones, source_id, catalog):
    """Resolve the shared, source-verified token ETB when applicable."""
    source=zones.kernel.get(source_id)
    if source.zone!="battlefield":
        raise ValueError("Source must be in play")
    rule=reviewed_static_rule(source.card.name,catalog.get(source.card.name))
    if rule is None or source.card.card_id!=rule.oracle_id:
        raise ValueError("Missing verified static ETB rule")
    if not rule.entry_tokens:return ()
    blueprint=TokenBlueprint(
        "Zombie",frozenset({"creature"}),frozenset({"Zombie"}),
        frozenset({"B"}),2,2,rule.entry_tokens)
    result=create_reviewed_token_batches(zones,source.controller,(blueprint,))
    zones.kernel.check_state_based()
    return tuple(result)
