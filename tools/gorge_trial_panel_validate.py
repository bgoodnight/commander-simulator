"""Fail-closed preparation of an exact, experimental-only Gorge opponent pool."""
import argparse
import json
from pathlib import Path

def validate(queue, panel):
    if queue.get("schema")!="gorge-precon-qualification-queue-v1" or panel.get("schema")!="gorge-initial-trial-opponents-v1":
        raise ValueError("Invalid precon schema")
    if panel.get("approved_for_production") is not False or queue.get("oracle_bulk_sha256")!=panel.get("source_oracle_sha256"):
        raise ValueError("Wrong Oracle source or production approval")
    keys=panel["opponents"]; pinned=panel["pinned_decklists"]
    if not 3<=len(keys)<=20 or len(set(keys))!=len(keys) or set(pinned)!=set(keys):
        raise ValueError("Invalid proposed opponent pool")
    if any(panel["observed_by_hero"].get(h,0)<3 for h in ("mortarion_current","magnus_premium")):
        raise ValueError("Insufficient prior bounded observations")
    pool={d["key"]:d for d in queue["decks"]}
    for key in keys:
        row=pool.get(key)
        if not row or not row.get("oracle_complete") or row.get("active_opponent") or row["decklist_sha256"]!=pinned[key]:
            raise ValueError(f"{key}: unverified experimental precon")
    return keys

def main():
    p=argparse.ArgumentParser()
    for k in ("queue","panel","out"):p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    keys=validate(json.loads(a.queue.read_text()),json.loads(a.panel.read_text()))
    a.out.write_text(",".join(keys)+"\n")
    print(f"Prepared {len(keys)} experimental stock opponents; none production-certified.")

if __name__=="__main__":main()
