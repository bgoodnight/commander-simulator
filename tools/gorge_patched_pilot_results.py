"""Extract complete, replay-verified AI benchmark results from native Gorge traces.

All four hero variants face default-bot precons and use the same attempted seed
range and fixed engine/deck versions. No sampled replay-based win rates.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ASTARTES = "b_2_2_astartes_warrior_menace"

def summarize(root:Path,deck:str,policy:str,n:int):
    root=Path(root)
    rows=[json.loads(x) for x in (root/"runs.jsonl").read_text().splitlines() if x.strip()]
    if len(rows)!=n or len({r["seed"] for r in rows})!=n:
        raise ValueError(f"Expected {n} distinct valid seeds")
    details=[]
    for r in rows:
        seat=r.get("hero_seat")
        if (not r.get("finished") or not r.get("replay_verified") or r.get("error")
            or type(seat) is not int or not (0<=seat<4) or r["decks"][seat]!=deck
            or r["policies"][seat]!=policy or any(p!="bot" for i,p in enumerate(r["policies"]) if i!=seat)):
            raise ValueError(f"Invalid cohort game seed={r.get('seed')}")
        trace=json.loads((root/"native"/f"gorge-seed-{r['seed']}.json").read_text())
        if trace.get("seed")!=r["seed"] or trace.get("chain")!=r["replay_chain"] or trace.get("decks")!=r["decks"]:
            raise ValueError(f"Native trace mismatch {r['seed']}")
        count=sum(e.get("kind")==31 and e.get("text")==ASTARTES and e.get("player")==seat
                  for e in trace["log"]["events"])
        details.append({"seed":r["seed"],"won":int(r.get("winner_seat")==seat and not r.get("draw")),
                        "draw":bool(r.get("draw")),"hero_seat":seat,
                        "opponents":tuple(r["decks"][i] for i in range(4) if i!=seat),
                        "turns":r["turns"],"astartes":count})
    result={"schema":"gorge-patched-pilot-v2","deck":deck,"policy":policy,
            "games":len(details),"wins":sum(r["won"] for r in details),
            "draws":sum(r["draw"] for r in details),
            "astartes_games":sum(r["astartes"]>0 for r in details),
            "astartes_tokens":sum(r["astartes"] for r in details),
            "details":details}
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--deck",required=True)
    p.add_argument("--policy",required=True)
    p.add_argument("--games",type=int,default=100)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=summarize(a.root,a.deck,a.policy,a.games)
    a.out.write_text(json.dumps(report,sort_keys=True)+"\n")
    print("PILOT_RESULT "+json.dumps({k:v for k,v in report.items() if k!="details"},sort_keys=True))
