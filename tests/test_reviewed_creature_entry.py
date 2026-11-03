"""Source-pinned, reusable creature-entry triggers through real object IDs."""
import json
import unittest
from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_creature_entry import (
    ReviewedCreatureEntryEngine, reviewed_creature_entry_rule)


class CreatureEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture=next(x for x in FIXTURES if x.key=="wretched_ranks")
        cls.catalog={x["deck_name"]:x["card"] for x in
                     json.loads(fixture.snapshot_path.read_text())["cards"]}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=33)
        self.life=KernelLife(self.kernel)
        self.C=C
        self.engine=ReviewedCreatureEntryEngine(
            self.zones,self.life,self.catalog)

    def body(self,seat,name="Zombie",subtypes=("Zombie",),colors=("B",),
             zone="battlefield",token=False):
        return self.zones.add(self.C(
            "test:"+name+":"+str(seat),name,
            frozenset({"creature"}),subtypes=frozenset(subtypes),
            colors=frozenset(colors),base_power=1,base_toughness=2,
            coverage="approx"),seat,zone,token=token)

    def source(self,name,seat=0,zone="hand"):
        raw=self.catalog[name]
        return self.zones.add(self.C(
            raw["oracle_id"],name,frozenset({"creature"}),
            subtypes=frozenset(raw["type_line"].split(" — ",1)[1].split()),
            colors=frozenset(raw["colors"]),base_power=int(raw["power"]),
            base_toughness=int(raw["toughness"]),coverage="approx"),seat,zone)

    def test_champion_another_own_zombie_only_once(self):
        champion=self.zones.move(self.source("Champion of the Perished"),
                                 "battlefield")
        initial=self.engine.resolve()
        self.assertEqual(initial,())
        self.assertEqual(self.kernel.get(champion).counters["+1/+1"],0)
        self.body(0)
        triggered=self.engine.resolve()
        self.assertEqual(len(triggered),1)
        self.assertEqual(triggered[0].operation,"counter_self")
        self.assertEqual(self.kernel.get(champion).counters["+1/+1"],1)
        self.assertEqual(self.engine.resolve(),())
        self.body(1)
        self.body(0,name="Human",subtypes=("Human",))
        self.engine.resolve()
        self.assertEqual(self.kernel.get(champion).counters["+1/+1"],1)
        self.body(0,token=True)
        self.engine.resolve()
        self.assertEqual(self.kernel.get(champion).counters["+1/+1"],2)
        self.assertTrue(self.zones.assert_consistent())

    def test_separate_source_instances_trigger_independently(self):
        one=self.zones.move(self.source("Champion of the Perished"),"battlefield")
        two=self.zones.move(self.source("Champion of the Perished"),"battlefield")
        self.engine.resolve()
        # Second Champion is itself another Zombie for the first.
        self.assertEqual(self.kernel.get(one).counters["+1/+1"],1)
        self.assertEqual(self.kernel.get(two).counters["+1/+1"],0)
        self.body(0)
        x=self.engine.resolve()
        self.assertEqual(len(x),2)
        self.assertEqual(self.kernel.get(one).counters["+1/+1"],2)
        self.assertEqual(self.kernel.get(two).counters["+1/+1"],1)

    def test_ayara_triggers_on_own_entry_then_allies_without_eliminated_seat(self):
        ayara=self.zones.move(self.source("Ayara, First of Locthwain"),
                              "battlefield")
        x=self.engine.resolve()
        self.assertEqual(len(x),1)
        self.assertEqual(x[0].operation,"opponent_drain")
        self.assertEqual(self.life.total(0),41)
        self.assertEqual([self.life.total(s) for s in (1,2,3)],[39,39,39])
        self.life.lose(3,39)
        self.body(0,colors=("B",))
        self.body(1,colors=("B",))
        self.body(0,name="Green",subtypes=("Elf",),colors=("G",))
        self.engine.resolve()
        self.assertEqual(self.life.total(0),42)
        self.assertEqual([self.life.total(s) for s in (1,2,3)],[38,38,0])
        self.assertEqual(self.engine.resolve(),())
        self.assertTrue(self.zones.assert_consistent())

    def test_reviewed_identity_and_source_lifetime(self):
        raw=self.catalog["Champion of the Perished"]
        self.assertIsNone(reviewed_creature_entry_rule("Champion of the Perished",
                        dict(raw,oracle_text="Unreviewed ability")))
        source=self.zones.move(self.source("Champion of the Perished"),
                               "battlefield")
        self.engine.resolve()
        self.zones.move(source,"graveyard","destroy")
        self.body(0)
        self.assertEqual(self.engine.resolve(),())
        self.assertTrue(self.zones.assert_consistent())


if __name__=="__main__":
    unittest.main()
