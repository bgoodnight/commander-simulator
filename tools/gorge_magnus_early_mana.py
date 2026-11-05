"""Measure early mana development from verified Magnus Gorge event streams.

Four PERSONAL turns of Magnus, not four global Commander turns. Reports
associations with wins, never calls a missed land drop a causal loss.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path

TURN_CHANGE=9
LAND_PLAYED=23
MANA_ADD=13
PUT_ON_STACK=11
HAND,COMMAND,STACK=1,6,5

def analyze(folder:Path,policy:str):
    folder=Path(folder)
    outcomes=[json.loads(x) for x in (folder/"runs.jsonl").read_text().splitlines() if x.strip()]
    if len(outcomes)!=100 or len({x.get("seed") for x in outcomes})!=100:
        raise ValueError("Expected 100 distinct games")
    records=[]
    for row in outcomes:
        hero=row.get("hero_seat")
        if (type(hero) is not int or hero not in range(4) or
                not row.get("finished") or not row.get("replay_verified") or row.get("error") or
                row["decks"][hero]!="magnus_budget" or row["policies"][hero]!=policy):
            raise ValueError(f"Unverified or mismatched seed {row.get('seed')}")
        source=json.loads((folder/"native"/f"gorge-seed-{row['seed']}.json").read_text())
        if source.get("seed")!=row["seed"] or source.get("chain")!=row["replay_chain"]:
            raise ValueError(f"Invalid native source {row['seed']}")
        objects={o["object_id"]:o for o in source["objects"]}
        personal_turn=0
        lands=mana_events=mana_units=spells=0
        for e in source["log"]["events"]:
            kind=e.get("kind")
            if kind==TURN_CHANGE and e.get("player")==hero:
                personal_turn+=1
            if personal_turn<1 or personal_turn>4: continue
            if kind==LAND_PLAYED and e.get("player")==hero:
                lands+=1
            elif kind==MANA_ADD and e.get("player")==hero:
                mana_events+=1
                mana_units+=max(0,e.get("amount",0))
            elif (kind==PUT_ON_STACK and e.get("from") in (HAND,COMMAND)
                  and e.get("to")==STACK and objects.get(e.get("obj"),{}).get("owner")==hero):
                spells+=1
        records.append({"seed":row["seed"],"won":bool(row.get("winner_seat")==hero and not row.get("draw")),
                        "personal_turns":personal_turn,"lands_first_four":lands,
                        "mana_add_events_first_four":mana_events,
                        "mana_added_units_first_four":mana_units,
                        "spells_first_four":spells})
    return aggregate(policy,records)

def aggregate(policy,rows):
    reached=[r for r in rows if r["personal_turns"]>=4]
    def cohort(group):
        return {"n":len(group),"wins":sum(r["won"] for r in group),
                "win_rate":round(sum(r["won"] for r in group)/len(group),4) if group else None,
                "mean_early_mana_units":round(sum(r["mana_added_units_first_four"] for r in group)/len(group),2) if group else None,
                "mean_early_casts":round(sum(r["spells_first_four"] for r in group)/len(group),2) if group else None}
    out={"schema":"gorge-magnus-early-mana-v1","pilot":policy,
         "games":len(rows),"games_reaching_four_hero_turns":len(reached),
         "wins_overall":sum(r["won"] for r in rows),
         "by_early_land_plays":{
            "0_to_2":cohort([r for r in reached if r["lands_first_four"]<=2]),
            "3":cohort([r for r in reached if r["lands_first_four"]==3]),
            "4_plus":cohort([r for r in reached if r["lands_first_four"]>=4])},
         "by_outcome":{
            "win":cohort([r for r in reached if r["won"]]),
            "nonwin":cohort([r for r in reached if not r["won"]])},
         "caveats":["LandPlayed counts land play events, not total available lands (ramp may put lands directly onto the battlefield).",
             "ManaAdd events reflect production, not available mana after discounts or mana spent.",
             "Four personal-turn restriction excludes games that ended earlier; these rates are exploratory and not causal.",
             "A cast is a PutOnStack event with a matching card owner; unusual casts may be missed.",
             "Opponent composition, start position and pilot are not adjusted here."]}
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--policy",required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=analyze(a.root,a.policy)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("EARLY_MANA "+json.dumps(report,sort_keys=True))
