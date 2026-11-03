# Simulation observation capture contract — next batch

**Goal:** Preserve actual, time-indexed simulation observations so later
feature engineering and hierarchical elastic-net analysis can be performed
without rerunning games. Do not hardcode analytics features into game rules.

## Mandatory next-batch output (distinct from public UI output)

Each run produces **two separate deliverables**:

1. The existing small \`commander-modeled-outcomes-v1\` JSON for Deck Lab.
2. A complete, offline **\`commander-game-observations-v1\` JSONL sidecar**.
   There is one record per executed seed/game, not merely the first three
   example replays. Preserve all underlying recorded action and state evidence.
   Archive these sidecars as GitHub Actions artifacts; do not copy them into
   the public Pages bundle.

A sidecar record must include exact deck key/hash, seed, scenario,
three opponent roles, pilot style and archetype, provisional rules mode,
requested and completed rounds, terminal/censored outcome, mulligan and
**kept opening hand**, ordered **turn_records**, ordered **state_snapshots**,
and four-seat **life_history**. Card-zone snapshots already contain actual
card names, owner/controller and object IDs; turn records already contain
observed mana, combat, pilot decisions, events and fidelity diagnostics.
Retain **null** and genuine attribution gaps. Do not guess unknown actor,
cause, opportunity, legal alternatives, or missing ability effects.

The source runner is authoritative. This exporter does not alter its
decision-making or invent additional mechanics. Ability/zone fidelity remains
as implemented by the engine. Future richer source events should be appended
to this raw timeline with versioned provenance, not silently backfilled
into old cohorts.

## Research/feature-engineering rules

- **Pregame**: use the kept opening hand, opponent assignment and
  source configuration; do not confuse cards in deck with drawn cards.
- **Time-dependent**: derive first draw/cast, turn in hand/on battlefield,
  board/resource status, actual life changes, available legal options,
  pilot decisions, and mechanisms from *observed* event/snapshot fields.
  Where action timing or legal opportunity is not represented, mark
  **unobserved** rather than imputing it from absence of an action.
- **Landmarks**: only data through T3/T6/T10/etc. may predict outcomes
  afterward. Exclude or separately handle games already terminal at the
  landmark; never use game duration or later card appearances as predictors.
- **Effects and interactions**: construct binary/card, mechanic, resource,
  opponent and two-way interaction features in the separate analysis
  layer, not in kernel rules code. Use canonical reviewed ability identities
  and mark supported/simplified/unsupported abilities.
- **Models**: prefer a single hierarchical elastic-net logistic model with
  seed-grouped tuning, stability analysis and held-out evaluation; enforce
  main-effect hierarchy for selected interactions. The prior tree + ridge
  draft PR #53 is *not* the desired final modeling contract.
- **Avoid false independence**: repeated seeds across different opponent
  scenarios may share hands; group these during validation, and preserve
  exact deck/rules/pilot/engine versions.
- **Exploration, not causality**: model coefficients are provisional
  simulator signals. Include fidelity caveats and direct links to the
  supporting game/turn observations, including contradictory cases.

## Mandatory validation before any 500+ game run

1. Run a 2–4 seed smoke cohort with the observation flag and check the
   one-to-one correspondence of seeds, starting hands, turns, states and
   life records. Validate every record, including terminal early games.
2. Verify that the sidecar count equals the number of simulated games.
   A missing opening hand or malformed chronology must **fail the batch**,
   not become an all-zero predictor or a fabricated observation.
3. Compare outcomes and deterministic checksums for a fixed seed **with
   and without** sidecar capture. Capture must not change game behavior.
4. Check gzip/ZIP sizes and retention. Keep raw observation histories in
   Actions/release evidence, not in static UI output. Do not exceed artifact
   limits; split by deck and scenario as needed.
5. Preserve published 500-game results and do not merge active unrelated
   rules/UI branches or trigger new 500-game simulations without review.

## CLI

    python tools/build_game_outcomes.py \
      --deck mortarion_physical_final --scenario mixed \
      --seeds 3 --rounds 30 --pilot-style adaptive \
      --provisional-mode safe --examples 2 \
      --observations-output dist/observations/mortarion-mixed.jsonl \
      --output dist/outcomes/mortarion-mixed.json

The sidecar has no statistical feature matrix. The next analytics revision
consumes these observations to engineer candidate features and run the
interaction-aware elastic net.
