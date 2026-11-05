"""Compact the published legacy Python archive to UI-selected, source-backed releases.

The complete original 53-release collection was independently archived to
private R2 in a verified immutable tarball before this reducer was introduced.
No Gorge data, current cohorts or R2 storage objects are touched.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from tools.publish_simulation_archive import validate_index, json_bytes


def compact_index(index: dict, deck_data: dict):
    """Keep whole releases containing the first deck-hash match per deck."""
    active = {
        d["key"]: d["deck_sha256"]
        for d in deck_data.get("decks", [])
        if isinstance(d, dict) and isinstance(d.get("key"), str)
        and isinstance(d.get("deck_sha256"), str)
    }
    chosen = {}
    for release in index["releases"]:
        for key, entry in release["decks"].items():
            if key not in chosen and active.get(key) == entry.get("deck_sha256"):
                chosen[key] = release["id"]
    if not chosen:
        raise ValueError("No live deck identities matched historical sources")
    selected_ids = set(chosen.values())
    releases = [r for r in index["releases"] if r["id"] in selected_ids]
    # Keep entire source-backed releases rather than fabricating partial ones.
    return {"format": index["format"], "releases": releases}, chosen


def retained_paths(index: dict):
    paths = {"manifest.json"}
    for release in index["releases"]:
        for entry in release["decks"].values():
            paths.add(entry["manifest"])
            paths.add(entry["runs"])
    return sorted(paths)


def compact(source: Path, decks: Path, destination: Path):
    source, decks, destination = map(Path, (source, decks, destination))
    if source.resolve() == destination.resolve():
        raise ValueError("Output must be distinct from source (no in-place deletion)")
    full = validate_index(source)
    compacted, selected = compact_index(full, json.loads(decks.read_text()))
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise ValueError("Output must be initially empty")
    for path in retained_paths(compacted):
        if path == "manifest.json":
            data = json_bytes(compacted)
            (destination / path).write_bytes(data)
        else:
            target = destination / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / path, target)
    if validate_index(destination) != compacted:
        raise ValueError("Compacted index failed full source hash verification")
    return {
        "original_releases": len(full["releases"]),
        "kept_releases": len(compacted["releases"]),
        "kept_files": len(retained_paths(compacted)),
        "selected_decks": selected,
        "index_sha256": hashlib.sha256((destination / "manifest.json").read_bytes()).hexdigest()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=Path("web/pages/data/simulation-archive"))
    parser.add_argument("--decks", type=Path, default=Path("docs/deck-lab/decks.json"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(compact(args.source, args.decks, args.out), sort_keys=True))


if __name__ == "__main__":
    main()
