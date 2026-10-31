"""M1: explicit, cache-first import of canonical commander deck variants.

Default is OFFLINE: seed previously verified snapshots and report missing names.
Only --fetch-missing enables Scryfall network calls, never during simulation.

Usage:
  python tools/import_deck_fixtures.py
  python tools/import_deck_fixtures.py --fetch-missing
  python tools/import_deck_fixtures.py --fixture mortarion_current --fetch-missing
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from commander_sim.card_cache import CardCatalog, deck_names
from commander_sim.deck_fixtures import FIXTURES, LEGACY_SEEDS, SHARED_CATALOG
from commander_sim.snapshots import validate_snapshot
from commander_sim.observation import observe
from tools.fetch_deck_identities import fetch


def prepare(*, fetch_missing=False, selected=None, catalog_path=SHARED_CATALOG,
            output_dir=None, request_batch=None):
    """Return a report per requested deck; only explicit online imports may fetch.

    Seed historical verified snapshots offline before any missing-name requests.
    If offline and a fixture needs missing identities, report missing names but
    continue to other fixtures; never claim that fixture has a valid manifest.
    """
    selected = set(selected) if selected is not None else {f.key for f in FIXTURES}
    valid = {f.key for f in FIXTURES}
    if unknown := selected - valid:
        raise ValueError("Unknown fixture keys: " + ", ".join(sorted(unknown)))
    catalog_path = Path(catalog_path)
    catalog = CardCatalog(catalog_path)
    for deck, snapshot in LEGACY_SEEDS:
        catalog.seed_snapshot(ROOT / snapshot, deck_path=ROOT / deck)
    catalog.save()
    reports = []
    for fixture in FIXTURES:
        if fixture.key not in selected:
            continue
        names = deck_names(fixture.deck_path.read_bytes())
        missing = [name for name in names if catalog.lookup(name) is None]
        destination = (Path(output_dir) / (fixture.key + "_m1_scryfall.json")
                       if output_dir is not None else fixture.snapshot_path)
        report = {"key": fixture.key, "commander": fixture.commander,
                  "deck": fixture.relative_path, "physical_cards": None,
                  "distinct_names": len(names), "missing_before_import": len(missing),
                  "unresolved_names": missing, "status": "missing_metadata",
                  "snapshot": str(destination), "manifest": str(destination.with_suffix(".manifest.json"))}
        try:
            if missing and not fetch_missing:
                reports.append(report)
                continue
            result = fetch(fixture.deck_path, destination,
                           catalog_path=catalog_path, offline=not fetch_missing,
                           request_batch=request_batch)
            checked = validate_snapshot(fixture.deck_path, destination,
                                        commander=fixture.commander)
            trace = observe(fixture.deck_path, destination,
                            commander=fixture.commander, turns=6, seed=0)
            if (checked.deck.count != 100 or len(trace["trace"]) != 6
                or any(t["playable_now"] for t in trace["trace"])):
                raise ValueError("M1 import/observation invariants failed")
            report.update(status="validated_observation", physical_cards=checked.deck.count,
                          unresolved_names=[], fetched=result["fetched"],
                          snapshot_sha256=checked.snapshot_sha256,
                          deck_sha256=checked.deck_sha256,
                          observation_seed=0, observation_turns=6,
                          not_live_gameplay=True)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            report.update(status="error", error=str(exc))
        reports.append(report)
        # A successful import updates the shared catalog on disk; subsequent
        # decks must see newly resolved aliases to avoid duplicate requests.
        catalog = CardCatalog(catalog_path)
    return {"mode": "explicit_online_import" if fetch_missing else "offline_only",
            "catalog": str(catalog_path), "decks": reports,
            "validated": sum(x["status"] == "validated_observation" for x in reports),
            "missing": sum(x["status"] == "missing_metadata" for x in reports),
            "errors": sum(x["status"] == "error" for x in reports)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-missing", action="store_true",
                        help="Explicitly request missing Scryfall identities over network")
    parser.add_argument("--fixture", action="append", choices=[f.key for f in FIXTURES])
    parser.add_argument("--catalog", type=Path, default=SHARED_CATALOG)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--report", type=Path,
                        help="Save JSON report (no direct card-data API requests)")
    args = parser.parse_args()
    report = prepare(fetch_missing=args.fetch_missing, selected=args.fixture,
                     catalog_path=args.catalog, output_dir=args.output_dir)
    print(json.dumps(report, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if report["missing"] == report["errors"] == 0 else 1)
