"""Metadata and curated-strategy reports never assert unsupported gameplay."""
import unittest

from commander_sim.feature_tracking import printed_features, analyze_game_turns


CATALOG = {
    "Wizard A": {"type_line": "Creature — Human Wizard", "keywords": ["Flying"]},
    "Wizard B": {"type_line": "Creature — Wizard", "keywords": ["Flying"]},
    "Tutor": {"type_line": "Sorcery", "keywords": []},
    "Engine": {"type_line": "Artifact", "keywords": []},
    "Swamp": {"type_line": "Basic Land — Swamp", "keywords": []},
}
PROFILE = {
    "key_cards": [{"id": "engine", "card": "Engine", "role": "mana engine"}],
    "groups": [{"id": "wizards", "cards": ["Wizard A", "Wizard B"]}],
    "combos": [{"id": "engine_pair", "pieces": ["Wizard A", "Engine"]}],
}


def snapshot(turn, battlefield=(), hand=(), graveyard=(), **other):
    return {
        "source": "authoritative_game", "turn": turn,
        "battlefield": list(battlefield), "hand": list(hand),
        "graveyard": list(graveyard), **other,
    }


class FeatureTrackingTests(unittest.TestCase):
    def test_metadata_keywords_types_and_subtypes(self):
        r = printed_features(CATALOG, {"Wizard A": 1, "Wizard B": 2, "Swamp": 33}, PROFILE)
        self.assertEqual(r["counts"]["keyword"]["Flying"], 3)
        self.assertEqual(r["counts"]["subtype"]["Wizard"], 3)
        self.assertEqual(r["counts"]["type"]["land"], 33)
        self.assertEqual(r["curated_groups"]["wizards"], 3)
        self.assertIn("not playable abilities", r["limitations"])

    def test_rejects_nonexistent_curated_card_and_duplicate_id(self):
        bad = {"key_cards": [{"id": "a", "card": "Not Real"}]}
        with self.assertRaises(ValueError):
            printed_features(CATALOG, {}, bad)
        bad = {"key_cards": [{"id": "x", "card": "Engine"}],
               "groups": [{"id": "x", "cards": ["Wizard A"]}]}
        with self.assertRaises(ValueError):
            printed_features(CATALOG, {}, bad)

    def test_counts_actual_board_without_extrapolating_keywords(self):
        r = analyze_game_turns(CATALOG, PROFILE, [
            snapshot(1, battlefield=["Wizard A"], hand=["Engine"]),
            snapshot(2, battlefield=["Wizard A", "Wizard B"], hand=["Engine"]),
        ])
        self.assertEqual([x["groups_on_battlefield"]["wizards"] for x in r["turns"]], [1, 2])
        self.assertEqual(r["turns"][0]["combos"][0]["status"], "all_pieces_accessible_unverified")

    def test_combo_requires_engine_verification_not_proximity(self):
        state = snapshot(3, battlefield=["Wizard A", "Engine"])
        r = analyze_game_turns(CATALOG, PROFILE, [state])
        self.assertEqual(r["turns"][0]["combos"][0]["status"], "all_pieces_present_unverified")
        state["engine_verified_combos"] = ["engine_pair"]
        r = analyze_game_turns(CATALOG, PROFILE, [state])
        self.assertEqual(r["turns"][0]["combos"][0]["status"], "engine_verified_operational")

    def test_access_via_verified_tutor_is_distinct_from_in_hand(self):
        access = [{"tutor": "Tutor", "target": "Engine", "destination": "hand", "verified": True}]
        r = analyze_game_turns(CATALOG, PROFILE, [
            snapshot(1, battlefield=["Wizard A"], hand=["Tutor"], verified_tutor_access=access)])
        self.assertTrue(r["turns"][0]["key_cards"][0]["engine_verified_tutor_access"])
        self.assertEqual(r["turns"][0]["key_cards"][0]["hand"], 0)
        self.assertEqual(r["turns"][0]["combos"][0]["status"], "all_pieces_accessible_unverified")

    def test_unverified_tutor_access_rejected(self):
        with self.assertRaises(ValueError):
            analyze_game_turns(CATALOG, PROFILE, [
                snapshot(1, verified_tutor_access=[{"tutor": "Tutor", "target": "Engine",
                                                     "destination": "hand", "verified": False}])])

    def test_observation_is_not_invented_battlefield(self):
        row = snapshot(1)
        row["source"] = "observation"
        with self.assertRaises(ValueError):
            analyze_game_turns(CATALOG, PROFILE, [row])

    def test_rejects_wrong_card_or_missing_zone(self):
        row = snapshot(1, battlefield=["Unverified"])
        with self.assertRaises(ValueError):
            analyze_game_turns(CATALOG, PROFILE, [row])
        row = snapshot(1)
        del row["hand"]
        with self.assertRaises(ValueError):
            analyze_game_turns(CATALOG, PROFILE, [row])

    def test_rejects_duplicate_turns_and_unrecognized_operational_combo(self):
        with self.assertRaises(ValueError):
            analyze_game_turns(CATALOG, PROFILE, [snapshot(1), snapshot(1)])
        with self.assertRaises(ValueError):
            analyze_game_turns(CATALOG, PROFILE, [
                snapshot(1, engine_verified_combos=["unregistered"])])

    def test_fully_empty_curated_profile_is_allowed(self):
        r = analyze_game_turns(CATALOG, {}, [snapshot(1)])
        self.assertEqual(r["turns"][0]["key_cards"], [])
        self.assertEqual(r["turns"][0]["combos"], [])


if __name__ == "__main__":
    unittest.main()
