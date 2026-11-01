"""Run the physical starter through the SAME reviewed-action IndexedKernel.

The physical owned list is unchanged. Only the explicit, documented one-card
legal test substitution is used. Unsupported Oracle abilities are not cast,
and neither goldfish win rates nor Commander brackets are inferred.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
from commander_sim.bounded_batch import run_bounded_batch
from commander_sim.early_game_runner import run_bounded_early_game

def run(*, seeds=40, turns=6):
    batch=run_bounded_batch("magnus_physical_trial",seeds=seeds,turns=turns)
    events=Counter()
    unsupported=Counter()
    previews=Counter()
    samples=[]
    for seed in range(seeds):
        record=run_bounded_early_game("magnus_physical_trial",seed=seed,turns=turns)
        assert len(record["state_snapshots"])==turns
        assert record["deck_sha256"]==batch["deck_sha256"]
        for row in record["events"]:
            for event in row["events"]:
                events[event["type"]]+=1
                if event["type"]=="source_paid_candidate":
                    previews[event["card"]]+=1
            unsupported.update(row["unsupported_cards_in_hand"])
        if seed<5:
            samples.append({
                "seed":seed,
                "opening_hand":record["mulligan"]["opening_hand"],
                "turns":[{
                    "turn":row["turn"],
                    "lands":row["land_count"],
                    "creatures":row["creature_count"],
                    "rocks":row["mana_rock_count"],
                    "hand":row["hand_size"],
                    "actions":[{"type":e["type"],"card":e.get("card")}
                               for e in row["events"]]
                } for row in record["events"]]
            })
    return {
        "mode":"bounded_authoritative_early_actions",
        "deck_key":"magnus_physical_trial",
        "deck_sha256":batch["deck_sha256"],
        "seed_count":seeds,"turns":turns,
        "legal_trial_substitution":{"removed":"Narset's Rebuke","added":"Island"},
        "batch":batch,
        "event_counts":dict(sorted(events.items())),
        "source_paid_candidate_counts":dict(previews.most_common(25)),
        "unsupported_hand_mentions":dict(unsupported.most_common(25)),
        "examples":samples,
        "limitations":("The established shared physical kernel handles reviewed lands, "
           "mana rocks, creatures, cleanup, and abilities with explicit review records. "
           "Unsupported spells still appear in draws, hands and graveyards, but "
           "payment candidates are not legal casts or resolved abilities. "
           "No opponent interaction, commander casting, combo wins or win rates.")
    }

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds",type=int,default=40)
    parser.add_argument("--turns",type=int,default=6)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=run(seeds=args.seeds,turns=args.turns)
    output=json.dumps(result,indent=2)
    if args.output:
        args.output.write_text(output+"\n")
    print("PHYSICAL_MAGNUS_REPORT",json.dumps({
        "seed_count":result["seed_count"],
        "deck_sha256":result["deck_sha256"],
        "final_checkpoint":result["batch"]["turns"][-1],
        "event_counts":result["event_counts"],
        "candidates":result["source_paid_candidate_counts"],
        "unsupported":result["unsupported_hand_mentions"]
    },sort_keys=True),flush=True)
