"""Report private Gorge native field coverage without source values."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path

def audit(root,hero):
    families=("events","intents","objects","snapshots")
    fields={k:Counter() for k in families}
    counts=Counter()
    kind_counts=Counter()
    kind_fields=defaultdict(Counter)
    seen=set()
    for runfile in Path(root).rglob("runs.jsonl"):
        for line in runfile.read_text().splitlines():
            if not line.strip():continue
            run=json.loads(line)
            seat=run.get("hero_seat")
            decks=run.get("decks",[])
            if type(seat) is not int or len(decks)!=4 or decks[seat]!=hero:continue
            seed=run["seed"]
            if seed in seen:raise ValueError("duplicate seed")
            seen.add(seed)
            src=runfile.parent/"native"/f"gorge-seed-{seed}.json"
            if not src.exists():
                counts["missing_native"]+=1
                continue
            data=json.loads(src.read_text())
            if data.get("chain")!=run.get("replay_chain") or data.get("seed")!=seed:
                raise ValueError("source identity mismatch")
            counts["native_games"]+=1
            groups={"events":data["log"]["events"],"intents":data["log"]["intents"],
                    "objects":data["objects"],"snapshots":data["snapshots"]}
            for name,items in groups.items():
                counts[name]+=len(items)
                for item in items:
                    if not isinstance(item,dict):raise ValueError("bad source record")
                    fields[name].update(item)
                    if name=="events":
                        kind=item.get("kind")
                        kind_counts[str(kind)]+=1
                        kind_fields[str(kind)].update(item)
    if not seen:raise ValueError("no hero games")
    return {"schema":"gorge-native-schema-audit-v1","hero":hero,
            "attempts":len(seen),"counts":dict(counts),
            "fields":{k:dict(v) for k,v in fields.items()},
            "event_kinds":dict(kind_counts),
            "event_kind_fields":{k:dict(v) for k,v in kind_fields.items()},
            "private_values_excluded":True,"production_eligible":False}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--native-root",required=True)
    parser.add_argument("--hero",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    result=audit(args.native_root,args.hero)
    Path(args.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"hero":args.hero,"attempts":result["attempts"],
        "counts":result["counts"],"kind_count":len(result["event_kinds"])},sort_keys=True))
