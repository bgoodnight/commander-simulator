"""Source-pinned activated utility recipes: cost and target semantics."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_death_effects import ReviewedDeathEngine
from commander_sim.reviewed_activated_utilities import (
    activate_reviewed,reviewed_activation)


class PhysicalUtilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES if f.key=="mortarion_physical_final")
        cls.catalog={e["deck_name"]:e["card"] for e in
                     json.loads(f.snapshot_path.read_text())["cards"]}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=9)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.mana=TemplateManaService(
            self.kernel,self.catalog,frozenset({"B"}),zones=self.zones)
        self.death=ReviewedDeathEngine(self.zones,self.life,self.catalog)

    def add(self,name,seat=0,types=("creature",),zone="battlefield",
            power=2,toughness=2,token=False):
        raw=self.catalog.get(name,{})
        return self.zones.add(self.C(
            raw.get("oracle_id","test:"+name),name,frozenset(types),
            base_power=power,base_toughness=toughness,coverage="approx"),
            seat,zone,token=token)

    def invoke(self,source,**kw):
        return activate_reviewed(self.zones,self.life,self.mana,self.death,
                                 self.catalog,source,turn=1,**kw)

    def test_unspeakable_symbol_pays_three_life_for_real_counter(self):
        source=self.add("Unspeakable Symbol",types=("enchantment",))
        target=self.add("Test Target",seat=2,power=4,toughness=4)
        out=self.invoke(source,target_id=target)
        self.assertIsNotNone(out)
        self.assertEqual(self.life.total(0),37)
        self.assertEqual(self.kernel.get(target).counters["+1/+1"],1)
        self.assertTrue(self.zones.assert_consistent())

    def test_life_paid_activation_refuses_lethal_cost(self):
        source=self.add("Unspeakable Symbol",types=("enchantment",))
        target=self.add("Body")
        self.life.lose(0,38)
        self.assertIsNone(self.invoke(source,target_id=target))
        self.assertEqual(self.kernel.get(target).counters["+1/+1"],0)

    def test_vito_lifelink_applies_to_current_creatures_and_expires(self):
        source=self.add("Vito, Thorn of the Dusk Rose")
        body=self.add("Body")
        for _ in range(5):self.add("Swamp",types=("land",))
        out=self.invoke(source)
        self.assertIsNotNone(out)
        self.assertIn("lifelink",self.kernel.get(body).keywords)
        self.kernel.cleanup()
        self.assertNotIn("lifelink",self.kernel.get(body).keywords)

    def test_yahenni_sacrifice_grants_indestructible_until_cleanup(self):
        source=self.add("Yahenni, Undying Partisan")
        victim=self.add("Token",token=True)
        out=self.invoke(source,sacrifice_id=victim)
        self.assertIsNotNone(out)
        self.assertNotIn(victim,self.kernel.objects)
        self.assertIn("indestructible",self.kernel.get(source).keywords)
        self.kernel.cleanup()
        self.assertNotIn("indestructible",self.kernel.get(source).keywords)
        self.assertTrue(self.zones.assert_consistent())

    def test_syr_konrad_mills_each_players_actual_library_object(self):
        source=self.add("Syr Konrad, the Grim")
        for _ in range(2):self.add("Swamp",types=("land",))
        for seat in range(4):
            self.add("Fodder "+str(seat),seat,zone="library")
        out=self.invoke(source)
        self.assertIsNotNone(out)
        self.assertEqual(len(out.affected_ids),4)
        self.assertTrue(all(len(self.zones.ids(seat,"graveyard"))==1
                            for seat in range(4)))
        self.assertTrue(self.zones.assert_consistent())

    def test_all_profiles_pin_source_identity(self):
        for name in ("Unspeakable Symbol","Vito, Thorn of the Dusk Rose",
                     "Yahenni, Undying Partisan","Syr Konrad, the Grim"):
            self.assertIsNotNone(reviewed_activation(name,self.catalog[name]))
            wrong=dict(self.catalog[name],oracle_id="fake")
            self.assertIsNone(reviewed_activation(name,wrong))


if __name__=="__main__":
    unittest.main()
