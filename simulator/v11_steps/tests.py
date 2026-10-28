"""Focused turn/step, simultaneous combat and expanded-card interaction checks."""
import unittest
from dataclasses import replace
from stepped import StepTable
from driver import StepDriver, STEPS
from rules import Cost, Modifier
from kernel import WorldEntry
import simulation as base


class RulesTests(unittest.TestCase):
    def setUp(self):
        self.t = StepTable(seed=71)
        self.t.priority_policy = lambda *args: None
        self.p = self.t.details
        self.clear_hands()
        for seat in range(4): self.t.rules.mana_pools[seat] = (30, 30, 30)

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

    def cast(self, card, p=None, **options):
        p = p or self.p; self.t.active_seat = p.seat; self.t.phase = 'main'
        a = self.t.action_with_options(p, card, **options) if options else self.t.action_for_card(p, card)
        self.assertTrue(self.t.cast(a)); return a

    def place(self, name):
        self.cast(self.give(name))
        return next(o.object_id for o in self.t.rules.on_battlefield() if o.card.name == name)

    def creature(self, p, power=3, toughness=3, keywords=()):
        return self.t.add_creature(p, power, toughness, 'declared fixture', token=True, keywords=keywords)

    def land(self, name='Island', p=None):
        p = p or self.p
        card = self.give(name, p)
        oid = self.t.zones.play_land(p.seat, card.object_id)
        self.t.world.views[oid] = WorldEntry(p, None, 'resource')
        return oid

    def test_expanded_cards_have_correct_types(self):
        for name, typ in [('Abrade','instant'), ('Capsize','instant'), ('Arcane Adaptation','enchantment')]:
            c = self.give(name)
            self.assertEqual(c.card_type, typ)
            self.assertNotEqual(c.effect, 'unsupported')

    def test_abrade_damage_mode_kills_three_toughness(self):
        c = self.creature(self.t.players[1], 3, 3)
        self.cast(self.give('Abrade'), mode='damage', target=c.id)
        self.assertNotIn(c.id, self.t.rules.objects)
        self.assertIn('Abrade', self.p.graveyard)

    def test_abrade_damage_accumulates_with_existing_damage(self):
        c = self.creature(self.t.players[1], 4, 5)
        self.t.rules.mark_damage(c.id, 2)
        self.cast(self.give('Abrade'), mode='damage', target=c.id)
        self.assertNotIn(c.id, self.t.rules.objects)

    def test_abrade_respects_indestructible(self):
        c = self.creature(self.t.players[1], 3, 3, ('indestructible',))
        self.cast(self.give('Abrade'), mode='damage', target=c.id)
        self.assertIn(c.id, self.t.rules.objects)
        self.assertEqual(self.t.rules.get(c.id).damage_marked, 3)

    def test_abrade_destroy_artifact_mode(self):
        rock = self.place('Sol Ring')
        self.cast(self.give('Abrade'), mode='artifact', target=rock)
        self.assertIn('Sol Ring', self.p.graveyard)

    def test_abrade_artifact_mode_not_creature_only_target(self):
        c = self.creature(self.t.players[1])
        card = self.give('Abrade'); action = self.t.action_with_options(self.p, card, mode='artifact', target=c.id)
        with self.assertRaises(ValueError): self.t.cast(action)
        self.assertIn(card, self.p.hand)

    def test_abrade_cannot_switch_mode_on_resolution(self):
        c = self.creature(self.t.players[1])
        original = self.give('Abrade')
        other = self.give('Capsize')
        used = []
        def policy(seat, frames, choices):
            if seat == 0 and frames and not used:
                choice = next((x for x in choices if x.kind == 'spell' and x.action.source == 'Capsize'), None)
                if choice: used.append(True)
                return choice
        self.t.priority_policy = policy
        self.cast(original, mode='damage', target=c.id)
        self.assertEqual(self.t.spell_stack.fizzled, 1)
        self.assertFalse(any(e[0] == 'abrade_destroy' for e in self.t.rule_events))

    def test_abrade_hexproof_target_rejected(self):
        c = self.creature(self.t.players[1], keywords=('hexproof',))
        with self.assertRaises(ValueError): self.cast(self.give('Abrade'), mode='damage', target=c.id)

    def test_abrade_invalid_mode_rejected(self):
        with self.assertRaises(ValueError): self.t.action_with_options(self.p, self.give('Abrade'), mode='both')

    def test_capsize_plain_goes_to_graveyard(self):
        oid = self.place('Sol Ring')
        self.cast(self.give('Capsize'), buyback=False, target=oid)
        self.assertIn('Sol Ring', [c.name for c in self.p.hand])
        self.assertIn('Capsize', self.p.graveyard)

    def test_capsize_buyback_returns_physical_card_to_hand(self):
        oid = self.place('Sol Ring'); before = sum(not o.token for o in self.t.rules.objects.values())
        self.cast(self.give('Capsize'), buyback=True, target=oid)
        self.assertIn('Capsize', [c.name for c in self.p.hand])
        self.assertNotIn('Capsize', self.p.graveyard)
        self.assertEqual(sum(not o.token for o in self.t.rules.objects.values()), before)

    def test_capsize_additional_cost_and_colored_pips(self):
        card = self.give('Capsize')
        plain = self.t.action_with_options(self.p, card, buyback=False)
        bought = self.t.action_with_options(self.p, card, buyback=True)
        self.assertEqual((plain.cost, bought.cost), (3, 6))
        self.assertEqual(bought.parameters['U'], 2)

    def test_capsize_reduction_applies_after_buyback_added(self):
        self.cast(self.t.zones.views(0, 'command')[0])
        for _ in range(5): self.creature(self.p, 1, 1)
        a = self.t.action_with_options(self.p, self.give('Capsize'), buyback=True)
        self.assertEqual(a.cost, 2)
        self.assertEqual(a.parameters['U'], 2)

    def test_countered_buyback_does_not_return_to_hand(self):
        target = self.creature(self.t.players[1]); q = self.t.players[2]
        self.give(p=q, effect='counter')
        self.t.priority_policy = lambda seat, frames, choices: next((c for c in choices if seat == 2 and c.kind == 'spell' and c.action.effect == 'counter'), None)
        self.cast(self.give('Capsize'), buyback=True, target=target.id)
        self.assertIn('Capsize', self.p.graveyard)
        self.assertFalse(any(c.name == 'Capsize' for c in self.p.hand))

    def test_fizzled_buyback_does_not_return_to_hand(self):
        target = self.creature(self.t.players[1]); q = self.t.players[2]
        self.give(p=q, effect='remove')
        self.t.priority_policy = lambda seat, frames, choices: next((c for c in choices if seat == 2 and c.kind == 'spell' and c.action.effect == 'remove' and c.action.target_object == target.id), None)
        self.cast(self.give('Capsize'), buyback=True, target=target.id)
        self.assertIn('Capsize', self.p.graveyard)
        self.assertEqual(self.t.spell_stack.fizzled, 1)

    def test_capsize_bounces_land_and_removes_mana_source(self):
        oid = self.land()
        self.cast(self.give('Capsize'), target=oid)
        self.assertNotIn(oid, self.t.rules.objects)
        self.assertEqual(self.p.lands, 0)
        self.assertTrue(self.t.assert_consistent())

    def test_capsize_token_ceases_without_hand_card(self):
        c = self.creature(self.t.players[1])
        self.cast(self.give('Capsize'), target=c.id)
        self.assertNotIn(c.id, self.t.rules.objects)
        self.assertFalse(any(x.name == 'declared fixture' for x in self.t.players[1].hand))

    def test_adaptation_adds_wizard_without_erasing_existing_types(self):
        icon = self.place('Third Path Iconoclast'); self.place('Arcane Adaptation')
        self.assertEqual(self.t.rules.subtypes(icon), frozenset({'Human','Monk','Wizard'}))
        self.assertEqual(self.t.rules.get(icon).card.subtypes, frozenset({'Human','Monk'}))

    def test_adaptation_affects_hand_library_graveyard_command(self):
        self.place('Arcane Adaptation')
        card = self.give('Third Path Iconoclast')
        self.assertIn('Wizard', self.t.rules.subtypes(card.object_id))
        oid = self.t.zones.move(card.object_id, 'graveyard')
        self.assertIn('Wizard', self.t.rules.subtypes(oid))
        other = next(c for c in self.p.library if c.card_type == 'creature')
        self.assertIn('Wizard', self.t.rules.subtypes(other.object_id))
        self.assertIn('Wizard', self.t.rules.subtypes(self.t.zones.ids(0, 'command')[0]))

    def test_adaptation_affects_creature_spell_on_stack(self):
        self.place('Arcane Adaptation'); observed = []
        def policy(seat, frames, choices):
            for f in frames:
                if f.kind == 'spell' and f.label == 'Third Path Iconoclast':
                    observed.append('Wizard' in self.t.rules.subtypes(f.source_id))
        self.t.priority_policy = policy
        self.cast(self.give('Third Path Iconoclast'))
        self.assertTrue(observed); self.assertTrue(all(observed))

    def test_adaptation_does_not_change_opponent_creatures_or_artifacts(self):
        creature = self.creature(self.t.players[1]); rock = self.place('Sol Ring')
        self.place('Arcane Adaptation')
        self.assertNotIn('Wizard', self.t.rules.subtypes(creature.id))
        self.assertNotIn('Wizard', self.t.rules.subtypes(rock))

    def test_adaptation_removal_stops_continuous_type_effect(self):
        icon = self.place('Third Path Iconoclast'); adaptation = self.place('Arcane Adaptation')
        self.t.world.move(adaptation, 'hand', 'bounce')
        self.assertNotIn('Wizard', self.t.rules.subtypes(icon))

    def test_harmonic_doubles_adapted_iconoclast_trigger(self):
        self.place('Third Path Iconoclast'); self.place('Harmonic Prodigy'); self.place('Arcane Adaptation')
        before = self.p.token_count()
        self.cast(self.give('Preordain'))
        self.assertEqual(self.p.token_count() - before, 2)

    def test_captured_doubled_triggers_survive_adaptation_bounce(self):
        self.place('Third Path Iconoclast'); self.place('Harmonic Prodigy'); adaptation = self.place('Arcane Adaptation')
        self.give('Capsize'); before = self.p.token_count(); used=[]
        def policy(seat, frames, choices):
            if seat == 0 and frames and not used:
                chosen=next((c for c in choices if c.kind=='spell' and c.action.source=='Capsize'),None)
                if chosen:
                    # A legal announced alternative target, fixed before casting.
                    chosen.action.target=0; chosen.action.target_object=adaptation; used.append(True)
                return chosen
        self.t.priority_policy=policy
        self.cast(self.give('Preordain'))
        # Two doubled Iconoclast triggers from each of two casts, captured
        # before Capsize removes the Adaptation.
        self.assertEqual(self.p.token_count()-before,4)
        self.assertFalse(any(o.card.name=='Arcane Adaptation' for o in self.t.rules.on_battlefield()))

    def test_frantic_discards_and_untaps_three_sources(self):
        ids=[self.land() for _ in range(3)]
        for oid in ids:self.t.rules.get(oid).tapped=True
        self.cast(self.give('Frantic Search'))
        self.assertTrue(all(not self.t.rules.get(x).tapped for x in ids))
        self.assertGreaterEqual(len(self.p.graveyard),3)

    def test_frantic_does_not_untap_rocks(self):
        oid=self.place('Sol Ring');self.t.rules.get(oid).tapped=True
        self.cast(self.give('Frantic Search'))
        self.assertTrue(self.t.rules.get(oid).tapped)

    def test_frantic_can_choose_opponent_land_without_targeting(self):
        opponent=self.t.players[1]
        card=self.give(p=opponent,effect='none')
        oid=self.t.zones.move(card.object_id,'battlefield');self.t.world.views[oid]=WorldEntry(opponent,None,'resource')
        self.t.rules.get(oid).tapped=True
        self.t.frantic_untap_policy=lambda seat, lands:(oid,)
        self.cast(self.give('Frantic Search'))
        self.assertFalse(self.t.rules.get(oid).tapped)

    def test_frantic_no_priority_inside_draw_discard_untap(self):
        ids=[self.land() for _ in range(3)]
        snapshots=[]
        self.t.priority_policy=lambda seat,frames,choices:snapshots.append(self.t.spell_stack.resolving) or None
        self.cast(self.give('Frantic Search'))
        self.assertTrue(snapshots);self.assertFalse(any(snapshots))

    def test_land_play_only_own_main_empty_stack(self):
        land=self.give('Island');self.t.phase='beginning'
        with self.assertRaises(ValueError):self.t.play_land(self.p,land,1)
        self.t.phase='main';self.t.active_seat=1
        with self.assertRaises(ValueError):self.t.play_land(self.p,land,1)

    def test_land_once_across_both_main_phases(self):
        first=self.give('Island');other=self.give('Mountain')
        self.t.safe_runner.new_turn(1)
        self.t.play_land(self.p,first,1)
        self.t.step='postcombat_main'
        with self.assertRaises(ValueError):self.t.play_land(self.p,other,1)

    def test_new_creature_cannot_attack_without_haste(self):
        c=self.creature(self.p)
        with self.assertRaises(ValueError):self.t.combat_engine.declare_attackers(self.p,[(c.id,1)])

    def test_haste_creature_can_attack_same_turn(self):
        c=self.creature(self.p,keywords=('haste',))
        self.t.combat_engine.declare_attackers(self.p,[(c.id,1)])
        self.assertTrue(self.t.rules.get(c.id).tapped)

    def test_vigilance_attacker_does_not_tap(self):
        c=self.creature(self.p,keywords=('haste','vigilance'))
        self.t.combat_engine.declare_attackers(self.p,[(c.id,1)])
        self.assertFalse(self.t.rules.get(c.id).tapped)

    def test_flying_block_legality_and_reach(self):
        attacker=self.creature(self.p,keywords=('haste','flying'))
        ground=self.creature(self.t.players[1]);reach=self.creature(self.t.players[1],keywords=('reach',))
        self.t.combat_engine.declare_attackers(self.p,[(attacker.id,1)])
        with self.assertRaises(ValueError):self.t.combat_engine.declare_blockers([(attacker.id,ground.id)])
        self.t.combat_engine.declare_blockers([(attacker.id,reach.id)])

    def test_blocker_can_block_summoning_sick_but_not_tapped(self):
        a=self.creature(self.p,keywords=('haste',));b=self.creature(self.t.players[1])
        self.t.combat_engine.declare_attackers(self.p,[(a.id,1)])
        self.t.rules.get(b.id).tapped=True
        with self.assertRaises(ValueError):self.t.combat_engine.declare_blockers([(a.id,b.id)])
        self.t.rules.get(b.id).tapped=False;self.t.combat_engine.declare_blockers([(a.id,b.id)])

    def test_removed_blocker_does_not_make_attacker_unblocked(self):
        a=self.creature(self.p,keywords=('haste',));b=self.creature(self.t.players[1])
        self.t.combat_engine.declare_attackers(self.p,[(a.id,1)])
        self.t.combat_engine.declare_blockers([(a.id,b.id)])
        self.t.world.move(b.id,'hand','bounce')
        record=self.t.combat_engine.damage(self.p)
        self.assertEqual(record['player_damage'],{})
        self.assertEqual(self.t.players[1].life,40)

    def test_removed_attacker_deals_no_damage(self):
        a=self.creature(self.p,keywords=('haste',))
        self.t.combat_engine.declare_attackers(self.p,[(a.id,1)])
        self.t.world.move(a.id,'hand','bounce')
        self.assertFalse(self.t.combat_engine.damage(self.p)['player_damage'])

    def test_two_pairs_receive_damage_before_any_sba(self):
        attackers=[self.creature(self.p,keywords=('haste',)) for _ in range(2)]
        blockers=[self.creature(self.t.players[1]) for _ in range(2)]
        self.t.combat_engine.declare_attackers(self.p,[(a.id,1) for a in attackers])
        self.t.combat_engine.declare_blockers([(a.id,b.id) for a,b in zip(attackers,blockers)])
        self.t.combat_engine.damage(self.p)
        self.assertTrue(all(self.t.rules.get(c.id).damage_marked==3 for c in attackers+blockers))
        self.t.spell_stack.checkpoint()
        self.assertTrue(all(c.id not in self.t.rules.objects for c in attackers+blockers))

    def test_multiple_players_take_lethal_combat_simultaneously(self):
        a=self.creature(self.p,keywords=('haste',));b=self.creature(self.p,keywords=('haste',))
        self.t.players[1].life=self.t.players[2].life=3
        self.t.combat_engine.declare_attackers(self.p,[(a.id,1),(b.id,2)])
        self.t.combat_engine.declare_blockers([]);self.t.combat_engine.damage(self.p)
        self.assertEqual([self.t.players[x].life for x in (1,2)],[0,0])
        self.t.spell_stack.checkpoint()
        self.assertTrue(all(self.t.players[x].eliminated_round is not None for x in (1,2)))

    def test_one_blocker_cannot_block_two_attackers(self):
        a=self.creature(self.p,keywords=('haste',));b=self.creature(self.p,keywords=('haste',));c=self.creature(self.t.players[1])
        self.t.combat_engine.declare_attackers(self.p,[(a.id,1),(b.id,1)])
        with self.assertRaises(ValueError):self.t.combat_engine.declare_blockers([(a.id,c.id),(b.id,c.id)])

    def test_damage_cleared_at_cleanup(self):
        c=self.creature(self.p,1,5);self.t.rules.mark_damage(c.id,2)
        self.t.cleanup_step(self.p)
        self.assertEqual(self.t.rules.get(c.id).damage_marked,0)

    def test_draw_step_and_no_upkeep_land_play(self):
        first_turn=[]
        def policy(seat,frames,choices):
            if self.t.turn_serial==1:first_turn.append((self.t.step,self.t.players[self.t.active_seat].lands,len(self.t.players[self.t.active_seat].hand)))
        self.t.priority_policy=policy
        self.t.run(1)
        upkeep=[x for x in first_turn if x[0]=='upkeep'];draw=[x for x in first_turn if x[0]=='draw']
        self.assertTrue(upkeep and draw);self.assertEqual(upkeep[0][1],0)
        self.assertEqual(draw[0][2],upkeep[0][2]+1)

    def test_both_main_phases_and_no_priority_at_untap_cleanup(self):
        steps=[]
        self.t.priority_policy=lambda *args:steps.append(self.t.step) or None
        self.t.run(1)
        self.assertIn('precombat_main',steps);self.assertIn('postcombat_main',steps)
        self.assertNotIn('untap',steps);self.assertNotIn('cleanup',steps)

    def test_no_attackers_skips_blockers_and_damage_steps(self):
        self.t.run(1)
        steps=[x[2] for x in self.t.step_history]
        self.assertNotIn('declare_blockers',steps);self.assertNotIn('combat_damage',steps)
        self.assertIn('end_combat',steps)

    def test_mana_pool_empties_between_steps(self):
        self.t.rules.mana_pools[0]=(1,2,3)
        StepDriver(self.t).window('draw','beginning',False)
        self.assertEqual(self.t.resources.pool(0),(0,0,0))

    def test_hand_discard_is_at_cleanup_not_main(self):
        self.p.draw(10)
        self.t.step='postcombat_main';self.t.phase='main'
        self.t.spell_stack.resolve()
        self.assertEqual(len(self.p.hand),10)
        self.t.cleanup_step(self.p)
        self.assertEqual(len(self.p.hand),7)

    def test_synthetic_combo_losing_setup_resolves_without_crash_or_win(self):
        p=self.t.players[3]
        self.t.finish(p,{'mode':'combo_win','required_pieces':3},base.Action(3,'fixture','sorcery','finisher',1))
        self.assertIsNone(self.t.winner);self.assertEqual(self.t.counts['abstract_combo_setup_lost'],1)

    def test_seeded_games_reproduce_steps_and_combat(self):
        a=StepTable(seed=104,trace=True).run(6);b=StepTable(seed=104,trace=True).run(6)
        self.assertEqual(a.step_history,b.step_history);self.assertEqual(a.combat_batches,b.combat_batches)
        self.assertEqual(a.events,b.events)

    def test_all_seats_keep_physical_counts(self):
        for seat in range(4):
            kinds=['aggro','control','combo'];kinds.insert(seat,'magnus')
            t=StepTable(kinds,seed=104).run(8)
            self.assertTrue(t.assert_consistent())
            for p in t.players:
                n=sum(not o.token and o.owner==p.seat for o in t.rules.objects.values())
                self.assertEqual(n,0 if p.eliminated_round is not None else 100 if p is t.details else 99)

    def test_coverage_breakdown_removes_only_implemented_cards_from_unsupported(self):
        d=self.t.diagnostics()
        for name in ('Abrade','Capsize','Arcane Adaptation'):self.assertNotIn(name,d['unsupported_definitions'])
        self.assertIn('Underworld Breach',d['unsupported_definitions'])
        self.assertNotIn('Frantic Search',d['approx_definitions'])


if __name__=='__main__':unittest.main(verbosity=2)
