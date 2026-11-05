"""Read-only exploratory diagnostics for *historical* R2 Gorge warehouse shards.

Input: downloaded warehouse/v1/**/games.parquet and optional events.parquet.
Outputs are local JSON, never uploaded to Pages or labeled current performance.
No elastic-net model is fitted: historical shards lack approved cohort lineage.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def run(root: Path) -> dict:
    import duckdb
    files = sorted(root.rglob("games.parquet"))
    if not files:
        raise ValueError("No R2 games.parquet shards found; nothing was analyzed")
    con = duckdb.connect(database=":memory:")
    paths = [str(p.resolve()) for p in files]
    con.read_parquet(paths, union_by_name=True).create_view("games_raw")
    columns = set(con.execute("DESCRIBE games_raw").df()["column_name"])
    required = {"game_id", "deck", "hero_seat", "winner_seat", "draw", "turns", "seed", "batch_id"}
    if missing := required - columns:
        raise ValueError(f"Missing warehouse columns: {sorted(missing)}")
    dup = con.execute("SELECT count(*)-count(DISTINCT game_id) FROM games_raw").fetchone()[0]
    if dup:
        raise ValueError(f"Duplicate game IDs detected ({dup}); aborting instead of double counting")
    # The legacy exporter only emitted replay-verified completed games,
    # but a Parquet row alone does not prove all eight current cohort fingerprints.
    # Therefore this is exploratory/historical ONLY.
    base = """
    FROM games_raw
    """
    outcome = con.execute("""
      SELECT deck, count(*) AS total, count(*) FILTER (WHERE draw) AS draws,
         count(*) FILTER (WHERE NOT draw AND winner_seat BETWEEN 0 AND 3) AS decisive,
         count(*) FILTER (WHERE NOT draw AND winner_seat=hero_seat) AS wins,
         count(*) FILTER (WHERE NOT draw AND winner_seat BETWEEN 0 AND 3
                           AND winner_seat<>hero_seat) AS losses,
         count(*) FILTER (WHERE NOT draw AND (winner_seat IS NULL OR winner_seat NOT BETWEEN 0 AND 3)) AS unknown,
         round(avg(turns),2) AS mean_turns
      FROM games_raw GROUP BY deck ORDER BY total DESC, deck
    """).fetchdf().to_dict(orient="records")
    seats = con.execute("""
      SELECT deck, hero_seat, count(*) AS total,
         count(*) FILTER (WHERE NOT draw AND winner_seat BETWEEN 0 AND 3) AS decisive,
         count(*) FILTER (WHERE NOT draw AND winner_seat=hero_seat) AS wins
      FROM games_raw GROUP BY 1,2 ORDER BY 1,2
    """).fetchdf().to_dict(orient="records")
    batches = con.execute("""
      SELECT batch_id, deck, count(*) AS games, count(DISTINCT seed) AS unique_seeds,
         count(*) FILTER (WHERE draw) AS draws,
         count(*) FILTER (WHERE NOT draw AND winner_seat BETWEEN 0 AND 3) AS decisive
      FROM games_raw GROUP BY 1,2 ORDER BY 1,2
    """).fetchdf().to_dict(orient="records")
    for rows in (outcome, seats):
        for row in rows:
            row["win_rate_decisive"] = (round(row["wins"]/row["decisive"], 5)
                                        if row["decisive"] else None)
    event_files = sorted(root.rglob("events.parquet"))
    events = []
    if event_files:
        con.read_parquet([str(p.resolve()) for p in event_files],
                         union_by_name=True).create_view("events_raw")
        events = con.execute("""
          SELECT kind_id, count(*) AS event_count,
                 count(DISTINCT game_id) AS games_with_event
          FROM events_raw GROUP BY kind_id ORDER BY event_count DESC LIMIT 25
        """).fetchdf().to_dict(orient="records")
    return {
        "schema": "gorge-r2-historical-exploration-v1",
        "status": "historical_diagnostics_only",
        "approved_cohort_analysis": False,
        "eligibility_note": "No current cohort approved in the reviewed registry; historical versions and experiments may be mixed.",
        "source": "local copies of private R2 warehouse/v1 Parquet shards",
        "source_shards": len(files),
        "event_shards": len(event_files),
        "game_counts_by_deck": outcome,
        "win_rate_by_hero_seat": seats,
        "batch_and_seed_inventory": batches,
        "event_type_frequency": events,
        "model_feasibility": {
            "elastic_net_fitted": False,
            "reason": "No approved current cohort and no verified observation-sidecar hand/landmark feature table",
            "requirements": [
                "approved pinned cohort with exact complete provenance",
                "verified decisive game outcomes and unique game IDs",
                "source-backed full per-game observations before each landmark",
                "grouped seed splits and outcome-blind feature engineering"
            ]
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warehouse-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.warehouse_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "game_shards": result["source_shards"],
                      "decks": len(result["game_counts_by_deck"]),
                      "report": str(args.output)}, sort_keys=True))


if __name__ == "__main__":
    main()
