"""Repeatable Gorge-shaped Parquet / DuckDB / R2 performance microbenchmark.

Synthetic benchmark only: fixture-derived event shape, not gameplay outcomes.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import statistics
import time

def measured(fn, repetitions=7):
    values=[]
    for _ in range(repetitions):
        start=time.perf_counter()
        result=fn()
        values.append(1000*(time.perf_counter()-start))
    return {"median_ms":round(statistics.median(values), 3),
            "min_ms":round(min(values),3),
            "max_ms":round(max(values),3),
            "result":result}

def run(out, games_count=1000, events_per_game=500):
    import duckdb
    import pyarrow as pa
    import pyarrow.parquet as pq
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    fixture=json.loads(Path("tests/fixtures/gorge/gorge-seed-300.ui.json").read_text())
    events=[e for t in fixture.get("turns",[]) for e in t.get("events",[])]
    if not events:
        raise ValueError("Gorge event fixture missing")
    game_rows=[{"game_id":f"benchmark/{i}", "deck":("mortarion" if i%2==0 else "magnus"),
                "seed":i, "hero_seat":0,"winner_seat":i%4,"draw":False,
                "turns":20+i%20} for i in range(games_count)]
    events_rows=[]
    for i in range(games_count):
        for j in range(events_per_game):
            event=events[(i*11+j)%len(events)]
            events_rows.append({"game_id":f"benchmark/{i}","seq":j+1,
                "kind_id":int(event.get("kind_id",0)),
                "player":int(event.get("player",0)) if type(event.get("player",0)) is int else None,
                "event_json":json.dumps(event,sort_keys=True,separators=(",",":"))})
    started=time.perf_counter()
    pq.write_table(pa.Table.from_pylist(game_rows),out/"games.parquet",compression="zstd")
    pq.write_table(pa.Table.from_pylist(events_rows),out/"events.parquet",compression="zstd",row_group_size=10000)
    write_ms=round(1000*(time.perf_counter()-started),1)
    conn=duckdb.connect()
    gp=str((out/"games.parquet").resolve()).replace("'","''")
    ep=str((out/"events.parquet").resolve()).replace("'","''")
    queries={
      "win_rate_by_deck":f"SELECT deck, count(*) n, avg(CASE WHEN winner_seat=hero_seat THEN 1.0 ELSE 0.0 END) win_rate FROM read_parquet('{gp}') GROUP BY deck",
      "event_type_counts":f"SELECT kind_id, count(*) n FROM read_parquet('{ep}') GROUP BY kind_id ORDER BY n DESC LIMIT 10",
      "single_game_replay":f"SELECT seq, kind_id, event_json FROM read_parquet('{ep}') WHERE game_id='benchmark/42' ORDER BY seq",
      "join_games_events":f"SELECT g.deck, count(*) n FROM read_parquet('{ep}') e JOIN read_parquet('{gp}') g USING(game_id) GROUP BY g.deck"
    }
    results={}
    for name,sql in queries.items():
        values=measured(lambda:conn.execute(sql).fetchall())
        results[name]={k:v for k,v in values.items() if k!="result"}
        results[name]["returned_rows"]=len(values["result"])
    summary={"label":"synthetic fixture-shaped Gorge benchmark, not actual game outcomes",
             "games":games_count,"events":len(events_rows),"fixture_events":len(events),
             "parquet_write_ms":write_ms,
             "files":{p.name:p.stat().st_size for p in out.glob("*.parquet")},
             "queries":results}
    (out/"benchmark.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
    return summary

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--games",type=int,default=500)
    p.add_argument("--events-per-game",type=int,default=400)
    a=p.parse_args()
    run(a.out,a.games,a.events_per_game)
