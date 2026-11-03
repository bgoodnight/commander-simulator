"""Fail closed if a published outcome batch cannot power the Results UI.

The full per-seed observation archive is validated separately. This checks
the small, current-release JSON that the browser actually receives.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(files, *, expected_games, expected_rounds):
    files = list(files)
    if not files:
        raise ValueError("No published candidate outcome files")
    totals = {"files": 0, "games": 0, "observed_rounds": 0,
              "named_actions": 0, "named_casts": 0, "named_activations": 0,
              "named_removals": 0, "rounds_with_resources": 0}
    for path in files:
        batch = json.loads(Path(path).read_text(encoding="utf-8"))
        runs = batch.get("runs")
        if (batch.get("format") != "commander-modeled-outcomes-v1"
                or batch.get("requested_rounds") != expected_rounds
                or not isinstance(runs, list) or len(runs) != expected_games
                or batch.get("seed_count") != expected_games):
            raise ValueError(f"Wrong batch format or size: {path}")
        seen = set()
        file_casts = 0
        for run in runs:
            seed, rounds = run.get("seed"), run.get("completed_rounds")
            records, history = run.get("ui_observations"), run.get("life_history")
            opening = run.get("opening_hand")
            if (not isinstance(seed, int) or isinstance(seed, bool)
                    or seed in seen or not isinstance(rounds, int)
                    or not 1 <= rounds <= expected_rounds
                    or not isinstance(opening, list) or len(opening) != 7
                    or not isinstance(records, list) or len(records) != rounds
                    or not isinstance(history, list) or len(history) != rounds + 1):
                raise ValueError(f"Missing or incomplete per-seed UI observations: {path} seed={seed}")
            seen.add(seed)
            for turn, row in enumerate(records, 1):
                if (not isinstance(row, dict) or row.get("turn") != turn
                        or not all(isinstance(row.get(k), list)
                                   for k in ("hand", "battlefield", "graveyard", "actions"))
                        or not all(isinstance(row.get(k), int)
                                   and not isinstance(row.get(k), bool) and row[k] >= 0
                                   for k in ("land_count", "creature_count", "mana_rock_count"))
                        or not all(isinstance(a, dict) and isinstance(a.get("type"), str)
                                   for a in row["actions"])):
                    raise ValueError(f"Incomplete UI turn/zone/resource data: {path} seed={seed} turn={turn}")
                totals["observed_rounds"] += 1
                totals["rounds_with_resources"] += 1
                for action in row["actions"]:
                    label = action.get("card") or action.get("source")
                    if not isinstance(label, str) or not label.strip():
                        continue
                    totals["named_actions"] += 1
                    action_type = action["type"]
                    if (action_type == "land_play"
                            or action_type.endswith("_cast")
                            or action_type in ("reviewed_commander_cast",
                                               "reviewed_instant_response",
                                               "reviewed_common_spell_resolved",
                                               "reviewed_zone_spell_resolved")):
                        file_casts += 1
                        totals["named_casts"] += 1
                    if "activated" in action_type or "trigger" in action_type:
                        totals["named_activations"] += 1
                    if isinstance(action.get("destroyed_count"), int) and action["destroyed_count"] > 0:
                        totals["named_removals"] += action["destroyed_count"]
        if not file_casts:
            raise ValueError(f"No named card-play evidence in full UI batch: {path}")
        totals["files"] += 1
        totals["games"] += len(runs)
    return totals


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--expected-games", type=int, required=True)
    parser.add_argument("--expected-rounds", type=int, required=True)
    args = parser.parse_args(argv)
    result = validate(sorted(args.source.glob("*.json")),
                      expected_games=args.expected_games, expected_rounds=args.expected_rounds)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
