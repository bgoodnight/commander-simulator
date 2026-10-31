"""One-shot Scryfall *names-only* catalog for offline deck-editor autocomplete.

Names are suggestions, not Oracle IDs or validated executable card metadata.
Use an explicit refresh operation to fetch the catalog once, then filter all
names locally as the user types. Full metadata is fetched separately only
when a selected card is added to a prepared deck.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .card_cache import atomic_json, canonical_bytes
from .deck_fixtures import CARD_DATA

DEFAULT_NAME_CATALOG = CARD_DATA / "scryfall_card_names.json"


def read_name_catalog(path=DEFAULT_NAME_CATALOG):
    """Read a locally pinned name list; missing means no extended suggestions."""
    path = Path(path)
    if not path.exists():
        return ()
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError("Invalid offline card-name catalog")
    names = record.get("names")
    if (record.get("schema_version") != 1 or
        record.get("source") != "Scryfall card-names catalog" or
        not isinstance(names, list) or
        any(not isinstance(x, str) or not x.strip() or len(x) > 250 for x in names) or
        len(set(names)) != len(names) or
        record.get("sha256") != hashlib.sha256(canonical_bytes(names)).hexdigest()):
        raise ValueError("Invalid or modified offline card-name catalog")
    return tuple(names)


def refresh_name_catalog(path=DEFAULT_NAME_CATALOG, *, opener=None):
    """Explicit network refresh; never invoked by autocomplete or a game."""
    request = Request(
        "https://api.scryfall.com/catalog/card-names",
        headers={
            "User-Agent": "CommanderSimulator/1.0 (explicit names catalog refresh)",
            "Accept": "application/json",
        },
    )
    try:
        with (opener or urlopen)(request, timeout=30) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise ValueError("Could not refresh Scryfall card-name catalog") from exc
    names = payload.get("data") if isinstance(payload, dict) else None
    if (not isinstance(names, list) or not names or
        any(not isinstance(name, str) or not name.strip() or len(name) > 250
            for name in names)):
        raise ValueError("Invalid Scryfall card-name catalog response")
    ordered = sorted(set(names), key=lambda x: (x.casefold(), x))
    record = {
        "schema_version": 1,
        "source": "Scryfall card-names catalog",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(canonical_bytes(ordered)).hexdigest(),
        "names": ordered,
    }
    atomic_json(path, record)
    return {"names": len(ordered), "path": str(path),
            "sha256": record["sha256"]}
