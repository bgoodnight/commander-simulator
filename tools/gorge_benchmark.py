"""Compare run characteristics without equating unlike simulator workloads.

Baseline uses our bounded one-real-seat / three abstract-seat kernel.
gorge uses four full pinned Commander decks, proper 40-life rules and bots.
Win percentages are NOT comparable across these two modes.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics
import time

DECKS=("mortarion_current","magnus_premium","necron_dynasties","wretched_ranks")


def baseline(games=3,turns=10,seed=100):
    from commander_sim.early_game_runner import run_bounded_early_game
    results=[]
    for index in range(games):
        key=DECKS[index%len(DECKS)]
        start=time.perf_counter()
        try:
            run=run_bounded_early_game(key,seed=seed+index,turns=turns,
                                       opponent_scenario="balanced")
            elapsed=time.perf_counter()-start
            results.append({
                "seed":seed+index,"deck":key,"elapsed_seconds":elapsed,
                "rounds":run["completed_rounds"],
                "outcome":run.get("outcome"),
                "events":sum(len(phase["events"]) for phase in run["events"]),
                "finished":bool(run["outcome"].get("complete")),
                "mode":run["mode"],
            })
        except Exception as exc:
            results.append({"seed":seed+index,"deck":key,
                "elapsed_seconds":time.perf_counter()-start,
                "error":type(exc).__name__+": "+str(exc),
                "finished":False})
    return results


def summarize(results,engine):
    times=[r["elapsed_seconds"] for r in results]
    successful=[r for r in results if not r.get("error")]
    completed=sum(bool(r.get("finished")) for r in results)
    total=sum(times)
    return {
        "engine":engine,"attempted":len(results),
        "completed":completed,"failed":len(results)-len(successful),
        "stalled_or_horizon_reached":sum(
            not r.get("finished") and not r.get("error") for r in results),
        "elapsed_seconds":round(total,3),
        "seconds_per_attempt":round(statistics.mean(times),3) if times else None,
        "games_per_minute":round(len(results)*60/total,2) if total else None,
        "median_turns_or_rounds":statistics.median([
            r.get("turns",r.get("rounds",0)) for r in successful])
            if successful else None,
        "average_events":round(statistics.mean([
            r.get("events",0) for r in successful]),1) if successful else None,
        "replay_verified":sum(bool(r.get("replay_verified")) for r in results),
        "winners":dict(Counter(
            r["decks"][r["winner_seat"]] for r in results
            if r.get("winner_seat") is not None)),
    }


def collect(gorge_path,baseline_path,output):
    gorge=[]
    for line in Path(gorge_path).read_text().splitlines():
        if line.strip():
            row=json.loads(line)
            if not isinstance(row,dict) or "seed" not in row:
                raise ValueError("Invalid gorge sample line")
            gorge.append(row)
    base=json.loads(Path(baseline_path).read_text())
    report={
        "schema":"commander-backend-comparison-v1",
        "gorge":summarize(gorge,"gorge_real_four_deck_commander"),
        "baseline":summarize(base,"python_bounded_abstract_opponent_pressure"),
        "comparable_metrics":(
            "Game counts, elapsed times and structural output availability "
            "are reported, but games/minute is NOT an apples-to-apples "
            "benchmark because gorge plays actual four-deck Commander games "
            "while the Python baseline uses three abstract opponent seats."),
        "limitations":[
            "Different engine rules, bot choices, opponents and game horizon",
            "No win-rate or power ranking comparison is valid",
            "Corpus fetch, compile and Go build time excluded from warm game throughput",
            "Replay event counts differ in meaning between the two engines",
            "Small sample: use larger runs before assessing stability and speed",
        ],
        "gorge_samples":gorge,
        "baseline_samples":base,
    }
    Path(output).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report


def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("baseline")
    a.add_argument("--games",type=int,default=3)
    a.add_argument("--turns",type=int,default=10)
    a.add_argument("--seed",type=int,default=100)
    a.add_argument("--output",required=True)
    b=sub.add_parser("collect")
    b.add_argument("--gorge",required=True)
    b.add_argument("--baseline",required=True)
    b.add_argument("--output",required=True)
    opts=parser.parse_args()
    if opts.cmd=="baseline":
        if opts.games<1 or opts.games>1000 or not 1<=opts.turns<=30:
            parser.error("Invalid sample range")
        rows=baseline(opts.games,opts.turns,opts.seed)
        Path(opts.output).write_text(json.dumps(rows,indent=2)+"\n")
        print(json.dumps(summarize(rows,"python_bounded_abstract_opponent_pressure")))
    else:
        report=collect(opts.gorge,opts.baseline,opts.output)
        print(json.dumps({"gorge":report["gorge"],"baseline":report["baseline"]}))
if __name__=="__main__":
    main()
