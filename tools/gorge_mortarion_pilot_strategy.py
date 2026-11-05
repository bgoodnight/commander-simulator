"""Source-backed Mortarion strategy evidence for matched pilot experiments."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

TRIGGER_KINDS = {27,38,46,54,72,80}
PEST_KINDS = {34,55,67,79,88}
PEST_CARDS = {"Pestilence","Pestilence Demon","Crypt Rats","Thrashing Wumpus"}
ASTARTES_STEM = "b_2_2_astartes_warrior_menace"


def analyze(folder: Path, pilot: str):
    folder=Path(folder)
    rows=[json.loads(line) for line in (folder/"runs.jsonl").read_text().splitlines() if line.strip()]
    if len(rows)!=100 or len({r["seed"] for r in rows})!=100:
        raise ValueError("Expected 100 unique outcome seeds")
    output=[]
    for row in rows:
        if not row.get("finished") or not row.get("replay_verified") or row.get("error"):
            raise ValueError(f"Unverified game {row.get('seed')}")
        hero=row.get("hero_seat")
        if type(hero) is not int or row["decks"][hero]!="mortarion_current" or row["policies"][hero]!=pilot:
            raise ValueError(f"Wrong hero policy/seat: {row.get('seed')}")
        path=folder/"native"/f"gorge-seed-{row['seed']}.json"
        source=json.loads(path.read_text())
        if source.get("seed")!=row["seed"] or source.get("chain")!=row["replay_chain"]:
            raise ValueError(f"Native source mismatch: {row['seed']}")
        objs={o["object_id"]:o.get("card_name") or o.get("effective_name")
              for o in source.get("objects",[]) if isinstance(o,dict)}
        astartes,pest,triggers,unknown=0,0,0,0
        for ev in source["log"]["events"]:
            if ev.get("player")!=hero:
                continue
            kind=ev.get("kind")
            text=str(ev.get("text",""))
            card=objs.get(ev.get("obj"))
            if kind==31 and ASTARTES_STEM in text.lower():
                astartes+=1
            if kind in PEST_KINDS and card in PEST_CARDS:
                pest+=1
            if kind in TRIGGER_KINDS and card=="Mortarion, Daemon Primarch":
                triggers+=1
            if kind==22 and "unknown token script" in text.lower() and ASTARTES_STEM in text.lower():
                unknown+=1
        output.append({"seed":row["seed"],"hero_seat":hero,
                       "won":int(not row.get("draw") and row.get("winner_seat")==hero),
                       "draw":bool(row.get("draw")),"turns":row.get("turns"),
                       "astartes_created":astartes,"pestilence_activations":pest,
                       "mortarion_trigger_events":triggers,"unknown_astartes_notes":unknown,
                       "chain":row["replay_chain"]})
    if sum(x["unknown_astartes_notes"] for x in output):
        raise ValueError("Unresolved Astartes token script remains")
    summary={"schema":"gorge-mortarion-pilot-strategy-v1","policy":pilot,
             "games":len(output),"wins":sum(x["won"] for x in output),
             "astartes_token_events":sum(x["astartes_created"] for x in output),
             "astartes_games":sum(x["astartes_created"]>0 for x in output),
             "mortarion_trigger_events":sum(x["mortarion_trigger_events"] for x in output),
             "pestilence_activations":sum(x["pestilence_activations"] for x in output),
             "pestilence_games":sum(x["pestilence_activations"]>0 for x in output),
             "pestilence_and_astartes_games":sum(x["pestilence_activations"]>0 and x["astartes_created"]>0 for x in output),
             "games_detail":output}
    return summary


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--folder",type=Path,required=True)
    p.add_argument("--policy",required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=analyze(args.folder,args.policy)
    args.out.write_text(json.dumps(result,sort_keys=True)+"\n")
    print("MORTARION_PILOT_STRATEGY "+json.dumps({k:v for k,v in result.items() if k!="games_detail"},sort_keys=True))

if __name__=="__main__":
    main()
