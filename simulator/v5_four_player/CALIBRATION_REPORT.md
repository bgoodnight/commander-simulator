# Commander Simulation v5 — Four active-player calibration

**Status:** preliminary abstract-archetype prototype; NOT an empirical metagame model or the full Magnus deck.
**Trials:** 2,800 random tables, 120 mirror games for each of seven play types, and 140 controlled games for each of six matchups; seed 20261028.

## Core results
- Winner found in **2,740/2,800 (97.9%)** random tables by the 30-round stopping point.
- Median completed game finished in round **18.0**; 10th/90th percentile completed games ended in rounds **13/24**.
- Median first elimination round: **14.0**.
- **484** random tables featured at least one single effect eliminating multiple players (combo or damage burst).

## Mixed-table wins per archetype seat
A deck type may appear in more than one seat per game. Denominator is the number of seats occupied by that type. Unresolved games count as non-wins; rates need not sum to exactly 100%.

| Play type | Seats | Wins | Wins / occupied seat |
|---|---:|---:|---:|
| aggro | 1,574 | 276 | 17.5% |
| tokens | 1,567 | 393 | 25.1% |
| ramp_stompy | 1,605 | 474 | 29.5% |
| control | 1,606 | 341 | 21.2% |
| spellslinger | 1,641 | 408 | 24.9% |
| midrange | 1,586 | 423 | 26.7% |
| combo | 1,621 | 425 | 26.2% |

**Diagnosis:** Combo initially dominated with an abstract two-piece win. Requiring three independently drawn/deployed setup pieces yields a less skewed spread; this is a provisional calibration, not proof that real decks are balanced. Aggro is still low relative to Ramp/Stompy.

## How games end

| Final cause | Games |
|---|---:|
| combat | 2085 |
| resolved_combo | 392 |
| persistent_finisher | 120 |
| spell_burst | 84 |
| turn_limit | 60 |
| burn | 32 |
| empty_library | 27 |

## Identical-archetype mirrors

A four-Control mirror can run long; a four-Spellslinger mirror can burst opponents out. Medians below are for completed games only; censored games are reported separately.

| Four of one play type | Median completed ending round | Completed by 30 rounds | Multi-elimination games |
|---|---:|---:|---:|
| aggro | 14.0 | 120/120 (100.0%) | 0 |
| tokens | 16.0 | 120/120 (100.0%) | 0 |
| ramp_stompy | 16.5 | 118/120 (98.3%) | 0 |
| control | 27 | 85/120 (70.8%) | 0 |
| spellslinger | 17.0 | 120/120 (100.0%) | 35 |
| midrange | 17.5 | 118/120 (98.3%) | 0 |
| combo | 18 | 119/120 (99.2%) | 117 |

## Controlled matchup checks

| Matchup | Median completed ending | Completed | Winning types |
|---|---:|---:|---|
| aggro + control + combo + ramp_stompy | 20.0 | 138/140 | control 40, combo 34, aggro 32, ramp_stompy 32, unresolved 2 |
| aggro + aggro + control + combo | 19.5 | 136/140 | aggro 62, control 48, combo 26, unresolved 4 |
| tokens + tokens + control + combo | 19 | 135/140 | tokens 60, combo 39, control 36, unresolved 5 |
| control + spellslinger + combo + midrange | 20 | 133/140 | combo 41, control 36, spellslinger 32, midrange 24, unresolved 7 |
| aggro + tokens + ramp_stompy + midrange | 14.0 | 140/140 | ramp_stompy 55, midrange 39, tokens 26, aggro 20 |
| control + control + combo + spellslinger | 23.0 | 128/140 | control 51, combo 46, spellslinger 31, unresolved 12 |

## What is actually modeled
- Every seat has a shuffled 99-card *abstract category* deck with fixed card action costs, hand draws and imperfect land development. Early ramp/engine permanents persist or can be removed.
- Four active players have actual life totals; attack damage and burn reduce life. A player is eliminated at zero or less and their resources leave the game.
- Noncombat finishers: a three-piece Combo win attempt can be countered, Spellslinger deals mass damage, Control deploys a persistent direct-damage clock, and Ramp/Midrange deploy overrun buffs.
- Generated actions have types (creature, instant, sorcery, artifact, enchantment), target objects, costs, and generic effect identifiers. Removal and counterspell responses depend on type and targetability.
- Counterspells use player mana and cards; one counter-counter is possible. Creatures can trade in combat, with one blocker per attacker and no detailed combat tricks.
- Same action/resolution engine accepts an injected detailed-deck pilot and named action definitions, without assuming Magnus occupies any specific seat.

## Known modeling limitations and calibration targets
1. **Game speed:** Median completed random match lasts 18 rounds, which may be slow for the intended moderately tuned Commander environment. Real tables vary widely; game length is a parameter to validate, not a fact about the metagame.
2. **Uneven archetypes:** Aggro wins less often than Ramp/Stompy; avoid forcing exact equal rates until archetype action profiles and game traces are qualitatively checked.
3. **Abstract resource economy:** Opponents have fixed-cost generic cards, simplified free redraws, no full color system, no actual commanders, no commander damage, no planeswalkers, no land abilities.
4. **Simplified resolution:** No comprehensive stack, priority, combat keyword set, instant-speed blocker removal, or complete response windows. Some effects (e.g. persistent overrun bonuses) stand in for richer printed effects.
5. **Interaction frequency:** Counterspell willingness and removal targeting are synthetic assumptions rather than fitted to real table logs.
6. **No fully implemented detailed deck:** The v3 Magnus catalog is packaged in `v3_source/`; the `v3_bridge_manifest.json` reports exactly which cards still need adapters. The named-card demo is an interface test, not a Magnus win-rate simulation.
7. **Winner statistics:** A 30-round stopping rule censors long games; mirroring and randomized seating reduce seat bias but do not eliminate model bias.

## Next engineering stages
1. Inspect the four narrated replays, paying attention to why Control survives, why Aggro gets attacked, and whether the Combo progress requirement feels realistic.
2. Add mana-color and exact-cost adapters, and replace the current three named-card demonstration with complete detailed-deck action registration.
3. Implement rich response hooks for Patron Wizard, Voidmage Prodigy, Sigil Tracer, selected buyback loops, and board protection, validating printed-text details and shared resource payment.
4. Calibrate moderate-vs-fast-vs-slow tables using measured or manually reviewed Commander games, then rerun matched seeds before proposing new swaps.

## Reproducibility
Run `python tests.py`, `python experiments.py`, `python replays.py`, `python integration_demo.py`. All scripts use the Python standard library, no network. The entire package is included in the archive.
