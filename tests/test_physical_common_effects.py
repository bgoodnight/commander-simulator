"""Common effects over one authoritative physical IndexedKernel/LiveZones."""
import unittest

from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.physical_common_effects import (
    CardQuantity, CounterPlacement, GraveyardToHand,
    draw_physical_cards, mill_physical_cards, put_reviewed_counters,
    retrieve_reviewed_graveyard_card,
)


class PhysicalCommonEffectTests(unittest.TestCase):
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K()
        self.z=Z(self.k,seed=19)
        self.Card=C

    def card(self,name,zone,types,seat=0):
        return self.z.add(self.Card("test:"+name,name,frozenset(types),
                     coverage="approx"),seat,zone)

    def test_draw_moves_real_top_library_id_to_hand(self):
        before=self.card("Zombie","library",{"creature"})
        result=draw_physical_cards(self.z,0,CardQuantity(1))
        self.assertTrue(result.complete)
        self.assertEqual(len(result.drawn_ids),1)
        self.assertNotEqual(result.drawn_ids[0],before)
        self.assertEqual(self.k.get(result.drawn_ids[0]).zone,"hand")
        self.assertTrue(self.z.assert_consistent())

    def test_draw_from_empty_reports_unresolved_loss_not_synthetic_win(self):
        result=draw_physical_cards(self.z,0,CardQuantity(1))
        self.assertFalse(result.complete)
        self.assertEqual(result.drawn_ids,())
        self.assertTrue(self.z.assert_consistent())

    def test_mill_moves_real_top_cards_to_graveyard(self):
        original=[self.card("Card"+str(i),"library",{"creature"}) for i in range(3)]
        moved=mill_physical_cards(self.z,0,CardQuantity(2))
        self.assertEqual(len(moved),2)
        self.assertEqual(len(self.z.ids(0,"graveyard")),2)
        self.assertEqual(len(self.z.ids(0,"library")),1)
        self.assertFalse(any(x in self.k.objects for x in original[-2:]))
        self.assertTrue(self.z.assert_consistent())

    def test_counter_placement_is_shared_across_positive_and_negative_counters(self):
        creature=self.card("Necroskitter","battlefield",{"creature"})
        for name,quantity in (("-1/-1",2),("+1/+1",1)):
            self.assertEqual(put_reviewed_counters(self.k,0,creature,
                CounterPlacement(name,quantity)),creature)
        self.assertEqual(self.k.get(creature).counters["-1/-1"],2)
        self.assertEqual(self.k.get(creature).counters["+1/+1"],1)

    def test_counter_requires_correct_controller_and_target_type(self):
        opponent=self.card("Opponent","battlefield",{"creature"},seat=1)
        rock=self.card("Rock","battlefield",{"artifact"})
        with self.assertRaises(ValueError):
            put_reviewed_counters(self.k,0,opponent,
                CounterPlacement("+1/+1",1))
        with self.assertRaises(ValueError):
            put_reviewed_counters(self.k,0,rock,
                CounterPlacement("+1/+1",1))
        self.assertFalse(self.k.get(opponent).counters["+1/+1"])
        self.assertFalse(self.k.get(rock).counters["+1/+1"])

    def test_reviewed_graveyard_to_hand_moves_only_owned_correct_type(self):
        zombie=self.card("Gravecrawler","graveyard",{"creature"})
        spell=self.card("Spell","graveyard",{"instant"})
        effect=GraveyardToHand(frozenset({"creature"}))
        new=retrieve_reviewed_graveyard_card(self.z,0,zombie,effect)
        self.assertEqual(self.k.get(new).zone,"hand")
        with self.assertRaises(ValueError):
            retrieve_reviewed_graveyard_card(self.z,0,spell,effect)
        self.assertIn(spell,self.z.ids(0,"graveyard"))
        self.assertTrue(self.z.assert_consistent())

    def test_invalid_effect_specs_fail_before_any_mutation(self):
        with self.assertRaises(ValueError):
            CardQuantity(-1)
        with self.assertRaises(ValueError):
            CounterPlacement("+1/+1",0)
        with self.assertRaises(ValueError):
            GraveyardToHand(frozenset())
        self.assertEqual(len(self.k.objects),0)


if __name__=="__main__":
    unittest.main()
