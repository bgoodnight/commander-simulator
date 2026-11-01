"""Produce versioned, reproducible bounded-game archives without touching Pages.

A run is generated only once; aggregates and drilldowns come from the same
physical-kernel records. Archives are *reviewed-action* games, not win rates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import run_bounded_early_game

DECK_KEYS = tuple(f.key for f in FIXTURES)
FORMAT = "commander-bounded-archive-v1"


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False) + "\n").encode("utf-8")


def _mean(values):
    return round(sum(values) / len(values), 3)


def summarize(runs, turns):
    """Aggregate exact event and per-turn physical measurements."""
    if not runs:
        raise ValueError("At least one run required")
    output = []
    for turn in range(turns):
        rows = [run["events"][turn] for run in runs]
        event_counts = {}
        for row in rows:
            for event in row["events"]:
                name = event["type"]
                event_counts[name] = event_counts.get(name, 0) + 1
        output.append({
            "turn": turn + 1,
            "mean_lands": _mean([row["land_count"] for row in rows]),
            "mean_creatures": _mean([row["creature_count"] for row in rows]),
            "mean_mana_rocks": _mean([row["mana_rock_count"] for row in rows]),
            "mean_hand_size": _mean([row["hand_size"] for row in rows]),
            "mean_unsupported_hand_cards": _mean([
                len(row["unsupported_cards_in_hand"]) for row in rows]),
            "event_counts": dict(sorted(event_counts.items())),
        })
    return output


def compact_run(run):
    """Preserve genuine physical events and useful per-seed drilldown."""
    return {
        "seed": run["seed"],
        "deck_key": run["deck_key"],
        "deck_sha256": run["deck_sha256"],
        "mode": run["mode"],
        "mulligan": run["mulligan"],
        "events": run["events"],
        "state_snapshots": [
            {k: state[k] for k in (
                "turn", "battlefield", "hand", "graveyard", "exile",
                "untracked_tokens", "object_views")}
            for state in run["state_snapshots"]],
    }


def generate(deck_key, *, seeds=100, turns=6, start_seed=0,
             runner=run_bounded_early_game):
    if deck_key not in DECK_KEYS:
        raise ValueError("Unknown pinned deck")
    if type(seeds) is not int or not 1 <= seeds <= 1000:
        raise ValueError("Seeds must be 1..1000")
    if type(turns) is not int or not 1 <= turns <= 10:
        raise ValueError("Turns must be 1..10")
    if type(start_seed) is not int or start_seed < 0:
        raise ValueError("Start seed must be nonnegative")
    runs = [runner(deck_key, seed=seed, turns=turns)
            for seed in range(start_seed, start_seed + seeds)]
    deck_hash = runs[0]["deck_sha256"]
    if any(run["deck_key"] != deck_key or run["deck_sha256"] != deck_hash
           or run["mode"] != "bounded_authoritative_early_actions"
           or len(run["events"]) != turns or
           len(run["state_snapshots"]) != turns
           for run in runs):
        raise ValueError("Mixed deck revision, fidelity or turn count")
    return {
        "format": FORMAT,
        "deck_key": deck_key,
        "deck_sha256": deck_hash,
        "seed_start": start_seed,
        "seed_count": seeds,
        "turn_count": turns,
        "mode": "bounded_authoritative_early_actions",
        "summary": summarize(runs, turns),
    }, [compact_run(run) for run in runs]


def write_archive(directory, deck_key, *, seeds=100, turns=6, start_seed=0,
                  runner=run_bounded_early_game):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    summary, runs = generate(deck_key, seeds=seeds, turns=turns,
                             start_seed=start_seed, runner=runner)
    run_name = f"{deck_key}-seeds-{start_seed}-{start_seed+seeds-1}.json"
    run_bytes = _json_bytes(runs)
    summary["run_file"] = run_name
    summary["run_sha256"] = hashlib.sha256(run_bytes).hexdigest()
    summary["schema_version"] = 1
    summary["limitations"] = (
        "Only reviewed physical actions execute. No general opponent priority, "
        "combat or validated multiplayer win rates."
    )
    (directory / run_name).write_bytes(run_bytes)
    summary_name = f"{deck_key}-manifest.json"
    (directory / summary_name).write_bytes(_json_bytes(summary))
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deck", required=True, choices=DECK_KEYS)
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--turns", type=int, default=6)
    parser.add_argument("--start-seed", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_archive(args.output, args.deck, seeds=args.seeds,
                           turns=args.turns, start_seed=args.start_seed)
    print(json.dumps({k: report[k] for k in (
        "format", "deck_key", "seed_count", "run_file", "run_sha256")}, indent=2))


if __name__ == "__main__":
    main()
