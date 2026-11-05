"""Paired exploratory AI pilot comparisons for fixed Gorge Commander cohorts."""
import argparse
import json
import math
from pathlib import Path

POLICIES=("bot","forge-heuristic","forge-heuristic-hold","lethal-pressure")
DECKS=("mortarion_current","magnus_budget")

def wilson(k,n):
    if not n:return (None,None)
    z=1.95996398454
    d=1+z*z/n
    m=(k/n+z*z/(2*n))/d
    h=z*math.sqrt(k*(n-k)/n**3+z*z/(4*n*n))/d
    return [round(m-h,4),round(m+h,4)]

def exact_pair_p(b,c):
    n=b+c
    if n==0:return 1.
    return min(1.,2*sum(math.comb(n,k) for k in range(min(b,c)+1))/2**n)

def compare(root:Path):
    results={"schema":"gorge-patched-four-pilot-comparison-v1",
             "policy_patch":"temporary pinned Gorge botpolicy trigger-cost-X/pay patch",
             "decks":{}}
    for deck in DECKS:
        cohorts={}
        for policy in POLICIES:
            path=root/deck/policy/"results.json"
            x=json.loads(path.read_text())
            if x["policy"]!=policy or x["deck"]!=deck or x["games"]!=100:
                raise ValueError(f"Unverified cohort {path}")
            records={v["seed"]:v for v in x["details"]}
            if len(records)!=100:raise ValueError(f"Duplicated seeds in {path}")
            cohorts[policy]=(x,records)
        shared=set.intersection(*(set(c[1]) for c in cohorts.values()))
        if not shared:raise ValueError(f"No shared seeds for {deck}")
        # Restrict comparisons to truly matched seat/opponent pods, rather than
        # merely assuming the same seed always generates the same seating.
        matched=sorted(s for s in shared if
                       len({(cohorts[p][1][s]["hero_seat"],
                             tuple(cohorts[p][1][s]["opponents"])) for p in POLICIES})==1)
        if not matched:raise ValueError(f"No identical seat/opponent pods for {deck}")
        out={"matched_games":len(matched),"policies":{},"pairwise_vs_bot":{}}
        for p,(x,records) in cohorts.items():
            out["policies"][p]={"games":100,"wins":x["wins"],"draws":x["draws"],
                "win_rate":x["wins"]/100,"wilson_95":wilson(x["wins"],100),
                "astartes_games":x["astartes_games"],
                "astartes_tokens":x["astartes_tokens"],
                "matched_wins":sum(records[s]["won"] for s in matched)}
        base=cohorts["bot"][1]
        for p in POLICIES[1:]:
            other=cohorts[p][1]
            better=sum(other[s]["won"] and not base[s]["won"] for s in matched)
            worse=sum(base[s]["won"] and not other[s]["won"] for s in matched)
            out["pairwise_vs_bot"][p]={"other_wins_bot_loses":better,
                "bot_wins_other_loses":worse,"paired_win_rate_diff":round((better-worse)/len(matched),4),
                "mcnemar_exact_unadjusted_p":round(exact_pair_p(better,worse),6)}
        results["decks"][deck]=out
    return results

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=compare(a.root)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("PILOT_COMPARISON "+json.dumps(report,sort_keys=True))
