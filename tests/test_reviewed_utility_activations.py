"""Utility activation templates use paid physical resources and proper zones."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_utility_activations import activate_utility

class UtilityActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES if f.key=="mortarion_physical_final")
        cls.catalog={r["deck_name"]:r["card"] for r in
                     json.loads(f.snapshot_path.read_text())["cards"]}
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=3)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.mana=TemplateManaService(self.kernel,self.catalog,
                                      frozenset({"B"}),zones=self.zones)
    def add(self,name,zone="battlefield",types=None):
        raw=self.catalog.get(name,{})
        if types is None:
            types=("land",) if "Land" in raw.get("type_line","") else ("creature",)
        return self.zones.add(self.C(raw.get("oracle_id","mock:"+name),name,
            frozenset(types),coverage="approx"),0,zone)
    def basics(self,n):
        return [self.add("Swamp",types=("land",)) for _ in range(n)]
    def library(self,n):
        for i in range(n):self.add("Card "+str(i),zone="library",types=("instant",))
    def use(self,source,**kw):
        return activate_utility(self.zones,self.life,0,source,self.catalog,
            self.mana,frozenset({"B"}),**kw)
    def test_war_room_life_payment_and_real_draw(self):
        room=self.add("War Room",types=("land",))
        self.basics(3)
        self.library(2)
        out=self.use(room)
        self.assertEqual(out.life_paid,1)
        self.assertEqual(self.life.total(0),39)
        self.assertEqual(len(out.new_object_ids),1)
        self.assertTrue(self.kernel.get(room).tapped)
    def test_barren_moor_cycles_from_hand_for_actual_card(self):
        land=self.add("Barren Moor",zone="hand",types=("land",))
        self.basics(1)
        self.library(1)
        out=self.use(land)
        self.assertEqual(out.operation,"draw")
        self.assertEqual(len(self.zones.ids(0,"graveyard")),1)
        self.assertEqual(len(self.zones.ids(0,"hand")),1)
    def test_reassembling_skeleton_returns_self_tapped(self):
        skeleton=self.add("Reassembling Skeleton",zone="graveyard")
        self.basics(2)
        out=self.use(skeleton)
        obj=self.kernel.get(out.new_object_ids[0])
        self.assertEqual(obj.zone,"battlefield")
        self.assertTrue(obj.tapped)
    def test_phyrexian_reclamation_recovers_graveyard_creature(self):
        source=self.add("Phyrexian Reclamation",types=("enchantment",))
        creature=self.add("Reassembling Skeleton",zone="graveyard")
        self.basics(2)
        out=self.use(source,target_id=creature)
        self.assertEqual(self.life.total(0),38)
        self.assertEqual(self.kernel.get(out.new_object_ids[0]).zone,"hand")
    def test_leechridden_swamp_needs_two_black_permanents(self):
        source=self.add("Leechridden Swamp",types=("land",))
        self.basics(1)
        self.assertIsNone(self.use(source))
        for name in ("Blood Artist","Vito, Thorn of the Dusk Rose"):
            raw=self.catalog[name]
            self.zones.add(self.C(raw["oracle_id"],name,
                frozenset({"creature"}),colors=frozenset({"B"}),
                coverage="approx"),0,"battlefield")
        self.assertIsNotNone(self.use(source))
        self.assertEqual([self.life.total(i) for i in range(4)],
                         [40,39,39,39])
    def test_mind_stone_source_cannot_pay_its_own_sacrifice_cost(self):
        stone=self.add("Mind Stone",types=("artifact",))
        self.library(1)
        self.assertIsNone(self.use(stone))
        self.basics(1)
        out=self.use(stone)
        self.assertEqual(len(out.new_object_ids),2)
        self.assertEqual(len(self.zones.ids(0,"graveyard")),1)
        self.assertTrue(self.zones.assert_consistent())
if __name__=="__main__":unittest.main()
