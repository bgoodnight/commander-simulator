# First full-panel Gorge qualification: 60 precon exposures (2026-11-05)

Source: [Actions run 42049173164](https://github.com/bgoodnight/commander-simulator/actions/runs/42049173164), artifact `gorge-precon-60-experimental-gameplay` (short retention). This experiment used the candidate panel generated from the pinned stock catalog and Scryfall Oracle enrichment, pinned Gorge/Forge card corpus, Mortarion as the hero, 40-life four-player Commander, and Gorge `bot` pilots.

## Observed, not inferred

- 60 actual attempted game records; **all 60 distinct candidate precons appeared in opponent seats** across the pods.
- 56 games completed with verified Gorge replays.
- 3 games reached the 60-turn limit without completing (seeds 186006, 186011, 186059).
- 1 Gorge engine error at seed **186047**, intent 630: `expected 1..1 choices, got 0`. Its recorded pod was `blight-curse--ecc`, `arm-for-battle--cmr`, `desert-bloom--otc`, `mortarion_current`. **Do not attribute this error to a specific card/deck without source evidence.**
- Every game remains experimental, **not eligible** for current production win rates or elastic-net models. No R2 mutation or Pages publication was attempted.

The initial workflow intentionally failed on the engine error, correctly preventing an unconditional compatibility claim. The follow-up workflow retains the source-backed failure in a structured `engine_errors` list, without silently discarding it. A green report-generation job must not be interpreted as evidence that the rules are fully supported.

## Outstanding certification gates

1. Reproduce seed 186047 with native intent/choice diagnostics to identify the missing legal-choice handling.
2. Compare each tested deck's observed signature mechanics to Oracle card text and canonical gameplay.
3. Review bot decisions and counts of materially important abilities, not only completion.
4. Decide whether 60-turn stalls reflect legitimately long games, weak pilot behavior, or missing interactions; retain denominator distinctions.
5. Repeat targeted tests following any Gorge rules/pilot change, then version the resulting eligibility metadata and approve cohorts deliberately.

All 60 decks remain staged; none promoted to the active opponent pool.

## Follow-up: source-verified ward-Blight repair and two-hero panel

The failing game was pinpointed from a native decision trace: at seed
`186047`, intent 630, Mortarion's player elected to pay Blight ward, then
Gorge created `Choose a creature to blight` with `min=1,max=1` and **zero
legal options**. This was an invalid rules-side decision, not a legal play
available to the bot.

`tools/patch_gorge_ward_blight.py` is a fail-closed overlay to the pinned
`engine/rules/ward.go`: when ward Blight has zero legal creatures, the
payment fails and the ward effect proceeds as unpaid. It makes no artificial
selection and changes no other ward payments. The same overlay is applied to
the 60-precon qualification workflow and the named Gorge precon/benchmark
workflows. Any future upstream source change requires review because the
overlay checks the exact pinned code fragment.

[Patched full-panel validation run 42052716986](https://github.com/bgoodnight/commander-simulator/actions/runs/42052716986):
**57/60 completed and replay-verified, 3 turn-limit stalls, 0 engine errors,
60/60 opponent precons encountered**. Exact seed 186047 completed on turn 36
with a verified replay; previous failure is resolved.

[Two-hero experimental run 42053608363](https://github.com/bgoodnight/commander-simulator/actions/runs/42053608363):
both `mortarion_current` and `magnus_premium` independently played 60
four-player games versus the same provisional 60-precon panel. Each had
**57 fully replay-verified completions, 3 60-turn stalls, 0 engine errors,
and exposure to all 60 opponents**. Across both: 120 attempts, 114 verified
completions, 6 capped games.

These are **experimental qualification recordings**, not current-model
observations. Completing 57 games does not yet certify pilot quality or
Oracle mechanic fidelity. Do not merge with old R2 win-rate estimates or
treat one appearance per candidate as an accurate deck power benchmark.
