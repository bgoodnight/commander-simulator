"""Summarize token recipe events, nearby token IDs and unsupported effects."""
import argparse,json
from collections import Counter
from pathlib import Path

def summarize(root,hero):
    runs=[json.loads(line) for line in (root/"runs.jsonl").read_text().splitlines() if line.strip()]
    games=[]
    for run in runs:
        trace=json.loads((root/"native"/f"gorge-seed-{run['seed']}.json").read_text())
        events=trace["log"]["events"]
        obj={o["object_id"]:o for o in trace["objects"]}
        tokens={k:o for k,o in obj.items() if o.get("is_token") is True}
        templates=Counter()
        following=Counter()
        warning_events=[]
        paired=0
        examples=[]
        for i,e in enumerate(events):
            if e["kind"]==31:
                recipe=str(e.get("text") or "<unspecified>")
                templates[recipe]+=1
                nearby=[x for x in events[i+1:i+5] if x.get("obj") in tokens and
                     x.get("kind") in (2,6,56)]
                if nearby:
                    paired+=1
                    t=tokens[nearby[0]["obj"]]
                    following[t.get("effective_name") or t.get("card_name") or "?"]+=1
                    if len(examples)<8:
                        examples.append({"seq":e.get("seq"),"recipe":recipe,
                          "next_token":t.get("effective_name"),"owner":t.get("owner"),
                          "next_kind":nearby[0]["kind"],"delta_seq":nearby[0]["seq"]-e["seq"]})
            if e["kind"]==22 and e.get("text"):
                warning_events.append(str(e["text"])[:180])
        hero_tokens=Counter(o.get("effective_name") or o.get("card_name") or "?"
             for o in tokens.values() if o.get("owner")==run["hero_seat"])
        games.append({"seed":run["seed"],"turns":run["turns"],
          "token_recipe_events":dict(templates.most_common()),
          "paired_to_subsequent_token_object":paired,
          "associated_token_names":dict(following.most_common()),
          "hero_owned_token_types":dict(hero_tokens.most_common()),
          "unsupported_effect_messages":dict(Counter(warning_events).most_common(12)),
          "token_event_examples":examples})
    total_recipes=sum((Counter(g["token_recipe_events"]) for g in games),Counter())
    total_hero=sum((Counter(g["hero_owned_token_types"]) for g in games),Counter())
    total_unsupported=sum((Counter(g["unsupported_effect_messages"]) for g in games),Counter())
    return {"hero":hero,"games":games,"summary":{
       "token_recipe_counts":dict(total_recipes.most_common()),
       "hero_owned_token_types":dict(total_hero.most_common()),
       "unsupported_effect_messages":dict(total_unsupported.most_common(20)),
       "adjacent_object_links":sum(g["paired_to_subsequent_token_object"] for g in games)},
       "limitations":"Association uses next-four native events, not definitive source trigger or Oracle conformity"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--hero",required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    res=summarize(a.root,a.hero)
    a.output.write_text(json.dumps(res,indent=2,sort_keys=True)+"\n")
    print("TOKEN_RULES_REVIEW",json.dumps({"hero":a.hero,**res["summary"]},sort_keys=True))
    for g in res["games"]:
        print("TOKEN_RULES_GAME",json.dumps({"hero":a.hero,"seed":g["seed"],
           "hero_token_types":g["hero_owned_token_types"],
           "creation_recipes":g["token_recipe_events"],
           "unsupported_effect_types":g["unsupported_effect_messages"]},sort_keys=True))
if __name__=="__main__":main()
