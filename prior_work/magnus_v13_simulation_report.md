# Magnus the Red — Thousand Sons Conclave v1.3
## Monte Carlo opening, mana development, and natural combo access

Date: 27 October 2026. Analyzed `/mnt/data/magnus_thousand_sons_v1_3.txt` (99-card library + Magnus the Red).

### Methodology
- 18,000 independently shuffled 99-card libraries, with an opening seven and one draw per turn on turns 1–10 (Commander multiplayer). No tutors, opponent interaction, extra drawing, scry, or actual spell play in these raw-access probabilities.
- 10,000 simple free-mulligan trials: keep seven with 2–4 lands; otherwise redraw seven and bottom one card (favoring a nonland, or a land if heavily flooded). This is a simplified one-mulligan London policy, not an optimal mulligan solver.
- 7,000 coarse mana-development trials: land drops and ramp rocks prioritized, with broad blue/red access and common enters-tapped heuristics. No mana spent on nonrock spells. These are optimistic opportunities, NOT cast-Magnus probabilities in fully played games.
- All percentages approximate; differences below ~1 percentage point may be sampling noise. Card-combination results are only *naturally seen* pieces, not assembled/resolved combos.

### Opening seven
| Event | % |
|---|---:|
| 0–1 land | 22.26 |
| 2–4 lands | 72.95 |
| 5–7 lands | 4.79 |
| 2–4 lands plus either Young Pyromancer or Third Path Iconoclast | 9.17 |
| 2–4 lands plus a rock (Sol Ring, Arcane Signet, Talisman, Izzet Signet) | 18.17 |

After a single simple free mulligan, 93.84% of retained hands have 2–4 lands; approximately 6% still have 0–1.

### Raw card access (unassisted)
| Metric | T3 | T4 | T5 | T8 |
|---|---:|---:|---:|---:|
| Draw at least the turn number in lands | 75.61 | 58.74 | 41.99 | 9.97 |
| See a conventional mana rock | 35.21 | 38.14 | 40.79 | 48.61 |
| See Young Pyromancer or Third Path Iconoclast | 18.94 | 20.83 | 22.57 | 27.78 |
| See any listed token source, including expensive cards | 53.99 | 57.78 | 61.43 | 70.36 |
| See a conventional counter, including Muddle | 47.81 | 51.26 | 54.51 | 63.30 |
| See removal/bounce | 54.43 | 58.08 | 61.39 | 69.84 |
| See one mana engine and one buyback card | 14.02 | 16.47 | 19.06 | 27.23 |

The token-source group includes slow/conditional cards, so it exaggerates the likelihood of *deploying* a token producer that early.

### Coarse mana-only sequence (optimistic)
| Turn | >=4 available mana | >=5 available mana with blue/red |
|---|---:|---:|
| 3 | 24.11 | 7.00 |
| 4 | 68.04 | 22.00 |
| 5 | 76.47 | 53.79 |
| 6 | 82.71 | 64.43 |

The mana heuristic has simplifying assumptions about Izzet Signet timing, Cascade Bluffs filtering, tapped lands, and spends mana on rocks but not on spells, engine creatures or protection. These figures are optimistic and are not estimates of the odds of resolving Magnus.

### Natural combo-card access by end of turn 8
| Pieces naturally seen | % of sequences |
|---|---:|
| Storm-Kiln Artist + Searing Touch | 2.317 |
| Young Pyromancer + Phyrexian Altar + Mystic Speculation | 0.256 |
| Stormsplitter + Sorcerer Class + Mystic Speculation | 0.317 |
| Stormsplitter + Phyrexian Altar + Mystic Speculation | 0.283 |
| Mathemagics + at least one copy effect (Twincast, Reverberate, Reiterate, Tzaangor Shaman, Dualcaster Mage) | 8.456 |
| Mathemagics + at least two of Twincast / Reverberate / Reiterate | 0.828 |

All percentages *exclude* tutors, extra draws, graveyard access, Mana Geyser, pre-existing token discount requirements, and needed resources. Natural combo access thus understates search/draw effects but grossly overstates readiness to win. Do not use these values as game win probabilities.

### Incremental benchmark calculations (exact hypergeometric, not simulated full gameplay)
| Modification | Raw access improvement |
|---|---|
| Two early token sources -> four: at least one seen by T3 | 19.27% -> 35.14% |
| Four rocks -> six: at least one seen by T3 | 35.14% -> 48.14% |
| 35 lands -> 36 lands: draw fourth land by T4 | 59.22% -> 62.09% |
| 35 lands -> 36 lands: opening 0–1 lands | 21.80% -> 20.15% |

Suggested focus, *not yet a deck edit*: prioritize more inexpensive token sources (e.g. Ral's Reinforcements, Dragon Fodder or Saheeli, Sublime Artificer), at least one more early ramp source, and a possible 36th land. Preserve the critical Wizard-control pieces, buyback loops, and Mathemagics alternative win condition.

### Interpretation
- Three bottlenecks are apparent: only two inexpensive repeatable token producers, only four conventional low-cost rocks, and few cheap card-draw spells.
- The very low natural appearance of three-card loops in the first 15 cards is expected in singleton Commander; the relevant fix is *overlapping functional roles* plus efficient card selection/tutors, not relying on a specific hand.
- Revisit spell/interaction slot economy before adding further costly engine pieces.
- Proper game-level performance requires a rules engine plus opponent models, which this test does not provide.
