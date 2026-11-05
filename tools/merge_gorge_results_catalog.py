"""Merge validated Gorge UI publications without dropping prior games.

Publishing is separate from simulations and native conversion. This merger
accepts only sanitized replay/analytics data and rejects seed collisions.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

from tools.gorge_results_pipeline import (
    SCHEMA, canonical_bytes, public_replay_is_safe, validate_existing,
)


def merge_publication(source, destination):
    source, destination = Path(source), Path(destination)
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    analytics = json.loads((source / "analytics.json").read_text(encoding="utf-8"))
    if (manifest.get("schema") != SCHEMA or
            manifest.get("visibility") != "omniscient" or
            manifest.get("synthetic_simulation_only") is not True or
            manifest.get("analytics_file") != "analytics.json" or
            analytics.get("schema") != "gorge-batch-analytics-v1" or
            not isinstance(analytics.get("games"), list)):
        raise ValueError("Invalid Gorge public publication contract")
    files = {"manifest.json", "analytics.json"}
    records = {}
    for entry in manifest.get("games", []):
        filename = entry.get("file", "")
        if not re.fullmatch(r"gorge-seed-[0-9]+\.ui\.json", filename):
            raise ValueError("Unsafe Gorge public replay file name")
        if filename in records:
            raise ValueError("Duplicate replay file")
        path = source / filename
        raw = path.read_bytes()
        if ("ui_sha256" in entry and
                hashlib.sha256(raw).hexdigest() != entry["ui_sha256"]):
            raise ValueError("Replay checksum mismatch")
        if not public_replay_is_safe(json.loads(raw), entry):
            raise ValueError("Invalid or misattributed public replay")
        records[filename] = entry
        files.add(filename)
    card_file = manifest.get("card_insights_file")
    card_insights = None
    if card_file is not None:
        if card_file != "card-insights.json":
            raise ValueError("Unexpected card insights file")
        from tools.gorge_card_insights import SCHEMA as CARD_SCHEMA
        card_insights = json.loads((source / card_file).read_text(encoding="utf-8"))
        if (card_insights.get("schema") != CARD_SCHEMA
                or card_insights.get("total_verified_games") != len(analytics["games"])
                or not isinstance(card_insights.get("decks"), dict)
                or sum(d.get("verified_games", 0) for d in
                       card_insights["decks"].values()) != len(analytics["games"])
                or any(d.get("observed_games") != d.get("verified_games")
                       for d in card_insights["decks"].values())):
            raise ValueError("Full card-insights cohort is incomplete")
        files.add(card_file)
    if {p.name for p in source.iterdir()} != files:
        raise ValueError("Non-allowlisted files in publication artifact")
    if card_insights is not None:
        # A complete source-backed cohort supersedes historical outcome-only
        # results. Old snapshots live in the dedicated archive branch, not
        # in the active statistics denominator.
        old_records, old_analytics = {}, {}
    else:
        old_records, old_analytics = validate_existing(destination)
    combined = dict(old_records)
    for filename, entry in records.items():
        prior = old_records.get(filename)
        if prior and (prior["seed"] != entry["seed"] or
                      prior["chain"] != entry["chain"] or
                      prior["decks"] != entry["decks"]):
            raise ValueError("Existing seed belongs to a different source game")
        combined[filename] = entry
    seeds = [entry["seed"] for entry in combined.values()]
    if len(set(seeds)) != len(seeds):
        raise ValueError("Duplicate seed across publication batches")
    batch = dict(old_analytics)
    for row in analytics["games"]:
        seed = row.get("seed")
        if type(seed) is not int or not row.get("replay_verified") or (
                "log" in row or "objects" in row):
            raise ValueError("Unsafe analytics game record")
        prior = batch.get(seed)
        if prior and prior.get("chain") != row.get("chain"):
            raise ValueError("Analytics seed collision")
        batch[seed] = row
    if len(combined) > 500:
        raise ValueError("Replay catalog exceeds safe static hosting limit")
    destination.mkdir(parents=True, exist_ok=True)
    if card_insights is not None:
        for old in destination.glob("gorge-seed-*.ui.json"):
            if old.name not in records:
                old.unlink()
    for filename in records:
        shutil.copyfile(source / filename, destination / filename)
    output_manifest = {
        "schema": SCHEMA,
        "catalog_version": 2,
        "visibility": "omniscient",
        "synthetic_simulation_only": True,
        "converter_version": manifest.get("converter_version"),
        "analytics_file": "analytics.json",
        **({"card_insights_file": "card-insights.json"} if card_insights else {}),
        "games": sorted(combined.values(), key=lambda r: r["seed"]),
    }
    output_analytics = {
        "schema": "gorge-batch-analytics-v1",
        "description": "Verified source metrics; replay files retained selectively",
        "games": [batch[seed] for seed in sorted(batch)],
    }
    (destination / "manifest.json").write_bytes(canonical_bytes(output_manifest))
    (destination / "analytics.json").write_bytes(canonical_bytes(output_analytics))
    if card_insights is not None:
        if len(batch) != card_insights["total_verified_games"]:
            raise ValueError("Card features cannot be mixed with another cohort")
        (destination / "card-insights.json").write_bytes(canonical_bytes(card_insights))
    return {"replays": len(combined), "analytics_games": len(batch),
            "new_or_updated": len(records)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(merge_publication(args.source, args.destination)))


if __name__ == "__main__":
    main()
