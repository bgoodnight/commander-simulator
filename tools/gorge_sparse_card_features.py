"""Versioned, sparse card-exposure features from native Gorge traces.

Builds long-form positive evidence at exact global-turn snapshot boundaries.
Absence of a row means *no recorded evidence*, not proven absence of a card
from a deck or proof it was never drawn. No terminal crosswalk leakage into
time-dependent predictors: identity is consulted only for events/objects
observed by the cutoff. Card casts are attributed to card OWNER, never caster.

One pass over sorted events and snapshots; per-landmark work is proportional
to observed card evidence, not deck-size times all native events.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

SCHEMA = "gorge-sparse-card-exposure-v1"
CAST_KIND = 11
OBSERVABLE_ZONES = ("hand", "battlefield", "graveyard", "exile")
FEATURE_DEFS = {
    "observed_any": "Card had a native cast event or appeared in the hero's observed zones on or before this boundary",
    "observed_cast_event_count_owner": "Count of cast events for objects owned by hero (not necessarily cast by hero)",
    "observed_first_cast_seq_owner": "First sequenced cast event for hero-owned card; NOT an exact turn or pilot attribution",
    "observed_first_snapshot_global_turn": "Earliest captured turn-entry snapshot showing hero-owned card in a hero zone",
    "observed_hand_snapshot_count": "Number of captured turn-entry snapshots showing hero-owned card in hero hand",
    "observed_battlefield_snapshot_count": "Number of captured turn-entry snapshots showing hero-owned card on hero battlefield",
    "observed_graveyard_snapshot_count": "Number of captured turn-entry snapshots showing hero-owned card in hero graveyard",
    "observed_exile_snapshot_count": "Number of captured turn-entry snapshots showing hero-owned card in hero exile",
    "observed_hand_at_landmark": "1 if present in hero hand at the exact boundary, else 0 IF the boundary is observed",
    "observed_battlefield_at_landmark": "1 if present in hero battlefield at exact boundary, else 0 IF observed",
    "observed_zone_persistence_lower_bound": "Number of sampled boundaries with evidence; NOT actual duration",
}


def _card_name(obj: dict) -> str | None:
    name = obj.get("card_name") or obj.get("effective_name")
    return name if isinstance(name,str) and name.strip() else None


def extract_card_rows(native: dict, hero: int, run_attempt: str,
                      landmarks: tuple[int,...]=(4,8,12)) -> tuple[list[dict],dict]:
    if native.get("schema") != "gorge-native-trace-v1":
        raise ValueError("Wrong native schema")
    if type(hero) is not int or hero not in range(4):
        raise ValueError("Invalid hero seat")
    if not run_attempt or "/" in run_attempt:
        raise ValueError("Unsafe/missing run identity")
    seed = native.get("seed")
    if type(seed) is not int:
        raise ValueError("Missing native seed")
    events = (native.get("log") or {}).get("events")
    snaps = native.get("snapshots")
    objects = native.get("objects")
    if not all(isinstance(a,list) for a in (events,snaps,objects)):
        raise ValueError("Missing source evidence")

    lookup={}
    for obj in objects:
        if type(obj) is not dict or type(obj.get("object_id")) is not int:
            raise ValueError("Malformed object crosswalk")
        oid=obj["object_id"]
        if oid in lookup:
            raise ValueError("Duplicate object identity")
        lookup[oid]=obj
    seq_before=-1
    for e in events:
        if (not isinstance(e,dict) or type(e.get("seq")) is not int
            or e["seq"]<=seq_before or type(e.get("kind")) is not int):
            raise ValueError("Malformed or unordered source events")
        seq_before=e["seq"]
    snapshots={}
    before_t=0
    before_seq=-1
    for i,s in enumerate(snaps):
        t,seq=s.get("turn"),s.get("after_event_seq")
        if (type(t) is not int or t<=before_t or type(seq) is not int
            or seq<=before_seq or seq>seq_before):
            raise ValueError("Malformed/unsorted snapshot")
        if s.get("boundary") not in (None,"first_pending_decision_of_turn"):
            raise ValueError("Unsupported snapshot boundary")
        players=s.get("players")
        if not isinstance(players,list) or len(players)!=4:
            raise ValueError("Missing four-seat snapshot")
        snapshots[t]=(i,seq,players[hero])
        before_t,before_seq=t,seq

    # Build state once per observed snapshot, processing events only up to
    # that snapshot. No final-state card/controller or post-cutoff predictors.
    sorted_landmarks=sorted(set(landmarks))
    if any(type(t) is not int or t<1 for t in sorted_landmarks):
        raise ValueError("Invalid global-turn landmarks")
    card_state=defaultdict(lambda:{
        "cast_count":0,"first_cast_seq":None,"first_seen_turn":None,
        "hand_samples":0,"battlefield_samples":0,
        "graveyard_samples":0,"exile_samples":0,
    })
    first_unresolved_cast_seq=None
    unresolved_total=0
    unknown_owner_cast=0
    pointer=0
    rows=[]
    missing_landmarks=0
    for turn in sorted(snapshots):
        _,boundary,p=snapshots[turn]
        while pointer<len(events) and events[pointer]["seq"]<=boundary:
            e=events[pointer]
            pointer+=1
            if e["kind"]!=CAST_KIND:
                continue
            oid=e.get("obj")
            obj=lookup.get(oid) if type(oid) is int else None
            # An unknown cast identity may belong to the hero: don't
            # interpret absent card-specific casts as *known* zero.
            if obj is None or type(obj.get("owner")) is not int or not _card_name(obj):
                unresolved_total+=1
                if first_unresolved_cast_seq is None:
                    first_unresolved_cast_seq=e["seq"]
                continue
            if obj["owner"]!=hero:
                continue
            card=_card_name(obj)
            st=card_state[card]
            st["cast_count"]+=1
            if st["first_cast_seq"] is None:
                st["first_cast_seq"]=e["seq"]

        zones=(p.get("zones") or {})
        zone_seen={}
        for zone in OBSERVABLE_ZONES:
            ids=zones.get(zone)
            if not isinstance(ids,list):
                raise ValueError(f"Snapshot lacks {zone} zone")
            zset=set()
            for oid in ids:
                obj=lookup.get(oid) if type(oid) is int else None
                if obj is None:
                    raise ValueError("Snapshot object missing from crosswalk")
                if obj.get("owner")!=hero:
                    continue
                card=_card_name(obj)
                if card:
                    zset.add(card)
            zone_seen[zone]=zset
        for card in set.union(*zone_seen.values()):
            st=card_state[card]
            if st["first_seen_turn"] is None:
                st["first_seen_turn"]=turn
            for zone in OBSERVABLE_ZONES:
                if card in zone_seen[zone]:
                    st[zone+"_samples"]+=1

        if turn not in sorted_landmarks:
            continue
        # Restrict emitted rows to cards with evidence through this cutoff.
        # Future identity alone does not materialize an early card row.
        for card,st in sorted(card_state.items()):
            out={
                "schema":SCHEMA,
                "run_attempt":run_attempt,
                "seed":seed,
                "hero_seat":hero,
                "landmark_global_turn":turn,
                "source_event_seq":boundary,
                "card_name":card,
                "observed_any":1,
                "observed_cast_event_count_owner":st["cast_count"],
                "observed_first_cast_seq_owner":st["first_cast_seq"],
                "observed_first_snapshot_global_turn":st["first_seen_turn"],
                "observed_hand_snapshot_count":st["hand_samples"],
                "observed_battlefield_snapshot_count":st["battlefield_samples"],
                "observed_graveyard_snapshot_count":st["graveyard_samples"],
                "observed_exile_snapshot_count":st["exile_samples"],
                "observed_hand_at_landmark":int(card in zone_seen["hand"]),
                "observed_battlefield_at_landmark":int(card in zone_seen["battlefield"]),
                "observed_zone_persistence_lower_bound":sum(
                    st[z+"_samples"] for z in OBSERVABLE_ZONES),
                "cast_ownership_complete_through_landmark":unresolved_total==0,
                "meaning":"observed_evidence_only_not_deck_membership",
                "model_eligible":False,
            }
            rows.append(out)

    missing_landmarks=len([t for t in sorted_landmarks if t not in snapshots])
    summary={
        "schema":SCHEMA,"run_attempt":run_attempt,"seed":seed,
        "landmarks_requested":len(sorted_landmarks),
        "landmarks_observed":len(sorted_landmarks)-missing_landmarks,
        "sparse_feature_rows":len(rows),
        "unresolved_cast_events":unresolved_total,
        "first_unresolved_cast_seq":first_unresolved_cast_seq,
        "production_eligible":False,
    }
    return rows,summary


def process_folder(root:Path,hero:str,run_attempt:str,
                   landmarks:tuple[int,...]=(4,8,12))->dict:
    files=sorted(root.rglob("runs.jsonl"))
    if not files:
        raise ValueError("No source runs.jsonl")
    rows=[]
    game_summaries=[]
    seen=set()
    for runfile in files:
        for line in runfile.read_text().splitlines():
            if not line.strip():continue
            run=json.loads(line)
            seat=run.get("hero_seat")
            decks=run.get("decks")
            if (type(seat) is not int or seat not in range(4)
                or not isinstance(decks,list) or len(decks)!=4 or decks[seat]!=hero):
                continue
            seed=run.get("seed")
            if type(seed) is not int or seed in seen:
                raise ValueError("Duplicate or invalid hero game seed")
            seen.add(seed)
            path=runfile.parent/"native"/f"gorge-seed-{seed}.json"
            if not path.is_file():
                game_summaries.append({"seed":seed,"native_available":False,
                                       "sparse_feature_rows":0})
                continue
            native=json.loads(path.read_text())
            if (native.get("seed")!=seed or native.get("hero_seat")!=seat
                or native.get("decks")!=decks or native.get("chain")!=run.get("replay_chain")):
                raise ValueError("Native run identity mismatch")
            game_rows,summary=extract_card_rows(native,seat,run_attempt,landmarks)
            rows.extend(game_rows)
            summary["native_available"]=True
            game_summaries.append(summary)
    if not seen:
        raise ValueError("No games matching hero")
    return {"hero":hero,"run_attempt":run_attempt,"rows":rows,
            "games":game_summaries,"attempts":len(seen),
            "native_available":sum(g["native_available"] for g in game_summaries)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-root",required=True,type=Path)
    p.add_argument("--hero",required=True)
    p.add_argument("--run-attempt",required=True)
    p.add_argument("--landmarks",default="4,8,12")
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    payload=process_folder(args.native_root,args.hero,args.run_attempt,
                           tuple(int(t) for t in args.landmarks.split(",")))
    args.output.mkdir(parents=True,exist_ok=True)
    path=args.output/"card_exposures.jsonl"
    with path.open("w") as w:
        for row in payload["rows"]:
            w.write(json.dumps(row,sort_keys=True)+"\n")
    dictionary={
        "schema":SCHEMA,"features":FEATURE_DEFS,
        "absence_policy":"Sparse rows only contain observed positives. No row is not evidence of absence or of not-drawn.",
        "time_policy":"Exact first cast event seq; first snapshot global turn is sampled observation, not time-to-cast.",
        "scope":"private experimental native Gorge only",
        "production_eligible":False,
    }
    (args.output/"card_feature_dictionary.json").write_text(json.dumps(dictionary,indent=2,sort_keys=True)+"\n")
    report={k:v for k,v in payload.items() if k!="rows"}
    report["total_sparse_rows"]=len(payload["rows"])
    (args.output/"card_feature_coverage.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"hero":args.hero,"attempts":payload["attempts"],
                      "native_available":payload["native_available"],
                      "sparse_rows":len(payload["rows"]),
                      "experimental":True},sort_keys=True))


if __name__=="__main__":
    main()
