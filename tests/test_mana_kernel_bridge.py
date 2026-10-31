"""M2 source-ID bridge contracts; no synthetic game-state inventory."""
import unittest
from dataclasses import dataclass
from types import SimpleNamespace

from commander_sim.mana_kernel_bridge import plan_live_basic_payment
from commander_sim.mana_costs import UnsupportedManaCost


@dataclass
class FakePermanent:
    object_id: int
    name: str
    controller: int = 0
    zone: str = 'battlefield'
    tapped: bool = False
    token: bool = False
    types: frozenset = frozenset({'land'})

    @property
    def card(self):
        return SimpleNamespace(name=self.name)


class LivePaymentBridgeTests(unittest.TestCase):
    def setUp(self):
        self.kernel = SimpleNamespace(objects={})

    def land(self, oid, name, **kwargs):
        self.kernel.objects[oid] = FakePermanent(oid, name, **kwargs)

    def plan(self, cost, colors=('U', 'R')):
        return plan_live_basic_payment(self.kernel, 0, cost, colors)

    def test_source_ids_from_authoritative_objects(self):
        self.land(37, 'Island')
        self.land(12, 'Mountain')
        result = self.plan('{U}{R}')
        self.assertEqual(set(result.source_ids), {12, 37})
        self.assertEqual(set(self.kernel.objects), {12, 37})

    def test_swamp_black_cast_payment_preview(self):
        self.land(5, 'Swamp')
        result = self.plan('{B}', ('B',))
        self.assertEqual(result.source_ids, (5,))
        self.assertFalse(self.kernel.objects[5].tapped)

    def test_true_colorless_is_not_generic_colored_mana(self):
        self.land(1, 'Swamp')
        self.assertIsNone(self.plan('{C}', ('B',)))
        self.land(2, 'Wastes')
        self.assertEqual(self.plan('{C}', ('B',)).source_ids, (2,))

    def test_command_tower_respects_commander_identity(self):
        self.land(9, 'Command Tower')
        self.assertEqual(self.plan('{B}', ('B',)).source_ids, (9,))
        self.assertIsNone(self.plan('{G}', ('B',)))

    def test_tapped_and_opponent_and_nonbattlefield_excluded(self):
        self.land(1, 'Island', tapped=True)
        self.land(2, 'Island', controller=1)
        self.land(3, 'Island', zone='graveyard')
        self.assertIsNone(self.plan('{U}'))
        self.land(4, 'Island')
        self.assertEqual(self.plan('{U}').source_ids, (4,))

    def test_unreviewed_nonbasics_and_tokens_are_not_guessed(self):
        self.land(1, 'Exotic Orchard')
        self.land(2, 'Treasure', token=True)
        self.land(3, 'Sol Ring', types=frozenset({'artifact'}))
        self.assertIsNone(self.plan('{1}'))

    def test_fixed_cost_restrictions_fail_closed(self):
        self.land(1, 'Island')
        for cost in ('{X}', '{U/R}', '{U/P}', '{S}', ''):
            with self.subTest(cost=cost), self.assertRaises(UnsupportedManaCost):
                self.plan(cost)
        with self.assertRaises(ValueError):
            self.plan('{U}', ('Q',))


if __name__ == '__main__':
    unittest.main()
