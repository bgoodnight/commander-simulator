import json
from pathlib import Path
root=Path(__file__).parent
x=json.loads((root/'results.json').read_text());sn=json.loads((root/'snowball_results.json').read_text())
lines=['# Magnus v4 — Opponent-only escalation calibration', '',
       '**Design:** Seven archetypes, each with its own synthetic 99-card deck and unified play priorities. Three independent opponents plus a *passive* 40-life Magnus placeholder. This is not a real Commander win-rate simulation.', '',
       '**Trials:** 600 uninterrupted 10-turn games per archetype (4,200 archetype games); 350 sampled three-opponent tables replayed both without and with interference (700 table games); 300 extra 8-turn snowball diagnostics per archetype (2,100 games); 15 automated tests.', '',
       '## 1. Goldfish trajectories', '',
       'Each entry is P10 / median / P90 **public threat index** in arbitrary proxy units, not win chance.', '',
       '| Play type | Turn 4 | Turn 8 | Turn 10 |','|---|---|---|---|']
for a,v in x['goldfish'].items():
    s=v['trajectory'];values=[]
    for t in [4,8,10]:values.append('/'.join(str(round(z,1)) for z in s[str(t)]['threat_p10_p50_p90']))
    lines.append('| '+a+' | '+' | '.join(values)+' |')
lines+=['',
        'Qualitative patterns: Aggro produces early board power; Ramp/Stompy produces more available mana by turn four; Tokens is widest and largest by turn ten due to compounded engines and buffs. Control and Combo are undercounted by the simple public-threat proxy, which currently values visible board and mana more than counterspells or hidden kill setup.', '',
        '## 2. Early favorable or unfavorable draws compound', '',
        'These are **observational groups**, not randomized causal effects. Values show mean turn-8 threat, sample sizes in parentheses.', '',
        '| Archetype | ≤3 mana sources at T4 | ≥5 mana sources at T4 | No engine at T4 | Engine at T4 |',
        '|---|---|---|---|---|']
for row in sn['results']:
    def render(key):
        z=row[key]
        return (f"{z['mean_t8_threat']} (n={z['n']})" if z['n'] else '—')
    lines.append('| '+row['archetype']+' | '+' | '.join(render(k) for k in ['early_mana_le_3','early_mana_ge_5','early_engine_no','early_engine_yes'])+' |')
lines+=['','## 3. Opponent-on-opponent interaction', '',
        'The same seeded starting libraries are used without and with opponent disruption. Later libraries can diverge because removing an engine changes subsequent draws.', '',
        '| Archetype | Median T10 power, no interaction | Median T10 power, with interaction | Mean creatures lost, with interaction |',
        '|---|---:|---:|---:|']
no=x['random_tables_no_interaction']['profiles'];yes=x['random_tables_with_interaction']['profiles']
for a in sorted(no):lines.append(f"| {a} | {no[a]['median_board_power']} | {yes[a]['median_board_power']} | {yes[a]['avg_creatures_lost']} |")
all_interact=x['random_tables_with_interaction'];ev=all_interact['events_total']
lines+=['',f"Across 350 intervened tables, opponents resolved **{ev.get('cast_removal',0)} generic removal spells**, **{ev.get('counters_used',0)} counterspells**, and **{ev.get('board_wipes_resolved',0)} board wipes**; **{ev.get('combat_deaths',0)} creatures** died in direct combat. This demonstrates real erosion of developed boards, although rates have not been calibrated to empirical tables.", '',
        '### Attacking targets by ordinal rank (conditional on eligibility)', '',
        'Raw target counts cannot be directly compared by rank because the rank-one player cannot target itself. The fractions below use only opportunities when a player of that rank was a legal target.', '',
        '| Target public-threat rank | Selected / eligible | Selection rate |','|---|---:|---:|']
for rank in range(1,5):
    k=f'attack_rank{rank}';n=all_interact['targets_by_threat_rank'].get(k,0);d=all_interact['eligible_target_opportunities'].get(k,0)
    lines.append(f'| {rank} | {n} / {d} | {n/d:.1%} |')
lines+=['',f"The passive Magnus seat was eliminated in {all_interact['passive_magnus_eliminated_pct']}% of interacted tables by turn 10; **this is not a Magnus survival estimate** because the seat does not play cards or respond to threats.", '',
        '## 4. Replay files', '',
        '- `trace_random_table.md` — automatically sampled Combo + Tokens + Spellslinger, seed 20261028. Paired no-interference and interactive turn-by-turn logs.',
        '- `trace_controlled_table.md` — Aggro + Control + Ramp/Stompy, seed 20261029. Same paired logs.', '',
        '## 5. Assessment and remaining issues', '',
        '**Working qualitatively:** fixed abstract draw costs, mana screw/flood, snowball development from early ramp and engines, separate opponents and life totals, multiple actions per turn when budget permits, probabilistic rank-sensitive target selection, targeted engine/creature destruction, simple blockers and combat deaths, and counterspells/wipes.', '',
        '**Still not trustworthy for card optimization:** (1) threat score undervalues control/hidden combo; (2) Token growth may be exaggerated; (3) mulligans, colored costs, combat and interaction are stylized; (4) abstract combo finishers record attempts instead of wins; (5) Magnus does not yet participate. Add an explicit public-versus-objective threat-and-defense scorecard and validate the curves against representative gameplay, then connect v3 Magnus event/response interfaces before testing deck swaps.', '',
        'All rates and template assumptions are synthetic and **not metagame-derived**.']
(root/'ASSESSMENT.md').write_text('\n'.join(lines)+'\n')
print('Wrote ASSESSMENT.md')
