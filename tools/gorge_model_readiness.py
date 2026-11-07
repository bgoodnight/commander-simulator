"""Preflight analytic readiness on extracted Gorge hero_features.jsonl.

Read-only, standard library only. This is a quality gate, not a model fit
or a cohort approval mechanism. It never treats missing native evidence as 0.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

SCHEMA = "gorge-model-readiness-v1"
PREGAME_FEATURES = (
    "hero_seat", "opening_basic_lands", "opening_sol_ring",
    "opening_arcane_signet", "opening_mind_stone",
)
# Must never become X. These columns are outcomes, post-outcome metadata, or IDs.
FORBIDDEN_PREDICTORS = frozenset({
    "seed", "deck", "won", "status", "game_turns",
    "source_sha256", "full_native_available", "native_events",
    "native_intents", "snapshot_count", "opening_hand_observed",
    "first_snapshot_life", "first_snapshot_hand_size",
})


def audit(rows: list[dict], features: tuple[str, ...] = PREGAME_FEATURES,
          min_class: int = 20, min_groups: int = 100) -> dict:
    if not rows:
        raise ValueError("No game records")
    if len({(r.get("deck"), r.get("seed")) for r in rows}) != len(rows):
        raise ValueError("Duplicate hero deck/seed; do not silently combine cohorts")
    if set(features) & FORBIDDEN_PREDICTORS:
        raise ValueError("Outcome, provenance, or postgame variable selected as predictor")
    if len(set(r.get("deck") for r in rows)) != 1:
        raise ValueError("A one-hero dataset is required")

    statuses = Counter(r.get("status", "unknown") for r in rows)
    missing = {name:sum(r.get(name) is None for r in rows) for name in features}
    native = sum(r.get("full_native_available") is True for r in rows)
    decisive = [r for r in rows if r.get("status") == "decisive" and r.get("won") in (0,1)
                and type(r.get("won")) is int]
    complete = [r for r in decisive if all(r.get(f) is not None for f in features)]
    wins = sum(r["won"] for r in decisive)
    losses = len(decisive) - wins
    complete_wins = sum(r["won"] for r in complete)
    complete_losses = len(complete)-complete_wins
    groups = len({r.get("seed") for r in complete})
    n_unique = {f:len({r.get(f) for r in complete}) for f in features}
    constant = [f for f,n in n_unique.items() if n < 2]

    blockers = []
    if any(r.get("status") == "decisive" and r.get("won") not in (0,1) for r in rows):
        blockers.append("Some decisive records have an unknown outcome")
    if len(complete) < len(decisive):
        blockers.append("Predictors missing in some decisive games; inspect selection bias")
    if min(complete_wins,complete_losses) < min_class:
        blockers.append("Insufficient outcome support in complete-case rows")
    if groups < min_groups:
        blockers.append("Insufficient independent seed groups")
    if len(constant) == len(features):
        blockers.append("No varying predictors")
    return {
        "schema": SCHEMA, "hero": rows[0].get("deck"),
        "attempts": len(rows), "outcome_status_counts": dict(statuses),
        "native_recordings":native, "decisive":len(decisive),
        "decisive_wins": wins, "decisive_losses":losses,
        "complete_case_decisive":len(complete),
        "complete_case_wins":complete_wins,
        "complete_case_losses":complete_losses,
        "independent_seed_groups_complete":groups,
        "feature_missing_counts":missing,
        "feature_unique_values_complete":n_unique,
        "constant_features_complete":constant,
        "preflight_blockers":blockers,
        "statistical_readiness": "not_ready" if blockers else "sample_size_only_pass",
        "production_eligible":False,
        "notes":[
            "Sample-size-only pass is NOT cohort approval or proof of predictive validity.",
            "First-decision hand features require temporal verification before pregame inference.",
            "Outcome categories are mutually exclusive; draw/stall/error are never coded as losses.",
            "Grouping by seed assumes one cohort; additional R2 cohorts must carry fingerprint IDs.",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--features", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--min-class", type=int, default=20)
    p.add_argument("--min-groups", type=int, default=100)
    args = p.parse_args()
    if args.min_class < 1 or args.min_groups < 2:
        p.error("positive min-class and min-groups >= 2 required")
    rows = [json.loads(x) for x in args.features.read_text().splitlines() if x.strip()]
    report = audit(rows, min_class=args.min_class, min_groups=args.min_groups)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print(json.dumps(report,sort_keys=True))


if __name__ == "__main__":
    main()
