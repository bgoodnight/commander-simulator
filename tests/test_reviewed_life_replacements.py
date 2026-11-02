"""Source-pinned opponent life-gain replacement fires before ledger commit."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_life_replacements import RULES

class ReviewedLifeReplacementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES
               if f.key=="mortarion_physical_final")
        cls.catalog={e["deck_name"]:e["card"] for e in
                     json.loads(f.snapshot_path.read_text())["cards"]}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=12)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.life.install_reviewed_replacements(self.catalog)

    def add_drone(self,seat=0,oracle=None):
        raw=self.catalog["Plague Drone"]
        return self.zones.add(self.C(
            oracle or raw["oracle_id"],"Plague Drone",
            frozenset({"creature"}),base_power=3,base_toughness=3,
            coverage="approx"),seat,"battlefield")

    def test_opponent_life_gain_becomes_loss_in_real_ledger(self):
        self.add_drone()
        self.life.gain(1,4)
        self.assertEqual(self.life.total(1),36)
        self.assertEqual(self.kernel.life_changes[-1].kind,"loss")
        self.assertEqual(self.kernel.life_changes[-1].amount,4)
        self.life.gain(0,3)
        self.assertEqual(self.life.total(0),43)

    def test_replacement_disappears_after_physical_source_leaves(self):
        drone=self.add_drone()
        self.life.gain(1,2)
        self.zones.move(drone,"graveyard","destroy")
        self.life.gain(1,2)
        self.assertEqual(self.life.total(1),40)
        self.assertEqual(self.kernel.life_changes[-1].kind,"gain")
        self.assertTrue(self.zones.assert_consistent())

    def test_multiple_approved_sources_do_not_double_apply_replacement(self):
        self.add_drone()
        self.add_drone()
        self.life.gain(2,3)
        self.assertEqual(self.life.total(2),37)
        self.assertEqual(len(self.kernel.life_changes),1)

    def test_wrong_oracle_identity_does_not_get_replacement(self):
        self.add_drone(oracle="fake")
        self.life.gain(1,5)
        self.assertEqual(self.life.total(1),45)

    def test_registration_matches_printed_oracle(self):
        rule=RULES["Plague Drone"]
        self.assertEqual(rule.oracle_id,self.catalog["Plague Drone"]["oracle_id"])
        self.assertIn(rule.excerpt,self.catalog["Plague Drone"]["oracle_text"])

if __name__=="__main__":
    unittest.main()
