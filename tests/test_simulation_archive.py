"""Archive contracts: deterministic saved records and no site mutations."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.build_simulation_archive import (
    DECK_KEYS, FORMAT, generate, write_archive,
)


def fake_run(deck, *, seed, turns):
    events = []
    states = []
    for index in range(1, turns + 1):
        events.append({
            "turn": index, "land_count": index, "creature_count": seed % 2,
            "mana_rock_count": 1, "hand_size": 7 - index,
            "unsupported_cards_in_hand": ["Test unreviewed"],
            "events": [{"type": "draw", "card": "Test Card"}],
        })
        states.append({
            "turn": index, "battlefield": [], "hand": [],
            "graveyard": [], "exile": [], "untracked_tokens": [],
            "object_views": {"battlefield": [], "hand": [],
                             "graveyard": [], "exile": []},
        })
    return {
        "seed": seed, "deck_key": deck, "deck_sha256": "test-sha",
        "mode": "bounded_authoritative_early_actions",
        "mulligan": {"policy": "keep"}, "events": events,
        "state_snapshots": states,
    }


class SimulationArchiveTests(unittest.TestCase):
    def test_all_six_decks_are_eligible(self):
        self.assertEqual(len(DECK_KEYS), 6)
        self.assertEqual(len(set(DECK_KEYS)), 6)

    def test_physical_mortarion_is_explicitly_eligible(self):
        from tools.build_simulation_archive import APPROVED_KEYS
        self.assertEqual(len(DECK_KEYS), 6)
        self.assertEqual(len(APPROVED_KEYS), 7)
        self.assertIn("mortarion_physical_final", APPROVED_KEYS)
        meta, runs = generate("mortarion_physical_final", seeds=4, turns=6, runner=fake_run)
        self.assertEqual(meta["deck_key"], "mortarion_physical_final")
        self.assertEqual(len(runs), 4)

    def test_archives_reproducible_and_reconcile_with_runs(self):
        a, runs = generate(DECK_KEYS[0], seeds=3, turns=2, runner=fake_run)
        b, other = generate(DECK_KEYS[0], seeds=3, turns=2, runner=fake_run)
        self.assertEqual(a, b)
        self.assertEqual(runs, other)
        self.assertEqual(a["format"], FORMAT)
        self.assertEqual(a["seed_count"], 3)
        self.assertEqual([r["seed"] for r in runs], [0, 1, 2])
        self.assertEqual(a["summary"][0]["event_counts"]["draw"], 3)
        self.assertEqual(a["summary"][1]["mean_lands"], 2)
        self.assertIn("exile", runs[0]["state_snapshots"][0])

    def test_persisted_manifest_matches_bytes_and_deck_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            report = write_archive(directory, DECK_KEYS[0],
                                   seeds=2, turns=2, start_seed=10,
                                   runner=fake_run)
            files = list(Path(directory).iterdir())
            self.assertEqual(len(files), 2)
            run_data = (Path(directory) / report["run_file"]).read_bytes()
            self.assertEqual(hashlib.sha256(run_data).hexdigest(),
                             report["run_sha256"])
            archive = json.loads(run_data)
            self.assertEqual([x["seed"] for x in archive], [10, 11])
            self.assertTrue(all(x["deck_sha256"] == report["deck_sha256"]
                                for x in archive))

    def test_mismatched_deck_revision_refused(self):
        def mismatch(deck, *, seed, turns):
            row = fake_run(deck, seed=seed, turns=turns)
            row["deck_sha256"] = str(seed)
            return row
        with self.assertRaisesRegex(ValueError, "Mixed"):
            generate(DECK_KEYS[0], seeds=2, runner=mismatch)

    def test_invalid_scope_refused(self):
        for kwargs in ({"seeds": 0}, {"seeds": 1001},
                       {"turns": 11}, {"start_seed": -1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                generate(DECK_KEYS[0], runner=fake_run, **kwargs)
        with self.assertRaises(ValueError):
            generate("not_a_fixture", runner=fake_run)


if __name__ == "__main__":
    unittest.main()
