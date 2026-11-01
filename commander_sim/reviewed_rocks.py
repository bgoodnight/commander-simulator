"""Oracle-pinned reviewed use of reusable mana-rock effect templates.

Only named, inspected cards get an effect here. Additional cards can use
the same defaults and small typed overrides without changing the planner.
Unmodeled sacrifice/draw side abilities and life/damage must not be silently
claimed as implemented. If printed text changes, review admission fails.
"""
from .effect_templates import ReviewedEffect, ManaMode, admit_reviewed_effect

ROCKS = {
    "Sol Ring": {
        "printed_cost": "{1}",
        "review": ReviewedEffect("6ad8011d-3471-4369-9d68-b264cc027487", "{T}: Add {C}{C}.",
            "rock_colorless_two",
            assumptions=("Mana ability modeled; other abilities if present are omitted",),
            ),
    },
    "Mind Stone": {
        "printed_cost": "{2}",
        "review": ReviewedEffect("c97361b5-af16-4a7b-af85-a429dbaf4ad2", "{T}: Add {C}.\n{1}, {T}, Sacrifice this artifact: Draw a card.",
            "rock_colorless_one",
            assumptions=("Mana ability modeled; other abilities if present are omitted",),
            ),
    },
    "Arcane Signet": {
        "printed_cost": "{2}",
        "review": ReviewedEffect("0bc7f093-bef0-4f1a-852c-4b75ebf54838", "{T}: Add one mana of any color in your commander's color identity.",
            "rock_commander_identity",
            assumptions=("Mana identity choices supplied by commander; other card functions omitted",),
            ),
    },
    "Charcoal Diamond": {
        "printed_cost": "{2}",
        "review": ReviewedEffect("1386d111-a2a7-4df1-91d7-947664126989", "This artifact enters tapped.\n{T}: Add {B}.",
            "rock_black_tapped",
            assumptions=("Entry tapped and black-mana activation modeled; no additional behavior",),
            ),
    },
    "Commander's Sphere": {
        "printed_cost": "{3}",
        "review": ReviewedEffect("0b67c4e2-f88b-4e01-85a1-9d5f5b8db13b", "{T}: Add one mana of any color in your commander's color identity.\nSacrifice this artifact: Draw a card.",
            "rock_commander_identity",
            assumptions=("Mana identity choices supplied by commander; other card functions omitted",),
            ),
    },
    "Izzet Signet": {
        "printed_cost": "{2}",
        "review": ReviewedEffect("2fda4fe7-8b0c-489c-a000-6d358e614e34", "{1}, {T}: Add {U}{R}.",
            "signet_ur",
            assumptions=("Generic activation funding required before U/R output",),
            ),
    },
    "Talisman of Creativity": {
        "printed_cost": "{2}",
        "review": ReviewedEffect("14d2979d-5728-42d7-a027-0eb1f754655d", "{T}: Add {C}.\n{T}: Add {U} or {R}. This artifact deals 1 damage to you.",
            "rock_colorless_one",
            assumptions=("Colorless and damaging colored modes modeled; no other effects",),
            ),
    },
}

def reviewed_rock(name, card, commander_colors):
    """Return (template, printed_cost) only for a pinned reviewed artifact."""
    row = ROCKS.get(name)
    if row is None or card.get("mana_cost") != row["printed_cost"]
            or "Artifact" not in card.get("type_line", "").split(" — ", 1)[0]:
        return None
    descriptor = row["review"]
    base = admit_reviewed_effect(card, descriptor)
    if name in ("Arcane Signet", "Commander\'s Sphere"):
        colors = tuple(sorted(set(commander_colors)))
        if not colors or any(c not in "WUBRG" for c in colors):
            raise ValueError("Commander color identity is required")
        descriptor = ReviewedEffect(descriptor.oracle_id, descriptor.oracle_text,
            descriptor.template, overrides=(("mana_modes",
                tuple(ManaMode((c,)) for c in colors)),),
            assumptions=descriptor.assumptions)
        base = admit_reviewed_effect(card, descriptor)
    if name == "Talisman of Creativity":
        descriptor = ReviewedEffect(descriptor.oracle_id, descriptor.oracle_text,
            descriptor.template, overrides=(("mana_modes",
                (ManaMode(("C",)), ManaMode(("U",), damage=1),
                 ManaMode(("R",), damage=1))),),
            assumptions=descriptor.assumptions)
        base = admit_reviewed_effect(card, descriptor)
    return base, row["printed_cost"]
