"""Priority acceptance tests using real live zones/resources and declared fixtures."""
import unittest
from dataclasses import replace
from gameplay import PriorityTable
from abilities import ActivatedSpec, MIND_STONE_DRAW
from priority import Choice
from rules import Cost, TriggerResult, SafetyLimits
from kernel import WorldEntry
import simulation as base


class PriorityTests(unittest.TestCase):
    def setUp(self):
        self.t = PriorityTable(seed=71)
        self.t.priority_policy = lambda *args: None
        self.p = self.t.details
        self.clear_hands()
        for seat in range(4): self.t.rules.mana_pools[seat] = (20, 20, 20)

    def clear_hands(self):
        for p in self.t.players:
            for oid in self.t.zones.ids(p.seat, 'hand'): self.t.zones.move(oid, 'library')

    def give(self, name=None, p=None, effect=None):
        p = p or self.p
        card = next(c for c in p.hand + p.library if (name is None or c.name == name)
                    and (effect is None or c.effect == effect))
        if card not in p.hand:
            new = self.t.zones.move(card.object_id, 'hand')
            card = next(c for c in p.hand if c.object_id == new)
        return card

    def cast(self, card, p=None):
        p = p or self.p
        self.t.active_seat = p.seat; self.t.phase = 'main'
        self.assertTrue(self.t.cast(self.t.action_for_card(p, card)))

    def place(self, name):
        self.cast(self.give(name))
        return next(o.object_id for o in self.t.rules.on_battlefield() if o.card.name == name)

    def tokens(self):
        return [o for o in self.t.rules.on_battlefield() if o.token and 'creature' in o.types]

    def test_pass_cycle_before_single_resolution(self):
        self.t.turn_order = [0, 2, 1, 3]
        self.cast(self.give('Preordain'))
        log = self.t.spell_stack.history
        idx = next(i for i, e in enumerate(log) if e[0] == 'resolve')
        self.assertEqual([e[1] for e in log[:idx] if e[0] == 'pass'], [0, 2, 1, 3])

    def test_cast_trigger_is_frame_not_immediate_effect(self):
        self.place('Young Pyromancer'); snapshots = []
        def policy(seat, frames, choices):
            if frames: snapshots.append(([f.kind for f in frames], len(self.tokens())))
        self.t.priority_policy = policy
        self.cast(self.give('Preordain'))
        self.assertEqual(snapshots[0], (['spell', 'triggered'], 0))
        self.assertEqual(len(self.tokens()), 1)
        self.assertEqual(self.t.spell_stack.triggers_resolved, 1)

    def test_counter_underlying_spell_while_trigger_is_on_top(self):
        self.place('Young Pyromancer'); q = self.t.players[2]
        self.give(p=q, effect='counter'); before = len(self.p.library)
        def policy(seat, frames, choices):
            return next((c for c in choices if seat == q.seat and c.kind == 'spell'
                         and c.action.effect == 'counter'), None)
        self.t.priority_policy = policy
        self.cast(self.give('Preordain'))
        self.assertEqual(len(self.tokens()), 1)
        self.assertIn('Preordain', self.p.graveyard)
        # Giving Preordain from library removes one; no Preordain draw resolves.
        self.assertEqual(len(self.p.library), before - 1)
        self.assertEqual(self.t.spell_stack.spells_countered, 1)

    def test_removing_trigger_source_does_not_remove_ability(self):
        pyro = self.place('Young Pyromancer'); q = self.t.players[2]
        self.give(p=q, effect='remove')
        def policy(seat, frames, choices):
            return next((c for c in choices if seat == q.seat and c.kind == 'spell'
                         and c.action.effect == 'remove' and c.action.target_object == pyro), None)
        self.t.priority_policy = policy
        self.cast(self.give('Preordain'))
        self.assertNotIn(pyro, self.t.rules.objects)
        self.assertIn('Young Pyromancer', self.p.graveyard)
        self.assertEqual(len(self.tokens()), 1)
        self.assertTrue(self.t.assert_consistent())

    def test_doubled_trigger_has_two_separate_frames(self):
        self.place('Young Pyromancer'); self.place('Harmonic Prodigy')
        snapshots = []
        self.t.priority_policy = lambda seat, frames, choices: snapshots.append(tuple(f.kind for f in frames)) or None
        self.cast(self.give('Preordain'))
        self.assertEqual(snapshots[0], ('spell', 'triggered', 'triggered'))
        self.assertEqual(len(self.tokens()), 2)

    def test_apnap_placement_uses_turn_order(self):
        self.t.active_seat = 2; self.t.turn_order = [2, 0, 3, 1]
        for p in self.t.players:
            source = self.t.world.create_treasure(p)
            self.t.spell_stack.trigger(TriggerResult(source.object_id, p.seat, 'draw'))
        self.t.spell_stack.resolve()
        resolved = [e[3] for e in self.t.spell_stack.history if e[0] == 'resolve']
        self.assertEqual(resolved, [1, 3, 0, 2])

    def test_controller_orders_own_triggers(self):
        source = self.t.world.create_treasure(self.p)
        self.t.spell_stack.trigger(TriggerResult(source.object_id, 0, 'draw', quantity=2))
        ids = [f.frame_id for f in self.t.spell_stack.pending]
        self.t.trigger_order_policy = lambda seat, frames: reversed(frames)
        self.t.spell_stack.resolve()
        self.assertEqual([e[1] for e in self.t.spell_stack.history if e[0] == 'resolve'], ids)

    def test_invalid_trigger_order_fails_closed(self):
        source = self.t.world.create_treasure(self.p)
        self.t.spell_stack.trigger(TriggerResult(source.object_id, 0, 'draw'))
        self.t.trigger_order_policy = lambda *args: ()
        with self.assertRaises(ValueError): self.t.spell_stack.resolve()
        self.assertEqual(len(self.t.spell_stack.pending), 1)

    def test_counterspell_choices_never_target_ability(self):
        self.place('Young Pyromancer'); self.give('Counterspell')
        observations = []
        def policy(seat, frames, choices):
            for c in choices:
                if c.kind == 'spell' and c.action.effect == 'counter':
                    observations.append(self.t.spell_stack.get(c.action.target_object).kind)
        self.t.priority_policy = policy
        self.cast(self.give('Preordain'))
        self.assertTrue(observations)
        self.assertEqual(set(observations), {'spell'})

    def test_counter_counter_reopens_priority(self):
        q = self.t.players[2]
        original = self.give(p=q, effect='creature')
        self.give(p=q, effect='counter'); self.give('Counterspell')
        def policy(seat, frames, choices):
            for c in choices:
                if c.kind != 'spell' or c.action.effect != 'counter': continue
                target = self.t.spell_stack.get(c.action.target_object)
                if seat == 0 and target.action.source == original.name: return c
                if seat == q.seat and target.action.source == 'Counterspell': return c
        self.t.priority_policy = policy
        self.cast(original, q)
        self.assertEqual(len(q.creatures), 1)
        self.assertEqual(self.t.spell_stack.max_depth_seen, 3)
        self.assertIn('Counterspell', self.p.graveyard)
        # The active player gets priority after q's counter resolves.
        log = self.t.spell_stack.history
        index = next(i for i,e in enumerate(log) if e[0] == 'resolve')
        self.assertEqual(next(e[1] for e in log[index+1:] if e[0] == 'pass'), q.seat)

    def test_all_players_can_pass_even_if_counter_is_held(self):
        self.give('Counterspell')
        q = self.t.players[2]
        self.cast(self.give(p=q, effect='creature'), q)
        self.assertEqual(len(q.creatures), 1)
        self.assertEqual(self.t.spell_stack.spells_countered, 0)

    def test_instant_response_supported_beyond_counters(self):
        creature = self.place('Young Pyromancer')
        q = self.t.players[2]; self.give(p=q, effect='remove')
        acted = []
        def policy(seat, frames, choices):
            if acted or not frames: return
            selected = next((c for c in choices if c.kind == 'spell' and c.action.effect == 'remove'), None)
            if selected: acted.append(seat)
            return selected
        self.t.priority_policy = policy
        self.cast(self.give('Preordain'))
        self.assertEqual(acted, [q.seat])
        self.assertNotIn(creature, self.t.rules.objects)

    def test_sorcery_not_legal_in_response(self):
        self.give('Ponder'); seen = []
        def policy(seat, frames, choices):
            if frames: seen.extend(c.action.source for c in choices if c.kind == 'spell')
        self.t.priority_policy = policy
        self.cast(self.give('Preordain'))
        self.assertNotIn('Ponder', seen)

    def test_offturn_instant_cast_while_stack_empty(self):
        q = self.t.players[2]; card = self.give(p=q, effect='remove')
        self.place('Young Pyromancer')
        fired = []
        def policy(seat, frames, choices):
            if seat == q.seat and not frames and not fired:
                c = next((c for c in choices if c.kind == 'spell' and c.action.source == card.name), None)
                if c: fired.append(True)
                return c
        self.t.priority_policy = policy
        self.t.main(self.p)
        self.assertTrue(fired)
        self.assertFalse(self.p.creatures)

    def test_priority_holder_retains_after_cast(self):
        q = self.t.players[2]; self.give(p=q, effect='remove')
        self.place('Young Pyromancer')
        fired = []
        def policy(seat, frames, choices):
            if seat == q.seat and frames and not fired:
                c = next((c for c in choices if c.kind == 'spell' and c.action.effect == 'remove'), None)
                if c: fired.append(True)
                return c
        self.t.priority_policy = policy
        self.cast(self.give('Preordain'))
        log = self.t.spell_stack.history
        index = next(i for i,e in enumerate(log) if e == ('action', q.seat, 'spell'))
        self.assertEqual(next(e[1] for e in log[index+1:] if e[0] == 'pass'), q.seat)

    def test_passes_reset_after_a_player_acts(self):
        q = self.t.players[2]; self.place('Young Pyromancer'); self.give(p=q, effect='remove')
        self.t.spell_stack.history.clear(); fired = []
        def policy(seat, frames, choices):
            if seat == q.seat and frames and not fired:
                c = next((c for c in choices if c.kind == 'spell' and c.action.effect == 'remove'), None)
                if c: fired.append(True)
                return c
        self.t.priority_policy = policy
        self.cast(self.give('Preordain'))
        log = self.t.spell_stack.history
        index = next(i for i,e in enumerate(log) if e == ('action', q.seat, 'spell'))
        following = [e[1] for e in log[index+1:] if e[0] == 'pass'][:4]
        self.assertEqual(following, [2, 3, 0, 1])

    def test_mana_action_not_stack_object_and_retains_priority(self):
        card = self.give('Island')
        oid = self.t.zones.play_land(0, card.object_id)
        self.t.world.views[oid] = WorldEntry(self.p, None, 'resource')
        for seat in range(4): self.t.rules.mana_pools[seat] = (0, 0, 0)
        acted = []
        def policy(seat, frames, choices):
            if seat == 0 and not acted:
                c = next(c for c in choices if c.kind == 'mana')
                acted.append(True); return c
        self.t.priority_policy = policy
        self.t.main(self.p)
        self.assertFalse(self.t.spell_stack.frames)
        self.assertEqual(self.t.spell_stack.max_depth_seen, 0)
        self.assertTrue(self.t.rules.get(oid).tapped)
        log = self.t.spell_stack.history
        index = log.index(('action', 0, 'mana'))
        self.assertEqual(next(e[1] for e in log[index+1:] if e[0] == 'pass'), 0)
        self.assertEqual(self.t.resources.pool(0), (0, 0, 0))

    def test_no_cast_mid_resolution(self):
        other = self.give('Brainstorm'); attempts = []
        def listener(table, event, action, payload):
            if event == 'spell_resolved':
                with self.assertRaises(ValueError): table.cast(table.action_for(self.p, other))
                attempts.append(True)
        self.t.on_event(listener)
        self.cast(self.give('Preordain'))
        self.assertTrue(attempts)

    def test_wrong_holder_cannot_cast(self):
        card = self.give('Brainstorm'); self.t.spell_stack.running = True; self.t.spell_stack.holder = 1
        with self.assertRaises(ValueError): self.t.cast(self.t.action_for(self.p, card))
        self.t.spell_stack.running = False

    def test_noninstant_requires_own_main_phase(self):
        card = self.give('Young Pyromancer'); self.t.phase = 'combat'
        with self.assertRaises(ValueError): self.t.cast(self.t.action_for(self.p, card))

    def test_counter_requires_live_spell_target(self):
        card = self.give('Counterspell'); action = self.t.action_for(self.p, card)
        action.target_object = 999
        before = self.t.resources.pool(0)
        with self.assertRaises(ValueError): self.t.cast(action)
        self.assertIn(card, self.p.hand)
        self.assertEqual(self.t.resources.pool(0), before)

    def test_mind_stone_ability_pays_tap_and_sacrifice_before_response(self):
        oid = self.place('Mind Stone'); before = len(self.p.hand); snapshots = []
        def policy(seat, frames, choices):
            if frames: snapshots.append((frames[-1].kind, oid in self.t.rules.objects, len(self.p.hand)))
        self.t.priority_policy = policy
        self.t.activate_ability(0, oid, MIND_STONE_DRAW)
        self.assertEqual(snapshots[0], ('activated', False, before))
        self.assertIn('Mind Stone', self.p.graveyard)
        self.assertEqual(len(self.p.hand), before + 1)
        self.assertEqual(self.t.spell_stack.abilities_resolved, 1)

    def test_mind_stone_cannot_pay_for_own_tap_activation(self):
        oid = self.place('Mind Stone')
        self.t.rules.mana_pools[0] = (0, 0, 0)
        with self.assertRaises(ValueError): self.t.activate_ability(0, oid, MIND_STONE_DRAW)
        self.assertIn(oid, self.t.rules.objects)
        self.assertFalse(self.t.rules.get(oid).tapped)

    def test_mind_stone_can_use_other_source_funding(self):
        oid = self.place('Mind Stone'); card = self.give('Island')
        land = self.t.zones.play_land(0, card.object_id)
        self.t.world.views[land] = WorldEntry(self.p, None, 'resource')
        self.t.rules.mana_pools[0] = (0, 0, 0)
        self.t.activate_ability(0, oid, MIND_STONE_DRAW)
        self.assertTrue(self.t.rules.get(land).tapped)
        self.assertNotIn(oid, self.t.rules.objects)

    def test_tapped_ability_source_rejected(self):
        oid = self.place('Mind Stone'); self.t.rules.get(oid).tapped = True
        with self.assertRaises(ValueError): self.t.activate_ability(0, oid, MIND_STONE_DRAW)

    def test_opponents_ability_source_rejected(self):
        oid = self.place('Mind Stone')
        with self.assertRaises(ValueError): self.t.activate_ability(1, oid, MIND_STONE_DRAW)

    def test_unsupported_activation_rejected_before_cost(self):
        with self.assertRaises(NotImplementedError): ActivatedSpec('invented', operation='invented')

    def test_unregistered_activation_rejected(self):
        oid = self.place('Mind Stone'); fake = ActivatedSpec('different_draw')
        with self.assertRaises(ValueError): self.t.activate_ability(0, oid, fake)

    def test_declared_ability_can_counter_trigger_frame(self):
        self.place('Young Pyromancer')
        source = self.t.world.create_treasure(self.t.players[2])
        ability = ActivatedSpec('fixture_nullify', operation='counter_stack', target_kinds=frozenset({'triggered'}))
        self.t.register_activation('treasure', ability); used = []
        def policy(seat, frames, choices):
            if seat == 2 and not used:
                c = next((c for c in choices if c.kind == 'activate'), None)
                if c: used.append(True)
                return c
        self.t.priority_policy = policy
        self.cast(self.give('Preordain'))
        self.assertFalse(self.tokens())
        self.assertEqual(self.t.spell_stack.abilities_resolved, 1)

    def test_controller_departure_removes_queued_abilities(self):
        source = self.t.world.create_treasure(self.p)
        self.t.spell_stack.trigger(TriggerResult(source.object_id, 0, 'draw'))
        self.p.life = 0
        self.t.spell_stack.resolve()
        self.assertFalse(self.t.spell_stack.frames)
        self.assertFalse(self.t.spell_stack.pending)
        self.assertEqual(self.t.spell_stack.triggers_resolved, 0)

    def test_source_departure_does_not_remove_queued_trigger(self):
        source = self.t.world.create_treasure(self.p)
        self.t.spell_stack.trigger(TriggerResult(source.object_id, 0, 'draw'))
        self.t.world.move(source.object_id, 'graveyard', 'sacrifice')
        before = len(self.p.hand)
        self.t.spell_stack.resolve()
        self.assertEqual(len(self.p.hand), before + 1)

    def test_trigger_created_treasure_available_only_after_resolution(self):
        self.place('Storm-Kiln Artist'); snapshots = []
        def policy(seat, frames, choices):
            if frames: snapshots.append((frames[-1].kind, self.p.treasures))
        self.t.priority_policy = policy
        self.cast(self.give('Preordain'))
        self.assertEqual(snapshots[0], ('triggered', 0))
        self.assertIn(('spell', 1), snapshots)

    def test_new_trigger_waits_until_resolving_object_finishes(self):
        source = self.t.world.create_treasure(self.p); observations = []
        def listener(table, event, action, payload):
            if event == 'spell_resolved':
                table.spell_stack.trigger(TriggerResult(source.object_id, 0, 'draw'))
                observations.append((table.spell_stack.resolving, len(table.spell_stack.pending), len(table.spell_stack.frames)))
        self.t.on_event(listener)
        self.cast(self.give('Preordain'))
        self.assertEqual(observations, [(True, 1, 0)])
        self.assertEqual(self.t.spell_stack.triggers_resolved, 1)

    def test_invalid_policy_action_rejected(self):
        self.t.priority_policy = lambda *args: Choice('nonsense')
        with self.assertRaises(ValueError): self.t.main(self.p)

    def test_priority_pass_budget_stops_unresolved(self):
        self.t.spell_stack.max_window_passes = 1
        self.t.run(1)
        self.assertEqual(self.t.win_reason, 'unresolved_safety_guard')
        self.assertEqual(self.t.safety_stop, 'priority_pass_budget')
        self.assertIsNone(self.t.winner)

    def test_stack_depth_budget_stops_unresolved(self):
        self.t.safe_runner.limits = SafetyLimits(max_stack_depth=0)
        self.t.priority_policy = None
        self.t.run(2)
        self.assertEqual(self.t.win_reason, 'unresolved_safety_guard')
        self.assertIsNone(self.t.winner)

    def test_no_physical_card_for_ability_frame(self):
        oid = self.place('Mind Stone')
        before = sum(not o.token for o in self.t.rules.objects.values())
        self.t.activate_ability(0, oid, MIND_STONE_DRAW)
        self.assertEqual(sum(not o.token for o in self.t.rules.objects.values()), before)
        self.assertTrue(self.t.assert_consistent())

    def test_unknown_trigger_operation_fails_closed(self):
        with self.assertRaises(NotImplementedError): self.t.spell_stack.trigger(TriggerResult(0, 0, 'invented'))
        with self.assertRaises(ValueError): self.t.spell_stack.trigger(TriggerResult(0, 4, 'draw'))
        with self.assertRaises(ValueError): self.t.spell_stack.trigger(TriggerResult(0, 0, 'draw', quantity=0))
        with self.assertRaises(NotImplementedError): self.t.spell_stack.trigger(TriggerResult(0, 0, 'create_token'))

    def test_seeded_games_reproduce_priority_history(self):
        a = PriorityTable(seed=104, trace=True).run(8)
        b = PriorityTable(seed=104, trace=True).run(8)
        self.assertEqual(a.events, b.events)
        self.assertEqual(a.spell_stack.history, b.spell_stack.history)

    def test_all_seats_physical_conservation(self):
        for seat in range(4):
            names = ['aggro', 'control', 'combo']; names.insert(seat, 'magnus')
            t = PriorityTable(names, seed=104).run(10)
            self.assertTrue(t.assert_consistent())
            for p in t.players:
                actual = sum(not o.token and o.owner == p.seat for o in t.rules.objects.values())
                self.assertEqual(actual, 0 if p.eliminated_round is not None else 100 if p is t.details else 99)

    def test_removal_fizzles_when_response_removes_its_target(self):
        target_player = self.t.players[2]
        self.cast(self.give(p=target_player, effect='creature'), target_player)
        target = target_player.creatures[0].id
        responder = self.t.players[1]; self.give(p=responder, effect='remove')
        def policy(seat, frames, choices):
            return next((c for c in choices if seat == responder.seat and c.kind == 'spell'
                         and c.action.effect == 'remove' and c.action.target_object == target), None)
        self.t.priority_policy = policy
        self.cast(self.give('Pongify'))
        self.assertNotIn(target, self.t.rules.objects)
        self.assertFalse(any(o.card.name == 'Ape (Pongify)' for o in self.t.rules.on_battlefield()))
        self.assertEqual(self.t.spell_stack.fizzled, 1)
        self.assertIn('Pongify', self.p.graveyard)

    def test_two_counters_same_target_second_one_fizzles(self):
        actor = self.t.players[1]; original = self.give(p=actor, effect='creature')
        responder = self.t.players[2]; self.give(p=responder, effect='counter')
        self.give('Counterspell')
        used = set()
        def policy(seat, frames, choices):
            if seat not in (0, 2) or seat in used: return
            if seat == 2 and 0 not in used: return
            choice = next((c for c in choices if c.kind == 'spell' and c.action.effect == 'counter'
                           and self.t.spell_stack.get(c.action.target_object).label == original.name), None)
            if choice: used.add(seat)
            return choice
        self.t.priority_policy = policy
        self.cast(original, actor)
        self.assertEqual(self.t.spell_stack.spells_countered, 1)
        self.assertEqual(self.t.spell_stack.fizzled, 1)
        self.assertFalse(actor.creatures)

    def test_can_counter_own_spell(self):
        self.give('Counterspell')
        def policy(seat, frames, choices):
            return next((c for c in choices if seat == 0 and c.kind == 'spell' and c.action.effect == 'counter'
                         and self.t.spell_stack.get(c.action.target_object).label == 'Preordain'), None)
        self.t.priority_policy = policy
        self.cast(self.give('Preordain'))
        self.assertEqual(self.t.spell_stack.spells_countered, 1)

    def test_activated_ability_can_be_used_offturn_with_priority(self):
        oid = self.place('Mind Stone'); actor = self.t.players[2]
        before = len(self.p.hand)
        def policy(seat, frames, choices):
            return next((c for c in choices if seat == 0 and frames and c.kind == 'activate'), None)
        self.t.priority_policy = policy
        self.cast(self.give(p=actor, effect='creature'), actor)
        self.assertNotIn(oid, self.t.rules.objects)
        self.assertEqual(len(self.p.hand), before + 1)

    def test_activation_is_not_a_spell_cast(self):
        self.place('Young Pyromancer'); oid = self.place('Mind Stone')
        self.t.activate_ability(0, oid, MIND_STONE_DRAW)
        self.assertFalse(self.tokens())

    def test_ability_counter_works_after_its_own_source_sacrifice(self):
        oid = self.place('Mind Stone'); before = len(self.p.hand)
        nullifier = self.t.world.create_treasure(self.t.players[2])
        specification = ActivatedSpec('fixture_nullify', sacrifice=True, operation='counter_stack',
                                      target_kinds=frozenset({'activated'}))
        self.t.register_activation('treasure', specification)
        def policy(seat, frames, choices):
            return next((c for c in choices if seat == 2 and c.kind == 'activate'), None)
        self.t.priority_policy = policy
        self.t.activate_ability(0, oid, MIND_STONE_DRAW)
        self.assertEqual(len(self.p.hand), before)
        self.assertNotIn(nullifier.object_id, self.t.rules.objects)
        self.assertEqual(self.t.spell_stack.abilities_resolved, 1)

    def test_forged_trigger_order_frame_rejected(self):
        source = self.t.world.create_treasure(self.p)
        self.t.spell_stack.trigger(TriggerResult(source.object_id, 0, 'draw'))
        self.t.trigger_order_policy = lambda seat, frames: (replace(frames[0], controller=1),)
        with self.assertRaises(ValueError): self.t.spell_stack.resolve()

    def test_new_card_drawn_by_trigger_can_be_cast_before_original_spell(self):
        self.place('Archmage Emeritus'); card = self.give('Brainstorm')
        self.t.zones.move(card.object_id, 'library')  # draw this exact card next
        used = []
        def policy(seat, frames, choices):
            if seat == 0 and frames and not used:
                choice = next((c for c in choices if c.kind == 'spell' and c.action.source == 'Brainstorm'), None)
                if choice: used.append(tuple(f.label for f in frames))
                return choice
        self.t.priority_policy = policy
        self.cast(self.give('Preordain'))
        self.assertEqual(used, [('Preordain',)])
        self.assertEqual(self.t.spell_stack.triggers_resolved, 2)

    def test_magnus_combat_trigger_uses_priority_stack(self):
        self.cast(self.t.zones.views(0, 'command')[0])
        magnus = self.p.creatures[0]
        self.t.current_attacker_id = magnus.id; self.t.phase = 'combat'
        before = self.t.spell_stack.triggers_resolved
        self.t.damage(self.t.players[1], 4, self.p, 'combat')
        self.assertEqual(self.t.spell_stack.triggers_resolved, before + 1)
        self.assertTrue(any(o.card.name == 'Spawn' for o in self.t.rules.on_battlefield()))

    def test_life_zero_during_cast_payment_removes_spell_before_priority(self):
        card = self.give('Fiery Islet')
        land = self.t.zones.play_land(0, card.object_id)
        self.t.world.views[land] = WorldEntry(self.p, None, 'resource')
        self.t.rules.mana_pools[0] = (0, 0, 0); self.p.life = 1
        self.cast(self.give('Preordain'))
        self.assertIsNotNone(self.p.eliminated_round)
        self.assertFalse(self.t.spell_stack.frames)
        self.assertFalse(self.t.zones._pending)
        self.assertTrue(self.t.assert_consistent())

    def test_diagnostics_are_explicit_about_remaining_gates(self):
        d = self.t.diagnostics()
        self.assertTrue(d['v10']['typed_priority_live'])
        self.assertIn('coarse', d['v10']['limits'][1])


if __name__ == '__main__': unittest.main(verbosity=2)
