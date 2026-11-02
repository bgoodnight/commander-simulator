"""Seeded bounded physical-deck trials via the existing IndexedKernel.

A deck must be registered in EXPERIMENTAL_FIXTURES and have a pinned,
independently imported Scryfall snapshot. No inferred abilities or win rates.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from commander_sim.bounded_batch import run_bounded_batch
from commander_sim.early_game_runner import run_bounded_early_game
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES

def run(deck_key,*,seeds=40,turns=6):
    if deck_key not in {fixture.key for fixture in EXPERIMENTAL_FIXTURES}:
        raise ValueError("Expected explicitly registered experimental deck")
    aggregate=run_bounded_batch(deck_key,seeds=seeds,turns=turns)
    events=Counter()
    unsupported=Counter()
    candidates=Counter()
    samples=[]
    for seed in range(seeds):
        result=run_bounded_early_game(deck_key,seed=seed,turns=turns)
        assert result["deck_sha256"]==aggregate["deck_sha256"]
        assert len(result["state_snapshots"])==turns
        for turn in result["events"]:
            for event in turn["events"]:
                events[event["type"]]+=1
                if event["type"]=="source_paid_candidate":
                    candidates[event["card"]]+=1
                    assert event["effect_status"]=="unsupported"
            unsupported.update(turn["unsupported_cards_in_hand"])
            assert turn["maximum_hand_size"] is None or turn["hand_size"]<=turn["maximum_hand_size"]
        if seed<3:
            samples.append({
                "seed":seed,
                "opening_hand":result["mulligan"]["opening_hand"],
                "turns":[{
                    "turn":turn["turn"],
                    "lands":turn["land_count"],
                    "rocks":turn["mana_rock_count"],
                    "creatures":turn["creature_count"],
                    "hand":turn["hand_size"],
                    "events":[{"type":event["type"],"card":event.get("card")}
                              for event in turn["events"]]
                } for turn in result["events"]]
            })
    return {
        "deck_key":deck_key,"deck_sha256":aggregate["deck_sha256"],
        "mode":"bounded_authoritative_early_actions",
        "seed_count":seeds,"turns":turns,
        "batch":aggregate,"events":dict(events),
        "candidate_cards":dict(candidates.most_common()),
        "unsupported_hand_mentions":dict(unsupported.most_common()),
        "sample_runs":samples,
        "caveat":"Only reviewed physical actions resolve; all remaining card abilities, "
                 "opponent priority and full targeting, exhaustive commander effects, "
                 "combat and calibrated multiplayer win rates remain unimplemented."
    }

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--deck",choices=sorted(f.key for f in EXPERIMENTAL_FIXTURES),required=True)
    parser.add_argument("--seeds",type=int,default=40)
    parser.add_argument("--turns",type=int,default=6)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    data=run(args.deck,seeds=args.seeds,turns=args.turns)
    if args.output:
        args.output.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    print("PHYSICAL_DECK_REPORT",json.dumps({
        "key":data["deck_key"],"deck_sha256":data["deck_sha256"],
        "n":data["seed_count"],"last_turn":data["batch"]["turns"][-1],
        "events":data["events"],"unsupported":data["unsupported_hand_mentions"]
    },sort_keys=True),flush=True)
