"""Explicit ordinary turn steps with priority and mana-pool boundaries."""
from rules import SafetyStop, TriggerResult
import simulation as base

STEPS = ('untap', 'upkeep', 'draw', 'precombat_main', 'begin_combat', 'declare_attackers',
         'declare_blockers', 'combat_damage', 'end_combat', 'postcombat_main', 'end', 'cleanup')

class StepDriver:
    def __init__(self, table): self.t = table

    def window(self, step, phase, priority=True):
        t = self.t
        t.resources.empty_pools(); t.step = step; t.phase = phase
        t.step_history.append((t.turn_serial, t.active_seat, step))
        t.note(f'  STEP P{t.active_seat}: {step}.')
        if priority:
            t.spell_stack.holder = t.active_seat
            t.spell_stack.resolve()
        return not t.end_check()

    def turn(self, player):
        t = self.t; t.active_seat = player.seat; t.turn_serial += 1
        t.safe_runner.new_turn(t.turn_serial); t.main_actions = 0
        self.window('untap', 'beginning', False)
        t.attack_ready[player.seat] = {o.object_id for o in t.rules.controlled(player.seat, {'creature'})}
        t.resources.untap(player.seat)
        for c in player.creatures: t.world.refresh(c.id)
        t.emit('turn_start', controller=player.seat, round=t.round_num)
        self.window('upkeep', 'beginning', False)
        # Synthetic engines/clocks declare approximate upkeep trigger operations.
        if player is not t.details:
            for permanent in tuple(player.permanents):
                if permanent.entered_round >= t.round_num: continue
                if permanent.kind == 'engine':
                    if player.rng.random() < base.TEM['engine']['extra_draw_chance']:
                        t.spell_stack.trigger(TriggerResult(permanent.id, player.seat, 'draw'))
                        t.counts['bonus_draws'] += 1
                    if player.rng.random() < base.TEM['engine']['token_chance']:
                        t.spell_stack.trigger(TriggerResult(permanent.id, player.seat, 'create_token',
                                              args=(('token_id', 'elemental_1_1'),)))
                elif permanent.kind == 'clock' and t.rivals(player):
                    target = t.choose_target(player, 'clock')
                    t.spell_stack.trigger(TriggerResult(permanent.id, player.seat, 'damage_player',
                                          args=(('target', target.seat), ('amount', permanent.value))))
        t.spell_stack.holder = player.seat; t.spell_stack.resolve()
        if t.end_check(): return
        self.window('draw', 'beginning', False)
        if player.alive: player.draw()  # multiplayer: first player also draws
        t.spell_stack.holder = player.seat; t.spell_stack.resolve()
        if t.end_check(): return
        if not self.window('precombat_main', 'main'): return
        if not self.window('begin_combat', 'combat'): return
        self.window('declare_attackers', 'combat', False)
        if player.alive: t.combat_engine.declare_attackers(player)
        else: t.combat_engine.attacks = []
        t.spell_stack.holder = player.seat; t.spell_stack.resolve()
        if t.end_check(): return
        if t.combat_engine.attacks:  # no attackers: skip blockers and damage steps
            self.window('declare_blockers', 'combat', False)
            t.combat_engine.declare_blockers()
            t.spell_stack.holder = player.seat; t.spell_stack.resolve()
            if t.end_check(): return
            self.window('combat_damage', 'combat', False)
            t.combat_engine.damage(player)
            t.spell_stack.holder = player.seat; t.spell_stack.resolve()
            if t.end_check(): return
        if not self.window('end_combat', 'combat'): return
        t.main_actions = 0
        if not self.window('postcombat_main', 'main'): return
        if not self.window('end', 'ending'): return
        self.window('cleanup', 'cleanup', False)
        # Cleanup normally gives no priority; repeat if a trigger/SBA window opens.
        for _ in range(16):
            t.cleanup_step(player)
            if not t.spell_stack.pending and not t.spell_stack.frames: break
            t.spell_stack.holder = player.seat; t.spell_stack.resolve()
        else: t.safe_runner._stop('cleanup_repeat_budget')
        t.resources.empty_pools(); t.assert_consistent()

    def run(self, rounds):
        t = self.t
        order = list(range(4)); t.rng.shuffle(order); t.turn_order = order
        try:
            for round_num in range(1, rounds + 1):
                t.round_num = round_num
                t.note(f'\n========== ROUND {round_num} ==========')
                for seat in order:
                    player = t.players[seat]
                    if player.alive: self.turn(player)
                    if t.end_check(): break
                t.turns.append({'round': round_num, 'players': [p.snapshot(round_num) for p in t.players],
                                'rankings': t.rankings()})
                if t.end_round is not None: break
        except SafetyStop as exc:
            t.safety_stop = exc.reason; t.win_reason = 'unresolved_safety_guard'
            t.winner = None; t.end_round = None
            t.note('  SAFETY HALT, unresolved: ' + exc.reason)
        if t.end_round is None and t.safety_stop is None: t.win_reason = 'turn_limit'
        t.assert_consistent()
        return t
