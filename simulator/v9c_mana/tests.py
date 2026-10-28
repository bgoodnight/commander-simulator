"""Live mana acceptance tests: actual source identities, costs and ordered funding."""
import unittest
from dataclasses import replace
from game import ManaTable
from resources import Cost, Activation, SourcePayment, ZERO, U, R, C
from rules import SafetyStop
from kernel import WorldEntry
from catalog import TREASURE
import simulation as base
import integrated as v6


class ManaTests(unittest.TestCase):
    def setUp(self):
        self.t = ManaTable(seed=71)
        self.r = self.t.resources
        self.p = self.t.details
        self.t.response_policy = lambda *args: None

    def source(self, name, seat=None, duplicate=False):
        seat = self.p.seat if seat is None else seat
        player = self.t.players[seat]
        if seat == self.p.seat and not duplicate:
            card = next(c for c in player.hand + player.library if c.name == name)
            oid = self.t.zones.move(card.object_id, 'battlefield')
        else:
            spec = (v6.named_spec(name) if seat == self.p.seat else
                    base.CardSpec(name, 'land', 0, 'land', 'none'))
            oid = self.t.zones.add_spec(spec, seat, 'battlefield', detailed=seat == self.p.seat)
        self.t.world.views[oid] = WorldEntry(player, None, 'resource')
        return oid

    def give(self, name, player=None, effect=None):
        player = self.p if player is None else player
        card = next(c for c in player.hand + player.library if (name is None or c.name == name)
                    and (effect is None or c.effect == effect))
        if card not in player.hand:
            oid = self.t.zones.move(card.object_id, 'hand')
            card = next(c for c in player.hand if c.object_id == oid)
        return card

    def clear_hands(self):
        for player in self.t.players:
            for oid in self.t.zones.ids(player.seat, 'hand'):
                self.t.zones.move(oid, 'library')

    def cast(self, card, player=None):
        player = self.p if player is None else player
        self.assertTrue(self.t.cast(self.t.action_for_card(player, card)))

    def test_live_policy_same_engine_for_all_seats(self):
        for p in self.t.players:
            self.assertIsInstance(p.payment_policy, SourcePayment)
            self.assertIs(p.payment_policy.resources, self.r)
        self.assertIs(self.r.kernel, self.t.rules)

    def test_basic_payment_taps_actual_id_once(self):
        oid = self.source('Island')
        plan = self.r.pay(self.p.seat, Cost(blue=1))
        self.assertEqual([a.source_id for a in plan.activations], [oid])
        self.assertTrue(self.t.rules.get(oid).tapped)
        self.assertIsNone(self.r.plan(self.p.seat, Cost(blue=1)))

    def test_colorless_cannot_pay_blue(self):
        self.source('Sol Ring')
        self.assertIsNone(self.r.plan(self.p.seat, Cost(blue=1)))

    def test_red_cannot_pay_blue(self):
        self.source('Mountain')
        self.assertIsNone(self.r.plan(self.p.seat, Cost(blue=1)))

    def test_opponent_sources_unavailable(self):
        self.source('Opponent land', seat=1)
        self.assertIsNone(self.r.plan(self.p.seat, Cost(generic=1)))

    def test_signet_cannot_fund_itself(self):
        self.source('Izzet Signet')
        self.assertIsNone(self.r.plan(self.p.seat, Cost(blue=1)))

    def test_signet_funding_precedes_output(self):
        signet = self.source('Izzet Signet'); island = self.source('Island')
        plan = self.r.pay(self.p.seat, Cost(blue=1, red=1))
        self.assertEqual([a.source_id for a in plan.activations], [island, signet])
        self.assertEqual(plan.unused, ZERO)

    def test_signet_uses_floating_funding(self):
        signet = self.source('Izzet Signet')
        self.t.rules.mana_pools[self.p.seat] = C
        plan = self.r.pay(self.p.seat, Cost(blue=1, red=1))
        self.assertEqual([a.source_id for a in plan.activations], [signet])

    def test_filters_require_colored_funding(self):
        self.source('Cascade Bluffs'); self.source('Sol Ring')
        self.assertIsNone(self.r.plan(self.p.seat, Cost(blue=1)))

    def test_filter_turns_red_into_double_blue(self):
        filt = self.source('Cascade Bluffs'); mountain = self.source('Mountain')
        plan = self.r.pay(self.p.seat, Cost(blue=2))
        self.assertEqual([a.source_id for a in plan.activations], [mountain, filt])

    def test_signet_then_filter_order_found(self):
        filt = self.source('Cascade Bluffs'); signet = self.source('Izzet Signet')
        ring = self.source('Sol Ring')
        plan = self.r.pay(self.p.seat, Cost(blue=3))
        self.assertEqual([a.source_id for a in plan.activations], [ring, signet, filt])

    def test_floating_mana_preserved_between_payments(self):
        self.source('Sol Ring')
        self.r.pay(self.p.seat, Cost(generic=1))
        self.assertEqual(self.r.pool(self.p.seat), C)
        second = self.r.pay(self.p.seat, Cost(generic=1))
        self.assertFalse(second.activations)
        self.assertEqual(self.r.pool(self.p.seat), ZERO)

    def test_zero_cost_does_not_tap_or_empty_pool(self):
        oid = self.source('Island'); self.t.rules.mana_pools[self.p.seat] = R
        self.r.pay(self.p.seat, Cost())
        self.assertFalse(self.t.rules.get(oid).tapped)
        self.assertEqual(self.r.pool(self.p.seat), R)

    def test_treasure_sacrifices_real_object_and_ceases(self):
        obj = self.t.world.create_treasure(self.p)
        self.assertTrue(all(ability.output[0] == 0 for ability in self.r.abilities(obj)))
        self.r.pay(self.p.seat, Cost(blue=1))
        self.assertNotIn(obj.object_id, self.t.rules.objects)
        self.assertNotIn(obj.object_id, self.t.world.views)
        self.assertEqual(self.p.treasures, 0)
        self.assertNotIn('Treasure', self.p.graveyard)
        self.assertTrue(self.t.assert_consistent())

    def test_tapped_treasure_cannot_be_spent(self):
        obj = self.t.world.create_treasure(self.p)
        obj.tapped = True
        self.assertIsNone(self.r.plan(self.p.seat, Cost(generic=1)))

    def test_treasure_can_fund_signet(self):
        signet = self.source('Izzet Signet'); obj = self.t.world.create_treasure(self.p)
        plan = self.r.pay(self.p.seat, Cost(blue=1, red=1))
        self.assertEqual([a.source_id for a in plan.activations], [obj.object_id, signet])

    def test_prefer_reusable_source_over_treasure(self):
        self.t.world.create_treasure(self.p); island = self.source('Island')
        plan = self.r.pay(self.p.seat, Cost(blue=1))
        self.assertEqual(plan.activations[0].source_id, island)
        self.assertEqual(self.p.treasures, 1)

    def test_painland_color_deals_damage(self):
        self.source('Shivan Reef')
        self.r.pay(self.p.seat, Cost(blue=1))
        self.assertEqual(self.p.life, 39)
        self.assertEqual(self.p.damage_taken, 1)

    def test_painland_generic_uses_colorless_without_damage(self):
        self.source('Shivan Reef')
        self.r.pay(self.p.seat, Cost(generic=1))
        self.assertEqual(self.p.life, 40)

    def test_talisman_color_deals_damage(self):
        self.source('Talisman of Creativity')
        self.r.pay(self.p.seat, Cost(red=1))
        self.assertEqual(self.p.life, 39)

    def test_islet_pays_life_not_damage(self):
        self.source('Fiery Islet')
        self.r.pay(self.p.seat, Cost(red=1))
        self.assertEqual(self.p.life, 39)
        self.assertEqual(self.p.damage_taken, 0)

    def test_islet_cannot_pay_life_unavailable(self):
        self.source('Fiery Islet'); self.p.life = 0
        self.assertIsNone(self.r.plan(self.p.seat, Cost(blue=1)))

    def test_mana_payment_life_loss_removes_cast_spell_before_response(self):
        self.clear_hands(); self.source('Fiery Islet'); self.p.life = 1
        self.cast(self.give('Preordain'))
        self.assertIsNotNone(self.p.eliminated_round)
        self.assertFalse(any(o.owner == self.p.seat for o in self.t.rules.objects.values()))
        self.assertEqual(self.r.pool(self.p.seat), ZERO)

    def test_stale_plan_after_tap_rejected_without_spending(self):
        oid = self.source('Island'); plan = self.r.plan(self.p.seat, Cost(blue=1))
        self.t.rules.get(oid).tapped = True
        with self.assertRaises(ValueError): self.r.pay(self.p.seat, Cost(blue=1), plan)
        self.assertEqual(self.r.pool(self.p.seat), ZERO)

    def test_stale_plan_after_destroy_rejected(self):
        oid = self.source('Island'); plan = self.r.plan(self.p.seat, Cost(blue=1))
        self.t.world.destroy(oid)
        with self.assertRaises(ValueError): self.r.pay(self.p.seat, Cost(blue=1), plan)

    def test_forged_plan_rejected_before_mutation(self):
        oid = self.source('Island'); plan = self.r.plan(self.p.seat, Cost(blue=1))
        forged = replace(plan, unused=(5, 5, 5))
        with self.assertRaises(ValueError): self.r.pay(self.p.seat, Cost(blue=1), forged)
        self.assertFalse(self.t.rules.get(oid).tapped)

    def test_planning_does_not_mutate_taps_life_or_pool(self):
        oid = self.source('Fiery Islet')
        self.r.plan(self.p.seat, Cost(blue=1))
        self.assertFalse(self.t.rules.get(oid).tapped)
        self.assertEqual(self.p.life, 40)
        self.assertEqual(self.r.pool(self.p.seat), ZERO)

    def test_planner_budget_fails_closed_without_payment(self):
        ids = [self.source('Island'), self.source('Mountain'), self.source('Sol Ring')]
        self.r.max_states = 1
        with self.assertRaises(SafetyStop): self.r.pay(self.p.seat, Cost(blue=9))
        self.assertFalse(any(self.t.rules.get(x).tapped for x in ids))
        self.assertFalse(self.r.payments)

    def test_interchangeable_sources_grouped(self):
        for _ in range(30): self.source('Island', duplicate=True)
        self.r.max_states = 100
        plan = self.r.plan(self.p.seat, Cost(blue=20))
        self.assertEqual(len(plan.activations), 20)
        self.assertLessEqual(plan.states, 22)

    def test_untap_only_active_players_sources(self):
        own = self.source('Island'); other = self.source('Other', seat=1)
        self.t.rules.get(own).tapped = self.t.rules.get(other).tapped = True
        self.r.untap(self.p.seat)
        self.assertFalse(self.t.rules.get(own).tapped)
        self.assertTrue(self.t.rules.get(other).tapped)

    def test_pools_empty_all_players_at_phase_boundary(self):
        self.t.rules.mana_pools = {seat: (1, 2, 3) for seat in range(4)}
        self.r.empty_pools()
        self.assertEqual(list(self.t.rules.mana_pools.values()), [ZERO] * 4)

    def test_main_phase_empties_floating_mana(self):
        self.p.pilot = type('Pass', (), {'select_action': lambda *args: None})()
        self.t.rules.mana_pools[self.p.seat] = (0, 2, 0)
        self.t.main(self.p)
        self.assertEqual(self.r.pool(self.p.seat), ZERO)

    def test_mana_fields_are_readonly(self):
        with self.assertRaises(TypeError): self.p.mana = 10
        with self.assertRaises(TypeError): self.p.ready_sources = ['Island']
        with self.assertRaises(TypeError): self.p.floating = (5, 0, 0)
        with self.assertRaises(TypeError): self.p.treasures = 5

    def test_new_rock_usable_same_main_phase(self):
        self.clear_hands(); self.source('Island')
        self.cast(self.give('Sol Ring'))
        oid = self.p.permanents[0].id
        self.assertFalse(self.t.rules.get(oid).tapped)
        plan = self.r.pay(self.p.seat, Cost(generic=2))
        self.assertEqual(plan.activations[0].source_id, oid)

    def test_cast_and_counter_pay_with_actual_sources(self):
        self.clear_hands(); actor = self.t.players[2]
        for i in range(10): self.source('Synthetic ' + str(i), seat=2)
        self.source('Island'); self.source('Island')
        self.give('Counterspell')
        self.t.response_policy = lambda top, opts: next((o for o in opts if o[1] is self.p), None)
        self.cast(self.give(None, actor, effect='creature'), actor)
        self.assertEqual(self.t.spell_stack.spells_countered, 1)
        self.assertEqual(len(self.r.payments), 2)
        self.assertTrue(self.t.assert_consistent())

    def test_new_cast_trigger_treasure_cannot_pay_own_spell(self):
        self.clear_hands()
        for _ in range(3): self.source('Island')
        self.source('Mountain')
        self.cast(self.give('Storm-Kiln Artist'))
        card = self.give('Preordain')
        # Artist is present, but all mana is tapped and its prospective cast
        # trigger cannot finance the spell whose casting would trigger it.
        self.assertFalse(self.t.cast(self.t.action_for(self.p, card)))
        self.assertEqual(len(self.r.payments), 1)
        self.assertEqual(self.p.treasures, 0)

    def test_spell_cost_colored_pips_not_waived(self):
        a = base.Action(self.p.seat, 'Fake', 'instant', 'draw', 0, parameters={'U': 1})
        with self.assertRaises(ValueError): self.p.payment_policy.can_pay(self.p, a)

    def test_unfetched_passage_produces_no_mana(self):
        self.source('Fabled Passage')
        self.assertIsNone(self.r.plan(self.p.seat, Cost(generic=1)))

    def test_pathway_face_controls_color(self):
        oid = self.source('Riverglide Pathway')
        self.t.rules.resource_names[oid] = 'Riverglide Pathway [R]'
        self.assertIsNone(self.r.plan(self.p.seat, Cost(blue=1)))
        self.assertIsNotNone(self.r.plan(self.p.seat, Cost(red=1)))

    def test_orchard_does_not_invent_colors_from_synthetic_opponent(self):
        self.source('Exotic Orchard'); self.source('Synthetic land', seat=1)
        self.assertIsNone(self.r.plan(self.p.seat, Cost(generic=1)))
        self.assertIsNone(self.r.plan(self.p.seat, Cost(blue=1)))

    def test_fellwar_does_not_invent_colors_from_colorless_land(self):
        self.source('Fellwar Stone'); self.source('Synthetic land', seat=1)
        self.assertIsNone(self.r.plan(self.p.seat, Cost(generic=1)))

    def test_unknown_named_source_fails_closed(self):
        obj = self.t.zones.kernel.add(
            self.t.zones.register(base.CardSpec('Unknown land', 'land', 0, 'land', 'none'), True),
            self.p.seat, zone='battlefield')
        self.t.world.views[obj.object_id] = WorldEntry(self.p, None, 'resource')
        self.assertIsNone(self.r.plan(self.p.seat, Cost(generic=1)))

    def test_seeded_source_games_reproduce(self):
        a = ManaTable(seed=104, trace=True).run(8)
        b = ManaTable(seed=104, trace=True).run(8)
        self.assertEqual(a.events, b.events)
        self.assertEqual(a.resources.payments, b.resources.payments)

    def test_portable_all_seats_conserve_cards(self):
        for seat in range(4):
            kinds = ['aggro', 'control', 'combo']; kinds.insert(seat, 'magnus')
            table = ManaTable(kinds, seed=104).run(10)
            self.assertIsNone(table.safety_stop)
            self.assertTrue(table.assert_consistent())
            for p in table.players:
                n = sum(not obj.token and obj.owner == p.seat for obj in table.rules.objects.values())
                self.assertEqual(n, 0 if p.eliminated_round is not None else 100 if p is table.details else 99)

    def test_cast_trigger_treasure_can_pay_a_later_spell(self):
        self.clear_hands()
        islands = [self.source('Island') for _ in range(3)]
        self.source('Mountain')
        self.cast(self.give('Storm-Kiln Artist'))
        self.t.rules.get(islands[0]).tapped = False
        self.cast(self.give('Preordain'))
        treasure = next(o.object_id for o in self.t.rules.on_battlefield() if o.token and o.card.name == 'Treasure')
        self.cast(self.give('Ponder'))
        self.assertNotIn(treasure, self.t.rules.objects)
        self.assertIn(treasure, self.r.payments[-1]['sources'])
        self.assertEqual(self.p.treasures, 1)

    def test_opposing_colored_land_changes_fellwar_options(self):
        self.source('Fellwar Stone')
        island = self.source('Island')
        self.t.rules.get(island).controller = 1
        self.t.rules.get(island).tapped = True  # 'could produce' ignores tap status
        self.assertIsNotNone(self.r.plan(self.p.seat, Cost(blue=1)))
        self.t.world.move(island, 'graveyard', 'destroy')
        self.assertIsNone(self.r.plan(self.p.seat, Cost(blue=1)))

    def test_orchard_dependency_cycle_does_not_invent_mana(self):
        self.source('Exotic Orchard')
        other = self.source('Exotic Orchard', duplicate=True)
        self.t.rules.get(other).controller = 1
        self.assertIsNone(self.r.plan(self.p.seat, Cost(generic=1)))

    def test_grouped_planner_matches_small_exhaustive_reference(self):
        from collections import deque
        import random
        rng = random.Random(20261028)
        for _ in range(30):
            self.setUp()
            for _ in range(rng.randrange(1, 6)):
                self.source(rng.choice(('Island', 'Mountain', 'Sol Ring', 'Izzet Signet', 'Cascade Bluffs')), duplicate=True)
            cost = Cost(rng.randrange(3), rng.randrange(3), rng.randrange(3))
            sources = self.r.sources(self.p.seat)
            queue = deque([(0, ZERO)]); seen = set(); possible = False
            def leftovers(pool, required):
                c, u, r = pool
                u -= required.blue; r -= required.red
                if min(u, r) < 0: return []
                return [(c-a, u-b, r-d) for a in range(c+1) for b in range(u+1) for d in range(r+1)
                        if a+b+d == required.generic]
            while queue:
                mask, pool = queue.popleft()
                if (mask, pool) in seen: continue
                seen.add((mask, pool))
                if leftovers(pool, cost): possible = True; break
                for i, (_, abilities) in enumerate(sources):
                    if mask & (1 << i): continue
                    for ability in abilities:
                        for left in leftovers(pool, ability.cost):
                            queue.append((mask | (1 << i), tuple(left[j]+ability.output[j] for j in range(3))))
            self.assertEqual(self.r.plan(self.p.seat, cost) is not None, possible)

    def test_diagnostics_claim_source_payment_but_not_general_priority(self):
        d = self.t.diagnostics()
        self.assertTrue(d['v9c']['source_backed_live_payment'])
        self.assertIn('counter-only', d['v9c']['limits'][0])


if __name__ == '__main__': unittest.main(verbosity=2)
