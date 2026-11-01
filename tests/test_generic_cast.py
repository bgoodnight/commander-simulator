"""Actual v9b physical-zone kernel integration for reviewed M2 creature casting."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'simulator/v9b_live'))
from state import IndexedKernel, LiveZones
from rules import CardDefinition

from commander_sim.generic_cast import ReviewedCreatureCast, cast_reviewed_creature


class ReviewedCastKernelTests(unittest.TestCase):
    def setUp(self):
        self.kernel = IndexedKernel()
        self.zones = LiveZones(self.kernel)
        self.review = ReviewedCreatureCast(
            'oracle:test-undead-augur', '{1}{B}{B}', True,
            ('Zombie death trigger not yet executable',))
        self.creature = CardDefinition(
            self.review.card_id, 'Test reviewed Zombie',
            frozenset({'creature'}), frozenset({'Zombie'}),
            base_power=2, base_toughness=2, coverage='approx',
            colors=frozenset({'B'}))
        self.card_id = self.zones.add(self.creature, 0, 'hand')

    def land(self, name, owner=0, tapped=False, zone='battlefield'):
        oid = self.zones.add(CardDefinition(
            'land:' + name, name, frozenset({'land'}),
            coverage='verified_subset'), owner, zone)
        self.kernel.get(oid).tapped = tapped
        return oid

    def cast(self, review=None):
        return cast_reviewed_creature(
            self.zones, 0, self.card_id,
            self.review if review is None else review, {'B'})

    def test_black_cost_pays_and_uses_real_stack_and_battlefield(self):
        s1, s2 = self.land('Swamp'), self.land('Swamp')
        s3 = self.land('Swamp')
        result = self.cast()
        self.assertEqual(set(result.paid_source_ids), {s1, s2, s3})
        self.assertEqual(self.zones.ids(0, 'hand'), ())
        self.assertEqual(len(self.zones.ids(0, 'stack')), 1)
        self.assertTrue(all(self.kernel.get(x).tapped for x in (s1, s2, s3)))
        self.assertEqual(result.ticket.card_name, 'Test reviewed Zombie')
        battlefield_id = self.zones.resolve(result.ticket)
        self.assertIn(battlefield_id, self.zones.ids(0, 'battlefield'))
        self.assertIn('Zombie death trigger', result.unresolved_later_abilities[0])
        self.assertEqual(len(self.kernel.objects), 4)
        self.assertTrue(self.zones.assert_consistent())

    def test_unsupported_entry_review_cannot_mutate(self):
        swamps = [self.land('Swamp') for _ in range(3)]
        with self.assertRaises(ValueError):
            self.cast(ReviewedCreatureCast(self.review.card_id, '{1}{B}{B}'))
        self.assertIn(self.card_id, self.zones.ids(0, 'hand'))
        self.assertTrue(all(not self.kernel.get(x).tapped for x in swamps))

    def test_no_cost_coverage_returns_uncommitted(self):
        swamps = [self.land('Swamp') for _ in range(2)]
        self.assertIsNone(self.cast())
        self.assertIn(self.card_id, self.zones.ids(0, 'hand'))
        self.assertFalse(any(self.kernel.get(x).tapped for x in swamps))

    def test_opponent_and_tapped_lands_cannot_pay(self):
        self.land('Swamp', owner=1)
        self.land('Swamp', tapped=True)
        self.land('Swamp', zone='graveyard')
        self.assertIsNone(self.cast())
        self.assertTrue(self.zones.assert_consistent())

    def test_unimplemented_card_fails_closed(self):
        self.kernel.get(self.card_id).card = CardDefinition(
            self.review.card_id, 'Test reviewed Zombie',
            frozenset({'creature'}), coverage='unimplemented')
        for _ in range(3):
            self.land('Swamp')
        with self.assertRaises(ValueError):
            self.cast()
        self.assertEqual(len(self.zones.ids(0, 'stack')), 0)

    def test_reviewed_artifact_creature_keeps_both_types(self):
        self.kernel.get(self.card_id).card = CardDefinition(
            self.review.card_id, 'Test artifact creature',
            frozenset({'artifact', 'creature'}), coverage='approx')
        for _ in range(3):
            self.land('Swamp')
        result = self.cast()
        permanent = self.zones.resolve(result.ticket)
        self.assertEqual(self.kernel.get(permanent).types, frozenset({'artifact', 'creature'}))
        self.assertTrue(self.zones.assert_consistent())

    def test_review_identity_cannot_substitute_another_card(self):
        for _ in range(3):
            self.land('Swamp')
        with self.assertRaises(ValueError):
            self.cast(ReviewedCreatureCast('oracle:other', '{1}{B}{B}', True))
        self.assertEqual(len(self.zones.ids(0, 'hand')), 1)

    def test_no_second_cast_without_card_in_hand(self):
        for _ in range(3):
            self.land('Swamp')
        self.cast()
        with self.assertRaises(ValueError):
            self.cast()

    def test_true_colorless_cost_requires_wastes(self):
        review = ReviewedCreatureCast(self.review.card_id, '{C}', True)
        self.land('Swamp')
        self.assertIsNone(self.cast(review))
        self.land('Wastes')
        result = self.cast(review)
        self.assertEqual(len(result.paid_source_ids), 1)
        self.assertEqual(self.kernel.get(result.paid_source_ids[0]).card.name, 'Wastes')


if __name__ == '__main__':
    unittest.main()
