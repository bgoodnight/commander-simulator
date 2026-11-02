"""Paired exploratory trials of shared provisional rules across four commanders.

These are bounded goldfish tests of *action availability*, not deck win rates.
Paired seeds and forced keeps preserve each deck's shuffle/opening hand
so differences in usable actions can be attributed to opting into the
partial rules layer. This is not a realistic mulligan-performance benchmark.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from commander_sim.early_game_runner import run_bounded_early_game

DECKS=("magnus_premium","wretched_ranks","mortarion_current",
       "necron_dynasties")

def run(*,seeds=6,turns=5):
    if type(seeds) is not int or not 1<=seeds<=40:
        raise ValueError("1..40 seeds required")
    if type(turns) is not int or not 1<=turns<=10:
        raise ValueError("1..10 turns required")
    result={}
    for deck in DECKS:
        per_mode={}
        opening=[]
        for mode in ("off","safe"):
            games=[run_bounded_early_game(deck,seed=seed,turns=turns,
                                         mulligan="keep",
                                         provisional_mode=mode)
                   for seed in range(seeds)]
            counts=Counter(
                event["type"] for game in games for phase in game["events"]
                for event in phase["events"])
            partial=Counter(
                event["type"] for game in games for phase in game["events"]
                for event in phase["events"]
                if event.get("fidelity")=="provisional_partial")
            last_hands=[len(game["events"][-1]["unsupported_cards_in_hand"])
                        for game in games]
            if not opening:
                opening=[game["mulligan"]["opening_hand"] for game in games]
            elif opening!=[game["mulligan"]["opening_hand"] for game in games]:
                raise AssertionError("Opting in changed paired opening hands")
            per_mode[mode]={
                "games":len(games),
                "total_events":sum(counts.values()),
                "reviewed_commander_casts":counts["reviewed_commander_cast"],
                "creatures_resolved":counts["creature_resolved"],
                "artifacts_resolved":counts["artifact_resolved"],
                "provisional_spells_resolved":counts["provisional_spell_resolved"],
                "provisional_action_types":dict(sorted(partial.items())),
                "mean_last_unsupported_hand":round(
                    sum(last_hands)/len(last_hands),3),
                "examples":[
                    {"seed":game["seed"],"turn":phase["turn"],
                     "event":event}
                    for game in games[:2] for phase in game["events"]
                    for event in phase["events"]
                    if event.get("fidelity")=="provisional_partial"
                ][:12],
            }
        result[deck]=per_mode
    return {
        "deck_families":list(DECKS),"seeds_per_deck":seeds,
        "turns":turns,"results":result,
        "warning":"Paired goldfish observations of partial effect coverage; "
                  "not a multiplayer win-rate or bracket assessment."
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--seeds",type=int,default=6)
    p.add_argument("--turns",type=int,default=5)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    result=run(seeds=a.seeds,turns=a.turns)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+"\n",
                                    encoding="utf-8")
    for deck,states in result["results"].items():
        for mode,summary in states.items():
            print("PROVISIONAL_COMPARISON",json.dumps({
                "deck":deck,"mode":mode,**{k:v for k,v in summary.items()
                                         if k!="examples"}},sort_keys=True))
