"""Verified tutor declarations composed from the same generic search default.

Exact Oracle/text is required. Only destination=hand tutor resolutions are
executable by the first narrow generic search action. Other destinations
and side effects require explicit host implementations.
"""
from .effect_templates import ReviewedEffect, admit_reviewed_effect

TUTORS = {
    "Fabricate": {
        "cost": "{2}{U}",
        "kind": "sorcery",
        "review": ReviewedEffect("422e1869-134f-463d-9fa1-86b66a998b3e", "Search your library for an artifact card, reveal it, put it into your hand, then shuffle.",
            "tutor_to_hand",
            overrides=(("search_types", frozenset(['artifact'])),
                ("reveal", True)),
            assumptions=("Pinned printed search restrictions checked; other abilities not inferred",)),
    },
    "Solve the Equation": {
        "cost": "{2}{U}",
        "kind": "sorcery",
        "review": ReviewedEffect("f02682f0-26c0-4032-9df3-273b6a45d0a8", "Search your library for an instant or sorcery card, reveal it, put it into your hand, then shuffle.",
            "tutor_to_hand",
            overrides=(("search_types", frozenset(['instant','sorcery'])),
                ("reveal", True)),
            assumptions=("Pinned printed search restrictions checked; other abilities not inferred",)),
    },
    "Merchant Scroll": {
        "cost": "{1}{U}",
        "kind": "sorcery",
        "review": ReviewedEffect("86cebe2a-95e7-4f22-99cc-e805aeaf347e", "Search your library for a blue instant card, reveal that card, put it into your hand, then shuffle.",
            "tutor_to_hand",
            overrides=(("search_types", frozenset(['instant'])),
                ("search_colors", frozenset(['U'])),
                ("reveal", True)),
            assumptions=("Pinned printed search restrictions checked; other abilities not inferred",)),
    },
    "Spellseeker": {
        "cost": "{2}{U}",
        "kind": "creature",
        "review": ReviewedEffect("47a785ed-8095-4685-8daa-02c4e2b0ffcd", "When this creature enters, you may search your library for an instant or sorcery card with mana value 2 or less, reveal it, put it into your hand, then shuffle.",
            "tutor_to_hand",
            overrides=(("search_types", frozenset(['instant','sorcery'])),
                ("max_mana_value", 2),
                ("reveal", True)),
            assumptions=("Pinned printed search restrictions checked; other abilities not inferred",)),
    },
    "Mystical Tutor": {
        "cost": "{U}",
        "kind": "instant",
        "review": ReviewedEffect("fb81f95c-70f8-4eb7-8d15-15d0ae23ec03", "Search your library for an instant or sorcery card, reveal it, then shuffle and put that card on top.",
            "tutor_to_hand",
            overrides=(("search_types", frozenset(['instant','sorcery'])),
                ("destination", "library_top"), ("reveal", True)),
            assumptions=("Pinned printed search restrictions checked; other abilities not inferred",)),
    },
}

def reviewed_tutor(name, card):
    row = TUTORS.get(name)
    if (row is None or card.get("mana_cost") != row["cost"]
            or row["kind"] not in card.get("type_line", "").split(" — ", 1)[0].lower().split()):
        return None
    return admit_reviewed_effect(card, row["review"]), row["cost"], row["kind"]
