"""Six-deck current-engine cache generation and compatibility contracts."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from commander_sim.deck_fixtures import FIXTURES
from tools import build_bounded_batches as generator


def fake_batch(key, *, seeds, turns):
    return {
        "mode": "bounded_real_action_batch",
        "deck_key": key,
        "deck_sha256": "a" * 64,
        "seed_count": seeds,
        "turns": [{"turn": t, "mean_hand_size": 7} for t in range(1, turns + 1)],
        "curated_milestones": None,
        "limitations": "Reviewed physical actions only",
    }


def fake_run(key, *, seed, turns):
    return {
        "mode": "bounded_authoritative_early_actions",
        "deck_key": key, "deck_sha256": "a" * 64,
        "seed": seed, "mulligan": {"policy": "one-free"},
        "events": [{
            "turn": t, "land_count": t, "hand_size": 7,
            "maximum_hand_size": 7,
            "unsupported_cards_in_hand": [],
            "events": [{"type": "draw", "card": "Swamp"}],
        } for t in range(1, turns + 1)],
        "state_snapshots": [{
            "turn": t, "hand": [], "battlefield": [],
        } for t in range(1, turns + 1)],
    }


class CurrentUiDataTests(unittest.TestCase):
    def test_all_six_canonical_decks_emit_matching_summary_and_runs(self):
        self.assertEqual(generator.KEYS, tuple(f.key for f in FIXTURES))
        with tempfile.TemporaryDirectory() as root:
            with patch.object(generator, "run_bounded_batch", side_effect=fake_batch), \
                    patch.object(generator, "run_bounded_early_game", side_effect=fake_run):
                summary = generator.generate(seeds=3, output=root)
            self.assertEqual(set(summary["decks"]), set(generator.KEYS))
            self.assertEqual(len(summary["decks"]), 6)
            saved = json.loads((Path(root) / "bounded-batches.json").read_text())
            self.assertEqual(saved, summary)
            for key, report in saved["decks"].items():
                self.assertEqual(report["deck_key"], key)
                self.assertEqual(report["seed_count"], 3)
                rows = json.loads((Path(root) / f"bounded-runs-{key}.json").read_text())
                self.assertEqual([r["seed"] for r in rows], [0, 1, 2])
                self.assertTrue(all(r["deck_key"] == key
                                    and r["deck_sha256"] == report["deck_sha256"]
                                    and len(r["events"]) == 6
                                    for r in rows))

    def test_cleanup_violation_refused_before_publishing_summary(self):
        with tempfile.TemporaryDirectory() as root:
            def incorrect(key, *, seed, turns):
                row = fake_run(key, seed=seed, turns=turns)
                row["events"][0]["hand_size"] = 8
                return row
            with patch.object(generator, "run_bounded_batch", side_effect=fake_batch), \
                    patch.object(generator, "run_bounded_early_game", side_effect=incorrect):
                with self.assertRaisesRegex(ValueError, "hand limit"):
                    generator.generate(seeds=2, output=root)
            self.assertFalse((Path(root) / "bounded-batches.json").exists())

    def test_invalid_seed_counts_do_not_mutate_output(self):
        with tempfile.TemporaryDirectory() as root:
            for count in (-1, 0, 1001, True):
                with self.subTest(count=count), self.assertRaises(ValueError):
                    generator.generate(seeds=count, output=root)
            self.assertEqual(list(Path(root).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
