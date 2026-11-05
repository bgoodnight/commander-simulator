"""Analyze all archived native Magnus outcomes by hero pilot.

Descriptive win/loss associations only; no causal attribution. Every feature
comes from an authoritative Gorge event or verified native object crosswalk.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import statistics

# Pinned Gorge append-only event IDs and zone IDs.
MOVE, DRAW, DAMAGE, TURN, MANA, ATTACK, LAND, CAST = 2, 3, 5, 9, 13, 16, 23, 11
HAND, STACK, COMMAND = 1, 5, 6
COMMANDER="Magnus the Red"

def analyze(root:Path, policy:str):
    root=Path(root)
    rows=[json.loads(x) for x in (root/"runs.jsonl").read_text().splitlines() if x.strip()]
    if len(rows)!=100 or len({r.get("seed") for r in rows})!=100:
        raise ValueError("Expected 100 distinct Magnus games")
    features=[]
    for row in rows:
        hero=row.get("hero_seat")
        if (not row.get("finished") or not row.get("replay_verified") or row.get("error") or
            type(hero) is not int or hero not in range(4) or row["decks"][hero]!="magnus_budget" or
            row["policies"][hero]!=policy):
            raise ValueError(f"Invalid game seed={row.get('seed')}")
        source=json.loads((root/"native"/f"gorge-seed-{row['seed']}.json").read_text())
        if (source.get("seed")!=row["seed"] or source.get("chain")!=row["replay_chain"] or
            source.get("decks")!=row["decks"] or source.get("schema")!="gorge-native-trace-v1"):
            raise ValueError(f"Native source mismatch seed={row['seed']}")
        objs={o["object_id"]:o for o in source.get("objects",[]) if isinstance(o,dict)}
        counts=Counter()
        played_cards=Counter()
        types=Counter()
        turn_index=0
        commander_first=None
        opening_hand_count=None
        for snap in source.get("snapshots",[]):
            if isinstance(snap,dict) and opening_hand_count is None and isinstance(snap.get("players"),list):
                seats=snap["players"]
                if hero<len(seats):
                    zones=seats[hero].get("zones",{})
                    opening_hand_count=len(zones.get("hand",[]))
        for event in source["log"]["events"]:
            k=event.get("kind")
            if k==TURN:
                turn_index+=1
            if k==DRAW and event.get("player")==hero:
                counts["cards_drawn_events"]+=1
            if k==LAND and event.get("player")==hero:
                counts["lands_played"]+=1
            if k==MANA and event.get("player")==hero:
                counts["mana_add_events"]+=1
                counts["mana_added_units"]+=max(0,event.get("amount",0))
            if k==ATTACK and event.get("ids"):
                own=set(i for i in event["ids"] if objs.get(i,{}).get("owner")==hero)
                if own: counts["attacking_creature_declarations"]+=len(own)
            if k==DAMAGE and event.get("obj") in objs and objs[event["obj"]].get("owner")==hero:
                counts["damage_events_from_owned_objects"]+=1
            if k==CAST and event.get("to")==STACK and event.get("from") in (HAND,COMMAND):
                obj=objs.get(event.get("obj"),{})
                if obj.get("owner")!=hero or obj.get("is_token"):
                    continue
                name=obj.get("card_name") or obj.get("effective_name")
                if not name: continue
                counts["casts_from_hand_or_command"]+=1
                played_cards[name]+=1
                typetext=" ".join(obj.get("types_at_end") or []).lower()
                if "instant" in typetext or "sorcery" in typetext:
                    counts["instant_sorcery_casts"]+=1
                if "creature" in typetext:
                    counts["creature_casts"]+=1
                if "artifact" in typetext:
                    counts["artifact_casts"]+=1
                if name==COMMANDER:
                    counts["magnus_casts"]+=1
                    if commander_first is None:commander_first=turn_index or None
        features.append({"seed":row["seed"],"won":bool(row.get("winner_seat")==hero and not row.get("draw")),
                         "draw":bool(row.get("draw")),"turns":row.get("turns"),
                         "hero_seat":hero,"opponents":[row["decks"][i] for i in range(4) if i!=hero],
                         "commander_first_global_turn":commander_first,
                         "opening_hand_at_first_snapshot":opening_hand_count,
                         "counts":dict(counts),"cards_cast":dict(played_cards)})
    return summarize(policy,features)

def summarize(policy,features):
    groups={"wins":[r for r in features if r["won"]],
            "nonwins":[r for r in features if not r["won"]]}
    metrics=["casts_from_hand_or_command","instant_sorcery_casts","creature_casts",
             "artifact_casts","cards_drawn_events","lands_played","mana_add_events",
             "mana_added_units","magnus_casts","attacking_creature_declarations"]
    aggregated={}
    for name,group in groups.items():
        aggregated[name]={"games":len(group),
            "means":{k:round(statistics.mean(r["counts"].get(k,0) for r in group),2) if group else None for k in metrics},
            "magnus_cast_games":sum(r["counts"].get("magnus_casts",0)>0 for r in group),
            "mean_turns":round(statistics.mean(r["turns"] for r in group),2) if group else None}
    by_card=defaultdict(lambda:{"wins":0,"nonwins":0,"casts_wins":0,"casts_nonwins":0})
    for r in features:
        key="wins" if r["won"] else "nonwins"
        for card,n in r["cards_cast"].items():
            by_card[card][key]+=1
            by_card[card]["casts_"+key]+=n
    cards=[{"card":card,**values} for card,values in by_card.items()]
    cards.sort(key=lambda r:(r["wins"]+r["nonwins"],r["wins"]),reverse=True)
    by_opponent=defaultdict(lambda:Counter())
    for r in features:
        for opp in r["opponents"]:
            by_opponent[opp]["games"]+=1
            by_opponent[opp]["wins"]+=int(r["won"])
    return {"schema":"gorge-magnus-native-winloss-v1","pilot":policy,
            "sample_size":len(features),"wins":len(groups["wins"]),"draws":sum(r["draw"] for r in features),
            "groups":aggregated,"cards":cards[:45],
            "opponents":{n:dict(c) for n,c in sorted(by_opponent.items())},
            "metric_limits":[
                "LandPlayed and Draw are events, not inferred card names.",
                "Casts from hand/command use PutOnStack events (kind=11) with source zone and owner crosswalk; stolen cards and special copy-casts may be missed.",
                "Card type is from the final object crosswalk and may not reflect temporary copy/transform status at cast time.",
                "Winner-vs-loser means are descriptive and confounded by game duration, opponents, and survival; they are not estimates of causal effects.",
                "No evidence of spell costs paid, Wizard triggers, damage to opponents, or mana spent without an explicit event-specific validation.",
                "Recorded 'turns' is the game outcome turn measure, not necessarily Magnus's personal turn count.",
            ]}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--policy",required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=analyze(a.root,a.policy)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("MAGNUS_ANALYSIS "+json.dumps({k:v for k,v in report.items() if k!="cards"},sort_keys=True))
    print("MAGNUS_CARDS "+json.dumps(report["cards"][:15],sort_keys=True))
