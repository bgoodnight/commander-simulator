"""Cache-first Scryfall import, explicitly invoked outside gameplay.

Usage:
  python tools/fetch_deck_identities.py DECK OUTPUT --catalog PATH
  python tools/fetch_deck_identities.py DECK OUTPUT --offline
  python tools/fetch_deck_identities.py DECK OUTPUT --seed-pair DECK SNAPSHOT

OUTPUT retains the legacy snapshot shape for commander_sim.snapshots.
OUTPUT.with_suffix('.manifest.json') pins exact Oracle-ID revisions. Existing
outputs/manifests are never silently replaced by different metadata: provide
new paths for a refreshed revision. No API calls occur in normal simulations.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# This script is executable as "python tools/fetch_deck_identities.py".
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from commander_sim.card_cache import (
    SCHEMA_VERSION, CardCatalog, atomic_json, card_aliases, deck_names, digest,
    verify_card,
)


def scryfall_batch(names):
    """Make one bounded, explicit Scryfall collection request (at most 75)."""
    if not names or len(names) > 75:
        raise ValueError("Scryfall collection request requires 1–75 names")
    payload = json.dumps({"identifiers": [
        {"name": name.split(" // ", 1)[0]} for name in names
    ]}).encode("utf-8")
    request = Request("https://api.scryfall.com/cards/collection", data=payload,
                      headers={"User-Agent": "CommanderSimulator/1.0 (explicit deck import)",
                               "Accept": "application/json", "Content-Type": "application/json"})
    with urlopen(request, timeout=45) as response:
        data = json.load(response)
    if not isinstance(data, dict) or not isinstance(data.get("data"), list):
        raise ValueError("Incomplete Scryfall collection response")
    return data["data"]


def _match_card(name, returned):
    matches = [card for card in returned
               if isinstance(card, dict) and name in card_aliases(card)]
    if len(matches) != 1:
        raise ValueError(f"Expected one exact card/face for {name!r}, found {len(matches)}")
    verify_card(matches[0])
    return matches[0]


def _same_manifest(a, b):
    return (a.get("schema_version") == b.get("schema_version")
            and a.get("deck_sha256") == b.get("deck_sha256")
            and a.get("cards") == b.get("cards"))


def fetch(deck_path, output, *, catalog_path=None, manifest_path=None,
          seed_pairs=(), offline=False, refresh=False, request_batch=None):
    """Explicit import. Returns a deck manifest; raises before writing on errors.

    A callback can replace the HTTP batch in tests. Cache misses do not
    automatically trigger any API request outside this explicit function.
    """
    deck_path, output = Path(deck_path), Path(output)
    catalog_path = Path(catalog_path or output.parent / "shared_scryfall_catalog.json")
    manifest_path = Path(manifest_path or output.with_suffix(".manifest.json"))
    if offline and refresh:
        raise ValueError("Cannot refresh Scryfall in offline mode")
    raw = deck_path.read_bytes()
    names = deck_names(raw)
    deck_sha = hashlib.sha256(raw).hexdigest()
    catalog = CardCatalog(catalog_path)
    for seed_deck, seed_snapshot in seed_pairs:
        catalog.seed_snapshot(seed_snapshot, deck_path=seed_deck)

    resolved = {}
    missing = []
    for name in names:
        result = None if refresh else catalog.lookup(name)
        if result is None:
            missing.append(name)
        else:
            resolved[name] = result

    if missing and offline:
        raise ValueError("Missing offline identities: " + ", ".join(missing))

    requester = request_batch or scryfall_batch
    for offset in range(0, len(missing), 75):
        batch = missing[offset:offset + 75]
        try:
            returned = requester(batch)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            raise ValueError(f"Scryfall import failed for {batch!r}: {exc}") from exc
        if not isinstance(returned, list):
            raise ValueError("Scryfall importer expected a list of cards")
        for name in batch:
            card = _match_card(name, returned)
            oracle_id, revision = catalog.add_card(card)
            resolved[name] = (oracle_id, revision, card)
        # Delay only between HTTP batches, never between cached imports.
        if request_batch is None and offset + 75 < len(missing):
            time.sleep(0.12)

    now = datetime.now(timezone.utc).isoformat()
    pinned = [{"deck_name": name, "oracle_id": resolved[name][0],
               "revision": resolved[name][1]} for name in names]
    manifest = {"schema_version": SCHEMA_VERSION, "deck_sha256": deck_sha,
                "catalog_schema_version": SCHEMA_VERSION, "created_at": now,
                "cards": pinned}
    snapshot = {"source": "Scryfall collection API, exact card/face match",
                "retrieved_at": now, "deck_sha256": deck_sha,
                "distinct_requested": len(names),
                "cards": [{"deck_name": name, "card": resolved[name][2]} for name in names],
                "problems": []}

    # Fail closed if existing paths are pinned to a different deck or revision.
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not _same_manifest(old, manifest):
            raise ValueError("Manifest already pins different revisions; choose new output paths")
    if output.exists():
        old = json.loads(output.read_text(encoding="utf-8"))
        if (old.get("deck_sha256") != deck_sha
            or [(e.get("deck_name"), digest(e.get("card"))) for e in old.get("cards", [])]
               != [(e["deck_name"], digest(e["card"])) for e in snapshot["cards"]]):
            raise ValueError("Snapshot already pins different cards; choose new output paths")

    catalog.save()
    if not manifest_path.exists():
        atomic_json(manifest_path, manifest)
    if not output.exists():
        atomic_json(output, snapshot)

    print(json.dumps({"requested": len(names), "cache_hits": len(names) - len(missing),
                      "fetched": len(missing), "catalog": str(catalog_path),
                      "manifest": str(manifest_path), "snapshot": str(output)},
                     indent=2))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--catalog", type=Path, help="Shared offline Oracle-ID catalog")
    parser.add_argument("--manifest", type=Path, help="Pinned per-deck manifest")
    parser.add_argument("--seed-pair", nargs=2, metavar=("DECK", "SNAPSHOT"),
                        action="append", default=[], help="Seed from an existing, hash-matched snapshot")
    parser.add_argument("--offline", action="store_true", help="Require every identity to be cached")
    parser.add_argument("--refresh", action="store_true", help="Explicitly refresh all identities")
    args = parser.parse_args()
    try:
        fetch(args.deck, args.output, catalog_path=args.catalog,
              manifest_path=args.manifest, seed_pairs=args.seed_pair,
              offline=args.offline, refresh=args.refresh)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
