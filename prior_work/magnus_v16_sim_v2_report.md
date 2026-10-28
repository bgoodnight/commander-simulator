# Magnus the Red v1.6 — improved early-game simulation

**Run:** October 28, 2026. **Deck:** unchanged v1.6, 99 library cards plus commander. **Trials:** 1,800 independent shuffled starting sequences per policy per scenario (10,800 simulated games), seed 20261028. Three policies share identical card draws and the same pilot routines except the decision to deploy Magnus; two scenarios (no disruption, and one hypothetical opponent removal spell at the end of turn 5).

## What has improved versus the earlier model

- Reads the real 100-card deck and uses a fresh randomized 99-card library. Includes one free mulligan of hands with 0–1 or 5–7 lands; then plays as drawn.
- All policies spend mana using the *same* deterministic heuristics: play lands, use cheap selection to find missing resources, cast ordinary mana rocks, cast eligible Magnus based on policy, develop available Wizard/token/mana engines, and spend remaining mana on suitable selection / small utility spells. The earlier script gave one strategy extra development slots; that bias is removed.
- Tracks colored mana and tapped physical sources, floating surplus from Sol Ring, Izzet Signet's input mana and UR output, and Treasure. It treats Lute's land-generated extra mana and level-two Sorcerer Class mana as restricted to instant/sorcery spells (and models basic phasing/expiry of Stormsplitter token copies at end step).
- Models common cheap Wizards and cantrips including Preordain, Ponder, Brainstorm, Impulse, Telling Time, and Frantic Search. Simulates Young Pyromancer, Third Path Iconoclast, Stormsplitter, Docent, Storm-Kiln Artist, Archmage Emeritus, and Harmonic Prodigy trigger effects during modeled spell casts. Models the instant/sorcery generic discounts of Magnus, Baral and Goblin Electromancer, including buyback's generic portion.
- Phyrexian Altar can sacrifice an existing token to make mana (the discount is computed before the payment), and Jace can loot. Some Spellseeker tutor options are modeled. A scripted opponent removal spell can be met with selected counters, Voidmage Prodigy or a sufficiently large Patron Wizard tax. Commander tax is added on later castings.
- Compares: **rush** (cast Magnus at the first opportunity), **delay one** (skip the first opportunity and attempt on a later turn), and **conditional** (wait at least one turn for useful setup/defense, but allow deployment from turn seven).

## Results (percentage of all simulated games)

### With no opposing disruption

| Outcome | Rush | Delay one turn | Conditional |
|---|---:|---:|---:|
| Cast Magnus by turn 5 | 73.5% | 34.8% | 17.5% |
| Cast Magnus by turn 6 | 86.1% | 72.6% | 45.0% |
| At Magnus's first arrival: engine **and** protection available | 13.1% | 31.6% | 38.1% |
| Magnus plus an engine on battlefield at end of turn 6 | 80.7% | 67.2% | 45.0% |
| Magnus + engine + protection available at end of turn 6 | 40.4% | 30.0% | 28.8% |
| Magnus plus an engine on battlefield at end of turn 8 | 91.5% | 88.7% | 88.5% |

### With one opposing removal attempt at end of turn 5

| Outcome | Rush | Delay one turn | Conditional |
|---|---:|---:|---:|
| Removal spell stopped | 23.3% | 26.5% | 25.2% |
| Magnus plus an engine present at end of turn 6 | 43.2% | **56.8%** | 36.8% |
| Magnus + engine + protection at end of turn 6 | 11.4% | 14.4% | 15.3% |
| Magnus plus an engine present at end of turn 8 | 81.2% | 84.8% | 85.2% |

The opponent is assumed to have 2 generic mana to pay soft counter taxes, and targets Magnus if present, or a useful support creature otherwise. This is **one illustrative threat**, not a model of actual opponent removal frequency or a win probability.

### Other useful observations

- At least one modeled card-selection spell had been cast by turn 3 in ~39–40% of games. Early mana is no longer left idle by a special rule that only allowed cantrips when land-starved.
- Players paid around 6.6–7.6 total mana by the end of turn 4 in the model (depending on policy). This is an action-economy proxy, not the proportion of all potentially generated mana that was spent.
- **Two or more creature tokens already in play when Magnus first arrives is uncommon** (~5–8% in the undisturbed trials). This is partly a modeling limitation: most interaction and spellcasting are not being played, and spells such as Chaos Warp, Jeska's Will, and later graveyard casts are not executed.
- Simulated instant/sorcery cast counts are only ~1.4 by turn 8 in undisturbed games, far below a real, active spellslinger game. Hence none of the token counts or late-game combo estimates should be considered realistic endgame production forecasts.
- The difference in 'at arrival' protection is substantial, but **absolute protection chances are approximate**: the model handles a limited group of real counters and does not model priority, redirection, all cards, or threat-specific targeting.

## What the results actually say

**The one-turn delay is an appealing default against interactive opponents**, because the v1.6 deck often spends most of its available mana to deploy Magnus and cannot protect him on the same turn. Under one removal attempt, delaying improves end-of-turn-six Magnus-plus-engine presence by **13.6 percentage points** (56.8 vs. 43.2). Without pressure, casting Magnus immediately produces a turn-six engine more often (80.7 vs. 67.2), and delaying does not have an unconditional benefit.

**Do not hard-code a delay.** Use a conditional play rule: defer Magnus if the additional setup turn can add a functional engine or protection, but cast him sooner if he already creates immediate value and opponents aren't representing dangerous interaction. The current 'conditional' pilot is too conservative: it waits for a narrow checklist and loses too much tempo.

**Don't change any deck slots yet.** The largest remaining source of uncertainty is card-play logic rather than the deck's exact 99.

## Ranked next improvements

1. **Better action planner (highest priority):** allow 2–3 turn lookahead / beam search instead of a fixed greedy spell order; consider spending 5 mana on two cheap permanents + cantrip against casting Magnus. Model decisions to hold up interaction and casting Magnus after other actions within the same turn.
2. **More spells, more real triggers:** implement key drawn interactive spells (Pongify, Abrade, Chaos Warp, March of Swirling Mist), actual token triggers and a representative opposing threat. The current model systematically underplays instants/sorceries and therefore understates both tokens and Treasures.
3. **Card tutor/graveyard engine:** model Muddle the Mixture transmute, Step Through Wizardcycling, Mystical Tutor, Underworld Breach escape, Exalted Flamer, and selected buyback loops with exact legal casting costs. Separate 'combo assembled' from 'actually executable with mana'.
4. **More precise mana and permanents:** true Cascade Bluffs filtering, exact Fellwar Stone colors from opponents, full Fabled Passage / Mystic Sanctuary logic, class activation timing, Jace transforming, triggered spell-copy effects, mana left floating on the stack, and spell-specific restrictions. Some of these are only approximated now.
5. **Representative opponent profiles:** test a control opponent with counters, an aggro opponent demanding early removal, and a midrange opponent with one wipe or graveyard hate; vary timing and success of interaction rather than only one targeted removal on turn five.
6. **Pilot calibration and uncertainty:** test smarter mulligan rules, policies that hold counterspell mana, and alternative greedy/beam weights. Report Monte Carlo confidence intervals **and model-assumption sensitivity**, since assumption uncertainty is far larger than ±2–3% sampling error.

## Limitations and reproducibility

This is a **transparent partial Magic simulator**, not a Magic rules engine or a predictor of multiplayer win rates. It explicitly supports a card subset; unmodeled cards remain in the hand and affect draw quality but are not falsely treated as castable or as automatic wins. It models first eight turns and one hypothetical removal scenario. No actual buyback infinity or Mathemagics kill is adjudicated.

Run from this directory:

```bash
python test_magnus_v16_sim_v2.py
python magnus_v16_sim_v2.py --trials 1800 --seed 20261028 --out magnus_v16_sim_v2_results.json
```

The unit tests check deck size, colored pip restrictions, generic buyback discounts, Lute and Class mana limits, Sol Ring excess mana, Izzet Signet filtering, Storm-Kiln / Harmonic triggers, Altar token sacrifice, temporary Stormsplitter tokens, and deterministic paired seeds.
