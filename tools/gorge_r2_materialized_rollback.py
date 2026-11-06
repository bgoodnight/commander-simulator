"""Offline validation for a guarded, pointer-only R2 Results rollback.

Download the *previously published immutable* version before invoking. This
script never writes R2; the workflow changes only current.json after validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from tools.gorge_cohort_eligibility import fingerprint, validate_registry

HEX = re.compile(r"^[0-9a-f]{64}$")
POINTER_SCHEMA = "gorge-r2-results-current-v1"
MANIFEST_SCHEMA = "gorge-r2-materialized-results-v1"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_checked(path, expected):
    if not HEX.fullmatch(str(expected)):
        raise ValueError("Malformed expected object digest")
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise ValueError(f"Digest mismatch: {path}")
    return json.loads(raw)


def verified_target(directory: Path, registry_path: Path, target_version: str):
    if not HEX.fullmatch(target_version):
        raise ValueError("Malformed rollback target version")
    version_root = directory / "versions" / target_version
    manifest_bytes = (version_root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if (manifest.get("schema") != MANIFEST_SCHEMA or
            manifest.get("version") != target_version or
            not isinstance(manifest.get("decks"), dict) or
            not manifest["decks"]):
        raise ValueError("Invalid rollback manifest")
    registry = json.loads(registry_path.read_bytes())
    cohorts = validate_registry(registry)
    if sha(registry_path.read_bytes()) != manifest.get("registry_sha256"):
        raise ValueError("Rollback registry version is no longer current")
    for deck, record in manifest["decks"].items():
        cohort = cohorts.get(record["cohort_id"])
        if (not cohort or cohort.get("status") != "current" or
                cohort.get("approved") is not True or
                cohort.get("deck") != deck or
                fingerprint(cohort) != record.get("cohort_fingerprint")):
            raise ValueError("Rollback would expose an ineligible cohort")
        n = record["n"]
        if (type(n) is not int or n < 1 or
                record["wins"] + record["losses"] != n or
                len(record["pages"]) != (n + 24) // 25):
            raise ValueError("Invalid rollback deck counts")
        root = version_root / deck
        summary_ref = record["summary"]
        if summary_ref["path"] != "summary.json":
            raise ValueError("Unexpected summary path")
        summary = read_checked(root / "summary.json", summary_ref["sha256"])
        if (summary.get("cohort_version") != target_version or
                summary.get("deck") != deck or
                (summary.get("n"), summary.get("wins"), summary.get("losses")) !=
                (n, record["wins"], record["losses"])):
            raise ValueError("Rollback summary mismatch")
        seen = set()
        for number, page_ref in enumerate(record["pages"]):
            rel = f"pages/{number:06d}.json"
            if page_ref["path"] != rel:
                raise ValueError("Unexpected page path")
            page = read_checked(root / rel, page_ref["sha256"])
            games = page.get("games")
            if (page.get("schema") != "gorge-r2-materialized-page-v1" or
                    page.get("deck") != deck or
                    page.get("version") != target_version or
                    page.get("page") != number or
                    page.get("total") != n or
                    not isinstance(games, list) or
                    len(games) != page_ref["count"] or
                    not 1 <= len(games) <= 25):
                raise ValueError("Rollback page mismatch")
            for game in games:
                gid = game["game_id"]
                if not isinstance(gid, str) or gid in seen:
                    raise ValueError("Duplicate rollback game ID")
                seen.add(gid)
                file_id = sha(gid.encode())
                detail = read_checked(root / "games" / (file_id + ".json"),
                                      game["sha256"])
                if (detail.get("schema") != "gorge-r2-materialized-game-v1" or
                        detail.get("deck") != deck or
                        detail.get("version") != target_version or
                        detail.get("game_id") != gid or
                        detail.get("batch", {}).get("deck_sha256") !=
                        record["ui_deck_sha256"]):
                    raise ValueError("Rollback game identity mismatch")
        if len(seen) != n:
            raise ValueError("Rollback page count inconsistent with full cohort")
    return {"schema": POINTER_SCHEMA, "version": target_version,
            "manifest_sha256": sha(manifest_bytes)}


def guarded_rollback(current: dict, expected_current: str, target: dict):
    if (current.get("schema") != POINTER_SCHEMA or
            not HEX.fullmatch(str(current.get("version", ""))) or
            not HEX.fullmatch(str(current.get("manifest_sha256", "")))):
        raise ValueError("Invalid current publication pointer")
    if current["version"] != expected_current:
        raise ValueError("Current pointer changed; rollback aborted")
    if current["version"] == target["version"]:
        raise ValueError("Target is already active")
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--expected-current", required=True)
    parser.add_argument("--target-version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = verified_target(args.download, args.registry, args.target_version)
    guarded_rollback(json.loads(args.current.read_bytes()),
                     args.expected_current, target)
    args.output.write_text(json.dumps(target, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"verified_rollback_target": args.target_version,
                      "from": args.expected_current}, sort_keys=True))


if __name__ == "__main__":
    main()
