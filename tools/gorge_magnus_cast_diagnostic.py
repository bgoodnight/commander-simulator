"""Inspect real event schema without publishing hidden hands or card lists."""
from collections import Counter
import json
import sys
from pathlib import Path
root=Path(sys.argv[1])
p=next((root/"native").glob("gorge-seed-*.json"))
t=json.loads(p.read_text())
events=t["log"]["events"]
objs=t["objects"]
ids={o["object_id"]:o for o in objs}
kinds=Counter(e.get("kind") for e in events)
trans=Counter((e.get("from"),e.get("to")) for e in events if e.get("kind")==2)
src_examples=[]
for e in events:
    if e.get("kind") in (2,11,12,23):
        o=ids.get(e.get("obj"),{})
        src_examples.append({"kind":e.get("kind"),"from":e.get("from"),"to":e.get("to"),"player":e.get("player"),"id_found":bool(o),"owner":o.get("owner"),"token":o.get("is_token"),"name_present":bool(o.get("card_name")),"keys":sorted(e.keys())})
        if len(src_examples)>=16:break
print("GORGEMAGNUS_DIAGNOSTIC "+json.dumps({"seed":t["seed"],"events":len(events),"hero_seat":t["hero_seat"],"object_count":len(objs),"kind_counts":dict(kinds),"move_transitions":{str(k):v for k,v in trans.items()},"examples":src_examples},sort_keys=True))
