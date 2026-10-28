import json
from pathlib import Path
from engine import Table,sample_archetypes
root=Path(__file__).parent
cases=[('trace_random_table',sample_archetypes(20261028),20261028),('trace_controlled_table',['aggro','control','ramp_stompy'],20261029)]
for name,profiles,seed in cases:
    games=[]
    for inter in (False,True):
        t=Table(profiles,seed=seed,interaction=inter,trace=True).run(10)
        games.append(t)
    head=[f'# {name.replace("_"," ").title()}', '',f'**Seed:** {seed}  ',f'**Archetypes:** {", ".join(profiles)}  ', '**Fourth seat:** passive Magnus (40 life, no board, no responses).', '',
          '## Paired outcomes (exact same abstract decks/draw order at initialization)', '',
          '| Seat | Without interaction: life / power / threat | With interaction: life / power / threat |',
          '|---|---|---|']
    for i in range(4):
        p0,p1=games[0].players[i],games[1].players[i]
        head.append(f'| {p0.seat}: {p0.arch} | {p0.life} / {p0.power()} / {p0.threat():.1f} | {p1.life} / {p1.power()} / {p1.threat():.1f} |')
    head+=['','## Main run — full event trace','', '```text',*games[1].events,'```','', '## No-interaction run — full event trace','', '```text',*games[0].events,'```']
    (root/f'{name}.md').write_text('\n'.join(head))
    print(name,profiles,[(p.life,p.power(),p.threat()) for p in games[1].players],len(games[1].events))
