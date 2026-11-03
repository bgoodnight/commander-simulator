"""Reviewed player choices exclude eliminated seats without forbidding self."""
import unittest

from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_entry_choices import set_reviewed_entry_choice

_OID="499dceab-1890-49c8-b35d-b059a1dc950f"
_CATALOG={"Stuffy Doll":{"oracle_id":_OID,
    "oracle_text":"As this creature enters, choose a player."}}


class ReviewedEntryChoiceEligibilityTests(unittest.TestCase):
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=29)
        self.life=KernelLife(self.kernel)
        self.source=self.zones.add(C(_OID,"Stuffy Doll",
            frozenset({"artifact","creature"}),coverage="approx"),
            0,"battlefield")

    def test_eliminated_player_cannot_be_selected(self):
        self.life.lose(1,40)
        with self.assertRaises(ValueError):
            set_reviewed_entry_choice(
                self.zones,self.source,_CATALOG,player=1)
        self.assertFalse(getattr(self.kernel,"reviewed_player_choices",{}))

    def test_any_other_active_player_is_eligible(self):
        self.life.lose(1,40)
        result=set_reviewed_entry_choice(
            self.zones,self.source,_CATALOG,player=2)
        self.assertEqual(result,2)
        self.assertEqual(self.kernel.reviewed_player_choices[self.source],2)

    def test_self_remains_legal_when_opponents_are_eliminated(self):
        for seat in (1,2,3):
            self.life.lose(seat,40)
        self.assertEqual(self.life.active_opponents(0),())
        self.assertEqual(set_reviewed_entry_choice(
            self.zones,self.source,_CATALOG,player=0),0)


if __name__=="__main__":
    unittest.main()
