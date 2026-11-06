"""Strict canonical identity / provenance for cross-batch Gorge analytics.

Does not read or alter UI materialized snapshots. Source evidence remains private.
"""
from __future__ import annotations

import re

_BATCH=re.compile(r"[0-9]+-[1-9][0-9]*\Z")
_DECK=re.compile(r"[a-z][a-z0-9_-]{1,75}\Z")
_SHA=re.compile(r"[a-f0-9]{64}\Z")
_GAME=re.compile(r"([0-9]+-[1-9][0-9]*)/([a-z][a-z0-9_-]{1,75})/([0-9]+)/([0-9]+)\Z")


def game_id(batch: str, deck: str, shard: int, seed: int) -> str:
    """Canonical ID as used by verified R2 warehouse and UI source projections."""
    if (not isinstance(batch,str) or not _BATCH.fullmatch(batch)
        or not isinstance(deck,str) or not _DECK.fullmatch(deck)
        or type(shard) is not int or shard < 0
        or type(seed) is not int or seed < 0):
        raise ValueError("Invalid canonical source identity")
    return f"{batch}/{deck}/{shard}/{seed}"


def parse_game_id(value: str) -> dict:
    if not isinstance(value,str):
        raise ValueError("Expected string game identity")
    match=_GAME.fullmatch(value)
    if match is None:
        raise ValueError("Invalid game identity")
    batch, deck, shard, seed=match.groups()
    result={"batch_id":batch,"deck":deck,"shard":int(shard),"seed":int(seed)}
    if game_id(**result) != value:
        raise ValueError("Noncanonical game identity")
    return result


def attach_identity(row: dict, *, batch: str, deck: str, shard: int=0,
                    cohort_id: str|None=None, source_sha256: str|None=None) -> dict:
    """Tag a game or feature row without claiming cohort approval."""
    if type(row) is not dict or type(row.get("seed")) is not int:
        raise ValueError("Missing source seed")
    if row.get("deck") not in (None,deck) or row.get("hero") not in (None,deck):
        raise ValueError("Mismatched deck identity")
    if row.get("game_id") not in (None,game_id(batch,deck,shard,row["seed"])):
        raise ValueError("Mismatched game ID")
    if source_sha256 is not None and (not isinstance(source_sha256,str) or not _SHA.fullmatch(source_sha256)):
        raise ValueError("Invalid source hash")
    if (row.get("source_sha256") is not None and source_sha256 is not None
        and row["source_sha256"] != source_sha256):
        raise ValueError("Source hash mismatch")
    return {**row,"game_id":game_id(batch,deck,shard,row["seed"]),
            "batch_id":batch,"shard":shard,"cohort_id":cohort_id,
            "source_sha256":source_sha256 or row.get("source_sha256")}


def merge_source_batches(batches: list[dict]) -> list[dict]:
    """Fail-closed union of independently verified run records.

    Each batch entry: batch_id, deck, shard, cohort_id, games.
    This is not a cohort-compatibility or model-eligibility approval.
    """
    result=[]
    seen={}
    for batch in batches:
        if not isinstance(batch,dict) or not isinstance(batch.get("games"),list):
            raise ValueError("Invalid batch descriptor")
        for row in batch["games"]:
            tagged=attach_identity(row,batch=batch["batch_id"],
                deck=batch["deck"],shard=batch["shard"],
                cohort_id=batch.get("cohort_id"))
            gid=tagged["game_id"]
            if gid in seen:
                raise ValueError("Duplicate immutable game identity across batches")
            seen[gid]=tagged
            result.append(tagged)
    return sorted(result,key=lambda x:x["game_id"])
