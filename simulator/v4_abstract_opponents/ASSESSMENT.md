# Magnus v4 — Opponent-only escalation calibration

**Design:** Seven archetypes, each with its own synthetic 99-card deck and unified play priorities. Three independent opponents plus a *passive* 40-life Magnus placeholder. This is not a real Commander win-rate simulation.

**Trials:** 600 uninterrupted 10-turn games per archetype (4,200 archetype games); 350 sampled three-opponent tables replayed both without and with interference (700 table games); 300 extra 8-turn snowball diagnostics per archetype (2,100 games); 15 automated tests.

## 1. Goldfish trajectories

Each entry is P10 / median / P90 **public threat index** in arbitrary proxy units, not win chance.

| Play type | Turn 4 | Turn 8 | Turn 10 |
|---|---|---|---|
| aggro | 11.8/15.3/19.0 | 24.6/32.1/41.9 | 30.4/40.8/52.2 |
| tokens | 10.9/15.9/20.9 | 29.1/43.4/62.7 | 38.6/59.0/88.6 |
| ramp_stompy | 9.4/13.7/18.7 | 26.3/37.8/48.3 | 33.0/47.5/63.0 |
| control | 8.5/12.9/17.8 | 20.8/31.2/43.0 | 26.0/40.9/56.3 |
| spellslinger | 8.8/13.7/19.2 | 24.7/37.0/48.5 | 34.3/51.0/65.8 |
| midrange | 9.5/14.0/18.0 | 23.7/33.9/43.6 | 30.4/42.6/56.6 |
| combo | 8.5/13.2/18.4 | 23.6/36.1/47.8 | 31.5/48.2/64.9 |

Qualitative patterns: Aggro produces early board power; Ramp/Stompy produces more available mana by turn four; Tokens is widest and largest by turn ten due to compounded engines and buffs. Control and Combo are undercounted by the simple public-threat proxy, which currently values visible board and mana more than counterspells or hidden kill setup.

## 2. Early favorable or unfavorable draws compound

These are **observational groups**, not randomized causal effects. Values show mean turn-8 threat, sample sizes in parentheses.

| Archetype | ≤3 mana sources at T4 | ≥5 mana sources at T4 | No engine at T4 | Engine at T4 |
|---|---|---|---|---|
| aggro | 29.22 (n=84) | 35.03 (n=47) | 32.66 (n=275) | 42.06 (n=25) |
| tokens | 33.57 (n=53) | 44.59 (n=105) | 37.88 (n=128) | 47.9 (n=172) |
| ramp_stompy | 21.98 (n=15) | 38.14 (n=235) | 34.24 (n=191) | 41.92 (n=109) |
| control | 22.58 (n=29) | 30.96 (n=161) | 24.0 (n=112) | 34.02 (n=188) |
| spellslinger | 30.13 (n=25) | 38.48 (n=183) | 32.73 (n=100) | 40.25 (n=200) |
| midrange | 25.39 (n=21) | 33.83 (n=171) | 31.35 (n=207) | 38.49 (n=93) |
| combo | 22.94 (n=25) | 36.87 (n=179) | 29.29 (n=103) | 38.12 (n=197) |

## 3. Opponent-on-opponent interaction

The same seeded starting libraries are used without and with opponent disruption. Later libraries can diverge because removing an engine changes subsequent draws.

| Archetype | Median T10 power, no interaction | Median T10 power, with interaction | Mean creatures lost, with interaction |
|---|---:|---:|---:|
| aggro | 30 | 6 | 7.25 |
| combo | 16 | 5 | 3.85 |
| control | 18 | 5 | 4.12 |
| midrange | 28 | 9 | 5.45 |
| ramp_stompy | 32 | 9 | 4.89 |
| spellslinger | 22 | 6 | 6.04 |
| tokens | 40 | 8 | 10.95 |

Across 350 intervened tables, opponents resolved **1130 generic removal spells**, **439 counterspells**, and **97 board wipes**; **4474 creatures** died in direct combat. This demonstrates real erosion of developed boards, although rates have not been calibrated to empirical tables.

### Attacking targets by ordinal rank (conditional on eligibility)

Raw target counts cannot be directly compared by rank because the rank-one player cannot target itself. The fractions below use only opportunities when a player of that rank was a legal target.

| Target public-threat rank | Selected / eligible | Selection rate |
|---|---:|---:|
| 1 | 2402 / 4142 | 58.0% |
| 2 | 3584 / 7656 | 46.8% |
| 3 | 2691 / 9193 | 29.3% |
| 4 | 1861 / 10011 | 18.6% |

The passive Magnus seat was eliminated in 7.1% of interacted tables by turn 10; **this is not a Magnus survival estimate** because the seat does not play cards or respond to threats.

## 4. Replay files

- `trace_random_table.md` — automatically sampled Combo + Tokens + Spellslinger, seed 20261028. Paired no-interference and interactive turn-by-turn logs.
- `trace_controlled_table.md` — Aggro + Control + Ramp/Stompy, seed 20261029. Same paired logs.

## 5. Assessment and remaining issues

**Working qualitatively:** fixed abstract draw costs, mana screw/flood, snowball development from early ramp and engines, separate opponents and life totals, multiple actions per turn when budget permits, probabilistic rank-sensitive target selection, targeted engine/creature destruction, simple blockers and combat deaths, and counterspells/wipes.

**Still not trustworthy for card optimization:** (1) threat score undervalues control/hidden combo; (2) Token growth may be exaggerated; (3) mulligans, colored costs, combat and interaction are stylized; (4) abstract combo finishers record attempts instead of wins; (5) Magnus does not yet participate. Add an explicit public-versus-objective threat-and-defense scorecard and validate the curves against representative gameplay, then connect v3 Magnus event/response interfaces before testing deck swaps.

All rates and template assumptions are synthetic and **not metagame-derived**.
