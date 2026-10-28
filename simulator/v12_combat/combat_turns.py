"""Damage-step scheduling with a checkpoint and priority after each batch."""
from driver import StepDriver


class CombatDriver(StepDriver):
    def damage_steps(self, player):
        t = self.t; combat = t.combat_engine
        early = combat.begin_damage()
        stages = ('first_strike_damage', 'combat_damage') if early else ('combat_damage',)
        for stage in stages:
            self.window(stage, 'combat', False)
            combat.damage(player, stage=stage)
            t.spell_stack.holder = player.seat
            t.spell_stack.resolve()
            if t.end_check(): return False
        return True
