"""Shared four-seat turn driver; neither pilot nor deck subtype owns the round loop."""
from __future__ import annotations
from rules import SafetyStop

class TurnDriver:
    def __init__(self,table):self.t=table
    def run(self,max_rounds=10):
        t=self.t
        order=list(range(len(t.players)))
        t.rng.shuffle(order);t.turn_order=order
        try:
            for turn in range(1,max_rounds+1):
                t.round_num=turn;t.note(f'\n========== ROUND {turn} ==========')
                for seat in order:
                    p=t.players[seat]
                    if not p.alive:continue
                    t.upkeep(p,turn)
                    if p.alive:
                        t.main(p)
                        t.combat(p)
                    t._cleanup_expiring()
                    if t.end_check():break
                t.turns.append({'round':turn,'players':[p.snapshot(turn) for p in t.players],
                                'rankings':t.rankings()})
                if t.trace:
                    t.note('  End round: '+', '.join(
                        f'P{q.seat} {q.archetype} life={q.life} board={q.power()} sources={q.available_sources()}'
                        for q in t.alive()))
                if t.end_round is not None:break
        except SafetyStop as exc:
            t.safety_stop=exc.reason;t.win_reason='unresolved_safety_guard';t.winner=None;t.end_round=None
            t.note('  SAFETY HALT (unresolved): '+exc.reason)
        if t.end_round is None and t.safety_stop is None:t.win_reason='turn_limit'
        return t
