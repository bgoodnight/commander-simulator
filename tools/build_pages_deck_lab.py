"""Build the fully static Commander Deck Lab for GitHub Pages.

No API requests or third-party dependencies. Reads committed, validated, pinned
Scryfall data and generates authentic fixed-seed *observations*, never games.
The output directory is the sole publicly deployable artifact. Do not publish
any private workspace revisions, source code, or unreconciled card ownership.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from commander_sim.card_cache import CardCatalog, pinned_deck_entries
from commander_sim.deck_fixtures import FIXTURES, SHARED_CATALOG
from commander_sim.deck_lab_api import deck_detail
from commander_sim.card_name_catalog import read_name_catalog, DEFAULT_NAME_CATALOG
from commander_sim.observation import observe
from commander_sim.reviewed_rocks import reviewed_rock
from tools.publish_simulation_archive import validate_index

DEFAULT_SEEDS = (0, 1, 2, 3, 4, 5, 7, 11, 21, 42, 99)


def card_image(card, *, artwork=True):
    """Scryfall's canonical public card-image CDN path from cached printing ID.

    Printings with no real Scryfall UUID have no known card image; the UI uses
    a locally rendered fantasy-stone placeholder rather than guessing art.
    """
    ident = card.get("id")
    if not isinstance(ident, str) or len(ident) != 36:
        return None
    try:
        import uuid
        if str(uuid.UUID(ident)) != ident.lower():
            return None
    except (ValueError, AttributeError):
        return None
    flavor = "art_crop" if artwork else "normal"
    return f"https://cards.scryfall.io/{flavor}/front/{ident[0]}/{ident[1]}/{ident}.jpg"


def card_class(type_line):
    primary = type_line.split(" // ", 1)[0]
    for term in ("Land", "Creature", "Artifact", "Enchantment", "Planeswalker",
                 "Instant", "Sorcery", "Battle"):
        if term in primary:
            return term
    return "Other"


def card_record(card):
    return {
        "oracle_id": card["oracle_id"], "name": card["name"],
        "type_line": card.get("type_line", ""), "category": card_class(card.get("type_line", "")),
        "mana_value": card.get("cmc", 0), "mana_cost": card.get("mana_cost", ""),
        "color_identity": card.get("color_identity", []),
        "commander_legality": card.get("legalities", {}).get("commander", "unknown"),
        "oracle_text": card.get("oracle_text") or "Printed Oracle text unavailable from this snapshot.",
        "power": card.get("power"), "toughness": card.get("toughness"),
        "image": card_image(card, artwork=False), "art": card_image(card, artwork=True),
        "scryfall": card.get("scryfall_uri"),
        "is_basic": bool("Basic Land" in card.get("type_line", "")),
        "face_names": [face["name"] for face in card.get("card_faces", [])
                       if isinstance(face, dict) and face.get("name")],
    }


def build(output, *, catalog_path=SHARED_CATALOG, name_catalog_path=DEFAULT_NAME_CATALOG,
          seeds=DEFAULT_SEEDS, archive_source=None):
    output = Path(output)
    if output.resolve() in (ROOT.resolve(), (ROOT / "web").resolve()):
        raise ValueError("Build output must be a separate directory")
    if not seeds or any(type(x) is not int or x < 0 for x in seeds) or len(set(seeds)) != len(seeds):
        raise ValueError("Seeds must be distinct nonnegative integers")
    catalog = CardCatalog(catalog_path)
    decks = []
    identities = {}
    observations = {}
    for fixture in FIXTURES:
        checked = deck_detail(fixture.key, catalog_path=catalog_path)
        pinned = pinned_deck_entries(fixture.deck_path, fixture.manifest_path, catalog_path)
        if checked["physical_cards"] != 100:
            raise ValueError("Incorrect deck size: " + fixture.key)
        for item in pinned:
            identities[item["card"]["oracle_id"]] = card_record(item["card"])
        cards = []
        for item in checked["cards"]:
            card = catalog.lookup(item["name"])
            if card is None:
                raise ValueError("Missing cached card: " + item["name"])
            cards.append({"name": item["name"], "oracle_id": card[0],
                          "qty": item["quantity"], "zone": item["zone"]})
        commander = next((item for item in cards if item["zone"] == "Commander"), None)
        if commander is None:
            raise ValueError("Missing Commander: " + fixture.key)
        commander_card = next(item["card"] for item in pinned if item["card"]["oracle_id"] == commander["oracle_id"])
        modeled_rocks = [item["card"]["oracle_id"] for item in pinned
                         if reviewed_rock(item["deck_name"], item["card"], commander_card.get("color_identity", [])) is not None]
        decks.append({
            "key": fixture.key, "commander": fixture.commander,
            "commander_id": commander["oracle_id"], "label": fixture.status,
            "deck_sha256": checked["deck_sha256"], "cards": cards,
            "types": checked["by_type"], "card_count": checked["physical_cards"],
            "snapshot_sha256": checked["source_snapshot_sha256"], "modeled_rocks": modeled_rocks,
        })
        # A fixed, reproducible menu of cache-backed observations. No browser
        # button will or can generate a new seed; never imply otherwise.
        observations[fixture.key] = {}
        for seed in seeds:
            result = observe(fixture.deck_path, fixture.snapshot_path,
                             commander=fixture.commander, seed=seed, turns=6)
            if result["mode"] != "observation" or any(t["playable_now"] for t in result["trace"]):
                raise ValueError("Unexpected live game action in static observation")
            if result["deck_sha256"] != checked["deck_sha256"]:
                raise ValueError("Observation uses wrong deck revision")
            observations[fixture.key][str(seed)] = result
    names = list(read_name_catalog(name_catalog_path))
    if len(names) < 1000:
        raise ValueError("Full offline Scryfall name catalog must be initialized")
    dataset = {
        "format": "commander-deck-lab-static-v1",
        "data_mode": "precomputed_observation_only",
        "seeds": list(seeds),
        "decks": decks, "cards": identities,
        "limitations": [
            "No browser-side Magic rules execution",
            "No new simulations or actual spells/combat",
            "Printed characteristics and total-mana candidates only",
            "Edits made in this browser are local and are NOT simulated",
            "Card images are loaded from Scryfall when connected",
        ],
    }
    # Metadata-only card names from Scryfall are not validated full identities.
    static = ROOT / "web" / "pages"
    if not static.is_dir():
        raise ValueError("Missing static Deck Lab source")
    output.mkdir(parents=True, exist_ok=True)
    # Four real HTML routes: index.html and summary.html display the
    # attractive Deck Summary by default; results.html retains the
    # interpretive observation archive and editor.html the deck workshop.
    # The same source shell selects content by pathname without a server.
    for filename in ("app.js", "results_insights.js", "brackets.js", "style.css", "game-changers.json"):
        shutil.copy2(static / filename, output / filename)
    for filename in ("index.html", "summary.html", "results.html", "editor.html"):
        shutil.copy2(static / "index.html", output / filename)
    (output / ".nojekyll").write_text("", encoding="utf-8")
    def write_json(name, obj):
        (output / name).write_text(
            json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
            encoding="utf-8",
        )
    write_json("decks.json", dataset)
    write_json("observations.json", observations)
    write_json("names.json", names)
    # Optional, separately versioned simulations. Never infer game results from
    # observations or overwrite existing UI cache files with new run formats.
    archive_source = (ROOT / "web/pages/data/simulation-archive"
                      if archive_source is None else Path(archive_source))
    archive_files = []
    if (archive_source / "manifest.json").is_file():
        index = validate_index(archive_source)
        public_root = output / "simulation-data"
        for release in index["releases"]:
            for entry in release["decks"].values():
                archive_files.extend((entry["manifest"], entry["runs"]))
        archive_files = ["manifest.json", *sorted(set(archive_files))]
        for relative in archive_files:
            target = public_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(archive_source / relative, target)
        validate_index(public_root)
    # Results are precomputed separately and must match the exported deck revisions.
    batches = json.loads((static / "data" / "bounded-batches.json").read_text(encoding="utf-8"))
    for key, batch in batches["decks"].items():
        deck = next(d for d in decks if d["key"] == key)
        if batch["deck_sha256"] != deck["deck_sha256"]:
            raise ValueError("Bounded batch uses wrong deck revision: " + key)
        runs = json.loads((static / "data" / f"bounded-runs-{key}.json").read_text(encoding="utf-8"))
        if (len(runs) != batch["seed_count"] or
            {r["seed"] for r in runs} != set(range(batch["seed_count"])) or
            any(r["deck_key"] != key or r["deck_sha256"] != deck["deck_sha256"] or
                r["mode"] != "bounded_authoritative_early_actions" or
                len(r["events"]) != len(batch["turns"]) or
                len(r["state_snapshots"]) != len(batch["turns"]) for r in runs)):
            raise ValueError("Invalid bounded run archive: " + key)
    write_json("bounded-batches.json", batches)
    for key in batches["decks"]:
        shutil.copy2(static / "data" / f"bounded-runs-{key}.json", output / f"bounded-runs-{key}.json")
    manifest = {
        "format": dataset["format"], "decks": len(decks),
        "cards": len(identities), "names": len(names),
        "seeds": list(seeds),
        "asset_sha256": {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                         for name in ("decks.json", "observations.json", "names.json", "bounded-batches.json",
                                      "index.html", "summary.html", "results.html", "editor.html",
                                      "app.js", "results_insights.js", "brackets.js", "style.css", "game-changers.json",
                                      *(f"bounded-runs-{key}.json" for key in batches["decks"]),
                                      *(f"simulation-data/{relative}" for relative in archive_files))},
        "note": "Published data includes only approved six canonical decks and fixed-seed observations.",
    }
    write_json("build-manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "_pages_dist")
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
