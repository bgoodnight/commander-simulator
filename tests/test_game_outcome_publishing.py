"""Offline publisher: accepted cohort, revision, checksum and stale-data gates."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.publish_game_outcomes import (
    publish, validate_library, validate_batch, PUBLIC_FORMAT,
)


SHA = "a" * 64
COMMIT = "b" * 40
DECK_HASHES = {"mortarion_current": SHA, "necron_dynasties": "c" * 64}


def example_batch(*, deck="mortarion_current", scenario="mixed", seeds=(0, 1),
                  mode="safe", style="adaptive", revision=None):
    rows = []
    for seed in seeds:
        end = [39, 38, 37, 36] if seed % 2 else [40, 35, 35, 35]
        rows.append({
            "seed": seed,
            "opponent_roles": {"1": "aggro", "2": "control", "3": "value"},
            "completed_rounds": 1,
            "outcome": {
                "status": "unresolved", "reason": "round_limit",
                "complete": False, "winner_seat": None,
                "requested_rounds": 1, "completed_rounds": 1,
            },
            "life_history": [
                {"round": 0, "life_totals": dict(zip("0123", [40]*4)),
                 "alive_seats": [0, 1, 2, 3],
                 "life_changes": [], "new_eliminations": []},
                {"round": 1, "life_totals": dict(zip("0123", end)),
                 "alive_seats": [0, 1, 2, 3],
                 "life_changes": [], "new_eliminations": []},
            ],
        })
    return {
        "format": "commander-modeled-outcomes-v1", "schema_version": 1,
        "deck_key": deck, "deck_sha256": revision or DECK_HASHES[deck],
        "scenario": scenario, "requested_rounds": 1,
        "seed_count": len(rows), "pilot_style": style,
        "provisional_mode": mode,
        "opponent_fidelity": "abstract_opponent_pressure_not_card_exact",
        "outcomes_are_competitive_win_rates": False,
        "summary": {
            "total_games": len(rows),
            "outcome_counts": {"win": 0, "loss": 0, "draw": 0,
                               "unresolved": len(rows), "not_evaluated": 0},
        },
        "runs": rows, "example_replays": [],
    }


class OutcomePublicationTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name)
        self.source = self.path / "incoming"
        self.source.mkdir()
        self.output = self.path / "public"

    def write(self, name, batch):
        (self.source / name).write_text(json.dumps(batch), encoding="utf-8")

    def test_many_scenarios_and_decks_get_one_index_with_lazy_deck_lookup(self):
        self.write("x.json", example_batch())
        self.write("y.json", example_batch(scenario="control"))
        self.write("z.json", example_batch(deck="necron_dynasties"))
        index = publish(self.source, self.output,
                        engine_commit=COMMIT, deck_hashes=DECK_HASHES)
        self.assertEqual(index["format"], PUBLIC_FORMAT)
        self.assertEqual(index["engine_commit"], COMMIT)
        self.assertEqual(len(index["files"]), 3)
        self.assertEqual(set(index["by_deck"]),
                         {"mortarion_current", "necron_dynasties"})
        self.assertEqual(sum(map(len, index["by_deck"].values())), 3)
        self.assertEqual(validate_library(self.output, deck_hashes=DECK_HASHES),
                         index)
        self.assertEqual(len(list(self.output.iterdir())), 4)

    def test_wrong_deck_revision_or_illegitimate_result_is_not_published(self):
        batch = example_batch(revision="z" * 64)
        self.write("wrong.json", batch)
        with self.assertRaisesRegex(ValueError, "revision"):
            publish(self.source, self.output,
                    engine_commit=COMMIT, deck_hashes=DECK_HASHES)
        self.assertFalse(self.output.exists())
        batch["deck_sha256"] = SHA
        batch["outcomes_are_competitive_win_rates"] = True
        self.write("wrong.json", batch)
        with self.assertRaises(ValueError):
            publish(self.source, self.output,
                    engine_commit=COMMIT, deck_hashes=DECK_HASHES)

    def test_duplicate_seeds_or_incorrect_summary_rejected(self):
        batch = example_batch(seeds=(1, 1))
        with self.assertRaisesRegex(ValueError, "duplicate seed"):
            validate_batch(batch, deck_hashes=DECK_HASHES)
        batch = example_batch()
        batch["summary"]["outcome_counts"]["win"] = 1
        with self.assertRaisesRegex(ValueError, "summary"):
            validate_batch(batch, deck_hashes=DECK_HASHES)

    def test_random_pods_reject_missing_or_invalid_seat_roles(self):
        value = example_batch(scenario="random")
        self.assertEqual(validate_batch(value, deck_hashes=DECK_HASHES),
                         "mortarion_current")
        value["runs"][0]["opponent_roles"] = {"1": "aggro", "2": "combo"}
        with self.assertRaisesRegex(ValueError, "independently assigned"):
            validate_batch(value, deck_hashes=DECK_HASHES)
        value["runs"][0]["opponent_roles"] = {
            "1": "aggro", "2": "combo", "3": "invented"
        }
        with self.assertRaisesRegex(ValueError, "independently assigned"):
            validate_batch(value, deck_hashes=DECK_HASHES)

    def test_opening_hand_is_optional_but_validated_when_present(self):
        batch=example_batch(scenario="random")
        self.assertEqual(validate_batch(batch,deck_hashes=DECK_HASHES),
                         "mortarion_current")
        batch["runs"][0]["opening_hand"]=["Swamp"]*6+["Blood Artist"]
        self.assertEqual(validate_batch(batch,deck_hashes=DECK_HASHES),
                         "mortarion_current")
        batch["runs"][0]["opening_hand"]=["Swamp"]*5
        with self.assertRaisesRegex(ValueError,"opening-hand"):
            validate_batch(batch,deck_hashes=DECK_HASHES)

    def test_corrupt_file_checksum_and_index_membership_rejected(self):
        self.write("x.json", example_batch())
        publish(self.source, self.output,
                engine_commit=COMMIT, deck_hashes=DECK_HASHES)
        datafile = next(p for p in self.output.glob("*.json")
                        if p.name != "manifest.json")
        datafile.write_text(datafile.read_text() + " ", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "checksum"):
            validate_library(self.output, deck_hashes=DECK_HASHES)
        publish(self.source, self.output,
                engine_commit=COMMIT, deck_hashes=DECK_HASHES)
        manifest = self.output / "manifest.json"
        index = json.loads(manifest.read_text())
        index["by_deck"]["mortarion_current"] = []
        manifest.write_text(json.dumps(index))
        with self.assertRaisesRegex(ValueError, "index"):
            validate_library(self.output, deck_hashes=DECK_HASHES)

    def test_no_unsafe_or_partial_publication_on_failed_replacement(self):
        self.write("x.json", example_batch())
        publish(self.source, self.output,
                engine_commit=COMMIT, deck_hashes=DECK_HASHES)
        original = (self.output / "manifest.json").read_bytes()
        self.write("other.json", example_batch(revision="bad"))
        with self.assertRaises(ValueError):
            publish(self.source, self.output,
                    engine_commit=COMMIT, deck_hashes=DECK_HASHES)
        self.assertEqual((self.output / "manifest.json").read_bytes(), original)

    def test_invalid_engine_commit_rejected(self):
        self.write("x.json", example_batch())
        with self.assertRaisesRegex(ValueError, "Git SHA"):
            publish(self.source, self.output,
                    engine_commit="../wrong", deck_hashes=DECK_HASHES)


if __name__ == "__main__":
    unittest.main()
