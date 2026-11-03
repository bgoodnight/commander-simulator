"""Reviewed paid attack recursion and opponent sacrifice use physical zones."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_attack_zones import (
    reviewed_attack_zone, resolve_attack_zone)


class AttackZoneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for fixture in FIXTURES:
            for row in json.loads(fixture.snapshot_path.read_text())["cards"]:
                cls.catalog.setdefault(row["deck_name"],row["card"])

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K();self.z=Z(self.k,seed=91);self.C=C
        self.life=KernelLife(self.k)
        self.mana=TemplateManaService(
            self.k,self.catalog,frozenset({"B"}),zones=self.z)

    def add(self,name,zone="battlefield",*,types=("creature",),seat=0,
            supertypes=(),identity=None):
        raw=self.catalog.get(name,{})
        return self.z.add(self.C(
            identity or raw.get("oracle_id","test:"+name),
            name,frozenset(types),supertypes=frozenset(supertypes),
            base_power=3,base_toughness=4,coverage="approx"),seat,zone)

    def run_attack(self,source,**kwargs):
        return resolve_attack_zone(
            self.z,self.life,self.catalog,source,mana_service=self.mana,**kwargs)

    def test_taskmaster_requires_payment_and_moves_one_actual_creature(self):
        attack=self.add("Eternal Taskmaster")
        target=self.add("Target",zone="graveyard")
        other=self.add("Spell",zone="graveyard",types=("instant",))
        self.assertIsNone(self.run_attack(attack).returned_id)
        self.assertIn(target,self.z.ids(0,"graveyard"))
        for _ in range(3):self.add("Swamp",types=("land",))
        result=self.run_attack(attack)
        self.assertEqual(result.operation,"paid_graveyard_creature_to_hand")
        self.assertEqual(self.k.get(result.returned_id).card.name,"Target")
        self.assertIn(other,self.z.ids(0,"graveyard"))
        self.assertNotIn(target,self.k.objects)
        self.assertTrue(self.z.assert_consistent())

    def test_taskmaster_no_target_leaves_mana_untapped(self):
        attacker=self.add("Eternal Taskmaster")
        lands=[self.add("Swamp",types=("land",)) for _ in range(3)]
        out=self.run_attack(attacker)
        self.assertIsNone(out.returned_id)
        self.assertTrue(all(not self.k.get(x).tapped for x in lands))

    def test_shard_requires_opponent_choice_from_own_board(self):
        shard=self.add("Shard of the Void Dragon")
        a=self.add("Seat one artifact",types=("artifact",),seat=1)
        b=self.add("Seat two enchantment",types=("enchantment",),seat=2)
        self.add("Seat two land",types=("land",),seat=2)
        c=self.add("Seat three land",types=("land",),seat=3)
        out=self.run_attack(shard)
        self.assertEqual(set(out.sacrificed_old_ids),{a,b})
        self.assertEqual(out.skipped_seats,(3,))
        self.assertNotIn(a,self.k.objects)
        self.assertNotIn(b,self.k.objects)
        self.assertIn(c,self.k.objects)
        self.assertTrue(self.z.assert_consistent())

    def test_shard_rejects_invalid_choices_without_partial_sacrifice(self):
        shard=self.add("Shard of the Void Dragon")
        a=self.add("Seat one",seat=1)
        b=self.add("Seat two",seat=2)
        with self.assertRaises(ValueError):
            self.run_attack(shard,choices={1:b})
        self.assertIn(a,self.k.objects)
        self.assertIn(b,self.k.objects)
        self.assertTrue(self.z.assert_consistent())

    def test_shard_commander_replacement_refuses_before_mutation(self):
        shard=self.add("Shard of the Void Dragon")
        a=self.add("Seat one",seat=1)
        self.add("Other commander",seat=2,supertypes=("commander",))
        with self.assertRaises(NotImplementedError):
            self.run_attack(shard)
        self.assertIn(a,self.k.objects)
        self.assertTrue(self.z.assert_consistent())

    def test_unverified_identity_and_revision_never_execute(self):
        fake=self.add("Eternal Taskmaster",identity="not-verified")
        self.add("Target",zone="graveyard")
        for _ in range(3):self.add("Swamp",types=("land",))
        self.assertIsNone(self.run_attack(fake))
        raw=dict(self.catalog["Eternal Taskmaster"],oracle_text="changed")
        self.assertIsNone(reviewed_attack_zone("Eternal Taskmaster",raw))


if __name__=="__main__":
    unittest.main()
