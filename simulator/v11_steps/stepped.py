"""V11 ordinary turn steps, combat batch and a small named-card expansion."""
from dataclasses import replace
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v10_priority'))
from gameplay import PriorityTable
from priority import PriorityStack, Choice
from rules import Event
from combat import Combat
from driver import StepDriver
import simulation as base
import integrated as v6
import cards


class StepStack(PriorityStack):
    trigger_operations = PriorityStack.trigger_operations | {'damage_player'}


class StepTable(PriorityTable):
    def __init__(self, *args, **kwargs):
        self.step = 'precombat_main'; self.turn_serial = 0
        self.attack_ready = {}; self.step_history = []; self.combat_batches = []
        self.rule_events = []
        super().__init__(*args, **kwargs)
        cards.install(self)
        self.spell_stack = StepStack(self)
        self.combat_engine = Combat(self)
        self.register_effect('named_abrade', self.resolve_abrade)
        self.register_effect('named_capsize', self.resolve_capsize)
        self.register_effect('named_adaptation', self.resolve_adaptation)

    def action_for(self, player, card):
        if card.name in cards.NEW: return cards.action(self, player, card)
        return super().action_for(player, card)

    def expected_action(self, player, card, announced=None):
        if card.name in cards.NEW:
            return cards.action(self, player, card, announced.tags if announced else None)
        if announced and announced.tags: raise ValueError('Unknown casting option for this card')
        return super().expected_action(player, card, announced)

    def action_with_options(self, player, card, *, mode=None, buyback=False, target=None):
        tags = (mode,) if card.name == 'Abrade' else ('buyback',) if buyback else ()
        action = cards.action(self, player, card, tags)
        if target is not None:
            action.target_object = target
            action.target = self.rules.get(target).controller
        return action

    def targets_legal(self, action):
        if action.effect not in ('named_abrade', 'named_capsize'): return super().targets_legal(action)
        oid = action.target_object
        if oid is None or oid not in self.rules.objects: return False
        if action.effect == 'named_abrade':
            mode = action.parameters.get('mode')
            if mode not in ('artifact', 'damage'): return False
            types = {'artifact'} if mode == 'artifact' else {'creature'}
        else: types = {'creature', 'artifact', 'enchantment', 'planeswalker', 'battle', 'land'}
        return (self.rules.legal_target(action.actor, oid, types)
                and self.rules.get(oid).controller == action.target)

    def resolve_abrade(self, table, action):
        oid = action.target_object; name = self.rules.get(oid).card.name
        if action.parameters['mode'] == 'artifact':
            moved = self.world.destroy(oid)
            self.rule_events.append(('abrade_destroy', name, bool(moved)))
            self.note(f'    Abrade artifact mode: {name}; destroyed={bool(moved)}.')
        else:
            prior = {x: self.rules.get(x).card.name for x in self.world.views if x in self.rules.objects}
            self.rules.mark_damage(oid, 3)
            self.world._after_movement(list(prior), prior)
            self.rule_events.append(('abrade_damage', name, 3))
            self.note(f'    Abrade damage mode: 3 damage to {name}.')

    def resolve_capsize(self, table, action):
        oid = action.target_object; name = self.rules.get(oid).card.name
        self.world.move(oid, 'hand', 'bounce')
        self.rule_events.append(('capsize_bounce', name, action.parameters.get('buyback', False)))
        self.note(f'    Capsize returns {name} to its owner\'s hand.')

    def resolve_adaptation(self, table, action):
        self.add_permanent(self.players[action.actor], 'type_effect', 0, action.source)
        self.rule_events.append(('adaptation', action.actor, 'Wizard'))
        self.note('    Arcane Adaptation enters: Wizard chosen; additive types apply in all declared zones.')

    def emit(self, name, action=None, **payload):
        if (name == 'spell_resolved' and action is not None and action.source == 'Capsize'
                and action.parameters.get('buyback')):
            ticket = self._spells.pop(id(action), None)
            if ticket and ticket.object_id in self.rules.objects:
                self.zones.move(ticket.object_id, 'hand')
                self.zones._pending.pop(ticket.object_id, None)
                self.rules.events.append(Event(name, action.actor, ticket.object_id, spell_types=ticket.spell_types))
                self.rule_events.append(('buyback_return', action.actor))
                self.note('    Buyback paid: Capsize returns to hand after successful resolution.')
        return super().emit(name, action, **payload)

    def resolve_selection(self, table, action):
        if action.source != 'Frantic Search': return super().resolve_selection(table, action)
        player = self.players[action.actor]
        player.draw(2)
        discard = sorted(player.hand, key=lambda c: (c.effect != 'unsupported', c.kind == 'land'))[:2]
        for card in discard: self.zones.discard(player.seat, card.object_id)
        lands = tuple(o.object_id for o in self.rules.on_battlefield() if 'land' in o.types)
        policy = getattr(self, 'frantic_untap_policy', None)
        if policy:
            chosen = tuple(policy(player.seat, lands))
        else:
            chosen = tuple(oid for oid in lands if self.rules.get(oid).controller == player.seat
                           and self.rules.get(oid).tapped)[:3]
        if len(chosen) > 3 or len(set(chosen)) != len(chosen) or any(oid not in lands for oid in chosen):
            raise ValueError('Frantic Search may untap up to three distinct lands')
        for oid in chosen: self.rules.get(oid).tapped = False
        self.rules._dirty()
        discarded_names=tuple(card.name for card in discard)
        self.rule_events.append(('frantic_search', len(discard), chosen, discarded_names))
        self.note(f'    Frantic Search: draw 2, discard {discarded_names}, untap lands {chosen}; no intermediate priority.')

    def pay_spell(self, player, card, action, response=False):
        name = card.name
        result = super().pay_spell(player, card, action, response)
        if player is self.details and name == 'Frantic Search':
            player.coverage['approx'] -= 1; player.coverage['supported'] += 1
        return result

    def finish(self, player, parameters, action):
        if parameters.get('mode') == 'combo_win' and player.combo() < parameters.get('required_pieces', 3):
            self.counts['abstract_combo_setup_lost'] += 1
            self.note('    Abstract combo finisher: setup no longer present; no players eliminated.')
            return
        return super().finish(player, parameters, action)

    def resolve_trigger(self, item):
        if item.op != 'damage_player': return super().resolve_trigger(item)
        args = dict(item.args); target = self.players[args['target']]
        if target.alive: self.damage(target, args['amount'], self.players[item.controller], 'persistent_finisher')

    def priority_choices(self, seat):
        choices = [choice for choice in super().priority_choices(seat)
                   if choice.kind != 'spell' or choice.action.source not in cards.NEW]
        player = self.players[seat]
        normal = seat == self.active_seat and self.phase == 'main' and not self.spell_stack.frames
        for card in player.hand:
            if card.name not in cards.NEW or card.card_type != 'instant' and not normal: continue
            variants = (('artifact',), ('damage',)) if card.name == 'Abrade' else ((), ('buyback',)) if card.name == 'Capsize' else ((),)
            alternatives = []
            for tags in variants:
                action = cards.action(self, player, card, tags)
                if not self.can_pay(player, action): continue
                if card.name == 'Arcane Adaptation': alternatives.append(Choice('spell', action=action)); continue
                for obj in self.rules.on_battlefield():
                    candidate = replace(action, target=obj.controller, target_object=obj.object_id)
                    if self.targets_legal(candidate): alternatives.append(Choice('spell', action=candidate))
            preferred = cards.action(self, player, card)
            alternatives.sort(key=lambda c: (c.action != preferred, c.action.target == seat))
            choices.extend(alternatives)
        if normal and getattr(player, '_land_turn', None) != self.safe_runner.turn:
            choices += [Choice('land', source_id=c.object_id) for c in player.hand if c.kind == 'land']
        return tuple(choices)

    def choose_priority(self, seat, choices):
        normal = seat == self.active_seat and self.phase == 'main' and not self.spell_stack.frames
        # Keep all legal own-target choices available to explicit policies, while
        # the default development pilot avoids destroying/bouncing its own board.
        useful = tuple(c for c in choices if not (c.kind == 'spell' and c.action.source in ('Abrade','Capsize')
                                                   and c.action.target == seat))
        if normal:
            land = next((c for c in useful if c.kind == 'land'), None)
            if land: return land
        choice = super().choose_priority(seat, useful)
        if choice: return choice
        if normal and self.main_actions < 12:
            return next((c for c in useful if c.kind == 'spell' and c.action.effect != 'counter'), None)
        if not normal and self.spell_stack.frames and self.rng.random() < .05:
            return next((c for c in useful if c.kind == 'spell' and c.action.source in ('Abrade','Capsize')), None)
        return None

    def commit_choice(self, seat, choice):
        if choice.kind == 'land':
            card = next(c for c in self.players[seat].hand if c.object_id == choice.source_id)
            self.play_land(self.players[seat], card, self.round_num)
        else: return super().commit_choice(seat, choice)

    def play_land(self, player, card, turn):
        if (player.seat != self.active_seat or self.phase != 'main' or self.spell_stack.frames
                or self.spell_stack.resolving or self.spell_stack.running and self.spell_stack.holder != player.seat):
            raise ValueError('Land play requires own main phase, priority and an empty stack')
        return super().play_land(player, card, turn)

    def damage(self, player, amount, source=None, cause='damage'):
        # The explicit driver owns combat checkpoints, not the serial v10 hook.
        return super(PriorityTable, self).damage(player, amount, source, cause)

    def cleanup_step(self, player):
        if player.alive and len(player.hand) > 7:
            if player is self.details: discards = player.hand[7:]
            else:
                priority = base.CONF['priority'].get(player.archetype, [])
                ordered = sorted(player.hand, key=lambda c: (c.kind == 'land' and player.lands < 5,
                                 -(priority.index(c.kind) if c.kind in priority else 99)), reverse=True)
                discards = ordered[7:]
            for card in discards: self.zones.discard(player.seat, card.object_id)
        # Existing 'expires' token marker is still an adapter, not a complete
        # delayed-trigger system. Other cleanup uses the authoritative kernel.
        for p in self.players:
            for creature in tuple(p.creatures):
                if creature.token and 'expires' in creature.keywords:
                    self.world.move(creature.id, 'exile', 'token_cease')
        self.world.cleanup()

    def run(self, max_rounds=8): return StepDriver(self).run(max_rounds)

    def diagnostics(self):
        d = super().diagnostics()
        definitions = {name.removeprefix('named:'): spec for name, spec in self.zones.specs.items() if name.startswith('named:')}
        d['unsupported_definitions'] = [name for name, spec in definitions.items() if spec.effect == 'unsupported']
        d['supported_definitions'] = sum(spec.effect != 'unsupported' for name, spec in definitions.items() if name != 'Magnus the Red')
        d['approx_definitions'] = sorted(v6.APPROX - {'Frantic Search'})
        d['known_rules_gaps'] = [x for x in d['known_rules_gaps'] if 'coarse' not in x and 'buyback' not in x
                                 and 'selection, scry' not in x]
        d['known_rules_gaps'] += ['single blockers; no first/double strike, trample or planeswalker attacks',
                                 'Wizard choice only for Arcane Adaptation; other selection/land utilities still partial',
                                 'Capsize buyback only; no general copy/loop or other buyback coverage',
                                 'temporary-token expiry remains cleanup adapter; no full delayed-trigger system']
        d['v10']['limits'][1] = 'ordinary step driver supplied by v11; limited combat keywords/assignments'
        d['v11'] = dict(explicit_steps=True, new_cards=list(cards.NEW), upgraded_cards=['Frantic Search'],
                        step_count=len(self.step_history), combat_batches=len(self.combat_batches),
                        rule_events=self.rule_events,
                        limits=['one detailed deck', 'one blocker per attacker', 'limited keywords and card text',
                                'Arcane Adaptation Wizard choice; Capsize buyback subset'])
        return d
