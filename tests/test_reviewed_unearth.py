"""Pinned Necron unearth pays existing mana and uses physical exile replacement."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.reviewed_unearth import (
    UNEARTH,reviewed_unearth,activate_reviewed_unearth,
    expire_reviewed_unearth)
from commander_sim.template_resources import TemplateManaService


class ReviewedUnearthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={row["deck_name"]:row["card"] for row in
            json.loads(next(f for f in FIXTURES if f.key=="necron_dynasties")
                       .snapshot_path.read_text())["cards"]}
        cls.catalog["Swamp"]={"type_line":"Basic Land — Swamp"}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=8)
        self.C=C
        self.mana=TemplateManaService(self.kernel,self.catalog,frozenset({"B"}))

    def add(self,name,zone,*,colors=None,card_id=None,types=("creature",)):
        row=self.catalog.get(name,{})
        return self.zones.add(self.C(
            card_id or row.get("oracle_id","test:"+name),
            name,frozenset(types),colors=frozenset(colors or []),
            coverage="approx"),0,zone)

    def swamp(self,n):
        return tuple(self.add("Swamp","battlefield",types=("land",))
                     for _ in range(n))

    def test_chronomancer_unearth_requires_actual_payment_then_exiles_at_endstep(self):
        self.swamp(3)
        old=self.add("Chronomancer","graveyard")
        result=activate_reviewed_unearth(
            self.zones,0,old,self.catalog,self.mana,sorcery_window=True)
        self.assertIsNotNone(result)
        self.assertEqual(len(result.paid_source_ids),3)
        self.assertEqual(result.source_old_id,old)
        permanent=self.kernel.get(result.permanent_id)
        self.assertEqual(permanent.zone,"battlefield")
        self.assertIn("haste",permanent.keywords)
        self.assertTrue(self.zones.assert_consistent())
        exiles=expire_reviewed_unearth(self.zones)
        self.assertEqual(len(exiles),1)
        self.assertEqual(exiles[0][0],result.permanent_id)
        exiled=self.kernel.get(exiles[0][1])
        self.assertEqual(exiled.zone,"exile")
        self.assertNotIn("haste",exiled.keywords)
        self.assertFalse(self.kernel.unearth_pending)
        self.assertTrue(self.zones.assert_consistent())

    def test_unearthed_sacrifice_is_replaced_with_exile_not_a_death(self):
        self.swamp(3)
        old=self.add("Skorpekh Lord","graveyard")
        result=activate_reviewed_unearth(
            self.zones,0,old,self.catalog,self.mana,sorcery_window=True)
        marker=len(self.kernel.events)
        next_id=self.zones.move(result.permanent_id,"graveyard","sacrifice")
        self.assertEqual(self.kernel.get(next_id).zone,"exile")
        self.assertEqual([e.name for e in self.kernel.events[marker:]
                          if e.name=="dies"],[])
        self.assertEqual(expire_reviewed_unearth(self.zones),())
        self.assertTrue(self.zones.assert_consistent())

    def test_unearthed_bounce_does_not_return_card_to_hand(self):
        self.swamp(3)
        old=self.add("Chronomancer","graveyard")
        result=activate_reviewed_unearth(
            self.zones,0,old,self.catalog,self.mana,sorcery_window=True)
        destination=self.zones.move(result.permanent_id,"hand","bounce")
        self.assertEqual(self.kernel.get(destination).zone,"exile")
        self.assertFalse(self.zones.ids(0,"hand"))

    def test_mandatory_etb_necron_cannot_silently_skip_effect(self):
        self.swamp(8)
        for name in ("Royal Warden","Triarch Praetorian",
                     "Canoptek Tomb Sentinel","Lokhust Heavy Destroyer"):
            with self.subTest(name=name):
                old=self.add(name,"graveyard")
                before=self.mana.floating()
                with self.assertRaises(NotImplementedError):
                    activate_reviewed_unearth(
                        self.zones,0,old,self.catalog,self.mana,sorcery_window=True)
                self.assertIn(old,self.zones.ids(0,"graveyard"))
                self.assertEqual(self.mana.floating(),before)
                self.assertFalse(self.kernel.unearth_pending)

    def test_insufficient_mana_and_wrong_timing_preserve_graveyard(self):
        old=self.add("Chronomancer","graveyard")
        with self.assertRaises(ValueError):
            activate_reviewed_unearth(
                self.zones,0,old,self.catalog,self.mana,sorcery_window=False)
        self.swamp(1)
        self.assertIsNone(activate_reviewed_unearth(
            self.zones,0,old,self.catalog,self.mana,sorcery_window=True))
        self.assertIn(old,self.zones.ids(0,"graveyard"))

    def test_wrong_source_identity_cannot_gain_unearth_permission(self):
        self.swamp(3)
        old=self.add("Chronomancer","graveyard",card_id="unreviewed")
        with self.assertRaises(ValueError):
            activate_reviewed_unearth(
                self.zones,0,old,self.catalog,self.mana,sorcery_window=True)
        self.assertIn(old,self.zones.ids(0,"graveyard"))

    def test_reviewed_registry_is_pinned_to_eight_named_necrons(self):
        self.assertEqual(len(UNEARTH),8)
        for name,rule in UNEARTH.items():
            with self.subTest(name=name):
                self.assertEqual(
                    reviewed_unearth(name,self.catalog[name]),rule)
                self.assertIn(rule.excerpt,self.catalog[name]["oracle_text"])
        self.assertIsNone(reviewed_unearth("Unreviewed Card",{}))


if __name__=="__main__":
    unittest.main()
