"""Validate an enriched gorge source-of-truth replay before UI publication.

Full recordings include hidden hands and libraries. Validation results are
counts only; never publish the source replay to a public GitHub Pages asset.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path


def validate_trace(record):
    if record.get("schema")!="gorge-native-trace-v1" or record.get("enrichment_schema")!="gorge-physical-state-v1":
        raise ValueError("Not an enriched gorge-native-trace-v1 recording")
    if len(record.get("decks",[]))!=4 or len(record.get("policies",[]))!=4:
        raise ValueError("Expected four players with actual deck identities")
    if not isinstance(record.get("log"),dict) or not record["log"].get("events"):
        raise ValueError("Missing actual gorge events")
    objects=record.get("objects")
    snaps=record.get("snapshots")
    if not isinstance(objects,list) or len(objects)<400 or not isinstance(snaps,list) or not snaps:
        raise ValueError("Expected all dealt cards and authoritative snapshots")
    by_id={}
    for obj in objects:
        oid=obj.get("object_id")
        if type(oid)!=int or oid<=0 or oid in by_id:
            raise ValueError("Duplicate or invalid physical object ID")
        if not isinstance(obj.get("card_name"),str) or not isinstance(obj.get("effective_name"),str):
            raise ValueError("Missing type-safe printed/effective card labels")
        by_id[oid]=obj
    if set(range(1,401))-set(by_id):
        raise ValueError("Physical opening deck objects missing")
    if any(not by_id[i]["card_name"] for i in range(1,401)):
        raise ValueError("A printed card name is missing from the first four decks")
    turns=[]
    zone_counts=Counter()
    for snap in snaps:
        turn=snap.get("turn")
        if (type(turn)!=int or turn<1 or (turns and turn<=turns[-1])
                or snap.get("boundary")!="first_pending_decision_of_turn"
                or not isinstance(snap.get("after_event_seq"),int)
                or not isinstance(snap.get("players"),list)
                or len(snap["players"])!=4):
            raise ValueError("Invalid or out-of-order source snapshot")
        turns.append(turn)
        seen=set()
        for i,p in enumerate(snap["players"]):
            if p.get("seat")!=i or type(p.get("life"))!=int or not isinstance(p.get("lost"),bool):
                raise ValueError("Invalid life, seat, or elimination state")
            mana=p.get("mana_pool")
            if not isinstance(mana,list) or len(mana)!=6 or any(type(x)!=int or x<0 for x in mana):
                raise ValueError("Invalid authoritative six-color mana pool")
            zones=p.get("zones")
            if not isinstance(zones,dict):
                raise ValueError("Missing physical zones")
            for name in ("library","hand","battlefield","graveyard","exile","command"):
                contents=zones.get(name)
                if not isinstance(contents,list):
                    raise ValueError("Unrecorded physical zone: "+name)
                zone_counts[name]+=len(contents)
                for oid in contents:
                    if type(oid)!=int or oid not in by_id:
                        raise ValueError("Unknown object in physical zone")
                    # Owner-scoped representation may place a stolen creature
                    # in its controller's battlefield, but never duplicate it.
                    if oid in seen:
                        raise ValueError("Object appears in two physical zones")
                    seen.add(oid)
    if any(p["life"]!=40 for p in snaps[0]["players"]):
        raise ValueError("Commander game did not start at 40 life")
    return {
        "schema":"gorge-enrichment-validation-v1",
        "seed":record.get("seed"),
        "decks":record["decks"],
        "objects":len(by_id),
        "original_physical_cards":400,
        "turn_boundaries":len(turns),
        "first_turn":turns[0],
        "last_turn":turns[-1],
        "snapshot_definition":"first_pending_decision_of_turn",
        "source_events":len(record["log"]["events"]),
        "observed_zone_entries":dict(zone_counts),
        "note":"Validated omniscient source; do not publish hidden zones",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--native-dir",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    paths=sorted(args.native_dir.glob("gorge-seed-*.json"))
    if not paths:
        raise SystemExit("No enriched gorge traces available")
    results=[validate_trace(json.loads(p.read_text())) for p in paths]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({"games":results},indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"verified":len(results),"objects":[x["objects"] for x in results],
        "turn_boundaries":[x["turn_boundaries"] for x in results]}))


if __name__=="__main__":
    main()
