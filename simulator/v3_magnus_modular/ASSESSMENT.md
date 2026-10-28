# v3 model review — October 28, 2026

## Verification of v2 architecture

The prior `magnus_v16_sim_v2.py` was monolithic. It loaded the 100-card deck and grouped individual cards using global sets `ROCK`, `CANTRIP`, `COUNTER`, `WIZARDS`, `TOKEN_ENGINES`, and `UTILITY_ENGINES`. It held a global `COST` dict. Resolving cards and spells involved several card-name branches inside `Game.cast_card`, `Game.smart_select`, and `Game.noncreature_trigger`; the pilot had hard-coded ordering in `play_engines` and `play_selection`. The previous simulation did **not** include a standalone combo table or execute buyback infinity.

Thus a deck swap *did* remove the old card from the draw pool, but the new card's abilities were absent until someone edited several different code locations.

## v3 architecture

- Deck membership (`deck_v16.json`), card abilities (`cards.json`), and combo recipes (`combos.json`) are separate, reusable data.
- The state engine dispatches generic named `event` + `op` effects for creatures, spells, and engines. A newly added card that uses an existing effect handler can work without changing play code. A card no longer in the deck can no longer be drawn. A card removed from the battlefield no longer triggers its effects.
- The mana layer accounts for colored pips, Sol Ring producing two mana with leftover floating, Signet needing one mana to activate, creature-only versus spell-only mana, physical tokens sacrificed to Altar, buyback generic discounts, and commander tax.
- Stormsplitter token **copies themselves trigger** on later casts that turn; both the original and its copies go away according to their individual token end-step instruction.
- Bounded combo exercises feed real cards into the same casting and mana-payment engine; they do not merely recognize a set of names. Combo metadata describes prerequisites and cycle economics; evaluators still require custom code for distinct mechanics.
- A single priority-based pilot and explicit Magnus policy control the sample turns.

## Two illustrated games, not aggregate performance claims

**Mana-poor seed 20261028 (rush):** starts with two lands and no useful ramp. Finds Telling Time on turn three, uses Brainstorm on turn four and Impulse on turn five, lands Magnus on turn six, then plays Voidmage Prodigy and Storm-Kiln Artist on turn seven. Without earlier ramp or token engines, the commander does not provide a substantial spell discount. The simulation creates two Spawn from assumed unblocked combat on turns seven and eight. **This highlights the limits of the deck's early mana, not evidence that it needs more token generators.**

**Seed 20261073 (one-turn delay, removal on turn 5):** selected to demonstrate a more productive cabal. Turn one Sol Ring, turn two Telling Time, turn three Impulse plus Sorcerer Class instead of Magnus, turn four Magnus, turn five Stormsplitter and Ponder, creating a temporary hasty copy. Magnus connects for a Spawn, then scripted removal destroys him at the end of turn five. A tax-inclusive seven-mana recast is available on turn six. By turns seven and eight, Storm-Kiln Artist and Archmage Emeritus establish resources; Sorcerer Class reaches level two. The deck has more engine pieces but still faces interaction and sequence choices.

This seed is **chosen for illustration**, and the goldfish assumes Magnus hits unblocked. These traces are not representative games or win rates.

## Critical limitations in descending order

1. **Card behavior coverage.** Eighteen card copies in the current 99 are still completely unmodeled beyond identity/cost, twenty partially modeled; some important Tzeentch triggers, Sigil Tracer copying, Muddle/Step Through tutors, Mathemagics/Comet Storm target choices, and Chaos Mutation's reveal mechanic are not operational. These omissions are more important than Monte Carlo sample size.
2. **Opponent and reaction model.** Only one scripted removal event. No priority windows, counters against stack targets with legal-target checks, holding mana for interaction, board wipes, or realistic opponent threat assessment. The pilot does not yet compare `play engine now` versus `reserve blue mana`.
3. **Combo planner.** Each recipe has a custom evaluator and a reproducible three-cast check. This is more meaningful than card access alone, but not a formal proof of infinity. The pilot currently checks but does not automatically initiate loops in the standard run. Copy spells, transformed Wizards, and recursion-dependent loops need new handlers.
4. **Better mana allocation.** The solver handles most early configurations, but is capped at 14 modeled mana sources and 45,000 search nodes, so resource-rich late games can fail to find valid plans. Filter lands and signet activation, life payments, floating mana across stack windows, and mana from other effects need refinements.
5. **Play planner.** Greedy ranking does not foresee a three-card turn. Implement a bounded beam search with simulated reserve-one-blue counterspell policy and state scoring on the next turn. Preserve paired shuffles for comparisons.
6. **Selection and tutors.** Selection is approximate and uses heuristic card scores. Model removal of irrelevant cards, conditional fetch shuffles, exact bottom ordering, graveyard plans, Jace's transformation, Mystic Retrieval-style effects when included, and more robust handling of library exhaustion.
7. **Metrics.** Record meaningful opportunities to spend each color, wasted mana when hands are constrained, effective spell discount, time-to-engine-plus-protection, number of spells cast after Magnus enters, and whether mana is genuinely positive in a combo. Compare models *on the same deck and seed* before comparing two decks.

## Suggested next engineering milestone

Implement a real **stack/reaction target model** and five missing card behaviors: `Step Through` Wizardcycling, `Muddle the Mixture` transmute, `Sigil Tracer` spell copying, `Chaos Mutation` creature replacement, and `Mathemagics` X-value/draws. Add scripted threat cards and the ability to reserve a blue mana for a response. Then test a short decision lookahead: cast Magnus now or deploy a Wizard and hold up a counter. Until then, treat deck optimization results as exploratory.

## Quality check

20 deterministic unit tests passed, covering swapping deck membership, swapping battlefield abilities, mana restrictions and costs, combo loops, temporary tokens, basic selection effects, and scripted spell resolution. Additional rules tests should precede large simulation runs; sample sizes are not a substitute for complete coverage.
