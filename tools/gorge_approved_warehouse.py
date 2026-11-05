"""Create a *separate* current-only warehouse materialization for analytics.

Never rewrite or remove original private R2 shards. Source games are screened
before events can join, so archived game actions cannot enter active features.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from tools.gorge_cohort_eligibility import eligible_partition, validate_registry


def partition_warehouse(games, events, registry):
    approved, excluded = eligible_partition(games, registry)
    ids = {game["game_id"] for game in approved}
    selected_events = [event for event in events if event.get("game_id") in ids]
    return approved, selected_events, excluded


def materialize(games_path: Path, events_path: Path, registry_path: Path, out: Path):
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("pyarrow required for protected warehouse projection") from exc
    registry = json.loads(registry_path.read_text())
    validate_registry(registry)
    game_table = pq.read_table(games_path)
    event_table = pq.read_table(events_path)
    game_rows = game_table.to_pylist()
    event_rows = event_table.to_pylist()
    approved, events, excluded = partition_warehouse(game_rows, event_rows, registry)
    approved_ids = {game["game_id"] for game in approved}
    if len(approved_ids) != len(approved):
        raise ValueError("Duplicate approved game")
    # Fail closed on any inconsistent event-to-game relationship.
    source_ids = {row.get("game_id") for row in game_rows}
    if any(event.get("game_id") not in source_ids for event in event_rows):
        raise ValueError("Orphaned event in source shard")
    out.mkdir(parents=True, exist_ok=True)
    mask = pa.array([r.get("game_id") in approved_ids for r in game_rows], type=pa.bool_())
    event_mask = pa.array([r.get("game_id") in approved_ids for r in event_rows], type=pa.bool_())
    pq.write_table(game_table.filter(mask), out / "games.parquet", compression="zstd")
    pq.write_table(event_table.filter(event_mask), out / "events.parquet", compression="zstd")
    result = {
        "schema": "gorge-approved-warehouse-projection-v1",
        "games_approved": len(approved), "games_excluded": len(excluded),
        "events_approved": len(events),
        "selection": "explicitly_approved_current_only",
        "exclusion_counts": {},
    }
    for row in excluded:
        reason = row["reason"]
        result["exclusion_counts"][reason] = result["exclusion_counts"].get(reason, 0) + 1
    (out / "eligibility-report.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--games", type=Path, required=True)
    p.add_argument("--events", type=Path, required=True)
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(materialize(a.games, a.events, a.registry, a.out), sort_keys=True))


if __name__ == "__main__":
    main()
