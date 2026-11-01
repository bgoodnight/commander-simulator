"""Kernel-owned, separate life-gain/loss contracts."""
import unittest
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife,LifeChange


class KernelLifeTests(unittest.TestCase):
    def setUp(self):
        K,_,_=_load_live_kernel()
        self.kernel=K()
        self.life=KernelLife(self.kernel)

    def test_four_commander_seats_start_forty(self):
        self.assertEqual(tuple(self.life.total(i) for i in range(4)),
                         (40,40,40,40))
        self.assertIs(KernelLife(self.kernel).kernel,self.kernel)

    def test_controller_loss_and_opponent_loss_are_not_damage(self):
        self.life.lose(1,2,source_id=7)
        self.life.gain(2,3,source_id=8)
        self.life.each_opponent_loses(0,1,source_id=9)
        self.assertEqual(tuple(self.life.total(i) for i in range(4)),
                         (40,37,42,39))
        self.assertEqual([x.kind for x in self.kernel.life_changes],
                         ["loss","gain","loss","loss","loss"])
        self.assertEqual(self.kernel.life_changes[-1].source_id,9)

    def test_invalid_life_modification_and_seats_rejected(self):
        for amount in (-1,True):
            with self.subTest(amount=amount),self.assertRaises(ValueError):
                LifeChange(0,amount,"loss")
        with self.assertRaises(ValueError):
            self.life.lose(4,1)
        with self.assertRaises(ValueError):
            self.life.each_opponent_loses(0,-2)
        self.assertEqual(self.life.total(0),40)


if __name__=="__main__":
    unittest.main()
