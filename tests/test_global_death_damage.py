"""Reactive global damage from a dying source is composed and nonduplicating."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_death_effects import (
    ReviewedDeathEngine,capture_battlefield)

class GlobalDeathDamageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES if f.key=="mortarion_physical_final")
        cls.catalog={row["deck_name"]:row["card"] for row in
                     json.loads(f.snapshot_path.read_text())["cards"]}
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K();self.z=Z(self.k,seed=11);self.C=C
        self.life=KernelLife(self.k)
        self.deaths=ReviewedDeathEngine(self.z,self.life,self.catalog)
    def add(self,name,power=2,toughness=2,seat=0):
        raw=self.catalog.get(name,{})
        return self.z.add(self.C(raw.get("oracle_id","test:"+name),name,
            frozenset({"creature"}),base_power=power,base_toughness=toughness,
            coverage="approx"),seat,"battlefield")
    def test_spitter_death_deals_all_player_and_creature_damage(self):
        source=self.add("Plague Spitter",2,2)
        small=self.add("Small",1,1,seat=2)
        before=capture_battlefield(self.k)
        at=len(self.k.moves)
        self.z.move(source,"graveyard","destroy")
        r=self.deaths.resolve_deaths(before,move_index=at,turn=2)
        self.assertTrue(any(o.source_name=="Plague Spitter" for o in r))
        self.assertNotIn(small,self.k.objects)
        self.assertTrue(all(self.life.total(i)==39 for i in range(4)))
        self.assertTrue(self.z.assert_consistent())
    def test_two_spitters_dying_together_deal_two_global_damage_but_once_each(self):
        a=self.add("Plague Spitter",2,2)
        b=self.add("Plague Spitter",2,2)
        self.add("Body",2,2,seat=1)
        before=capture_battlefield(self.k)
        at=len(self.k.moves)
        self.z.move(a,"graveyard","destroy")
        self.z.move(b,"graveyard","destroy")
        r=self.deaths.resolve_deaths(before,move_index=at,turn=1)
        self.assertEqual(sum(o.source_name=="Plague Spitter" for o in r),2)
        self.assertTrue(all(self.life.total(i)==38 for i in range(4)))
        self.assertEqual(self.deaths.resolve_deaths(before,move_index=at,turn=1),())
        self.assertTrue(self.z.assert_consistent())
if __name__=="__main__":
    unittest.main()
