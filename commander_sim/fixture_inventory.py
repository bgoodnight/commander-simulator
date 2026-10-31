"""Read-only, offline deck fixture inventory for the future Deck Lab U0.

This is a metadata/observation endpoint, NOT a live simulator or rules engine.
No Scryfall requests are made by this module.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .card_cache import pinned_deck_entries, deck_names
from .deck_fixtures import FIXTURES, SHARED_CATALOG
from .observation import observe
from .snapshots import validate_snapshot


def inventory(*, catalog_path=SHARED_CATALOG, output_dir=None):
    """Return fixture readiness with explicit metadata/observation limitations."""
    decks = []
    for fixture in FIXTURES:
        snapshot = (Path(output_dir) / fixture.snapshot_path.name
                    if output_dir is not None else fixture.snapshot_path)
        manifest = snapshot.with_suffix(".manifest.json")
        status = "missing_metadata"
        error = None
        n = len(deck_names(fixture.deck_path.read_bytes()))
        cards = None
        if snapshot.exists() and manifest.exists():
            try:
                resolved = pinned_deck_entries(fixture.deck_path, manifest, catalog_path)
                checked = validate_snapshot(fixture.deck_path, snapshot,
                                            commander=fixture.commander)
                if len(resolved) != len(checked.cards):
                    raise ValueError("Pinned manifest count differs from snapshot")
                status = "validated_observation"
                cards = checked.deck.count
            except (ValueError, KeyError, TypeError, OSError) as exc:
                status = "invalid_metadata"
                error = str(exc)
        elif snapshot.exists() or manifest.exists():
            status = "incomplete_metadata"

        decks.append({
            "key": fixture.key, "commander": fixture.commander,
            "deck_path": fixture.relative_path, "status": status,
            "ownership_label": fixture.status, "distinct_card_names": n,
            "physical_card_count": cards,
            "observation_available": status == "validated_observation",
            "actual_gameplay_available": False,
            "limitations": ("Opening hand, first basic land and printed mana-value "
                            "screens only; no real casts, costs, combat or win rates"),
            **({"error": error} if error is not None else {}),
        })
    return {"mode": "offline_inventory", "decks": decks}


def fixture_observation(key, *, catalog_path=SHARED_CATALOG, output_dir=None,
                        seed=0, turns=6, mulligan='keep'):
    """Produce an existing six-turn observation for one validated fixture."""
    fixture = next((f for f in FIXTURES if f.key == key), None)
    if fixture is None:
        raise ValueError("Unknown deck fixture: " + str(key))
    snapshot = (Path(output_dir) / fixture.snapshot_path.name
                if output_dir is not None else fixture.snapshot_path)
    pinned_deck_entries(fixture.deck_path, snapshot.with_suffix(".manifest.json"),
                        catalog_path)
    return observe(fixture.deck_path, snapshot, seed=seed, turns=turns,
                   commander=fixture.commander, mulligan=mulligan)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=SHARED_CATALOG)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--observe", choices=[f.key for f in FIXTURES])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--turns", type=int, default=6)
    args = parser.parse_args()
    try:
        data = (fixture_observation(args.observe, catalog_path=args.catalog,
                                    output_dir=args.output_dir,
                                    seed=args.seed, turns=args.turns)
                if args.observe else inventory(catalog_path=args.catalog,
                                               output_dir=args.output_dir))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps(data, indent=2))
