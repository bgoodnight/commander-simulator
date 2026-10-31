"""Cache-first card discovery for theorycrafting and future Deck Lab editing.

Metadata retrieval occurs at the *deck preparation* boundary, never in a
simulation turn, snapshot validator, card lookup, or local suggestion query.
The Scryfall API supplies identity and printed metadata, not executable rules.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from .card_cache import CardCatalog, card_aliases
from .deck_fixtures import SHARED_CATALOG
from .card_name_catalog import DEFAULT_NAME_CATALOG, read_name_catalog


def local_suggestions(query, *, catalog_path=SHARED_CATALOG,
                      name_catalog_path=DEFAULT_NAME_CATALOG, limit=20):
    """Autocomplete from Scryfall's once-fetched name list and cached records.

    A name-only suggestion is *not* a verified Oracle-ID record. Selecting it
    in a saved deck causes metadata preflight to fetch/validate that specific
    identity once. This function is entirely offline.
    """
    if not isinstance(query, str) or len(query) > 150:
        raise ValueError("Search must be text of at most 150 characters")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 40:
        raise ValueError("Suggestion limit must be between 1 and 40")
    needle = query.strip().casefold()
    if len(needle) < 2:
        return []
    catalog = CardCatalog(catalog_path)
    matches = []
    by_name = set()
    for oracle_id, revision in catalog.current.items():
        card = catalog.get_pinned(oracle_id, revision)
        aliases = card_aliases(card)
        eligible = [name for name in aliases if needle in name.casefold()]
        if not eligible:
            continue
        best = min(eligible, key=lambda name: (
            0 if name.casefold() == needle else
            1 if name.casefold().startswith(needle) else 2,
            len(name), name.casefold()
        ))
        score = (0 if best.casefold() == needle else
                 1 if best.casefold().startswith(needle) else 2)
        by_name.update(name.casefold() for name in aliases)
        matches.append((score, best.casefold(), {
            "name": best, "canonical_name": card["name"],
            "oracle_id": oracle_id, "source": "local_cache",
            "requires_metadata_import": False,
            "type_line": card.get("type_line", ""),
        }))
    for name in read_name_catalog(name_catalog_path):
        if name.casefold() in by_name or needle not in name.casefold():
            continue
        score = (0 if name.casefold() == needle else
                 1 if name.casefold().startswith(needle) else 2)
        matches.append((score, name.casefold(), {
            "name": name, "canonical_name": name,
            "oracle_id": None, "source": "scryfall_name_catalog",
            "requires_metadata_import": True,
            "type_line": None,
        }))
    matches.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in matches[:limit]]


def online_name_suggestions(query, *, opener=None):
    """Explicitly requested remote name suggestions; no card metadata writes.

    Not called from the local typing endpoint or simulation. A future UI must
    opt in to remote suggestions and debounce requests independently.
    """
    if not isinstance(query, str) or len(query) > 150:
        raise ValueError("Search must be text of at most 150 characters")
    query = query.strip()
    if len(query) < 2:
        return []
    url = "https://api.scryfall.com/cards/autocomplete?" + urlencode({"q": query})
    request = Request(url, headers={
        "User-Agent": "CommanderSimulator/1.0 (explicit name suggestion)",
        "Accept": "application/json"
    })
    transport = opener or urlopen
    try:
        with transport(request, timeout=15) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise ValueError("Card name suggestion request failed") from exc
    names = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
        raise ValueError("Invalid card-name suggestion response")
    return names[:20]


def prepare_theorycraft_deck(
    deck_path, commander, *, catalog_path=SHARED_CATALOG,
    output_dir=None, auto_fetch=True, request_batch=None,
):
    """Prepare a new deck once, then pin its exact cached card revisions.

    auto_fetch=True matches the user's first-run preference. Calling this
    method is a deliberate *preflight/import*, before any gameplay. Subsequent
    runs use saved snapshot/manifest and cannot fetch without another preflight.
    No invalid or ambiguous name is silently guessed or fuzzy corrected.
    """
    from .snapshots import validate_snapshot
    from tools.fetch_deck_identities import fetch

    if not isinstance(commander, str) or not commander.strip():
        raise ValueError("Commander is required")
    deck_path = Path(deck_path)
    raw = deck_path.read_bytes()
    deck_sha = hashlib.sha256(raw).hexdigest()
    output_dir = Path(output_dir) if output_dir is not None else (
        deck_path.parent / ".commander_metadata"
    )
    # Key the artifact on the entire deck hash, preserving every earlier
    # variant's manifest and replay when a user edits or renames the list.
    snapshot_path = output_dir / (deck_sha + ".json")
    result = fetch(
        deck_path, snapshot_path, catalog_path=catalog_path,
        offline=not auto_fetch, request_batch=request_batch,
    )
    verified = validate_snapshot(deck_path, snapshot_path, commander=commander)
    if verified.deck.count != 100:
        raise ValueError("Expected a full 100-card Commander deck")
    return {
        "deck_sha256": deck_sha,
        "snapshot": str(snapshot_path),
        "manifest": str(snapshot_path.with_suffix(".manifest.json")),
        "catalog": str(catalog_path),
        "commander": verified.deck.commander,
        "physical_cards": verified.deck.count,
        "new_identities_fetched": result["fetched"],
        "cache_hits": result["cache_hits"],
        "metadata_only": True,
        "gameplay_ready": False,
    }
