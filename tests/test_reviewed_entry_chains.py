"""Bounded, source-pinned entry chains after physical graveyard recursion."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_entry_chains import (
    resolve_reviewed_entry_chain, bounded_entry_choice)


class EntryChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for fixture in FIXTURES:
            for item in json.loads(fixture.snapshot_path.read_text())["cards"]:
                cls.catalog.setdefault(item["deck_name"],item["card"])

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K()
        self.z=Z(self.k,seed=19)
        self.C=C
        self.life=KernelLife(self.k)

    def add(self,name,zone,*,types=("creature",),card_id=None,seat=0):
        raw=self.catalog.get(name,{})
        return self.z.add(self.C(card_id or raw.get("oracle_id","test:"+name),
                   name,frozenset(types),coverage="approx"),seat,zone)

    def reanimate(self,name,*,types=("creature",)):
        source=self.add(name,"graveyard",types=types)
        return self.z.move(source,"battlefield","resolve")

    def entry(self,ids,*,budget=12):
        return resolve_reviewed_entry_chain(
            self.z,self.life,ids,self.catalog,max_triggers=budget)

    def test_scarab_reanimation_chain_uses_shared_target_policy_and_real_tokens(self):
        source=self.reanimate("Canoptek Scarab Swarm",types=("artifact","creature"))
        self.add("Own artifact","graveyard",types=("artifact",))
        self.add("Enemy artifact","graveyard",types=("artifact",),seat=2)
        self.add("Enemy land","graveyard",types=("land",),seat=2)
        answer=self.entry((source,))
        self.assertTrue(answer.complete)
        self.assertEqual(len(answer.resolved),1)
        result=answer.resolved[0]
        self.assertEqual(result.target_seat,2)
        self.assertEqual(len(result.exiled_ids),2)
        self.assertEqual(len(result.token_ids),2)
        self.assertEqual(len(self.z.ids(0,"graveyard")),1)
        self.assertTrue(self.z.assert_consistent())

    def test_grave_titan_reanimation_triggers_reviewed_token_creation(self):
        source=self.reanimate("Grave Titan")
        answer=self.entry((source,))
        self.assertTrue(answer.complete)
        self.assertEqual(len(answer.resolved),1)
        self.assertEqual(answer.resolved[0].operation,"zombie_two")
        self.assertEqual(len(answer.resolved[0].token_ids),2)
        self.assertTrue(all(self.k.get(i).token
                            for i in answer.resolved[0].token_ids))
        self.assertTrue(self.z.assert_consistent())

    def test_triarch_praetorian_graveyard_only_draw_two_and_lose_two(self):
        source=self.reanimate("Triarch Praetorian",
                              types=("artifact","creature"))
        for i in range(3):
            self.add("Filler"+str(i),"library")
        answer=self.entry((source,))
        self.assertTrue(answer.complete)
        self.assertEqual(len(answer.resolved),1)
        self.assertEqual(answer.resolved[0].operation,"draw_lose_two")
        self.assertEqual(len(answer.resolved[0].drawn_ids),2)
        self.assertEqual(self.life.total(0),38)
        self.assertTrue(self.z.assert_consistent())

    def test_technomancer_reanimation_chains_into_flayed_one_mill(self):
        technomancer=self.add("Technomancer","hand",
                               types=("artifact","creature"))
        source=self.z.move(technomancer,"battlefield","resolve")
        self.add("Flayed One","graveyard",types=("artifact","creature"))
        self.add("Lychguard","graveyard",types=("artifact","creature"))
        for i in range(7):
            self.add("Filler"+str(i),"library")
        answer=self.entry((source,))
        names=[r.source_name for r in answer.resolved]
        self.assertEqual(names,["Technomancer","Flayed One"])
        self.assertTrue(answer.complete)
        self.assertEqual(len(answer.resolved[0].milled_ids),3)
        self.assertEqual(len(answer.resolved[1].milled_ids),3)
        self.assertEqual(len(self.z.ids(0,"library")),1)
        self.assertTrue(self.z.assert_consistent())

    def test_limit_exposes_pending_mandatory_trigger_instead_of_claiming_complete(self):
        technomancer=self.add("Technomancer","hand",
                               types=("artifact","creature"))
        source=self.z.move(technomancer,"battlefield","resolve")
        self.add("Flayed One","graveyard",types=("artifact","creature"))
        self.add("Lychguard","graveyard",types=("artifact","creature"))
        for i in range(7):
            self.add("Filler"+str(i),"library")
        answer=self.entry((source,),budget=1)
        self.assertFalse(answer.complete)
        self.assertEqual([r.source_name for r in answer.resolved],["Technomancer"])
        self.assertTrue(answer.deferred_ids)

    def test_fabricate_choice_is_host_supplied_not_magic_name_parser(self):
        source=self.reanimate("Marionette Apprentice")
        answer=self.entry((source,))
        self.assertTrue(answer.complete)
        self.assertEqual(len(answer.resolved),1)
        self.assertEqual(answer.resolved[0].operation,"fabricate_one")
        self.assertEqual(len(answer.resolved[0].token_ids),1)
        self.assertTrue(self.z.assert_consistent())

    def test_identity_spoof_and_unreviewed_source_do_not_resolve_effect(self):
        unreviewed=self.reanimate("Unknown Creature")
        spoof=self.add("Flayed One","graveyard",
                       card_id="wrong:oracle",types=("artifact","creature"))
        spoof=self.z.move(spoof,"battlefield","resolve")
        for i in range(3):
            self.add("Filler"+str(i),"library")
        answer=self.entry((unreviewed,spoof))
        self.assertEqual(answer.resolved,())
        self.assertEqual(set(answer.unreviewed_ids),{unreviewed,spoof})
        self.assertEqual(len(self.z.ids(0,"library")),3)
        self.assertTrue(self.z.assert_consistent())

    def test_entry_chain_requires_finite_budget_and_matching_life_kernel(self):
        with self.assertRaises(ValueError):
            self.entry((),budget=0)
        with self.assertRaises(ValueError):
            self.entry((),budget=101)


if __name__=="__main__":
    unittest.main()
