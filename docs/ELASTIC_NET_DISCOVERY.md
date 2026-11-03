# Elastic-net discovery (replaces tree and ridge)

The feature engineer consumes *complete* JSONL observations from the next
game cohort. The statistical model does not alter simulator rules or piloting.
`python -m pip install scikit-learn` is needed only for offline discovery.

    python tools/discover_game_signals.py --source dist/observations \
      --output dist/analytics/mortarion-physical.json --landmark 0

A second run with `--landmark 6` uses only features recorded through
turn six among games still underway at that landmark. Do not pool landmark
and pregame models as if they describe the same population.

The single model family is **elastic-net logistic regression** for win by the
recorded bounded horizon. Main effects and automatically generated binary
card × opponent-type interactions are examined together. Candidate interactions
are filtered by observed support, never by outcome. After fitting, interactions
without selected constituent main effects are excluded and the same penalized
model is refit (strong-heredity *selection*, not a constrained hierarchical
penalty). No tree screening, ridge-only second fit, ordinary regression refit,
or p-values. Features are not causal effects.

Whole seeds, not individual scenario rows, are held out. Regularization is
selected in grouped inner CV; outer held-out Brier is compared with a
composition-only reference. Stability counts use bootstrap samples of seed
groups, and finding cards show support, direction, selection frequency and
conditional coefficient. Missing source observations fail closed. Insufficient
data emits a flagged report rather than a fabricated signal.

The report is a compact JSON consumer artifact, **not a second simulation**.
Older 500-game outcome batches lack per-game hands and cannot support card
discovery; do not silently repurpose the three example replays.
