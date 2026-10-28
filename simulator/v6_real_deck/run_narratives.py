"""Reproduce v6 integration narratives. Intentionally four games, not Monte Carlo."""
import json
from pathlib import Path
from integrated import MixedTable
ROOT=Path(__file__).parent
CASES=[
    ('01_unforced_mixed',102,('aggro','control','combo'),None,10),
    ('02_unforced_pressure',105,('aggro','tokens','ramp_stompy'),None,10),
    ('03_unforced_magnus',103,('control','spellslinger','midrange'),None,10),
    ('04_forced_opening_diagnostic',404,('control','combo','tokens'),
        ['Island','Mountain','Island','Sol Ring','Young Pyromancer','Preordain','Counterspell'],10),
]
rows=[]
for name,seed,archetypes,opening,rounds in CASES:
    t=MixedTable(archetypes,seed,trace=True,opening=opening).run(rounds)
    p=t.details
    dat={'summary':t.summary(),'diagnostics':t.diagnostics(),'turns':t.turns,'events':t.events}
    (ROOT/f'{name}.json').write_text(json.dumps(dat,indent=2))
    lines=[f'# v6 narrated game: {name}',f'**Seed:** {seed}  **Seats:** Magnus (real v1.6), '+', '.join(archetypes),
           f'**Opening:** {"FORCED diagnostic, not a random opening" if opening else "random v1.6 opening"}',
           f'**Result:** {t.summary()["outcome"]}, winner seat {t.winner}, {t.round_num} rounds',
           '## Summary of the Magnus seat',
           f'- Life {p.life}; {p.lands} lands; {p.cards_cast} total spells cast; Magnus cast {p.commander_casts} time(s); {p.token_count()} tokens on battlefield at end.',
           f'- Cards cast by coverage: {dict(p.coverage)}; remaining unsupported in hand: {[c.name for c in p.hand if c.effect=="unsupported"]}.',
           f'- Unsupported distinct nonland card definitions: {len(t.diagnostics()["unsupported_definitions"])}.',
           '\n## Board-state timeline',
           '| Round | Magnus life / creatures / tokens / mana sources | P1 life/power | P2 life/power | P3 life/power |',
           '|---:|---|---|---|---|']
    for round in t.turns:
        ps=round['players'];a=ps[0]
        cells=[f"{a['life']} / {a['creatures']} / {a['tokens']} / {a['sources']}"]
        cells.extend(f"{x['life']} / {x['power']}" if x['alive'] else 'OUT' for x in ps[1:])
        lines.append('| '+str(round['round'])+' | '+' | '.join(cells)+' |')
    lines.extend(['\n## Event-by-event narrative','```text',*t.events,'```',
                 '\n## Important limitations','This is a mixed-deck integration diagnostic, **not** a valid Magnus deck power or win-rate evaluation. '
                 'Unsupported cards cannot resolve; some selection spells and the opponent stack remain simplified. '
                 'See `ASSESSMENT.md` for supported interactions and missing mechanics.'])
    (ROOT/f'{name}.md').write_text('\n'.join(lines)+'\n')
    rows.append({'name':name,'seed':seed,'opening_forced':bool(opening),'opponents':list(archetypes),
                 'ending_round':t.end_round,'outcome':t.win_reason,'magnus_life':p.life,
                 'magnus_casts':p.commander_casts,'magnus_spells_cast':p.cards_cast,'final_tokens':p.token_count(),
                 'named_support_cast':dict(p.coverage),'unsupported_remaining':sum(c.effect=='unsupported' for c in p.hand),
                 'counters_used':p.counters_used,'removal_used':p.removal_used,
                 'losses':t.eliminations})
(ROOT/'narrative_results.json').write_text(json.dumps(rows,indent=2))
for row in rows:print(row)
