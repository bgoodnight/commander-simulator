"""Exploratory hierarchical elastic-net discovery from real game observation sidecars.

Requires scikit-learn (analysis-only, not simulator dependency).
No random forest, tree screen, second unpenalized regression, or p-values.
Unknown/missing opening hands are rejected rather than coded as absent.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import random


FORMAT="commander-elastic-net-discovery-v1"
SOURCE="commander-game-observations-v1"


def read_observations(source):
    paths=sorted(Path(source).glob("*.jsonl"))+sorted(Path(source).glob("*.jsonl.gz"))
    if not paths:
        raise ValueError("No source observation JSONL files")
    rows=[]
    for path in paths:
        opener=gzip.open if path.suffix==".gz" else open
        with opener(path,"rt",encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
    for row in rows:
        if (row.get("format")!=SOURCE
                or not isinstance(row.get("mulligan"),dict)
                or not isinstance(row["mulligan"].get("opening_hand"),list)
                or len(row["mulligan"]["opening_hand"])!=7
                or type(row.get("seed")) is not int
                or not isinstance(row.get("opponent_roles"),dict)
                or not isinstance(row.get("outcome"),dict)):
            raise ValueError("Missing complete, authoritative observations")
    keys={(r["deck_key"],r["deck_sha256"],r["pilot_style"],
           r["provisional_mode"],r["requested_rounds"]) for r in rows}
    if len(keys)!=1:
        raise ValueError("Cannot model mixed deck, pilot, rules, or horizons")
    identities={(r["scenario"],r["seed"]) for r in rows}
    if len(identities)!=len(rows):
        raise ValueError("Duplicate scenario/seed observations")
    return rows


def features(row,landmark=0):
    """Every feature must be observed no later than its named landmark."""
    out={}
    hand=set(row["mulligan"]["opening_hand"])
    for card in hand:
        out["opening:"+card]=1.
    roles=Counter(row["opponent_roles"].values())
    for name,count in roles.items():
        out["opponent_count:"+str(name)]=float(count)
        out["opponent_present:"+str(name)]=1.
    if not landmark:
        return out
    hist=row["life_history"]
    snapshots=row["state_snapshots"]
    events=row["turn_records"]
    if len(hist)<=landmark or len(snapshots)<landmark or len(events)<landmark:
        raise ValueError("Landmark not observed in a surviving game")
    state=snapshots[landmark-1]
    turn=events[landmark-1]
    for key in ("hand","battlefield","graveyard"):
        if not isinstance(state.get(key),list):
            raise ValueError("Missing authoritative landmark zone")
        out["zone_size:"+key]=float(len(state[key]))
    for card in set(state["hand"]):
        out["hand_at_landmark:"+card]=1.
    for key in ("land_count","creature_count","mana_rock_count","hand_size"):
        if isinstance(turn.get(key),(int,float)):
            out["resource:"+key]=float(turn[key])
    life=hist[landmark].get("life_totals",{})
    if "0" in life:
        out["life:pilot"]=float(life["0"])
    for seat in ("1","2","3"):
        if seat in life:
            out["life:opponent_"+seat]=float(life[seat])
    actions=[x for t in events[:landmark] for x in t.get("events",[])]
    out["actions:draws"]=sum(x.get("type")=="draw" for x in actions)
    out["actions:casts"]=sum(str(x.get("type","")).endswith("_cast") for x in actions)
    out["actions:unsupported"]=sum(bool(x.get("unsupported_abilities")) for x in actions)
    return out


def design(rows,landmark=0,min_support=8,max_interactions=300):
    filtered=[]
    for r in rows:
        if landmark and r["completed_rounds"]<=landmark:
            continue  # Finished at/before landmark, not in the surviving risk set.
        if r["outcome"]["status"] not in ("win","loss","draw","unresolved"):
            continue
        filtered.append(r)
    feats=[features(r,landmark) for r in filtered]
    n=len(feats)
    seed_count=len({r["seed"] for r in filtered})
    candidates=sorted({name for row in feats for name in row})
    keep=[]
    for name in candidates:
        values=[row.get(name,0.) for row in feats]
        present_seeds={r["seed"] for r,value in zip(filtered,values) if value>0}
        if name.startswith("opening:"):
            # Kept-hand access repeats across matched scenarios. Require
            # independently sampled seeds on both sides of the indicator.
            if (len(present_seeds)<min_support
                    or seed_count-len(present_seeds)<min_support):
                continue
        elif (name.startswith("hand_at_landmark:")
              or name.startswith("opponent_present:")):
            # Opponent types and later card access can vary *within* a seed
            # across scenarios, so do not mistake per-seed presence for a
            # constant row-level predictor.
            if (len(present_seeds)<min_support
                    or sum(v>0 for v in values)<min_support
                    or sum(v<=0 for v in values)<min_support):
                continue
        elif max(values)-min(values)<1e-12:
            continue
        keep.append(name)
    # Interaction candidates have no outcome-dependent pre-screening.
    card=[k for k in keep if k.startswith("opening:") or k.startswith("hand_at_landmark:")]
    other=[k for k in keep if k.startswith("opponent_present:")]
    pairs=[]
    for a in card:
        for b in other:
            supported={r["seed"] for r,f in zip(filtered,feats)
                       if bool(f.get(a,0.)) and bool(f.get(b,0.))}
            support=len(supported)
            if min_support<=support<=seed_count-min_support:
                pairs.append((a,b,support))
    pairs.sort(key=lambda row:(-row[2],row[0],row[1]))
    parents={}
    for a,b,_ in pairs[:max_interactions]:
        key=a+" × "+b
        parents[key]=(a,b)
        for row in feats:
            row[key]=float(bool(row.get(a,0.)) and bool(row.get(b,0.)))
    names=keep+list(parents)
    matrix=[[row.get(k,0.) for k in names] for row in feats]
    outcomes=[int(r["outcome"]["status"]=="win") for r in filtered]
    return filtered,names,matrix,outcomes,parents


def _model(C,l1_ratio,seed):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(penalty="elasticnet",solver="saga",
                           C=C,l1_ratio=l1_ratio,max_iter=3000,
                           tol=0.002,random_state=seed))


def _hierarchical_fit(X,y,names,parents,*,C,l1_ratio,seed):
    """Remove interaction terms whose two main effects do not survive.

    Fits are exclusively elastic net. Strong heredity applies to retained
    interactions, without claiming constrained-penalty estimation.
    """
    import numpy as np
    active=list(range(len(names)))
    while True:
        fitted=_model(C,l1_ratio,seed).fit(X[:,active],y)
        coefs=dict(zip((names[i] for i in active),
                       fitted.steps[-1][1].coef_[0]))
        drop=[name for name in parents if name in coefs
              and abs(coefs[name])>1e-7
              and any(abs(coefs.get(p,0.))<=1e-7 for p in parents[name])]
        if not drop:
            return fitted,active,coefs
        to_drop=set(drop)
        active=[i for i in active if names[i] not in to_drop]


def analyze(rows,*,landmark=0,min_support=8,bootstrap=16):
    import numpy as np
    from sklearn.model_selection import GroupShuffleSplit,GroupKFold
    from sklearn.metrics import brier_score_loss
    from sklearn.exceptions import ConvergenceWarning
    import warnings
    deck=rows[0]["deck_key"]
    revision=rows[0]["deck_sha256"]
    result={"format":FORMAT,"schema_version":1,"deck_key":deck,
            "deck_sha256":revision,"landmark_round":landmark,
            "method":"hierarchical_elastic_net_logistic",
            "limitations":"Exploratory simulated-game associations, not causal effects or real Commander win rates.",
            "status":"insufficient_data","games":0,"independent_seeds":0,"findings":[]}
    cohort,names,matrix,y,parents=design(rows,landmark,min_support)
    groups=np.array([r["seed"] for r in cohort])
    result["games"]=len(cohort)
    result["independent_seeds"]=len(set(groups))
    result["win_count"]=sum(y)
    result["nonwin_count"]=len(y)-sum(y)
    result["candidate_main_effects"]=len(names)-len(parents)
    result["candidate_interactions"]=len(parents)
    if (len(set(groups))<20 or min(sum(y),len(y)-sum(y))<10
            or len(names)<2):
        result["reason"]="Need at least 20 independent seeds, 10 wins, 10 nonwins and two variable features"
        return result
    X=np.asarray(matrix,dtype=float)
    y=np.asarray(y,dtype=int)
    train,test=next(GroupShuffleSplit(n_splits=1,test_size=.25,
                                      random_state=1349).split(X,y,groups))
    if min(sum(y[train]),len(train)-sum(y[train]))<5:
        result["reason"]="Insufficient outcome events in seed-grouped training split"
        return result
    seeds_train=groups[train]
    splits=min(4,len(set(seeds_train)))
    # Transparent, nonparametric opponent-composition baseline: a smoothed
    # observed training win share for each three-seat composition. No ridge
    # or second regression model is fitted.
    prior=float(np.mean(y[train]))
    table_counts=defaultdict(lambda:[0,0])
    def composition(row):
        return tuple(sorted(row["opponent_roles"].values()))
    for i in train:
        record=table_counts[composition(cohort[i])]
        record[0]+=int(y[i])
        record[1]+=1
    baseline=np.asarray([
        (table_counts[composition(cohort[i])][0]+2*prior)/
        (table_counts[composition(cohort[i])][1]+2)
        for i in test],dtype=float)
    best=None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore",ConvergenceWarning)
        for C in (0.1,1.,5.):
            for ratio in (0.4,0.8):
                scores=[]
                for tr,va in GroupKFold(n_splits=splits).split(
                        X[train],y[train],seeds_train):
                    if len(set(y[train][tr]))<2:
                        continue
                    clf=_model(C,ratio,21).fit(X[train][tr],y[train][tr])
                    p=clf.predict_proba(X[train][va])[:,1]
                    scores.append(brier_score_loss(y[train][va],p))
                if scores:
                    score=float(np.mean(scores))
                    if best is None or score<best[0]:
                        best=(score,C,ratio)
        if best is None:
            result["reason"]="Could not form valid seed-grouped CV folds"
            return result
        _,C,ratio=best
        model,active,coefs=_hierarchical_fit(X[train],y[train],names,
            parents,C=C,l1_ratio=ratio,seed=17)
        predictions=model.predict_proba(X[test][:,active])[:,1]
    selected=[name for name in names if abs(coefs.get(name,0.))>1e-7]
    selections=defaultdict(int)
    directions=defaultdict(int)
    rng=random.Random(212)
    unique=sorted(set(seeds_train))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore",ConvergenceWarning)
        for i in range(bootstrap):
            sampled=[rng.choice(unique) for _ in unique]
            index=np.concatenate([train[seeds_train==v] for v in sampled])
            if len(set(y[index]))<2:
                continue
            _,_,fitted=_hierarchical_fit(X[index],y[index],names,parents,
                C=C,l1_ratio=ratio,seed=i+31)
            for name,value in fitted.items():
                if abs(value)>1e-7:
                    selections[name]+=1
                    directions[name]+=1 if value>0 else -1
    findings=[]
    for name in selected:
        j=names.index(name)
        findings.append({"feature":name,"coefficient":round(float(coefs[name]),5),
            "direction":"positive" if coefs[name]>0 else "negative",
            "selection_frequency":round(selections[name]/max(bootstrap,1),3),
            "direction_consistency":round(abs(directions[name])/max(selections[name],1),3),
            "observed_games":int(np.count_nonzero(X[:,j])),
            "observed_seeds":len({r["seed"] for r,v in zip(cohort,X[:,j]) if v>0}),
            "interaction_parents":list(parents[name]) if name in parents else []})
    findings.sort(key=lambda r:(-r["selection_frequency"],
                                -abs(r["coefficient"]),r["feature"]))
    result.update({"status":"ready","findings":findings,
        "selected_predictors":len(findings),"outer_test_games":len(test),
        "outer_test_seed_groups":len(set(groups[test])),
        "holdout_brier":round(float(brier_score_loss(y[test],predictions)),5),
        "opponent_baseline_brier":round(float(brier_score_loss(y[test],baseline)),5),
        "baseline_method":"smoothed empirical win share by three-opponent composition",
        "tuned_C":C,"tuned_l1_ratio":ratio,
        "bootstrap_repetitions":bootstrap,
        "validation":"Whole seed groups held out across scenarios; CV performed only on training seeds",
        "hierarchy":"Interactions lacking either selected parent main effect are discarded and the elastic net is refit"})
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--landmark",type=int,default=0)
    parser.add_argument("--min-support",type=int,default=8)
    parser.add_argument("--bootstrap",type=int,default=16)
    parser.add_argument("--engine-commit",default=None)
    args=parser.parse_args(argv)
    if args.landmark<0 or args.min_support<2 or args.bootstrap<1:
        parser.error("Nonnegative landmark and positive support/bootstrap required")
    rows=read_observations(args.source)
    report=analyze(rows,landmark=args.landmark,
                   min_support=args.min_support,bootstrap=args.bootstrap)
    if args.engine_commit is not None:
        if len(args.engine_commit)!=40 or any(c not in "0123456789abcdef" for c in args.engine_commit):
            parser.error("Engine commit must be a 40-character Git SHA")
        report["engine_commit"]=args.engine_commit
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({k:report.get(k) for k in
                      ("status","games","independent_seeds","selected_predictors",
                       "holdout_brier","opponent_baseline_brier")},indent=2))


if __name__=="__main__":
    main()
