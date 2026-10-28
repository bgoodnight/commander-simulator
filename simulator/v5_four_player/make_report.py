"""Rebuild human-readable calibration report from results_v5.json."""
import json
from pathlib import Path
from simulation import ROOT

def build():
 d=json.loads((ROOT/'results_v5.json').read_text())
 s=d['random_tables']['summary']; meta=d['meta']
 lines=['# Commander Simulation v5 — Four active-player calibration',
        '', '**Status:** preliminary abstract-archetype prototype; NOT an empirical metagame model or the full Magnus deck.',
        f'**Trials:** {meta["mixed_trials"]:,} random tables, {meta["mirror_trials_per_type"]} mirror games for each of seven play types, and {meta["controlled_trials_per_matchup"]} controlled games for each of six matchups; seed {meta["seed"]}.',
        '', '## Core results',
        f'- Winner found in **{s["completed"]:,}/{s["games"]:,} ({s["completion_pct"]}%)** random tables by the 30-round stopping point.',
        f'- Median completed game finished in round **{s["median_finish_round"]}**; 10th/90th percentile completed games ended in rounds **{s["p10_finish_round"]}/{s["p90_finish_round"]}**.',
        f'- Median first elimination round: **{s["first_elimination_round_median"]}**.',
        f'- **{s["multi_elim_games"]}** random tables featured at least one single effect eliminating multiple players (combo or damage burst).',
        '', '## Mixed-table wins per archetype seat',
        'A deck type may appear in more than one seat per game. Denominator is the number of seats occupied by that type. Unresolved games count as non-wins; rates need not sum to exactly 100%.',
        '', '| Play type | Seats | Wins | Wins / occupied seat |', '|---|---:|---:|---:|']
 for a,x in d['random_tables']['archetypes'].items():
  lines.append(f'| {a} | {x["seat_exposures"]:,} | {x["wins"]:,} | {x["wins_per_seat_pct"]}% |')
 lines+=['', '**Diagnosis:** Combo initially dominated with an abstract two-piece win. Requiring three independently drawn/deployed setup pieces yields a less skewed spread; this is a provisional calibration, not proof that real decks are balanced. Aggro is still low relative to Ramp/Stompy.',
        '', '## How games end', '', '| Final cause | Games |', '|---|---:|']
 for cause,n in sorted(s['win_causes'].items(),key=lambda x:-x[1]):lines.append(f'| {cause} | {n} |')
 lines+=['', '## Identical-archetype mirrors',
         '', 'A four-Control mirror can run long; a four-Spellslinger mirror can burst opponents out. Medians below are for completed games only; censored games are reported separately.',
         '', '| Four of one play type | Median completed ending round | Completed by 30 rounds | Multi-elimination games |',
         '|---|---:|---:|---:|']
 for a,x in d['mirrors'].items():
  lines.append(f'| {a} | {x["median_finish_round"]} | {x["completed"]}/{x["games"]} ({x["completion_pct"]}%) | {x["multi_elim_games"]} |')
 lines+=['','## Controlled matchup checks','','| Matchup | Median completed ending | Completed | Winning types |','|---|---:|---:|---|']
 for name,x in d['controlled'].items():
  wins=', '.join(f'{k} {v}' for k,v in sorted(x['winner_archetypes'].items(),key=lambda z:-z[1]))
  lines.append(f'| {" + ".join(x["archetypes"])} | {x["median_finish_round"]} | {x["completed"]}/{x["games"]} | {wins} |')
 lines+=['','## What is actually modeled',
         '- Every seat has a shuffled 99-card *abstract category* deck with fixed card action costs, hand draws and imperfect land development. Early ramp/engine permanents persist or can be removed.',
         '- Four active players have actual life totals; attack damage and burn reduce life. A player is eliminated at zero or less and their resources leave the game.',
         '- Noncombat finishers: a three-piece Combo win attempt can be countered, Spellslinger deals mass damage, Control deploys a persistent direct-damage clock, and Ramp/Midrange deploy overrun buffs.',
         '- Generated actions have types (creature, instant, sorcery, artifact, enchantment), target objects, costs, and generic effect identifiers. Removal and counterspell responses depend on type and targetability.',
         '- Counterspells use player mana and cards; one counter-counter is possible. Creatures can trade in combat, with one blocker per attacker and no detailed combat tricks.',
         '- Same action/resolution engine accepts an injected detailed-deck pilot and named action definitions, without assuming Magnus occupies any specific seat.',
         '', '## Known modeling limitations and calibration targets',
         '1. **Game speed:** Median completed random match lasts 18 rounds, which may be slow for the intended moderately tuned Commander environment. Real tables vary widely; game length is a parameter to validate, not a fact about the metagame.',
         '2. **Uneven archetypes:** Aggro wins less often than Ramp/Stompy; avoid forcing exact equal rates until archetype action profiles and game traces are qualitatively checked.',
         '3. **Abstract resource economy:** Opponents have fixed-cost generic cards, simplified free redraws, no full color system, no actual commanders, no commander damage, no planeswalkers, no land abilities.',
         '4. **Simplified resolution:** No comprehensive stack, priority, combat keyword set, instant-speed blocker removal, or complete response windows. Some effects (e.g. persistent overrun bonuses) stand in for richer printed effects.',
         '5. **Interaction frequency:** Counterspell willingness and removal targeting are synthetic assumptions rather than fitted to real table logs.',
         '6. **No fully implemented detailed deck:** The v3 Magnus catalog is packaged in `v3_source/`; the `v3_bridge_manifest.json` reports exactly which cards still need adapters. The named-card demo is an interface test, not a Magnus win-rate simulation.',
         '7. **Winner statistics:** A 30-round stopping rule censors long games; mirroring and randomized seating reduce seat bias but do not eliminate model bias.',
         '', '## Next engineering stages',
         '1. Inspect the four narrated replays, paying attention to why Control survives, why Aggro gets attacked, and whether the Combo progress requirement feels realistic.',
         '2. Add mana-color and exact-cost adapters, and replace the current three named-card demonstration with complete detailed-deck action registration.',
         '3. Implement rich response hooks for Patron Wizard, Voidmage Prodigy, Sigil Tracer, selected buyback loops, and board protection, validating printed-text details and shared resource payment.',
         '4. Calibrate moderate-vs-fast-vs-slow tables using measured or manually reviewed Commander games, then rerun matched seeds before proposing new swaps.',
         '', '## Reproducibility',
         'Run `python tests.py`, `python experiments.py`, `python replays.py`, `python integration_demo.py`. All scripts use the Python standard library, no network. The entire package is included in the archive.','']
 (ROOT/'CALIBRATION_REPORT.md').write_text('\n'.join(lines))
 print('Report built from',meta)
if __name__=='__main__':build()
