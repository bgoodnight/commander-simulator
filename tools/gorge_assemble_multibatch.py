"""Cross-batch safe wrapper around single-game Gorge landmark assembler.

Each source batch supplies game, landmark, and event rows with the same verified
batch/deck/shard context. The existing single-batch implementation is reused
per game to prevent seed collisions in historical analysis. No UI or R2 writes.
"""
from __future__ import annotations

from collections import defaultdict

from tools.gorge_analytic_identity import attach_identity
from tools.gorge_assemble_model_table import assemble


def assemble_batches(batches: list[dict]) -> list[dict]:
    all_rows=[]
    seen_games=set()
    for batch in batches:
        batch_id=batch["batch_id"]
        deck=batch["deck"]
        shard=batch["shard"]
        cohort=batch.get("cohort_id")
        games=[attach_identity(row,batch=batch_id,deck=deck,shard=shard,
                               cohort_id=cohort) for row in batch["games"]]
        landmarks=[attach_identity(row,batch=batch_id,deck=deck,shard=shard,
                                   cohort_id=cohort) for row in batch["landmarks"]]
        source_events=batch.get("events")
        events=None if source_events is None else [
            attach_identity(row,batch=batch_id,deck=deck,shard=shard,
                            cohort_id=cohort) for row in source_events]
        game_map={}
        for game in games:
            gid=game["game_id"]
            if gid in seen_games or gid in game_map:
                raise ValueError("Duplicate canonical game across source batches")
            seen_games.add(gid)
            game_map[gid]=game
        if not game_map:raise ValueError("Empty batch games")
        landmark_map=defaultdict(list)
        for landmark in landmarks:
            landmark_map[landmark["game_id"]].append(landmark)
        event_map=defaultdict(list)
        for event in events or []:
            event_map[event["game_id"]].append(event)
        if set(landmark_map)!=set(game_map):
            raise ValueError("Missing or extraneous game landmarks")
        if events is not None and set(event_map)!=set(game_map):
            raise ValueError("Missing or extraneous event game")
        for gid,game in game_map.items():
            joined=assemble([game],landmark_map[gid],
                            event_map[gid] if events is not None else None)
            for row in joined:
                all_rows.append({**row,"game_id":gid,
                    "batch_id":batch_id,"shard":shard,
                    "cohort_id":cohort,
                    "source_sha256":game.get("source_sha256")})
    return sorted(all_rows,key=lambda row:(row["game_id"],row["landmark_global_turn"]))
