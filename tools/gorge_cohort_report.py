"""Precompute Gorge cohort statistics and exploratory elastic-net models.

Only fully verified game-level rows are used. No replay sampling enters the
denominator. No inferred card actions, p-values, or causal claims are produced.
"""
from __future__ import annotations
from collections import defaultdict
from math import exp, log, sqrt
import json
from pathlib import Path
from statistics import median

SCHEMA = "gorge-cohort-report-v1"
PLAYER_KEYS = ("mortarion_current", "magnus_budget",
               "necron_dynasties", "wretched_ranks")


def eligible(row):
    if (not isinstance(row, dict) or row.get("finished") is not True or
            row.get("replay_verified") is not True or
            type(row.get("seed")) is not int or
            not isinstance(row.get("decks"), list) or len(row["decks"]) != 4 or
            len(set(row["decks"])) != 4 or
            type(row.get("player_seat")) is not int or
            row["player_seat"] not in range(4)):
        return False
    hero = row["decks"][row["player_seat"]]
    if row.get("player_deck", hero) != hero:
        return False
    if row.get("draw") is True:
        return row.get("winner_seat") is None
    return type(row.get("winner_seat")) is int and row["winner_seat"] in range(4)


def outcome(row):
    return "draw" if row.get("draw") is True else (
        "win" if row["winner_seat"] == row["player_seat"] else "loss")


def round_number(value, digits=3):
    return round(value, digits) if value is not None else None


def wilson(wins, n):
    if not n:
        return None
    z = 1.96
    phat = wins/n
    denom = 1+z*z/n
    center = (phat+z*z/(2*n))/denom
    radius = z*sqrt((phat*(1-phat)+z*z/(4*n))/n)/denom
    return [round_number(max(0,center-radius), 4),
            round_number(min(1,center+radius), 4)]


def bucket(rows):
    n = len(rows)
    wins = sum(outcome(r) == "win" for r in rows)
    losses = sum(outcome(r) == "loss" for r in rows)
    draws = n-wins-losses
    lengths = [r["turns"] for r in rows
               if type(r.get("turns")) in (int, float) and r["turns"] >= 0]
    return {
        "n": n, "wins": wins, "losses": losses, "draws": draws,
        "win_rate": round_number(wins/n, 4) if n else None,
        "wilson_95": wilson(wins, n),
        "median_game_turns": round_number(median(lengths), 2) if lengths else None,
        "game_turns_coverage": len(lengths),
    }


def opponents(row):
    return [name for i,name in enumerate(row["decks"])
            if i != row["player_seat"]]


def source_tags(row, field):
    data = row.get("seat_metadata")
    if not isinstance(data, list) or len(data) != 4:
        return []
    tags = set()
    for i,meta in enumerate(data):
        if i == row["player_seat"]:
            continue
        if not isinstance(meta, dict) or meta.get("deck_key") != row["decks"][i]:
            continue
        if field == "colors":
            value = meta.get("color_identity", [])
        elif field == "archetypes":
            value = [meta.get("primary_archetype"), *meta.get("secondary_archetypes", [])]
        else:
            raise ValueError(field)
        if isinstance(value, list):
            tags.update(tag for tag in value if isinstance(tag,str) and tag)
    return sorted(tags)


def grouped(rows, category):
    groups = defaultdict(list)
    for row in rows:
        if category == "opponents":
            keys = opponents(row)
        elif category == "seats":
            keys = [str(row["player_seat"]+1)]
        elif category in ("archetypes", "colors"):
            keys = source_tags(row, category)
        elif category == "identities":
            keys = []
            metadata = row.get("seat_metadata")
            if isinstance(metadata, list) and len(metadata) == 4:
                for i, meta in enumerate(metadata):
                    if i == row["player_seat"] or not isinstance(meta, dict) or meta.get("deck_key") != row["decks"][i]:
                        continue
                    colors = meta.get("color_identity")
                    if isinstance(colors, list) and all(c in "WUBRG" for c in colors):
                        keys.append("".join(c for c in "WUBRG" if c in colors) or "Colorless")
        elif category == "pods":
            keys = [" / ".join(sorted(opponents(row)))]
        else:
            raise ValueError(category)
        for key in set(keys):
            groups[key].append(row)
    return [{"name":key, **bucket(group)} for key,group in groups.items()]


def sigmoid(t):
    if t>=0:
        q=exp(-min(t,700))
        return 1/(1+q)
    q=exp(max(t,-700))
    return q/(1+q)


def train(xs, ys, strength, iterations=60):
    """Coordinate-Newton elastic-net logistic regression, pure Python.

    Binary sparse predictors, unpenalized intercept, equal L1/L2 penalty.
    Updates use the exact conditional Bernoulli gradient and curvature,
    avoiding costly full-gradient passes on every iteration.
    """
    n=len(ys)
    p=len(xs[0])
    cols=[[i for i,x in enumerate(xs) if x[j]>0] for j in range(p)]
    weights=[0.0]*p
    base=min(max(sum(ys)/n,1e-5),1-1e-5)
    intercept=log(base/(1-base))
    logits=[intercept]*n
    probs=[base]*n
    lam1=strength*.5
    lam2=strength*.5
    for _ in range(iterations):
        # Intercept has no penalty.
        grad=sum(q-y for q,y in zip(probs,ys))/n
        hessian=max(sum(q*(1-q) for q in probs)/n,1e-8)
        delta=max(-2.0,min(2.0,-grad/hessian))
        intercept+=delta
        if delta:
            for i in range(n):
                logits[i]+=delta
                probs[i]=sigmoid(logits[i])
        largest=abs(delta)
        for j,indexes in enumerate(cols):
            if not indexes:
                continue
            gradient=sum(probs[i]-ys[i] for i in indexes)/n+lam2*weights[j]
            curvature=(sum(probs[i]*(1-probs[i]) for i in indexes)/n+lam2)
            if curvature<=0:
                continue
            proposal=weights[j]-gradient/curvature
            shrink=lam1/curvature
            updated=max(0,proposal-shrink) if proposal>=0 else min(0,proposal+shrink)
            change=max(-2.0,min(2.0,updated-weights[j]))
            if not change:
                continue
            weights[j]+=change
            largest=max(largest,abs(change))
            for i in indexes:
                logits[i]+=change
                probs[i]=sigmoid(logits[i])
        if largest<1e-6:
            break
    return intercept, weights


def log_loss(predicted, actual):
    z=min(max(predicted,1e-7),1-1e-7)
    return -(actual*log(z)+(1-actual)*log(1-z))


def regression(rows, family):
    # Draws are excluded from the binary win/loss model and explicitly counted.
    binary=[r for r in rows if outcome(r)!="draw"]
    wins=sum(outcome(r)=="win" for r in binary)
    n=len(binary)
    result={"method":"elastic-net logistic regression",
            "family":family,"n":n,"draws_excluded":len(rows)-n,
            "data_scope":"all verified cohort outcomes",
            "features_scope":"opponent presence and player seat only",
            "status":"insufficient_data"}
    if n<80 or min(wins,n-wins)<15:
        result["reason"]="Requires at least 80 decisive games, 15 wins and 15 losses."
        return result
    feature_sets=[]
    for r in binary:
        feature_sets.append(set(
            ["seat:"+str(r["player_seat"]+1)] if r["player_seat"] else []
        ).union(
            ("opponent:"+k for k in opponents(r)) if family=="opponents"
            else (family[:-1]+":"+k for k in source_tags(r,family))
        ))
    names=sorted({k for tags in feature_sets for k in tags})
    # Remove constants, whose coefficient cannot be distinguished from intercept.
    names=[key for key in names
           if 8<=sum(key in tags for tags in feature_sets)<=n-8]
    if not names:
        result["reason"]="No variable opponent or seating predictors."
        return result
    xs=[[float(k in tags) for k in names] for tags in feature_sets]
    ys=[int(outcome(r)=="win") for r in binary]
    # Seed-based held-out folds avoid using a game to evaluate its own fit.
    folds=[r["seed"]%3 for r in binary]
    candidate=(.008,.03,.1)
    scores=[]
    for strength in candidate:
        total=0.0
        for fold in range(3):
            tr=[i for i,v in enumerate(folds) if v!=fold]
            te=[i for i,v in enumerate(folds) if v==fold]
            if not tr or not te:
                continue
            intercept,coefs=train([xs[i] for i in tr],[ys[i] for i in tr],strength,60)
            total+=sum(log_loss(sigmoid(intercept+sum(w*v for w,v in zip(coefs,xs[i]))),ys[i])
                       for i in te)
        scores.append(total/n)
    best=min(range(len(candidate)),key=lambda j:scores[j])
    strength=candidate[best]
    intercept,coefs=train(xs,ys,strength,120)
    null=sum(log_loss(sum(ys)/n,y) for y in ys)/n
    result.update({
        "status":"ready","alpha":strength,"l1_ratio":.5,"folds":3,
        "cv_log_loss":round_number(scores[best],4),
        "null_log_loss":round_number(null,4),
        "baseline_win_rate":round_number(wins/n,4),
        "intercept":round_number(intercept,4),
        "predictors":[{"feature":name,"coefficient":round_number(coef,4),
                       "odds_ratio":round_number(exp(max(-10,min(10,coef))),3),
                       "games_exposed":sum(name in tags for tags in feature_sets)}
                      for name,coef in sorted(zip(names,coefs),key=lambda x:-abs(x[1]))],
        "limitations":"Exploratory penalized associations, not causal effects or significance tests. "
        "Opponent archetype, color and deck are correlated; models are separate by family. "
        "The same precon can appear with other opponents in four-player pods. "
        "CV log loss is an out-of-fold descriptive diagnostic, not an external validation."
    })
    result["features_scope"]=family+" present in pod, adjusted for player seat"
    return result


def make_report(games):
    if not isinstance(games,list):
        raise ValueError("Expected verified analytics games array")
    seeds=set()
    for row in games:
        if not eligible(row):
            raise ValueError("Invalid or unverified Gorge outcome in cohort")
        if row["seed"] in seeds:
            raise ValueError("Duplicate Gorge game seed")
        seeds.add(row["seed"])
    result={"schema":SCHEMA,"source_schema":"gorge-batch-analytics-v1",
            "total_verified_games":len(games),"decks":{},
            "scope":"All verified game outcomes. Detailed replay-derived card, life and state metrics are separate."}
    for key in sorted({r.get("player_deck",r["decks"][r["player_seat"]]) for r in games}):
        rows=[r for r in games
              if r.get("player_deck",r["decks"][r["player_seat"]])==key]
        groups={family:sorted(grouped(rows,family),
                 key=lambda g:(-g["n"],g["name"]))
                for family in ("opponents","pods","seats","archetypes","colors","identities")}
        models={family:regression(rows,family)
                for family in ("opponents","archetypes","colors")}
        result["decks"][key]={"player_deck":key,
             **bucket(rows),"groups":groups,"regressions":models,
             "game_turn_histogram": [{"turns": turn, "games": sum(r.get("turns") == turn for r in rows)}
                                     for turn in sorted({r["turns"] for r in rows if type(r.get("turns")) is int and r["turns"] >= 0})],
             "detailed_replay_count":sum(r.get("detailed_replay_retained") is True
                                          for r in rows)}
    return result


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    source=json.loads(a.input.read_text(encoding="utf-8"))
    if source.get("schema")!="gorge-batch-analytics-v1":
        raise ValueError("Not authoritative Gorge analytics")
    report=make_report(source["games"])
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,separators=(",",":"),sort_keys=True)+"\n",encoding="utf-8")
    print("Precomputed Gorge cohort:",report["total_verified_games"],"verified games")


if __name__=="__main__":
    main()
