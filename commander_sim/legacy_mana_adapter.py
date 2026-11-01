"""Adapt reviewed six-color rock descriptors to the historical U/R/C planner.

The historic v9c-v35 engine already owns the mana ability planner and kernel.
This module only translates our canonical pinned, reviewed ManaMode records
into its Ability/Cost representation; it never creates mana or state itself.
No name-specific mana effects or privileged fallback are defined here.
"""
from .reviewed_rocks import ROCKS, reviewed_rock

HISTORICAL_UR = frozenset({"U", "R"})
HISTORICAL_PIPS = frozenset({"C", "U", "R"})


def reviewed_legacy_rock_modes(name, Ability, Cost, *,
                               commander_colors=HISTORICAL_UR):
    """Return old-planner Ability tuple, or None if not a reviewed rock.

    Construct exact review evidence from the pinned registration (not inferred
    from card type or Oracle text at runtime), then use one shared conversion.
    A new card needs a reviewed descriptor, not a provider.py special case.
    """
    registered = ROCKS.get(name)
    if registered is None:
        return None
    declaration = registered["review"]
    identity = {
        "oracle_id": declaration.oracle_id,
        "oracle_text": declaration.oracle_text,
        "layout": "normal",
        "type_line": "Artifact",
        "mana_cost": registered["printed_cost"],
    }
    template, _ = reviewed_rock(name, identity, commander_colors)
    abilities = []
    for mode in template.mana_modes:
        if not mode.tap or any(symbol not in HISTORICAL_PIPS
                               for symbol in mode.output + mode.activation_colors):
            # Historical U/R/C engine cannot silently gain black, green, or
            # white capabilities from a six-color template.
            raise NotImplementedError("Legacy mana provider lacks this mana mode")
        result = (mode.output.count("C"),
                  mode.output.count("U"),
                  mode.output.count("R"))
        cost = Cost(generic=mode.activation_generic,
                    blue=mode.activation_colors.count("U"),
                    red=mode.activation_colors.count("R"))
        abilities.append(Ability(result, cost, life=mode.life,
                                 damage=mode.damage,
                                 sacrifice=mode.sacrifice))
    return tuple(abilities)
