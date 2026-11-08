"""Read an explicitly reviewed, source-completion shard inventory.

Never derive expected shards from an R2 directory listing: an interrupted upload
would make the incomplete listing look authoritative. The inventory is kept in
version control and must be updated as part of approving additional batches.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from tools.gorge_cohort_eligibility import validate_registry


def validate_inventory(document, registry, requested_batches):
    cohorts = validate_registry(registry)
    if document.get("schema") != "gorge-r2-approved-source-inventory-v1":
        raise ValueError("Unrecognized approved source inventory")
    records = document.get("batches")
    if not isinstance(records, list) or not records:
        raise ValueError("No explicitly attested source batches")
    expected = []
    known = set()
    for record in records:
        batch = record.get("batch")
        if (not isinstance(batch, str) or
                not re.fullmatch(r"[0-9]+-[0-9]+", batch) or batch in known):
            raise ValueError("Duplicate or malformed attested source batch")
        known.add(batch)
        if not isinstance(record.get("completion_ref"), str) or not record["completion_ref"].startswith("github:"):
            raise ValueError("Source batch lacks a reviewed completion reference")
        shards = record.get("shards")
        if not isinstance(shards, list) or not shards:
            raise ValueError("Attested batch has no shards")
        identities = set()
        for item in shards:
            if not isinstance(item, dict) or set(item) != {"deck", "shard", "games"}:
                raise ValueError("Malformed attested shard")
            deck, shard, games = item["deck"], item["shard"], item["games"]
            if (not isinstance(deck, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", deck)
                or type(shard) is not int or shard < 0 or
                type(games) is not int or games < 1):
                raise ValueError("Invalid attested shard identity/count")
            if (deck, shard) in identities:
                raise ValueError("Duplicate attested shard")
            identities.add((deck, shard))
            if not any(c.get("approved") is True and c.get("status") == "current"
                       and c.get("deck") == deck and c.get("source_batch") == batch
                       for c in cohorts.values()):
                raise ValueError("Attested shard lacks approved current cohort")
            expected.append({"batch": batch, "deck": deck, "shard": str(shard),
                             "games": games})
    if set(requested_batches) != known:
        raise ValueError("Requested batches differ from reviewed source inventory")
    return expected


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--inventory", type=Path, required=True)
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--batches-file", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    requested = [x.strip() for x in args.batches_file.read_text().splitlines() if x.strip()]
    approved = validate_inventory(json.loads(args.inventory.read_text()),
                                  json.loads(args.registry.read_text()), requested)
    args.out.write_text(json.dumps(approved, sort_keys=True, indent=2) + "\n")
    print(f"Verified {len(approved)} explicitly attested source shards")


if __name__ == "__main__":
    main()
