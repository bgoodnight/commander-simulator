"""Detailed, source-backed token event/object attribution diagnostics.

Produce a compact per-hero report only; full original source remains in GitHub
run artifacts. This is a consistency audit, not an Oracle-rules certification.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path

def inspect(root:Path,hero:str):
    runs=[json.loads(s) for s in (root/"runs.jsonl").read_text().splitlines() if s.strip()]
    result=[]
    for run in runs:
        seed=run["seed"]
        native=json.loads((root/"native"/f"gorge-seed-{seed}.json").read_text())
        obj={o["object_id"]:o for o in native["objects"]}
        ev=native["log"]["events"]
        hero_seat=run["hero_seat"]
        all_tokens={k:o for k,o in obj.items() if o.get("is_token") is True}
        created={e.get("obj") for e in ev if e.get("kind")==31 and e.get("obj") in all_tokens}
        unexplained={k:o for k,o in all_tokens.items() if k not in created}
        named=Counter((o.get("effective_name") or o.get("card_name") or "unknown") for o in all_tokens.values())
        by_owner=Counter(str(o.get("owner")) for o in all_tokens.values())
        by_created=Counter((obj[e["obj"]].get("effective_name") or obj[e["obj"]].get("card_name") or "unknown")
                for e in ev if e.get("kind")==31 and e.get("obj") in obj)
        by_hero=Counter((o.get("effective_name") or o.get("card_name") or "unknown")
                for o in all_tokens.values() if o.get("owner")==hero_seat)
        unmatched=[]
        for oid,o in sorted(unexplained.items()):
            references=[i for i,e in enumerate(ev) if e.get("obj")==oid or
                (isinstance(e.get("ids"),list) and oid in e.get("ids"))]
            snippets=[]
            for i in references[:4]:
                snippets.extend({"seq":e.get("seq"),"kind":e.get("kind"),
                    "obj":e.get("obj"),"player":e.get("player"),"from":e.get("from"),
                    "to":e.get("to"),"text":str(e.get("text",""))[:140]}
                    for e in ev[max(0,i-1):min(len(ev),i+2)])
            unmatched.append({"object_id":oid,"name":o.get("effective_name") or o.get("card_name"),
                "owner":o.get("owner"),"controller_at_end":o.get("controller_at_end"),
                "event_references":len(references),"surrounding_events":snippets[:12]})
        token_event_missing_obj=sum(e.get("kind")==31 and e.get("obj") not in obj for e in ev)
        declared_non_token=sum(e.get("kind")==31 and e.get("obj") in obj
                               and obj[e["obj"]].get("is_token") is not True for e in ev)
        result.append({"seed":seed,"hero_seat":hero_seat,"finished":run.get("finished"),
          "events":len(ev),"intents":len(native["log"].get("intents",[])),
          "created_token_events":sum(e.get("kind")==31 for e in ev),
          "distinct_token_creation_object_ids":len(created),
          "token_objects":len(all_tokens),
          "token_name_counts":dict(named.most_common()),
          "hero_owned_token_names":dict(by_hero.most_common()),
          "token_owners_by_seat":dict(by_owner),
          "token_names_from_creation_events":dict(by_created.most_common()),
          "unmatched_token_objects":unmatched,
          "unresolved_token_event_objects":token_event_missing_obj,
          "non_token_creation_objects":declared_non_token})
    return {"schema":"gorge-native-token-diagnostics-v1","hero":hero,"games":result,
      "limitations":["Token generation observed in all four seats, not necessarily by the commander",
      "No mechanical cause/trigger/source attribution guaranteed by object name alone",
      "Created tokens may disappear between sampled snapshots; observation counts need not match creation",
      "An unmatched token could be made by copy/replacement rules or indicate omitted native events"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--hero",required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=inspect(a.root,a.hero)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("TOKEN_DIAGNOSTIC",json.dumps({"hero":a.hero,
      "games":len(result["games"]),
      "hero_tokens":sum(sum(x["hero_owned_token_names"].values()) for x in result["games"]),
      "unmatched_token_objects":sum(len(x["unmatched_token_objects"]) for x in result["games"]),
      "names":dict(sum((Counter(x["hero_owned_token_names"]) for x in result["games"]),Counter()))},sort_keys=True))
    for game in result["games"]:
        if game["unmatched_token_objects"]:
            print("TOKEN_UNMATCHED",json.dumps({"hero":a.hero,"seed":game["seed"],
               "objects":game["unmatched_token_objects"]},sort_keys=True))
if __name__=="__main__":main()
