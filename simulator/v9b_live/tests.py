"""Live migration acceptance tests: inventories, stack timing and removals."""
import unittest
from dataclasses import FrozenInstanceError
from live import LiveTable
from rules import SafetyLimits
import integrated as v6


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.t = LiveTable(seed=71)
        self.t.response_policy = lambda top, opts: None

    def clear_hands(self):
        for p in self.t.players:
            for oid in self.t.zones.ids(p.seat, 'hand'):
                self.t.zones.move(oid, 'library')

    def give(self, p, name=None, effect=None):
        card = next(c for c in p.library + p.hand if (name is None or c.name == name)
                    and (effect is None or c.effect == effect))
        if card not in p.hand:
            oid = self.t.zones.move(card.object_id, 'hand')
            card = next(c for c in p.hand if c.object_id == oid)
        return card

    def ready(self, p):
        p.mana = 30
        if p is self.t.details:
            p.ready_sources = ['Island'] * 10 + ['Mountain'] * 10
            p.floating = (0, 0, 0)

    def cast(self, p, card):
        self.ready(p)
        action = self.t.action_for_card(p, card)
        self.assertTrue(self.t.cast(action))
        return action

    def physical_counts(self):
        return [sum(not o.token and o.owner == p.seat for o in self.t.rules.objects.values())
                for p in self.t.players]

    def test_initial_inventory_397_physical_cards(self):
        self.assertEqual(self.physical_counts(), [100, 99, 99, 99])
        self.assertEqual([len(p.hand) for p in self.t.players], [7] * 4)
        self.assertIs(self.t.zones.kernel, self.t.rules)
        self.assertIs(self.t.world.kernel, self.t.rules)

    def test_hand_and_library_are_readonly(self):
        p = self.t.details
        with self.assertRaises(AttributeError): p.hand.append(p.hand[0])
        with self.assertRaises(TypeError): p.hand = []
        with self.assertRaises(TypeError): p.library = []
        with self.assertRaises(FrozenInstanceError): p.hand[0].object_id = 0
        with self.assertRaises(TypeError): p.hand[0].parameters['coverage'] = 'pretend'

    def test_draw_uses_fresh_id_and_same_definition(self):
        p = self.t.players[2]; before = p.library[-1]
        p.draw()
        self.assertNotIn(before.object_id, self.t.rules.objects)
        self.assertEqual(p.hand[-1].definition_id, before.definition_id)
        self.assertEqual(self.physical_counts(), [100, 99, 99, 99])

    def test_mulligan_reuses_inventory(self):
        p = self.t.details
        before = sorted(o.card.card_id for o in self.t.rules.objects.values() if o.owner == p.seat)
        p.mulligan()
        after = sorted(o.card.card_id for o in self.t.rules.objects.values() if o.owner == p.seat)
        self.assertEqual(before, after)
        self.assertEqual(len(p.hand), 7)
        self.assertTrue(self.t.assert_consistent())

    def test_empty_draw_has_no_synthetic_card(self):
        p = self.t.players[2]
        self.t.zones.mill(p.seat, len(p.library))
        before = len(p.hand)
        p.draw(2)
        self.assertFalse(p.alive)
        self.assertEqual(len(p.hand), before)
        self.t.eliminate(p, 'empty_library')
        self.assertEqual(self.physical_counts()[2], 0)

    def test_diagnostic_opening_conserves_cards(self):
        t = LiveTable(opening=('Island', 'Island', 'Sol Ring', 'Preordain'))
        self.assertEqual([c.name for c in t.details.hand[:4]], ['Island', 'Island', 'Sol Ring', 'Preordain'])
        self.assertEqual(sum(not o.token for o in t.rules.objects.values()), 397)

    def test_invalid_opening_fails(self):
        with self.assertRaises(ValueError): LiveTable(opening=('Not in deck',))

    def test_named_creature_reuses_physical_spell(self):
        self.clear_hands(); p = self.t.details
        card = self.give(p, 'Young Pyromancer'); definition = card.definition_id
        self.cast(p, card)
        matching = [o for o in self.t.rules.objects.values() if o.card.card_id == definition]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].zone, 'battlefield')
        self.assertIn(matching[0].object_id, self.t.world.views)
        self.assertEqual(self.physical_counts(), [100, 99, 99, 99])

    def test_abstract_creature_conserved(self):
        self.clear_hands(); p = self.t.players[1]
        card = self.give(p, effect='creature')
        self.cast(p, card)
        self.assertEqual(self.physical_counts()[1], 99)
        self.assertEqual(len(p.creatures), 1)

    def test_abstract_artifact_conserved(self):
        self.clear_hands(); p = self.t.players[1]
        self.cast(p, self.give(p, effect='ramp'))
        self.assertEqual(self.physical_counts()[1], 99)
        self.assertEqual(len(p.permanents), 1)

    def test_named_rock_and_destruction(self):
        self.clear_hands(); p = self.t.details
        self.cast(p, self.give(p, 'Sol Ring'))
        self.assertEqual(p.rock_names, ['Sol Ring'])
        oid = p.permanents[0].id
        self.t.world.destroy(oid)
        self.assertNotIn('Sol Ring', p.rock_names)
        self.assertIn('Sol Ring', p.graveyard)
        self.assertEqual(self.physical_counts()[0], 100)

    def test_instant_not_in_graveyard_during_cast_event(self):
        self.clear_hands(); p = self.t.details; observations = []
        def listen(table, event, action, payload):
            if event == 'spell_cast':
                observations.append((self.t.zones.names(p.seat, 'stack'), p.graveyard))
        self.t.on_event(listen)
        self.cast(p, self.give(p, 'Preordain'))
        self.assertEqual(observations, [(('Preordain',), ())])
        self.assertIn('Preordain', p.graveyard)
        self.assertFalse(self.t.zones.ids(p.seat, 'stack'))

    def test_countered_spell_and_counter_both_move_to_graveyard(self):
        self.clear_hands(); p = self.t.players[1]; q = self.t.details
        self.give(q, 'Counterspell'); self.ready(q)
        self.t.response_policy = lambda top, opts: next((o for o in opts if o[1] is q), None)
        card = self.give(p, effect='creature'); name = card.name
        self.cast(p, card)
        self.assertIn(name, p.graveyard)
        self.assertIn('Counterspell', q.graveyard)
        self.assertFalse(p.creatures)
        self.assertEqual(self.t.spell_stack.spells_countered, 1)
        self.assertTrue(self.t.assert_consistent())

    def test_counter_counter_moves_all_cards_once(self):
        self.clear_hands(); p = self.t.players[2]; q = self.t.details
        original = self.give(p, effect='creature')
        own_counter = self.give(p, effect='counter')
        self.give(q, 'Counterspell'); self.ready(q)
        def policy(top, opts):
            actor = q if top.action.source == original.name else p
            return next((o for o in opts if o[1] is actor), None)
        self.t.response_policy = policy
        self.cast(p, original)
        self.assertEqual(len(p.creatures), 1)
        self.assertIn(own_counter.name, p.graveyard)
        self.assertIn('Counterspell', q.graveyard)
        self.assertEqual(self.t.spell_stack.max_depth_seen, 3)
        self.assertEqual(self.physical_counts(), [100, 99, 99, 99])

    def test_commander_counter_returns_to_command_with_tax(self):
        self.clear_hands(); p = self.t.details; q = self.t.players[2]
        self.give(q, effect='counter'); self.ready(q)
        self.t.response_policy = lambda top, opts: next((o for o in opts if o[1] is q), None)
        self.cast(p, self.t.zones.views(p.seat, 'command')[0])
        self.assertTrue(p.commander_in_zone)
        self.assertEqual(p.commander_casts, 1)
        self.assertEqual(self.t.action_for(p, v6.named_spec('Magnus the Red')).cost, 7)
        self.assertEqual(self.physical_counts()[0], 100)

    def test_commander_death_and_recast(self):
        self.clear_hands(); p = self.t.details
        self.cast(p, self.t.zones.views(p.seat, 'command')[0])
        old = p.creatures[0].id
        self.t.world.destroy(old)
        self.assertTrue(p.commander_in_zone)
        self.cast(p, self.t.zones.views(p.seat, 'command')[0])
        self.assertFalse(p.commander_in_zone)
        self.assertNotEqual(p.creatures[0].id, old)
        self.assertEqual(p.commander_casts, 2)

    def test_bounce_returns_same_card_with_fresh_id(self):
        self.clear_hands(); p = self.t.details
        self.cast(p, self.give(p, 'Young Pyromancer'))
        oid = p.creatures[0].id
        self.t.world.move(oid, 'hand', 'bounce')
        self.assertEqual([c.name for c in p.hand], ['Young Pyromancer'])
        self.assertFalse(p.creatures)
        self.assertTrue(self.t.assert_consistent())

    def test_token_dies_without_graveyard_card(self):
        p = self.t.details
        creature = self.t.add_creature(p, 1, 1, 'Elemental', token=True)
        self.t.world.destroy(creature.id)
        self.assertNotIn('Elemental', p.graveyard)
        self.assertTrue(self.t.assert_consistent())

    def test_cleanup_reconciles_state_based_death(self):
        self.clear_hands(); p = self.t.details
        self.cast(p, self.give(p, 'Young Pyromancer'))
        self.t.world.modifier(p.creatures[0], toughness=-2)
        self.t.world.cleanup()
        self.assertFalse(p.creatures)
        self.assertIn('Young Pyromancer', p.graveyard)
        self.assertTrue(self.t.assert_consistent())

    def test_land_has_shared_identity_and_drop_limit(self):
        self.clear_hands(); p = self.t.details
        land = self.give(p, 'Island'); other = self.give(p, 'Mountain')
        self.t.safe_runner.new_turn(1)
        self.t.play_land(p, land, 1)
        self.assertEqual(p.lands, 1)
        self.assertEqual(p.land_names, ['Island'])
        self.assertIn(self.t.zones.ids(p.seat, 'battlefield')[0], self.t.world.views)
        with self.assertRaises(ValueError): self.t.play_land(p, other, 1)

    def test_fetch_sacrifice_search_shuffle_and_conservation(self):
        self.clear_hands(); p = self.t.details
        land = self.give(p, 'Fabled Passage')
        self.t.safe_runner.new_turn(1)
        before = len(p.library)
        self.t.play_land(p, land, 1)
        self.assertIn('Fabled Passage', p.graveyard)
        self.assertEqual(len(p.library), before - 1)
        self.assertEqual(p.lands, 1)
        self.assertTrue(self.t.rules.get(self.t.zones.ids(p.seat, 'battlefield')[0]).tapped)
        self.assertTrue(any(op[0] == 'shuffle' for op in self.t.zones.operations))
        self.assertEqual(self.physical_counts()[0], 100)

    def test_brainstorm_returns_two_physical_cards(self):
        self.clear_hands(); p = self.t.details
        card = self.give(p, 'Brainstorm'); before = len(p.library)
        self.cast(p, card)
        self.assertEqual(len(p.library), before - 1)
        self.assertEqual(len(p.hand), 1)
        self.assertIn('Brainstorm', p.graveyard)

    def test_frantic_search_discards_real_cards(self):
        self.clear_hands(); p = self.t.details
        self.cast(p, self.give(p, 'Frantic Search'))
        self.assertEqual(len(p.graveyard), 3)
        self.assertFalse(p.hand)

    def test_cleanup_discards_excess_instead_of_deleting(self):
        p = self.t.details
        p.draw(4)
        p.pilot = type('Pass', (), {'select_action': lambda *args: None})()
        self.t.main(p)
        self.assertEqual(len(p.hand), 7)
        self.assertEqual(len(p.graveyard), 4)
        self.assertEqual(self.physical_counts()[0], 100)

    def test_elimination_removes_every_zone_without_dies(self):
        self.clear_hands(); p = self.t.details
        self.cast(p, self.give(p, 'Young Pyromancer'))
        before = sum(e.name == 'dies' for e in self.t.rules.events)
        p.life = 0; self.t.eliminate(p, 'test')
        self.assertFalse(any(o.owner == p.seat for o in self.t.rules.objects.values()))
        self.assertEqual(sum(e.name == 'dies' for e in self.t.rules.events), before)
        self.assertTrue(self.t.assert_consistent())

    def test_player_leaving_with_counter_on_stack_does_not_counter(self):
        self.clear_hands(); p = self.t.players[1]; q = self.t.details
        self.give(q, 'Counterspell'); self.ready(q)
        self.t.response_policy = lambda top, opts: next((o for o in opts if o[1] is q), None)
        def leave(table, event, action, payload):
            if event == 'spell_cast' and action.actor == q.seat:
                q.life = 0; table.eliminate(q, 'test')
        self.t.on_event(leave)
        self.cast(p, self.give(p, effect='creature'))
        self.assertEqual(len(p.creatures), 1)
        self.assertEqual(self.t.spell_stack.spells_countered, 0)
        self.assertTrue(self.t.assert_consistent())

    def test_empty_library_during_selection_removes_stack_card(self):
        self.clear_hands(); p = self.t.details
        card = self.give(p, 'Brainstorm')
        self.t.zones.mill(p.seat, len(p.library))
        self.cast(p, card)
        self.assertIsNotNone(p.eliminated_round)
        self.assertEqual(self.physical_counts()[0], 0)

    def test_unsupported_card_stays_in_hand(self):
        self.clear_hands(); p = self.t.details
        card = self.give(p, effect='unsupported'); self.ready(p)
        action = self.t.action_for(p, card)
        with self.assertRaises(ValueError): self.t.cast(action)
        self.assertIn(card, p.hand)

    def test_fabricated_cost_rejected_before_spending(self):
        self.clear_hands(); p = self.t.details
        card = self.give(p, 'Preordain'); self.ready(p)
        action = self.t.action_for(p, card); action.cost = 0
        before = p.mana
        with self.assertRaises(ValueError): self.t.cast(action)
        self.assertEqual(p.mana, before)
        self.assertIn(card, p.hand)

    def test_multiple_real_decks_still_rejected(self):
        with self.assertRaises(NotImplementedError): LiveTable(['magnus', 'magnus', 'aggro', 'control'])

    def test_seeded_events_reproduce(self):
        a = LiveTable(seed=104, trace=True).run(8)
        b = LiveTable(seed=104, trace=True).run(8)
        self.assertEqual(a.events, b.events)
        self.assertEqual(a.turns, b.turns)

    def test_all_seats_and_physical_conservation(self):
        for seat in range(4):
            kinds = ['aggro', 'control', 'combo']; kinds.insert(seat, 'magnus')
            t = LiveTable(kinds, seed=104).run(10)
            self.assertTrue(t.assert_consistent())
            self.assertIs(t.details, t.players[seat])
            for p in t.players:
                actual = sum(not o.token and o.owner == p.seat for o in t.rules.objects.values())
                self.assertEqual(actual, 0 if p.eliminated_round is not None else 100 if p is t.details else 99)

    def test_safety_stop_stays_unresolved_and_indexed(self):
        self.t.safe_runner.limits = SafetyLimits(max_total_actions=1)
        self.t.run(8)
        self.assertEqual(self.t.win_reason, 'unresolved_safety_guard')
        self.assertIsNone(self.t.winner)
        self.assertTrue(self.t.assert_consistent())

    def test_live_diagnostics_do_not_claim_mana_or_full_priority(self):
        d = self.t.diagnostics()
        self.assertTrue(d['v9b']['authoritative_card_zones_in_live_game'])
        self.assertFalse(d['v9']['multi_detailed_games_supported'])
        self.assertIn('legacy mana', d['v9b']['limits'][0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
