"""Additional reusable graveyard-move and opponent-discard subscriptions."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_reactive_triggers import ReactiveTriggerEngine

class ReactiveGraveyardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES if f.key=="mortarion_physical_final")
        cls.catalog={x["deck_name"]:x["card"] for x in
                     json.loads(f.snapshot_path.read_text())["cards"]}
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=3)
        self.C=C
        self.life=KernelLife(self.kernel)
    def add(self,name,seat=0,zone="battlefield"):
        raw=self.catalog.get(name,{})
        return self.zones.add(self.C(raw.get("oracle_id","test:"+name),name,
            frozenset({"creature"}),base_power=2,base_toughness=2,
            coverage="approx"),seat,zone)

    def test_syr_konrad_sees_creature_milled_from_other_library(self):
        self.add("Syr Konrad, the Grim")
        prey=self.add("Enemy",seat=2,zone="library")
        events=ReactiveTriggerEngine(self.zones,self.life,self.catalog)
        self.zones.move(prey,"graveyard","mill")
        result=events.resolve()
        self.assertEqual(sum(x.event=="creature_to_grave_nonbattlefield" for x in result),1)
        self.assertEqual(self.life.total(1),39)
        self.assertEqual(self.life.total(2),39)
        self.assertEqual(self.life.total(3),39)
        self.assertEqual(self.life.total(0),40)

    def test_syr_konrad_only_sees_own_creatures_leaving_graveyard(self):
        self.add("Syr Konrad, the Grim")
        own=self.add("Own",zone="graveyard")
        enemy=self.add("Enemy",seat=1,zone="graveyard")
        events=ReactiveTriggerEngine(self.zones,self.life,self.catalog)
        self.zones.move(enemy,"exile","exile")
        self.assertEqual(events.resolve(),())
        self.zones.move(own,"exile","exile")
        result=events.resolve()
        self.assertEqual(len(result),1)
        self.assertEqual(self.life.total(1),39)

    def test_sangromancer_gains_for_each_opponent_discard_only(self):
        self.add("Sangromancer")
        enemy=self.add("Enemy",seat=2,zone="hand")
        own=self.add("Own",zone="hand")
        events=ReactiveTriggerEngine(self.zones,self.life,self.catalog)
        self.zones.discard(2,enemy)
        self.zones.discard(0,own)
        result=events.resolve()
        self.assertEqual(sum(x.event=="opponent_discard" for x in result),1)
        self.assertEqual(self.life.total(0),43)

    def test_syr_konrad_nonbattlefield_move_is_not_double_counted(self):
        self.add("Syr Konrad, the Grim")
        enemy=self.add("Enemy",seat=2,zone="library")
        events=ReactiveTriggerEngine(self.zones,self.life,self.catalog)
        self.zones.move(enemy,"graveyard","mill")
        self.assertEqual(len(events.resolve()),1)
        self.assertEqual(events.resolve(),())
        self.assertEqual(self.life.total(1),39)

if __name__=="__main__":
    unittest.main()
