"""Pre-mutation identity and legality for shared physical zone batches."""
import unittest
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.batch_zone_resolution import (
    ZoneMoveRequest,resolve_physical_zone_batch)


class BatchZoneResolutionTests(unittest.TestCase):
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=5)
        self.C=C

    def put(self,name,owner=0,zone="graveyard",controller=None):
        oid=self.zones.add(self.C("test:"+name,name,
            frozenset({"creature"}),subtypes=frozenset({"Zombie"}),
            coverage="approx"),owner,zone)
        if controller is not None:
            self.kernel.get(oid).controller=controller
        return oid

    def test_exile_batch_preserves_each_original_owner_and_provenance(self):
        first=self.put("First",0)
        second=self.put("Second",1)
        out=resolve_physical_zone_batch(self.zones,(
            ZoneMoveRequest(first,"exile","exile"),
            ZoneMoveRequest(second,"exile","exile")),label="living_death_exile")
        self.assertEqual(out.label,"living_death_exile")
        self.assertEqual([x.before.owner for x in out.movements],[0,1])
        self.assertEqual([x.before.card_name for x in out.movements],
                         ["First","Second"])
        for moved in out.movements:
            self.assertEqual(self.kernel.get(moved.new_object_id).zone,"exile")
            self.assertIn(moved.new_object_id,
                          self.zones.ids(moved.before.owner,"exile"))
        self.assertTrue(self.zones.assert_consistent())

    def test_graveyard_then_battlefield_phases_use_fresh_ids(self):
        original=self.put("Returnable")
        exile=resolve_physical_zone_batch(
            self.zones,(ZoneMoveRequest(original,"exile","exile"),))
        exiled=exile.movements[0].new_object_id
        returned=resolve_physical_zone_batch(
            self.zones,(ZoneMoveRequest(exiled,"battlefield","resolve"),))
        obj=self.kernel.get(returned.movements[0].new_object_id)
        self.assertEqual(obj.zone,"battlefield")
        self.assertEqual(obj.owner,0)
        self.assertNotEqual(original,obj.object_id)
        self.assertTrue(self.zones.assert_consistent())

    def test_batch_snapshots_controller_before_move(self):
        original=self.put("Stolen",owner=1,zone="battlefield",controller=0)
        outcome=resolve_physical_zone_batch(
            self.zones,(ZoneMoveRequest(original,"graveyard","sacrifice"),))
        before=outcome.movements[0].before
        self.assertEqual((before.owner,before.controller,before.zone),
                         (1,0,"battlefield"))
        new=outcome.movements[0].new_object_id
        self.assertEqual(self.kernel.get(new).owner,1)
        self.assertTrue(self.zones.assert_consistent())

    def test_duplicate_ids_rejected_before_any_mutation(self):
        oid=self.put("One")
        with self.assertRaises(ValueError):
            resolve_physical_zone_batch(self.zones,(
                ZoneMoveRequest(oid,"exile","exile"),
                ZoneMoveRequest(oid,"hand","resolve")))
        self.assertEqual(self.kernel.get(oid).zone,"graveyard")
        self.assertTrue(self.zones.assert_consistent())

    def test_stale_or_invalid_request_rejected_before_any_mutation(self):
        oid=self.put("One")
        for invalid in (ZoneMoveRequest(999999,"exile","exile"),
                        ZoneMoveRequest(oid,"graveyard","resolve"),
                        ZoneMoveRequest(oid,"nowhere","resolve")):
            with self.assertRaises(ValueError):
                resolve_physical_zone_batch(self.zones,(
                    ZoneMoveRequest(oid,"exile","exile"),invalid))
            self.assertEqual(self.kernel.get(oid).zone,"graveyard")
        self.assertTrue(self.zones.assert_consistent())


if __name__=="__main__":
    unittest.main()
