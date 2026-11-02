"""Replay v1 contracts ensure abbreviated stress data never becomes invented game state."""
import unittest
from tools.build_opponent_replay import convert, FORMAT


def sample():
    scenarios = {}
    for name in ("balanced", "aggressive", "control", "combo", "goldfish"):
        scenarios[name] = {
            "summary": {"seeds": 24, "survived_by_horizon": 24,
                        "eliminated_by_horizon": 0},
            "narratives": [{
                "seed": 0, "scenario": None if name == "goldfish" else name,
                "seat_roles": {} if name == "goldfish" else
                              {"1": "aggro", "2": "control", "3": "value"},
                "eliminated": False,
                "turns": [
                    {"turn": 1, "life": 40, "lands": 1, "creatures": 0,
                     "hand_size": 7, "events": [
                         {"type": "land_play", "card": "Swamp"},
                         {"type": "opponent_abstract_unblocked_damage",
                          "seat": 1, "target_seat": 0, "amount": 2},
                         {"type": "opponent_life_zero", "seat": 3, "target_seat": None}]},
                    {"turn": 2, "life": 38, "lands": 1, "creatures": 0,
                     "hand_size": 6, "events": []},
                ],
            }]
        }
    return {"deck": "mortarion_physical_final", "turn_horizon": 10,
            "seeds_per_scenario": 24, "scenarios": scenarios,
            "warning": "Only abstract pressure; not full games",
            "review_flags": []}


class ReplayExportTests(unittest.TestCase):
    def convert(self, data):
        return convert(data, source_run=41444353902,
                       engine_commit="a" * 40, deck_sha256="b" * 64)

    def test_export_preserves_order_and_raw_event_fields(self):
        result = self.convert(sample())
        self.assertEqual(result["format"], FORMAT)
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["fidelity"]["opponent_battlefield_snapshots"], False)
        self.assertEqual(result["fidelity"]["individual_card_draws"], False)
        game = result["scenarios"]["balanced"]["games"][0]
        self.assertEqual(len(game["seats"]), 4)
        turn = game["rounds"][0]
        self.assertEqual(set(turn["snapshots"]), {"0"})
        self.assertEqual([e["type"] for e in turn["actions"]],
                         ["land_play", "opponent_abstract_unblocked_damage",
                          "opponent_life_zero"])
        self.assertEqual(turn["actions"][1]["fields"]["amount"], 2)
        self.assertEqual(turn["actions"][1]["actor_seat"], 1)
        self.assertEqual(turn["actions"][2]["actor_seat"], None)
        self.assertEqual(turn["actions"][2]["affected_seat"], 3)
        self.assertEqual(len(result["scenarios"]["goldfish"]["games"][0]["seats"]), 1)

    def test_no_inferred_opponent_life_or_zone_changes(self):
        result = self.convert(sample())
        round2 = result["scenarios"]["balanced"]["games"][0]["rounds"][1]
        self.assertEqual(round2["snapshots"]["0"]["life"], 38)
        self.assertFalse(round2["actions"])
        self.assertNotIn("1", round2["snapshots"])
        self.assertNotIn("graveyard", round2)
        self.assertNotIn("draws", round2)

    def test_rejects_wrong_deck_scenario_and_duplicate_seeds(self):
        bad = sample()
        bad["deck"] = "mortarion_current"
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            self.convert(bad)
        bad = sample()
        bad["scenarios"]["balanced"]["narratives"][0]["scenario"] = "combo"
        with self.assertRaisesRegex(ValueError, "Narrative"):
            self.convert(bad)
        bad = sample()
        bad["scenarios"]["balanced"]["narratives"] *= 2
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.convert(bad)


if __name__ == "__main__":
    unittest.main()
