"""Read-only inventory of available Gorge R2 sources, without game-level exports.

Requires trusted runner credentials through the AWS CLI environment.
Never downloads events, hands, Parquet payloads, or native archives.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import re
import subprocess

BUCKET = "gorge-simulations"
PREFIXES = ("warehouse/", "native/", "results/", "archives/")
ACCOUNT_RE = re.compile(r"^[a-fA-F0-9]{32}$")


def aws(endpoint: str, *args: str) -> str:
    return subprocess.run(["aws", "--endpoint-url", endpoint, *args], check=True,
                          capture_output=True, text=True, timeout=120).stdout


def list_prefix(endpoint: str, prefix: str, max_objects: int) -> list[dict]:
    token = None
    records = []
    while True:
        args = ["s3api", "list-objects-v2", "--bucket", BUCKET,
                "--prefix", prefix, "--output", "json"]
        if token:
            args += ["--continuation-token", token]
        result = json.loads(aws(endpoint, *args))
        for obj in result.get("Contents", []):
            records.append({"key": obj["Key"], "bytes": obj["Size"]})
        if len(records) > max_objects:
            raise ValueError(f"Inventory exceeds configured object limit for {prefix}")
        if not result.get("IsTruncated"):
            break
        token = result.get("NextContinuationToken")
        if not token:
            raise ValueError("R2 truncated listing without next token")
    return records


def inventory(endpoint: str, max_objects: int = 100000) -> dict:
    rows = []
    for prefix in PREFIXES:
        rows.extend(list_prefix(endpoint, prefix, max_objects))
    by_family = {}
    for prefix in PREFIXES:
        group = [r for r in rows if r["key"].startswith(prefix)]
        by_family[prefix[:-1]] = {
            "objects": len(group), "bytes": sum(r["bytes"] for r in group)}
    warehouse = defaultdict(lambda: {"manifests": 0, "parquet_games": 0,
                                      "parquet_events": 0, "bytes": 0,
                                      "heroes": set(), "declared_games": 0,
                                      "declared_events": 0, "shards_with_counts": 0})
    errors = []
    for r in rows:
        parts = r["key"].split("/")
        if len(parts) < 3 or parts[:2] != ["warehouse", "v1"]:
            continue
        batch = parts[2]
        item = warehouse[batch]
        item["bytes"] += r["bytes"]
        if len(parts) > 3:
            item["heroes"].add(parts[3])
        name = parts[-1]
        if name == "games.parquet":
            item["parquet_games"] += 1
        if name == "events.parquet":
            item["parquet_events"] += 1
        if name != "manifest.json":
            continue
        item["manifests"] += 1
        try:
            # Download only a tiny shard manifest, not a private game record.
            raw = aws(endpoint, "s3", "cp", f"s3://{BUCKET}/{r['key']}", "-",
                      "--no-progress")
            manifest = json.loads(raw)
            if manifest.get("schema") != "gorge-warehouse-shard-v1":
                errors.append("unrecognized_manifest_schema")
                continue
            games = manifest.get("games")
            events = manifest.get("native_events")
            if type(games) is int and games >= 0:
                item["declared_games"] += games
                item["shards_with_counts"] += 1
            if type(events) is int and events >= 0:
                item["declared_events"] += events
        except (ValueError, subprocess.CalledProcessError, json.JSONDecodeError):
            errors.append("manifest_unreadable")
    batches = []
    for batch, x in sorted(warehouse.items()):
        batches.append({
            "batch_id": batch,
            "heroes": sorted(x["heroes"]),
            "manifest_count": x["manifests"],
            "games_parquet_objects": x["parquet_games"],
            "events_parquet_objects": x["parquet_events"],
            "declared_games": x["declared_games"],
            "shards_with_game_counts": x["shards_with_counts"],
            "declared_events": x["declared_events"],
            "stored_bytes": x["bytes"],
        })
    native = Counter()
    native_examples = Counter()
    for row in rows:
        key = row["key"]
        if key.startswith("native/"):
            components = key.split("/")
            family = "/".join(components[:min(4, len(components))])
            native[family] += 1
            native_examples[components[-1].split(".")[-1]] += 1
    return {
        "schema": "gorge-r2-historical-inventory-v1",
        "source": "authenticated-read-only-r2-listing-and-warehouse-manifests",
        "families": by_family,
        "warehouse_batches": batches,
        "warehouse_batch_count": len(batches),
        "warehouse_declared_games_total": sum(b["declared_games"] for b in batches),
        "warehouse_game_count_coverage": sum(b["shards_with_game_counts"] for b in batches),
        "native_prefix_object_counts": dict(sorted(native.items())),
        "native_objects_total": sum(native.values()),
        "manifest_errors": dict(Counter(errors)),
        "complete_game_count_claim": False,
        "notes": [
            "Totals are warehouse-manifest declarations, not a deduplicated unique-game count.",
            "Native objects may contain multiple games, may duplicate warehouse runs, or lack complete recordings.",
            "Inventory does not read private gameplay or determine native coverage per game.",
            "Historical GitHub Actions artifacts are not included.",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--account-id", required=True)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--max-objects-per-prefix", type=int, default=100000)
    a = p.parse_args()
    if not ACCOUNT_RE.fullmatch(a.account_id):
        p.error("Invalid R2 account ID")
    if a.max_objects_per_prefix < 1:
        p.error("Positive object cap required")
    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("AWS_SECRET_ACCESS_KEY"):
        p.error("R2 access credentials unavailable")
    result = inventory(f"https://{a.account_id}.r2.cloudflarestorage.com",
                       a.max_objects_per_prefix)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "warehouse_batches": result["warehouse_batch_count"],
        "declared_games": result["warehouse_declared_games_total"],
        "native_objects": result["native_objects_total"],
        "families": result["families"], "manifest_errors": result["manifest_errors"]
    }, sort_keys=True))


if __name__ == "__main__":
    main()
