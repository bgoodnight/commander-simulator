"""Manually reviewed conditional creatures for the bounded M3 early-turn runner.

Reviewed here means: casting from HAND and entering normally has no immediately
mandatory unresolved effect under the *limited* no-combat,
no-opponent environment. Only independently pinned reviewed cast-trigger
abilities are available in the bounded runner; activated, combat, death,
ETB, and other triggered effects remain unsupported. This is NOT a blanket simplification of their full card
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


# Source-verified bodies with no mandatory unhandled immediate ETB effects.
# Later abilities remain bounded by their separately reviewed effect slots.
_ADDITIONAL_SAFE_BODIES = {
  "wretched_ranks": {
    "Graveborn Muse": {
      "oracle_id": "d2a65ff4-ab82-42f7-9d90-feb29132121e",
      "oracle_text": "At the beginning of your upkeep, you draw X cards and lose X life, where X is the number of Zombies you control."
    },
    "Headless Rider": {
      "oracle_id": "d4fdacd7-3101-44e2-a880-dde7326137a4",
      "oracle_text": "Whenever this creature or another nontoken Zombie you control dies, create a 2/2 black Zombie creature token."
    },
    "Vengeful Dead": {
      "oracle_id": "277c8ee9-0157-4e45-96ad-1b67716955ee",
      "oracle_text": "Whenever this creature or another Zombie dies, each opponent loses 1 life."
    },
    "Midnight Reaper": {
      "oracle_id": "e8c7566d-7cc0-48af-a986-83223ec7e06c",
      "oracle_text": "Whenever a nontoken creature you control dies, this creature deals 1 damage to you and you draw a card."
    }
  },
  "mortarion_current": {
    "Great Unclean One": {
      "oracle_id": "cd9031e4-9f6f-4dd8-908e-dcf7b79438e5",
      "oracle_text": "Reverberating Summons — At the beginning of your end step, each opponent loses 2 life. Then for each opponent who has less life than you, create a 1/3 black Demon creature token named Plaguebearer of Nurgle."
    },
    "Jadar, Ghoulcaller of Nephalia": {
      "oracle_id": "fb3defc0-c93a-4423-9ff9-c399f8a8ef1f",
      "oracle_text": "At the beginning of your end step, if you control no creatures with decayed, create a 2/2 black Zombie creature token with decayed. (It can't block. When it attacks, sacrifice it at end of combat.)"
    },
    "Morbid Opportunist": {
      "oracle_id": "322f44f0-e6da-4ee0-b474-e7d5e9a461c5",
      "oracle_text": "Whenever one or more other creatures die, draw a card. This ability triggers only once each turn."
    },
    "Pitiless Plunderer": {
      "oracle_id": "a784481f-eccb-4112-bb38-04a659319660",
      "oracle_text": "Whenever another creature you control dies, create a Treasure token. (It's an artifact with \"{T}, Sacrifice this token: Add one mana of any color.\")"
    },
    "Blood Artist": {
      "oracle_id": "310f141c-7f37-4729-aed6-dd9c09db448d",
      "oracle_text": "Whenever this creature or another creature dies, target player loses 1 life and you gain 1 life."
    },
    "Sangromancer": {
      "oracle_id": "920445ab-0ac2-4de7-bc1c-f5e58eb4424c",
      "oracle_text": "Flying\nWhenever a creature an opponent controls dies, you may gain 3 life.\nWhenever an opponent discards a card, you may gain 3 life."
    },
    "Yahenni, Undying Partisan": {
      "oracle_id": "fdba89eb-1cf5-46e6-9d09-1adb9bc40fcd",
      "oracle_text": "Haste\nWhenever a creature an opponent controls dies, put a +1/+1 counter on Yahenni.\nSacrifice another creature: Yahenni gains indestructible until end of turn."
    }
  },
  "mortarion_ideal": {
    "Great Unclean One": {
      "oracle_id": "cd9031e4-9f6f-4dd8-908e-dcf7b79438e5",
      "oracle_text": "Reverberating Summons — At the beginning of your end step, each opponent loses 2 life. Then for each opponent who has less life than you, create a 1/3 black Demon creature token named Plaguebearer of Nurgle."
    },
    "Tallyman of Nurgle": {
      "oracle_id": "7cc4a635-8730-4018-a8fd-b29fb5479928",
      "oracle_text": "Lifelink\nThe Seven-fold Chant — At the beginning of your end step, if a creature died this turn, you draw a card and you lose 1 life. If seven or more creatures died this turn, instead you draw seven cards and you lose 7 life."
    },
    "Ophiomancer": {
      "oracle_id": "55eca80c-dcd8-4c2f-aa0f-fb0aec7b80f7",
      "oracle_text": "At the beginning of each upkeep, if you control no Snakes, create a 1/1 black Snake creature token with deathtouch."
    },
    "Morbid Opportunist": {
      "oracle_id": "322f44f0-e6da-4ee0-b474-e7d5e9a461c5",
      "oracle_text": "Whenever one or more other creatures die, draw a card. This ability triggers only once each turn."
    },
    "Venomcrawler": {
      "oracle_id": "f3a07ae4-b0f8-43e6-adba-217f220cc2d0",
      "oracle_text": "Lifelink\nDevourer of Souls — Whenever another creature dies, put a +1/+1 counter on this creature."
    }
  }
}
for _deck, _reviews in _ADDITIONAL_SAFE_BODIES.items():
    REVIEWED_BY_DECK.setdefault(_deck, {}).update(_reviews)

def reviewed_creature(deck_key, name, source_card):
    approved = REVIEWED_BY_DECK.get(deck_key, {}).get(name)
    return bool(approved and source_card.get("layout") == "normal"
                and source_card.get("oracle_id") == approved["oracle_id"]
                and source_card.get("oracle_text") == approved["oracle_text"]
                and "Creature" in source_card.get("type_line", "").split(" — ", 1)[0])


LIMITATIONS = (
    "This bounded no-opponent runner imports all six pinned decks and plays "
    "reviewed land and source-paid mana-rock actions. Separately approved "
    "ordinary creatures, hand-cast instant/sorcery tutors with hand/library-top "
    "destinations, and hand-cast fixed token sorceries also resolve through "
    "the same physical zones. Four pinned cast-trigger source abilities "
    "(Young Pyromancer, Talrand, Archmage Emeritus, Storm-Kiln Artist) "
    "execute without opposing priority. Other cards or ability slots "
    "remain unsupported. Treasure/Clue activations, flashback, broad ETB/death "
    "triggers, sacrifice payoffs, full priority, multiplayer interaction, "
    "combat, replacement/continuous rules, commander casting and complete "
    "graveyard recursion remain unavailable. No validated win rates, "
    "full-deck performance or functional combo rankings may be inferred."
)
