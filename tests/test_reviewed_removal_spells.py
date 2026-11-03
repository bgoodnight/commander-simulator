"""Physical removal/debuff templates preserve targets, life and death triggers."""
import json
import unittest
from commander_sim.deck_fixtures import FIXTURES,EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_death_effects import ReviewedDeathEngine
from commander_sim.reviewed_removal_spells import (
    cast_removal,reviewed_removal,valid_removal_target)
from commander_sim.resource_pilot import choose_reviewed_removal

class ReviewedRemovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for fixture in (*FIXTURES,*EXPERIMENTAL_FIXTURES):
            cls.catalog.update({row["deck_name"]:row["card"] for row
                in json.loads(fixture.snapshot_path.read_text())["cards"]})
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
             frozenset(types),subtypes=frozenset({"Swamp"}) if name=="Swamp" else frozenset(),
             base_power=power,base_toughness=toughness,
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
    def test_go_for_the_throat_excludes_artifact_creatures_for_all_players(self):
        self.lands(2)
        artifact=self.add("Artifact attacker",("artifact","creature"),seat=1)
        ordinary=self.add("Normal attacker",("creature",),seat=1,power=4)
        self.add("Friendly nonartifact",("creature",),seat=0)
        rule=reviewed_removal("Go for the Throat",self.catalog["Go for the Throat"])
        self.assertIsNotNone(rule)
        self.assertFalse(valid_removal_target(self.zones,0,rule,artifact))
        self.assertTrue(valid_removal_target(self.zones,0,rule,ordinary))
        self.assertEqual(choose_reviewed_removal(
            self.zones,0,self.life,rule),(ordinary,0))
        with self.assertRaises(ValueError):
            self.cast("Go for the Throat",artifact)
        result=self.cast("Go for the Throat",ordinary)
        self.assertEqual(result.destroyed_count,1)
        self.assertIn(artifact,self.kernel.objects)
        self.assertNotIn(ordinary,self.kernel.objects)
        self.assertTrue(self.zones.assert_consistent())
        self.assertIsNone(reviewed_removal("Go for the Throat",
            dict(self.catalog["Go for the Throat"],oracle_text="Wrong")))

    def test_withering_torment_targets_enchantment_and_loses_two_life(self):
        self.lands(3)
        target=self.add("Opponent Aura",("enchantment",),seat=1)
        rule=reviewed_removal("Withering Torment",self.catalog["Withering Torment"])
        self.assertIsNotNone(rule)
        self.assertTrue(valid_removal_target(self.zones,0,rule,target))
        # The generic pilot must see noncreature engine pieces as targets.
        self.assertEqual(choose_reviewed_removal(
            self.zones,0,self.life,rule),(target,0))
        result=self.cast("Withering Torment",target)
        self.assertEqual(result.destroyed_count,1)
        self.assertEqual(self.life.total(0),38)
        self.assertNotIn(target,self.kernel.objects)
        self.assertIsNone(reviewed_removal("Withering Torment",
                          dict(self.catalog["Withering Torment"],
                               oracle_id="mismatched-source")))
        self.assertTrue(self.zones.assert_consistent())

    def test_mutilate_uses_actual_swamp_subtypes_not_global_land_count(self):
        self.lands(4)
        self.add("Island",("land",))
        self.add("Swamp",("land",),seat=1)
        a=self.add("Small foe",("creature",),seat=1,toughness=3)
        b=self.add("Big foe",("creature",),seat=2,toughness=6)
        ally=self.add("Friendly",("creature",),seat=0,toughness=5)
        rule=reviewed_removal("Mutilate",self.catalog["Mutilate"])
        self.assertIsNotNone(rule)
        # Mutilate uses four controlled Swamps and does not require a target.
        result=self.cast("Mutilate")
        self.assertIn(a,result.affected_ids)
        self.assertNotIn(a,self.kernel.objects)
        self.assertIn(b,self.kernel.objects)
        self.assertEqual(self.kernel.get(b).toughness,2)
        self.assertEqual(self.kernel.get(ally).toughness,1)
        self.assertEqual(self.life.total(0),40)
        self.kernel.cleanup()
        self.assertEqual(self.kernel.get(b).toughness,6)
        self.assertTrue(self.zones.assert_consistent())

    def test_consuming_corruption_pays_sources_damages_creature_and_gains_life(self):
        self.lands(3)
        self.add("Swamp",("land",),seat=1)
        self.add("Island",("land",))
        target=self.add("Enemy",("creature",),seat=1,toughness=2)
        self.life.lose(0,8)
        rule=reviewed_removal("Consuming Corruption",
                              self.catalog["Consuming Corruption"])
        self.assertIsNotNone(rule)
        self.assertIsNone(reviewed_removal("Consuming Corruption",
                    dict(self.catalog["Consuming Corruption"],mana_cost="{B}")))
        self.assertEqual(choose_reviewed_removal(
            self.zones,0,self.life,rule),(target,0))
        result=self.cast("Consuming Corruption",target)
        self.assertEqual(result.destroyed_count,1)
        self.assertNotIn(target,self.kernel.objects)
        self.assertEqual(self.life.total(0),35)
        self.assertTrue(self.zones.assert_consistent())

    def test_swamp_scaled_damage_zero_without_swamps(self):
        self.add("Island",("land",))
        enemy=self.add("Enemy",("creature",),seat=1,toughness=2)
        rule=reviewed_removal("Consuming Corruption",self.catalog["Consuming Corruption"])
        self.assertIsNone(choose_reviewed_removal(self.zones,0,self.life,rule))
        self.assertIsNone(self.cast("Consuming Corruption",enemy))
        self.assertIn(enemy,self.kernel.objects)
        self.assertTrue(self.zones.assert_consistent())

if __name__=="__main__":unittest.main()
