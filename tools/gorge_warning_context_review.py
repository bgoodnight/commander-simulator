"""Compact audited warning contexts from retained Gorge native logs."""
import argparse,json
from collections import Counter
from pathlib import Path

TERMS=("cast aborted","TokenAttacking$","ChangeZone ignores","Play found no card")
def inspect(root,hero):
    runs=[json.loads(s) for s in (root/"runs.jsonl").read_text().splitlines() if s.strip()]
    result=[]
    for run in runs:
        trace=json.loads((root/"native"/f"gorge-seed-{run['seed']}.json").read_text())
        obj={x["object_id"]:x for x in trace["objects"]}
        events=trace["log"]["events"]
        counts=Counter()
        examples={}
        for i,event in enumerate(events):
            msg=str(event.get("text") or "")
            if event.get("kind")!=22 or not any(term in msg for term in TERMS):continue
            counts[msg]+=1
            if len(examples.get(msg,[]))>=4:continue
            context=[]
            for ev in events[max(0,i-7):i+3]:
                oid=ev.get("obj")
                o=obj.get(oid) if type(oid) is int else None
                context.append({"kind":ev.get("kind"),"seq":ev.get("seq"),"player":ev.get("player"),
                  "name":o.get("effective_name") if o else None,
                  "text":str(ev.get("text") or "")[:100]})
            examples.setdefault(msg,[]).append({"warning_seq":event["seq"],
                "object":obj.get(event.get("obj"),{}).get("effective_name"),
                "context":context})
        result.append({"seed":run["seed"],"counts":dict(counts),"examples":examples})
    return {"hero":hero,"games":result}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path);p.add_argument("--hero",required=True)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();r=inspect(a.root,a.hero)
    a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    for game in r["games"]:
        if game["counts"]:
            print("WARNING_CONTEXT",json.dumps({"hero":a.hero,**game},sort_keys=True))
if __name__=="__main__":main()
