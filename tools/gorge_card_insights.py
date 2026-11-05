"""Merge complete verified Gorge card-feature shards into UI-ready rankings.

The native recorder is authoritative. These statistics are computed from
each verified game's source events and turn-entry snapshots BEFORE retaining
only selected replay files. No missing games can enter the denominator.
"""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
from statistics import median

SCHEMA = "gorge-card-insights-v1"
KINDS = ("played", "creature", "instant", "spell", "artifact", "enchantment",
         "land", "seen", "seenCreature", "unplayed", "activated", "triggered",
         "removal", "creatureKills", "damage", "longest", "finisher",
         "tutorFound", "tutorUsed")
EVENT_KINDS = {"removal", "creatureKills", "damage", "tutorFound", "tutorUsed"}
PRESENCE_KINDS = {"seen", "seenCreature", "unplayed"}


def merge_shards(paths, authoritative_games):
    """Require one feature row for every verified source game, exactly once."""
    rows = {r["seed"]: r for r in authoritative_games}
    if len(rows) != len(authoritative_games):
        raise ValueError("Duplicate authoritative game seed")
    feature_seeds = set()
    decks = defaultdict(lambda: {"seed_chains": {}, "shards": [], "cards": {
        kind: {} for kind in KINDS}, "confirmed_tutors": 0, "deck_sha256": None})
    for filename in paths:
        shard = json.loads(Path(filename).read_text(encoding="utf-8"))
        deck = shard.get("deck")
        if shard.get("schema") != "gorge-card-insights-shard-v1" or not isinstance(deck, str):
            raise ValueError(f"Invalid feature shard {filename}")
        pairs = shard.get("seed_chains")
        if not isinstance(pairs, list) or len(pairs) != shard.get("completed_verified_games"):
            raise ValueError(f"Incomplete source feature shard {filename}")
        if len({s for s, _ in pairs}) != len(pairs):
            raise ValueError("Duplicate game seed within card features")
        for seed, chain in pairs:
            row = rows.get(seed)
            if seed in feature_seeds or row is None or row.get("chain") != chain or (
                row.get("player_deck", row["decks"][row["player_seat"]]) != deck):
                raise ValueError(f"Card features misattributed or unverified: {seed}")
            feature_seeds.add(seed)
        group = decks[deck]
        previous = group["deck_sha256"]
        sha = shard.get("deck_sha256")
        if not isinstance(sha, str) or len(sha) != 64 or (
                previous is not None and previous != sha):
            raise ValueError("Different player deck revisions in one feature cohort")
        group["deck_sha256"] = sha
        group["shards"].append(set(s for s, _ in pairs))
        group["seed_chains"].update(dict(pairs))
        group["confirmed_tutors"] += shard.get("confirmed_tutors", 0)
        categories = shard.get("categories")
        if not isinstance(categories, dict) or set(categories) != set(KINDS):
            raise ValueError("Missing measured insight category")
        for kind in KINDS:
            for item in categories[kind]:
                name = item.get("name")
                if not isinstance(name, str) or not name.strip():
                    raise ValueError("Unknown card identity in source features")
                cards = group["cards"][kind]
                stats = cards.setdefault(name, {"counts": {}, "seen": set(),
                    "durations": [], "timesPlayed": 0, "events": []})
                for seed, count in item.get("counts", []):
                    if seed not in group["seed_chains"] or seed in stats["counts"] or (
                            not isinstance(count, (int, float)) or count < 0):
                        raise ValueError("Invalid per-game feature count")
                    stats["counts"][seed] = count
                for seed in item.get("seen", []):
                    if seed not in group["seed_chains"]:
                        raise ValueError("Card seen in the wrong game")
                    stats["seen"].add(seed)
                duration = item.get("durations", [])
                if not isinstance(duration, list) or any(
                        not isinstance(x, (int, float)) or x < 0 for x in duration):
                    raise ValueError("Invalid holding-time observation")
                stats["durations"].extend(duration)
                stats["timesPlayed"] += item.get("timesPlayed", 0)
                for seed, turn in item.get("events", []):
                    if seed not in group["seed_chains"] or type(turn) is not int:
                        raise ValueError("Unattributed card action")
                    stats["events"].append([seed, turn])
    if feature_seeds != set(rows):
        raise ValueError(f"Card feature coverage incomplete: {len(feature_seeds)}/{len(rows)}")

    payload = {"schema": SCHEMA, "total_verified_games": len(rows),
               "source": "native Gorge events and explicitly omniscient turn-entry snapshots",
               "decks": {}}
    for deck, group in sorted(decks.items()):
        n = len(group["seed_chains"])
        rankings = {}
        for kind, items in group["cards"].items():
            ranked = []
            for name, item in items.items():
                counts = item["counts"]
                durations = item["durations"]
                total = sum(counts.values())
                games = sum(c > 0 for c in counts.values())
                avg = (sum(durations) / len(durations)) if kind == "longest" and durations else total/n
                if kind == "longest":
                    score = avg
                elif kind in PRESENCE_KINDS:
                    score = len(item["seen"])
                elif kind in ("activated", "triggered"):
                    score = total / n
                elif kind in EVENT_KINDS:
                    score = total
                else:
                    score = games
                if score <= 0:
                    continue
                full_counts = [counts.get(seed, 0) for seed in group["seed_chains"]]
                ranked.append({
                    "name": name, "score": round(score, 7),
                    "average": round(avg, 7),
                    "median": median(durations if kind == "longest" else full_counts),
                    "heldMedian": median(durations) if durations else None,
                    "timesPlayed": item["timesPlayed"],
                    "games": games, "eventCount": total,
                    "seenGames": len(item["seen"]),
                    "turns": [turn for _, turn in item["events"]],
                    "exampleEvents": item["events"][:60],
                    "exampleSeenSeeds": sorted(item["seen"])[:60]
                })
            ranked.sort(key=lambda r: (-r["score"], -r["average"],
                                      -r["games"], r["name"]))
            rankings[kind] = ranked
        payload["decks"][deck] = {
            "deck_sha256": group["deck_sha256"],
            "verified_games": n, "observed_games": n,
            "confirmed_tutors": group["confirmed_tutors"],
            "categories": rankings,
            "coverage": {"numerator": n, "denominator": n,
                         "level": "full-cohort", "missing": 0}
        }
    return payload


def write_report(shard_root, authoritative_games, target):
    paths = sorted(Path(shard_root).glob("*/*/card-insights.json"))
    report = merge_shards(paths, authoritative_games)
    target = Path(target)
    target.write_text(json.dumps(report, sort_keys=True,
                                 separators=(",", ":")) + "\n", encoding="utf-8")
    return report
