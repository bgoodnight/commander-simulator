"""Reusable effect templates are descriptors, not invented card rules."""
import unittest

from commander_sim.effect_templates import (
    ManaMode, EffectTemplate, ReviewedEffect, compose_effect,
    admit_reviewed_effect, tutor_matches,
)
from commander_sim.reviewed_rocks import reviewed_rock


class EffectTemplateTests(unittest.TestCase):
    def test_multi_mana_and_funded_activation_are_shared_templates(self):
        self.assertEqual(compose_effect(ReviewedEffect(
            "x", "text", "rock_colorless_two",
            assumptions=("approved generic source",))).mana_modes[0].output, ("C", "C"))
        mode = compose_effect(ReviewedEffect(
            "x", "text", "signet_ur",
            assumptions=("approved generic source",))).mana_modes[0]
        self.assertEqual(mode.activation_generic, 1)
        self.assertEqual(mode.output, ("U", "R"))

    def test_tutor_template_is_metadata_filter_not_real_search(self):
        r = ReviewedEffect("id", "search text", "tutor_to_hand",
            overrides=(("search_types", frozenset({"instant", "sorcery"})),
                       ("max_mana_value", 2), ("reveal", True)),
            assumptions=("reveals eligible printed type",))
        template = compose_effect(r)
        self.assertTrue(tutor_matches(template, {"type_line": "Instant", "cmc": 2}))
        self.assertFalse(tutor_matches(template, {"type_line": "Creature — Wizard", "cmc": 2}))
        self.assertFalse(tutor_matches(template, {"type_line": "Sorcery", "cmc": 3}))
        self.assertFalse(tutor_matches(template, {"type_line": "Instant"}))
        self.assertEqual(template.destination, "hand")

    def test_overrides_reject_arbitrary_rules_or_other_effect_family(self):
        for overrides in ((("python", "execute"),),
                          (("search_types", frozenset({"creature"})),)):
            with self.assertRaises(ValueError):
                compose_effect(ReviewedEffect("id", "text", "rock_colorless_one",
                    overrides=overrides, assumptions=("review",)))

    def test_unknown_card_does_not_gain_effect_by_type_or_role(self):
        review = ReviewedEffect("oracle-id", "{T}: Add {C}.",
                                "rock_colorless_one",
                                assumptions=("reviewed tap",))
        with self.assertRaises(ValueError):
            admit_reviewed_effect({"oracle_id": "other", "oracle_text": "{T}: Add {C}.",
                                   "layout": "normal"}, review)
        with self.assertRaises(ValueError):
            admit_reviewed_effect({"oracle_id": "oracle-id", "oracle_text": "changed",
                                   "layout": "normal"}, review)

    def test_tapped_rock_entry_is_composable(self):
        template = compose_effect(ReviewedEffect("id", "text", "rock_black_tapped",
                                                  assumptions=("ETB tapped",)))
        self.assertTrue(template.enter_tapped)
        self.assertEqual(template.mana_modes[0].output, ("B",))

    def test_bad_template_modes_fail_closed(self):
        with self.assertRaises(ValueError):
            ManaMode(("Q",))
        with self.assertRaises(ValueError):
            EffectTemplate("library_search", search_types=frozenset({"not-a-type"}))
        with self.assertRaises(ValueError):
            ReviewedEffect("id", "text", "rock_colorless_two")

    def test_exact_pinned_rock_and_identity_modes(self):
        sample = {"oracle_id": "0bc7f093-bef0-4f1a-852c-4b75ebf54838",
                  "oracle_text": "{T}: Add one mana of any color in your commander's color identity.",
                  "mana_cost": "{2}", "type_line": "Artifact",
                  "layout": "normal"}
        template, cost = reviewed_rock("Arcane Signet", sample, {"U", "R"})
        self.assertEqual(cost, "{2}")
        self.assertEqual({mode.output for mode in template.mana_modes}, {("U",), ("R",)})
        self.assertIsNone(reviewed_rock("Generic mana rock", sample, {"U", "R"}))
        sample["oracle_text"] = "different"
        with self.assertRaises(ValueError):
            reviewed_rock("Arcane Signet", sample, {"U", "R"})


if __name__ == "__main__":
    unittest.main()
