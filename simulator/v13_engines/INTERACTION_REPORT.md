# V13 interaction results

All 7 targeted scenarios passed. Each Markdown narrative has a companion JSON record of source payments, selection, engine events and priority.

| Scenario | Observed outcome |
|---|---|
| [Exact selection across five spells](01_selection_choices.md) | Brainstorm: Abrade selected with exact requested top/bottom choices; Ponder: Abrade selected with exact requested top/bottom choices; Preordain: Abrade selected with exact requested top/bottom choices; Telling Time: Abrade selected with exact requested top/bottom choices; Impulse: Abrade selected with exact requested top/bottom choices. Brainstorm/Ponder/Preordain draw; Telling Time/Impulse put a looked-at card into hand. |
| [Prowess, trigger doubling and Wizard adaptation](02_prowess_types.md) | Ponder gave Harmonic exactly +1/+1, doubled Pyromancer to 2 Elementals, and created 1 Iconoclast Soldier. After Adaptation resolved, Preordain doubled Iconoclast too. Totals: 4 Elementals, 4 Soldiers. Harmonic reached 4/6 after three noncreature casts, then returned to 1/3 in cleanup. |
| [Artifact power tracks tokens entering and being spent](03_artifact_power.md) | Artist was 4 power with Sol Ring plus an artifact Soldier. Ponder added 2 Treasures and another Soldier, raising it to 7. Activating an actual Treasure for U immediately lowered power to 6. That mana paid for Preordain; its triggers added 3 artifacts, raising power to 9. |
| [Baral loot is successful-counter-only and independently optional](04_baral_counter.md) | An actual Counterspell countered the control seat's creature spell. Harmonic doubled Baral into two separate loot triggers. The first was accepted (draw then discard); the second was declined. Counterspell's colored UU requirement was preserved despite Baral. |
| [Copies trigger again and delayed exile is not doubled](05_copy_expiry.md) | With Harmonic, the first spell produced 2 Stormsplitter tokens. The second produced 6 more: 9 Stormsplitters including the original. At the next end-step beginning, exactly 8 delayed exile abilities queued (not doubled). Tokens survived until those abilities resolved, then all 8 ceased; the original remained. |
| [A copy made during an end step waits through cleanup](06_late_copy.md) | Brainstorm was cast with actual source mana during end-step priority. Its Stormsplitter token was created after that step began. It survived cleanup, then its delayed exile triggered and resolved at the following player's end step. |
| [Queued copies survive a source bounce without copying pumps](07_copy_last_known.md) | Ponder queued a copy trigger. Capsize responded, queuing another before bouncing the pumped original Stormsplitter. Both copy triggers resolved: the older one used last-known copiable values. Both tokens were base 1/4, not the modified original's 4/7; the actual original card returned to hand. |

Sweep: 200 twelve-round games across all four Magnus seats; 0 safety stops; 100652 steps; 10948 source payments; 454 selection-choice records; 234 engine events. All consistency/conservation checks passed.

Exploratory median milliseconds per eight-round game (12 samples/engine): {'CombatTable': 331.252, 'EngineTable': 448.467}. Card-selection and engine changes alter trajectories, so this is not an isolated microbenchmark.

One real detailed deck plus synthetic opponents; no win-rate inference. Safety stops, if any, remain unresolved games.
