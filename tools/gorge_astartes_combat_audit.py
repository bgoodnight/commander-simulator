"""Audit real archived Gorge traces for combat involvement of Astartes tokens.

Reads object crosswalk and native event IDs, never infers that a token attacked
from its creation, card name appearance in text, or a winning game.
"""
from __future__ import annotations
import argparse
import collections
import json
from pathlib import Path

K_DECLARE_ATTACKERS=16
K_DAMAGE=5
K_TOKEN_CREATE=31
ASTARTES_STEM="b_2_2_astartes_warrior_menace"


def audit(root:Path, pilot:str):
    root=Path(root)
    runs=[json.loads(x) for x in (root/"runs.jsonl").read_text().splitlines() if x.strip()]
    if len(runs)!=100:
        raise ValueError(f"Expected 100 verified games, got {len(runs)}")
    summary=collections.Counter()
    examples=[]
    for row in runs:
        if not row.get("finished") or not row.get("replay_verified") or row.get("error"):
            raise ValueError(f"Unverified game {row.get('seed')}")
        hero=row["hero_seat"]
        if row["policies"][hero]!=pilot or row["decks"][hero]!="mortarion_current":
            raise ValueError(f"Wrong pilot/deck for {row['seed']}")
        source=json.loads((root/"native"/f"gorge-seed-{row['seed']}.json").read_text())
        if source.get("chain")!=row["replay_chain"]:
            raise ValueError(f"Native chain mismatch {row['seed']}")
        tokens={int(o["object_id"]) for o in source["objects"]
                if o.get("is_token") and
                ("astartes" in (o.get("effective_name") or "").lower()
                 or "astartes" in (o.get("card_name") or "").lower())}
        created=sum(e.get("kind")==K_TOKEN_CREATE and e.get("text")==ASTARTES_STEM and e.get("player")==hero
                    for e in source["log"]["events"])
        # Every source-backed token object ID is checked against declarations,
        # which store attacker object IDs in the authoritative event.ids list.
        attacks=[]
        damage=[]
        for e in source["log"]["events"]:
            if e.get("kind")==K_DECLARE_ATTACKERS:
                attacks.extend(i for i in (e.get("ids") or []) if i in tokens)
            if e.get("kind")==K_DAMAGE and e.get("obj") in tokens:
                damage.append(e)
        if created:
            summary["games_with_astartes_created"]+=1
            summary["created_tokens"]+=created
        if attacks:
            summary["games_with_astartes_attacking"]+=1
            summary["attack_declarations"]+=len(attacks)
            summary["unique_astartes_declared"]+=len(set(attacks))
        if damage:
            summary["games_with_astartes_damage_events"]+=1
            summary["astartes_damage_events"]+=len(damage)
            summary["astartes_damage_amount_recorded"]+=sum(max(0,e.get("amount",0)) for e in damage)
        if created and len(examples)<12:
            examples.append({"seed":row["seed"],"created":created,
                             "astartes_objects":len(tokens),"attacking":len(attacks),
                             "distinct_attackers":len(set(attacks)),
                             "damage_events":len(damage),"won":row.get("winner_seat")==hero})
    return {"schema":"gorge-astartes-native-combat-audit-v1",
            "pilot":pilot,"games":len(runs),
            "metrics":dict(summary),"examples":examples,
            "attack_evidence":"kind=16 DeclareAttackers, ids includes token object id",
            "damage_evidence":"kind=5 Damage, obj references token object id",
            "caveat":"Damage events need source semantics checked before interpreting as player combat damage"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--policy",required=True)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=audit(a.root,a.policy)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print("ASTARTES_COMBAT_AUDIT "+json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
