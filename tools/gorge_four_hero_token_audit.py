"""Audit token creation in a bounded Gorge game batch without approving games.

Reports per-game counts and rule-risk indicators. Event kind 31 is source-native
token creation; exact object/event attribution is checked separately.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path

TOKEN_CREATED=31

def audit_folder(root:Path,hero:str)->dict:
    path=root/"runs.jsonl"
    runs=[json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not runs:raise ValueError("No games")
    records=[]
    for run in runs:
        seed=run["seed"]
        native_path=root/"native"/f"gorge-seed-{seed}.json"
        if not native_path.is_file():raise ValueError("Missing native trace")
        native=json.loads(native_path.read_text())
        if native.get("seed")!=seed or native.get("chain")!=run.get("replay_chain") or native.get("decks")!=run.get("decks"):
            raise ValueError("Source mismatch")
        if native.get("schema")!="gorge-native-trace-v1":raise ValueError("Unexpected trace schema")
        objects={obj["object_id"]:obj for obj in native["objects"]}
        if len(objects)!=len(native["objects"]):raise ValueError("Duplicate native objects")
        events=native["log"]["events"]
        kinds=Counter()
        errors=[]
        unknown_refs=0
        for event in events:
            kinds[str(event["kind"])]+=1
            if event["kind"]==TOKEN_CREATED:
                oid=event.get("obj")
                if oid is not None and oid not in objects:
                    unknown_refs+=1
                # Not all token creation kinds include one distinct object id:
                # avoid treating an absent obj as non-creation.
                if oid in objects and objects[oid].get("is_token") is False:
                    errors.append("token event refers to explicitly nontoken object")
        snapshots=native.get("snapshots") or []
        seen_token_objects=set()
        for snap in snapshots:
            for p in snap.get("players",[]):
                for zone,ids in (p.get("zones") or {}).items():
                    for oid in ids:
                        if oid not in objects:
                            raise ValueError("Snapshot references unknown object")
                        if zone=="battlefield" and objects[oid].get("is_token") is True:
                            seen_token_objects.add(oid)
        created=sum(event["kind"]==TOKEN_CREATED for event in events)
        tokens=sum(obj.get("is_token") is True for obj in objects.values())
        if not run.get("replay_verified"):errors.append("native replay not verified")
        if run.get("error"):errors.append("engine recorded error")
        records.append({"seed":seed,"finished":run.get("finished"),"replay_verified":run.get("replay_verified"),
          "turns":run.get("turns"),"token_creation_events":created,"token_objects":tokens,
          "token_objects_seen_on_board":len(seen_token_objects),"unknown_token_event_objects":unknown_refs,
          "event_kinds":dict(kinds),"issues":errors})
    return {"schema":"gorge-four-hero-token-qualification-v1","hero":hero,
      "games":len(records),"token_creation_events":sum(x["token_creation_events"] for x in records),
      "minted_token_objects":sum(x["token_objects"] for x in records),
      "tokens_observed_on_board":sum(x["token_objects_seen_on_board"] for x in records),
      "replay_verified":sum(x["replay_verified"] is True for x in records),
      "rules_risk_flags":sum(len(x["issues"]) for x in records),
      "token_event_count_not_equivalent_to_minted_objects":True,
      "manual_semantic_review_still_required":True,"experimental_not_approved":True,
      "by_game":records}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--hero",required=True)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    report=audit_folder(a.root,a.hero)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("by_game",)},sort_keys=True))
    if report["rules_risk_flags"]:raise SystemExit("Source integrity or token risk flags; review report")
if __name__=="__main__":main()
