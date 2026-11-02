"""Physical removal/debuff templates preserve targets, life and death triggers."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_death_effects import ReviewedDeathEngine
from commander_sim.reviewed_removal_spells import cast_removal,reviewed_removal

class ReviewedRemovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES if f.key=="mortarion_physical_final")
        cls.catalog={row["deck_name"]:row["card"] for row
                     in json.loads(f.snapshot_path.read_text())["cards"]}
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=24)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.mana=TemplateManaService(self.kernel,self.catalog,
                                      frozenset({"B"}),zones=self.zones)
        self.death=ReviewedDeathEngine(self.zones,self.life,self.catalog)
    def add(self,name,types,zone="battlefield",seat=0,power=2,toughness=2):
        raw=self.catalog.get(name,{})
        return self.zones.add(self.C(raw.get("oracle_id","test:"+name),name,
             frozenset(types),base_power=power,base_toughness=toughness,
             coverage="approx"),seat,zone)
    def lands(self,n):
        for _ in range(n):self.add("Swamp",("land",))
    def cast(self,name,target=None,x=0):
        oid=self.add(name,("sorcery",) if self.catalog[name]["type_line"]=="Sorcery"
                     else ("instant",),"hand")
        return cast_removal(self.zones,self.life,0,oid,self.catalog,
                            frozenset({"B"}),self.mana,
                            target_id=target,x=x,death_engine=self.death)
    def test_infernal_grasp_destroys_physical_creature_and_loses_two(self):
        self.lands(2)
        target=self.add("Enemy",("creature",),seat=1)
        r=self.cast("Infernal Grasp",target)
        self.assertEqual(r.destroyed_count,1)
        self.assertEqual(self.life.total(0),38)
        self.assertTrue(self.zones.assert_consistent())
    def test_bile_blight_applies_name_matched_debuff_to_all(self):
        self.lands(2)
        a=self.add("Enemy",("creature",),seat=1)
        b=self.add("Enemy",("creature",),seat=2)
        keep=self.add("Other",("creature",),seat=1,toughness=5)
        r=self.cast("Bile Blight",a)
        self.assertEqual(r.destroyed_count,2)
        self.assertIn(keep,self.kernel.objects)
        self.assertTrue(self.zones.assert_consistent())
    def test_toxic_deluge_pays_life_and_ignores_indestructible(self):
        self.lands(3)
        enemy=self.add("Enemy",("creature",),seat=1,toughness=2)
        r=self.cast("Toxic Deluge",x=2)
        self.assertEqual(r.destroyed_count,1)
        self.assertEqual(self.life.total(0),38)
        self.assertTrue(self.zones.assert_consistent())
    def test_feed_the_swarm_requires_opponent_and_mana_value(self):
        self.lands(2)
        own=self.add("Own",("creature",))
        with self.assertRaises(ValueError):
            self.cast("Feed the Swarm",own)
        self.assertIsNone(reviewed_removal("Feed the Swarm",
                        dict(self.catalog["Feed the Swarm"],oracle_text="Invalid")))
if __name__=="__main__":unittest.main()
