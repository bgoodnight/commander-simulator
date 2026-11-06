# Modeling Insights: staged UI contract and analytic publication gates

**Status:** draft-only optional UI consumer in PR #227. No production Worker route or validated model report currently exists. The report is intentionally hidden when absent; existing Key Insights and Turn Reviewer remain unchanged.

## API contract (proposed, not yet implemented)

`GET /v1/ui/model-insights?deck=<deck>` returns a bounded, explicitly approved, source-derived result using the active materialized cohort pointer:

```json
{
  "schema": "gorge-r2-materialized-response-v1",
  "status": "ready",
  "deck": "mortarion_current",
  "version": "<immutable source+model report version matching the active UI cohort>",
  "report": {
    "schema": "gorge-model-insights-v1",
    "status": "validated",
    "deck": "mortarion_current",
    "cohort_version": "<same active UI cohort version>",
    "feature_schema": "features-v1",
    "validation": {
      "strategy": "grouped_held_out",
      "leakage_audit_passed": true,
      "feature_coverage_complete": true,
      "outcome_coverage_complete": true,
      "n_games": 0,
      "n_groups": 0,
      "wins": 0,
      "losses": 0,
      "brier": 0.0,
      "baseline_brier": 0.0
    },
    "features": []
  }
}
```

**The JSON is an illustrative structural schema, not data or a valid publishable report.** The test-only fixtures use synthetic numbers. A Worker may return 404 or `status: model_pending` until a verified report is materialized, and the UI hides the section.

## Analytic requirements before publishing

1. Obtain complete, actor-correct, omniscient native Gorge data through verified private R2/Worker access; compare a sample with authoritative immutable source recordings. Preserve attempted/failed/turn-capped denominators alongside decisive outcomes.
2. Create immutable `game_id=batch/deck/shard/seed`, cohort and source fingerprints, feature-source evidence, and pregame/landmark cutoff semantics. Apply seat-zero omitted-player fix; owner is not caster.
3. Use all compatible, independently seeded games for training with group-aware splits; repeated landmarks from one game stay in the same fold. Compare opponent-context-only baseline against regularized logistic elastic net and an EBM challenger, with out-of-sample predictions and proper calibration measurements.
4. Prevent future information, terminal-state leakage, inapplicable card-absence indicators, postgame card membership lookups, and censoring-derived selection bias. Do not call held-out selection frequencies causal effects.
5. Ensure source cohort version, model feature schema, outcomes, native-source digest, training code commit and report integrity hash are pinned in an **authenticated analytical report manifest**, then publish only a sanitized, reviewed report into the UI namespace.
6. An initial minimum of 100 distinct groups, 20 wins and 20 losses and complete feature/outcome coverage is **only a necessary UI visibility gate**, not sufficient for statistical validation. Require an independent statistical review for cohort independence, nested CV or independent test-set performance, calibration, stability, multiplicity and trial sensitivity.
7. Never infer that successful test fixtures or in-sample EBM examples justify ranked card effects. When insufficient data, render no modeling claims; existing descriptive Key Insights stay visible.

## Integration and UI coordination

The optional standalone model module, injected after Key Insights, listens for a version-pinned `gorge:cohort-ready` event. It refuses mismatched versions and resets when results change. It does not modify the currently staged styling, dashboard, Worker, R2 publishing, or native source pipelines. Align visual placement with the separate new staging branch before merging, and do not merge directly into production while the ongoing results work is active.

### Remaining implementation

- Produce trustworthy held-out model report(s) from a large, complete, provenance-verified source population. The existing 12+12 corrected baseline cannot supply valid rankings.
- Implement a Worker route that serves the sanitized report under the *same immutable cohort version* after strict digest and coverage verification.
- Add end-to-end staging tests: absent report, stale report, tampered report, partial coverage, supported report, deck change during fetch, and production layout.
