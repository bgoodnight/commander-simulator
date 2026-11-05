"""Pinned Gorge ward-Blight overlay stays narrowly scoped and fail closed."""
import unittest
from tools.patch_gorge_ward_blight import TARGET, REPLACEMENT, patched


class WardBlightPatchTests(unittest.TestCase):
    def test_guard_prevents_mandatory_zero_candidate_decision(self):
        result = patched("prefix\n" + TARGET + "\nsuffix")
        self.assertIn("if len(ids) == 0", result)
        self.assertIn("return false, false", result)
        self.assertIn('e.askWardObjects(rp, ctx, payer, "ward_blight"', result)
        self.assertNotIn(TARGET, result)
        self.assertEqual(result.count(REPLACEMENT), 1)

    def test_refuse_unpinned_or_already_patched_source(self):
        for source in ("wrong version", TARGET + "\n" + TARGET, REPLACEMENT):
            with self.assertRaisesRegex(ValueError, "source changed"):
                patched(source)


if __name__ == "__main__":
    unittest.main()
