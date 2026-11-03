"""Single read-only catalog of source-reviewed shared effect families.

Every Commander deck imports the same operation definitions. Named-card
registrations supply only pinned Oracle identity and typed effect parameters.
The original handler modules remain executors; the catalog must never infer
runtime permission from heuristics or card-name matches alone.

When adding a reusable mechanic, register the existing shared executor here
and bind reviewed cards to that executor in its source-owned module. No deck
specific registry and no duplicate mutable game state are introduced.
"""
from collections import defaultdict
from dataclasses import dataclass
from types import MappingProxyType

from .reviewed_rocks import ROCKS
from .reviewed_tutors import TUTORS
from .reviewed_token_spells import TOKEN_SPELLS
from .bounded_trigger_effects import REVIEWED_CAST_TRIGGERS
from .reviewed_death_effects import DEATH_RULES
from .reviewed_sacrifice_actions import SACRIFICE_MODES
from .reviewed_phase_effects import PHASE_RULES
from .reviewed_unearth import UNEARTH
from .reviewed_flashback import FLASHBACK
from .reviewed_enter_effects import ENTER_RULES
from .reviewed_cost_reduction import REDUCERS
from .reviewed_graveyard_creatures import GRAVEYARD_CREATURES
from .reviewed_nonhand_cast_triggers import NONHAND_CAST_TRIGGERS
from .reviewed_escape import BREACH_REVIEWS
from .reviewed_buyback import BUYBACK
from .reviewed_spell_copy import REVIEWED_COPY_SPELLS
from .reviewed_draw_spells import DRAW_SPELLS
from .reviewed_common_spells import RECIPES as COMMON_SPELLS
from .reviewed_removal_spells import RULES as REMOVAL_SPELLS
from .reviewed_lands import LANDS
from .reviewed_land_entry import RULES as LAND_ENTRIES
from .reviewed_zone_spells import RULES as ZONE_SPELLS
from .reviewed_graveyard_spells import RULES as GRAVEYARD_SPELLS
from .reviewed_attachments import RULES as ATTACHMENTS
from .reviewed_utility_activations import RULES as UTILITY_ACTIVATIONS
from .reviewed_activated_utilities import RULES as ACTIVATED_UTILITIES
from .reviewed_reactive_triggers import RULES as REACTIVE_TRIGGERS
from .reviewed_attack_triggers import RULES as ATTACK_TRIGGERS
from .reviewed_static_modifiers import RULES as STATIC_CREATURE_RULES
from .reviewed_creature_entry import RULES as CREATURE_ENTRY_RULES
from .reviewed_attack_tokens import RULES as ATTACK_TOKEN_RULES
from .reviewed_attack_mill import RULES as ATTACK_MILL_RULES
from .reviewed_attack_zones import RULES as ATTACK_ZONE_RULES
from .reviewed_artifact_departures import RULES as ARTIFACT_DEPARTURE_RULES
from .reviewed_combat_damage import RULES as COMBAT_DAMAGE_RULES


# These are effect families, not card classes or entire-card fidelity claims.
# Multiple cards from unrelated decks can register against one family.
EFFECT_FAMILIES = MappingProxyType({
    "mana_and_cost": frozenset({"mana","land_mana","cost_reduction","land_entry"}),
    "search_and_library": frozenset({"search","draw_spell","common_spell"}),
    "tokens_and_counters": frozenset({"fixed_token_spell","static_creature_modifier",
                                     "creature_entry_trigger","artifact_departure_trigger"}),
    "zone_and_graveyard": frozenset({"unearth","flashback","graveyard_creature_cast",
                                    "escape_grant","zone_spell","graveyard_spell"}),
    "cast_and_stack": frozenset({"cast_trigger","nonhand_cast_trigger","buyback",
                                "spell_copy","removal_spell"}),
    "triggers_and_timing": frozenset({"death_trigger","phase_trigger",
                                      "reactive_trigger","attack_trigger",
                                      "attack_token_trigger","attack_mill_trigger",
                                      "attack_zone_trigger","combat_damage_player_trigger",
                                      "enter_trigger"}),
    "activated_and_attachments": frozenset({"sacrifice_activation",
                                             "utility_activation","activated_utility",
                                             "attachment"}),
})


@dataclass(frozen=True)
class EffectRegistration:
    operation: str
    oracle_id: str
    name: str
    family: str


def registered_sources():
    """Return the existing reviewed source registries, as shared references.

    Do not materialize or execute a new copy of card logic. The source
    modules own the trusted printed-card bindings and the live handlers.
    """
    return (
            ("mana",ROCKS),
            ("search",TUTORS),
            ("fixed_token_spell",TOKEN_SPELLS),
            ("cast_trigger",REVIEWED_CAST_TRIGGERS),
            ("death_trigger",DEATH_RULES),
            ("sacrifice_activation",SACRIFICE_MODES),
            ("phase_trigger",PHASE_RULES),
            ("unearth",UNEARTH),
            ("flashback",FLASHBACK),
            ("enter_trigger",ENTER_RULES),
            ("cost_reduction",REDUCERS),
            ("graveyard_creature_cast",GRAVEYARD_CREATURES),
            ("nonhand_cast_trigger",NONHAND_CAST_TRIGGERS),
            ("escape_grant",BREACH_REVIEWS),
            ("buyback",BUYBACK),
            ("spell_copy",REVIEWED_COPY_SPELLS),
            # Maintain named audit parity with the physical turn driver's other
            # exact source-reviewed handlers. This is suboperation coverage only.
            ("draw_spell",DRAW_SPELLS),
            ("common_spell",COMMON_SPELLS),
            ("removal_spell",REMOVAL_SPELLS),
            ("land_mana",LANDS),
            ("land_entry",LAND_ENTRIES),
            ("zone_spell",ZONE_SPELLS),
            ("graveyard_spell",GRAVEYARD_SPELLS),
            ("attachment",ATTACHMENTS),
            ("utility_activation",UTILITY_ACTIVATIONS),
            ("activated_utility",ACTIVATED_UTILITIES),
            ("reactive_trigger",REACTIVE_TRIGGERS),
            ("attack_trigger",ATTACK_TRIGGERS),
            ("attack_token_trigger",ATTACK_TOKEN_RULES),
            ("attack_mill_trigger",ATTACK_MILL_RULES),
            ("attack_zone_trigger",ATTACK_ZONE_RULES),
            ("artifact_departure_trigger",ARTIFACT_DEPARTURE_RULES),
            ("combat_damage_player_trigger",COMBAT_DAMAGE_RULES),
            ("static_creature_modifier",STATIC_CREATURE_RULES),
            ("creature_entry_trigger",CREATURE_ENTRY_RULES),
    
    )


def _family_for(operation):
    matches=[family for family,kinds in EFFECT_FAMILIES.items()
             if operation in kinds]
    if len(matches)!=1:
        raise ValueError("Operation must belong to exactly one shared family: "+operation)
    return matches[0]


def effect_registrations():
    """Flatten pinned, reviewed suboperations without granting execution rights."""
    result=[]
    for kind,source in registered_sources():
        family=_family_for(kind)
        for name,row in source.items():
            if kind in {"mana","search"}:
                ids=(row["review"].oracle_id,)
            elif kind=="cast_trigger":
                ids=tuple(spec.card.oracle_id for spec in row)
            elif isinstance(row,tuple):
                ids=tuple(item.oracle_id for item in row)
            else:
                ids=(row.oracle_id,)
            for oracle_id in ids:
                if not isinstance(oracle_id,str) or not oracle_id:
                    raise ValueError("Reviewed operation has no pinned Oracle ID")
                result.append(EffectRegistration(kind,oracle_id,name,family))
    return tuple(result)


def named_registrations():
    """Compatibility view consumed by the existing six-deck coverage audit."""
    catalog=defaultdict(list)
    for item in effect_registrations():
        catalog[item.name].append((item.operation,item.oracle_id))
    return {name:tuple(records) for name,records in catalog.items()}


def operation_index():
    """Read-only index for import audits and operator discovery, never execution."""
    by_operation=defaultdict(list)
    for item in effect_registrations():
        by_operation[item.operation].append(item)
    return MappingProxyType({
        kind:tuple(records) for kind,records in sorted(by_operation.items())
    })
