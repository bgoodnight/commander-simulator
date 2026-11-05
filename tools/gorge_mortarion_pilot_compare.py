"""Compare matched-seed Mortarion pilot outcomes, with honest uncertainty."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

POLICIES=("bot","forge-heuristic","forge-heuristic-hold","lethal-pressure")


def wilson(wins,n):
    if n==0:return [None,None]
    z=1.959963984540054
    center=(wins/n+z*z/(2*n))/(1+z*z/n)
    margin=z*math.sqrt((wins/n)*(1-wins/n)/n+z*z/(4*n*n))/(1+z*z/n)
    return [round(center-margin,4),round(center+margin,4)]


def mcnemar_exact(b,c):
    n=b+c
    if n==0:return 1.0
    lower=sum(math.comb(n,k) for k in range(min(b,c)+1))
    return round(min(1.0,2*lower/(2**n)),6)


def compare(root:Path):
    cohorts={}
    for policy in POLICIES:
        payload=json.loads((root/policy/"strategy.json").read_text())
        if payload["policy"]!=policy or payload["games"]!=100:
            raise ValueError("Wrong policy or incomplete outcome cohort")
        rows={r["seed"]:r for r in payload["games_detail"]}
        if len(rows)!=100:
            raise ValueError("Duplicate seed in policy")
        cohorts[policy]=(payload,rows)
    shared=set.intersection(*(set(rows) for _,rows in cohorts.values()))
    if not shared:
        raise ValueError("No shared valid seeds")
    report={"schema":"gorge-mortarion-matched-pilots-v1",
            "comparison":"shared verified seed intersection (attempted seed, rotated seat and opponent pod match)",
            "policies":{},
            "shared_seed_count":len(shared),"pairwise_to_default":{}}
    for policy,(payload,rows) in cohorts.items():
        wins=payload["wins"]
        report["policies"][policy]={
            "games":100,"wins":wins,"win_rate":wins/100,
            "win_rate_95pct_wilson":wilson(wins,100),
            "astartes_token_events":payload["astartes_token_events"],
            "astartes_games":payload["astartes_games"],
            "mortarion_trigger_events":payload["mortarion_trigger_events"],
            "pestilence_activations":payload["pestilence_activations"],
            "pestilence_and_astartes_games":payload["pestilence_and_astartes_games"],
            "wins_shared_seeds":sum(rows[seed]["won"] for seed in shared)}
    baseline=cohorts["bot"][1]
    for policy in POLICIES[1:]:
        other=cohorts[policy][1]
        b=sum(bool(other[seed]["won"]) and not baseline[seed]["won"] for seed in shared)
        c=sum(bool(baseline[seed]["won"]) and not other[seed]["won"] for seed in shared)
        report["pairwise_to_default"][policy]={
            "matched_games":len(shared),
            "other_wins_baseline_loses":b,
            "baseline_wins_other_loses":c,
            "matched_win_rate_difference":round((b-c)/len(shared),4),
            "mcnemar_exact_two_sided_p":mcnemar_exact(b,c),
            "note":"Exploratory, unadjusted for three comparisons; do not overclaim significance"}
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    report=compare(args.root)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("MORTARION_PILOT_COMPARISON "+json.dumps(report,sort_keys=True))
