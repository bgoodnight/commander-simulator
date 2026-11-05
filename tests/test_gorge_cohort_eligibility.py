"""Eligibility regression tests: historical rules must not contaminate current metrics."""
import copy
import unittest

from tools.gorge_cohort_eligibility import (
    SCHEMA, IDENTITY_FIELDS, eligible_partition, fingerprint, inspect,
    validate_registry,
)


def setup():
    c = {"cohort_id": "post-fix-v1", "status": "current", "approved": True,
         "approval_ref": "reviewed-protocol-001"}
    c.update({k: "sha-" + k for k in IDENTITY_FIELDS})
    registry = {"schema": SCHEMA, "cohorts": [
        {"cohort_id": "old-mortarion", "status": "archived", "approved": False},
        {"cohort_id": "test-panel", "status": "experimental", "approved": False},
        c,
    ]}
    row = {"cohort_id": "post-fix-v1", "cohort_manifest_sha256": fingerprint(c),
           "game_id": "new/1", "source_sha256": "a" * 64,
           "finished": True, "replay_verified": True, "error": None}
    row.update({k: c[k] for k in IDENTITY_FIELDS})
    return registry, row


class EligibilityTests(unittest.TestCase):
    def test_mixed_archive_and_experiment_are_excluded(self):
        registry, current = setup()
        old = dict(current, cohort_id="old-mortarion", game_id="old/1")
        experiment = dict(current, cohort_id="test-panel", game_id="test/1")
        legacy = dict(current, game_id="legacy/1")
        legacy.pop("cohort_id")
        selected, excluded = eligible_partition([old, experiment, legacy, current], registry)
        self.assertEqual([r["game_id"] for r in selected], ["new/1"])
        self.assertEqual(len(excluded), 3)
        self.assertEqual({x["reason"] for x in excluded},
                         {"archived", "experimental", "unknown_or_legacy_cohort"})

    def test_same_cohort_changed_rules_or_pilot_is_ineligible(self):
        registry, row = setup()
        for key in IDENTITY_FIELDS:
            changed = dict(row, **{key: "older-value"})
            self.assertEqual(inspect(changed, registry), (False, "version_mismatch"))

    def test_unsafe_digest_or_unverified_is_excluded(self):
        registry, row = setup()
        for key, value in [("source_sha256", None), ("replay_verified", False),
                           ("cohort_manifest_sha256", "invalid")]:
            changed = dict(row, **{key: value})
            self.assertFalse(inspect(changed, registry)[0])

    def test_registry_rejects_unapproved_current_cohort(self):
        registry, row = setup()
        registry["cohorts"][-1]["approved"] = False
        with self.assertRaisesRegex(ValueError, "explicitly approved"):
            eligible_partition([row], registry)

    def test_duplicate_approved_game_ids_fail(self):
        registry, row = setup()
        with self.assertRaisesRegex(ValueError, "distinct"):
            eligible_partition([row, row], registry)

    def test_no_implicit_current_cohort(self):
        registry = {"schema": SCHEMA, "cohorts": []}
        _, row = setup()
        selected, excluded = eligible_partition([row], registry)
        self.assertEqual(selected, [])
        self.assertEqual(excluded[0]["reason"], "unknown_or_legacy_cohort")


if __name__ == "__main__":
    unittest.main()
