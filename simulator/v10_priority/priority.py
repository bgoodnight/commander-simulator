"""One bounded LIFO stack and four-seat priority loop for spells and abilities.

Rules mechanics are independent of card names. Handlers/providers live on the
owning table. Frame IDs are stack identities, never battlefield object IDs.
"""
from dataclasses import dataclass, replace
from itertools import count


@dataclass(frozen=True)
class Frame:
    frame_id: int
    kind: str
    controller: int
    source_id: int | None
    label: str
    action: object = None
    trigger: object = None
    ability: object = None
    target_frame: int | None = None


@dataclass(frozen=True)
class Choice:
    kind: str
    action: object = None
    source_id: int | None = None
    ability: object = None
    target_frame: int | None = None
    activation: object = None


class PriorityStack:
    trigger_operations = frozenset({'draw', 'create_token'})
    def __init__(self, table):
        self.table = table; self.frames = []; self.pending = []
        self._ids = count(1); self.running = False; self.resolving = False
        self.holder = None; self.history = []
        self.max_depth_seen = 0; self.spells_resolved = self.spells_countered = 0
        self.counters_resolved = self.responses_attempted = self.passes = 0
        self.triggers_queued = self.triggers_resolved = self.abilities_resolved = 0
        self.fizzled = 0; self.max_window_actions = 512; self.max_window_passes = 4096

    def order(self, start=None):
        seats = list(getattr(self.table, 'turn_order', (0, 1, 2, 3)))
        if len(seats) != 4 or set(seats) != set(range(4)): raise ValueError('Invalid four-seat turn order')
        start = self.table.active_seat if start is None else start
        i = seats.index(start)
        return seats[i:] + seats[:i]

    def alive(self, seat):
        p = self.table.players[seat]
        return p.life > 0 and p.eliminated_round is None

    def next_alive(self, seat):
        return next((s for s in self.order(seat)[1:] + [seat] if self.alive(s)), None)

    def get(self, frame_id):
        return next((f for f in self.frames if f.frame_id == frame_id), None)

    def push(self, frame):
        self.frames.append(frame)
        self.table.safe_runner.check(stack_depth=len(self.frames))
        self.max_depth_seen = max(self.max_depth_seen, len(self.frames))
        self.history.append(('push', frame.frame_id, frame.kind, frame.controller, frame.label))
        self.table.note(f'    STACK +{frame.frame_id} [{frame.kind}] P{frame.controller}: {frame.label}.')

    def spell(self, action, source_id):
        if any(f.action is action for f in self.frames): return
        self.push(Frame(next(self._ids), 'spell', action.actor, source_id, action.source,
                        action=action, target_frame=action.target_object if action.effect == 'counter' else None))
        self.holder = action.actor  # casting player keeps priority

    def trigger(self, item):
        if item.controller not in range(4) or not isinstance(item.quantity, int) or item.quantity < 1:
            raise ValueError('Invalid triggered ability controller or quantity')
        if item.op == 'create_token':
            from catalog import DEFINITIONS
            if dict(item.args).get('token_id') not in DEFINITIONS:
                raise NotImplementedError('Unknown trigger token definition')
        if item.op not in self.trigger_operations:
            raise NotImplementedError('Unsupported triggered stack operation ' + item.op)
        self.table.safe_runner.guard_trigger_count(item.quantity)
        for _ in range(item.quantity):
            label = self.table.rules.get(item.source_id).card.name if item.source_id in self.table.rules.objects else 'departed source'
            frame = Frame(next(self._ids), 'triggered', item.controller, item.source_id,
                          label + ': ' + item.op, trigger=replace(item, quantity=1))
            self.pending.append(frame); self.triggers_queued += 1

    def activated(self, seat, source_id, ability, target_frame=None, label='ability'):
        self.push(Frame(next(self._ids), 'activated', seat, source_id, label,
                        ability=ability, target_frame=target_frame))
        self.holder = seat

    def checkpoint(self):
        t = self.table
        # SBA repeat and pending placement happen before priority, never midway
        # through a resolving frame. Current named triggers have no meta-triggers.
        for _ in range(64):
            # Complete ALL SBA waves before placing any waiting triggers.
            for _ in range(64):
                before = tuple(t.rules.objects)
                for p in t.players:
                    if p.life <= 0 and p.eliminated_round is None: t.eliminate(p, 'state_based')
                prior = {oid: t.rules.get(oid).card.name for oid in t.world.views if oid in t.rules.objects}
                t.rules.check_state_based()
                t.world._after_movement(list(prior), prior)
                if tuple(t.rules.objects) == before: break
            else:
                t.safe_runner._stop('state_based_checkpoint_budget')
            self.frames[:] = [f for f in self.frames if self.alive(f.controller)
                              and (f.kind != 'spell' or t.stack_action_active(f.action))]
            batch = tuple(self.pending); placements = []
            for seat in self.order():
                owned = tuple(f for f in batch if f.controller == seat and self.alive(seat))
                policy = getattr(t, 'trigger_order_policy', None)
                ordered = tuple(policy(seat, owned)) if policy and owned else owned
                if (len(ordered) != len(owned) or {f.frame_id for f in ordered} != {f.frame_id for f in owned}
                        or any(not any(f is original for original in owned) for f in ordered)):
                    raise ValueError('Trigger ordering must be a permutation of controlled triggers')
                placements.extend(ordered)
            # Validate every controller's order before consuming any pending
            # triggers, so a rejected policy cannot silently delete abilities.
            for frame in batch:
                if not self.alive(frame.controller): self.pending.remove(frame)
            for frame in placements:
                self.pending.remove(frame)
                self.push(frame)
            if not self.pending: break
        else:
            t.safe_runner._stop('state_based_checkpoint_budget')
        if self.holder is None or not self.alive(self.holder):
            self.holder = next((s for s in self.order() if self.alive(s)), None)

    def counter(self, target_id, allowed_kinds, controller=None):
        frame = self.get(target_id)
        if frame is None or frame.kind not in allowed_kinds: return None
        self.frames.remove(frame)
        if frame.kind == 'spell':
            self.spells_countered += 1; self.table.counts['spells_countered'] += 1
            self.table.emit('spell_countered', frame.action)
            if controller is not None:
                self.table.emit('spell_countered_by', controller=controller, countered_frame=target_id)
        self.history.append(('counter', target_id, frame.kind))
        self.table.note(f'    STACK -{target_id}: {frame.label} countered.')
        return frame

    def resolve_top(self):
        t = self.table
        frame = self.frames.pop()
        self.resolving = True; resolved = True
        try:
            if frame.kind == 'spell':
                if frame.action.effect == 'counter':
                    target = self.get(frame.target_frame)
                    if not target or target.kind != 'spell' or not t.counter_allowed(frame.action, target):
                        self.fizzled += 1; resolved = False; t.fizzle_spell(frame.action)
                    else:
                        removed = self.counter(target.frame_id, {'spell'}, frame.controller)
                        self.counters_resolved += 1; t.counts['counters_cast'] += 1
                        t.players[frame.controller].counters_used += 1
                        if removed.action.effect == 'counter': t.counts['counter_counters'] += 1
                        t.resolve_counter_rider(frame.action, removed.action)
                        self.spells_resolved += 1; t.emit('spell_resolved', frame.action)
                elif not t.targets_legal(frame.action):
                    self.fizzled += 1; resolved = False; t.fizzle_spell(frame.action)
                else:
                    t.apply(frame.action)
                    self.spells_resolved += 1; t.emit('spell_resolved', frame.action)
            elif frame.kind == 'triggered':
                t.resolve_trigger(frame.trigger); self.triggers_resolved += 1
            elif frame.kind == 'activated':
                if t.resolve_activation(frame): self.abilities_resolved += 1
                else: self.fizzled += 1; resolved = False
            else:
                raise NotImplementedError('Unknown stack kind ' + frame.kind)
            self.history.append(('resolve' if resolved else 'fizzle', frame.frame_id, frame.kind, frame.controller))
        finally:
            self.resolving = False
        self.holder = t.active_seat  # active player, not last caster, after resolution
        self.checkpoint()

    def resolve(self, action=None):
        if getattr(self.table, 'response_policy', None) is not None:
            raise NotImplementedError('V10 uses priority_policy, not the old counter-only response_policy')
        if self.running: return True  # a committed response must not recursively drain
        self.running = True; passed = []; actions = pass_count = 0
        try:
            self.checkpoint()
            while self.holder is not None:
                self.checkpoint()
                passed[:] = [seat for seat in passed if self.alive(seat)]
                if len([seat for seat in self.order() if self.alive(seat)]) <= 1:
                    self.table.end_check()
                    return True
                seat = self.holder
                if not self.alive(seat):
                    self.holder = self.next_alive(seat); continue
                choices = self.table.priority_choices(seat)
                policy = getattr(self.table, 'priority_policy', None)
                choice = policy(seat, tuple(self.frames), choices) if policy else self.table.choose_priority(seat, choices)
                if choice is None:
                    self.passes += 1; pass_count += 1
                    if pass_count > self.max_window_passes:
                        self.table.safe_runner._stop('priority_pass_budget')
                    self.history.append(('pass', seat, tuple(f.frame_id for f in self.frames)))
                    passed.append(seat)
                    live = {s for s in self.order() if self.alive(s)}
                    if set(passed) == live:
                        passed.clear()
                        if not self.frames: return True  # current phase/window can finish
                        self.resolve_top()
                    else:
                        self.holder = self.next_alive(seat)
                    continue
                if choice not in choices: raise ValueError('Priority policy chose an illegal action')
                actions += 1
                if actions > self.max_window_actions:
                    self.table.safe_runner._stop('priority_action_budget')
                passed.clear()  # ANY action, including a mana ability, resets passes
                self.history.append(('action', seat, choice.kind))
                self.responses_attempted += int(bool(self.frames))
                self.table.commit_choice(seat, choice)
                self.holder = seat
                self.checkpoint()
            return True
        finally:
            self.running = False
