"""Physical Underworld Breach costs, legal reviewed escape and expiry."""
import unittest

from commander_sim.early_game_runner import _load_live_kernel, run_bounded_early_game
from commander_sim.reviewed_escape import (
    BREACH_ORACLE, BREACH_TEXT, reviewed_breach, breach_sources,
    escape_candidates, cast_reviewed_escape_token_spell,
    sacrifice_breach_at_end_step)
from commander_sim.reviewed_token_spells import TOKEN_SPELLS
from commander_sim.template_resources import TemplateManaService


class PhysicalEscapeTests(unittest.TestCase):
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K()
        self.z=Z(self.k,seed=3)
        self.C=C
        self.raw={
            "Underworld Breach":{
                "oracle_id":BREACH_ORACLE,"oracle_text":BREACH_TEXT,
                "mana_cost":"{1}{R}","layout":"normal",
                "type_line":"Enchantment","colors":["R"]},
            "Mountain":{"type_line":"Basic Land — Mountain"}}
        for name,row in TOKEN_SPELLS.items():
            self.raw[name]={
                "oracle_id":row.oracle_id,"oracle_text":row.oracle_text,
                "mana_cost":row.mana_cost,"layout":"normal",
                "type_line":"Sorcery","colors":["R"]}
        self.mana=TemplateManaService(self.k,self.raw,{"R"},zones=self.z)

    def add(self,name,zone="graveyard",owner=0,oracle=None):
        raw=self.raw.get(name,{})
        t=("land" if name=="Mountain" else
           "enchantment" if name=="Underworld Breach" else "sorcery")
        return self.z.add(self.C(
            oracle or raw.get("oracle_id","fake:"+name),name,
            frozenset({t}),coverage="approx",
            colors=frozenset({"R"}) if t=="sorcery" else None),
            owner,zone)

    def ready(self):
        breach=self.add("Underworld Breach","battlefield")
        source=self.add("Strike It Rich")
        fodder=[self.add("Mountain","graveyard") for _ in range(3)]
        self.add("Mountain","battlefield")
        return breach,source,tuple(fodder)

    def test_escape_consumes_three_other_cards_and_normal_spell_cost(self):
        breach,source,fodder=self.ready()
        preview=escape_candidates(self.z,0,source,self.raw,self.mana)
        self.assertEqual(preview,fodder)
        self.assertEqual(self.z.ids(0,"exile"),())
        events=[]
        answer=cast_reviewed_escape_token_spell(
            self.z,0,source,self.raw,self.mana,exile_ids=fodder,
            sorcery_window=True,on_cast=lambda ticket:events.append(ticket))
        self.assertEqual(answer.exiled_other_ids,fodder)
        self.assertEqual(len(answer.paid_source_ids),1)
        self.assertEqual(len(answer.created_token_ids),1)
        self.assertEqual(self.k.get(answer.graveyard_id).card.name,"Strike It Rich")
        self.assertEqual(len(self.z.ids(0,"exile")),3)
        self.assertTrue(all(self.k.get(i).zone=="exile" for i in self.z.ids(0,"exile")))
        self.assertEqual(len(events),1)
        self.assertEqual(dict(self.k.events[-3].metadata).get("origin"),"graveyard")
        self.assertTrue(self.z.assert_consistent())

    def test_fourth_graveyard_card_is_required_and_source_excluded(self):
        breach=self.add("Underworld Breach","battlefield")
        source=self.add("Strike It Rich")
        fodder=[self.add("Mountain") for _ in range(2)]
        self.add("Mountain","battlefield")
        self.assertEqual(escape_candidates(self.z,0,source,self.raw,self.mana),())
        with self.assertRaises(ValueError):
            cast_reviewed_escape_token_spell(
                self.z,0,source,self.raw,self.mana,exile_ids=(source,*fodder),
                sorcery_window=True)
        self.assertIn(source,self.z.ids(0,"graveyard"))
        self.assertTrue(all(not self.k.get(i).tapped for i in self.z.ids(0,"battlefield")))

    def test_mana_requirements_and_invalid_fodder_are_nonmutating(self):
        breach,source,fodder=self.ready()
        self.k.get(next(i for i in self.z.ids(0,"battlefield")
                            if self.k.get(i).card.name=="Mountain")).tapped=True
        self.assertEqual(escape_candidates(self.z,0,source,self.raw,self.mana),())
        with self.assertRaises(ValueError):
            cast_reviewed_escape_token_spell(
                self.z,0,source,self.raw,self.mana,exile_ids=fodder,
                sorcery_window=True)
        self.assertEqual(len(self.z.ids(0,"graveyard")),4)
        self.assertEqual(self.z.ids(0,"exile"),())

    def test_invalid_source_identity_or_missing_breach_fails_closed(self):
        _,source,fodder=self.ready()
        bad=dict(self.raw["Underworld Breach"])
        bad["oracle_text"]="Unreviewed static effect"
        self.raw["Underworld Breach"]=bad
        self.assertFalse(reviewed_breach("Underworld Breach",bad))
        self.assertEqual(escape_candidates(self.z,0,source,self.raw,self.mana),())
        self.raw["Underworld Breach"]["oracle_text"]=BREACH_TEXT
        self.z.move(next(i for i in self.z.ids(0,"battlefield")
                         if self.k.get(i).card.name=="Underworld Breach"),
                    "graveyard","sacrifice")
        self.assertEqual(escape_candidates(self.z,0,source,self.raw,self.mana),())

    def test_escape_can_recur_only_if_new_fodder_and_mana_exist(self):
        _,source,fodder=self.ready()
        first=cast_reviewed_escape_token_spell(
            self.z,0,source,self.raw,self.mana,exile_ids=fodder,sorcery_window=True)
        self.assertEqual(escape_candidates(
            self.z,0,first.graveyard_id,self.raw,self.mana),())
        self.assertEqual(len(self.z.ids(0,"graveyard")),1)
        self.assertTrue(self.z.assert_consistent())

    def test_breach_sacrificed_at_end_step_and_no_longer_grants_escape(self):
        old,source,fodder=self.ready()
        results=sacrifice_breach_at_end_step(self.z,0,self.raw)
        self.assertEqual(len(results),1)
        self.assertEqual(results[0][0],old)
        self.assertIn(results[0][1],self.z.ids(0,"graveyard"))
        self.assertEqual(escape_candidates(self.z,0,source,self.raw,self.mana),())
        self.assertEqual(sacrifice_breach_at_end_step(self.z,0,self.raw),())
        self.assertTrue(self.z.assert_consistent())

    def test_six_decks_deterministic_with_legal_end_step_limits(self):
        for deck in ("magnus_premium","magnus_budget","wretched_ranks",
                     "mortarion_current","mortarion_ideal","necron_dynasties"):
            with self.subTest(deck=deck):
                a=run_bounded_early_game(deck,seed=8,turns=6)
                b=run_bounded_early_game(deck,seed=8,turns=6)
                self.assertEqual(a,b)
                for turn,state in zip(a["events"],a["state_snapshots"]):
                    casts=[e for e in turn["events"]
                           if e["type"]=="reviewed_escape_cast"]
                    self.assertLessEqual(len(casts),1)
                    self.assertTrue(all(len(e["exiled_other_object_ids"])==3
                                        and e["source_graveyard_id"] not in
                                        e["exiled_other_object_ids"] for e in casts))
                    self.assertEqual(turn["library_size"]+turn["hand_size"]+
                        len(state["battlefield"])+len(state["graveyard"])+
                        len(state["exile"])+1,100)


if __name__=="__main__":
    unittest.main()
