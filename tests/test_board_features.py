"""Automatic printed-feature turn trends never invent keyword effects."""
import unittest

from commander_sim.board_features import analyze_authoritative_run, analyze_board_features

CATALOG = {
    "Wizard": {"type_line": "Creature — Human Wizard", "keywords": ["Flying"]},
    "Zombie": {"type_line": "Creature — Zombie", "keywords": []},
}


def state(turn, cards=(), tokens=()):
    return {"source": "authoritative_game", "turn": turn,
            "battlefield": list(cards), "hand": [], "graveyard": [],
            "untracked_tokens": [{"object_id": i + 100, "name": token}
                                 for i, token in enumerate(tokens)]}


class BoardFeaturesTests(unittest.TestCase):
    def test_printed_keyword_progress_through_real_states(self):
        result = analyze_board_features(CATALOG, [
            state(1), state(2, ["Wizard"]),
            state(3, ["Wizard", "Wizard", "Zombie"]),
        ])
        self.assertEqual([x["printed_features"]["keyword"].get("Flying", 0)
                          for x in result["turns"]], [0, 1, 2])
        self.assertEqual(result["turns"][2]["printed_features"]["subtype"]["Wizard"], 2)
        self.assertEqual(result["turns"][2]["printed_features"]["type"]["creature"], 3)

    def test_uncatalogued_token_is_not_inferred_keyword(self):
        result = analyze_board_features(CATALOG, [state(1, ["Wizard"], ["Zombie token"])])
        row = result["turns"][0]
        self.assertEqual(row["catalogued_battlefield_count"], 1)
        self.assertEqual(row["untracked_token_count"], 1)
        self.assertEqual(row["printed_features"]["keyword"]["Flying"], 1)
        self.assertIn("does not measure keyword effects", result["limitations"])

    def test_rejects_observation_and_unknown_nontoken(self):
        obs = state(1, ["Wizard"])
        obs["source"] = "observation"
        with self.assertRaises(ValueError):
            analyze_board_features(CATALOG, [obs])
        with self.assertRaises(ValueError):
            analyze_board_features(CATALOG, [state(1, ["Missing"])])

    def test_rejects_duplicate_turns_or_malformed_tokens(self):
        with self.assertRaises(ValueError):
            analyze_board_features(CATALOG, [state(1), state(1)])
        row = state(1)
        row["untracked_tokens"] = [{"name": "Token"}]
        with self.assertRaises(ValueError):
            analyze_board_features(CATALOG, [row])

    def test_combines_auto_and_curated_without_mutating_state(self):
        states = [state(1, ["Wizard"])]
        profile = {"key_cards": [{"id": "wizard", "card": "Wizard"}],
                   "groups": [{"id": "creature_group", "cards": ["Wizard", "Zombie"]}]}
        result = analyze_authoritative_run(CATALOG, profile, states)
        self.assertEqual(result["strategy"]["turns"][0]["key_cards"][0]["battlefield"], 1)
        self.assertEqual(result["strategy"]["turns"][0]["groups_on_battlefield"]["creature_group"], 1)
        self.assertEqual(result["automatic"]["turns"][0]["printed_features"]["keyword"]["Flying"], 1)
        self.assertEqual(states[0]["battlefield"], ["Wizard"])


if __name__ == "__main__":
    unittest.main()
