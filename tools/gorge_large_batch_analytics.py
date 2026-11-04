"""Assemble a 2,000-game Gorge cohort with sampled source-backed replays.

Input shards contain exact Gorge summaries for every game and native traces
only for selected replays. Never fabricate card actions or turn-level events
for games without a retained native trace.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from tools.commander_deck_library import load_library, matchup_annotations, validate_pod
from tools.gorge_results_pipeline import project_batch, canonical_bytes

PLAYERS = ("mortarion_current", "magnus_budget", "necron_dynasties", "wretched_ranks")
BASE_SEED = 10000
GAMES_EACH = 500
SHARDS = 5
SHARD_SIZE = 100
SEEDS_PER_SHARD = 1000
SEEDS_PER_DECK = SHARDS * SEEDS_PER_SHARD
MAX_ATTEMPTS = 500
SAMPLED_PER_SHARD = 2


def assemble(root: Path, destination: Path):
    library = load_library()
    rows = {}
    sampled = []
    pod_dir = destination.parent / "gorge-validated-pods"
    native_dir = destination.parent / "gorge-sampled-native"
    pod_dir.mkdir(parents=True, exist_ok=True)
    native_dir.mkdir(parents=True, exist_ok=True)
    for idx, hero in enumerate(PLAYERS):
        for shard in range(SHARDS):
            folder = root / hero / str(shard)
            pod_path = folder / "pod.json"
            pod = json.loads(pod_path.read_text())
            if pod.get("hero") != hero:
                raise ValueError(f"Wrong hero in {pod_path}")
            validate_pod(library, hero, pod["opponent_pool"])
            # Each player has an immutable validated deck-file hash dictionary.
            target_pod = pod_dir / f"{hero}-pod.json"
            if target_pod.exists():
                if json.loads(target_pod.read_text()) != pod:
                    raise ValueError(f"Deck version changed mid-cohort: {hero}")
            else:
                shutil.copy2(pod_path, target_pod)
            records = [json.loads(line) for line in (folder / "runs.jsonl").read_text().splitlines()
                       if line.strip()]
            if len(records) != SHARD_SIZE:
                raise ValueError(f"Partial shard: {hero}/{shard}")
            seed_start = BASE_SEED + idx*SEEDS_PER_DECK + shard*SEEDS_PER_SHARD
            last_seed = seed_start - 1
            for offset, row in enumerate(records):
                seed = row.get("seed")
                if (type(seed) is not int or seed <= last_seed or
                        seed < seed_start or seed >= seed_start + MAX_ATTEMPTS or
                        seed in rows):
                    raise ValueError(f"Duplicate or unexpected seed {seed}")
                last_seed = seed
                if (not row.get("finished") or not row.get("replay_verified") or
                        row.get("error") or row.get("draw") not in (True, False)):
                    raise ValueError(f"Unverified or unfinished Gorge game {seed}")
                if not isinstance(row.get("decks"), list) or len(row["decks"]) != 4:
                    raise ValueError(f"Invalid pod in Gorge game {seed}")
                seat = row.get("hero_seat")
                decks = row["decks"]
                if (type(seat) is not int or seat not in range(4) or
                        decks[seat] != hero or len(set(decks)) != 4 or
                        any(x not in pod["opponent_pool"] for i,x in enumerate(decks) if i != seat)):
                    raise ValueError(f"Player/precon assignment failed: {seed}")
                if not isinstance(row.get("replay_chain"), str) or not row["replay_chain"]:
                    raise ValueError(f"Missing verified Gorge chain {seed}")
                if row["draw"]:
                    if row.get("winner_seat") is not None:
                        raise ValueError(f"Draw marked with winner {seed}")
                elif row.get("winner_seat") not in range(4):
                    raise ValueError(f"Missing winner {seed}")
                rows[seed] = (row, pod)
                if offset < SAMPLED_PER_SHARD:
                    src = folder / "native" / f"gorge-seed-{seed}.json"
                    if not src.is_file():
                        raise ValueError(f"Missing sampled native recording {seed}")
                    shutil.copy2(src, native_dir / src.name)
                    sampled.append(row)
    if len(rows) != len(PLAYERS)*GAMES_EACH:
        raise ValueError(f"Expected 2,000 verified outcomes, got {len(rows)}")
    sampled_path = destination.parent / "gorge-retained-summaries.jsonl"
    sampled_path.write_text("".join(json.dumps(row, separators=(",", ":"))+"\n"
                                    for row in sampled))
    report = project_batch(native_dir=native_dir, summaries=sampled_path,
                           out=destination, include_hidden=True,
                           pod_dir=pod_dir, max_replays=len(sampled))
    if report["catalog_games"] != 40:
        raise ValueError("Unexpected replay retention count")
    analytics = json.loads((destination / "analytics.json").read_text())
    details = {r["seed"]:r for r in analytics["games"]}
    archived_at = datetime.now(timezone.utc).isoformat()
    all_rows = []
    for seed in sorted(rows):
        row, pod = rows[seed]
        seat = row["hero_seat"]
        hero = row["decks"][seat]
        if seed in details:
            enriched = details[seed]
            enriched["player_deck"] = hero
            enriched["detailed_replay_retained"] = True
        else:
            hashes = pod["deck_sha256"]
            annotated = matchup_annotations(library, row["decks"], hero=hero)
            enriched = {
                "seed": seed, "chain": row["replay_chain"],
                "decks": row["decks"], "policies": row["policies"],
                "player_seat": seat, "player_deck": hero,
                "winner_seat": row.get("winner_seat"), "draw": bool(row["draw"]),
                "finished": True, "replay_verified": True,
                "turns": row.get("turns"),
                "seat_metadata": [{**a, "seat": i, "deck_sha256": hashes[name]}
                                  for i,(name,a) in enumerate(zip(row["decks"],annotated))],
                "metadata_version": library["metadata_version"],
                "detailed_replay_retained": False,
                "detail_unavailable_reason": "Native trace intentionally not retained; verified outcome only",
            }
        all_rows.append(enriched)
    analytics["games"] = all_rows
    analytics["description"] = (
        "Every outcome and player seat is source-verified. Detailed turn, action, "
        "card and state data are available only for the retained sampled replays."
    )
    (destination / "analytics.json").write_bytes(canonical_bytes(analytics))
    catalog = json.loads((destination / "manifest.json").read_text())
    catalog["catalog_version"] = 5
    catalog["cohort_description"] = "500 Gorge games per player deck, sampled replays"
    catalog["cohort_recorded_at"] = archived_at
    catalog["total_verified_games"] = len(rows)
    catalog["detailed_replays"] = len(sampled)
    catalog["replay_retention"] = {"per_player": 10, "total": len(sampled)}
    for entry in catalog["games"]:
        # This time reflects batch processing, not an invented game-start timestamp.
        entry["simulated_at"] = archived_at
    (destination / "manifest.json").write_bytes(canonical_bytes(catalog))
    return {"verified": len(rows), "replays": len(sampled),
            "players": {hero: sum(x["player_deck"] == hero for x in all_rows)
                        for hero in PLAYERS}}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--shards", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    print(json.dumps(assemble(args.shards, args.out), sort_keys=True))


if __name__ == "__main__":
    main()
