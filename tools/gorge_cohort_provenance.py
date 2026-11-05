"""Bind future source-backed Gorge games to an immutable, pinned cohort identity.

Produces a new stamped JSONL; original native recordings and run summaries
are never rewritten or silently promoted to active analytics.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from tools.gorge_cohort_eligibility import IDENTITY_FIELDS, fingerprint


def stamp(rows, native_dir, cohort):
    if not isinstance(cohort,dict) or not isinstance(cohort.get("cohort_id"),str) or not cohort["cohort_id"]:
        raise ValueError("Missing cohort identity")
    for key in IDENTITY_FIELDS:
        if not isinstance(cohort.get(key),str) or not cohort[key]:
            raise ValueError(f"Missing pinned cohort source {key}")
    if not isinstance(rows,list) or not rows:
        raise ValueError("No games supplied")
    seen=set()
    stamped=[]
    for row in rows:
        seed=row.get("seed")
        if type(seed) is not int or seed in seen:
            raise ValueError("Duplicate or invalid native seed")
        seen.add(seed)
        names=row.get("decks")
        if not isinstance(names,list) or len(names)!=4 or len(set(names))!=4:
            raise ValueError("Invalid four-player lineup")
        if row.get("finished") is not True or row.get("replay_verified") is not True or row.get("error"):
            raise ValueError("Unverified outcome must remain diagnostic, not stamped warehouse data")
        if row.get("draw") is True and row.get("winner_seat") is not None:
            raise ValueError("Draw cannot have winner")
        if row.get("draw") is not True and (type(row.get("winner_seat")) is not int or row["winner_seat"] not in range(4)):
            raise ValueError("Decisive outcome lacks valid winner")
        native=(Path(native_dir)/f"gorge-seed-{seed}.json").read_bytes()
        source=json.loads(native)
        if (source.get("schema")!="gorge-native-trace-v1" or
                source.get("seed")!=seed or source.get("chain")!=row.get("replay_chain") or
                source.get("decks")!=names):
            raise ValueError("Native log and game summary disagree")
        if any(k in row for k in (*IDENTITY_FIELDS,"cohort_id","cohort_manifest_sha256")):
            raise ValueError("Input already contains cohort provenance: refuse restamping")
        stamped.append({**row, "cohort_id":cohort["cohort_id"],
                        **{k:cohort[k] for k in IDENTITY_FIELDS},
                        "cohort_manifest_sha256":fingerprint(cohort),
                        "source_sha256":hashlib.sha256(native).hexdigest()})
    return stamped


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--runs",required=True,type=Path)
    p.add_argument("--native-dir",required=True,type=Path)
    p.add_argument("--cohort",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    rows=[json.loads(line) for line in a.runs.read_text().splitlines() if line.strip()]
    cohort=json.loads(a.cohort.read_text())
    result=stamp(rows,a.native_dir,cohort)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("w") as f:
        for row in result:
            f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
    print(json.dumps({"stamped_verified_games":len(result),"cohort_id":cohort["cohort_id"]}))

if __name__=="__main__":
    main()
