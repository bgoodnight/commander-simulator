"""Build an original Results-compatible R2 projection from immutable Gorge sources.

Offline, no cloud writes, no cohort approval. Reuses the synthetic omniscient exporter and original-renderer adapter. Only run on a
verified source archive; never infer omitted data.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from tools.gorge_ui_export import convert

ROOT=Path(__file__).resolve().parents[1]

def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build(source_dir:Path, deck:str, batch:str, shard:int, out:Path,
          ui_deck_sha:str)->dict:
    source_dir=Path(source_dir)
    if not re.fullmatch(r"[a-z][a-z0-9_-]{1,75}",deck):
        raise ValueError("Invalid deck")
    if not re.fullmatch(r"[0-9]+-[0-9]+",batch):
        raise ValueError("Invalid source run-attempt batch")
    if type(shard) is not int or shard<0:
        raise ValueError("Invalid shard")
    if not re.fullmatch(r"[a-f0-9]{64}",ui_deck_sha):
        raise ValueError("Invalid original UI deck hash")
    manifest=json.loads((source_dir/"source-manifest.json").read_text())
    run_id,attempt=batch.split("-")
    if (manifest.get("schema")!="gorge-fresh-corrected-pilot-source-v1" or
        manifest.get("source_run_id")!=run_id or
        str(manifest.get("run_attempt"))!=attempt or
        manifest.get("hero_deck")!=deck or
        manifest.get("approval") is not False):
        raise ValueError("Native recording provenance mismatch")
    source_deck_sha=manifest.get("hero_deck_sha256")
    if not isinstance(source_deck_sha,str) or not re.fullmatch(r"[a-f0-9]{64}",source_deck_sha):
        raise ValueError("Missing native deck fingerprint")
    runs=[json.loads(x) for x in (source_dir/"runs.jsonl").read_text().splitlines() if x.strip()]
    if not runs or len(runs)!=manifest.get("attempts_expected") or len(runs)>200:
        raise ValueError("Incomplete run population")
    items=[]
    seeds=set()
    for row in runs:
        seed,seat=row.get("seed"),row.get("hero_seat")
        if (type(seed) is not int or seed in seeds or
            type(seat) is not int or seat not in range(4) or
            not isinstance(row.get("decks"),list) or
            len(row["decks"])!=4 or row["decks"][seat]!=deck or
            row.get("finished") is not True or
            row.get("replay_verified") is not True or
            row.get("draw") is True or row.get("error")):
            raise ValueError(f"Unverified or nondecisive native game: {seed}")
        seeds.add(seed)
        native_file=source_dir/"native"/f"gorge-seed-{seed}.json"
        native=json.loads(native_file.read_text())
        if (native.get("schema")!="gorge-native-trace-v1" or
            native.get("seed")!=seed or
            native.get("chain")!=row.get("replay_chain") or
            native.get("hero_seat")!=seat or
            native.get("decks")!=row.get("decks")):
            raise ValueError(f"Native trace provenance mismatch: {seed}")
        replay=convert(native,include_hidden=True)
        winner=row.get("winner_seat")
        if type(winner) is not int or winner not in range(4):
            raise ValueError("No decisive winner")
        items.append({"game_id":f"{batch}/{deck}/{shard}/{seed}",
            "seed":seed,"chain":row["replay_chain"],
            "source_sha256":digest(native_file),
            "hero_seat":seat,"winner_seat":winner,"replay":replay})
    payload={"schema":"gorge-original-ui-projection-input-v1",
        "source_batch":batch,"shard":shard,"deck":deck,
        "deck_sha256":ui_deck_sha,"source_deck_sha256":source_deck_sha,
        "games":items}
    out=Path(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        input_file=Path(directory)/"source-input.json"
        input_file.write_text(json.dumps(payload,separators=(",",":")))
        subprocess.run(["node",str(ROOT/"tools/gorge_original_ui_projection.cjs"),
                        str(input_file),str(out)],
                       check=True,cwd=ROOT)
    projection=json.loads(out.read_text())
    if (len(projection["games"])!=len(runs) or
        any(game["run"]["gorge_source"]["visibility"]!="omniscient"
            for game in projection["games"])):
        raise ValueError("Projection dropped a source run")
    return {"schema":projection["schema"],"deck":deck,
            "games":len(runs),"ui_deck_sha256":ui_deck_sha,
            "source_deck_sha256":source_deck_sha,
            "approved":False,
            "output_sha256":digest(out)}

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--deck",required=True)
    p.add_argument("--batch",required=True)
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--ui-deck-sha",required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build(a.source_dir,a.deck,a.batch,a.shard,
                           a.out,a.ui_deck_sha),sort_keys=True))
if __name__=="__main__":
    main()
