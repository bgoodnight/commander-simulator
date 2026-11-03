"""Validate complete run-level observation JSONL before retaining a batch.

Does not infer missing events, actions, actor seats, object IDs, or card effects.
All records are source observations, not analysis-derived features.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(paths, *, expected_games, expected_rounds):
    paths=list(paths)
    if not paths or type(expected_games) is not int or expected_games<1:
        raise ValueError("Expected nonempty observation files and positive game count")
    total=0
    cohorts=set()
    for path in paths:
        rows=[json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines()]
        if len(rows)!=expected_games:
            raise ValueError("Incomplete observation cohort: "+str(path))
        seeds=set()
        cohort=None
        for row in rows:
            key=(row.get("deck_key"),row.get("deck_sha256"),
                 row.get("scenario"),row.get("pilot_style"),
                 row.get("provisional_mode"),row.get("requested_rounds"))
            seed=row.get("seed")
            rounds=row.get("completed_rounds")
            outcome=row.get("outcome")
            turns=row.get("turn_records")
            snapshots=row.get("state_snapshots")
            hist=row.get("life_history")
            hand=row.get("mulligan",{}).get("opening_hand")
            if (row.get("format")!="commander-game-observations-v1"
                    or row.get("schema_version")!=1
                    or row.get("requested_rounds")!=expected_rounds
                    or type(seed) is not int or seed<0 or seed in seeds
                    or type(rounds) is not int or rounds<1 or rounds>expected_rounds
                    or not isinstance(hand,list) or len(hand)!=7
                    or not isinstance(turns,list) or len(turns)!=rounds
                    or not isinstance(snapshots,list) or len(snapshots)!=rounds
                    or not isinstance(hist,list) or len(hist)!=rounds+1
                    or not isinstance(outcome,dict)
                    or outcome.get("completed_rounds")!=rounds
                    or any(not isinstance(t,dict) or t.get("turn")!=i
                           for i,t in enumerate(turns,1))
                    or any(not isinstance(s,dict) or s.get("turn")!=i
                           for i,s in enumerate(snapshots,1))
                    or any(not isinstance(h,dict) or h.get("round")!=i
                           for i,h in enumerate(hist))):
                raise ValueError("Invalid or incomplete authoritative observation record")
            if cohort is None:
                cohort=key
            if key!=cohort:
                raise ValueError("Mixed observation provenance in one file")
            seeds.add(seed)
        if cohort in cohorts:
            raise ValueError("Repeated observation cohort")
        cohorts.add(cohort)
        total+=len(rows)
    return {"files":len(paths),"games":total,"cohorts":len(cohorts)}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--expected-games",type=int,required=True)
    parser.add_argument("--expected-rounds",type=int,required=True)
    args=parser.parse_args(argv)
    result=validate(sorted(args.source.glob("*.jsonl")),
                    expected_games=args.expected_games,
                    expected_rounds=args.expected_rounds)
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
