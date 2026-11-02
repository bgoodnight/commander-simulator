# Opening-hand card discovery: deliberately small first step

This is an exploratory *offline* tool. It does not make causal claims about
individual cards or estimate actual competitive Commander win rates.

## What is added

The authentic per-game modeled-outcome export now includes the seven card names
in the **kept opening hand**, recorded by the live game runner before actions.
This adds only a small list per game, not a full replay. Old exports remain
loadable in the UI, but lack the evidence needed for card discovery. They are
rejected by the analysis instead of treating missing cards as absent.

One binary indicator is generated for every eligible unique card name: present
in the opening hand (1) or absent (0). A card appearing twice as a basic land
still gets one flag.

The outcome is a **modeled win by the fixed requested round horizon**. A
nonwinning unresolved game counts as no win by that horizon; it is not
reclassified as a loss. All analyzed batches must agree on exact deck revision,
pilot style, provisional rules setting, archetype and round horizon.

## Two-stage exploratory procedure

1. Split by complete **simulation seed groups**. Five-scenario 500-game batches
   may use the same shuffled opening hand five times, so rows cannot be
   independently split. One quarter of distinct seeds go to validation.
2. Drop cards that are almost always present or absent in training (minimum
   eight appearances by default).
3. Fit 64 bootstrapped **depth-two classification trees** on training rows,
   sampling subsets of candidate cards at each split. Rank cards by summed
   Gini reduction and retain at most eight names.
4. Fit a ridge-penalized binary logistic regression of winning by horizon
   on selected card flags with fixed scenario and opposing-type-count controls.
   The intercept is not penalized. Report shrinkage odds ratios as **hypotheses**.
5. On unseen seed groups, compare Brier score with an otherwise identical
   **controls-only** regression. Flag whether selected cards add held-out
   predictive value. Avoid post-selection p-values.

Run after generating feature-capable batches from the branch:

    python tools/analyze_card_outcomes.py \
      --source dist/incoming-outcomes \
      --output dist/review/opening-hand-discovery.json \
      --top-k 8 --trees 64

The output is a deterministic JSON analysis artifact, **not yet a UI panel**.
Nothing in this branch alters the current 500-game batch or pushes new results
to main. It depends on draft PR #50, which adds independently sampled opponent
roles and the updated opponent-type UI. Both can remain staged.

## Deferred

Card first drawn or played by turn 3, card synergies, product terms, stepwise
selection, formal uncertainty intervals, and visual results cards need later
work. Recording "ever seen" as a predictor would be biased by game length.
Results are simulator-specific, and selected odds ratios are not inferential
effect estimates without additional selection-aware validation.
