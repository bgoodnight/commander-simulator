"""M2: strictly bounded source-paid mana feasibility, not legal gameplay."""
import unittest
from unittest.mock import patch

from commander_sim.mana_costs import (
    FixedManaCost, UnsupportedManaCost, parse_fixed_mana_cost,
    plan_source_payment
)
from commander_sim.deck_fixtures import FIXTURES
from commander_sim.observation import observe


class FixedManaTests(unittest.TestCase):
    def test_parse_fixed_colored_generic_true_colorless(self):
        cost=parse_fixed_mana_cost("{3}{B}{B}{C}")
        self.assertEqual(cost.generic,3)
        self.assertEqual(cost.colored,("B","B","C"))
        self.assertEqual(cost.mana_value,6)
        self.assertEqual(parse_fixed_mana_cost("{0}").mana_value,0)

    def test_unsupported_and_ambiguous_costs_fail_closed(self):
        for value in ("", "{X}{B}", "{U/R}", "{2/B}", "{B/P}",
                      "{S}", "{1}{B} junk", "{-1}", "2BB", "{C/R}"):
            with self.subTest(value=value),self.assertRaises(UnsupportedManaCost):
                parse_fixed_mana_cost(value)
        with self.assertRaises(ValueError):
            plan_source_payment(FixedManaCost(0,("B",)),("B",))

    def test_swamps_pay_black_not_blue_and_generic_accepts_any_color(self):
        swamp=({"B"},)
        self.assertEqual(plan_source_payment(parse_fixed_mana_cost("{B}"),swamp),(0,))
        self.assertIsNone(plan_source_payment(parse_fixed_mana_cost("{U}"),swamp))
        self.assertIsNone(plan_source_payment(parse_fixed_mana_cost("{C}"),swamp))
        self.assertEqual(plan_source_payment(parse_fixed_mana_cost("{1}"),swamp),(0,))

    def test_true_colorless_requires_wastes_or_other_real_colorless(self):
        sources=({"B"},{"C"},{"B"})
        self.assertIsNone(plan_source_payment(parse_fixed_mana_cost("{C}{C}"),sources))
        self.assertEqual(plan_source_payment(parse_fixed_mana_cost("{1}{C}"),sources),(1,0))
        self.assertIsNone(plan_source_payment(parse_fixed_mana_cost("{2}{C}{C}"),sources))

    def test_flexible_source_is_preserved_for_rare_colored_pip(self):
        sources=({"U"},{"U","R"},{"R"})
        plan=plan_source_payment(parse_fixed_mana_cost("{1}{U}{R}"),sources)
        self.assertIsNotNone(plan)
        self.assertEqual(len(set(plan)),3)
        self.assertIsNone(plan_source_payment(parse_fixed_mana_cost("{R}{R}{R}"),sources))

    def test_payment_planner_is_pure_deterministic_and_cannot_reuse_a_source(self):
        sources=({"B"},{"U","B"},{"C"})
        before=tuple(frozenset(x) for x in sources)
        cost=parse_fixed_mana_cost("{1}{B}{B}")
        plan1=plan_source_payment(cost,sources)
        plan2=plan_source_payment(cost,sources)
        self.assertEqual(plan1,plan2)
        self.assertEqual(len(set(plan1)),3)
        self.assertEqual(tuple(frozenset(x) for x in sources),before)
        self.assertIsNone(plan_source_payment(parse_fixed_mana_cost("{B}{B}{B}"),sources))


class ManaPreviewObservations(unittest.TestCase):
    def test_mono_black_and_magnus_have_color_checked_cost_previews(self):
        with patch("urllib.request.urlopen",side_effect=AssertionError("No network")):
            for key in ("wretched_ranks","magnus_premium","necron_dynasties"):
                fixture=next(f for f in FIXTURES if f.key==key)
                with self.subTest(deck=key):
                    a=observe(fixture.deck_path,fixture.snapshot_path,
                              commander=fixture.commander,seed=17,turns=6)
                    b=observe(fixture.deck_path,fixture.snapshot_path,
                              commander=fixture.commander,seed=17,turns=6)
                    self.assertEqual(a,b)
                    self.assertEqual(a["mode"],"observation")
                    self.assertIn("No taps, casts",a["mana_preview_scope"])
                    self.assertEqual(len(a["trace"]),6)
                    for t in a["trace"]:
                        self.assertEqual(t["playable_now"],[])
                        for preview in t["source_paid_mana_preview"]:
                            self.assertEqual(preview["status"],"source_paid_mana_preview")
                            self.assertEqual(len(preview["source_indices"]),
                                             len(set(preview["source_indices"])))
                            self.assertTrue(all(0<=i<len(t["modeled_sources"])
                                                for i in preview["source_indices"]))
                            self.assertEqual(preview["source_names"],
                                [t["modeled_sources"][i]["card"]
                                 for i in preview["source_indices"]])


if __name__=="__main__":
    unittest.main()
