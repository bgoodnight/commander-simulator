"""Theorycraft a new Commander deck with one cache-first metadata preflight.

Example:
  python tools/theorycraft.py my_modified_deck.txt --commander "Ghoulcaller Gisa"
  python tools/theorycraft.py my_modified_deck.txt --commander "Ghoulcaller Gisa" --offline

The first preflight may fetch missing identities from Scryfall (unless --offline).
Later preflights reuse the catalog and the SHA-pinned snapshot without calling
Scryfall. The observation is a mana-value *screen*, not a played Magic game.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from commander_sim.card_discovery import prepare_theorycraft_deck
from commander_sim.deck_fixtures import SHARED_CATALOG
from commander_sim.observation import observe


def run(deck, commander, *, offline=False, catalog_path=SHARED_CATALOG,
        output_dir=None, seed=0, turns=6, request_batch=None):
    prepared = prepare_theorycraft_deck(
        deck, commander, catalog_path=catalog_path, output_dir=output_dir,
        auto_fetch=not offline, request_batch=request_batch,
    )
    result = observe(
        deck, prepared["snapshot"], commander=commander,
        seed=seed, turns=turns,
    )
    return {"preflight": prepared, "observation": result}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck", type=Path)
    parser.add_argument("--commander", required=True)
    parser.add_argument("--catalog", type=Path, default=SHARED_CATALOG)
    parser.add_argument("--output-dir", type=Path,
                        help="Location of SHA-pinned snapshots (default: deck/.commander_metadata)")
    parser.add_argument("--offline", action="store_true",
                        help="Fail closed if an identity is not in the shared cache")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--turns", type=int, default=6)
    args = parser.parse_args()
    try:
        report = run(args.deck, args.commander, offline=args.offline,
                     catalog_path=args.catalog, output_dir=args.output_dir,
                     seed=args.seed, turns=args.turns)
    except (ValueError, TypeError, OSError, KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2))
