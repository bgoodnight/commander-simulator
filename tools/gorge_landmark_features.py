"""Build source-backed turn-entry features from full Gorge native recordings.

No implicit future information; landmarks are GLOBAL turns, not hero turns.
Derived values are observations at the first pending decision, not turn-end.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

LANDS=frozenset(("Plains","Island","Swamp","Mountain","Forest","Wastes"))
ZONES=("hand","battlefield","graveyard","exile","command")


def features(native:dict, hero_seat:int, cutoffs:tuple[int,...]=(4,8,12)) -> list[dict]:
    if native.get("schema")!="gorge-native-trace-v1":
        raise ValueError("Wrong native schema")
    if type(hero_seat) is not int or hero_seat not in range(4):
        raise ValueError("Invalid hero seat")
    objects=native.get("objects")
    snaps=native.get("snapshots")
    if not isinstance(objects,list) or not isinstance(snaps,list):
        raise ValueError("Missing native object crosswalk or snapshots")
    lookup={}
    for obj in objects:
        oid=obj.get("object_id")
        if type(oid) is not int or oid in lookup:
            raise ValueError("Duplicate/invalid native object ID")
        lookup[oid]=obj
    evidence=[]
    prev_turn=-1
    prev_seq=-1
    for i,snap in enumerate(snaps):
        turn=snap.get("turn")
        seq=snap.get("after_event_seq")
        if type(turn) is not int or turn<=prev_turn or type(seq) is not int or seq<=prev_seq:
            raise ValueError("Unordered or invalid snapshot turn/sequence")
        prev_turn,prev_seq=turn,seq
        if snap.get("boundary") not in (None,"first_pending_decision_of_turn"):
            raise ValueError("Unrecognized snapshot boundary")
        players=snap.get("players")
        if not isinstance(players,list) or len(players)!=4:
            raise ValueError("Missing four-seat snapshot")
        p=players[hero_seat]
        zones=p.get("zones")
        if not isinstance(zones,dict):
            raise ValueError("Missing snapshot zones")
        field={"global_turn":turn,"source_snapshot_index":i,"source_event_seq":seq,
               "active_seat":snap.get("active_seat"),
               "hero_life":p.get("life"),"hero_lost":p.get("lost"),
               "hero_hand_count":None,"hero_battlefield_count":None,
               "hero_graveyard_count":None,"hero_basic_lands_on_battlefield":None,
               "hero_tokens_on_battlefield":None}
        valid=True
        for zone in ZONES:
            ids=zones.get(zone)
            if ids is not None:
                if not isinstance(ids,list) or any(type(oid) is not int or oid not in lookup for oid in ids):
                    raise ValueError("Unknown native object at snapshot")
        hand=zones.get("hand")
        board=zones.get("battlefield")
        grave=zones.get("graveyard")
        if isinstance(hand,list):field["hero_hand_count"]=len(hand)
        if isinstance(board,list):
            field["hero_battlefield_count"]=len(board)
            field["hero_basic_lands_on_battlefield"]=sum(lookup[oid].get("card_name") in LANDS for oid in board)
            field["hero_tokens_on_battlefield"]=sum(lookup[oid].get("is_token") is True for oid in board)
        if isinstance(grave,list):field["hero_graveyard_count"]=len(grave)
        evidence.append(field)
    output=[]
    for cutoff in cutoffs:
        if type(cutoff) is not int or cutoff<1:raise ValueError("Bad landmark cutoff")
        # Exact snapshot at this global turn: don't use a future snapshot
        # or carry forward a state that may have changed in the interval.
        chosen=next((s for s in evidence if s["global_turn"]==cutoff),None)
        row={"landmark_global_turn":cutoff,"landmark_observed":chosen is not None,
             "feature_observation_boundary":"first_pending_decision_of_turn",
             "is_pregame":False}
        for key in ("source_snapshot_index","source_event_seq","active_seat","hero_life",
                    "hero_lost","hero_hand_count","hero_battlefield_count",
                    "hero_graveyard_count","hero_basic_lands_on_battlefield",
                    "hero_tokens_on_battlefield"):
            row[key]=chosen[key] if chosen else None
        output.append(row)
    return output


def extract_root(root:Path, hero:str, cutoffs:tuple[int,...]=(4,8,12))->list[dict]:
    rows=[]
    found=list(root.rglob("runs.jsonl"))
    if not found:raise ValueError("No runs.jsonl found in native archive")
    for manifest in found:
        folder=manifest.parent
        for line in manifest.read_text().splitlines():
            if not line.strip():continue
            run=json.loads(line)
            decks=run.get("decks",[])
            seat=run.get("hero_seat")
            if type(seat) is not int or len(decks)!=4 or decks[seat]!=hero:
                continue
            path=folder/"native"/f"gorge-seed-{run['seed']}.json"
            if not path.is_file():
                # Keep missing source explicit; do not fabricate snapshot features.
                for t in cutoffs:
                    rows.append({"seed":run["seed"],"hero":hero,"landmark_global_turn":t,
                                 "landmark_observed":False,"native_available":False})
                continue
            native=json.loads(path.read_text())
            if (native.get("seed")!=run.get("seed") or native.get("chain")!=run.get("replay_chain")
                or native.get("decks")!=decks):
                raise ValueError(f"Run/native identity mismatch for seed {run.get('seed')}")
            for row in features(native,seat,cutoffs):
                rows.append({"seed":run["seed"],"hero":hero,"native_available":True,**row})
    if not rows:raise ValueError("No games for hero in native input")
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-root",type=Path,required=True)
    p.add_argument("--hero",required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--landmarks",default="4,8,12")
    a=p.parse_args()
    cutoffs=tuple(int(x) for x in a.landmarks.split(","))
    data=extract_root(a.native_root,a.hero,cutoffs)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text("".join(json.dumps(r,sort_keys=True)+"\n" for r in data))
    print(json.dumps({"hero":a.hero,"landmark_rows":len(data),
        "observed":sum(r.get("landmark_observed",False) for r in data),
        "status":"experimental_features_only"}))


if __name__=="__main__":
    main()
