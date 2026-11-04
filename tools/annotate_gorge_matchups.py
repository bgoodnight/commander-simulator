"""Attach verified deck metadata to Gorge results without altering source rows."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from tools.commander_deck_library import load_library, matchup_annotations, validate_pod

def annotate_result(row, library, hero, opponents, hashes):
    keys=row.get("decks")
    seat=row.get("hero_seat")
    if (not isinstance(keys,list) or len(keys)!=4 or type(seat)!=int
            or seat not in range(4) or keys[seat]!=hero):
        raise ValueError("Missing or incorrect designated player seat")
    validate_pod(library,hero,opponents)
    if any(k not in opponents for i,k in enumerate(keys) if i!=seat):
        raise ValueError("Custom or unregistered deck appeared in opponent seat")
    if len(set(keys))!=4:
        raise ValueError("A deck was used twice in one pod")
    if not all(k in hashes for k in keys):
        raise ValueError("Missing deck fingerprint")
    return {
        "schema":"gorge-matchup-observation-v1",
        "seed":row["seed"],
        "source_game":row,
        "player_seat":seat,
        "player_deck":hero,
        "seat_metadata":[{
            **annotation,"seat":i,"deck_sha256":hashes[keys[i]]
        } for i,annotation in enumerate(matchup_annotations(library,keys))],
        "metadata_version":library["metadata_version"],
        "outcome":{
            "finished":row.get("finished"),
            "replay_verified":row.get("replay_verified"),
            "winner_seat":row.get("winner_seat"),
            "draw":row.get("draw"),
            "player_won":bool(row.get("finished") and
                              row.get("winner_seat")==seat and
                              not row.get("draw")),
        },
        "analysis_note":"One row per multiplayer pod; opponent archetypes/colors co-occur and are not independent matchups."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--runs",type=Path,required=True)
    p.add_argument("--pod",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    config=json.loads(args.pod.read_text())
    library=load_library()
    rows=[json.loads(line) for line in args.runs.read_text().splitlines() if line.strip()]
    result=[annotate_result(row,library,config["hero"],
                            config["opponent_pool"],config["deck_sha256"])
            for row in rows]
    if len({x["seed"] for x in result})!=len(result):
        raise ValueError("Duplicate seeds")
    args.out.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in result))
    print(json.dumps({"annotated":len(result),"player":config["hero"]}))

if __name__=="__main__":
    main()
