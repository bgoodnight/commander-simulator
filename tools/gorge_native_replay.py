"""Versioned, read-only index over gorge's full native event stream.

Never rewrite, reinterpret, or discard the original log/intent records.
This view gives our simulator UI bounded segments and event-family counts
without pretending a numeric game event supplies hidden card state.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path

GORGE_KINDS={
    0:"game_start",1:"shuffle",2:"move_zone",3:"draw",4:"life_change",
    5:"damage",6:"tap",7:"untap",8:"step_change",9:"turn_change",
    10:"priority",11:"put_on_stack",12:"resolve",13:"mana_add",
    14:"mana_clear",15:"counter_change",16:"declare_attackers",
    17:"declare_blockers",18:"player_lost",19:"game_over",
}
# This table is based on gorge's pinned engine/events/event.go. Events after
# 19 remain explicit numeric unknowns, never assigned guessed names.


def index_native_trace(payload):
    if not isinstance(payload,dict) or payload.get("schema")!="gorge-native-trace-v1":
        raise ValueError("Unknown or missing gorge native format")
    if payload.get("engine")!="gorge" or payload.get("format")!="commander":
        raise ValueError("Not a gorge Commander recording")
    log=payload.get("log")
    if not isinstance(log,dict) or not isinstance(log.get("events"),list):
        raise ValueError("Native event log is missing")
    names=payload.get("decks")
    policies=payload.get("policies")
    if not isinstance(names,list) or len(names)!=4 or not isinstance(policies,list) or len(policies)!=4:
        raise ValueError("Native recording lacks four seat identities and pilots")
    events=log["events"]
    sections=[]
    current=[]
    last_seq=-1
    def emit():
        if not current:
            return
        sections.append({
            "segment":len(sections),
            "start_seq":current[0]["seq"],
            "end_seq":current[-1]["seq"],
            "events":len(current),
            "kinds":dict(sorted(Counter(
                GORGE_KINDS.get(ev["kind"],"unknown_"+str(ev["kind"]))
                for ev in current).items())),
            "raw_event_range":[len(events_seen_before[0]),len(events_seen_before[0])+len(current)],
        })
        events_seen_before[0].extend(current)
    events_seen_before=[[]]
    for event in events:
        if not isinstance(event,dict):
            raise ValueError("Malformed event")
        seq=event.get("seq")
        kind=event.get("kind")
        if type(seq) is not int or seq<=last_seq or type(kind) is not int or kind<0:
            raise ValueError("Unsorted or malformed event stream")
        last_seq=seq
        if kind==9 and current:
            emit()
            current=[]
        current.append(event)
    emit()
    if len(events_seen_before[0])!=len(events):
        raise ValueError("Event partition is not lossless")
    return {
        "schema":"gorge-native-index-v1",
        "engine":"gorge",
        "seed":payload.get("seed"),
        "decks":names,"policies":policies,
        "chain":payload.get("chain"),
        "event_count":len(events),
        "intent_count":len(log.get("intents",[])),
        "segments":sections,
        "raw_record_retained":True,
        "interpretation":"A segment starts at a native TurnChange event; "
            "it is not a claim about a player's whole round. "
            "Raw gorge events and intents remain the source of truth.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--native-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    found={}
    for src in sorted(args.native_dir.glob("gorge-seed-*.json")):
        view=index_native_trace(json.loads(src.read_text()))
        dest=args.out/(src.stem+".index.json")
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(view,indent=2)+"\n")
        found[src.name]={"index":dest.name,"events":view["event_count"],
                         "segments":len(view["segments"])}
    print(json.dumps(found,indent=2))

if __name__=="__main__":
    main()
