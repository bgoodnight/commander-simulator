"""Parameterized paid graveyard abilities used by Zombie and Necron decks."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_lands import reviewed_land
from commander_sim.reviewed_utility_activations import (
    UtilityRule, reviewed_utility, activate_utility)
from commander_sim.resource_pilot import choose_utility_activation


class SharedRecursionActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for fixture in FIXTURES:
            for item in json.loads(fixture.snapshot_path.read_text())["cards"]:
                cls.catalog.setdefault(item["deck_name"],item["card"])

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K()
        self.z=Z(self.k,seed=43)
        self.C=C
        self.life=KernelLife(self.k)
        self.mana=TemplateManaService(self.k,self.catalog,frozenset({"B"}),
                                      zones=self.z)

    def add(self,name,zone="battlefield",*,types=("creature",),
            subtypes=(),supertypes=(),card_id=None,seat=0):
        row=self.catalog.get(name,{})
        return self.z.add(self.C(card_id or row.get("oracle_id","test:"+name),
             name,frozenset(types),subtypes=frozenset(subtypes),
             supertypes=frozenset(supertypes),coverage="approx"),seat,zone)

    def swamps(self,n):
        return [self.add("Swamp",types=("land",)) for _ in range(n)]

    def use(self,source,**kwargs):
        return activate_utility(self.z,self.life,0,source,self.catalog,
                                self.mana,frozenset({"B"}),**kwargs)

    def test_persistent_specimen_reuses_same_self_resurrection_as_skeleton(self):
        self.swamps(3)
        src=self.add("Persistent Specimen",zone="graveyard")
        out=self.use(src)
        self.assertEqual(out.operation,"self_to_battlefield_tapped")
        restored=self.k.get(out.new_object_ids[0])
        self.assertEqual(restored.card.name,"Persistent Specimen")
        self.assertTrue(restored.tapped)
        self.assertNotIn(src,self.k.objects)
        self.assertTrue(self.z.assert_consistent())

    def test_lord_of_undead_requires_tap_readiness_and_a_zombie(self):
        source=self.add("Lord of the Undead",subtypes=("Zombie",))
        other=self.add("Human",zone="graveyard",subtypes=("Human",))
        target=self.add("Zombie",zone="graveyard",subtypes=("Zombie",))
        self.swamps(2)
        self.assertIsNone(self.use(source,target_id=target))
        self.assertFalse(self.k.get(source).tapped)
        with self.assertRaises(ValueError):
            self.use(source,target_id=other,tap_ready=True)
        self.assertFalse(self.k.get(source).tapped)
        out=self.use(source,target_id=target,tap_ready=True)
        self.assertIsNotNone(out)
        self.assertTrue(self.k.get(source).tapped)
        self.assertEqual(self.k.get(out.new_object_ids[0]).zone,"hand")
        self.assertEqual(self.k.get(out.new_object_ids[0]).card.name,"Zombie")
        self.assertIn(other,self.z.ids(0,"graveyard"))
        self.assertTrue(self.z.assert_consistent())

    def test_memorial_folly_source_is_excluded_from_mana_and_sacrifices(self):
        source=self.add("Memorial to Folly",types=("land",))
        zombie=self.add("Zombie",zone="graveyard")
        self.swamps(2)
        self.assertIsNone(self.use(source,target_id=zombie))
        self.assertEqual(self.k.get(source).zone,"battlefield")
        third=self.swamps(1)
        out=self.use(source,target_id=zombie)
        self.assertIsNotNone(out)
        self.assertEqual(out.operation,"creature_to_hand")
        self.assertEqual(len(out.new_object_ids),2)
        self.assertEqual(self.k.get(out.new_object_ids[0]).zone,"graveyard")
        self.assertEqual(self.k.get(out.new_object_ids[-1]).zone,"hand")
        self.assertNotIn(source,self.k.objects)
        self.assertTrue(self.z.assert_consistent())
        self.assertEqual(reviewed_land("Memorial to Folly",
                   self.catalog["Memorial to Folly"],frozenset({"B"}))
                   .enters_tapped(0),True)

    def test_lychguard_returns_all_and_only_legendary_creatures(self):
        source=self.add("Lychguard",types=("artifact","creature"))
        first=self.add("First legend",zone="graveyard",
                       supertypes=("legendary",))
        second=self.add("Second legend",zone="graveyard",
                        supertypes=("legendary",))
        ordinary=self.add("Ordinary",zone="graveyard")
        spell=self.add("Legendary enchantment",zone="graveyard",
                       types=("enchantment",),supertypes=("legendary",))
        self.swamps(4)
        out=self.use(source)
        self.assertEqual(out.operation,"all_legendary_creatures_to_hand")
        self.assertNotIn(source,self.k.objects)
        self.assertEqual(len(out.new_object_ids),3)
        self.assertEqual(
            {self.k.get(i).card.name for i in out.new_object_ids[1:]},
            {"First legend","Second legend"})
        self.assertEqual(self.k.get(out.new_object_ids[0]).zone,"graveyard")
        self.assertIn(ordinary,self.z.ids(0,"graveyard"))
        self.assertIn(spell,self.z.ids(0,"graveyard"))
        self.assertNotIn(first,self.k.objects)
        self.assertNotIn(second,self.k.objects)
        self.assertTrue(self.z.assert_consistent())

    def test_lychguard_does_not_retrieve_opponent_legendary_creatures(self):
        source=self.add("Lychguard",types=("artifact","creature"))
        enemy=self.add("Enemy legend",zone="graveyard",seat=1,
                       supertypes=("legendary",))
        self.swamps(4)
        out=self.use(source)
        self.assertEqual(len(out.new_object_ids),1)
        self.assertIn(enemy,self.z.ids(1,"graveyard"))
        self.assertTrue(self.z.assert_consistent())

    def test_source_identity_and_utility_types_fail_closed(self):
        for name in ("Lychguard","Persistent Specimen","Lord of the Undead",
                     "Memorial to Folly"):
            row=self.catalog[name]
            self.assertIsNotNone(reviewed_utility(name,row),name)
            invalid=dict(row,oracle_id="00000000-0000-4000-8000-000000000000")
            self.assertIsNone(reviewed_utility(name,invalid))
        with self.assertRaises(ValueError):
            UtilityRule("id","text","battlefield","{B}","draw",
                        tap_creature=True)
        with self.assertRaises(ValueError):
            UtilityRule("id","text","battlefield","{B}",
                        "all_legendary_creatures_to_hand",
                        target_supertypes=frozenset({"legendary"}),
                        target_subtypes=frozenset({"Zombie"}))

    def test_pilot_does_not_tap_summoning_sick_lord(self):
        lord=self.add("Lord of the Undead",subtypes=("Zombie",))
        corpse=self.add("Zombie corpse",zone="graveyard",
                        subtypes=("Zombie",))
        self.swamps(2)
        option=choose_utility_activation(
            self.z,0,self.life,self.mana,self.catalog,
            hand_cast_reviewed=lambda obj: True,
            tap_ready=lambda obj: False)
        self.assertIsNone(option)
        option=choose_utility_activation(
            self.z,0,self.life,self.mana,self.catalog,
            hand_cast_reviewed=lambda obj: True,
            tap_ready=lambda obj: True)
        self.assertEqual(option,(lord,corpse))


if __name__=="__main__":
    unittest.main()
