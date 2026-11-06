"""Produce an attested card-insights sidecar from complete native recordings.

This is an offline, explicit operation. It requires the corrected attribution
extractor; public replay projections cannot substitute for omniscient native
event evidence. Source files are never written to a public output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from tools.gorge_cohort_eligibility import inspect
from tools.gorge_r2_full_cohort_insights import SCHEMA


def digest(raw: bytes):
    return hashlib.sha256(raw).hexdigest()


def verify_hero_attribution(features: dict, deck_entry: dict, cards: dict):
    """Reject opponent-owned spell names from every hero played-card category."""
    allowed = {name.casefold() for card in deck_entry["cards"]
               for name in [card["name"], *(cards.get(
                   card["oracle_id"], {}).get("face_names") or [])]}
    for kind in ("played", "creature", "artifact", "enchantment", "instant",
                 "spell", "land", "unplayed"):
        for item in features.get("categories", {}).get(kind, []):
            if str(item.get("name", "")).casefold() not in allowed:
                raise ValueError("Opponent or unknown card misattributed as hero: " +
                                 str(item.get("name")))


def prepare(native_source: Path, shard: Path, catalog: Path,
            registry_file: Path, out: Path):
    import pyarrow.parquet as pq

    manifest_raw = (shard / "manifest.json").read_bytes()
    games_raw = (shard / "games.parquet").read_bytes()
    ui_raw = (shard / "ui-original.v1.json").read_bytes()
    manifest = json.loads(manifest_raw)
    projection = json.loads(ui_raw)
    registry = json.loads(registry_file.read_bytes())
    expected = manifest["files"]["games.parquet"]
    if (manifest.get("schema") != "gorge-warehouse-shard-v1"
        or len(games_raw) != expected["bytes"]
        or digest(games_raw) != expected["sha256"]):
        raise ValueError("Warehouse source manifest mismatch")
    rows = pq.read_table(shard / "games.parquet").to_pylist()
    if len(rows) != expected["rows"]:
        raise ValueError("Incomplete Parquet game shard")
    approved = []
    for row in rows:
        eligible, _ = inspect(row, registry)
        if (eligible and row.get("draw") is False and
            type(row.get("winner_seat")) is int and row["winner_seat"] in range(4)):
            approved.append(row)
    if not approved:
        raise ValueError("No approved decisive games for card insights")
    deck = manifest["player_deck"]
    batch = manifest["batch_id"]
    if (projection.get("schema") != "gorge-r2-original-ui-projection-v1"
        or projection.get("deck") != deck or projection.get("source_batch") != batch
        or len(projection.get("games", [])) != len(approved)):
        raise ValueError("Missing or mismatched original UI projection")
    catalog_doc = json.loads(catalog.read_text())
    decks = [d for d in catalog_doc["decks"] if d["key"] == deck]
    if len(decks) != 1 or decks[0]["deck_sha256"] != projection["ui_deck_sha256"]:
        raise ValueError("UI catalog hash differs from approved source")
    source_rows = [json.loads(line) for line in (native_source / "runs.jsonl").read_text().splitlines()
                   if line.strip()]
    by_seed = {r["seed"]: r for r in source_rows}
    if len(by_seed) != len(source_rows):
        raise ValueError("Duplicate native source seeds")
    if set(by_seed) != {row["seed"] for row in approved}:
        raise ValueError("Native recordings must cover exactly approved games")
    native = native_source / "native"
    expected_files = {f"gorge-seed-{row['seed']}.json" for row in approved}
    if {p.name for p in native.glob("gorge-seed-*.json")} != expected_files:
        raise ValueError("Missing or unexpected native recordings")
    source_hashes = {}
    for row in approved:
        recorded = by_seed[row["seed"]]
        if (recorded.get("replay_chain") != row["chain"] or
            recorded.get("hero_seat") != row["hero_seat"] or
            recorded.get("decks", [None] * 4)[row["hero_seat"]] != deck or
            recorded.get("winner_seat") != row["winner_seat"] or
            recorded.get("finished") is not True or
            recorded.get("replay_verified") is not True or recorded.get("error")):
            raise ValueError("Native summary and approved source disagree")
        raw = (native / f"gorge-seed-{row['seed']}.json").read_bytes()
        trace = json.loads(raw)
        if (trace.get("seed") != row["seed"] or
            trace.get("chain") != row["chain"] or
            trace.get("hero_seat") != row["hero_seat"] or
            trace.get("decks") != json.loads(row["decks_json"]) or
            digest(raw) != row["source_sha256"]):
            raise ValueError("Native recording digest or identity mismatch")
        source_hashes[row["game_id"]] = digest(raw)

    with tempfile.TemporaryDirectory(prefix="gorge-native-insight-evidence-") as name:
        tmp = Path(name)
        ui_dir = tmp / "ui"
        summary = tmp / "runs.jsonl"
        pod = tmp / "pod.json"
        feature_path = tmp / "features.json"
        summary.write_text("\n".join(json.dumps(by_seed[row["seed"]]) for row in approved)+"\n")
        pod.write_text(json.dumps({"hero": deck, "deck_sha256": {
            deck: projection["ui_deck_sha256"]}}))
        files = [str(native / f"gorge-seed-{row['seed']}.json") for row in approved]
        subprocess.run([sys.executable, "-m", "tools.gorge_ui_export", *files,
                        "--include-hidden", "--out", str(ui_dir)],
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["node", "tools/gorge_card_insights_extract.cjs",
                        str(ui_dir), str(summary), str(pod), str(catalog),
                        str(feature_path)], check=True, stdout=subprocess.DEVNULL)
        features = json.loads(feature_path.read_text())
    verify_hero_attribution(features, decks[0], catalog_doc["cards"])
    if (features.get("completed_verified_games") != len(approved)
        or features.get("deck") != deck or
        features.get("deck_sha256") != projection["ui_deck_sha256"]):
        raise ValueError("Native extractor was incomplete")
    envelope = {
        "schema": SCHEMA,
        "manifest_sha256": digest(manifest_raw),
        "games_sha256": digest(games_raw),
        "ui_sha256": digest(ui_raw),
        "source_recordings": source_hashes,
        "features": features,
        "producer": "corrected_native_gorge_card_insights",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(envelope, sort_keys=True,
                              separators=(",", ":"))+"\n")
    return {"deck": deck, "approved_games": len(approved),
            "sidecar_sha256": digest(out.read_bytes())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-source", type=Path, required=True)
    parser.add_argument("--shard", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, default=Path("docs/deck-lab/decks.json"))
    parser.add_argument("--registry", type=Path,
                        default=Path("data/gorge_analytics_cohort_registry_v1.json"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.native_source, args.shard, args.catalog,
                             args.registry, args.out), sort_keys=True))


if __name__ == "__main__":
    main()
