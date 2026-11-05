"""Stage the Oracle-enriched 60-precon panel for explicit Gorge certification.

Produces an immutable-source qualification queue, never live opponent roles.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ENRICHMENT_SCHEMA = "gorge-precon-card-metadata-enrichment-v1"
PANEL_SCHEMA = "gorge-opponent-selection-assessment-v1"
QUEUE_SCHEMA = "gorge-precon-qualification-queue-v1"


def build_queue(enrichment: dict, panel: dict) -> dict:
    if enrichment.get("schema") != ENRICHMENT_SCHEMA or panel.get("schema") != PANEL_SCHEMA:
        raise ValueError("Unexpected enrichment or panel schema")
    if enrichment.get("oracle_bulk_sha256") != panel.get("source_oracle_sha256"):
        raise ValueError("Oracle snapshot mismatch")
    if enrichment.get("source_catalog_commit") != panel.get("source_catalog_commit"):
        raise ValueError("Catalog provenance mismatch")
    if enrichment.get("as_of") != panel.get("as_of"):
        raise ValueError("Release cutoff mismatch")
    if panel.get("status") != "provisional_not_gorge_qualified":
        raise ValueError("Expected provisional, non-activated selection")
    selected = panel.get("shortlist", [])
    if len(selected) != 60 or len({r["key"] for r in selected}) != 60:
        raise ValueError("Exactly 60 distinct selected decks are required")
    catalog = {r["key"]: r for r in enrichment["decks"]}
    result = []
    for index, choice in enumerate(selected, start=1):
        key = choice["key"]
        if key not in catalog:
            raise ValueError(f"Unrecognized selected deck: {key}")
        deck = catalog[key]
        if deck["is_duplicate_variant"] or deck["active_opponent"]:
            raise ValueError(f"Duplicate or active opponent in staging panel: {key}")
        if deck.get("color_identity") is None:
            raise ValueError(f"Unresolved commander identity: {key}")
        cards = deck["cards"]
        if sum(card["count"] for card in cards) != 100:
            raise ValueError(f"Invalid 100-card source decklist: {key}")
        if deck["cards_resolved"] != sum(c["count"] for c in cards if c["resolved"]):
            raise ValueError(f"Oracle resolution count mismatch: {key}")
        # Preserve exact cards and original Scryfall annotation, including unknowns.
        source_hash = hashlib.sha256(
            json.dumps([(c["name"], c["count"]) for c in cards],
                       separators=(",", ":"), ensure_ascii=False).encode()
        ).hexdigest()
        result.append({
            "priority": index, "key": key, "name": deck["name"],
            "commander": deck["commander"], "set_code": deck["set_code"],
            "release_date": deck["release_date"],
            "color_identity": deck["color_identity"],
            "cards_resolved": deck["cards_resolved"],
            "cards_total": 100, "oracle_complete": deck["cards_resolved"] == 100,
            "unresolved_card_names": [c["name"] for c in cards if not c["resolved"]],
            "oracle_card_annotations": cards,
            "mechanic_counts_exploratory": deck["counts"],
            "mechanic_keywords": deck["mechanic_keywords"],
            "nonland_mean_mana_value": deck["nonland_mean_mana_value"],
            "decklist_sha256": source_hash,
            "primary_archetype": None, "secondary_archetypes": [],
            "archetype_review": "pending",
            "gorge_parse": "not_tested", "gorge_rules": "not_tested",
            "gorge_pilot": "not_tested", "gameplay_fidelity": "not_tested",
            "qualification": "queued_not_approved",
            "active_opponent": False,
        })
    return {
        "schema": QUEUE_SCHEMA,
        "status": "certification_pending_no_activation",
        "as_of": enrichment["as_of"],
        "source_catalog_commit": enrichment["source_catalog_commit"],
        "oracle_bulk_sha256": enrichment["oracle_bulk_sha256"],
        "oracle_bulk_metadata": enrichment.get("oracle_bulk_metadata", {}),
        "selection_schema": panel["schema"],
        "selection_method": panel["selection_method"],
        "panel_size": len(result),
        "qualification_requirements": [
            "Complete and unambiguous card identity resolution",
            "Curated and reviewed strategic archetype",
            "Gorge deck parsing and exact printed-card coverage",
            "Verified signature-mechanic and rules execution",
            "Reviewed pilot decisions from native Gorge recordings",
            "Passing bounded four-player gameplay fidelity tests",
        ],
        "decks": result,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--enrichment", required=True, type=Path)
    p.add_argument("--panel", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    payload = build_queue(json.loads(args.enrichment.read_text()),
                          json.loads(args.panel.read_text()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"queued": len(payload["decks"]),
                      "oracle_complete": sum(d["oracle_complete"] for d in payload["decks"]),
                      "active": sum(d["active_opponent"] for d in payload["decks"])}))


if __name__ == "__main__":
    main()
