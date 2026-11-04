"""Evidence-based gorge UI replay export. No fabricated game-state snapshots.

The original gorge log remains authoritative. Public mode omits hidden zones
and private events by default. --include-hidden enables existing omniscient
recording for synthetic four-bot games; it never exports native bot intents.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
from tools.gorge_public_state import project

SCHEMA="gorge-ui-replay-v1"
KINDS={0:"game_start",1:"shuffle",2:"zone_change",3:"draw",
4:"life_change",5:"damage",6:"tap",7:"untap",8:"step_change",
9:"turn_change",10:"priority",11:"cast",12:"resolve",13:"mana",
14:"mana_clear",15:"counter_change",16:"attackers",17:"blockers",
18:"player_lost",19:"game_over",20:"decision_requested",
21:"decision_recorded",22:"note",23:"land_played",24:"targets",
27:"trigger",31:"token_created",
# These kinds were left as opaque native_NN strings by the original exporter.
# Names/ordinals below are pinned to gorge engine/events/event.go.
34:"ability_activated",38:"delayed_trigger",46:"keyword_trigger",
54:"granted_trigger",55:"mana_ability_activated",
67:"granted_ability_activated",72:"merged_trigger",
79:"gained_ability_activated",80:"gained_trigger",
88:"keyword_ability_activated"}
SKIP={1,8,10,14,20,21,28}


def convert(source, *, include_hidden=False):
    if (source.get("schema")!="gorge-native-trace-v1"
        or source.get("engine")!="gorge"
        or source.get("format")!="commander"):
        raise ValueError("Expected native gorge Commander recording")
    log=source.get("log") or {}
    events=log.get("events")
    if not isinstance(events,list) or not events or not isinstance(log.get("intents"),list):
        raise ValueError("Missing gorge event/intent records")
    if len(source.get("decks",[]))!=4 or len(source.get("policies",[]))!=4:
        raise ValueError("Expected four Commander seats")
    identity={}
    conflicts=set()
    previous=-1
    for event in events:
        seq,kind=event.get("seq"),event.get("kind")
        if type(seq) is not int or seq<=previous or type(kind) is not int or kind<0:
            raise ValueError("Unordered or malformed native events")
        previous=seq
        # Explicit native casting-event names are evidence, not inferred names.
        if kind==11 and (include_hidden or not event.get("secret")) and type(event.get("obj")) is int and isinstance(event.get("text"),str) and event["text"].strip():
            obj=str(event["obj"])
            name=event["text"].strip()
            if obj in identity and identity[obj]!=name:
                conflicts.add(obj)
            identity[obj]=name
    for obj in conflicts:
        identity.pop(obj,None)
    if include_hidden:
        # A native one-game crosswalk is necessary to name hidden draws,
        # opening hands and library identities. It is NOT emitted separately
        # as a native object catalog or reusable cross-game identity.
        for obj in source.get("objects",[]):
            if type(obj.get("object_id")) is not int:
                raise ValueError("Malformed omniscient object crosswalk")
            name=obj.get("card_name") or obj.get("effective_name")
            if not isinstance(name,str) or not name.strip():
                continue
            oid=str(obj["object_id"])
            if oid not in identity:
                identity[oid]=name
    turns=[]
    current=None
    hidden=0
    emitted=0
    for event in events:
        if event.get("secret") and not include_hidden:
            hidden+=1
            continue
        kind=event["kind"]
        if kind==9:
            current={"turn":event.get("amount"),"seat":event.get("player",0),
                     "events":[],"highlights":[],"counts":{}}
            turns.append(current)
        elif current is None:
            current={"turn":0,"seat":None,"events":[],"highlights":[],"counts":{}}
            turns.append(current)
        if kind in SKIP:
            continue
        row={"seq":event["seq"],"kind":KINDS.get(kind,"native_"+str(kind)),
             "kind_id":kind}
        for key in ("player","obj","amount","counter","from","to","text","ids"):
            if key in event:
                row[key]=event[key]
        obj=str(event.get("obj"))
        if obj in identity:
            row["card_name"]=identity[obj]
        if kind==11 and isinstance(event.get("text"),str):
            row["card_name"]=event["text"]
        current["events"].append(row)
        emitted+=1
    for turn in turns:
        turn["counts"]=dict(Counter(row["kind"] for row in turn["events"]))
        turn["event_count"]=len(turn["events"])
        turn["highlights"]=[
            {key:row[key] for key in ("seq","kind","card_name","text","amount","counter") if key in row}
            for row in turn["events"]
            if row["kind"] in ("draw","cast","land_played","token_created","damage","game_over",
                               "trigger","ability_activated","keyword_trigger",
                               "delayed_trigger","granted_trigger","merged_trigger",
                               "gained_trigger","mana_ability_activated",
                               "granted_ability_activated","gained_ability_activated",
                               "keyword_ability_activated")
        ][:12]
    safe_snapshots=project(source,include_hidden=include_hidden)
    return {
        "snapshots":safe_snapshots,
        "snapshot_definition":"first_pending_decision_of_turn" if safe_snapshots else None,
        "schema":SCHEMA,"engine":"gorge","seed":source.get("seed"),
        "chain":source.get("chain"),"decks":source["decks"],
        "policies":source["policies"],"turns":turns,
        "object_identity":identity,
        "source":{"schema":source["schema"],
                  "total_native_events":len(events),
                  "total_native_decisions":len(log["intents"]),
                  "exported_events":emitted,
                  "omitted_hidden_events":hidden,
                  "event_seq_preserved":True},
        "state":{"life":"turn_entry_snapshots" if safe_snapshots else None,
                 "hands":"named_turn_entry_snapshots" if safe_snapshots and include_hidden else None,
                 "libraries":"named_turn_entry_snapshots" if safe_snapshots and include_hidden else None,
                 "battlefields":"all_players_turn_entry_snapshots" if safe_snapshots else None,
                 "graveyards":"all_players_turn_entry_snapshots" if safe_snapshots else None,
                 "mana_pools":"turn_entry_snapshots" if safe_snapshots else None,
                 "counters":None,
                 "reason":("Synthetic omniscient replay: hidden names for all four players, from exact native card-object snapshots. Boundaries are turn entry, NOT turn end." if include_hidden and safe_snapshots else
                           "Turn-entry public state; private hand identities omitted." if safe_snapshots else
                           "Native snapshots were not captured.")},
        "visibility":"omniscient" if include_hidden else "public_events_only",
        "synthetic_simulation_only":bool(include_hidden),
        "limitations":[
            "Card names require explicit native card identity evidence.",
            "Highlights are actual events, not inferred actions.",
            "Snapshots are taken at the first decision of each turn, NOT at turn end.",
            "Opening hands and draws are sourced; mulligan count is not established by a single opening snapshot.",
            "Native gorge replay remains authoritative.",
        ],
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("inputs",nargs="+",type=Path)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--include-hidden",action="store_true")
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    for src in args.inputs:
        view=convert(json.loads(src.read_text()),include_hidden=args.include_hidden)
        dst=args.out/(src.stem+".ui.json")
        dst.write_text(json.dumps(view,ensure_ascii=False,separators=(",",":"))+"\n")
        print(dst,view["source"])


if __name__=="__main__":
    main()
