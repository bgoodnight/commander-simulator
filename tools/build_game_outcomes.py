"""Generate UI-friendly longer-game life trajectories and modeled outcomes.

This output is a separate experimental schema, never a replacement for the
six-turn Deck Lab baseline. Three opponents are ABSTRACT stress policies,
not legal Commander decks. Counts are modeled outcomes, NOT competitive win
rates. Games that run out the clock are right-censored/unresolved.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from commander_sim.deck_fixtures import FIXTURES, EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import run_bounded_early_game
from commander_sim.opponent_stress import SCENARIOS, OPPONENT_TYPES
from commander_sim.pilot_policy import STYLES,ARCHETYPES

FORMAT = "commander-modeled-outcomes-v1"
DECK_KEYS = tuple(f.key for f in (*FIXTURES,*EXPERIMENTAL_FIXTURES))
OUTCOME_STATES = ("win","loss","draw","unresolved","not_evaluated")


def _mean(values):
    return round(sum(values)/len(values),3)


def _quantile(values,fraction):
    """Stable linear quantile for any n>=1; no external dependencies."""
    values=sorted(values)
    position=(len(values)-1)*fraction
    lo=int(position)
    hi=min(len(values)-1,lo+1)
    return round(values[lo]+(values[hi]-values[lo])*(position-lo),3)


def summarize_games(runs, requested_rounds):
    """Count results without assigning a winner to censored games."""
    if not runs or type(requested_rounds) is not int:
        raise ValueError("Nonempty runs and a positive integer horizon required")
    outcome_counts={state:0 for state in OUTCOME_STATES}
    eliminated={str(seat):0 for seat in range(4)}
    completion=[]
    terminal_rounds={state:{} for state in OUTCOME_STATES}
    for run in runs:
        result=run["outcome"]
        status=result["status"]
        if status not in outcome_counts:
            raise ValueError("Unexpected modeled outcome")
        outcome_counts[status]+=1
        completed=result["completed_rounds"]
        hist=terminal_rounds[status]
        hist[str(completed)]=hist.get(str(completed),0)+1
        if result["complete"]:
            completion.append(result["completed_rounds"])
        for entry in result["eliminations"]:
            eliminated[str(entry["seat"])]+=1
    trend=[]
    for round_id in range(requested_rounds+1):
        observed=[run["life_history"][round_id]
                  for run in runs if len(run["life_history"])>round_id]
        if not observed:
            continue
        by_seat={str(seat):[record["life_totals"][seat]
                            for record in observed] for seat in range(4)}
        trend.append({
            "round":round_id,
            "observed_games":len(observed),
            "mean_life":{seat:_mean(vals)
                         for seat,vals in by_seat.items()},
            "median_life":{seat:median(vals)
                           for seat,vals in by_seat.items()},
            "p25_life":{seat:_quantile(vals,0.25)
                        for seat,vals in by_seat.items()},
            "p75_life":{seat:_quantile(vals,0.75)
                        for seat,vals in by_seat.items()},
            "alive_games":{str(seat):sum(seat in row["alive_seats"]
                                       for row in observed)
                           for seat in range(4)},
        })
    return {
        "total_games":len(runs),
        "outcome_counts":outcome_counts,
        "resolved_games":len(completion),
        "right_censored_games":outcome_counts["unresolved"],
        "median_rounds_to_modeled_terminal":(
            median(completion) if completion else None),
        "eliminations_by_seat":eliminated,
        "round_counts_by_outcome":terminal_rounds,
        "life_by_round":trend,
        "interpretation":(
            "Outcomes use modeled life-zero elimination only, with "
            "three abstract opponents. Unresolved runs are right-censored. "
            "No validated Commander multiplayer win rate is estimated."),
    }


def generate(deck_key, *, seeds=12, rounds=20, start_seed=0,
             scenario="random", provisional_mode="off",
             pilot_style="adaptive",pilot_archetype="auto",examples=0, runner=run_bounded_early_game):
    if (deck_key not in DECK_KEYS
            or type(seeds) is not int or not 1<=seeds<=200
            or type(rounds) is not int or not 1<=rounds<=30
            or type(start_seed) is not int or start_seed<0
            or scenario not in SCENARIOS
            or provisional_mode not in {"off","safe"}
            or pilot_style not in STYLES or pilot_archetype not in ARCHETYPES
            or type(examples) is not int or not 0<=examples<=3):
        raise ValueError("Invalid modeled outcome batch configuration")
    raw=[]
    for seed in range(start_seed,start_seed+seeds):
        pilot_kw=({"pilot_archetype":pilot_archetype}
                  if pilot_archetype!="auto" else {})
        run=runner(deck_key,seed=seed,turns=rounds,
                   opponent_scenario=scenario,
                   provisional_mode=provisional_mode,
                   pilot_style=pilot_style,**pilot_kw)
        if (run["deck_key"]!=deck_key
                or run["mode"]!="bounded_three_opponent_pressure"
                or run["outcome"]["fidelity"]!=
                       "abstract_opponent_pressure_not_real_decks"
                or run["outcome"]["requested_rounds"]!=rounds
                or not 1<=run["completed_rounds"]<=rounds
                or len(run["life_history"])!=run["completed_rounds"]+1):
            raise ValueError("Inconsistent bounded opponent run")
        raw.append(run)
    revision=raw[0]["deck_sha256"]
    if any(run["deck_sha256"]!=revision for run in raw):
        raise ValueError("Cannot aggregate mixed deck revisions")
    records=[{
        "seed":run["seed"],
        "opponent_roles":run["opponent_roles"],
        "opponent_composition":sorted(run["opponent_roles"].values()),
        # Kept opening hand is known before gameplay, unlike "ever seen".
        **({"opening_hand":list(run["mulligan"]["opening_hand"])}
           if isinstance(run.get("mulligan"),dict)
           and isinstance(run["mulligan"].get("opening_hand"),list) else {}),
        "completed_rounds":run["completed_rounds"],
        "outcome":run["outcome"],
        "life_history":run["life_history"],
    } for run in raw]
    replays=[{
        "seed":run["seed"],
        "opponent_roles":run["opponent_roles"],
        "opponent_composition":sorted(run["opponent_roles"].values()),
        "outcome":run["outcome"],
        "events":run["events"],
        "state_snapshots":run["state_snapshots"],
        "fidelity":"bounded_replay_with_abstract_opponents",
    } for run in raw[:examples]]
    return {
        "format":FORMAT,"schema_version":1,
        "deck_key":deck_key,"deck_sha256":revision,
        "seed_start":start_seed,"seed_count":seeds,
        "requested_rounds":rounds,
        "scenario":scenario,"opponent_type_pool":list(OPPONENT_TYPES),
        "provisional_mode":provisional_mode,
        "pilot_style":pilot_style,
        "pilot_archetype":raw[0].get("pilot_archetype"),
        "pilot_signals":raw[0].get("pilot_signals"),
        "opponent_fidelity":"abstract_opponent_pressure_not_card_exact",
        "outcomes_are_competitive_win_rates":False,
        "summary":summarize_games(raw,rounds),
        "runs":records,
        "example_replays":replays,
    }


def write_batch(path,deck_key,**kwargs):
    data=generate(deck_key,**kwargs)
    location=Path(path)
    location.parent.mkdir(parents=True,exist_ok=True)
    location.write_text(
        json.dumps(data,sort_keys=True,ensure_ascii=False,
                   separators=(",",":"))+"\n",encoding="utf-8")
    return data


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deck",choices=DECK_KEYS,required=True)
    parser.add_argument("--seeds",type=int,default=12)
    parser.add_argument("--rounds",type=int,default=20)
    parser.add_argument("--start-seed",type=int,default=0)
    parser.add_argument("--scenario",choices=sorted(SCENARIOS),
                        default="random")
    parser.add_argument("--provisional-mode",choices=("off","safe"),
                        default="off")
    parser.add_argument("--pilot-style",choices=STYLES,default="adaptive")
    parser.add_argument("--pilot-archetype",choices=ARCHETYPES,default="auto")
    parser.add_argument("--examples",type=int,default=0,
                        help="Include 0–3 full per-game replay drilldowns")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv)
    result=write_batch(args.output,args.deck,
        seeds=args.seeds,rounds=args.rounds,start_seed=args.start_seed,
        scenario=args.scenario,provisional_mode=args.provisional_mode,
        pilot_style=args.pilot_style,pilot_archetype=args.pilot_archetype,
        examples=args.examples)
    print(json.dumps({
        "format":result["format"],"deck_key":result["deck_key"],
        "requested_rounds":result["requested_rounds"],
        "scenario":result["scenario"],
        "pilot_style":result["pilot_style"],
        "pilot_archetype":result["pilot_archetype"],
        "summary":{k:v for k,v in result["summary"].items()
                   if k!="life_by_round"},
        "output":str(args.output)},indent=2))


if __name__=="__main__":
    main()
