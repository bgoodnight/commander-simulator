"""Deterministic, source-verified Gorge v1 Parquet shard export.

Native logs are never rewritten. Event payloads are retained exactly in JSON,
including source seq/kind, without guessing card names or turn boundaries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "gorge-warehouse-shard-v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def build_rows(folder: Path, batch_id: str, deck: str, shard: int, runs_file="runs.jsonl"):
    """Validate all sources before creating any output. No sampled-game fallback."""
    folder = Path(folder)
    if runs_file not in ("runs.jsonl", "runs-stamped.jsonl"):
        raise ValueError("Unsupported provenance-bearing runs input")
    records = [json.loads(line) for line in (folder / runs_file).read_text().splitlines()
               if line.strip()]
    if not records:
        raise ValueError("Empty Gorge shard")
    if len({row.get("seed") for row in records}) != len(records):
        raise ValueError("Duplicate Gorge seed")
    if "/" in batch_id or not batch_id or not batch_id.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Unsafe batch identifier")
    games, events = [], []
    for row in records:
        seed = row.get("seed")
        if type(seed) is not int or not row.get("finished") or not row.get("replay_verified") or row.get("error"):
            raise ValueError(f"Unverified game: {seed}")
        seat = row.get("hero_seat")
        decks = row.get("decks")
        if type(seat) is not int or seat not in range(4) or not isinstance(decks, list) or len(decks) != 4 or decks[seat] != deck:
            raise ValueError(f"Wrong hero/seat: {seed}")
        chain = row.get("replay_chain")
        if not isinstance(chain, str) or not chain:
            raise ValueError(f"Missing verified replay chain: {seed}")
        source_file = folder / "native" / f"gorge-seed-{seed}.json"
        raw = source_file.read_bytes()
        source = json.loads(raw)
        if (source.get("schema") != "gorge-native-trace-v1"
                or source.get("engine") != "gorge" or source.get("format") != "commander"
                or source.get("seed") != seed or source.get("chain") != chain
                or source.get("decks") != decks):
            raise ValueError(f"Native/source mismatch: {seed}")
        log = source.get("log") or {}
        native_events = log.get("events")
        if not isinstance(native_events, list) or not isinstance(log.get("intents"), list):
            raise ValueError(f"Missing authoritative Gorge events: {seed}")
        gid = f"{batch_id}/{deck}/{shard}/{seed}"
        previous = -1
        for event in native_events:
            seq, kind = event.get("seq"), event.get("kind")
            if type(seq) is not int or seq <= previous or type(kind) is not int or kind < 0:
                raise ValueError(f"Malformed or unordered events: {seed}")
            previous = seq
            events.append({
                "game_id": gid, "seed": seed, "chain": chain,
                "seq": seq, "kind_id": kind,
                "player": event.get("player") if type(event.get("player")) is int else None,
                "object_id": event.get("obj") if type(event.get("obj")) is int else None,
                "secret": bool(event.get("secret")),
                "event_json": canonical(event).decode("utf-8"),
            })
        raw_sha = hashlib.sha256(raw).hexdigest()
        if row.get("source_sha256") is not None and row["source_sha256"] != raw_sha:
            raise ValueError(f"Stamped native recording digest mismatch: {seed}")
        # Preserve provenance as explicit nullable fields. Older R2 shards
        # remain historical because their version fingerprints are missing.
        from tools.gorge_cohort_eligibility import IDENTITY_FIELDS
        recorded = {
            "cohort_id": row.get("cohort_id"),
            "cohort_manifest_sha256": row.get("cohort_manifest_sha256"),
            **{key: row.get(key) for key in IDENTITY_FIELDS},
        }
        games.append({
            **recorded,
            "finished": row["finished"],
            "replay_verified": row["replay_verified"],
            "error": row.get("error"),
            "game_id": gid, "batch_id": batch_id, "deck": deck, "shard": shard,
            "seed": seed, "chain": chain,
            "hero_seat": seat, "winner_seat": row.get("winner_seat"),
            "draw": bool(row.get("draw")), "turns": row.get("turns"),
            "decks_json": canonical(decks).decode("utf-8"),
            "policies_json": canonical(row.get("policies")).decode("utf-8"),
            "source_sha256": raw_sha,
            "native_event_count": len(native_events),
            "native_intent_count": len(log["intents"]),
        })
    return games, events


def export(folder: Path, out: Path, batch_id: str, deck: str, shard: int, runs_file="runs.jsonl"):
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Install pyarrow to export the Gorge warehouse") from exc
    games, events = build_rows(folder, batch_id, deck, shard, runs_file)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, rows in (("games", games), ("events", events)):
        path = out / (name + ".parquet")
        table = pa.Table.from_pylist(rows)
        pq.write_table(table, path, compression="zstd", row_group_size=10000)
        files[path.name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            "bytes": path.stat().st_size, "rows": len(rows)}
    manifest = {"schema": SCHEMA, "batch_id": batch_id, "player_deck": deck,
                "shard": shard, "games": len(games), "native_events": len(events),
                "files": files, "event_contract": "exact native Gorge event payload in event_json",
                "visibility": "private-omniscient", "recording_retention": "separate R2 native archive"}
    (out / "manifest.json").write_bytes(canonical(manifest) + b"\n")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-folder", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--deck", required=True)
    parser.add_argument("--shard", required=True, type=int)
    parser.add_argument("--runs-file", choices=("runs.jsonl", "runs-stamped.jsonl"),
                        default="runs.jsonl", help="Stamped source-backed input for eligible cohorts")
    args = parser.parse_args()
    print(json.dumps(export(args.shard_folder, args.out, args.batch_id,
                            args.deck, args.shard, args.runs_file), sort_keys=True))


if __name__ == "__main__":
    main()
