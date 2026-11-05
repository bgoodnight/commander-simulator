"""Benchmark source-verified native Gorge Parquet, not fabricated gameplay rows."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import time

def timed(fn, repetitions=7):
    measurements=[]
    outcome=None
    for _ in range(repetitions):
        start=time.perf_counter()
        outcome=fn()
        measurements.append((time.perf_counter()-start)*1000)
    return {"median_ms":round(statistics.median(measurements),3),
            "min_ms":round(min(measurements),3),
            "max_ms":round(max(measurements),3),
            "returned_rows":len(outcome)}

def benchmark(directory:Path, expected_games:int):
    import duckdb
    import pyarrow.parquet as pq
    directory=Path(directory)
    games_path=directory/"games.parquet"
    events_path=directory/"events.parquet"
    manifest=json.loads((directory/"manifest.json").read_text())
    games_meta=pq.read_metadata(games_path)
    events_meta=pq.read_metadata(events_path)
    assert manifest["games"]==games_meta.num_rows==expected_games
    assert manifest["native_events"]==events_meta.num_rows
    for name in ("games.parquet","events.parquet"):
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==manifest["files"][name]["sha256"]
    conn=duckdb.connect()
    gp=str(games_path.resolve()).replace("'","''")
    ep=str(events_path.resolve()).replace("'","''")
    gid=conn.execute(f"SELECT game_id FROM read_parquet('{gp}') ORDER BY seed LIMIT 1").fetchone()[0]
    safe_gid=gid.replace("'","''")
    queries={
      "win_rate_by_deck":f"SELECT deck, count(*) n, avg(CASE WHEN NOT draw AND winner_seat=hero_seat THEN 1.0 ELSE 0.0 END) win_rate FROM read_parquet('{gp}') GROUP BY deck",
      "event_type_counts":f"SELECT kind_id, count(*) n FROM read_parquet('{ep}') GROUP BY kind_id ORDER BY n DESC LIMIT 10",
      "single_game_events":f"SELECT seq,kind_id,event_json FROM read_parquet('{ep}') WHERE game_id='{safe_gid}' ORDER BY seq",
      "game_event_join":f"SELECT g.deck, count(*) n FROM read_parquet('{ep}') e JOIN read_parquet('{gp}') g USING (game_id) GROUP BY g.deck"
    }
    results={name:timed(lambda sql=sql:conn.execute(sql).fetchall())
             for name,sql in queries.items()}
    report={"schema":"gorge-real-query-benchmark-v1",
            "provenance":"100 source-verified Gorge native recordings, not synthetic fixture events",
            "games":manifest["games"],"events":manifest["native_events"],
            "events_per_game":round(manifest["native_events"]/manifest["games"],1),
            "files":{p.name:p.stat().st_size for p in (games_path,events_path)},
            "query_latency":results}
    (directory/"real-benchmark.json").write_text(json.dumps(report,indent=2)+"\n")
    print("REAL_GORGE_QUERY_RESULT "+json.dumps(report,sort_keys=True))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--warehouse",type=Path,required=True)
    p.add_argument("--expected-games",type=int,default=100)
    args=p.parse_args()
    benchmark(args.warehouse,args.expected_games)
