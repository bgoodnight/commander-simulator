"""Compare authoritative Gorge pilot recordings without publishing to Deck Lab.

Read only native events and source outcomes. These reports describe observed
actions, not intended strategy or counterfactual decision quality.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

HIGHLIGHTS={11:"cast",23:"land",34:"activated",55:"mana ability",
            67:"activated",79:"activated",88:"activated",
            27:"trigger",38:"trigger",46:"trigger",54:"trigger",
            72:"trigger",80:"trigger",16:"attackers declared",
            17:"blockers declared",5:"damage",19:"game over"}
CAST=11
ABILITY={34,55,67,79,88}
TRIGGER={27,38,46,54,72,80}


def game_summary(record, native):
    if native.get("schema")!="gorge-native-trace-v1" or native.get("seed")!=record["seed"]:
        raise ValueError("Wrong native recording")
    if native.get("chain")!=record["replay_chain"] or native.get("decks")!=record["decks"]:
        raise ValueError("Native log failed source chain/deck verification")
    if not record.get("finished") or not record.get("replay_verified") or record.get("error"):
        raise ValueError("Unverified game")
    hero=record["hero_seat"]
    if native.get("hero_seat")!=hero:
        raise ValueError("Incorrect hero seat")
    identities={}
    for obj in native.get("objects",[]):
        if isinstance(obj,dict):
            name=obj.get("card_name") or obj.get("effective_name")
            if name and isinstance(obj.get("object_id"),int):
                identities[obj["object_id"]]=name
    turns=[]
    current={"number":0,"active_seat":None,"actions":[]}
    totals=Counter()
    for e in native["log"]["events"]:
        kind=e.get("kind")
        if kind==9:
            if current["actions"]:
                turns.append(current)
            current={"number":e.get("amount"),"active_seat":e.get("player",0),"actions":[]}
        if kind not in HIGHLIGHTS:
            continue
        seat=e.get("player",0)
        # Native attackers events designate defending player; they do not
        # establish who attacked or how many creatures attacked.
        if kind in (16,17):
            continue
        if seat!=hero or kind==19:
            continue
        card=identities.get(e.get("obj")) or (e.get("text") if kind==11 else None)
        action={"seq":e["seq"],"kind":HIGHLIGHTS[kind],"turn":current["number"]}
        if card:
            action["card"]=card
        if kind==5 and isinstance(e.get("amount"),int):
            action["amount"]=e["amount"]
        current["actions"].append(action)
        totals[HIGHLIGHTS[kind]]+=1
    if current["actions"]:
        turns.append(current)
    plays=[a for t in turns for a in t["actions"] if a["kind"]=="cast"]
    ability=[a for t in turns for a in t["actions"] if a["kind"]=="activated"]
    outcomes={"win":not record["draw"] and record["winner_seat"]==hero,
              "draw":record["draw"],"loss":not record["draw"] and record["winner_seat"]!=hero}
    return {"seed":record["seed"],"hero_seat":hero,"decks":record["decks"],
            "policy":record["policies"][hero],
            "chain":record["replay_chain"],
            "outcome":next(k for k,v in outcomes.items() if v),
            "turns":record["turns"],
            "casts":totals["cast"],"activations":totals["activated"],
            "triggers":totals["trigger"],"lands":totals["land"],
            "first_cast":plays[0] if plays else None,
            "first_ability":ability[0] if ability else None,
            "source_actions":turns}


def summarize(directory,deck,policy):
    root=Path(directory)
    records=[json.loads(line) for line in (root/"outcomes.jsonl").read_text().splitlines() if line.strip()]
    if len(records)!=10:
        raise ValueError("Expected ten verified narratives")
    games=[]
    for row in records:
        raw=root/"native"/f"gorge-seed-{row['seed']}.json"
        games.append(game_summary(row,json.loads(raw.read_text())))
    data={"schema":"gorge-pilot-narrative-v1","deck":deck,"policy":policy,"games":games}
    (root/"narrative.json").write_text(json.dumps(data,separators=(",",":"))+"\n")
    return data


def compare(left,right):
    a={g["seed"]:g for g in left["games"]}
    b={g["seed"]:g for g in right["games"]}
    matched=sorted(set(a)&set(b))
    if not matched:
        raise ValueError("No matched verified seeds")
    rows=[]
    for seed in matched:
        x,y=a[seed],b[seed]
        if x["decks"]!=y["decks"] or x["hero_seat"]!=y["hero_seat"]:
            raise ValueError("Same seed has non-comparable pod or seat")
        def first_actions(game):
            out=[]
            for turn in game["source_actions"]:
                for act in turn["actions"]:
                    if act["kind"] in ("cast","activated","land","trigger"):
                        out.append({k:act[k] for k in ("turn","kind","card") if k in act})
                if len(out)>=8: break
            return out[:8]
        rows.append({"seed":seed,"opponents":[deck for i,deck in enumerate(x["decks"]) if i!=x["hero_seat"]],
                     "seat":x["hero_seat"],"bot_outcome":x["outcome"],
                     "forge_outcome":y["outcome"],"bot_casts":x["casts"],
                     "forge_casts":y["casts"],"bot_activations":x["activations"],
                     "forge_activations":y["activations"],
                     "bot_first_actions":first_actions(x),
                     "forge_first_actions":first_actions(y)})
    return {"deck":left["deck"],"matched":len(matched),"bot_total":len(a),
            "forge_total":len(b),
            "bot_wins":sum(g["outcome"]=="win" for g in a.values()),
            "forge_wins":sum(g["outcome"]=="win" for g in b.values()),
            "discordant":[r for r in rows if r["bot_outcome"]!=r["forge_outcome"]],
            "matched_games":rows}


def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="mode",required=True)
    one=sub.add_parser("summarize")
    one.add_argument("directory");one.add_argument("deck");one.add_argument("policy")
    both=sub.add_parser("compare")
    both.add_argument("folder");both.add_argument("deck")
    args=p.parse_args()
    if args.mode=="summarize":
        report=summarize(args.directory,args.deck,args.policy)
        print("NARRATIVE_SOURCE",json.dumps({"deck":args.deck,"policy":args.policy,
                                             "games":len(report["games"])}))
        return
    base=Path(args.folder)
    def load(policy):
        return json.loads((base/args.deck/policy/"narrative.json").read_text())
    report=compare(load("bot"),load("forge-heuristic"))
    print("NARRATIVE_COMPARE",json.dumps(report,separators=(",",":")))
    with open(base/"comparison.jsonl","a") as f:
        f.write(json.dumps(report,separators=(",",":"))+"\n")
    print("Matched",args.deck,report["matched"],"bot wins",report["bot_wins"],
          "forge wins",report["forge_wins"],"outcome changes",len(report["discordant"]))


if __name__=="__main__":
    main()
