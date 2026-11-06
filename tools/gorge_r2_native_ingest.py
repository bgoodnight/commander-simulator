"""Read-only R2 batch acquisition for Gorge analytics.

Only explicitly named warehouse/v1 batches. Credentials are inherited by AWS CLI
from trusted runner environment. No mutating S3 operations or public exports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
from typing import Callable

BATCH = re.compile(r"^[A-Za-z0-9_-]+$")
PART = re.compile(r"^[A-Za-z0-9_-]+$")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_shards(root: Path) -> dict:
    manifests = sorted(root.rglob("manifest.json"))
    if not manifests:
        raise ValueError("No warehouse manifests found in downloaded batch")
    entries = []
    seen = set()
    for path in manifests:
        m = json.loads(path.read_text())
        if m.get("schema") != "gorge-warehouse-shard-v1":
            raise ValueError(f"Unsupported warehouse schema: {path}")
        for filename in ("games.parquet", "events.parquet"):
            info = (m.get("files") or {}).get(filename)
            item = path.parent / filename
            if not info or not item.is_file():
                raise ValueError(f"Missing source-backed file: {item}")
            if item.stat().st_size != info.get("bytes") or digest(item) != info.get("sha256"):
                raise ValueError(f"Warehouse digest or byte count mismatch: {item}")
        key = (m.get("batch_id"), m.get("player_deck"), m.get("shard"))
        if key in seen:
            raise ValueError(f"Duplicate shard identity: {key}")
        seen.add(key)
        entries.append({"batch_id":key[0], "hero":key[1], "shard":key[2],
                        "games":m.get("games"),"events":m.get("native_events")})
    return {"schema":"gorge-r2-batch-acquisition-v1","shards":entries,
            "shard_count":len(entries),"source_verified":True,
            "production_eligible":False}


def safely_extract_native(archive: Path, dest: Path) -> None:
    """Reject links, devices, traversal and absolute paths before unpacking."""
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            p = Path(member.name)
            if (p.is_absolute() or ".." in p.parts or
                not (member.isfile() or member.isdir()) or
                not (dest / p).resolve().is_relative_to(dest.resolve())):
                raise ValueError(f"Unsafe tar entry {member.name!r}")
        tar.extractall(dest, filter="data")


def _aws(args: list[str], endpoint: str) -> subprocess.CompletedProcess:
    return subprocess.run(["aws", "--endpoint-url",endpoint,*args],
                          check=True, text=True, capture_output=True)


def download(batch: str, destination: Path, endpoint: str, bucket: str,
             hero: str | None = None, fetch_native: bool = True) -> dict:
    if not BATCH.fullmatch(batch):
        raise ValueError("Unsafe batch ID")
    if hero is not None and not PART.fullmatch(hero):
        raise ValueError("Unsafe hero key")
    if not endpoint.startswith("https://") or not endpoint.endswith(".r2.cloudflarestorage.com"):
        raise ValueError("Expected Cloudflare R2 endpoint")
    if bucket != "gorge-simulations":
        raise ValueError("Unexpected R2 bucket")
    destination.mkdir(parents=True,exist_ok=True)
    prefix=f"warehouse/v1/{batch}/"
    if hero:
        prefix+=hero+"/"
    local=destination/"warehouse"
    local.mkdir(parents=True,exist_ok=True)
    _aws(["s3","cp",f"s3://{bucket}/{prefix}",str(local),"--recursive",
          "--exclude","*","--include","*/manifest.json",
          "--include","*/games.parquet","--include","*/events.parquet",
          "--no-progress"], endpoint)
    report=verify_shards(local)
    if any(s["batch_id"] != batch for s in report["shards"]):
        raise ValueError("Downloaded manifest belongs to unexpected batch")
    if hero and any(s["hero"] != hero for s in report["shards"]):
        raise ValueError("Downloaded manifest belongs to unexpected hero")
    report["batch_id"]=batch
    report["warehouse_only"]=not fetch_native
    report["native_archives"]=[]
    if fetch_native:
        # Native files are named by run, not warehouse path. Download ONLY keys
        # whose filename contains the exact run-attempt suffix, then inspect
        # archive contents and native identity before deriving features.
        listing=_aws(["s3api","list-objects-v2","--bucket",bucket,
                      "--prefix","native/v1/","--output","json"],endpoint)
        keys=[x["Key"] for x in json.loads(listing.stdout).get("Contents",[])]
        suffix="-"+batch+".tar.gz"
        matched=[key for key in keys if key.endswith(suffix) and
                 (hero is None or key.startswith("native/v1/"+hero+"/"))]
        if not matched:
            raise ValueError("No exact batch native archives found; no features inferred")
        for key in matched:
            if not re.fullmatch(r"native/v1/[A-Za-z0-9_-]+/[0-9]+/[A-Za-z0-9_-]+\.tar\.gz",key):
                raise ValueError(f"Unexpected native object key {key}")
            archive=destination/"archives"/key.replace("/","__")
            archive.parent.mkdir(parents=True,exist_ok=True)
            _aws(["s3","cp",f"s3://{bucket}/{key}",str(archive),"--no-progress"],endpoint)
            target=destination/"native_shards"/key.replace("/","__").removesuffix(".tar.gz")
            safely_extract_native(archive,target)
            report["native_archives"].append({"key":key,"sha256":digest(archive),
                                              "extracted":str(target)})
    return report


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch-id",required=True)
    ap.add_argument("--hero")
    ap.add_argument("--destination",type=Path,required=True)
    ap.add_argument("--account-id",required=True)
    ap.add_argument("--bucket",default="gorge-simulations")
    ap.add_argument("--warehouse-only",action="store_true")
    args=ap.parse_args()
    if not re.fullmatch(r"[a-fA-F0-9]{32}",args.account_id):
        ap.error("R2 account ID must be 32 hex characters")
    report=download(args.batch_id,args.destination,
           f"https://{args.account_id}.r2.cloudflarestorage.com",
           args.bucket,hero=args.hero,fetch_native=not args.warehouse_only)
    (args.destination/"r2-acquisition.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"shards":report["shard_count"],"native_archives":len(report["native_archives"]),
                      "source_verified":True,"production_eligible":False}))


if __name__=="__main__":
    main()
