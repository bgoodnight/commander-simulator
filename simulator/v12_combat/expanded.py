"""V12 combat expansion, reusing the live zone/mana/priority/step engine."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v11_steps'))
from stepped import StepTable
from battle import ExpandedCombat
from combat_turns import CombatDriver


class CombatTable(StepTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.combat_engine = ExpandedCombat(self)

    def run(self, max_rounds=8): return CombatDriver(self).run(max_rounds)

    def diagnostics(self):
        d = super().diagnostics()
        d['known_rules_gaps'] = [s for s in d['known_rules_gaps'] if 'single blockers' not in s and 'multiblock' not in s]
        d['known_rules_gaps'].append('no commander damage, live spell copies or verified Magnus loops')
        d['known_rules_gaps'].append('no multi-attacker blockers, deathtouch/lifelink, prevention or planeswalker/battle attacks')
        d['v12'] = dict(multiple_blockers=True, trample=True, first_strike=True, double_strike=True,
                        damage_assignment='chosen at damage time; no assignment order',
                        limits=['each blocker blocks one attacker', 'player attacks only',
                                'no new named cards or keyword-granting spells', 'pilot remains heuristic'])
        return d
