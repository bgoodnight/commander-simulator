"""Regression for password-gated outcome publication cohorts."""

import json
from pathlib import Path
import tempfile
import unittest

from tools.append_requested_outcomes import append
from tools.build_game_outcomes import generate
from tools.publish_game_outcomes import validate_library


class RequestedOutcomePublicationTests(unittest.TestCase):
    def test_scenarios_accumulate_only_for_matching_engine_source(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            output = directory / "published"
            source = directory / "incoming.json"
            for scenario, expected_count in [("mixed", 1), ("control", 2)]:
                source.write_text(json.dumps(generate(
                    "necron_dynasties", seeds=1, rounds=2,
                    scenario=scenario, examples=0
                )), encoding="utf-8")
                index = append(source, output, engine_commit="a" * 40)
                self.assertEqual(len(index["files"]), expected_count)
                self.assertEqual(len(validate_library(output)["files"]), expected_count)
            source.write_text(json.dumps(generate(
                "necron_dynasties", seeds=1, rounds=2,
                scenario="combo", examples=0
            )), encoding="utf-8")
            index = append(source, output, engine_commit="b" * 40)
            self.assertEqual(len(index["files"]), 1)
            self.assertEqual(len(validate_library(output)["files"]), 1)


if __name__ == "__main__":
    unittest.main()
