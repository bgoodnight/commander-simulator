"""Conservative time-indexed Gorge event feature extraction.

Kind IDs are audited against native-compatible exported Gorge replay examples;
native event JSON is authoritative. This module records observed EVENTS, not
mana efficiency, spell payment, sacrifice mechanics or causal contributions.

A cast card's immutable owner is not necessarily its spell caster. Therefore
owner-attributed card casts are explicitly labeled as such; hero actions are
not inferred from owner, missing player (seat 0 omitempty), or end controller.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

# Reviewed from canonical Gorge replay export: source kind_id -> event name.
KINDS = {
    11:"cast", 13:"mana", 23:"land_played", 31:"token_created",
    34:"ability_activated", 27:"trigger", 5:"damage",
}
FEATURE_KIND = {
    "pod_cast_events": 11,
    "pod_mana_events": 13,
    "pod_land_play_events": 23,
    "pod_token_creation_events": 31,
    "pod_ability_activation_events": 34,
    "pod_trigger_events": 27,
    "pod_damage_events": 5,
}
# Explicitly NOT supported until event/intent semantics are audited:
# sacrifices, net mana, discounts, hero-controlled actions, actual mana paid.

def event_features(native:dict, hero_seat:int, cutoffs:tuple[int,...]=(4,8,12)) -> list[dict]:
    if native.get("schema") != "gorge-native-trace-v1":
        raise ValueError("Unsupported source schema")
    if type(hero_seat) is not int or hero_seat not in range(4):
        raise ValueError("Invalid hero seat")
    events=(native.get("log") or {}).get("events")
    objects=native.get("objects")
    snapshots=native.get("snapshots")
    if not isinstance(events,list) or not isinstance(objects,list) or not isinstance(snapshots,list):
        raise ValueError("Missing authoritative source events, objects or snapshots")
    lookup={}
    for obj in objects:
        oid=obj.get("object_id")
        if type(oid) is not int or oid in lookup:
            raise ValueError("Invalid/duplicate object ID")
        lookup[oid]=obj

    prev=-1
    for e in events:
        if type(e) is not dict or type(e.get("seq")) is not int or e["seq"]<=prev or type(e.get("kind")) is not int:
            raise ValueError("Invalid or unordered event sequence/kind")
        prev=e["seq"]
    by_turn={}
    prev_turn=-1
    prev_boundary=-1
    for s in snapshots:
        turn,seq=s.get("turn"),s.get("after_event_seq")
        if (type(turn) is not int or turn<=prev_turn or type(seq) is not int
            or seq<=prev_boundary or seq>prev):
            raise ValueError("Invalid snapshot cutoff or ordering")
        if s.get("boundary") not in (None,"first_pending_decision_of_turn"):
            raise ValueError("Unrecognized snapshot type")
        by_turn[turn]=seq
        prev_turn,prev_boundary=turn,seq

    output=[]
    for turn in cutoffs:
        if type(turn) is not int or turn<1: raise ValueError("Invalid requested turn")
        boundary=by_turn.get(turn)
        row={"landmark_global_turn":turn, "landmark_observed":boundary is not None,
             "event_cutoff_seq":boundary,
             "evidence_event_sequences":{},
             "hero_owned_card_cast_events":None,
             "hero_owned_card_cast_unique_cards":None,
             "hero_owned_cast_card_names":None,
             "hero_owned_cast_attribution_complete":None,
             "sacrifice_event_count":None,
             "hero_mana_generated":None,
             "hero_spell_cost_reduction":None}
        for feat in FEATURE_KIND:
            row[feat]=None
        if boundary is None:
            output.append(row)
            continue
        # Absolute source event seq; no post-cutoff leakage.
        eligible=[e for e in events if e["seq"]<=boundary]
        counts=Counter(e["kind"] for e in eligible)
        for feat,kind in FEATURE_KIND.items():
            row[feat]=counts.get(kind,0)
            row["evidence_event_sequences"][feat]=[e["seq"] for e in eligible if e["kind"]==kind]
        hero_cast=[]
        unknown=0
        for e in eligible:
            if e["kind"]!=KINDS_INV_CAST: continue
            oid=e.get("obj")
            obj=lookup.get(oid) if type(oid) is int else None
            if obj is None or type(obj.get("owner")) is not int:
                unknown+=1
                continue
            if obj["owner"]==hero_seat:
                hero_cast.append((e["seq"],obj.get("card_name") or obj.get("effective_name")))
        row["hero_owned_cast_attribution_complete"]=unknown==0
        if unknown==0:
            row["hero_owned_card_cast_events"]=len(hero_cast)
            row["hero_owned_card_cast_unique_cards"]=len(set(name for _,name in hero_cast if name))
            row["hero_owned_cast_card_names"]=sorted({name for _,name in hero_cast if name})
        row["evidence_event_sequences"]["hero_owned_card_cast_events"]=[seq for seq,_ in hero_cast]
        output.append(row)
    return output

KINDS_INV_CAST=11


def extract_root(root:Path,hero:str,cutoffs:tuple[int,...]=(4,8,12)) -> list[dict]:
    records=[]
    seen=set()
    files=sorted(root.rglob("runs.jsonl"))
    if not files:raise ValueError("Missing source runs.jsonl")
    for runfile in files:
        for line in runfile.read_text().splitlines():
            if not line.strip():continue
            run=json.loads(line)
            seed,seat=run.get("seed"),run.get("hero_seat")
            decks=run.get("decks")
            if (type(seat) is not int or seat not in range(4) or
                not isinstance(decks,list) or len(decks)!=4 or decks[seat]!=hero):
                continue
            if type(seed) is not int or seed in seen:
                raise ValueError("Duplicate or invalid seed in hero source")
            seen.add(seed)
            src=runfile.parent/"native"/f"gorge-seed-{seed}.json"
            if not src.is_file():
                for turn in cutoffs:
                    records.append({"seed":seed,"hero":hero,"native_available":False,
                                    "landmark_global_turn":turn,"landmark_observed":False})
                continue
            native=json.loads(src.read_text())
            if (native.get("seed")!=seed or native.get("decks")!=decks or
                native.get("chain")!=run.get("replay_chain") or native.get("hero_seat")!=seat):
                raise ValueError("Native identity mismatch")
            for feat in event_features(native,seat,cutoffs):
                records.append({"seed":seed,"hero":hero,"native_available":True,**feat})
    if not records:raise ValueError("No hero games in source")
    return records


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-root",type=Path,required=True)
    p.add_argument("--hero",required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--landmarks",default="4,8,12")
    a=p.parse_args()
    turns=tuple(int(x) for x in a.landmarks.split(","))
    data=extract_root(a.native_root,a.hero,turns)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    # This output contains private card names, evidence and must be retained
    # only in a trusted private analysis directory, never public artifacts.
    a.output.write_text("".join(json.dumps(row,sort_keys=True)+"\n" for row in data))
    observed=[r for r in data if r.get("landmark_observed")]
    print(json.dumps({"schema":"gorge-event-features-v0",
                      "hero":a.hero,"rows":len(data),"observed":len(observed),
                      "owner_attribution_complete":sum(r.get("hero_owned_cast_attribution_complete") is True for r in observed),
                      "pod_cast_events":sum(r.get("pod_cast_events") or 0 for r in observed),
                      "status":"exploratory_event_counts_only"},sort_keys=True))


if __name__=="__main__":
    main()
