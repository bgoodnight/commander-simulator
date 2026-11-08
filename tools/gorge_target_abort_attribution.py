"""Identify repeated Gorge cast proposals reversed for missing targets."""
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path

def audit(root,hero):
    runs=[json.loads(s) for s in (root/"runs.jsonl").read_text().splitlines() if s.strip()]
    out=[]
    for run in runs:
        data=json.loads((root/"native"/f"gorge-seed-{run['seed']}.json").read_text())
        objects={x["object_id"]:x for x in data["objects"]}
        events=data["log"]["events"]
        names=Counter()
        examples=defaultdict(list)
        for i,e in enumerate(events):
            if e.get("kind")!=22 or e.get("text")!="cast aborted: no legal target":continue
            candidate=None
            for previous in reversed(events[max(i-40,0):i]):
                if previous.get("kind")==11 and previous.get("obj") is not None:
                    candidate=previous
                    break
            if candidate is None:
                key="<no recent cast>"
            else:
                identity=objects.get(candidate["obj"]) or {}
                key=identity.get("card_name") or identity.get("effective_name") or "<unnamed card>"
            names[key]+=1
            if len(examples[key])<3:
                examples[key].append({"warning_seq":e.get("seq"),
                  "cast_seq":candidate.get("seq") if candidate else None,
                  "caster":candidate.get("player") if candidate else None,
                  "source_object":candidate.get("obj") if candidate else None})
        out.append({"seed":run["seed"],"aborted_casts_by_card":dict(names.most_common()),
                    "examples":dict(examples)})
    return {"hero":hero,"games":out,"note":"Nearest preceding cast is a diagnostic hypothesis, not definitive source attribution"}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--hero",required=True)
    a=p.parse_args()
    d=audit(a.root,a.hero)
    print("TARGET_ABORT_ATTRIBUTION",json.dumps(d,sort_keys=True))
