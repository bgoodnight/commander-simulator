"""Attribute failed target announcements using the exact reversal event.

The immediately preceding MoveZone 'reversed' is a stronger association
than a prior unrelated PutOnStack. Keep unresolved cases explicit.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from collections import Counter

def audit(root,hero):
    runs=[json.loads(x) for x in (root/"runs.jsonl").read_text().splitlines() if x.strip()]
    for run in runs:
        native=json.loads((root/"native"/f"gorge-seed-{run['seed']}.json").read_text())
        objects={o["object_id"]:o for o in native["objects"]}
        events=native["log"]["events"]
        names=Counter()
        seqs=[]
        for i,e in enumerate(events):
            if e["kind"]!=22 or e.get("text")!="cast aborted: no legal target":continue
            last=[ev for ev in events[max(0,i-6):i] if ev["kind"]==2 and ev.get("text")=="reversed"]
            if not last:
                names["<no reversed card in prior 6 events>"]+=1
                continue
            rev=last[-1]
            o=objects.get(rev.get("obj"),{})
            name=o.get("card_name") or o.get("effective_name") or "<unnamed object>"
            names[name]+=1
            if len(seqs)<10:
                seqs.append({"warning_seq":e["seq"],"reverse_seq":rev["seq"],
                    "reversed_id":rev.get("obj"),"name":name,
                    "reversal_from":rev.get("from"),"reversal_to":rev.get("to")})
        print("TARGET_REVERSALS",json.dumps({"hero":hero,"seed":run["seed"],
            "sources_by_reversed_object":dict(names.most_common()),"samples":seqs},sort_keys=True))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--hero",required=True)
    a=p.parse_args()
    audit(a.root,a.hero)
