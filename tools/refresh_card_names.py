"""Explicitly download Scryfall's complete canonical English card-name catalog.

One API call updates a local, SHA-verified names-only file. The Deck Lab
filters this local list on every keystroke, with *zero* Scryfall requests.
Full card identity details are fetched separately on deck preflight.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from commander_sim.card_name_catalog import DEFAULT_NAME_CATALOG, refresh_name_catalog


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_NAME_CATALOG)
    args = parser.parse_args()
    try:
        print(json.dumps(refresh_name_catalog(args.output), indent=2))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
