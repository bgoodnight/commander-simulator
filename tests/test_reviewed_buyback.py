"""Source-paid buyback uses real stack, library, hand and no virtual cards."""
import json
import unittest
from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel,run_bounded_early_game
from commander_sim.reviewed_buyback import (
    BUYBACK, reviewed_buyback, buyback_total_cost,cast_reviewed_buyback)
from commander_sim.template_resources import TemplateManaService

class BuybackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for fixture in FIXTURES:
            for row in json.loads(fixture.snapshot_path.read_text())["cards"]:
                cls.catalog.setdefault(row["deck_name"],row["card"])
        cls.catalog["Island"]={"type_line":"Basic Land — Island"}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K()
        self.z=Z(self.k,seed=21)
        self.C=C
        self.service=TemplateManaService(self.k,self.catalog,{"U","R"},zones=self.z)

    def add(self,name,zone="hand",oid=None):
        raw=self.catalog.get(name,{})
        return self.z.add(self.C(oid or raw.get("oracle_id","test:"+name),
            name,frozenset({"land"} if name=="Island" else {"instant"}),
            colors=frozenset({"U"}) if name=="Whispers of the Muse" else None,
            coverage="approx"),0,zone)

    def setup_spell(self,lands=6):
        for _ in range(lands):
            self.add("Island","battlefield")
        source=self.add("Whispers of the Muse")
        self.add("Draw target","library")
        return source

    def cast(self,oid,buyback):
        return cast_reviewed_buyback(self.z,0,oid,self.catalog,self.service,
                        buyback=buyback,casting_window=True)

    def test_full_buyback_returns_original_card_and_draws(self):
        oid=self.setup_spell()
        result=self.cast(oid,True)
        self.assertTrue(result.bought_back)
        self.assertEqual(result.destination,"hand")
        self.assertEqual(self.k.get(result.destination_id).card.name,"Whispers of the Muse")
        self.assertIn(result.destination_id,self.z.ids(0,"hand"))
        self.assertEqual(len(result.drawn_ids),1)
        self.assertEqual(len(result.paid_source_ids),6)
        self.assertNotIn(oid,self.k.objects)
        self.assertEqual(self.z.ids(0,"stack"),())
        self.assertTrue(self.z.assert_consistent())

    def test_without_buyback_goes_to_graveyard(self):
        oid=self.setup_spell(lands=1)
        result=self.cast(oid,False)
        self.assertFalse(result.bought_back)
        self.assertEqual(result.destination,"graveyard")
        self.assertIn(result.destination_id,self.z.ids(0,"graveyard"))
        self.assertEqual(len(result.paid_source_ids),1)
        self.assertTrue(self.z.assert_consistent())

    def test_cannot_freely_return_spell_without_additional_five_mana(self):
        oid=self.setup_spell(lands=5)
        self.assertIsNone(self.cast(oid,True))
        self.assertIn(oid,self.z.ids(0,"hand"))
        self.assertEqual(self.z.ids(0,"stack"),())
        self.assertEqual(self.z.ids(0,"graveyard"),())
        self.assertTrue(self.z.assert_consistent())

    def test_repeat_cast_requires_new_mana_not_free(self):
        oid=self.setup_spell()
        first=self.cast(oid,True)
        self.assertIsNone(self.cast(first.destination_id,False))
        self.add("Island","battlefield")
        again=self.cast(first.destination_id,False)
        self.assertEqual(again.destination,"graveyard")
        self.assertEqual(len(again.drawn_ids),1)
        self.assertEqual(sum(o.card.name=="Whispers of the Muse"
                             for o in self.k.objects.values()),1)
        self.assertTrue(self.z.assert_consistent())

    def test_invalid_source_text_timing_and_false_card_fail_closed(self):
        oid=self.setup_spell()
        wrong=dict(self.catalog)
        wrong["Whispers of the Muse"]=dict(self.catalog["Whispers of the Muse"])
        wrong["Whispers of the Muse"]["oracle_text"]="Unreviewed"
        self.assertIsNone(reviewed_buyback("Whispers of the Muse",wrong["Whispers of the Muse"]))
        with self.assertRaises(ValueError):
            cast_reviewed_buyback(self.z,0,oid,wrong,self.service,buyback=True,casting_window=True)
        with self.assertRaises(ValueError):
            cast_reviewed_buyback(self.z,0,oid,self.catalog,self.service,buyback=True,casting_window=False)
        self.assertIn(oid,self.z.ids(0,"hand"))

    def test_empty_library_rejected_before_payment(self):
        oid=self.setup_spell()
        draw=self.z.ids(0,"library")[0]
        self.z.move(draw,"graveyard","mill")
        with self.assertRaises(NotImplementedError):
            self.cast(oid,True)
        self.assertIn(oid,self.z.ids(0,"hand"))
        self.assertFalse(any(self.k.get(i).tapped for i in self.z.ids(0,"battlefield")))

    def test_six_deck_replay_conserves_cards_and_buyback_choices(self):
        for key in ("magnus_premium","magnus_budget","wretched_ranks",
                    "mortarion_current","mortarion_ideal","necron_dynasties"):
            with self.subTest(deck=key):
                a=run_bounded_early_game(key,seed=5,turns=5)
                self.assertEqual(a,run_bounded_early_game(key,seed=5,turns=5))
                for turn,state in zip(a["events"],a["state_snapshots"]):
                    casts=[e for e in turn["events"] if e["type"]=="reviewed_buyback_cast"]
                    self.assertLessEqual(len(casts),1)
                    self.assertEqual(len(casts),sum(e["type"]=="reviewed_buyback_resolved" for e in turn["events"]))
                    self.assertEqual(turn["library_size"]+turn["hand_size"]+
                        len(state["battlefield"])+len(state["graveyard"])+
                        len(state["exile"])+1,100)

if __name__=="__main__":
    unittest.main()
