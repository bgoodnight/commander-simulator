"""Build immutable, cohort-complete public Results from verified R2 source shards.

Input layout: <source>/<batch>/<deck>/<shard>/{manifest.json,games.parquet,ui-original.v1.json}
No R2 writes. Publishing is a separate, manifest-last workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from tools.gorge_cohort_eligibility import inspect, fingerprint, validate_registry

SCHEMA = "gorge-r2-materialized-results-v1"
FORBIDDEN = {"event_json", "intents", "log", "objects", "object_identity",
             "secret", "native_events", "source_object_id", "library", "hidden_cards"}
HANDS = {"hand", "opening_hand", "opponent_hands", "opening_hands_by_seat"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(data: bytes):
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical(value) + b"\n"
    path.write_bytes(payload)
    return digest(payload)


def safe_run(value):
    if not isinstance(value, dict) or set(value) - {
        "seed", "completed_rounds", "opening_board_states", "opening_hand",
        "opening_hands_by_seat", "opening_hand_count", "mulligan",
        "ui_observations", "life_history", "opponent_decks", "gorge_source", "outcome"
    }:
        raise ValueError("Invalid original UI run")
    def visit(obj):
        if isinstance(obj, list):
            for item in obj: visit(item)
        elif isinstance(obj, dict):
            for key, item in obj.items():
                if key in FORBIDDEN or (key in HANDS and item is not None):
                    raise ValueError("Private source value in UI projection")
                visit(item)
    visit(value)


def project(source: Path, registry_path: Path, output: Path):
    import pyarrow.parquet as pq

    registry_bytes = registry_path.read_bytes()
    registry = json.loads(registry_bytes)
    cohorts = validate_registry(registry)
    if not any(c["status"] == "current" and c.get("approved") is True
               for c in cohorts.values()):
        raise ValueError("No approved current cohorts")
    manifests = sorted(source.glob("*/*/*/manifest.json"))
    if not manifests:
        raise ValueError("No source shards")
    by_deck = defaultdict(list)
    projections = defaultdict(dict)
    source_refs = []
    seen = set()
    for manifest_path in manifests:
        batch, deck, shard = manifest_path.relative_to(source).parts[:3]
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
        if (manifest.get("schema") != "gorge-warehouse-shard-v1"
            or manifest.get("batch_id") != batch
            or manifest.get("player_deck") != deck
            or str(manifest.get("shard")) != shard):
            raise ValueError("Mismatched source manifest")
        games_path = manifest_path.parent / "games.parquet"
        raw = games_path.read_bytes()
        info = manifest["files"]["games.parquet"]
        if len(raw) != info["bytes"] or digest(raw) != info["sha256"]:
            raise ValueError("Unverified Parquet source bytes")
        rows = pq.read_table(games_path).to_pylist()
        if len(rows) != info["rows"]:
            raise ValueError("Parquet row mismatch")
        approved = []
        for row in rows:
            ok, _ = inspect(row, registry)
            if not ok:
                continue
            if (row.get("draw") is not False or type(row.get("hero_seat")) is not int
                or type(row.get("winner_seat")) is not int
                or row["hero_seat"] not in range(4)
                or row["winner_seat"] not in range(4)):
                continue
            gid = row.get("game_id")
            if not isinstance(gid, str) or gid in seen:
                raise ValueError("Duplicate/missing approved game ID")
            seen.add(gid)
            pod = json.loads(row["decks_json"])
            if (len(pod) != 4 or pod[row["hero_seat"]] != deck
                or len(set(pod)) != 4):
                raise ValueError("Invalid source pod")
            approved.append(row)
        if not approved:
            continue
        projection_path = manifest_path.parent / "ui-original.v1.json"
        if not projection_path.is_file():
            raise ValueError("Missing approved shard replay projection")
        projection_bytes = projection_path.read_bytes()
        projection = json.loads(projection_bytes)
        if (projection.get("schema") != "gorge-r2-original-ui-projection-v1"
            or projection.get("deck") != deck
            or projection.get("source_batch") != batch
            or str(projection.get("shard")) != shard
            or len(projection.get("games", [])) != len(approved)):
            raise ValueError("Partial or invalid source projection")
        ui_sha = projection.get("ui_deck_sha256")
        native_sha = projection.get("source_deck_sha256")
        if not isinstance(ui_sha, str) or len(ui_sha) != 64:
            raise ValueError("Missing UI deck hash")
        indexed = {row["game_id"]: row for row in approved}
        for row in approved:
            if row["player_deck_sha256"] != native_sha:
                raise ValueError("Mixed native deck revision")
        for item in projection["games"]:
            gid = item.get("game_id")
            row = indexed.get(gid)
            if (not row or gid in projections[deck]
                or item.get("source_sha256") != row["source_sha256"]
                or item.get("chain") != row["chain"]):
                raise ValueError("Projection differs from source")
            run = item["run"]
            safe_run(run)
            if (run.get("seed") != row["seed"]
                or run.get("gorge_source", {}).get("chain") != row["chain"]
                or run.get("gorge_source", {}).get("visibility") != "public_events_only"
                or run.get("gorge_source", {}).get("synthetic_simulation_only") is not False
                or run.get("outcome", {}).get("complete") is not True
                or run.get("outcome", {}).get("status") !=
                   ("win" if row["hero_seat"] == row["winner_seat"] else "loss")
                or run.get("outcome", {}).get("winner_seat") !=
                   (row["winner_seat"] - row["hero_seat"]) % 4):
                raise ValueError("Invalid projected game outcome")
            projections[deck][gid] = {"run": run, "ui_sha": ui_sha}
        by_deck[deck].extend(approved)
        source_refs.append({"batch": batch, "deck": deck, "shard": shard,
                            "manifest_sha256": digest(manifest_bytes),
                            "games_sha256": digest(raw),
                            "ui_sha256": digest(projection_bytes),
                            "approved_games": len(approved)})

    if not by_deck:
        raise ValueError("No approved decisive games")
    basis = {"registry_sha256": digest(registry_bytes), "source_shards": source_refs}
    version = digest(canonical(basis))
    root = output / "versions" / version
    decks = {}
    for deck, rows in sorted(by_deck.items()):
        rows.sort(key=lambda r: r["game_id"])
        revisions = {projections[deck][r["game_id"]]["ui_sha"] for r in rows}
        fingerprints = {fingerprint(cohorts[r["cohort_id"]]) for r in rows}
        cohort_ids = sorted({r["cohort_id"] for r in rows})
        if len(revisions) != 1 or len(fingerprints) != 1:
            raise ValueError("Mixed UI revision or cohort in one deck")
        wins = sum(r["hero_seat"] == r["winner_seat"] for r in rows)
        turns = sorted(r["turns"] for r in rows)
        opponent_counts = defaultdict(lambda: {"n": 0, "wins": 0, "losses": 0})
        for row in rows:
            for name in json.loads(row["decks_json"]):
                if name == deck:
                    continue
                tally = opponent_counts[name]
                tally["n"] += 1
                tally["wins" if row["hero_seat"] == row["winner_seat"] else "losses"] += 1
        n = len(rows)
        summary = {
            "schema": "gorge-r2-live-summary-v1", "source": "r2-materialized-verified",
            "population": "approved_current_decisive_only", "deck": deck,
            "status": "ready", "n": n, "wins": wins, "losses": n - wins,
            "win_rate": wins / n, "baseline": .25,
            "median_game_turns": (turns[(n - 1) // 2] + turns[n // 2]) / 2,
            "game_turn_histogram": [{"turn": k, "games": v}
                                    for k, v in sorted(Counter(turns).items())],
            "groups": {"opponents": sorted(
                [{"name": name, **count, "win_rate": count["wins"] / count["n"]}
                 for name, count in opponent_counts.items()],
                key=lambda v: (-v["n"], v["name"]))},
            "regressions": {"status": "not_precomputed"},
            "disclaimer": "All explicitly approved current decisive games; no inferred card effects.",
            "cohort_version": version,
        }
        deck_root = root / deck
        summary_hash = write_json(deck_root / "summary.json", summary)
        pages = []
        for start in range(0, n, 25):
            selected = rows[start:start + 25]
            runs = [projections[deck][r["game_id"]]["run"] for r in selected]
            rounds = max(r["completed_rounds"] for r in runs)
            batch = {
                "format": "commander-gorge-outcomes-v1", "schema_version": 1,
                "engine": "gorge", "deck_key": deck,
                "deck_sha256": next(iter(revisions)),
                "scenario": "four_real_commander_decks", "pilot_style": "gorge_bot",
                "provisional_mode": "not_applicable",
                "opponent_fidelity": "gorge_native_full_100_card_decks",
                "outcomes_are_competitive_win_rates": False,
                "requested_rounds": rounds,
                "runs": [{**run, "outcome": {**run["outcome"], "requested_rounds": rounds}}
                         for run in runs], "example_replays": []
            }
            page_no = start // 25
            rel = f"pages/{page_no:06d}.json"
            checksum = write_json(deck_root / rel, {
                "schema": "gorge-r2-materialized-page-v1",
                "deck": deck, "version": version, "page": page_no,
                "total": n, "has_more": start + len(selected) < n,
                "next_cursor": str(page_no + 1) if start + len(selected) < n else None,
                "game_ids": [r["game_id"] for r in selected], "batch": batch
            })
            pages.append({"path": rel, "sha256": checksum, "count": len(selected)})
        decks[deck] = {
            "n": n, "wins": wins, "losses": n - wins,
            "ui_deck_sha256": next(iter(revisions)),
            "cohort_id": cohort_ids[0], "cohort_fingerprint": next(iter(fingerprints)),
            "summary": {"path": "summary.json", "sha256": summary_hash},
            "pages": pages
        }
    manifest = {"schema": SCHEMA, "version": version, "registry_sha256": digest(registry_bytes),
                "decks": decks, "source_shards": source_refs}
    manifest_hash = write_json(root / "manifest.json", manifest)
    pointer = {"schema": "gorge-r2-results-current-v1", "version": version,
               "manifest_sha256": manifest_hash}
    write_json(output / "current.json", pointer)
    return {"version": version, "decks": {k: v["n"] for k, v in decks.items()},
            "source_shards": len(source_refs)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(project(args.source, args.registry, args.out), sort_keys=True))


if __name__ == "__main__":
    main()
