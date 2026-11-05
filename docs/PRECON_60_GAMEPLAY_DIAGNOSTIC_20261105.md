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
