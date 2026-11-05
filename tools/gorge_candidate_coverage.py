"""Read-only descriptive coverage and diversity audit for stock Commander candidates.

The release eligibility cutoff is explicit and reproducible. Color identity,
archetype, card-type counts, interaction counts, and Gorge compatibility are
UNKNOWN until enriched from verified card metadata and behavior tests.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
from pathlib import Path

from tools.audit_gorge_candidate_catalog import validate_catalog, DEFAULT

BASICS=("Plains","Island","Swamp","Mountain","Forest","Wastes")
TARGET=60


def era(year):
    y=int(year)
    if y<=2017:return "2011-2017"
    if y<=2021:return "2018-2021"
    if y<=2024:return "2022-2024"
    return "2025+"


def jaccard(a,b):
    shared=len(a & b)
    union=len(a | b)
    return shared/union if union else 1.0


def profile(d):
    cards={r["name"]:r["count"] for r in d["cards"]}
    return {
        "key":d["key"],"name":d["name"],"commander":d["commander"],
        "release_date":d["release_date"],"release_era":era(d["release_date"][:4]),
        "set_code":d["set_code"],"source_type":"stock_precon_candidate",
        "unique_card_names":len(cards),
        "basic_land_counts":{n:cards.get(n,0) for n in BASICS},
        "basic_land_total":sum(cards.get(n,0) for n in BASICS),
        "card_list_sha256":hashlib.sha256(json.dumps(d["cards"],sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "color_identity":None,"primary_archetype":None,"secondary_archetypes":None,
        "functional_counts":None,"rules_coverage":None,"pilot_validated":False,
        "qualification":"not_evaluated",
    }


def make_report(catalog=DEFAULT, as_of="2026-11-05", shortlist=TARGET):
    validate_catalog(catalog)
    cutoff=datetime.date.fromisoformat(as_of)
    raw=json.loads(Path(catalog).read_text())
    released,future=[],[]
    for d in raw["decks"]:
        (released if datetime.date.fromisoformat(d["release_date"])<=cutoff else future).append(d)
    if not released:
        raise ValueError("No released candidates on the cutoff")
    profiles=[profile(d) for d in released]
    profile_map={p["key"]:p for p in profiles}
    card_sets={d["key"]:{c["name"] for c in d["cards"]} for d in released}
    names=collections.Counter(d["commander"] for d in released)
    years=collections.Counter(d["release_date"][:4] for d in released)
    eras=collections.Counter(era(d["release_date"][:4]) for d in released)
    card_freq=collections.Counter(c["name"] for d in released for c in d["cards"])
    basic_prevalence={x:sum(x in card_sets[d["key"]] for d in released) for x in BASICS}
    all_keys=sorted(card_sets)
    max_pairs=[]
    for i,key in enumerate(all_keys):
        for other in all_keys[i+1:]:
            overlap=jaccard(card_sets[key],card_sets[other])
            if overlap>=0.48:
                max_pairs.append({"deck_a":key,"deck_b":other,"jaccard":round(overlap,4)})
    max_pairs.sort(key=lambda r:(-r["jaccard"],r["deck_a"],r["deck_b"]))
    # Provisional *composition-diversity* shortlist; not a replacement for
    # stratified selection on verified color/archetype/behavioral attributes.
    selected=[]
    quotas=collections.Counter()
    target=min(shortlist,len(released))
    if target<1:raise ValueError("Shortlist target must be positive")
    # Establish an era anchor to avoid selecting only recent products.
    for label in ("2011-2017","2018-2021","2022-2024","2025+"):
        candidates=[p for p in profiles if p["release_era"]==label]
        if candidates and len(selected)<target:
            anchor=min(candidates,key=lambda p:p["key"])
            selected.append(anchor["key"]);quotas[label]+=1
    while len(selected)<target:
        best=None
        for p in profiles:
            key=p["key"]
            if key in selected:continue
            # Minimum Jaccard distance from selected panel rewards novelty.
            nearest=max(jaccard(card_sets[key],card_sets[s]) for s in selected) if selected else 0
            # Soft quota encourages release-era diversity; never claims true
            # game-mechanic, archetype, or color diversity.
            era_count=eras[p["release_era"]]
            target_share=target*era_count/len(released)
            shortage=max(0.0,target_share-quotas[p["release_era"]])/max(1,target_share)
            score=(1-nearest)+0.08*shortage
            candidate=(score,-nearest,key)
            if best is None or candidate[0]>best[0]+1e-12 or (abs(candidate[0]-best[0])<=1e-12 and key<best[2]):
                best=candidate
        chosen=best[2];selected.append(chosen);quotas[profile_map[chosen]["release_era"]]+=1
    return {
        "schema":"gorge-precon-descriptive-coverage-v1",
        "as_of":as_of,"source_commit":raw["source"]["commit"],
        "source_catalog_count":len(raw["decks"]),
        "released_count":len(released),"future_count":len(future),
        "future_decks":[{"key":d["key"],"name":d["name"],"release_date":d["release_date"]} for d in future],
        "unique_card_names":len(card_freq),"unique_commanders":len(names),
        "duplicate_commander_names":{n:k for n,k in sorted(names.items()) if k>1},
        "release_years":dict(sorted(years.items())),"release_eras":dict(sorted(eras.items())),
        "basic_land_prevalence":basic_prevalence,
        "caveat_basic_land_counts":"Basic lands do not determine Commander color identity; multicolor and nonbasic-only decks make such inference invalid.",
        "common_cards":card_freq.most_common(30),
        "high_overlap_deck_pairs":max_pairs[:40],
        "high_overlap_pair_count":len(max_pairs),
        "feature_completeness":{
            "decklist_and_commander":len(released),
            "release_date":len(released),
            "verified_color_identity":0,
            "reviewed_archetype":0,
            "verified_card_role_counts":0,
            "Gorge_qualified":0,
        },
        "shortlist_method":"provisional greedy max-min Jaccard diversity of card-name sets + release-era coverage; NOT final color/archetype balance",
        "provisional_shortlist_count":len(selected),
        "provisional_shortlist_release_eras":dict(sorted(quotas.items())),
        "provisional_shortlist":[profile_map[key] for key in selected],
        "released_profiles":profiles,
        "next_gate":"Enrich exact commander color identity and card Oracle metadata, derive reviewed mechanic labels, then optimize balanced coverage; validate Gorge before admitting opponents.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--catalog",type=Path,default=DEFAULT)
    p.add_argument("--as-of",default="2026-11-05")
    p.add_argument("--shortlist",type=int,default=TARGET)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=make_report(a.catalog,a.as_of,a.shortlist)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:report[k] for k in ("released_count","future_count","unique_card_names","unique_commanders","release_eras","provisional_shortlist_count","feature_completeness")},sort_keys=True))


if __name__=="__main__":main()
