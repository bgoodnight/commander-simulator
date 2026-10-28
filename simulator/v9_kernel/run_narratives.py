"""Deterministic infrastructure replays with Magnus moved through four seats."""
from __future__ import annotations
import json
from pathlib import Path
from adapter import V9Table
from table import CentralTable as V8Table
ROOT=Path(__file__).resolve().parent
CASES=[('01_original_seat',102,0,('aggro','control','combo'),None),
       ('02_right_of_aggro',104,1,('aggro','tokens','ramp_stompy'),None),
       ('03_third_seat',103,2,('control','spellslinger','midrange'),None),
       ('04_forced_seat_three',404,3,('control','combo','tokens'),('Sol Ring','Young Pyromancer','Harmonic Prodigy','Ponder','Preordain','Island'))]
records=[]
for label,seed,detailed,opponents,opening in CASES:
    kinds=list(opponents);kinds.insert(detailed,'magnus')
    t=V9Table(kinds,seed=seed,trace=True,opening=opening).run(10)
    old=V8Table(opponents,seed=seed,trace=False,opening=opening).run(10)
    record={'case':label,'seed':seed,'providers':kinds,'forced_opening':bool(opening),
            'rounds':t.round_num,'winner':t.winner,'win_reason':t.win_reason,
            'detailed_seat':detailed,'magnus_life':t.details.life,
            'magnus_spells':t.details.cards_cast,
            'v8_same_seed_baseline':{'magnus_life':old.details.life,'magnus_spells':old.details.cards_cast,'reason':old.win_reason},
            'consistent':t.world.consistent(),'safety_stop':t.safety_stop,
            'coverage':dict(t.details.coverage),'unsupported_seen':dict(t.details.unsupported_seen)}
    records.append(record)
    columns=['seat','archetype','life','cards_cast','creatures','land_count']
    lines=[f'# v9 infrastructure narrative: {label}',
           f'**Seed:** {seed} · **Magnus seat:** {detailed} · **Forced opening:** {bool(opening)}',
           f'**Result:** {t.win_reason}; winner {t.winner}; Magnus life {t.details.life} after {t.round_num} rounds',
           '', '| Seat | Provider | Life | Casts | Creatures | Mana sources |',
           '|---:|---|---:|---:|---:|---:|']
    for p in t.players:
        lines.append(f'| {p.seat} | {p.archetype} | {p.life} | {p.cards_cast} | {len(p.creatures)} | {p.available_sources()} |')
    lines.extend(['','## Diagnostics',
      f'- Kernel views consistent: **{t.world.consistent()}**',
      f'- Safety stop: **{t.safety_stop}**',
      f'- Shared-stack depth: **{t.spell_stack.max_depth_seen}**',
      f'- Casts resolved: **{t.spell_stack.spells_resolved}**; countered: **{t.spell_stack.spells_countered}**',
      f'- Unsupported named cards seen: `{dict(t.details.unsupported_seen)}`',
      f'- Same-seed v8 Magnus at seat zero: life {old.details.life}; spells {old.details.cards_cast}',
      '- Different seat numbering changes turn ordering, random choice and response behavior; this is not a deck-strength comparison.',
      '', '## Action-by-action transcript','```text',*t.events,'```','',
      '## Boundaries','Card-zone and typed-source services are tested separately; this live replay still uses legacy hand/library, mana, counter-only priority, and incomplete named-card effects.'])
    (ROOT/(label+'.md')).write_text('\n'.join(lines)+'\n')
    (ROOT/(label+'.json')).write_text(json.dumps({'record':record,'rounds':t.turns,'diagnostics':t.diagnostics(),'events':t.events},indent=2)+'\n')
    print(label, 'seat',detailed,'life',t.details.life,'spells',t.details.cards_cast,'consistent',t.world.consistent())
(ROOT/'narrative_results.json').write_text(json.dumps(records,indent=2)+'\n')
