"""Reproducible coverage-oriented candidate selection from Oracle-enriched decklists.

Not an archetype classifier or Gorge certification. Uses observed card counts,
commander colors and release era. Retains source fidelity and all candidates.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import statistics
from pathlib import Path

FIELDS = (
    "creatures", "lands", "artifacts", "enchantments", "instants",
    "sorceries", "mana_rocks_proxy", "ramp_text_proxy",
    "draw_text_proxy", "removal_text_proxy", "counterspell_text_proxy",
    "token_text_proxy", "reanimation_text_proxy", "graveyard_text_proxy",
    "tutor_text_proxy", "sacrifice_text_proxy", "life_loss_text_proxy",
)
COLORS = "WUBRG"


def era(date):
    y = int(date[:4])
    return "2011-17" if y <= 2017 else "2018-21" if y <= 2021 else "2022-24" if y <= 2024 else "2025+"


def quantile(xs, q):
    a = sorted(xs)
    if not a:
        return None
    k = (len(a)-1)*q
    lo, hi = math.floor(k), math.ceil(k)
    return a[lo] + (a[hi]-a[lo])*(k-lo)


def normalized_features(rows):
    # Rank scaling is resistant to extreme one-off text-proxy counts.
    vectors={}
    for field in FIELDS + ("nonland_mean_mana_value",):
        raw={r["key"]:r.get("counts",{}).get(field) if field in FIELDS
             else r.get(field) for r in rows}
        values=sorted({x for x in raw.values() if isinstance(x,(int,float))})
        ranks={v:(i/(len(values)-1) if len(values)>1 else 0.5)
               for i,v in enumerate(values)}
        vectors[field]={k:ranks.get(v,0.5) for k,v in raw.items()}
    return vectors


def summary(rows):
    result={}
    for field in FIELDS + ("nonland_mean_mana_value",):
        values=[r.get("counts",{}).get(field) if field in FIELDS else r.get(field)
                for r in rows]
        vals=[v for v in values if isinstance(v,(float,int))]
        result[field]={
            "n":len(vals),"min":min(vals) if vals else None,
            "p10":quantile(vals,.1),"median":quantile(vals,.5),
            "p90":quantile(vals,.9),"max":max(vals) if vals else None,
            "positive":sum(v>0 for v in vals),
        }
    return result


def select(rows, panel_size=60):
    if panel_size<1:
        raise ValueError("Panel size must be positive")
    rows=sorted(rows,key=lambda x:x["key"])
    if panel_size>len(rows):
        raise ValueError("Cannot select more decks than unique candidate rows")
    color_counter=collections.Counter("".join(c for c in COLORS if c in r.get("color_identity",[])) or "C" for r in rows)
    eras=collections.Counter(era(r["release_date"]) for r in rows)
    vectors=normalized_features(rows)
    selected=[]
    diagnostics={}
    # At least one per color-identity group, where cardinality permits.
    color_groups=sorted(color_counter,key=lambda k:(color_counter[k],k))
    for ci in color_groups:
        if len(selected)>=panel_size:
            break
        candidates=[r for r in rows if ("".join(c for c in COLORS if c in r.get("color_identity",[])) or "C")==ci]
        # Prefer full source matching within a color group.
        best=max(candidates,key=lambda r:(r["card_name_coverage"],-int(r["release_date"][:4]),r["key"]))
        selected.append(best["key"])
    while len(selected)<panel_size:
        chosen=None
        for row in rows:
            k=row["key"]
            if k in selected:
                continue
            x=[vectors[f][k] for f in vectors]
            distances=[]
            for prior in selected:
                y=[vectors[f][prior] for f in vectors]
                d=math.sqrt(sum((a-b)**2 for a,b in zip(x,y))/len(x))
                distances.append(d)
            novelty=min(distances) if distances else 1.
            ci="".join(c for c in COLORS if c in row.get("color_identity",[])) or "C"
            ci_selected=sum(("".join(c for c in COLORS if c in r.get("color_identity",[])) or "C")==ci
                            for r in rows if r["key"] in selected)
            era_selected=sum(era(r["release_date"])==era(row["release_date"])
                             for r in rows if r["key"] in selected)
            color_need=max(0, panel_size*color_counter[ci]/len(rows)-ci_selected)
            era_need=max(0, panel_size*eras[era(row["release_date"])]/len(rows)-era_selected)
            # Light representation adjustments, strong coverage-completeness bonus.
            score=novelty + .035*color_need + .015*era_need + .07*row["card_name_coverage"]
            candidate=(score,row["card_name_coverage"],k)
            if chosen is None or candidate[:2]>chosen[:2] or (candidate[:2]==chosen[:2] and k<chosen[2]):
                chosen=candidate
        selected.append(chosen[2])
        diagnostics[chosen[2]]=round(chosen[0],5)
    by_key={r["key"]:r for r in rows}
    return [by_key[k] for k in selected], diagnostics


def report(payload, panel_size=60):
    if payload.get("schema")!="gorge-precon-card-metadata-enrichment-v1":
        raise ValueError("Wrong enrichment schema")
    unique=[r for r in payload.get("decks",[]) if not r["is_duplicate_variant"]]
    if len(unique)<100:
        raise ValueError("Expected at least 100 unique, released candidates")
    if any(r.get("active_opponent") for r in unique):
        raise ValueError("Enrichment must not activate opponent roles")
    if any(r.get("color_identity") is None for r in unique):
        raise ValueError("Cannot balance verified color identities with unresolved commanders")
    panel, scores=select(unique,panel_size)
    def color(r):
        return "".join(c for c in COLORS if c in r["color_identity"]) or "C"
    return {
        "schema":"gorge-opponent-selection-assessment-v1",
        "status":"provisional_not_gorge_qualified",
        "source_oracle_sha256":payload["oracle_bulk_sha256"],
        "source_catalog_commit":payload["source_catalog_commit"],
        "as_of":payload["as_of"],
        "candidate_count":len(unique),
        "target_panel_size":len(panel),
        "selection_method":"one color-identity anchor per present identity, then greedy max-min rank-normalized mechanic/type counts plus slight coverage/color/era balance; exploratory text proxies",
        "limitations":[
            "Not yet balanced on reviewed archetype classifications or pilot ability.",
            "Text proxies have imperfect sensitivity and specificity; rarity does not imply usefulness.",
            "Novelty ranking is a candidate triage aid, not predictive performance.",
            "Panel is not admitted to the active Gorge opponent library.",
        ],
        "all_candidate_feature_distribution":summary(unique),
        "panel_feature_distribution":summary(panel),
        "all_candidate_color_distribution":dict(sorted(collections.Counter(map(color,unique)).items())),
        "panel_color_distribution":dict(sorted(collections.Counter(map(color,panel)).items())),
        "all_candidate_era_distribution":dict(sorted(collections.Counter(era(r["release_date"]) for r in unique).items())),
        "panel_era_distribution":dict(sorted(collections.Counter(era(r["release_date"]) for r in panel).items())),
        "shortlist":[{"key":r["key"],"name":r["name"],"commander":r["commander"],
                      "colors":color(r),"era":era(r["release_date"]),
                      "card_name_coverage":r["card_name_coverage"],
                      "counts":r["counts"],"nonland_mean_mana_value":r["nonland_mean_mana_value"],
                      "selection_score":scores.get(r["key"])}
                     for r in panel],
        "unresolved_candidates":[{"key":r["key"],"name":r["name"],
                                  "cards_resolved":r["cards_resolved"]}
                                 for r in unique if r["cards_resolved"]<100],
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--enrichment",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--panel-size",type=int,default=60)
    args=p.parse_args()
    result=report(json.loads(args.enrichment.read_text()),args.panel_size)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "candidate_count":result["candidate_count"],
        "target_panel_size":result["target_panel_size"],
        "all_candidate_color_distribution":result["all_candidate_color_distribution"],
        "panel_color_distribution":result["panel_color_distribution"],
        "selected":len(result["shortlist"]),
        "unresolved_candidates":len(result["unresolved_candidates"]),
    },sort_keys=True))


if __name__=="__main__":
    main()
