"""Regression coverage for pinned cross-deck death effects using real moves."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_death_effects import (
    DEATH_RULES, ReviewedDeathEngine, capture_battlefield,
)


class ReviewedDeathEffectsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for fixture in FIXTURES:
            for row in json.loads(fixture.snapshot_path.read_text())["cards"]:
                cls.catalog.setdefault(row["deck_name"],row["card"])

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=9)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.engine=ReviewedDeathEngine(self.zones,self.life,self.catalog)

    def add(self,name,*,controller=0,types=("creature",),subtypes=(),
            zone="battlefield",token=False,oracle=None):
        row=self.catalog.get(name)
        oid=oracle or (row["oracle_id"] if row else "test:"+name)
        return self.zones.add(self.C(oid,name,frozenset(types),
            subtypes=frozenset(subtypes),coverage="approx"),controller,
            zone,token=token)

    def stock_draw(self,seat,count):
        for i in range(count):
            self.add("Card "+str(seat)+" "+str(i),controller=seat,
                     types=("instant",),zone="library")

    def kill(self,*targets,turn=1,reason="sacrifice"):
        before=capture_battlefield(self.kernel)
        start=len(self.kernel.moves)
        for oid in targets:
            self.zones.move(oid,"graveyard",reason)
        return self.engine.resolve_deaths(before,move_index=start,turn=turn)

    def test_zombie_death_composes_headless_open_graves_and_undead_augur(self):
        self.add("Headless Rider")
        self.add("Open the Graves",types=("enchantment",))
        self.add("Undead Augur")
        victim=self.add("Victim",subtypes=("Zombie",))
        self.stock_draw(0,3)
        outcomes=self.kill(victim)
        self.assertEqual([o.source_name for o in outcomes],
            ["Headless Rider","Open the Graves","Undead Augur"])
        zombies=[x for x in self.kernel.on_battlefield()
                 if x.token and x.card.name=="Zombie"]
        self.assertEqual(len(zombies),2)
        self.assertEqual(self.life.total(0),39)
        self.assertEqual(len(self.zones.ids(0,"hand")),1)
        self.assertTrue(self.zones.assert_consistent())

    def test_self_death_still_triggers_headless_and_vengeful(self):
        headless=self.add("Headless Rider",subtypes=("Zombie",))
        self.add("Vengeful Dead",subtypes=("Zombie",))
        result=self.kill(headless)
        self.assertEqual([x.source_name for x in result],
                         ["Headless Rider","Vengeful Dead"])
        self.assertEqual([self.life.total(seat) for seat in range(4)],
                         [40,39,39,39])
        self.assertEqual(sum(x.token and x.card.name=="Zombie"
                             for x in self.kernel.on_battlefield()),1)

    def test_bastion_and_plunderer_share_one_creature_death(self):
        self.add("Bastion of Remembrance",types=("enchantment",))
        self.add("Pitiless Plunderer")
        victim=self.add("Victim")
        resolved=self.kill(victim)
        self.assertEqual({x.operation for x in resolved},{"drain_gain","treasure"})
        self.assertEqual([self.life.total(seat) for seat in range(4)],
                         [41,39,39,39])
        tokens=[o for o in self.kernel.on_battlefield() if o.token]
        self.assertEqual(len(tokens),1)
        self.assertEqual(tokens[0].card.name,"Treasure")
        self.assertTrue(self.zones.assert_consistent())

    def test_once_per_turn_morbid_handles_batch_and_repeated_movement(self):
        self.add("Morbid Opportunist")
        self.stock_draw(0,4)
        a=self.add("A")
        b=self.add("B",controller=1)
        first=self.kill(a,b,turn=1)
        self.assertEqual(len([r for r in first if r.source_name=="Morbid Opportunist"]),1)
        self.assertEqual(len(self.zones.ids(0,"hand")),1)
        self.assertEqual(self.engine.resolve_deaths(
            capture_battlefield(self.kernel),move_index=len(self.kernel.moves),turn=1),())
        c=self.add("C",controller=1)
        self.assertEqual(len(self.kill(c,turn=1)),0)
        d=self.add("D",controller=1)
        self.assertEqual(len(self.kill(d,turn=2)),1)
        self.assertEqual(len(self.zones.ids(0,"hand")),2)

    def test_source_survives_to_receive_counter_not_after_death(self):
        crawler=self.add("Venomcrawler")
        enemy=self.add("Opponent creature",controller=1)
        outcomes=self.kill(enemy)
        self.assertEqual(len(outcomes),1)
        self.assertEqual(self.kernel.get(crawler).counters["+1/+1"],1)
        # A simultaneously dying source still generates its stack trigger,
        # but there is no surviving battlefield object to receive counters.
        other=self.add("Another",controller=1)
        result=self.kill(crawler,other)
        self.assertEqual(sum(r.source_name=="Venomcrawler" for r in result),1)
        self.assertNotIn(crawler,self.kernel.objects)

    def test_yahenni_massacre_wurm_meathook_per_controller(self):
        yahenni=self.add("Yahenni, Undying Partisan")
        self.add("Massacre Wurm")
        self.add("The Meathook Massacre",types=("enchantment",))
        target=self.add("Enemy creature",controller=2)
        result=self.kill(target)
        self.assertEqual(len(result),3)
        self.assertEqual(self.kernel.get(yahenni).counters["+1/+1"],1)
        self.assertEqual(self.life.total(2),38)
        self.assertEqual(self.life.total(0),41)
        self.assertEqual(self.life.total(1),40)

    def test_artifact_sacrifice_triggers_marionette_apprentice_only_once(self):
        self.add("Marionette Apprentice")
        artifact=self.add("Disposable artifact",types=("artifact",))
        results=self.kill(artifact)
        self.assertEqual(len(results),1)
        self.assertEqual(results[0].source_name,"Marionette Apprentice")
        self.assertEqual(tuple(self.life.total(i) for i in range(4)),
                         (40,39,39,39))
        self.assertEqual(len(self.engine.invocations),1)

    def test_unreviewed_identity_never_executes_and_death_moves_required(self):
        self.add("Headless Rider",oracle="wrong-id")
        victim=self.add("Victim",subtypes=("Zombie",))
        self.assertEqual(self.kill(victim),())
        self.assertTrue(self.zones.assert_consistent())
        self.assertGreaterEqual(len(DEATH_RULES),12)

    def test_snapshot_missing_dead_id_refused_without_trigger_side_effect(self):
        self.add("Open the Graves",types=("enchantment",))
        before=capture_battlefield(self.kernel)
        victim=self.add("Victim")
        index=len(self.kernel.moves)
        self.zones.move(victim,"graveyard","sacrifice")
        with self.assertRaises(ValueError):
            self.engine.resolve_deaths(before,move_index=index,turn=1)
        self.assertFalse(self.engine.invocations)

    def test_death_draw_requires_library_capacity_without_partial_processing(self):
        self.add("Undead Augur")
        victim=self.add("Victim",subtypes=("Zombie",))
        before=capture_battlefield(self.kernel)
        index=len(self.kernel.moves)
        self.zones.move(victim,"graveyard","destroy")
        with self.assertRaises(NotImplementedError):
            self.engine.resolve_deaths(before,move_index=index,turn=1)
        self.assertEqual(self.life.total(0),40)
        self.assertEqual(self.engine.invocations,[])


if __name__=="__main__":
    unittest.main()
