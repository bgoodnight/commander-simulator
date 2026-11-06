"""Read one exact private corrected-pilot experimental R2 archive (no writes).

This source archive is intentionally NOT a warehouse/v1 Parquet batch. Keep the
formats distinct and never treat experimental records as approved statistics.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

from tools.gorge_r2_native_ingest import _aws, safely_extract_native, digest

VALID = re.compile(r"^[0-9]+-[1-9][0-9]*$")
HEROES = frozenset({"mortarion_current", "magnus_premium"})


def acquire(run_attempt: str, hero: str, account_id: str, destination: Path) -> dict:
    if not VALID.fullmatch(run_attempt):
        raise ValueError("Run attempt must be numeric run-id-attempt")
    if hero not in HEROES:
        raise ValueError("Unrecognized hero deck")
    if not re.fullmatch(r"[a-fA-F0-9]{32}", account_id):
        raise ValueError("Invalid Cloudflare account ID")
    key = f"native/experimental/corrected-pilot/v1/{run_attempt}/{hero}.tar.gz"
    endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
    destination.mkdir(parents=True,exist_ok=True)
    archive=destination/"source.tar.gz"
    _aws(["s3","cp",f"s3://gorge-simulations/{key}",str(archive),"--no-progress"],endpoint)
    extracted=destination/"extracted"
    safely_extract_native(archive,extracted)
    results=extracted/"results"
    runfile=results/"runs.jsonl"
    source_manifest=results/"source-manifest.json"
    qualification=results/"qualification-summary.json"
    if not all(p.is_file() for p in (runfile,source_manifest,qualification)):
        raise ValueError("Incomplete native source archive")
    manifest=json.loads(source_manifest.read_text())
    summary=json.loads(qualification.read_text())
    run_id, attempt=run_attempt.split("-")
    if (manifest.get("schema")!="gorge-fresh-corrected-pilot-source-v1"
        or manifest.get("source_run_id")!=run_id
        or str(manifest.get("run_attempt"))!=attempt
        or manifest.get("hero_deck")!=hero
        or manifest.get("approval") is not False):
        raise ValueError("Source provenance/approval mismatch")
    runs=[json.loads(line) for line in runfile.read_text().splitlines() if line.strip()]
    if len(runs)!=manifest.get("attempts_expected") or len(runs)!=summary.get("attempted"):
        raise ValueError("Attempt count does not match source manifest and qualification summary")
    seeds=set()
    missing=[]
    verified=0
    completed=0
    for row in runs:
        seed=row.get("seed")
        seat=row.get("hero_seat")
        decks=row.get("decks")
        if (type(seed) is not int or seed in seeds or type(seat) is not int
            or seat not in range(4) or not isinstance(decks,list)
            or len(decks)!=4 or decks[seat]!=hero):
            raise ValueError("Duplicate seed or unexpected hero identity")
        seeds.add(seed)
        completed+=int(row.get("finished") is True)
        verified+=int(row.get("replay_verified") is True)
        p=results/"native"/f"gorge-seed-{seed}.json"
        if not p.exists():
            missing.append(seed)
            continue
        native=json.loads(p.read_text())
        if (native.get("schema")!="gorge-native-trace-v1"
            or native.get("seed")!=seed
            or native.get("chain")!=row.get("replay_chain")
            or native.get("decks")!=decks
            or native.get("hero_seat")!=seat
            or not isinstance((native.get("log") or {}).get("events"),list)
            or not isinstance((native.get("log") or {}).get("intents"),list)):
            raise ValueError(f"Native verification failed for seed {seed}")
    if completed != summary.get("completed") or verified != summary.get("replay_verified"):
        raise ValueError("Outcome counts disagree with source summary")
    report={
        "schema":"gorge-experimental-r2-acquisition-v1",
        "source_key":key,"archive_sha256":digest(archive),
        "run_attempt":run_attempt,"hero":hero,"attempts":len(runs),
        "completed":completed,"replay_verified":verified,
        "native_available":len(runs)-len(missing),"native_missing_seeds":missing,
        "source_manifest":manifest,
        "qualifying_status":summary.get("status"),
        "approval":False,"production_eligible":False,
        "extracted_results":str(results),
    }
    (destination/"acquisition-report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-attempt",required=True)
    p.add_argument("--hero",choices=sorted(HEROES),required=True)
    p.add_argument("--account-id",required=True)
    p.add_argument("--destination",type=Path,required=True)
    a=p.parse_args()
    r=acquire(a.run_attempt,a.hero,a.account_id,a.destination)
    print(json.dumps({key:r[key] for key in ("hero","attempts","completed",
          "replay_verified","native_available","native_missing_seeds","production_eligible")},sort_keys=True))


if __name__=="__main__":
    main()
