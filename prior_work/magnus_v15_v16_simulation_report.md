# Magnus the Red — v1.5 versus v1.6 early-game simulation

**Date:** October 27, 2026  
**Decks:** Same 35 lands and six conventional mana rocks. v1.6 swaps Cryptic Gateway → Telling Time; Guttersnipe → Preordain; Past in Flames → Impulse.

## Results

| Metric | v1.5 | v1.6 | Δ percentage points |
|---|---:|---:|---:|
| Saw early selection by turn 5 | 23.02% | 48.49% | +25.47 |
| Saw >=2 selection spells by turn 5 | 1.36% | 11.05% | +9.69 |
| Saw a mana rock by turn 5 | 54.80% | 54.78% | -0.02 |
| Saw an early cabal creature by turn 5 | 70.42% | 70.47% | +0.05 |
| Saw a conventional counter by turn 5 | 54.92% | 54.85% | -0.07 |
| Cast selection by turn 3 | 18.11% | 38.38% | +20.27 |
| Four lands by turn 5 | 71.10% | 75.51% | +4.41 |
| Magnus deployed by turn 4 | 31.22% | 33.74% | +2.52 |
| Magnus deployed by turn 5 | 62.58% | 67.69% | +5.11 |
| Magnus deployed by turn 6 | 73.92% | 78.62% | +4.70 |
| Magnus and early engine by turn 6 | 51.84% | 56.94% | +5.10 |
| Magnus and counter in hand by turn 6 | 46.62% | 51.09% | +4.47 |
| Magnus cast with held cheap-counter mana by turn 6 | 3.28% | 4.05% | +0.77 |
| Magnus + live counter mana at end of turn 6 main phase | 30.37% | 34.01% | +3.64 |
| Magnus + live counter mana at end of turn 7 main phase | 38.99% | 42.68% | +3.69 |

## Interpretation

- v1.6 greatly improves access to early hand-smoothing (23% → 48.5% by turn five).
- With the same land and rock counts, the ramp improvement comes from finding land/rocks with selection spells. The illustrative sequencing model suggests Magnus deployment by turn five improves from roughly 63% to 68%.
- A cabal/early engine together with Magnus by turn six rises from roughly 52% to 57%.
- Immediate counterspell mana on the turn Magnus enters is still scarce under an earliest-cast policy; delaying Magnus to leave open protection should be tested.
- The cheap selection package helps, but there is no modeled increase in intrinsic access to counterspells or the buyback card suite.
- The simulation does not model full tutoring, opposing removal, exact board-state combos, and does not predict wins.

## Methods and limitations

1. **150,000 natural-access draws:** shuffled 99-card libraries with an opening seven and one card drawn per turn; no mulligans, spell effects, or opponents. Cards seen is not the same as cards cast.
2. **18,000 simplified play sequences per deck:** prioritize playing one land per turn, casting six conventional mana rocks, using available inexpensive selection spells to find useful cards, casting inexpensive engine creatures, and casting Magnus when mana is available. Ponder, Preordain, Telling Time, Impulse and Brainstorm change the simulated library/hand as appropriate. A modeled Jace can loot on later turns.
3. **Not a full rules engine:** Izzet Signet and mana-color allocation are approximated; not all ETB taps, costs, mana-generation spells, tutors, or triggered abilities are simulated. The pilot does not deliberately keep open counterspell mana.
4. **No opponents:** protection is a proxy based on a held counterspell and residual mana, not the ability to survive in a real match. It does not credit Patron Wizard/Voidmage Prodigy board control, phasing, or alternate protection.
5. **Not comparable to earlier absolute rates:** different sequencing assumptions were used. The meaningful estimates are the side-by-side v1.5/v1.6 differences under the same method.

## Recommended next experiment

Run a patient-Magnus casting policy (delay commander one turn when a counter can be held up), and compare 35 versus 36 lands or an additional two-mana rock only if the early-mana bottleneck persists.

## Source materials

- `magnus_sim_v16.py` (reproducible script)
- `magnus_v15_v16_results.json` (numeric results)
- `magnus_thousand_sons_v1_6.txt` (new decklist)
- `magnus_thousand_sons_v1_6_import.txt` (one card per line)
