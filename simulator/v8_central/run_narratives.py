"""Small reproducible qualitative diagnostics, not deck-strength calibration."""
import json
from pathlib import Path
from table import CentralTable
from bridge import ModularTable
ROOT=Path(__file__).resolve().parent
CASES=[('01_mixed',102,('aggro','control','combo'),None),
       ('02_pressure',104,('aggro','tokens','ramp_stompy'),None),
       ('03_control_heavy',103,('control','spellslinger','midrange'),None),
       ('04_forced_triggers',404,('control','combo','tokens'),('Sol Ring','Young Pyromancer','Harmonic Prodigy','Ponder','Preordain','Island'))]
records=[]
for label,seed,opponents,opening in CASES:
    t=CentralTable(opponents,seed=seed,trace=True,opening=opening).run(10)
    old=ModularTable(opponents,seed=seed,trace=False,opening=opening).run(10)
    d=t.diagnostics()['v8'];prior=old.summary()
    record={'case':label,'seed':seed,'opponents':opponents,'opening_forced':bool(opening),
            'winner':t.winner,'reason':t.win_reason,'rounds':t.round_num,
            'magnus_life':t.details.life,'magnus_casts':t.details.commander_casts,
            'magnus_spells':t.details.cards_cast,'tokens':t.details.token_count(),
            'opponent_lives':{str(p.seat):p.life for p in t.players[1:]},
            'eliminations':t.eliminations,'v8':d,
            'v7_paired_reference':{'magnus_life':old.details.life,'outcome':prior['outcome'],
                                   'magnus_spells':old.details.cards_cast}}
    records.append(record)
    lines=[f'# V8 narrated game: {label}',
           f'**Seed:** {seed} | **Seats:** Magnus vs {", ".join(opponents)} | **Opening:** {"forced diagnostic" if opening else "shuffled"}',
           f'**Result:** {t.win_reason}; winner seat {t.winner}; Magnus life {t.details.life} after {t.round_num} rounds',
           '', '## Player scoreboard',
           '| Seat | Pilot | Life | Casts | Creatures left | Mana sources |',
           '|---:|---|---:|---:|---:|---:|']
    for p in t.players:
        lines.append(f'| {p.seat} | {p.archetype} | {p.life} | {p.cards_cast} | {len(p.creatures)} | {p.available_sources()} |')
    lines+=['','## Shared-rule diagnostics',
            f'- Persistent-kernel vs legacy-view consistency: **{d["kernel_view_consistent"]}**',
            f'- Shared-stack max depth: **{d["shared_stack_max_depth"]}**; countered frames: **{d["shared_stack_countered"]}**',
            f'- Game-object zone transitions: **{d["zone_transitions"]}**; simultaneous combat-damage batches: **{d["combat_damage_batches"]}**',
            f'- Trigger instances: **{t.shared_triggers}**; cost queries: **{t.shared_cost_queries}**',
            f'- Safety stop: **{t.safety_stop}**',
            f'- Magnus unsupported cards held: {dict(t.details.unsupported_seen)}',
            '', '## Round-by-round comparison',
            '| Round | Magnus life | Token count | P1 life | P2 life | P3 life |',
            '|---:|---:|---:|---:|---:|---:|']
    for row in t.turns:
        p=row['players'];lines.append(f'| {row["round"]} | {p[0]["life"]} | {p[0]["tokens"]} | {p[1]["life"]} | {p[2]["life"]} | {p[3]["life"]} |')
    lines+=['','## Action-by-action transcript','```text',*t.events,'```',
            '', '## Scope reminder',
            'This is an infrastructure diagnostic. v8 does not claim accurate deck win rates. '
            'Counterspell response priority is bounded and simplified; selection, several lands, and unimplemented real cards remain partial.']
    (ROOT/(label+'.md')).write_text('\n'.join(lines)+'\n')
    (ROOT/(label+'.json')).write_text(json.dumps({'summary':t.summary(),'record':record,'diagnostics':t.diagnostics(),
                                                      'rounds':t.turns,'events':t.events},indent=2)+'\n')
    print(label,'Magnus life',t.details.life,'spells',t.details.cards_cast,'v7',old.details.life,'stack',d['shared_stack_max_depth'],'consistency',d['kernel_view_consistent'])
(ROOT/'narrative_results.json').write_text(json.dumps(records,indent=2)+'\n')
