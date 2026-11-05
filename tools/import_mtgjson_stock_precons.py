"""Import an explicit, auditable stock Commander opponent expansion from MTGJSON.

An *offline setup* command only: never fetch during a game. The curated allowlist
is an identity gate, not a guarantee that Gorge implements each card's rules.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

from tools.fetch_gorge_precons import validate_precon

BASE = "https://mtgjson.com/api/v5"
# Display names must match a single official Commander Deck product in DeckList.
# The commander and color identity must agree with our versioned role metadata.
EXPANDED_STOCK = {
    "explorers-of-the-deep": "Explorers of the Deep",
    "veloci-ramp-tor": "Veloci-ramp-tor",
    "quick-draw": "Quick Draw",
    "desert-bloom": "Desert Bloom",
    "creative-energy": "Creative Energy",
    "squirreled-away": "Squirreled Away",
    "endless-punishment": "Endless Punishment",
    "tricky-terrain": "Tricky Terrain",
}


def _download(url, fetch):
    raw = fetch(url)
    if not isinstance(raw, bytes):
        raise ValueError("MTGJSON response must be raw bytes")
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def select_entries(index, names=EXPANDED_STOCK):
    if not isinstance(index, dict) or not isinstance(index.get("data"), list):
        raise ValueError("Invalid MTGJSON DeckList")
    chosen = {}
    for slug, display in names.items():
        matches = [row for row in index["data"]
                   if row.get("type") == "Commander Deck"
                   and row.get("name", "").casefold() == display.casefold()
                   and isinstance(row.get("fileName"), str)]
        if len(matches) != 1:
            raise ValueError(f"{slug}: expected one stock Commander Deck catalog entry; found {len(matches)}")
        chosen[slug] = matches[0]
    return chosen


def convert(doc, slug, metadata):
    data = doc.get("data")
    if not isinstance(data, dict) or data.get("type") != "Commander Deck":
        raise ValueError(f"{slug}: not a Commander Deck")
    commander = data.get("commander")
    main = data.get("mainBoard")
    if not isinstance(commander, list) or len(commander) != 1 or not isinstance(main, list):
        raise ValueError(f"{slug}: requires one commander and a main board")
    lead = commander[0]
    if type(lead.get("count")) is not int or lead["count"] != 1:
        raise ValueError(f"{slug}: commander quantity must be one")
    name = lead.get("name")
    if name != metadata["commander"]:
        raise ValueError(f"{slug}: unexpected printed commander: {name}")
    if set(lead.get("colorIdentity", [])) != set(metadata["color_identity"]):
        raise ValueError(f"{slug}: commander color identity mismatch")
    names = set()
    rows = []
    for card in [lead, *main]:
        card_name, qty = card.get("name"), card.get("count")
        if not isinstance(card_name, str) or not card_name or type(qty) is not int or qty < 1:
            raise ValueError(f"{slug}: malformed card quantity/name")
        if card_name in names:
            raise ValueError(f"{slug}: repeated main-deck card name {card_name}")
        names.add(card_name)
        rows.append({"name": card_name, "count": qty})
    deck = {"format": "commander", "commander": name, "cards": rows}
    validate_precon(deck, slug)
    if data.get("sideBoard"):
        # Extra display commanders, tokens, planes and supplemental cards are
        # not silently incorporated into the fixed stock 100-card deck.
        raise ValueError(f"{slug}: unexpected sideboard; review product manually")
    return deck


def import_expanded(out: Path, *, registry=None, fetch=None):
    from tools.commander_deck_library import load_library, by_key
    fetch = fetch or (lambda url: urlopen(url, timeout=45).read())
    registry = registry or load_library()
    known = by_key(registry)
    for slug in EXPANDED_STOCK:
        if slug not in known or known[slug]["role"] != "opponent" or known[slug]["provenance"] != "stock_precon":
            raise ValueError(f"{slug}: missing approved stock opponent metadata")
    index, index_hash = _download(BASE + "/DeckList.json", fetch)
    chosen = select_entries(index)
    output = {}
    manifest = []
    for slug, entry in chosen.items():
        url = BASE + "/decks/" + entry["fileName"] + ".json"
        doc, sha = _download(url, fetch)
        if doc.get("data", {}).get("code") != entry.get("code"):
            raise ValueError(f"{slug}: source deck code mismatch")
        deck = convert(doc, slug, known[slug])
        output[slug] = deck
        manifest.append({
            "key": slug, "source": url, "source_sha256": sha,
            "catalog_sha256": index_hash, "mtgjson_filename": entry["fileName"],
            "release_date": entry.get("releaseDate"), "commander": deck["commander"],
            "cards": 100, "provenance": "stock_precon",
            "deck_sha256": hashlib.sha256((json.dumps(deck, sort_keys=True) + "\n").encode()).hexdigest()
        })
    # Fail-closed, all-or-nothing validation BEFORE writing output.
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for slug, deck in output.items():
        (out / (slug + ".json")).write_text(json.dumps(deck, indent=2, sort_keys=True) + "\n")
    (out / "expanded_stock_manifest.json").write_text(json.dumps({
        "schema": "gorge-expanded-stock-precon-v1", "catalog_source": BASE + "/DeckList.json",
        "decks": manifest,
        "status": "decklist_identity_validated_not_simulation_rules_certified"
    }, indent=2, sort_keys=True) + "\n")
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    print(json.dumps({"decks": import_expanded(args.out)}, indent=2))
