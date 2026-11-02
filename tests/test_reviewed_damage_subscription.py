"""Source-reviewed damage subscriptions use the authoritative creature-damage log."""
import json
import unittest

from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_entry_choices import (
    reviewed_entry_choice,set_reviewed_entry_choice)
from commander_sim.reviewed_reactive_triggers import ReactiveTriggerEngine
from commander_sim.reviewed_death_effects import ReviewedDeathEngine
from commander_sim.composed_abilities import ComposedAbilityEngine


class DamageSubscriptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES
               if f.key=="mortarion_physical_final")
        cls.catalog={e["deck_name"]:e["card"] for e in
                     json.loads(f.snapshot_path.read_text())["cards"]}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=88)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.mana=TemplateManaService(
            self.kernel,self.catalog,frozenset({"B"}),zones=self.zones)
        self.death=ReviewedDeathEngine(self.zones,self.life,self.catalog)
        self.comp=ComposedAbilityEngine(
            self.zones,self.life,self.catalog,self.mana,self.death)
        self.reactive=ReactiveTriggerEngine(
            self.zones,self.life,self.catalog)

    def add(self,name,types=("creature",),power=2,toughness=2,keywords=()):
        raw=self.catalog.get(name,{})
        return self.zones.add(self.C(
            raw.get("oracle_id","test:"+name),name,
            frozenset(types),base_power=power,base_toughness=toughness,
            keywords=frozenset(keywords),coverage="approx"),0,"battlefield")

    def doll(self):
        return self.add("Stuffy Doll",power=0,toughness=1,
                        keywords=("indestructible",))

    def test_stuffy_doll_damage_targets_physical_chosen_player(self):
        doll=self.doll()
        set_reviewed_entry_choice(self.zones,doll,self.catalog,player=2)
        pest=self.add("Pestilence",types=("enchantment",))
        self.add("Swamp",types=("land",))
        self.assertIsNotNone(self.comp.activate(pest,turn=1))
        outcomes=self.reactive.resolve()
        self.assertEqual(self.life.total(0),39)
        self.assertEqual(self.life.total(1),39)
        self.assertEqual(self.life.total(2),38)
        self.assertEqual(self.life.total(3),39)
        self.assertTrue(any(x.source_name=="Stuffy Doll"
                            and x.quantity==1 for x in outcomes))
        self.assertIn(doll,self.kernel.objects)
        self.assertTrue(self.zones.assert_consistent())

    def test_tapped_stuffy_doll_ping_reuses_composed_damage_operation(self):
        doll=self.doll()
        set_reviewed_entry_choice(self.zones,doll,self.catalog,player=3)
        self.assertIsNotNone(self.comp.activate(doll,turn=1,tap_ready=True))
        self.assertTrue(self.kernel.get(doll).tapped)
        events=self.reactive.resolve()
        self.assertEqual(len([e for e in events
                              if e.source_name=="Stuffy Doll"]),1)
        self.assertEqual(self.life.total(3),39)
        self.assertIsNone(self.comp.activate(doll,turn=1))
        self.assertEqual(self.reactive.resolve(),())
        self.assertTrue(self.zones.assert_consistent())

    def test_damage_without_mandatory_entry_choice_fails_closed(self):
        doll=self.doll()
        self.kernel.mark_damage(doll,1)
        with self.assertRaises(ValueError):
            self.reactive.resolve()

    def test_pinned_entry_choice_rejects_wrong_identity(self):
        self.assertIsNotNone(reviewed_entry_choice(
            "Stuffy Doll",self.catalog["Stuffy Doll"]))
        impostor=self.doll()
        self.kernel.get(impostor).card=self.C(
            "unreviewed","Stuffy Doll",frozenset({"creature"}),
            base_power=0,base_toughness=1,
            keywords=frozenset({"indestructible"}),coverage="approx")
        with self.assertRaises(ValueError):
            set_reviewed_entry_choice(self.zones,impostor,self.catalog,player=1)


if __name__=="__main__":
    unittest.main()
