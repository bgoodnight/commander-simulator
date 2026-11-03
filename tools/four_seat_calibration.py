"""Reproducible four-active-seat calibration using the preserved v5 abstract engine.

Do not interpret the results as real Commander deck win rates. Every seat runs
an abstract 99-card category deck with mana, hand, creatures and interactions.
The physical deck engine is not part of these games.
"""
from __future__ import annotations
import argparse
import collections
import itertools
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "simulator" / "v5_four_player"
sys.path.insert(0, str(LEGACY))
from simulation import ARCHETYPES, Table  # noqa: E402

CORE = ("aggro", "control", "combo", "midrange")

def med(items):
    return statistics.median(items) if items else None

def run(games_per_mirror=20, games_per_rotation=4, limit=30, seed=20261103):
    if games_per_mirror < 1 or games_per_rotation < 1 or limit < 1:
        raise ValueError("Positive counts and rounds required")
    records = []
    def observe(kind, names, fixture_seed):
        game = Table(list(names), seed=fixture_seed).run(limit)
        row = game.summary()
        row["kind"] = kind
        row["turn_order"] = list(game.turn_order)
        # Preserve actual round-boundary observations for developmental metrics.
        row["round_history"] = game.turns
        records.append(row)
    for index, archetype in enumerate(ARCHETYPES):
        for rep in range(games_per_mirror):
            observe("mirror", (archetype,) * 4,
                    seed + 100000 + index * 10000 + rep)
    for rotation, names in enumerate(itertools.permutations(CORE)):
        for rep in range(games_per_rotation):
            observe("rotating_archetypes", names,
                    seed + 200000 + rotation * 10000 + rep)
    by_archetype = collections.defaultdict(lambda: collections.Counter())
    by_seat = collections.defaultdict(lambda: collections.Counter())
    by_order = collections.defaultdict(lambda: collections.Counter())
    by_mirror = collections.defaultdict(lambda: collections.Counter())
    ending = collections.defaultdict(list)
    development = collections.defaultdict(lambda: collections.defaultdict(list))
    for game in records:
        kind=game["kind"]
        ending[kind].append(game["ending_round"])
        positions={seat:i for i,seat in enumerate(game["turn_order"])}
        for seat, archetype in enumerate(game["archetypes"]):
            by_archetype[archetype]["exposures"]+=1
            by_seat[seat]["exposures"]+=1
            by_order[positions[seat]]["exposures"]+=1
            if kind=="mirror":
                by_mirror[archetype][f"exposure_{seat}"]+=1
            if game["winner"]==seat:
                by_archetype[archetype]["wins"]+=1
                by_seat[seat]["wins"]+=1
                by_order[positions[seat]]["wins"]+=1
                if kind=="mirror":
                    by_mirror[archetype][f"win_{seat}"]+=1
            for snap in game["round_history"]:
                if snap["round"] in (3,5,8,10):
                    player=snap["players"][seat]
                    for field in ("sources","creatures","power","engines","combo","hand","public_threat"):
                        development[archetype][(snap["round"],field)].append(player[field])
    def rates(counts):
        return {str(k): {**dict(v),"win_rate":round(v["wins"]/v["exposures"],4)}
                for k,v in sorted(counts.items())}
    out={
        "format":"four-active-abstract-calibration-v1",
        "provenance":"legacy simulator/v5_four_player; all seats are synthetic archetypes",
        "parameters":{"games_per_mirror":games_per_mirror,
                      "games_per_rotation":games_per_rotation,
                      "seed":seed,"max_rounds":limit},
        "games":len(records),
        "completed":sum(g["winner"] is not None for g in records),
        "median_completion_round":med([g["ending_round"] for g in records if g["ending_round"] is not None]),
        "wins_by_archetype":rates(by_archetype),
        "wins_by_seat":rates(by_seat),
        "wins_by_turn_order":rates(by_order),
        "mirror_seat_results":{k:dict(v) for k,v in sorted(by_mirror.items())},
        "median_development_by_role":{
            archetype:{f"round_{round_no}_{field}":med(values)
                       for (round_no,field),values in sorted(fields.items())}
            for archetype,fields in sorted(development.items())},
        "causes":dict(collections.Counter(g["outcome"] for g in records)),
        "limitations":[
            "No printed-card accuracy; deck entries are synthetic 99-card action categories",
            "No real physical Commander decks are injected; this tests four-seat AI policies only",
            "The old v5 rules engine has simplified generic mana, stack and combat",
            "Mirror equality tests seat bias, not strategy parity; archetype parity is diagnostic, not forced",
            "Early-terminated games do not contribute later-round development observations",
        ],
    }
    return out,records

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mirrors",type=int,default=20)
    p.add_argument("--rotations",type=int,default=4)
    p.add_argument("--rounds",type=int,default=30)
    p.add_argument("--seed",type=int,default=20261103)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--records",type=Path,required=True)
    a=p.parse_args()
    data,records=run(a.mirrors,a.rotations,a.rounds,a.seed)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.records.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
    a.records.write_text("\n".join(json.dumps(r,sort_keys=True,separators=(",",":"))
                                    for r in records)+"\n")
    print(json.dumps({k:data[k] for k in ("games","completed","median_completion_round",
                                         "wins_by_archetype","wins_by_seat","wins_by_turn_order")},
                     indent=2))
if __name__=="__main__":
    main()
