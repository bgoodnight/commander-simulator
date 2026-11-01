"""Reiterate copies active reviewed spell effects without inventing cards."""
import json
import unittest
from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel,run_bounded_early_game
from commander_sim.reviewed_spell_copy import (
    REITERATE,reviewed_copy_spell,verified_copy_target,cast_reiterate_copy)
from commander_sim.reviewed_token_spells import (
    reviewed_token_spell,create_reviewed_token_batches)
from commander_sim.bounded_trigger_effects import resolve_reviewed_spell_triggers
from commander_sim.template_resources import TemplateManaService


class ReiterateCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for fixture in FIXTURES:
            for row in json.loads(fixture.snapshot_path.read_text())["cards"]:
                cls.catalog.setdefault(row["deck_name"],row["card"])
        cls.catalog["Mountain"]={"type_line":"Basic Land — Mountain"}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K()
        self.z=Z(self.k,seed=19)
        self.C=C
        self.mana=TemplateManaService(self.k,self.catalog,{"R","U"},zones=self.z)

    def add(self,name,zone="hand",*,owner=0,oracle=None,types=None):
        raw=self.catalog.get(name,{})
        if types is None:
            types={"land"} if name=="Mountain" else (
                {"creature"} if name=="Storm-Kiln Artist" else
                {"instant"} if name=="Reiterate" else {"sorcery"})
        return self.z.add(self.C(
            oracle or raw.get("oracle_id","test:"+name),name,
            frozenset(types),coverage="approx",
            colors=frozenset({"R"}) if name!="Mountain" else None),
            owner,zone)

    def target_pending(self,land_count=7,spell="Strike It Rich"):
        for _ in range(land_count):
            self.add("Mountain","battlefield")
        original=self.add(spell)
        raw=self.catalog[spell]
        payment=self.mana.pay_spell(0,raw["mana_cost"],self.k.get(original))
        self.assertIsNotNone(payment)
        ticket=self.z.cast(0,original)
        return ticket

    def cast_copy(self,ticket,*,buyback=False,on_copy=None):
        copier=self.add("Reiterate")
        return cast_reiterate_copy(self.z,0,copier,ticket,self.catalog,
            self.mana,buyback=buyback,casting_window=True,on_copy=on_copy)

    def test_real_target_remains_stack_and_copy_produces_independent_effect(self):
        target=self.target_pending(land_count=4)
        result=self.cast_copy(target)
        self.assertEqual(result.copied_card_name,"Strike It Rich")
        self.assertEqual(len(result.created_token_ids),1)
        self.assertEqual(len(result.mana_source_ids),3)
        self.assertEqual(self.k.get(result.copier_destination_id).zone,"graveyard")
        self.assertEqual(self.k.get(target.object_id).zone,"stack")
        self.assertEqual(len(self.z.ids(0,"stack")),1)
        self.assertEqual(len(self.z.ids(0,"battlefield")),5)
        original=reviewed_token_spell("Strike It Rich",self.catalog["Strike It Rich"])
        new_tokens=[]
        self.z.resolve(target,effect=lambda k,t:new_tokens.extend(
            create_reviewed_token_batches(self.z,0,original.batches)))
        self.assertEqual(len(new_tokens),1)
        self.assertNotEqual(new_tokens[0],result.created_token_ids[0])
        self.assertEqual(sum(o.card.name=="Strike It Rich" for o in self.k.objects.values()),1)
        self.assertTrue(self.z.assert_consistent())

    def test_buyback_cost_returns_reiterate_to_actual_hand(self):
        target=self.target_pending(land_count=7)
        result=self.cast_copy(target,buyback=True)
        self.assertEqual(result.copier_destination,"hand")
        self.assertTrue(result.bought_back)
        self.assertEqual(len(result.mana_source_ids),6)
        self.assertIn(result.copier_destination_id,self.z.ids(0,"hand"))
        self.assertEqual(self.k.get(target.object_id).zone,"stack")
        self.assertTrue(self.z.assert_consistent())

    def test_buyback_fails_without_six_extra_mana_and_preserves_target(self):
        target=self.target_pending(land_count=4)
        copier=self.add("Reiterate")
        result=cast_reiterate_copy(self.z,0,copier,target,self.catalog,
                      self.mana,buyback=True,casting_window=True)
        self.assertIsNone(result)
        self.assertIn(copier,self.z.ids(0,"hand"))
        self.assertIn(target.object_id,self.z.ids(0,"stack"))
        self.assertFalse(any(e.name=="spell_copied" for e in self.k.events))

    def test_copy_event_triggers_magecraft_not_cast_only_triggers(self):
        target=self.target_pending(land_count=4)
        self.add("Storm-Kiln Artist","battlefield",types={"creature"})
        events=[]
        result=self.cast_copy(target,on_copy=lambda ticket:events.extend(
            resolve_reviewed_spell_triggers(
                self.z,0,self.catalog,event="spell_copied",
                spell_types=frozenset({"sorcery"}))))
        self.assertEqual(len(result.created_token_ids),1)
        self.assertEqual(len(events),1)
        self.assertEqual(events[0].card_name,"Storm-Kiln Artist")
        self.assertEqual(len(events[0].created_token_ids),1)
        self.assertEqual(len([e for e in self.k.events if e.name=="spell_copied"]),1)
        self.assertTrue(self.z.assert_consistent())

    def test_target_no_longer_pending_is_not_copyable(self):
        ticket=self.target_pending(land_count=4)
        original=reviewed_token_spell("Strike It Rich",self.catalog["Strike It Rich"])
        self.z.resolve(ticket,effect=lambda k,t:
            create_reviewed_token_batches(self.z,0,original.batches))
        copier=self.add("Reiterate")
        with self.assertRaises(ValueError):
            cast_reiterate_copy(self.z,0,copier,ticket,self.catalog,
                self.mana,casting_window=True)
        self.assertIn(copier,self.z.ids(0,"hand"))

    def test_unreviewed_text_or_copier_identity_refused_before_payment(self):
        ticket=self.target_pending(land_count=4)
        copier=self.add("Reiterate",oracle="false")
        with self.assertRaises(ValueError):
            cast_reiterate_copy(self.z,0,copier,ticket,self.catalog,
                self.mana,casting_window=True)
        self.assertEqual(self.k.get(ticket.object_id).zone,"stack")
        self.assertIn(copier,self.z.ids(0,"hand"))
        self.assertIsNone(reviewed_copy_spell(
            "Reiterate",{**self.catalog["Reiterate"],"oracle_text":"bad"}))

    def test_bounded_pilot_copy_events_have_single_legal_response_pair(self):
        for deck in ("magnus_premium","magnus_budget"):
            for seed in (0,1,2,7,9):
                with self.subTest(deck=deck,seed=seed):
                    run=run_bounded_early_game(deck,seed=seed,turns=6)
                    for turn in run["events"]:
                        casts=[e for e in turn["events"]
                               if e["type"]=="reviewed_spell_copy_cast"]
                        resolutions=[e for e in turn["events"]
                            if e["type"]=="reviewed_spell_copy_resolved"]
                        self.assertLessEqual(len(casts),1)
                        self.assertEqual(len(casts),len(resolutions))
                        for cast,resolved in zip(casts,resolutions):
                            self.assertEqual(cast["card"],"Reiterate")
                            self.assertEqual(cast["copied_spell"],
                                             resolved["copied_spell"])
                            self.assertEqual(resolved["card"],"Reiterate")
                            self.assertEqual(resolved["destination"],
                                             "hand" if cast["buyback"] else "graveyard")
                            self.assertTrue(resolved["created_token_ids"])

    def test_all_six_decks_replay_without_unauthorized_copy(self):
        for key in ("magnus_premium","magnus_budget","wretched_ranks",
                    "mortarion_current","mortarion_ideal","necron_dynasties"):
            with self.subTest(deck=key):
                a=run_bounded_early_game(key,seed=4,turns=4)
                b=run_bounded_early_game(key,seed=4,turns=4)
                self.assertEqual(a,b)
                for row,state in zip(a["events"],a["state_snapshots"]):
                    self.assertEqual(row["library_size"]+row["hand_size"]+
                        len(state["battlefield"])+len(state["graveyard"])+
                        len(state["exile"])+1,100)

if __name__=="__main__":
    unittest.main()
