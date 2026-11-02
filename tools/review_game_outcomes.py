"""Review a recorded cohort before scaling modeled Commander simulations.

Reads actual output from build_game_outcomes.py; cannot infer missing plays,
opponent deck identities, or accurate multiplayer win probabilities.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import median

from commander_sim.deck_lab_api import deck_detail
from commander_sim.opponent_stress import SCENARIOS
from tools.publish_game_outcomes import validate_batch


SCENARIOS_ORDER = ("balanced", "aggressive", "control", "combo", "mixed")
STATES = ("win", "loss", "draw", "unresolved", "not_evaluated")


def _median(values):
    return median(values) if values else None


def _pilot_elimination_round(run):
    rows = run["life_history"]
    for previous, current in zip(rows, rows[1:]):
        before, after = previous["life_totals"], current["life_totals"]
        if (0 in previous["alive_seats"] and 0 not in current["alive_seats"]) or (
            before["0"] > 0 and after["0"] <= 0):
            return current["round"]
    return None


def summarize(source, *, deck_key, seed_count, requested_rounds,
              scenarios=SCENARIOS_ORDER):
    root = Path(source)
    files = sorted(root.glob("*.json"))
    if len(files) != len(scenarios) or set(scenarios) - set(SCENARIOS):
        raise ValueError("Scenario count or identity does not match requested sample")
    deck_hash = deck_detail(deck_key)["deck_sha256"]
    output = {}
    replays = 0
    decision_roles = Counter()
    event_types = Counter()
    engine_sha = set()
    for path in files:
        batch = json.loads(path.read_text(encoding="utf-8"))
        validate_batch(batch, deck_hashes={deck_key: deck_hash})
        scenario = batch["scenario"]
        if (batch["deck_key"] != deck_key or scenario not in scenarios
                or scenario in output or batch["requested_rounds"] != requested_rounds
                or batch["seed_count"] != seed_count
                or {run["seed"] for run in batch["runs"]} != set(range(seed_count))):
            raise ValueError("Unexpected deck, scenario, horizon or incomplete seed range: "
                             + path.name)
        if not batch.get("pilot_archetype"):
            raise ValueError("Expected the merged archetype-aware pilot to record its archetype")
        if batch.get("pilot_style") != "adaptive" or batch.get("provisional_mode") != "safe":
            raise ValueError("Unexpected pilot style or rules approximation")
        rows = batch["runs"]
        counts = Counter(run["outcome"]["status"] for run in rows)
        complete = [run["completed_rounds"] for run in rows
                    if run["outcome"].get("complete")]
        knockouts = [_pilot_elimination_round(run) for run in rows
                     if run["outcome"]["status"] == "loss"]
        knockouts = [turn for turn in knockouts if turn is not None]
        victories = [run["completed_rounds"] for run in rows
                     if run["outcome"]["status"] == "win"]
        snapshots = {}
        for turn in (6, 10, 20, 30):
            life = [run["life_history"][turn]["life_totals"]["0"] for run in rows
                    if turn < len(run["life_history"])]
            snapshots[str(turn)] = {"games_observed":len(life),
                                     "median_own_life":_median(life)}
        for replay in batch.get("example_replays", []):
            replays += 1
            for round_record in replay.get("events", []):
                for decision in round_record.get("pilot_decisions", []):
                    decision_roles[str(decision.get("role", "unspecified"))] += 1
                for event in round_record.get("events", []):
                    event_types[str(event.get("type", "unspecified"))] += 1
        output[scenario] = {
            "games": len(rows),
            "outcomes":{status:counts[status] for status in STATES},
            "modeled_win_share":round(counts["win"] / len(rows), 4),
            "median_terminal_round":_median(complete),
            "terminal_games":len(complete),
            "median_pilot_elimination_round":_median(knockouts),
            "pilot_knockout_games":len(knockouts),
            "median_victory_round":_median(victories),
            "victory_games":len(victories),
            "life_snapshots":snapshots,
            "pilot_archetype":batch["pilot_archetype"],
            "example_replays":len(batch.get("example_replays", [])),
        }
    if set(output) != set(scenarios):
        raise ValueError("Missing requested scenario in complete batch")
    totals = {status:sum(output[s]["outcomes"][status] for s in scenarios)
              for status in STATES}
    return {
        "format":"commander-modeled-outcome-review-v1",
        "deck_key":deck_key, "deck_sha256":deck_hash,
        "pilot_style":"adaptive", "provisional_mode":"safe",
        "max_rounds":requested_rounds,
        "total_games":len(scenarios)*seed_count,
        "totals":totals,
        "scenarios":{scenario:output[scenario] for scenario in scenarios},
        "replay_samples":replays,
        "sampled_pilot_decisions_by_role":dict(sorted(decision_roles.items())),
        "sampled_game_events_by_type":dict(sorted(event_types.items())),
        "limitations":[
            "Opponent seats use abstract pressure policies, not full Commander decks",
            "Only life-zero modeled endgames are measured",
            "Unresolved games are right-censored, never losses",
            "Pilot action counts summarize the limited example replays, not all games",
        ],
        "review_warnings":([
            "Over half of games were unresolved at the horizon"
        ] if totals["unresolved"] > len(scenarios)*seed_count/2 else []) + (
            ["Recorded replay examples contained no pilot decisions"]
            if not decision_roles else []
        ),
    }


def markdown(report):
    rows = [
        "# Mortarion · 500-game simulation review",
        "",
        f"Deck: {report['deck_key']} · {report['deck_sha256'][:12]}",
        f"Adaptive pilot · safe approximations · {report['max_rounds']}-round limit",
        "",
        "| Abstract opponent group | Games | W | L | Draw | Unresolved | Median finish round | Median our knockout round |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, record in report["scenarios"].items():
        c=record["outcomes"]
        rows.append(f"| {name.capitalize()} | {record['games']} | {c['win']} | "
                    f"{c['loss']} | {c['draw']} | {c['unresolved']} | "
                    f"{record['median_terminal_round'] if record['median_terminal_round'] is not None else '—'} | "
                    f"{record['median_pilot_elimination_round'] if record['median_pilot_elimination_round'] is not None else '—'} |")
    totals = report["totals"]
    rows.extend([
        "",
        f"**Total:** {report['total_games']} · Wins {totals['win']} · "
        f"Losses {totals['loss']} · Draws {totals['draw']} · "
        f"Unresolved {totals['unresolved']}",
        "",
        f"**Narrative samples:** {report['replay_samples']} recorded replays.",
        "Sampled pilot decision roles: " +
        (", ".join(f"{k} {v}" for k,v in report["sampled_pilot_decisions_by_role"].items()) or "None"),
        "",
        "**Review warnings:** " +
        ("; ".join(report["review_warnings"]) if report["review_warnings"] else
         "No automatic sample-wide warning; review seed narratives before other decks."),
        "",
        "**Interpretation:** Modeled four-seat pressure only; no competitive win-rate claim.",
        "",
    ])
    return "\n".join(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--deck",default="mortarion_physical_final")
    parser.add_argument("--seeds",type=int,default=100)
    parser.add_argument("--rounds",type=int,default=30)
    parser.add_argument("--json-output",type=Path,required=True)
    parser.add_argument("--markdown-output",type=Path,required=True)
    args=parser.parse_args()
    report=summarize(args.source,deck_key=args.deck,
                     seed_count=args.seeds,requested_rounds=args.rounds)
    for path in (args.json_output,args.markdown_output):
        path.parent.mkdir(parents=True,exist_ok=True)
    args.json_output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",
                                encoding="utf-8")
    args.markdown_output.write_text(markdown(report),encoding="utf-8")
    print(markdown(report))


if __name__ == "__main__":
    main()
