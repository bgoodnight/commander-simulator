"""Versioned deck-role and matchup metadata for Gorge Commander pods.

This is a repository-owned *selection contract*, not a card-rule implementation.
Archetype annotations are curated hypotheses; do not treat them as measured
statistics. Keep actual deck hashes and pilot/engine versions in game records.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

DEFAULT_LIBRARY = Path(__file__).resolve().parents[1] / "data" / "commander_deck_library.json"
COLORS = frozenset("WUBRG")
ROLES = frozenset({"player", "opponent", "both"})


def load_library(path=DEFAULT_LIBRARY):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "commander-deck-library-v1":
        raise ValueError("Unrecognized Commander library metadata schema")
    items = data.get("decks")
    if not isinstance(items, list) or not items:
        raise ValueError("Missing deck metadata")
    known = set()
    archetypes = set(data.get("allowed_archetypes", []))
    if not archetypes:
        raise ValueError("Missing archetype vocabulary")
    for row in items:
        key = row.get("key")
        if not isinstance(key, str) or not key or "/" in key or key in known:
            raise ValueError("Invalid or duplicate deck key")
        known.add(key)
        if row.get("role") not in ROLES:
            raise ValueError(f"{key}: unknown deck role")
        if row["role"] in ("opponent", "both") and row.get("provenance") != "stock_precon":
            raise ValueError(f"{key}: only verified stock precons may be opponents")
        colors = row.get("color_identity")
        if (not isinstance(colors, list) or len(colors) != len(set(colors))
                or any(c not in COLORS for c in colors)):
            raise ValueError(f"{key}: invalid color identity")
        labels = [row.get("primary_archetype")] + row.get("secondary_archetypes", [])
        if any(x not in archetypes for x in labels):
            raise ValueError(f"{key}: unknown archetype annotation")
        if not isinstance(row.get("commander"), str) or not row["commander"]:
            raise ValueError(f"{key}: missing commander identity")
    return data


def by_key(library):
    return {r["key"]: r for r in library["decks"]}


def opponent_keys(library):
    return [r["key"] for r in library["decks"] if r["role"] in ("opponent", "both")]


def player_keys(library):
    return [r["key"] for r in library["decks"] if r["role"] in ("player", "both")]


def validate_pod(library, hero, opponents):
    rows = by_key(library)
    if hero not in rows or rows[hero]["role"] not in ("player", "both"):
        raise ValueError("Selected hero must be an authorized player deck")
    if (not isinstance(opponents, (list, tuple)) or len(opponents) < 3
            or len(opponents) != len(set(opponents))):
        raise ValueError("Provide at least three distinct precon opponents")
    for key in opponents:
        if key == hero or key not in rows or rows[key]["role"] not in ("opponent", "both"):
            raise ValueError(f"{key}: not an authorized stock-precon opponent")
    return hero, list(opponents)


def validate_deck_files(library, hero, opponents, directory):
    """Validate all selected deck files and commander identities before Gorge."""
    from tools.fetch_gorge_precons import validate_precon
    validate_pod(library, hero, opponents)
    root = Path(directory)
    registry = by_key(library)
    versions = {}
    for key in [hero, *opponents]:
        path = root / (key + ".json")
        raw = path.read_bytes()
        doc = validate_precon(json.loads(raw), key)
        if doc["commander"] != registry[key]["commander"]:
            raise ValueError(f"{key}: commander name does not match metadata")
        versions[key] = hashlib.sha256(raw).hexdigest()
    return versions


def matchup_annotations(library, keys, hero=None):
    """Emit immutable per-seat annotations alongside each simulation result.

    A color is present as a binary property, not a claim that that color
    caused a game loss. Enrich recorded games with these keys and deck hashes
    for subsequent pod-level logistic models.
    """
    rows = by_key(library)
    return [{
        "deck_key": key,
        "role": "player" if key == hero else "opponent" if hero is not None else rows[key]["role"],
        "commander": rows[key]["commander"],
        "color_identity": rows[key]["color_identity"],
        "colors_present": {c: c in rows[key]["color_identity"] for c in "WUBRG"},
        "primary_archetype": rows[key]["primary_archetype"],
        "secondary_archetypes": rows[key]["secondary_archetypes"],
        "matchup_metadata_version": rows[key]["matchup_metadata_version"],
    } for key in keys]


def main():
    p = argparse.ArgumentParser(description="Validate a player vs precons Gorge pod")
    p.add_argument("--hero", required=True)
    p.add_argument("--opponents", required=True, help="Comma-separated precon keys")
    p.add_argument("--deck-dir", required=True)
    p.add_argument("--output")
    args = p.parse_args()
    library = load_library()
    opponents = args.opponents.split(",")
    versions = validate_deck_files(library, args.hero, opponents, args.deck_dir)
    output = {
        "schema": "gorge-opponent-pod-v1",
        "hero": args.hero,
        "opponent_pool": opponents,
        "deck_sha256": versions,
        "matchup_annotations": matchup_annotations(library, [args.hero, *opponents], hero=args.hero),
        "metadata_version": library["metadata_version"],
    }
    payload = json.dumps(output, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
