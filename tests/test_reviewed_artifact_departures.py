"""Last-known artifact departures use one shared trigger and zone history."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_death_effects import (
    ReviewedDeathEngine, capture_battlefield)
from commander_sim.reviewed_artifact_departures import (
    ReviewedArtifactDepartureEngine)


class ArtifactDepartureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(x for x in FIXTURES if x.key=="necron_dynasties")
        cls.catalog={row["deck_name"]:row["card"] for row in
                     json.loads(f.snapshot_path.read_text())["cards"]}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K();self.z=Z(self.k,seed=51);self.C=C
        self.life=KernelLife(self.k)
        self.deaths=ReviewedDeathEngine(self.z,self.life,self.catalog)

    def add(self,name,*,types=("creature",),seat=0,identity=None,zone="battlefield"):
        raw=self.catalog.get(name,{})
        return self.z.add(self.C(identity or raw.get("oracle_id","test:"+name),
                         name,frozenset(types),base_power=5,base_toughness=5,
                         coverage="approx"),seat,zone)

    def move_and_resolve(self,target,to_zone="graveyard",reason="sacrifice"):
        before=capture_battlefield(self.k)
        start=len(self.k.moves)
        self.z.move(target,to_zone,reason)
        self.deaths.resolve_deaths(before,move_index=start,turn=1)
        return before,start

    def test_artifact_death_adds_two_counters_to_shard(self):
        shard=self.add("Shard of the Void Dragon")
        target=self.add("Artifact",types=("artifact",),seat=2)
        self.move_and_resolve(target)
        self.assertEqual(self.k.get(shard).counters["+1/+1"],2)
        self.assertTrue(self.z.assert_consistent())

    def test_artifact_exile_counts_and_deduplicates(self):
        shard=self.add("Shard of the Void Dragon")
        target=self.add("Artifact",types=("artifact",),seat=3)
        before,start=self.move_and_resolve(target,"exile","exile")
        self.assertEqual(self.k.get(shard).counters["+1/+1"],2)
        self.assertEqual(self.deaths.artifact_departures.resolve(
            before,move_index=start),())
        self.assertEqual(self.k.get(shard).counters["+1/+1"],2)
        self.assertTrue(self.z.assert_consistent())

    def test_multiple_artifacts_in_same_batch_each_trigger(self):
        shard=self.add("Shard of the Void Dragon")
        x=self.add("Artifact one",types=("artifact",))
        y=self.add("Artifact two",types=("artifact","creature"),seat=2)
        before=capture_battlefield(self.k)
        start=len(self.k.moves)
        self.z.move(x,"graveyard","sacrifice")
        self.z.move(y,"graveyard","sacrifice")
        self.deaths.resolve_deaths(before,move_index=start,turn=2)
        self.assertEqual(self.k.get(shard).counters["+1/+1"],4)
        self.assertTrue(self.z.assert_consistent())

    def test_nonartifacts_do_not_trigger(self):
        shard=self.add("Shard of the Void Dragon")
        creature=self.add("Human",types=("creature",))
        self.move_and_resolve(creature)
        self.assertEqual(self.k.get(shard).counters["+1/+1"],0)

    def test_unverified_source_fails_closed(self):
        fake=self.add("Shard of the Void Dragon",identity="fake:shard")
        art=self.add("Artifact",types=("artifact",))
        self.move_and_resolve(art)
        self.assertEqual(self.k.get(fake).counters["+1/+1"],0)

    def test_departed_source_does_not_gain_counters(self):
        shard=self.add("Shard of the Void Dragon")
        art=self.add("Artifact",types=("artifact",))
        before=capture_battlefield(self.k)
        start=len(self.k.moves)
        self.z.move(shard,"graveyard","sacrifice")
        self.z.move(art,"graveyard","sacrifice")
        self.deaths.resolve_deaths(before,move_index=start,turn=1)
        self.assertNotIn(shard,self.k.objects)
        self.assertTrue(self.z.assert_consistent())


if __name__=="__main__":
    unittest.main()
