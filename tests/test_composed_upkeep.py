"""Shared upkeep, amass and opponent-death effects on authoritative zones."""
import json
import unittest

from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_death_effects import ReviewedDeathEngine
from commander_sim.composed_abilities import ComposedAbilityEngine


class UpkeepComposedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES
               if f.key=="mortarion_physical_final")
        cls.catalog={e["deck_name"]:e["card"] for e
                     in json.loads(f.snapshot_path.read_text())["cards"]}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=41)
        self.Card=C
        self.life=KernelLife(self.kernel)
        self.mana=TemplateManaService(self.kernel,self.catalog,
                                      frozenset({"B"}),zones=self.zones)
        self.death=ReviewedDeathEngine(self.zones,self.life,self.catalog)
        self.abilities=ComposedAbilityEngine(
            self.zones,self.life,self.catalog,self.mana,self.death)

    def add(self,name,types=("creature",),seat=0,power=2,toughness=2,
            oracle=None):
        raw=self.catalog.get(name,{})
        return self.zones.add(self.Card(
            oracle or raw.get("oracle_id","test:"+name),name,
            frozenset(types),base_power=power,base_toughness=toughness,
            coverage="approx"),seat,"battlefield")

    def test_amass_creates_one_army_then_adds_counters(self):
        self.add("Dreadhorde Invasion",("enchantment",))
        first=self.abilities.upkeep(active_seat=0,turn=1)
        self.assertEqual(len(first),1)
        self.assertEqual(self.life.total(0),39)
        self.assertEqual(len(first[0].created_ids),1)
        army=self.kernel.get(first[0].created_ids[0])
        self.assertEqual(army.power,1)
        self.assertTrue({"Army","Zombie"} <= set(army.subtypes))
        self.assertEqual(self.abilities.upkeep(active_seat=0,turn=1),())
        second=self.abilities.upkeep(active_seat=0,turn=2)
        self.assertEqual(second[0].created_ids,())
        self.assertEqual(army.power,2)
        self.assertEqual(self.life.total(0),38)
        self.assertTrue(self.zones.assert_consistent())

    def test_plague_spitter_upkeep_uses_global_damage_and_death(self):
        self.add("Plague Spitter",toughness=2)
        enemy=self.add("Enemy Body",seat=1,toughness=1)
        result=self.abilities.upkeep(active_seat=0,turn=1)
        self.assertEqual(result[0].deaths,0)  # No registered death trigger source.
        self.assertNotIn(enemy,self.kernel.objects)
        self.assertEqual([self.life.total(i) for i in range(4)],[39]*4)
        self.assertTrue(self.zones.assert_consistent())

    def test_sangromancer_gain_is_shared_opponent_creature_death_rule(self):
        self.add("Sangromancer",power=3,toughness=4)
        self.add("Pestilence",types=("enchantment",))
        self.add("Enemy",seat=1,toughness=1)
        for _ in range(2):self.add("Swamp",types=("land",))
        pest=next(o.object_id for o in self.kernel.on_battlefield()
                  if o.card.name=="Pestilence")
        result=self.abilities.activate(pest,turn=1)
        self.assertEqual(result.deaths,1)
        self.assertEqual(self.life.total(0),42)
        self.assertTrue(self.zones.assert_consistent())

    def test_unreviewed_upkeep_card_is_inert(self):
        self.add("Dreadhorde Invasion",types=("enchantment",),
                 oracle="wrong-source")
        self.assertEqual(self.abilities.upkeep(active_seat=0,turn=1),())
        self.assertEqual(self.life.total(0),40)


if __name__=="__main__":
    unittest.main()
