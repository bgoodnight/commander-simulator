"""Manually reviewed conditional creatures for the bounded M3 early-turn runner.

Reviewed here means: casting from HAND and entering normally has no immediately
mandatory unresolved effect under the *limited* creature/land-only no-combat,
no-opponent environment. Activated, combat and conditional triggered effects
remain unsupported. This is NOT a blanket simplification of their full card
rules. Oracle IDs and text are pinned to the inspected 2026-10-31 fixtures;
changes fail closed. No metadata-only card is automatically granted abilities.
"""

REVIEWED_BY_DECK = {
  "wretched_ranks": {
    "Cryptbreaker": {
      "oracle_id": "16f75a65-d067-4f79-81b9-833c373cf4d2",
      "oracle_text": "{1}{B}, {T}, Discard a card: Create a 2/2 black Zombie creature token.\nTap three untapped Zombies you control: You draw a card and lose 1 life."
    },
    "Carrion Feeder": {
      "oracle_id": "a1cc5e37-b09a-4b7f-afd5-77c1c35aa425",
      "oracle_text": "This creature can't block.\nSacrifice a creature: Put a +1/+1 counter on this creature."
    },
    "Undead Augur": {
      "oracle_id": "c26887e1-27f4-4550-921b-53460e43c079",
      "oracle_text": "Whenever this creature or another Zombie you control dies, you draw a card and lose 1 life."
    },
    "Midnight Reaper": {
      "oracle_id": "e8c7566d-7cc0-48af-a986-83223ec7e06c",
      "oracle_text": "Whenever a nontoken creature you control dies, this creature deals 1 damage to you and you draw a card."
    },
    "Headless Rider": {
      "oracle_id": "d4fdacd7-3101-44e2-a880-dde7326137a4",
      "oracle_text": "Whenever this creature or another nontoken Zombie you control dies, create a 2/2 black Zombie creature token."
    },
    "Vengeful Dead": {
      "oracle_id": "277c8ee9-0157-4e45-96ad-1b67716955ee",
      "oracle_text": "Whenever this creature or another Zombie dies, each opponent loses 1 life."
    },
    "Liliana's Reaver": {
      "oracle_id": "97332d4e-a55c-4e4f-9040-bf426a7c8e39",
      "oracle_text": "Deathtouch\nWhenever this creature deals combat damage to a player, that player discards a card and you create a tapped 2/2 black Zombie creature token."
    },
    "Gravecrawler": {
      "oracle_id": "09ff28b1-b6c9-48e6-b12e-2f0e644f709f",
      "oracle_text": "This creature can't block.\nYou may cast this card from your graveyard as long as you control a Zombie."
    }
  },
  "magnus_premium": {
    "Young Pyromancer": {
      "oracle_id": "5fac139a-07d3-4e6c-98e3-d98b199f7a6f",
      "oracle_text": "Whenever you cast an instant or sorcery spell, create a 1/1 red Elemental creature token."
    },
    "Talrand, Sky Summoner": {
      "oracle_id": "ea1eb902-a23c-44ff-9169-19baf71de238",
      "oracle_text": "Whenever you cast an instant or sorcery spell, create a 2/2 blue Drake creature token with flying."
    },
    "Archmage Emeritus": {
      "oracle_id": "8305d576-21d8-4ce7-8eda-a7cd9793aca5",
      "oracle_text": "Magecraft — Whenever you cast or copy an instant or sorcery spell, draw a card."
    },
    "Baral, Chief of Compliance": {
      "oracle_id": "baf80db7-2ca8-4bfc-b5b6-25ed51878dd7",
      "oracle_text": "Instant and sorcery spells you cast cost {1} less to cast.\nWhenever a spell or ability you control counters a spell, you may draw a card. If you do, discard a card."
    }
  },
  "magnus_budget": {
    "Young Pyromancer": {
      "oracle_id": "5fac139a-07d3-4e6c-98e3-d98b199f7a6f",
      "oracle_text": "Whenever you cast an instant or sorcery spell, create a 1/1 red Elemental creature token."
    },
    "Talrand, Sky Summoner": {
      "oracle_id": "ea1eb902-a23c-44ff-9169-19baf71de238",
      "oracle_text": "Whenever you cast an instant or sorcery spell, create a 2/2 blue Drake creature token with flying."
    },
    "Archmage Emeritus": {
      "oracle_id": "8305d576-21d8-4ce7-8eda-a7cd9793aca5",
      "oracle_text": "Magecraft — Whenever you cast or copy an instant or sorcery spell, draw a card."
    },
    "Baral, Chief of Compliance": {
      "oracle_id": "baf80db7-2ca8-4bfc-b5b6-25ed51878dd7",
      "oracle_text": "Instant and sorcery spells you cast cost {1} less to cast.\nWhenever a spell or ability you control counters a spell, you may draw a card. If you do, discard a card."
    }
  }
}


def reviewed_creature(deck_key, name, source_card):
    approved = REVIEWED_BY_DECK.get(deck_key, {}).get(name)
    return bool(approved and source_card.get("layout") == "normal"
                and source_card.get("oracle_id") == approved["oracle_id"]
                and source_card.get("oracle_text") == approved["oracle_text"]
                and "Creature" in source_card.get("type_line", "").split(" — ", 1)[0])


LIMITATIONS = (
    "This bounded runner permits supported land plays and approved source-paid "
    "creature and mana-rock casts from hand. Reviewed rock mana abilities include "
    "Sol Ring two-colorless output, basic colored rocks and funded Signet modes. "
    "Colored damage/life-paying modes, activated draw/sacrifice side abilities, "
    "other ramp, tutor spells, combat, opponents, death/cast/ETB triggers, "
    "priority and commander casting remain unmodeled. No full deck power, "
    "win rates or functional combo accessibility may be inferred."
)
