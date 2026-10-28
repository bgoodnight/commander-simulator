"""Produce exact deterministic narration of four-player tests."""
from simulation import Table,ROOT
import json

SCENARIOS={
 'control_mirror':(55000,['control']*4),
 'spellslinger_burst':(55007,['spellslinger']*4),
 'aggro_aggro_control_combo':(55000,['aggro','aggro','control','combo']),
 'mixed_archetypes':(55000,['aggro','control','combo','ramp_stompy']),
}

def write_scenario(name,seed,types):
 t=Table(types,seed=seed,trace=True).run(30)
 summary=t.summary()
 path=ROOT/f'replay_{name}.md'
 s=[f'# Four-player replay: {name.replace("_"," ").title()}',
    f'**Seed:** {seed} · **Seats:** '+', '.join(f'P{i} {a}' for i,a in enumerate(types)),
    f'**Result:** '+(f'P{t.winner} wins ({t.win_reason}) in round {t.end_round}' if t.winner is not None else f'Unresolved at round 30 ({t.win_reason})'),
    '\n## Elimination order']
 for e in summary['eliminations']:
    s.append(f'- Round {e["round"]}: P{e["seat"]} ({e["archetype"]}) eliminated by {e["cause"]}')
 s+=['\n## Board-state timeline','Life is the actual game resource; public threat is an arbitrary target-selection proxy.']
 s.append('| Round | P0 life / power / mana | P1 life / power / mana | P2 life / power / mana | P3 life / power / mana | Public leader |')
 s.append('|---:|---|---|---|---|---|')
 for x in t.turns:
    p=x['players'];r=x['rankings'];leader=next((f'P{seat}' for seat,v in r.items() if v==1),'—')
    s.append('| '+str(x['round'])+' | '+' | '.join(f'{q["life"]} / {q["power"]} / {q["sources"]}' if q['alive'] else 'OUT' for q in p)+' | '+leader+' |')
 s+=['\n## Detailed action log','This is a simplified Commander model, not a rules-accurate MTG game.']
 s.extend(t.events)
 path.write_text('\n'.join(s)+'\n')
 (ROOT/f'replay_{name}.json').write_text(json.dumps({'summary':summary,'turns':t.turns},indent=2))
 return path,summary

if __name__=='__main__':
 for name,(seed,types) in SCENARIOS.items():
  path,summary=write_scenario(name,seed,types)
  print(path.name,len(path.read_text()),summary['winner_archetype'],summary['outcome'],summary['ending_round'])
