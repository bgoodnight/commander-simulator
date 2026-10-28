# Magnus the Red v1.6 — Timing-policy Monte Carlo

Run date: 2026-10-28  
Deck: exact 100-card v1.6 prototype (`magnus_thousand_sons_v1_6.txt`), with 99-card library and Magnus in command zone.

## Question
Does casting Magnus at the first legal opportunity, waiting one complete turn to develop the cabal, or waiting until setup/protection is ready produce the best early engine and resilience?

## Design
2,500 seeded randomized games per policy per scenario; **15,000 simulated games** in total. Six experiments: three policies × (no disruption or one opposing instant-speed removal spell after turn five development). The same starting random seeds are reused for the competing policies. One free London-style mulligan; ordinary multiplayer Commander turn-one draw. A simple priority-based pilot plays lands and conventional mana rocks, uses Brainstorm/Ponder/Preordain/Telling Time/Impulse/Frantic Search, casts low-cost Wizard and token engine permanents, and seeks to deploy Magnus.

**Policies:**
1. **Rush:** first turn with enough colored mana to cast Magnus, after land and mana rocks.
2. **Delay one:** pass on the first opportunity, develop cheaper engine pieces, then attempt Magnus the following turn.
3. **Prepared:** wait at least one turn and then seek an engine and a modeled defensive option. If waiting too long, attempt deployment from turn seven onward.

**Modeled effects:** Sol Ring (2 colorless), Arcane Signet, Talisman of Creativity, Fellwar Stone (assumed to provide needed blue/red), Izzet Signet (one mana in, UR out), Mind Stone, basic/dual lands, Baral/Goblin Electromancer cost reduction on instants/sorceries, Magnus token discount on instants/sorceries, Young Pyromancer/Third Path Iconoclast/Docent/Stormsplitter token triggers on modeled instant/sorcery casts, Harmonic Prodigy amplification when applicable, Storm-Kiln Artist Treasure generation, Sorcerer Class level-two *spell-only* creature mana (with tap readiness restrictions), Jace's looting, and an assumed 50% chance each later turn of Magnus connecting in combat. Selected counters and the defensive abilities of Voidmage Prodigy and Patron Wizard were modeled. Counter outcomes are simplified: Flusterstorm, for example, can fail if its tax is paid. Commander tax increases by two after a removal/recast.

**Not modeled or simplified:** Full official priority and mana rules, all possible choices and casts, opponent combat, all card effects and tutor resolution, actual multiplayer interaction, Phyrexian Altar sacrifice timing, Underworld Breach reuse, Resonating Lute untap synergies, late-game combo execution, and long-run win rates. This model has optimistic mana/color assumptions and extremely limited spellcasting; the Patron Wizard tax-counter success in the removal test is an arbitrary 50% when eligible. Qualitative direction matters more than individual percentage points.

## Without disruption

| Outcome | Rush | Delay one | Prepared |
|:--|--:|--:|--:|
| First cast of Magnus by turn 5 | 77.7% | 41.4% | 14.2% |
| First cast of Magnus by turn 6 | 88.2% | 76.6% | 34.2% |
| Useful engine permanent present when Magnus enters | 67.2% | 77.6% | 82.9% |
| Token-generating creature already present when Magnus enters | 24.9% | 33.5% | 38.7% |
| At least one creature token already present when Magnus enters | 3.2% | 4.6% | 6.6% |
| Castable counterspell or Voidmage protection when Magnus enters | 6.8% | 26.0% | 32.8% |
| Engine permanent **and** castable counterspell/Voidmage when Magnus enters | 4.6% | 21.0% | 27.4% |
| Magnus plus a usable engine present by end of turn 6 | 74.9% | 62.4% | 34.2% |
| Magnus plus a usable engine present by end of turn 8 | 87.8% | 84.5% | 82.8% |

**Important:** "Usable engine" is an intentionally broad status proxy: a board containing an independently useful Wizard/resource piece, not a proven self-sustaining combo. The model casts only a small selection of spells, so it substantially understates the number of tokens a real deck may create by continuing to cast interactive spells.

## With one attempted removal after turn five

The scripted opponent targets Magnus if he is already in play, otherwise targets a valuable engine creature. A held counterspell, Voidmage Prodigy, or an assumed successful Patron Wizard tax can stop it. This scenario is **not** a statistical estimate of actual opponent behavior.

| Outcome | Rush | Delay one | Prepared |
|:--|--:|--:|--:|
| Removal spell successfully stopped (all trials) | 26.1% | 32.9% | 33.6% |
| Magnus on battlefield after turn 6 | 48.7% | 64.8% | 20.2% |
| Magnus plus a useful engine after turn 6 | 37.6% | 45.7% | 20.2% |
| Magnus plus a useful engine after turn 7 | 61.0% | 65.3% | 59.1% |
| Magnus plus a useful engine after turn 8 | 74.0% | 76.5% | 73.6% |

## Interpretation

1. **The one-turn delay is a defensible default** if opponents are likely to remove Magnus: the model shows a 16-point increase in Magnus's presence at the end of turn six (64.8% vs 48.7%) under the specified disruption. It also shows a roughly fourfold increase in arriving with a castable counterspell or Voidmage protection (26.0% vs 6.8% without disruption).
2. **The delay is not automatically optimal** in a low-interaction game: rush has a higher chance of Magnus plus an engine on the battlefield by the end of turn six (74.9% vs 62.4%).
3. **Waiting for a perfect board is expensive:** the prepared policy enters with more protection conditionally but yields much less midgame commander uptime.
4. **One turn of setup does not magically create tokens:** raw token presence at deployment is rare in this simple model. Prefer deploying a token engine plus a castable cheap spell and either an untapped counter or Wizard defense before Magnus.
5. **Current bottleneck is available defense on the cast turn**, even after a one-turn delay. Supporting the cabal with cheap interaction or a repeatable Wizard-based counterspell is more meaningful than adding another finisher.

## Pilot rule recommendation
Cast Magnus when you already have **(a) a meaningful benefit**, such as a token engine and a cheap instant/sorcery or two existing tokens, and **(b) a way to protect the next exchange**, such as held low-cost interaction or untapped Wizard defenses. In a low-threat game with no protection, casting earlier is justified when it produces an immediate discount or expected token attack. If the board is empty, use the five-mana turn to develop a rock and one or two engine pieces instead.

## Reproducibility
- `magnus_v16_patient_sim.py` — script
- `magnus_v16_patient_results.json` — raw metrics and policies
- `magnus_thousand_sons_v1_6.txt` — deck tested

Note: run-count uncertainty near 50% is around ±2 percentage points at a rough 95% confidence interval from sampling, *in addition to the much larger uncertainty from game-model assumptions*.
