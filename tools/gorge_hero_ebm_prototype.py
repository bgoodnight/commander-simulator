"""Extract one-hero Gorge native recordings and demonstrate an Explainable Boosting Machine.

Only descriptive diagnostics are supported on experimental/unapproved games.
Requires interpret-core for optional EBM fitting; never publishes to Pages or R2.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

SCHEMA = "gorge-hero-features-v0"
LANDS = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"}
# This list is *not* an exhaustive land classifier; use only explicit basic lands
# for basic-land features until reviewed Oracle type metadata is joined.


def extract(folder: Path, expected_deck: str) -> tuple[list[dict], dict]:
    runs_file = folder / "runs.jsonl"
    if not runs_file.is_file():
        raise ValueError("Missing runs.jsonl; source is required")
    runs = [json.loads(x) for x in runs_file.read_text().splitlines() if x.strip()]
    rows = []
    reasons = Counter()
    seen = set()
    for run in runs:
        seed = run.get("seed")
        if (type(seed) is not int or seed in seen):
            raise ValueError("Invalid or duplicated seed")
        seen.add(seed)
        hero = run.get("hero_seat")
        decks = run.get("decks")
        if (type(hero) is not int or hero not in range(4) or
            not isinstance(decks, list) or len(decks) != 4 or decks[hero] != expected_deck):
            raise ValueError(f"Invalid player/deck identity seed {seed}")
        status = ("error" if run.get("error") else
                  "turn_cap" if not run.get("finished") and run.get("stall_reason") == "turns" else
                  "unfinished" if not run.get("finished") else
                  "unverified" if not run.get("replay_verified") else
                  "draw" if run.get("draw") else
                  "decisive")
        reasons[status] += 1
        path = folder / "native" / f"gorge-seed-{seed}.json"
        row = {
            "seed": seed, "deck": expected_deck, "hero_seat": hero,
            "opponent_decks": "|".join(sorted(d for i,d in enumerate(decks) if i != hero)),
            "game_turns": run.get("turns"), "status": status,
            "won": (int(run.get("winner_seat") == hero) if status == "decisive" else None),
            "source_sha256": None, "full_native_available": path.exists(),
            "opening_hand_observed": False, "opening_basic_lands": None,
            "opening_hand_size": None, "opening_sol_ring": None,
            "opening_arcane_signet": None, "opening_mind_stone": None,
            "first_snapshot_life": None, "first_snapshot_hand_size": None,
            "native_events": None, "native_intents": None,
            "snapshot_count": None,
        }
        if path.exists():
            raw = path.read_bytes()
            native = json.loads(raw)
            if (native.get("schema") != "gorge-native-trace-v1" or
                native.get("seed") != seed or native.get("chain") != run.get("replay_chain") or
                native.get("decks") != decks):
                raise ValueError(f"Native source mismatch seed {seed}")
            row["source_sha256"] = hashlib.sha256(raw).hexdigest()
            log = native.get("log") or {}
            events, intents = log.get("events"), log.get("intents")
            if not isinstance(events, list) or not isinstance(intents, list):
                raise ValueError(f"Missing native events or intents seed {seed}")
            row["native_events"], row["native_intents"] = len(events), len(intents)
            snaps = native.get("snapshots") or []
            row["snapshot_count"] = len(snaps)
            # Earliest snapshot is a first-decision state, NOT necessarily a
            # verified kept hand *before any game actions*. Label accordingly.
            if snaps and len(snaps[0].get("players", [])) == 4:
                sp = snaps[0]["players"][hero]
                zones = sp.get("zones") or {}
                hand_ids = zones.get("hand")
                objects = {o.get("object_id"):o for o in native.get("objects", [])
                           if isinstance(o, dict)}
                if isinstance(hand_ids, list) and all(oid in objects for oid in hand_ids):
                    names = [objects[oid].get("card_name") for oid in hand_ids]
                    if all(isinstance(n, str) and n for n in names):
                        row["opening_hand_observed"] = True
                        row["opening_basic_lands"] = sum(n in LANDS for n in names)
                        row["opening_hand_size"] = len(names)
                        row["opening_sol_ring"] = int("Sol Ring" in names)
                        row["opening_arcane_signet"] = int("Arcane Signet" in names)
                        row["opening_mind_stone"] = int("Mind Stone" in names)
                row["first_snapshot_life"] = sp.get("life")
                row["first_snapshot_hand_size"] = (
                    len(hand_ids) if isinstance(hand_ids, list) else None)
        rows.append(row)
    return rows, {"source_games":len(runs), "outcome_status_counts":dict(reasons),
                  "native_recordings":sum(r["full_native_available"] for r in rows),
                  "opening_hand_observed":sum(r["opening_hand_observed"] for r in rows)}


def demo_ebm(rows: list[dict], min_rows: int = 8) -> dict:
    """Fit an explicitly noninferential model for API/output smoke testing only.

    Never use holdout performance, explanations, or feature ranks from the
    tiny demonstration to infer deck strength or recommend swaps.
    """
    cohort = [r for r in rows if r["status"] == "decisive" and r["opening_hand_observed"]]
    y = [r["won"] for r in cohort]
    result = {"model":"ExplainableBoostingClassifier",
              "status":"not_fit", "n":len(cohort), "wins":sum(y),
              "losses":len(y)-sum(y), "production_eligible":False,
              "interpretation":"Software smoke test only; no causal/predictive claims."}
    if len(cohort) < min_rows or len(set(y)) < 2:
        result["reason"] = "Insufficient complete decisive observations or only one outcome class"
        return result
    try:
        from interpret.glassbox import ExplainableBoostingClassifier
        import numpy as np
    except ImportError:
        result["reason"] = "Install interpret-core to run optional EBM demonstration"
        return result
    names = ["hero_seat", "opening_basic_lands", "opening_sol_ring",
             "opening_arcane_signet", "opening_mind_stone"]
    X = np.array([[r[k] for k in names] for r in cohort], dtype=float)
    # Purely illustrative in-sample fit. Interactions disabled due tiny sample.
    m = ExplainableBoostingClassifier(interactions=0, outer_bags=1,
        inner_bags=0, min_samples_leaf=2, max_rounds=25, validation_size=0,
        random_state=20261105)
    try:
        m.fit(X, np.array(y), feature_names=names)
        probs = m.predict_proba(X)[:,1]
    except (ValueError, RuntimeError) as exc:
        result["reason"] = f"EBM fit unavailable on this cohort: {type(exc).__name__}: {exc}"
        return result
    result.update({"status":"demo_fit_only", "feature_names":names,
                   "in_sample_probability_range":[float(probs.min()),float(probs.max())],
                   "features_used":len(names),
                   "warning":"In-sample fit on tiny experimental sample; NOT validated performance or importance."})
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--hero", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--demo-ebm", action="store_true")
    a = p.parse_args()
    rows, coverage = extract(a.source, a.hero)
    a.output.mkdir(parents=True, exist_ok=True)
    # JSONL is portable; modeled and source columns can later be partitioned
    # into Parquet without changing the extractor.
    (a.output/"hero_features.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True)+"\n" for r in rows))
    report = {"schema":SCHEMA, "hero":a.hero, "coverage":coverage,
              "source":"full native Gorge recordings where available",
              "cohort":"experimental_unapproved", "production_eligible":False,
              "feature_cautions":[
                  "First-decision snapshot is not verified pregame opening hand",
                  "Basic land indicator deliberately excludes nonbasic lands",
                  "Final outcome and game duration are never used as model features",
                  "Unavailable native recordings produce missing features, not zero",
                  "No model scores or rankings are valid at current sample size"],
              "ebm":demo_ebm(rows) if a.demo_ebm else
                    {"status":"not_requested"}}
    (a.output/"feasibility.json").write_text(json.dumps(report, indent=2,sort_keys=True)+"\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
