"""Build a complete per-deck card report from retained native recordings.

This is an offline diagnostic/export step; it neither approves nor publishes a
cohort. Named hands stay in a temporary directory and only aggregate card
statistics and source digests are written to the output report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from tools.gorge_card_insights import merge_shards


def build(source: Path, catalog: Path, deck: str, output: Path) -> dict:
    records = [json.loads(line) for line in (source / "runs.jsonl").read_text().splitlines() if line.strip()]
    if not records:
        raise ValueError("No source games")
    decks = json.loads(catalog.read_text())["decks"]
    selected = [entry for entry in decks if entry.get("key") == deck]
    if len(selected) != 1:
        raise ValueError("Deck must match exactly one catalog revision")
    sha = selected[0].get("deck_sha256")
    if not isinstance(sha, str) or len(sha) != 64:
        raise ValueError("Missing UI deck revision")
    seeds = [row.get("seed") for row in records]
    if any(type(seed) is not int for seed in seeds) or len(set(seeds)) != len(seeds):
        raise ValueError("Duplicate or invalid source seeds")
    native = source / "native"
    files = sorted(native.glob("gorge-seed-*.json"))
    if {p.name for p in files} != {f"gorge-seed-{s}.json" for s in seeds}:
        raise ValueError("Native recordings do not exactly match source games")
    authoritative = []
    digests = []
    for row in records:
        seat = row.get("hero_seat")
        if (type(seat) is not int or seat not in range(4) or
                len(row.get("decks", [])) != 4 or row["decks"][seat] != deck or
                not row.get("finished") or not row.get("replay_verified") or row.get("error")):
            raise ValueError("Unverified game or wrong player deck")
        path = native / f"gorge-seed-{row['seed']}.json"
        raw = path.read_bytes()
        trace = json.loads(raw)
        if (trace.get("seed") != row["seed"] or trace.get("chain") != row.get("replay_chain") or
                trace.get("decks") != row["decks"] or trace.get("hero_seat") != seat):
            raise ValueError("Native recording does not match summary")
        digests.append({"seed": row["seed"], "sha256": hashlib.sha256(raw).hexdigest()})
        authoritative.append({"seed": row["seed"], "chain": row.get("replay_chain"),
                              "decks": row["decks"], "player_seat": seat, "player_deck": deck})
    with tempfile.TemporaryDirectory(prefix="gorge-card-insights-") as name:
        tmp = Path(name)
        ui = tmp / "ui"
        pod = tmp / "pod.json"
        feature = tmp / "features.json"
        pod.write_text(json.dumps({"hero": deck, "deck_sha256": {deck: sha}}))
        subprocess.run([sys.executable, "-m", "tools.gorge_ui_export", *map(str, files),
                        "--include-hidden", "--out", str(ui)], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["node", "tools/gorge_card_insights_extract.cjs", str(ui),
                        str(source / "runs.jsonl"), str(pod), str(catalog), str(feature)], check=True)
        report = merge_shards([feature], authoritative)
    report["source_recordings"] = sorted(digests, key=lambda item: item["seed"])
    # The source-to-UI deck revision and cohort still need the existing
    # publication audit. A matching catalog key alone cannot prove identity.
    report["publication_eligible"] = False
    report["ui_revision_source_verified"] = False
    output.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--deck", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = build(args.source, args.catalog, args.deck, args.out)
    print(f"Built complete report for {report['total_verified_games']} games")


if __name__ == "__main__":
    main()
