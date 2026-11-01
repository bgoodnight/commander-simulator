"""Poxwalkers nonhand spell triggers from real zone-backed cast events."""
import unittest

from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.reviewed_nonhand_cast_triggers import (
    NONHAND_CAST_TRIGGERS, resolve_reviewed_nonhand_cast_triggers)
from commander_sim.reviewed_flashback import cast_reviewed_flashback
from commander_sim.reviewed_token_spells import TOKEN_SPELLS
from commander_sim.template_resources import TemplateManaService


class NonhandCastTriggerTests(unittest.TestCase):
    def setUp(self):
        K,Z,C = _load_live_kernel()
        self.k=K()
        self.z=Z(self.k,seed=40)
        self.C=C
        review=NONHAND_CAST_TRIGGERS["Poxwalkers"]
        strike=TOKEN_SPELLS["Strike It Rich"]
        self.catalog={
            "Poxwalkers":{"oracle_id":review.oracle_id,
                          "oracle_text":review.oracle_text,
                          "type_line":"Creature — Zombie"},
            "Strike It Rich":{"oracle_id":strike.oracle_id,
                              "oracle_text":strike.oracle_text,
                              "mana_cost":strike.mana_cost,
                              "type_line":"Sorcery", "layout":"normal",
                              "colors":["R"]},
            "Mountain":{"type_line":"Basic Land — Mountain"}}
        self.mana=TemplateManaService(
            self.k,self.catalog,{"R"},zones=self.z)

    def add(self,name,zone,*,owner=0,oracle=None,coverage="approx"):
        raw=self.catalog.get(name,{})
        return self.z.add(self.C(
            oracle or raw.get("oracle_id","test:"+name),name,
            frozenset({"land"} if name=="Mountain" else
                      {"creature"} if name=="Poxwalkers" else {"sorcery"}),
            subtypes=frozenset({"Zombie"}) if name=="Poxwalkers" else frozenset(),
            colors=frozenset({"R"}) if name=="Strike It Rich" else None,
            coverage=coverage),owner,zone)

    def physical_cast(self,*,origin="graveyard",seat=0):
        spell=self.add("Strike It Rich",origin,owner=seat)
        return self.z.cast(
            seat,spell,reviewed_origin="graveyard"
            if origin=="graveyard" else None)

    def test_real_flashback_returns_poxwalkers_tapped_and_creates_treasure(self):
        old=self.add("Poxwalkers","graveyard")
        for _ in range(3):
            self.add("Mountain","battlefield")
        spell=self.add("Strike It Rich","graveyard")
        observed=[]
        out=cast_reviewed_flashback(
            self.z,0,spell,self.catalog,self.mana,sorcery_window=True,
            on_cast=lambda ticket: observed.extend(
                resolve_reviewed_nonhand_cast_triggers(
                    self.z,0,ticket,self.catalog)))
        self.assertIsNotNone(out)
        self.assertEqual(len(observed),1)
        new=observed[0]["object_id"]
        self.assertNotIn(old,self.k.objects)
        self.assertEqual(self.k.get(new).zone,"battlefield")
        self.assertTrue(self.k.get(new).tapped)
        self.assertEqual(observed[0]["origin"],"graveyard")
        self.assertEqual(self.k.get(out.exiled_id).zone,"exile")
        self.assertTrue(self.z.assert_consistent())

    def test_hand_cast_does_not_resurrect_poxwalkers(self):
        old=self.add("Poxwalkers","graveyard")
        ticket=self.physical_cast(origin="hand")
        self.assertEqual(resolve_reviewed_nonhand_cast_triggers(
            self.z,0,ticket,self.catalog),())
        self.assertIn(old,self.z.ids(0,"graveyard"))

    def test_wrong_oracle_or_opponent_graveyard_not_activated(self):
        wrong=self.add("Poxwalkers","graveyard",oracle="fake")
        opponent=self.add("Poxwalkers","graveyard",owner=1)
        ticket=self.physical_cast()
        self.assertEqual(resolve_reviewed_nonhand_cast_triggers(
            self.z,0,ticket,self.catalog),())
        self.assertIn(wrong,self.z.ids(0,"graveyard"))
        self.assertIn(opponent,self.z.ids(1,"graveyard"))

    def test_multiple_poxwalkers_return_once_each_and_remain_physical(self):
        a=self.add("Poxwalkers","graveyard")
        b=self.add("Poxwalkers","graveyard")
        ticket=self.physical_cast()
        results=resolve_reviewed_nonhand_cast_triggers(
            self.z,0,ticket,self.catalog)
        self.assertEqual(len(results),2)
        self.assertEqual({x["source_graveyard_id"] for x in results},{a,b})
        self.assertTrue(all(self.k.get(x["object_id"]).tapped for x in results))
        self.assertTrue(self.z.assert_consistent())

    def test_fabricated_or_stale_cast_event_is_rejected(self):
        self.add("Poxwalkers","graveyard")
        ticket=self.physical_cast()
        fake=self.add("Poxwalkers","graveyard")
        with self.assertRaises(ValueError):
            resolve_reviewed_nonhand_cast_triggers(
                self.z,0,self.C("fake","Fake",frozenset({"sorcery"})),
                self.catalog)
        # Nonhand trigger must observe this cast immediately, not be retried.
        self.z.move(fake,"hand","resolve")
        with self.assertRaises(ValueError):
            resolve_reviewed_nonhand_cast_triggers(
                self.z,0,ticket,self.catalog)


if __name__=="__main__":
    unittest.main()
