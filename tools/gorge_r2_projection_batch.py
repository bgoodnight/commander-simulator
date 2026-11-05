"""Versioned batch gate for privately stored R2 warehouse shards.

Raw data are immutable. Only approved, decisive rows/events may be included.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
from tools.gorge_cohort_eligibility import validate_registry
from tools.gorge_approved_warehouse import materialize


def project(source: Path, registry_file: Path, out: Path, batch: str):
    if not re.fullmatch(r"[0-9]+-[0-9]+", batch):
        raise ValueError("Invalid batch identifier")
    source = Path(source)
    registry_file = Path(registry_file)
    raw = registry_file.read_bytes()
    registry = json.loads(raw)
    cohorts = validate_registry(registry)
    if not any(c["status"] == "current" and c.get("approved") is True
               for c in cohorts.values()):
        raise ValueError("No approved current cohorts: refuse publishing an empty view")
    manifests = sorted(source.glob("*/*/manifest.json"))
    if not manifests:
        raise ValueError("No source shards")
    report = {"schema": "gorge-r2-projection-publication-v1",
              "source_batch": batch,
              "registry_sha256": hashlib.sha256(raw).hexdigest(),
              "source_shards": [], "total_games_approved": 0,
              "total_events_approved": 0, "data_class": "current_decisive_only"}
    shards = set()
    for manifest_path in manifests:
        deck, shard = manifest_path.relative_to(source).parts[:2]
        if (deck, shard) in shards:
            raise ValueError("Duplicate source shard")
        shards.add((deck, shard))
        metadata = json.loads(manifest_path.read_text())
        if metadata.get("schema") != "gorge-warehouse-shard-v1" or metadata.get("batch_id") != batch:
            raise ValueError("Source shard manifest mismatch")
        if str(metadata.get("shard")) != shard or metadata.get("player_deck") != deck:
            raise ValueError("Source deck or shard mismatch")
        folder = manifest_path.parent
        for filename in ("games.parquet", "events.parquet"):
            info = metadata["files"][filename]
            payload = (folder / filename).read_bytes()
            if len(payload) != info["bytes"] or hashlib.sha256(payload).hexdigest() != info["sha256"]:
                raise ValueError("Source Parquet digest mismatch")
        current = out / deck / shard
        result = materialize(folder / "games.parquet", folder / "events.parquet",
                             registry_file, current)
        report["total_games_approved"] += result["games_approved"]
        report["total_events_approved"] += result["events_approved"]
        report["source_shards"].append({"deck": deck, "shard": shard, "result": result})
    if report["total_games_approved"] == 0:
        raise ValueError("No current decisive games in source batch; no R2 publish")
    (out / "publication.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--registry", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--batch", required=True)
    a = p.parse_args()
    print(json.dumps(project(a.source, a.registry, a.out, a.batch), sort_keys=True))


if __name__ == "__main__":
    main()
