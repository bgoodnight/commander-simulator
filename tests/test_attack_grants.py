"""Attack-grant effect belongs to one reviewed source, not a hardcoded unit."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.reviewed_attack_triggers import resolve_attack_grants

class AttackGrantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES if f.key=="mortarion_physical_final")
        cls.catalog={x["deck_name"]:x["card"] for x in
                     json.loads(f.snapshot_path.read_text())["cards"]}
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K();self.z=Z(self.k,seed=1);self.C=C
    def add(self,name,types,subtypes=(),power=0,token=False):
        raw=self.catalog.get(name,{})
        return self.z.add(self.C(raw.get("oracle_id","test:"+name),name,
            frozenset(types),subtypes=frozenset(subtypes),
            base_power=power,base_toughness=8,coverage="approx"),
            0,"battlefield",token=token)
    def test_six_power_zombie_token_gets_lifelink_until_cleanup(self):
        self.add("Dreadhorde Invasion",("enchantment",))
        zombie=self.add("Zombie Army",("creature",),("Zombie","Army"),6,True)
        self.assertEqual(len(resolve_attack_grants(
            self.k,self.catalog,zombie)),1)
        self.assertIn("lifelink",self.k.get(zombie).keywords)
        self.k.cleanup()
        self.assertNotIn("lifelink",self.k.get(zombie).keywords)
    def test_small_zombie_or_nontoken_do_not_receive_attack_bonus(self):
        self.add("Dreadhorde Invasion",("enchantment",))
        small=self.add("Small Zombie",("creature",),("Zombie",),5,True)
        nontoken=self.add("Big Zombie",("creature",),("Zombie",),7,False)
        self.assertEqual(resolve_attack_grants(self.k,self.catalog,small),())
        self.assertEqual(resolve_attack_grants(self.k,self.catalog,nontoken),())
if __name__=="__main__":
    unittest.main()
