"""Physical mass creature exchange sequence, without invented priority."""
import unittest
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.mass_zone_sequences import resolve_mass_creature_exchange


class MassCreatureExchangeTests(unittest.TestCase):
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=11)
        self.C=C
        self.life=KernelLife(self.kernel)

    def creature(self,name,owner=0,zone="graveyard",controller=None,
                 commander=False):
        card=self.C("test:"+name,name,frozenset({"creature"}),
            subtypes=frozenset({"Zombie"}),
            supertypes=frozenset({"commander"}) if commander else frozenset(),
            coverage="approx")
        oid=self.zones.add(card,owner,zone)
        if controller is not None:
            self.kernel.get(oid).controller=controller
        return oid

    def test_each_player_exiles_then_sacrifices_then_returns(self):
        old_a=self.creature("Old A",owner=0)
        old_b=self.creature("Old B",owner=1)
        board_a=self.creature("Board A",owner=0,zone="battlefield")
        board_b=self.creature("Board B",owner=1,zone="battlefield")
        outcome=resolve_mass_creature_exchange(self.zones,self.life)
        self.assertEqual(len(outcome.exiled.movements),2)
        self.assertEqual(len(outcome.sacrificed.movements),2)
        self.assertEqual(len(outcome.returned.movements),2)
        self.assertEqual({m.before.object_id for m in outcome.exiled.movements},
                         {old_a,old_b})
        self.assertEqual({m.before.object_id for m in outcome.sacrificed.movements},
                         {board_a,board_b})
        self.assertEqual({self.kernel.get(m.new_object_id).card.name
                          for m in outcome.returned.movements},
                         {"Old A","Old B"})
        self.assertEqual({self.kernel.get(m.new_object_id).card.name
                          for m in outcome.sacrificed.movements},
                         {"Board A","Board B"})
        self.assertTrue(self.zones.assert_consistent())

    def test_sacrifice_uses_controller_but_card_moves_to_owners_grave(self):
        stolen=self.creature("Stolen",owner=1,zone="battlefield",controller=0)
        result=resolve_mass_creature_exchange(self.zones,self.life)
        before=result.sacrificed.movements[0].before
        self.assertEqual((before.object_id,before.owner,before.controller),
                         (stolen,1,0))
        self.assertEqual(self.kernel.get(
            result.sacrificed.movements[0].new_object_id).owner,1)
        self.assertEqual(len(result.returned.movements),0)

    def test_eliminated_seat_is_not_eligible_for_mass_effect(self):
        untouched=self.creature("Inactive",owner=2)
        self.life.lose(2,40)
        result=resolve_mass_creature_exchange(self.zones,self.life)
        self.assertEqual(result.participating_seats,(0,1,3))
        self.assertEqual(len(result.exiled.movements),0)
        self.assertEqual(self.kernel.get(untouched).zone,"graveyard")

    def test_commander_choice_unavailable_fails_before_any_zone_move(self):
        old=self.creature("Old")
        commander=self.creature("Leader",zone="battlefield",commander=True)
        with self.assertRaises(NotImplementedError):
            resolve_mass_creature_exchange(self.zones,self.life)
        self.assertEqual(self.kernel.get(old).zone,"graveyard")
        self.assertEqual(self.kernel.get(commander).zone,"battlefield")
        self.assertTrue(self.zones.assert_consistent())


if __name__=="__main__":
    unittest.main()
