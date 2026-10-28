"""Open the next-end-step delayed-trigger window before ordinary end priority."""
from combat_turns import CombatDriver


class EngineDriver(CombatDriver):
    def window(self,step,phase,priority=True):
        if step!='end':return super().window(step,phase,priority)
        okay=super().window(step,phase,False)
        self.t.begin_end_step()
        if priority:
            self.t.spell_stack.holder=self.t.active_seat;self.t.spell_stack.resolve()
        return okay and not self.t.end_check()
