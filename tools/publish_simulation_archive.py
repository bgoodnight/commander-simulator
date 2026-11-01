"""Validate bounded simulation batches and publish a persistent Pages index.

Input: existing per-deck archive manifests and their matching run JSON files.
Output: an immutable revision/config directory plus a small discoverable index.
This module does not generate games, call an API, or modify the user interface.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from commander_sim.deck_fixtures import FIXTURES
from tools.build_simulation_archive import FORMAT

PUBLIC_FORMAT = "commander-simulation-library-v1"
KEYS = frozenset(f.key for f in FIXTURES)


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False) + "\n").encode("utf-8")


def read_archive(source, key):
    source = Path(source)
    if key not in KEYS:
        raise ValueError("Unknown approved deck")
    manifest_path = source / (key + "-manifest.json")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    filename = manifest.get("run_file")
    if (not isinstance(filename, str)
            or PurePosixPath(filename).name != filename
            or filename != (
                f"{key}-seeds-{manifest.get('seed_start')}-"
                f"{manifest.get('seed_start', 0)+manifest.get('seed_count', 0)-1}.json")):
        raise ValueError("Invalid or unsafe archive filename")
    payload = (source / filename).read_bytes()
    if hashlib.sha256(payload).hexdigest() != manifest.get("run_sha256"):
        raise ValueError("Archive run checksum mismatch")
    runs = json.loads(payload)
    n = manifest.get("seed_count")
    if (manifest.get("format") != FORMAT or manifest.get("deck_key") != key
            or manifest.get("mode") != "bounded_authoritative_early_actions"
            or type(n) is not int or n < 1 or len(runs) != n
            or not isinstance(manifest.get("deck_sha256"), str)
            or len(manifest["deck_sha256"]) != 64
            or type(manifest.get("seed_start")) is not int
            or manifest["seed_start"] < 0
            or type(manifest.get("turn_count")) is not int
            or not 1 <= manifest["turn_count"] <= 10):
        raise ValueError("Invalid bounded archive metadata")
    seeds = range(manifest["seed_start"], manifest["seed_start"] + n)
    if (any(run.get("seed") != seed
            or run.get("deck_key") != key
            or run.get("deck_sha256") != manifest["deck_sha256"]
            or run.get("mode") != manifest["mode"]
            or len(run.get("events", [])) != manifest["turn_count"]
            or len(run.get("state_snapshots", [])) != manifest["turn_count"]
            for run, seed in zip(runs, seeds))):
        raise ValueError("Archive run rows do not match manifest")
    return manifest_bytes, payload, manifest


def validate_index(root):
    """Fail closed on nonexistent, mismatched, mutable or escaping files."""
    root = Path(root)
    index = json.loads((root / "manifest.json").read_bytes())
    if index.get("format") != PUBLIC_FORMAT or not isinstance(index.get("releases"), list):
        raise ValueError("Unsupported published archive index")
    ids = set()
    for release in index["releases"]:
        name = release.get("id")
        if not isinstance(name, str) or name in ids:
            raise ValueError("Invalid or duplicate archive ID")
        ids.add(name)
        entries = release.get("decks")
        if not isinstance(entries, dict) or not entries or set(entries) - KEYS:
            raise ValueError("Unrecognized archived decks")
        for key, entry in entries.items():
            for name_field, sha_field in (("manifest", "manifest_sha256"),
                                           ("runs", "run_sha256")):
                relative = entry.get(name_field)
                if not isinstance(relative, str):
                    raise ValueError("Missing archived path")
                path = PurePosixPath(relative)
                if (path.is_absolute() or ".." in path.parts or
                        not path.parts or path.parts[0] != "releases" or
                        path.suffix != ".json"):
                    raise ValueError("Unsafe archived path")
                data = (root / relative).read_bytes()
                if hashlib.sha256(data).hexdigest() != entry.get(sha_field):
                    raise ValueError("Archived file checksum mismatch")
            m = json.loads((root / entry["manifest"]).read_bytes())
            if (m.get("deck_key") != key or m.get("deck_sha256") != entry.get("deck_sha256")
                    or m.get("run_sha256") != entry.get("run_sha256")
                    or m.get("seed_count") != release.get("seed_count")
                    or m.get("turn_count") != release.get("turn_count")):
                raise ValueError("Inconsistent published archive manifest")
    return index


def publish_archives(source, destination, *, engine_commit, keys=None):
    """Copy checked archives under a stable revision; preserve prior releases."""
    if (not isinstance(engine_commit, str) or len(engine_commit) != 40
            or any(x not in "0123456789abcdef" for x in engine_commit)):
        raise ValueError("Expected full lowercase engine commit SHA")
    keys = tuple(sorted(KEYS if keys is None else keys))
    if not keys or len(keys) != len(set(keys)) or set(keys) - KEYS:
        raise ValueError("Invalid archive deck selection")
    checked = {key: read_archive(source, key) for key in keys}
    first = checked[keys[0]][2]
    seed_start = first["seed_start"]
    n = first["seed_count"]
    turns = first["turn_count"]
    if any(m["seed_start"] != seed_start or m["seed_count"] != n
           or m["turn_count"] != turns for _, _, m in checked.values()):
        raise ValueError("Mixed archive seed/turn parameters")
    identity = f"{engine_commit}/seeds-{seed_start}-{seed_start+n-1}-turns-{turns}"
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    index_path = root / "manifest.json"
    old = validate_index(root) if index_path.exists() else {
        "format": PUBLIC_FORMAT, "releases": []}
    existing = next((x for x in old["releases"] if x["id"] == identity), None)
    release = {
        "id": identity, "engine_commit": engine_commit,
        "seed_start": seed_start, "seed_count": n, "turn_count": turns,
        "mode": "bounded_authoritative_early_actions", "decks": {}}
    for key in keys:
        manifest_bytes, run_bytes, manifest = checked[key]
        prefix = f"releases/{identity}/{key}"
        relative_manifest = f"{prefix}/manifest.json"
        relative_runs = f"{prefix}/{manifest['run_file']}"
        release["decks"][key] = {
            "deck_sha256": manifest["deck_sha256"],
            "manifest": relative_manifest,
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "runs": relative_runs,
            "run_sha256": manifest["run_sha256"]}
    if existing is not None:
        if existing != release:
            raise ValueError("Cannot overwrite an existing archive release")
        return validate_index(root)
    for key, (manifest_bytes, run_bytes, manifest) in checked.items():
        entry = release["decks"][key]
        for relative, data in ((entry["manifest"], manifest_bytes),
                               (entry["runs"], run_bytes)):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() != data:
                raise ValueError("Immutable archive path collision")
            target.write_bytes(data)
    # Newest published release first. The existing static Deck Lab reads
    # releases[0], so insertion order is authoritative, not lexical SHA order.
    # Preserve every older release unchanged for historical comparisons.
    old["releases"].insert(0, release)
    index_path.write_bytes(json_bytes(old))
    return validate_index(root)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--engine-commit", required=True)
    args = parser.parse_args(argv)
    result = publish_archives(args.source, args.output,
                              engine_commit=args.engine_commit)
    print(json.dumps({"releases": len(result["releases"]),
                      "latest": result["releases"][0]["id"]}, indent=2))


if __name__ == "__main__":
    main()
