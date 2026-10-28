"""Live priority integration with v9c resources, v9b zones and v8 rules.

The driver remains coarse. Only registered effects/activations are legal;
new priority windows do not imply complete named-card or combat coverage.
"""
from pathlib import Path
import sys
from dataclasses import replace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v9c_mana'))
from game import ManaTable, SourceBattlefield
from resources import Cost, Activation, spend
from priority import PriorityStack, Choice
from abilities import NAMED_ACTIVATIONS
from table import CentralTable
from rules import Event
from responses import descriptor
import simulation as base


class PriorityBattlefield(SourceBattlefield):
    def damage_pair(self, first, second):
        result = super().damage_pair(first, second)
        t = self.table
        if t.phase == 'combat' and not t.spell_stack.running:
            t.spell_stack.resolve()
        return result


class PriorityTable(ManaTable):
    battlefield_class = PriorityBattlefield

    def __init__(self, *args, **kwargs):
        self.active_seat = 0; self.phase = 'main'; self.main_actions = 0
        self.activation_catalog = dict(NAMED_ACTIVATIONS)
        super().__init__(*args, **kwargs)
        self.spell_stack = PriorityStack(self)

    def _apply_pending(self, pending):
        for item in pending: self.spell_stack.trigger(item)

    def resolve_trigger(self, item):
        return CentralTable._apply_pending(self, [item])

    def emit(self, name, action=None, **payload):
        if name == 'spell_cast' and action is not None and isinstance(self.spell_stack, PriorityStack):
            ticket = self._spells.get(id(action))
            if ticket: self.spell_stack.spell(action, ticket.object_id)
        result = super().emit(name, action, **payload)
        if name == 'spell_cast' and isinstance(self.spell_stack, PriorityStack) and not self.spell_stack.resolving:
            self.spell_stack.checkpoint()
        return result

    def counter_allowed(self, action, target):
        if target.kind != 'spell': return False
        card = next((c for zone in ('hand', 'stack') for c in self.zones.views(action.actor, zone)
                     if c.name == action.source), None)
        if card is None: return False
        allowed = descriptor(card).legal_spell_types
        typ = target.action.card_type
        return typ in allowed or 'noncreature' in allowed and typ != 'creature'

    def targets_legal(self, action):
        if action.effect == 'counter':
            target = self.spell_stack.get(action.target_object)
            return bool(target and self.counter_allowed(action, target))
        if action.effect not in ('remove', 'named_pongify', 'burn'): return True
        if action.effect == 'burn':
            return action.target in range(4) and self.players[action.target].alive
        oid = action.target_object
        if oid is None or oid not in self.rules.objects: return False
        types = {'creature'} if action.effect == 'named_pongify' else {'creature', 'artifact', 'enchantment', 'planeswalker'}
        if not self.rules.legal_target(action.actor, oid, types): return False
        return self.rules.get(oid).controller == action.target

    def cast(self, action):
        s = self.spell_stack
        if s.resolving: raise ValueError('No priority during resolution')
        if s.running:
            if s.holder != action.actor: raise ValueError('Caster does not hold priority')
        elif action.actor != self.active_seat or self.phase != 'main' or s.frames or s.pending:
            raise ValueError('Start casting from the appropriate priority window')
        sorcery_window = action.actor == self.active_seat and self.phase == 'main' and not s.frames
        if action.card_type != 'instant' and not sorcery_window:
            raise ValueError('Sorcery timing required')
        if not self.targets_legal(action): raise ValueError('Illegal spell target')
        normal = action.actor == self.active_seat and not s.frames
        before = self.players[action.actor].cards_cast
        if normal: self.main_actions += 1
        try:
            return super().cast(action)
        finally:
            if normal and self.players[action.actor].cards_cast == before: self.main_actions -= 1

    def fizzle_spell(self, action):
        ticket = self._spells.pop(id(action), None)
        if ticket and ticket.object_id in self.rules.objects:
            self.zones.move(ticket.object_id, 'graveyard', commander_choice=True)
            self.zones._pending.pop(ticket.object_id, None)
        self.counts['spells_fizzled'] += 1
        self.rules.events.append(Event('spell_fizzled', action.actor, ticket.object_id if ticket else None))
        base.Table.emit(self, 'spell_fizzled', action)
        self.note(f'    FIZZLE: {action.source} has no legal target.')

    def register_activation(self, card_id, specification):
        current = self.activation_catalog.get(card_id, ())
        if any(a.key == specification.key for a in current): raise ValueError('Duplicate activation key')
        self.activation_catalog[card_id] = current + (specification,)

    def activation_available(self, seat, oid, specification, target_frame=None):
        if oid not in self.rules.objects: return False
        obj = self.rules.get(oid)
        if obj.zone != 'battlefield' or obj.controller != seat: return False
        if specification not in self.activation_catalog.get(obj.card.card_id, ()): return False
        if specification.tap and (obj.tapped or 'creature' in obj.types): return False
        if specification.target_kinds:
            target = self.spell_stack.get(target_frame)
            if target is None or target.kind not in specification.target_kinds: return False
        excluded = (oid,) if specification.tap or specification.sacrifice else ()
        return self.resources.plan(seat, specification.cost, excluded) is not None

    def activate_ability(self, seat, oid, specification, target_frame=None):
        s = self.spell_stack
        if s.resolving: raise ValueError('No priority during resolution')
        if s.running and s.holder != seat: raise ValueError('Activator does not hold priority')
        if not s.running and (seat != self.active_seat or self.phase != 'main' or s.frames or s.pending):
            raise ValueError('Activation requires priority')
        if not self.activation_available(seat, oid, specification, target_frame):
            raise ValueError('Illegal or unpayable activation')
        source_name = self.rules.get(oid).card.name
        excluded = (oid,) if specification.tap or specification.sacrifice else ()
        self.resources.pay(seat, specification.cost, excluded=excluded)
        if specification.tap:
            self.rules.get(oid).tapped = True; self.rules._dirty()
        if specification.sacrifice:
            self.world.move(oid, 'graveyard', 'sacrifice')
        s.activated(seat, oid, specification, target_frame, source_name + ': ' + specification.key)
        self.rules.events.append(Event('ability_activated', seat, oid))
        self.emit('ability_activated', controller=seat, source_id=oid, ability=specification.key)
        if not s.running: s.resolve()
        return True

    def resolve_activation(self, frame):
        ability = frame.ability
        if ability.operation == 'draw':
            player = self.players[frame.controller]
            player.draw(ability.amount)
            if not player.alive: self.eliminate(player, 'empty_library')
        elif ability.operation == 'counter_stack':
            if not self.spell_stack.counter(frame.target_frame, ability.target_kinds): return False
        else: raise NotImplementedError('Unknown activated operation ' + ability.operation)
        self.rules.events.append(Event('ability_resolved', frame.controller, frame.source_id))
        self.emit('ability_resolved', controller=frame.controller, source_id=frame.source_id, ability=ability.key)
        return True

    def priority_choices(self, seat):
        s = self.spell_stack; player = self.players[seat]; choices = []
        for card in player.hand + self.zones.views(seat, 'command'):
            if card.effect in ('none', 'unsupported'): continue
            normal = seat == self.active_seat and self.phase == 'main' and not s.frames
            if card.card_type != 'instant' and not normal: continue
            action = self.action_for_card(player, card)
            if card.effect == 'counter':
                for frame in s.frames:
                    a = replace(action, target=frame.controller, target_object=frame.frame_id)
                    if self.counter_allowed(a, frame) and self.can_pay(player, a): choices.append(Choice('spell', action=a))
            elif self.targets_legal(action) and self.can_pay(player, action):
                choices.append(Choice('spell', action=action))
        for obj in tuple(self.rules.on_battlefield()):
            if obj.controller != seat: continue
            for specification in self.activation_catalog.get(obj.card.card_id, ()):
                targets = [f.frame_id for f in s.frames if f.kind in specification.target_kinds] if specification.target_kinds else [None]
                for target in targets:
                    if self.activation_available(seat, obj.object_id, specification, target):
                        choices.append(Choice('activate', source_id=obj.object_id, ability=specification, target_frame=target))
        # Mana abilities are immediate actions retaining priority, not stack frames.
        for oid, abilities in self.resources.sources(seat):
            for ability in abilities:
                if ability.life and player.life < ability.life: continue
                for pool in spend(self.resources.pool(seat), ability.cost):
                    choices.append(Choice('mana', activation=Activation(oid, ability, pool)))
        return tuple(choices)

    def choose_priority(self, seat, choices):
        s = self.spell_stack; player = self.players[seat]
        if not s.frames and seat == self.active_seat and self.phase == 'main' and self.main_actions < 12:
            action = player.pilot.select_action(self, player)
            selected = next((c for c in choices if c.kind == 'spell' and action is not None and c.action.source == action.source), None)
            if selected: return selected
        for choice in choices:
            if choice.kind == 'spell' and choice.action.effect == 'counter':
                target = s.get(choice.action.target_object)
                if target.controller == seat: continue
                defend = target.action.target == seat or target.action.effect in ('wipe', 'finisher')
                chance = .12 + .34 * defend + .2 * (target.action.effect == 'counter')
                chance += base.CONF['counter_response_bonus'].get(player.archetype, 0)
                if self.rng.random() < min(.85, chance): return choice
            elif choice.kind == 'spell' and s.frames and choice.action.card_type == 'instant':
                if choice.action.effect in ('remove', 'named_pongify', 'burn') and self.rng.random() < .08:
                    return choice
            elif choice.kind == 'activate' and not s.frames and len(player.hand) <= 2:
                return choice
        return None

    def commit_choice(self, seat, choice):
        if choice.kind == 'spell':
            if not self.cast(choice.action): raise ValueError('Selected spell is no longer payable')
        elif choice.kind == 'activate':
            self.activate_ability(seat, choice.source_id, choice.ability, choice.target_frame)
        elif choice.kind == 'mana':
            self.resources.activate(seat, choice.activation)
        else: raise ValueError('Unknown priority action')

    def upkeep(self, player, turn):
        self.active_seat = player.seat; self.phase = 'beginning'; self.main_actions = 0
        result = super().upkeep(player, turn)
        self.spell_stack.holder = player.seat
        self.spell_stack.checkpoint()
        self.phase = 'main'
        return result

    def main(self, player):
        self.active_seat = player.seat; self.phase = 'main'; self.spell_stack.holder = player.seat
        try: self.spell_stack.resolve()
        finally:
            self.resources.empty_pools(); self.phase = 'combat'

    def combat(self, player):
        self.phase = 'combat'
        try: return super().combat(player)
        finally: self.phase = 'end'

    def damage(self, player, amount, source=None, cause='damage'):
        result = super().damage(player, amount, source, cause)
        if self.phase == 'combat' and not self.spell_stack.running:
            self.spell_stack.holder = self.active_seat
            self.spell_stack.resolve()
        return result

    def _cleanup_expiring(self):
        self.phase = 'end'
        if self.spell_stack.frames or self.spell_stack.pending:
            self.spell_stack.holder = self.active_seat; self.spell_stack.resolve()
        super()._cleanup_expiring()
        for player in self.players:
            if not player.alive or player.seat != self.active_seat: continue
            if len(player.hand) > 7:
                # Historical discard preference, now applied at end/cleanup.
                if player is self.details: discard = player.hand[7:]
                else:
                    priority = base.CONF['priority'].get(player.archetype, [])
                    ordered = sorted(player.hand, key=lambda c: (c.kind == 'land' and player.lands < 5,
                                     -(priority.index(c.kind) if c.kind in priority else 99)), reverse=True)
                    discard = ordered[7:]
                for card in discard: self.zones.discard(player.seat, card.object_id)
        self.resources.empty_pools()

    def assert_consistent(self):
        super().assert_consistent()
        s = getattr(self, 'spell_stack', None)
        if isinstance(s, PriorityStack) and not self.safety_stop:
            framed = {f.source_id for f in s.frames if f.kind == 'spell'}
            # During a resolution its physical ticket remains until completion.
            if not s.resolving and framed != set(self.zones._pending):
                raise AssertionError('Physical spells and priority frames diverged')
        return True

    def diagnostics(self):
        d = super().diagnostics(); s = self.spell_stack
        d['known_rules_gaps'] = [x for x in d['known_rules_gaps'] if 'counter-only' not in x and 'precombat hand-size' not in x]
        d['known_rules_gaps'] += ['coarse phase/serial combat driver; not every official step is exposed',
                                 'only registered trigger/activation operations; creature tap abilities unsupported']
        d['v9']['migration_status'] = 'shared physical zones, source-ID mana and typed priority stack'
        d['v9b']['limits'][1] = 'typed priority supplied by v10; incomplete card/step coverage remains'
        d['v9c']['limits'][0] = 'typed priority supplied by v10; incomplete card/step coverage remains'
        d['v8']['limits'] = ['shared physical state and typed priority stack; partial card/step coverage']
        d['v10'] = dict(typed_priority_live=True, passes=s.passes, triggers_queued=s.triggers_queued,
                        triggers_resolved=s.triggers_resolved, activations_resolved=s.abilities_resolved,
                        fizzled=s.fizzled, max_depth=s.max_depth_seen, remaining_frames=len(s.frames),
                        pending_triggers=len(s.pending), limits=['one detailed deck', 'coarse step/combat timing',
                        'Mind Stone draw plus explicitly registered nonmana activations; not all named abilities'])
        return d
