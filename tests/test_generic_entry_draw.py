"""Shared physical entry-draw recipe admission and exact import grammar."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES,EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel,run_bounded_early_game
from commander_sim.kernel_life import KernelLife
from commander_sim.provisional_import import provisional_profile,provisional_report
from commander_sim.library_actions import LibraryAction,resolve_library_actions
from commander_sim.reviewed_enter_effects import (
    reviewed_enter_rule,execute_reviewed_enter)


class SharedEntryDrawTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for f in (*FIXTURES,*EXPERIMENTAL_FIXTURES):
            cls.catalog.update({x["deck_name"]:x["card"] for x in
                json.loads(f.snapshot_path.read_text())["cards"]})

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K()
        self.z=Z(self.k,seed=71)
        self.C=C
        self.life=KernelLife(self.k)

    def raw(self,text,mana="{2}{U}"):
        return {"name":"Future Entry","oracle_id":"aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
                "oracle_text":text,"type_line":"Creature — Wizard",
                "layout":"normal","mana_cost":mana}

    def add(self,name,zone="library",card_id=None):
        card=self.catalog.get(name,{})
        return self.z.add(self.C(card_id or card.get("oracle_id","test:"+name),
           name,frozenset({"creature"}),coverage="approx"),0,zone)

    def test_provisional_simple_creature_entry_draw_is_typed_and_complete(self):
        p=provisional_profile(self.raw(
            "Flying\nWhen this creature enters, draw two cards."))
        self.assertEqual(p.kind,"creature_body")
        self.assertEqual(p.entry_actions,(LibraryAction("draw",2),))
        self.assertEqual(p.library_actions,())

    def test_named_oracle_ability_label_and_ward_can_be_imported(self):
        raw=self.catalog["Lord of Change"]
        p=provisional_profile(raw)
        self.assertIsNotNone(p)
        self.assertEqual(p.entry_actions,(LibraryAction("draw",3),))
        self.assertIn("ward",raw["oracle_text"].lower())

    def test_multiple_complete_library_entries_resolve_in_order(self):
        p=provisional_profile(self.raw(
            "When this creature enters, mill two cards.\n"
            "When this creature enters, draw one card."))
        self.assertIsNotNone(p)
        self.assertEqual(p.entry_actions,
                         (LibraryAction("mill",2),LibraryAction("draw",1)))
        for i in range(4):
            self.add("Card "+str(i))
        effect=resolve_library_actions(self.z,0,p.entry_actions)
        self.assertEqual(len(effect.milled_ids),2)
        self.assertEqual(len(effect.drawn_ids),1)
        self.assertEqual([s["kind"] for s in effect.steps],["mill","draw"])
        self.assertTrue(self.z.assert_consistent())

    def test_unrecognized_mandatory_entry_stays_unreviewed(self):
        for text in (
            "When this creature enters, draw two cards, then win the game.",
            "When this creature enters, draw two cards. Sacrifice a creature.",
            "When this creature enters, draw eight cards.",
            "When this creature enters, draw three cards.\n"
            "When this creature enters, destroy target creature.",
            "If this creature would enter, exile it instead.",
            "When this creature enters, target player draws two cards.",
        ):
            with self.subTest(text=text):
                self.assertIsNone(provisional_profile(self.raw(text)))

    def test_non_normal_and_missing_oracle_id_fail_closed(self):
        raw=self.raw("When this creature enters, draw two cards.")
        self.assertIsNone(provisional_profile(dict(raw,layout="adventure")))
        self.assertIsNone(provisional_profile(dict(raw,oracle_id=None)))

    def test_one_full_physical_pin_for_lord_of_change(self):
        source=self.catalog["Lord of Change"]
        rule=reviewed_enter_rule("Lord of Change",source)
        self.assertIsNotNone(rule)
        self.assertEqual(rule.library_actions,(LibraryAction("draw",3),))
        altered=dict(source,oracle_id="bad:oracle")
        self.assertIsNone(reviewed_enter_rule("Lord of Change",altered))

    def test_lord_of_change_enters_and_draws_three_actual_cards(self):
        source=self.add("Lord of Change","hand")
        entered=self.z.move(source,"battlefield","resolve")
        self.add("First")
        self.add("Second")
        self.add("Third")
        self.add("Fourth")
        result=execute_reviewed_enter(
            self.z,self.life,entered,self.catalog)
        self.assertEqual(result.operation,"library_recipe")
        self.assertEqual(len(result.drawn_ids),3)
        self.assertEqual(result.library_steps[0]["kind"],"draw")
        self.assertEqual(len(self.z.ids(0,"hand")),3)
        self.assertEqual(len(self.z.ids(0,"library")),1)
        self.assertTrue(self.z.assert_consistent())

    def test_import_report_exposes_entry_action_not_whole_card_fidelity(self):
        raw=self.raw("When this creature enters, draw two cards.")
        report=provisional_report([{"deck_name":raw["name"],"card":raw}])[0]
        self.assertEqual(report["entry_actions"],
                         [{"kind":"draw","count":2}])
        self.assertEqual(report["fidelity"],"provisional_partial")
        self.assertEqual(report["status"],"provisional")

    def test_mandatory_draw_preflight_refuses_short_library(self):
        with self.assertRaises(ValueError):
            resolve_library_actions(
                self.z,0,(LibraryAction("draw",3),))
        self.assertEqual(len(self.z.ids(0,"hand")),0)

    def test_two_magnus_variants_keep_authoritative_zone_conservation(self):
        for key in ("magnus_premium","magnus_budget"):
            with self.subTest(key=key):
                run=run_bounded_early_game(
                    key,turns=4,seed=9,provisional_mode="safe")
                self.assertEqual(run["completed_rounds"],4)
                self.assertTrue(all("life_totals" in turn
                    for turn in run["events"]))
                self.assertIn("pilot_decisions",run["events"][0])


    def test_exact_compound_entry_sequences_are_typed(self):
        cases=(
            ("When this creature enters, mill two cards, then draw a card.",
             (LibraryAction("mill",2),LibraryAction("draw",1))),
            ("When this creature enters, draw a card, then discard a card.",
             (LibraryAction("draw",1),LibraryAction("discard",1))),
            ("Ominous Research — When this creature enters, mill three cards, then draw two cards.",
             (LibraryAction("mill",3),LibraryAction("draw",2))),
        )
        for text,expected in cases:
            with self.subTest(text=text):
                p=provisional_profile(self.raw(text))
                self.assertIsNotNone(p)
                self.assertEqual(p.entry_actions,expected)
                self.assertEqual(p.fidelity,"provisional_partial")

    def test_compound_entry_mills_then_draws_actual_physical_cards(self):
        text="When this creature enters, mill two cards, then draw a card."
        p=provisional_profile(self.raw(text))
        self.assertIsNotNone(p)
        for i in range(3):
            self.add("Library "+str(i))
        out=resolve_library_actions(self.z,0,p.entry_actions)
        self.assertEqual(len(out.milled_ids),2)
        self.assertEqual(len(out.drawn_ids),1)
        self.assertEqual(len(self.z.ids(0,"graveyard")),2)
        self.assertEqual(len(self.z.ids(0,"hand")),1)
        self.assertEqual(len(self.z.ids(0,"library")),0)
        self.assertEqual([x["kind"] for x in out.steps],["mill","draw"])
        self.assertTrue(self.z.assert_consistent())

    def test_entry_draw_then_discard_moves_real_card_and_keeps_no_ghost(self):
        p=provisional_profile(self.raw(
            "When this creature enters, draw a card, then discard a card."))
        self.add("Only")
        out=resolve_library_actions(self.z,0,p.entry_actions)
        self.assertEqual(len(out.drawn_ids),1)
        self.assertEqual(len(out.discarded_ids),1)
        self.assertEqual(len(self.z.ids(0,"hand")),0)
        self.assertEqual(len(self.z.ids(0,"graveyard")),1)
        self.assertTrue(self.z.assert_consistent())

    def test_compound_entry_fails_closed_on_incomplete_rules(self):
        for text in (
            "When this creature enters, mill two cards, then draw a card, then win the game.",
            "When this creature enters, target player mills two cards, then draws a card.",
            "When this creature enters, mill eight cards, then draw a card.",
            "When this creature enters, draw a card, then discard two cards.",
            "When this creature enters, draw a card, then discard a card. Exile a creature.",
        ):
            with self.subTest(text=text):
                self.assertIsNone(provisional_profile(self.raw(text)))


if __name__=="__main__":
    unittest.main()
