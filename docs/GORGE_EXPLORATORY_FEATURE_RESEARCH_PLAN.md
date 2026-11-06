# Exploratory Gorge feature research plan

Preserve full native evidence. Engineer broad, versioned sparse card features and only later select model predictors. Include observed hand presence, cast counts, first cast event sequence, sampled zone persistence, contextual opponent metadata, and noncard game-state measures. A row without observed evidence is not automatically zero. Keep exact event sequence separate from sampled global-turn timing; do not invent cast turns or actors. Maintain exact game/cohort IDs, deck fingerprints and provenance.

For discovery use seed-grouped nested cross validation and out-of-bag estimates (when estimator supports them), with opponent-only baseline, calibrated Brier and log-loss, and model instability checks. OOB estimates are not a null-hypothesis test and do not remove post-selection bias. Register follow-up matched-seed card-swap experiments separately, then evaluate on independent seeds and opponent assignments. Experimental cohorts are never promoted without approval.

Current first R2 sparse extractor is a prototype that materializes the per-batch JSONL in memory. Before large cohorts, switch to bounded per-game streaming and compressed partitioned Parquet; do not treat the current prototype as production-scale.
