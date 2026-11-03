"""Mortarion-derived upkeep counter mechanics reuse physical counter/death state."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_death_effects import ReviewedDeathEngine
from commander_sim.reviewed_phase_effects import (
    ReviewedPhaseEngine, reviewed_phase_permanent, reviewed_phase_creature)


class NegativeCounterPhaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for fixture in FIXTURES:
            for item in json.loads(fixture.snapshot_path.read_text())["cards"]:
                cls.catalog.setdefault(item["deck_name"],item["card"])

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K();self.z=Z(self.k,seed=33);self.C=C
        self.life=KernelLife(self.k)
        self.deaths=ReviewedDeathEngine(self.z,self.life,self.catalog)
        self.engine=ReviewedPhaseEngine(
            self.z,self.life,self.catalog,death_engine=self.deaths)

    def add(self,name,*,types=("creature",),seat=0,colors=None,
            power=2,toughness=2,keywords=(),identity=None):
        raw=self.catalog.get(name,{})
        return self.z.add(self.C(
            identity or raw.get("oracle_id","test:"+name),name,
            frozenset(types),base_power=power,base_toughness=toughness,
            keywords=frozenset(keywords),
            colors=frozenset(colors) if colors is not None else None,
            coverage="approx"),seat,"battlefield")

    def upkeep(self,round_id=1,choices=None):
        return self.engine.resolve(phase="upkeep",active_seat=0,
                                   round_id=round_id,choices=choices)

    def test_banshee_places_counters_on_each_verified_nonblack_creature(self):
        banshee=self.add("Midnight Banshee",colors="B",toughness=4)
        white=self.add("White creature",colors="W",seat=1)
        colorless=self.add("Colorless creature",colors="")
        black=self.add("Black creature",colors="B",seat=2)
        unknown=self.add("Unknown color",colors=None,seat=3)
        out=self.upkeep()
        self.assertEqual(len(out),1)
        self.assertEqual(set(out[0].countered_ids),{white,colorless})
        self.assertEqual(self.k.get(white).counters["-1/-1"],1)
        self.assertEqual(self.k.get(colorless).counters["-1/-1"],1)
        for oid in (banshee,black,unknown):
            self.assertEqual(self.k.get(oid).counters["-1/-1"],0)
        self.assertEqual(self.upkeep(),())
        self.assertTrue(self.z.assert_consistent())

    def test_banshee_counter_kills_one_toughness_and_observes_death(self):
        self.add("Midnight Banshee",colors="B",toughness=5)
        victim=self.add("Fragile",colors="W",seat=1,toughness=1)
        self.upkeep()
        self.assertNotIn(victim,self.k.objects)
        self.assertEqual(len(self.z.ids(1,"graveyard")),1)
        self.assertTrue(self.z.assert_consistent())

    def test_crumbling_ashes_destroys_existing_countered_creature(self):
        ashes=self.add("Crumbling Ashes",types=("enchantment",))
        victim=self.add("Target",seat=1)
        safe=self.add("Safe",seat=2)
        self.k.add_counter(victim,"-1/-1",1)
        out=self.upkeep()
        self.assertEqual(out[0].destroyed_old_id,victim)
        self.assertNotIn(victim,self.k.objects)
        self.assertIn(safe,self.k.objects)
        self.assertIn(ashes,self.k.objects)
        self.assertTrue(self.z.assert_consistent())

    def test_crumbling_ashes_has_no_effect_without_legal_target(self):
        self.add("Crumbling Ashes",types=("enchantment",))
        self.add("No counters",seat=1)
        result=self.upkeep()
        self.assertIsNone(result[0].destroyed_old_id)

    def test_crumbling_explicit_invalid_choice_is_nonmutating(self):
        ashes=self.add("Crumbling Ashes",types=("enchantment",))
        valid=self.add("Countered",seat=1)
        invalid=self.add("No counters",seat=2)
        self.k.add_counter(valid,"-1/-1",1)
        with self.assertRaises(ValueError):
            self.upkeep(choices={ashes:invalid})
        self.assertIn(valid,self.k.objects)
        self.assertIn(invalid,self.k.objects)
        self.assertTrue(self.z.assert_consistent())

    def test_ashes_does_not_destroy_indestructible_countered_creature(self):
        self.add("Crumbling Ashes",types=("enchantment",))
        indestructible=self.add("Protected",seat=1,
                               keywords=("indestructible",))
        self.k.add_counter(indestructible,"-1/-1",1)
        self.assertIsNone(self.upkeep()[0].destroyed_old_id)
        self.assertIn(indestructible,self.k.objects)

    def test_source_pin_and_spell_admission(self):
        self.assertTrue(reviewed_phase_creature(
            "Midnight Banshee",self.catalog["Midnight Banshee"]))
        self.assertTrue(reviewed_phase_permanent(
            "Crumbling Ashes",self.catalog["Crumbling Ashes"]))
        changed=dict(self.catalog["Midnight Banshee"],
                     oracle_id="changed-id")
        self.assertFalse(reviewed_phase_creature("Midnight Banshee",changed))
        fake=self.add("Midnight Banshee",colors="B",identity="fake:source")
        target=self.add("White creature",colors="W")
        self.assertEqual(self.upkeep(),())
        self.assertEqual(self.k.get(target).counters["-1/-1"],0)


if __name__=="__main__":
    unittest.main()
