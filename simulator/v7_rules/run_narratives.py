"""Reproduce the small v7 qualitative validation set; no Monte Carlo calibration."""
from pathlib import Path
import json
from collections import Counter
from bridge import ModularTable
from loops import LoopCertificate,LoopResolver
ROOT=Path(__file__).resolve().parent
CASES=[
 ('01_mixed',102,('aggro','control','combo'),None),
 ('02_pressure',104,('aggro','tokens','ramp_stompy'),None),
 ('03_control_heavy',103,('control','spellslinger','midrange'),None),
 ('04_forced_triggers',404,('control','combo','tokens'),
  ['Sol Ring','Young Pyromancer','Preordain','Ponder','Island','Mountain','Harmonic Prodigy'])]
results=[]
for name,seed,opponents,opening in CASES:
    table=ModularTable(opponents,seed=seed,trace=True,opening=opening).run(10)
    p=table.details
    record={'case':name,'seed':seed,'opponents':opponents,'forced_opening':bool(opening),
            'outcome':table.win_reason,'winner':table.winner,'rounds':table.round_num,
            'magnus_life':p.life,'magnus_casts':p.commander_casts,'casts':p.cards_cast,
            'tokens':p.token_count(),'shared_triggers':table.shared_triggers,
            'cost_queries':table.shared_cost_queries,'safety_stop':table.safety_stop,
            'total_casts':table.counts['casts'],'eliminations':table.eliminations}
    results.append(record)
    (ROOT/(name+'.json')).write_text(json.dumps({'record':record,'diagnostics':table.diagnostics(),
                                                 'rounds':table.turns,'events':table.events},indent=2)+'\n')
    md=[f'# V7 narrated test: {name}',f'**Seed:** {seed}  · **Opponents:** {", ".join(opponents)}  · **Opening:** {"FORCED test fixture" if opening else "natural"}',
        f'**Result:** {table.win_reason}; winner {table.winner}; rounds {table.round_num}',
        f'**Magnus:** {p.life} life; {p.cards_cast} spells; commander cast {p.commander_casts}×; {p.token_count()} creature tokens.',
        f'**V7 rules:** {table.shared_triggers} trigger instances; {table.shared_cost_queries} cost checks; safety stop = {table.safety_stop or "none"}.',
        '', '## Round-level state',
        '| Round | Magnus life / tokens / spells cast | Others life (P1/P2/P3) |',
        '|---:|---|---|']
    for row in table.turns:
        a,b,c,d=row['players']
        md.append(f"| {row['round']} | {a['life']} / {a['tokens']} / {a['cards_cast']} | {b['life']} / {c['life']} / {d['life']} |")
    md+=['','## Full action narrative','```text',*table.events,'```','',
         '## Important scope note','This is a synthetic mixed-table diagnostic, not a validated Magnus win-rate game. '
         'The v7 rules kernel currently centralizes cost/trigger/keyword/target primitives via an adapter. '
         'The full stack, commander damage, exact card effects, and opponent card behavior remain unfinished.']
    (ROOT/(name+'.md')).write_text('\n'.join(md)+'\n')

# A hypothetical verified loop demonstration to test STOP and compressed lethal;
# NOT a claim that these conditions are assembled in the current Magnus deck.
planner=LoopResolver()
ex=LoopCertificate('illustrative_burn_loop',True,True,True,damage_each_opponent=1,
                   targets=(1,2,3),response_window_resolved=True)
example=planner.evaluate(ex,{1:12,2:38,3:40},library_size=30)
unsafe=planner.evaluate(LoopCertificate('illustrative_draw_burn',True,True,True,
                    damage_each_opponent=1,draw_per_cycle=1,targets=(1,2,3),response_window_resolved=True),
                    {1:12,2:38,3:40},library_size=30)
(ROOT/'narrative_results.json').write_text(json.dumps({'games':results,
   'hypothetical_loop_demonstration':{'compressed_lethal':vars(example),'draw_loop':vars(unsafe)}},indent=2)+'\n')
print(json.dumps({'games':results,'loop_demo':{'lethal':vars(example),'unsafe':vars(unsafe)}},indent=2))
