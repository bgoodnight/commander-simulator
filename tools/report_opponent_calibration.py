"""Descriptive calibration from REAL bounded-game observations, not a four-AI fairness test.

All metrics are explicit proxies for abstract opponents; seat zero is a real deck.
Use complete JSONL per seed to avoid relying on a few example replays.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, Counter
import json
from pathlib import Path
from statistics import median


ROLES = ("aggro", "control", "value", "combo")
EVENTS = {
    "creature": "opponent_abstract_creature",
    "combat_damage": "opponent_abstract_unblocked_damage",
    "blocked": "opponent_abstract_blocked_combat",
    "removal": ("opponent_abstract_destroy", "opponent_abstract_exile"),
    "combo": "opponent_abstract_combo_loss",
}


def med(values):
    return median(values) if values else None


def summarize(source):
    paths = sorted(Path(source).glob("*.jsonl"))
    if not paths:
        raise ValueError("No authentic observation files")
    games = []
    by_role = defaultdict(list)
    per_seat = defaultdict(lambda: defaultdict(list))
    deck_summary = defaultdict(list)
    seen = set()
    for path in paths:
        for line in path.read_text(encoding="utf8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            key = (row["deck_key"], row["scenario"], row["seed"])
            if key in seen:
                raise ValueError(f"Duplicate game {key}")
            seen.add(key)
            turns = row["turn_records"]
            if len(turns) != row["completed_rounds"]:
                raise ValueError(f"Incomplete chronology {key}")
            result = row["outcome"]
            roles = {int(s): role for s, role in row["opponent_roles"].items()}
            if set(roles) != {1, 2, 3} or not set(roles.values()) <= set(ROLES):
                raise ValueError(f"Unknown opposing seat/role {key}")
            games.append({
                "deck": row["deck_key"], "scenario": row["scenario"],
                "seed": row["seed"], "rounds": row["completed_rounds"],
                "outcome": result["status"],
            })
            deck_summary[row["deck_key"]].append(games[-1])
            events = [
                (t["turn"], action)
                for t in turns for action in t.get("events", [])
                if isinstance(action, dict)
            ]
            for seat, role in roles.items():
                authored = [(turn, e) for turn, e in events
                            if e.get("seat") == seat and
                            str(e.get("type", "")).startswith("opponent_")]
                times = {}
                count = Counter()
                for kind, event_types in EVENTS.items():
                    event_types = (event_types,) if isinstance(event_types, str) else event_types
                    sample = [(turn, e) for turn, e in authored
                              if e.get("type") in event_types]
                    times[kind] = min((turn for turn, _ in sample), default=None)
                    count[kind] = len(sample)
                # Proxy: second creature entered play, not a verified lethal threat.
                creature_turns = [turn for turn, e in authored
                                  if e.get("type") == EVENTS["creature"]]
                times["two_creatures"] = creature_turns[1] if len(creature_turns) >= 2 else None
                hits = [(turn, int(e.get("amount") or 0))
                        for turn, e in authored if e.get("type") == EVENTS["combat_damage"]]
                damage = 0
                pressure_turn = None
                for turn, amount in hits:
                    damage += amount
                    if damage >= 5 and pressure_turn is None:
                        pressure_turn = turn
                times["five_combat_damage"] = pressure_turn
                losing_turn = next((h["round"] for h in row["life_history"]
                                    if seat not in h["alive_seats"]), None)
                rec = {
                    "deck": row["deck_key"], "scenario": row["scenario"],
                    "seed": row["seed"], "seat": seat, "role": role,
                    "rounds_observed": row["completed_rounds"],
                    "first": times, "counts": dict(count),
                    "observed_combat_damage": damage,
                    "eliminated_round": losing_turn,
                }
                by_role[role].append(rec)
                per_seat[role][seat].append(rec)
    def report(rows):
        n = len(rows)
        first = {kind: {
            "observed": sum(r["first"][kind] is not None for r in rows),
            "median_round_if_observed": med([r["first"][kind] for r in rows
                                            if r["first"][kind] is not None])
        } for kind in (*EVENTS, "two_creatures", "five_combat_damage")}
        return {
            "seat_games": n,
            "creature_spawn_per_seat_game": round(sum(r["counts"]["creature"] for r in rows)/n, 2),
            "combat_events_per_seat_game": round(sum(r["counts"]["combat_damage"] for r in rows)/n, 2),
            "removal_events_per_seat_game": round(sum(r["counts"]["removal"] for r in rows)/n, 2),
            "combo_events_per_seat_game": round(sum(r["counts"]["combo"] for r in rows)/n, 2),
            "first_events": first,
            "median_observed_combat_damage": med([r["observed_combat_damage"] for r in rows]),
            "seat_eliminated": sum(r["eliminated_round"] is not None for r in rows),
        }
    return {
        "format": "opponent-pressure-calibration-baseline-v1",
        "total_games": len(games),
        "decks": {deck: {
            "games": len(rows),
            "outcomes": dict(Counter(r["outcome"] for r in rows)),
            "median_terminal_round": med([r["rounds"] for r in rows if r["outcome"] in ("win", "loss", "draw")]),
            "median_last_observed_round": med([r["rounds"] for r in rows]),
        } for deck, rows in sorted(deck_summary.items())},
        "opponent_archetypes": {role: report(rows) for role, rows in sorted(by_role.items())},
        "role_by_seat": {role: {str(seat): report(rows)
                                  for seat, rows in sorted(seats.items())}
                         for role, seats in sorted(per_seat.items())},
        "limitations": [
            "This is not a four-AI tournament: seat zero is a full real deck pilot.",
            "Opponent policies are abstract, not source-paid Commander decks.",
            "All four archetypes can spawn creatures; other card-type play is not fully modeled.",
            "Threat proxies are first two spawned creatures and cumulative 5 combat damage, not demonstrated lethal threats.",
            "Medians conditional on observation exclude games without the event.",
            "No equal-seat or equal-archetype win-rate estimate is possible from this asymmetric engine."
        ],
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=summarize(args.source)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"games":result["total_games"],"decks":result["decks"],
                      "opponent_archetypes":result["opponent_archetypes"]},
                     indent=2,sort_keys=True))


if __name__=="__main__":
    main()
