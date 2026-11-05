"""Validate the archived stock-precon *candidate* catalog without admitting opponents.

Candidate records are source-controlled observations, not Gorge rules support.
"""
from __future__ import annotations
import argparse
import collections
import json
from pathlib import Path

DEFAULT=Path(__file__).resolve().parents[1]/"data/gorge_stock_precon_candidates_v1.json"


def validate_catalog(path=DEFAULT, minimum=100):
    doc=json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("schema")!="gorge-stock-candidate-catalog-v1":
        raise ValueError("Incorrect catalog schema")
    source=doc.get("source", {})
    if not source.get("commit") or not source.get("file"):
        raise ValueError("Missing upstream provenance and immutable commit")
    decks=doc.get("decks",[])
    if len(decks)<minimum:
        raise ValueError(f"Only {len(decks)} valid catalog entries; need {minimum}")
    names=set()
    by_set=collections.Counter()
    by_year=collections.Counter()
    card_counts=collections.Counter()
    for d in decks:
        key=d.get("key")
        if not key or key in names:
            raise ValueError(f"Missing/duplicate candidate identity: {key}")
        names.add(key)
        if d.get("qualification")!="not_evaluated":
            raise ValueError(f"{key}: candidate catalog must not approve Gorge simulation")
        if d.get("provenance")!="stock_precon_candidate":
            raise ValueError(f"{key}: unsupported provenance")
        cards=d.get("cards")
        if not isinstance(cards,list) or not cards:
            raise ValueError(f"{key}: missing cards")
        quantities={}
        for card in cards:
            name,count=card.get("name"),card.get("count")
            if not name or type(count) is not int or count<=0 or name in quantities:
                raise ValueError(f"{key}: duplicate or invalid card quantity/name")
            quantities[name]=count
        if sum(quantities.values())!=100 or quantities.get(d.get("commander"))!=1:
            raise ValueError(f"{key}: wrong card count or commander")
        if not d.get("set_code") or not d.get("release_date"):
            raise ValueError(f"{key}: missing release metadata")
        by_set[d["set_code"]]+=1
        by_year[d["release_date"][:4]]+=1
        for c in cards:
            card_counts[c["name"]]+=1
    return {"schema":"gorge-candidate-catalog-audit-v1","candidates":len(decks),
            "source_commit":source["commit"],"set_count":len(by_set),
            "release_years":dict(sorted(by_year.items())),
            "unique_card_names":len(card_counts),
            "top_cards":card_counts.most_common(20),
            "status":"unqualified_candidates_no_simulation_admission"}


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--catalog",type=Path,default=DEFAULT)
    p.add_argument("--minimum",type=int,default=100)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    report=validate_catalog(a.catalog,a.minimum)
    payload=json.dumps(report,indent=2,sort_keys=True)+"\n"
    if a.output:a.output.write_text(payload,encoding="utf-8")
    print(payload)
