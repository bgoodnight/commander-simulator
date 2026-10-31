"""Local, reversible Deck Lab U1 deck variants.

Canonical source decklists are read-only. Every saved variation is a new deck
file and SHA-pinned, offline card snapshot. All validation is authoritative
DeckProvider logic, not a parallel rule implementation in the browser.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import json
import re

from .card_cache import CardCatalog, atomic_json
from .deck_fixtures import FIXTURES, ROOT, SHARED_CATALOG
from .deck_lab_api import deck_detail
from .decks import DeckProvider

DEFAULT_WORKSPACE = ROOT / "workspace" / "deck_lab"
BASICS = frozenset({
    "Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes",
    "Snow-Covered Plains", "Snow-Covered Island", "Snow-Covered Swamp",
    "Snow-Covered Mountain", "Snow-Covered Forest",
})


def _fixture(key):
    result = next((f for f in FIXTURES if f.key == key), None)
    if result is None:
        raise ValueError("Unknown canonical deck: " + str(key))
    return result


def _changes_checked(changes):
    if not isinstance(changes, list) or len(changes) > 80:
        raise ValueError("Changes must be a list of at most 80 swaps")
    clean = []
    for item in changes:
        if not isinstance(item, dict) or set(item) != {"remove", "add"}:
            raise ValueError("Every change must contain remove and add")
        old, new = item["remove"], item["add"]
        if any(not isinstance(v, str) or not v.strip() or len(v) > 200
               for v in (old, new)):
            raise ValueError("Each swap must contain two card names")
        clean.append((old.strip(), new.strip()))
    return clean


def _validation_records(catalog, names):
    """Use the existing DeckProvider's strict Commander validation."""
    records = []
    for name in names:
        result = catalog.lookup(name)
        if result is None:
            raise ValueError("Card metadata unavailable; prepare/import first: " + name)
        oracle_id, revision, card = result
        row = {
            "name": card["name"], "oracle_id": oracle_id,
            "type_line": card["type_line"],
            "color_identity": card["color_identity"],
            "commander_legality": card.get("legalities", {}).get("commander"),
        }
        if name != card["name"]:
            row["deck_name"] = name
            row["card_faces"] = card.get("card_faces", [])
        records.append(row)
    return records


def compose_draft(base_key, changes, *, catalog_path=SHARED_CATALOG):
    """Build a proposed 100-card deck; fail closed on invalid changes.

    This service accepts *cached exact names only*. A future U2 may invoke
    prepare_theorycraft_deck before the save to import new metadata, but this
    U1 endpoint makes no external requests.
    """
    fixture = _fixture(base_key)
    swaps = _changes_checked(changes)
    original = deck_detail(base_key, catalog_path=catalog_path)
    counts = Counter({item["name"]: item["quantity"]
                      for item in original["cards"] if item["zone"] != "Commander"})
    commander = fixture.commander
    catalog = CardCatalog(catalog_path)
    for old, new in swaps:
        if old == commander or new == commander:
            raise ValueError("Changing the commander is not supported in U1")
        if old not in counts or counts[old] < 1:
            raise ValueError("Card is no longer in the draft: " + old)
        if catalog.lookup(new) is None:
            raise ValueError("Card metadata unavailable; prepare/import first: " + new)
        counts[old] -= 1
        if not counts[old]:
            del counts[old]
        counts[new] += 1
    # Stable, readable canonical output. A new version does not overwrite a
    # canonical source deck or accidentally inherit stale section-count labels.
    lines = ["# Local Deck Lab draft based on " + base_key,
             "Commander", "1 " + commander, "Library"]
    for name in sorted(counts, key=str.casefold):
        lines.append(str(counts[name]) + " " + name)
    text = "\n".join(lines) + "\n"
    used = [commander, *counts]
    records = _validation_records(catalog, used)
    cmd = catalog.lookup(commander)
    if cmd is None:
        raise ValueError("Commander not in the local catalog")
    identity = frozenset(cmd[2]["color_identity"])
    provider = DeckProvider(records, commander=commander, color_identity=identity)
    validated = provider.parse(text)
    # Also detect printed aliases of one Oracle ID when supplied twice under
    # different names. The shared provider checks duplicate Oracle IDs.
    before = Counter({item["name"]: item["quantity"] for item in original["cards"]
                      if item["zone"] != "Commander"})
    difference = sorted(({"name": name, "before": before[name], "after": counts[name],
                           "delta": counts[name] - before[name]}
                         for name in (before.keys() | counts.keys())
                         if before[name] != counts[name]), key=lambda x: x["name"].casefold())
    return {"base_key": base_key, "commander": commander,
            "deck_text": text, "physical_cards": validated.count,
            "distinct_names": len(counts) + 1,
            "deck_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "diff": difference, "swaps": len(swaps),
            "metadata_only": True, "actual_gameplay_available": False}


def save_draft(base_key, changes, title, *, catalog_path=SHARED_CATALOG,
               workspace=DEFAULT_WORKSPACE):
    """Versioned Save As; existing deck/version files are never overwritten."""
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 70:
        raise ValueError("Version name must be 1–70 characters")
    slug = re.sub(r"[^a-z0-9]+", "-", title.strip().lower()).strip("-")[:45]
    if not slug:
        raise ValueError("Version title must contain letters or digits")
    draft = compose_draft(base_key, changes, catalog_path=catalog_path)
    workspace = Path(workspace)
    stem = slug + "-" + draft["deck_sha256"][:16]
    deck_path = workspace / (stem + ".txt")
    meta_path = workspace / (stem + ".deck.json")
    if deck_path.exists() or meta_path.exists():
        raise ValueError("This saved version already exists; choose another title")
    # Save an immutable new deck first; if offline snapshot validation fails,
    # delete the newly-created deck rather than leave an invalid working copy.
    workspace.mkdir(parents=True, exist_ok=True)
    from .card_discovery import prepare_theorycraft_deck
    try:
        deck_path.write_text(draft["deck_text"], encoding="utf-8")
        prepared = prepare_theorycraft_deck(
            deck_path, draft["commander"], catalog_path=catalog_path,
            output_dir=workspace / "metadata", auto_fetch=False,
        )
        record = {"title": title.strip(), "base_key": base_key,
                  "deck_path": str(deck_path), "deck_sha256": draft["deck_sha256"],
                  "commander": draft["commander"], "changes": changes,
                  "snapshot": prepared["snapshot"], "manifest": prepared["manifest"],
                  "metadata_only": True}
        atomic_json(meta_path, record)
        return record
    except Exception:
        if deck_path.exists() and not meta_path.exists():
            deck_path.unlink()
        raise


def saved_versions(*, workspace=DEFAULT_WORKSPACE):
    """List versions in the workspace, but never mutate canonical decks."""
    workspace = Path(workspace)
    if not workspace.exists():
        return []
    versions = []
    for path in sorted(workspace.glob("*.deck.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        deck_path = Path(item["deck_path"])
        if deck_path.parent.resolve() != workspace.resolve():
            raise ValueError("Workspace path outside configured directory")
        if not deck_path.is_file() or hashlib.sha256(deck_path.read_bytes()).hexdigest() != item["deck_sha256"]:
            raise ValueError("Saved deck has changed since validation: " + str(deck_path))
        versions.append(item)
    return versions
