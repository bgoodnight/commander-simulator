"""Read-only local Deck Lab data API backed by immutable M1 deck snapshots.

No card import, Scryfall access, deck writes or executable Magic rules. This
API reports *observation*, never mislabels candidate cards as legal casts.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from .card_cache import card_aliases, pinned_deck_entries
from .deck_fixtures import FIXTURES, EXPERIMENTAL_FIXTURES, SHARED_CATALOG
from .fixture_inventory import inventory, fixture_observation
from .snapshots import validate_snapshot


def _get_fixture(key):
    fixture = next((f for f in (*FIXTURES, *EXPERIMENTAL_FIXTURES) if f.key == key), None)
    if fixture is None:
        raise ValueError("Unknown deck fixture: " + str(key))
    return fixture


def deck_detail(key, *, catalog_path=SHARED_CATALOG, output_dir=None):
    """Verified card inventory for one canonical deck; no rule execution."""
    fixture = _get_fixture(key)
    snapshot_path = (
        Path(output_dir) / fixture.snapshot_path.name
        if output_dir is not None else fixture.snapshot_path
    )
    entries = pinned_deck_entries(
        fixture.deck_path, snapshot_path.with_suffix(".manifest.json"), catalog_path
    )
    checked = validate_snapshot(
        fixture.deck_path, snapshot_path, commander=fixture.commander
    )
    by_alias = {}
    for entry in entries:
        for alias in card_aliases(entry["card"]):
            previous = by_alias.setdefault(alias, entry["card"])
            if previous["oracle_id"] != entry["card"]["oracle_id"]:
                raise ValueError("Ambiguous source alias in verified deck")
    cards = []
    types = Counter()
    for section, name, quantity in checked.deck.cards:
        card = by_alias.get(name)
        if card is None:
            raise ValueError("Unresolved verified card: " + name)
        type_line = card["type_line"]
        cards.append({
            "zone": section, "name": name, "quantity": quantity,
            "type_line": type_line, "mana_value": card.get("cmc"),
            "mana_cost": card.get("mana_cost", ""),
            "oracle_id": card["oracle_id"],
            "abilities_status": "not_assessed",
        })
        primary = type_line.split(" // ", 1)[0]
        card_type = ("Land" if "Land" in primary else
                     "Creature" if "Creature" in primary else
                     "Artifact" if "Artifact" in primary else
                     "Enchantment" if "Enchantment" in primary else
                     "Instant" if "Instant" in primary else
                     "Sorcery" if "Sorcery" in primary else "Other")
        types[card_type] += quantity
    return {
        "key": key, "commander": fixture.commander,
        "label": fixture.status, "physical_cards": checked.deck.count,
        "distinct_names": len(cards), "source_snapshot_sha256": checked.snapshot_sha256,
        "deck_sha256": checked.deck_sha256, "by_type": dict(sorted(types.items())),
        "cards": cards, "actual_gameplay_available": False,
        "ability_coverage": "not assessed by card metadata import",
    }


def catalog_response(*, catalog_path=SHARED_CATALOG, output_dir=None):
    return inventory(catalog_path=catalog_path, output_dir=output_dir)


def observation_response(key, *, seed=0, turns=6, mulligan='keep', catalog_path=SHARED_CATALOG,
                         output_dir=None):
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("Seed must be an integer")
    if not isinstance(turns, int) or isinstance(turns, bool) or not 1 <= turns <= 20:
        raise ValueError("The Deck Lab observation horizon must be 1–20 turns")
    return fixture_observation(
        key, catalog_path=catalog_path, output_dir=output_dir,
        seed=seed, turns=turns, mulligan=mulligan
    )
