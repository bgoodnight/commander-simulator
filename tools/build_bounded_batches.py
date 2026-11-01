"""Regenerate all six pinned Deck Lab six-turn batches from the current engine.

The four legacy summary/drilldown datasets become six. This tool only writes
validated JSON inputs to the existing static UI; no browser code is changed.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from commander_sim.bounded_batch import run_bounded_batch
from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import run_bounded_early_game

KEYS = tuple(f.key for f in FIXTURES)
FILES = (
    "commander_sim/generic_cast.py",
    "commander_sim/reviewed_sacrifice_actions.py",
    "commander_sim/early_game_runner.py",
    "commander_sim/bounded_batch.py",
)


def generate(*, seeds=100, output=None):
    if type(seeds) is not int or not 1 <= seeds <= 1000:
        raise ValueError("Seed count must be 1 through 1000")
    out = Path(output) if output is not None else ROOT / "web/pages/data"
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "format": "bounded-batches-v1",
        "base_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "engine_files_sha256": {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in FILES
        },
        "decks": {},
    }
    if len(KEYS) != 6 or len(set(KEYS)) != 6:
        raise ValueError("Expected the six approved fixture decks")

    for key in KEYS:
        batch = run_bounded_batch(key, seeds=seeds, turns=6)
        runs = []
        for seed in range(seeds):
            run = run_bounded_early_game(key, seed=seed, turns=6)
            if (run["deck_sha256"] != batch["deck_sha256"]
                    or run["mode"] != "bounded_authoritative_early_actions"
                    or len(run["events"]) != 6
                    or len(run["state_snapshots"]) != 6):
                raise ValueError("Run does not match current bounded batch")
            for turn in run["events"]:
                maximum = turn.get("maximum_hand_size")
                if maximum is not None and turn["hand_size"] > maximum:
                    raise ValueError("Cleanup hand limit was not enforced")
            compact = {k: run[k] for k in
                       ("mode", "deck_key", "deck_sha256", "seed")}
            compact["mulligan"] = {"policy": run["mulligan"]["policy"]}
            compact["events"] = [
                {
                    **{k: row[k] for k in
                       ("turn", "land_count", "hand_size",
                        "unsupported_cards_in_hand")},
                    "events": [
                        {k: e[k] for k in ("type", "card") if k in e}
                        for e in row["events"]
                    ],
                } for row in run["events"]
            ]
            compact["state_snapshots"] = [
                {k: state[k] for k in ("turn", "hand", "battlefield")}
                for state in run["state_snapshots"]
            ]
            runs.append(compact)
        filename = f"bounded-runs-{key}.json"
        (out / filename).write_text(
            json.dumps(runs, separators=(",", ":")) + "\n",
            encoding="utf-8")
        result["decks"][key] = batch
        print(f"{key}: {seeds} six-turn runs verified", flush=True)
    (out / "bounded-batches.json").write_text(
        json.dumps(result, separators=(",", ":")) + "\n",
        encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    generate(seeds=args.seeds, output=args.output)


if __name__ == "__main__":
    main()
