"""Export staged stock precons and summarize independent Gorge load checks.

Never promotes decks into live opponent roles. Only authentic catalog names
are exported: unresolved Scryfall entries remain explicit and may fail Gorge.
"""
import argparse
import json
import re
from pathlib import Path


def export(queue, out):
    if queue.get("schema") != "gorge-precon-qualification-queue-v1" or queue.get("status") != "certification_pending_no_activation":
        raise ValueError("Unexpected/unapproved queue")
    rows = queue.get("decks", [])
    if len(rows) != 60 or len({d["key"] for d in rows}) != 60:
        raise ValueError("Expected 60 unique staged decklists")
    out.mkdir(parents=True, exist_ok=True)
    names = []
    for d in rows:
        key = d["key"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", key):
            raise ValueError(f"Invalid candidate key {key!r}")
        if d["active_opponent"] or d["qualification"] != "queued_not_approved":
            raise ValueError(f"Candidate no longer staged: {key}")
        cards = [{"name": c["name"], "count": c["count"]} for c in d["oracle_card_annotations"]]
        if sum(c["count"] for c in cards) != 100:
            raise ValueError(f"Non-100-card deck: {key}")
        commander = d["commander"]
        if sum(c["count"] for c in cards if c["name"] == commander) != 1:
            raise ValueError(f"Unsupported commander location/count: {key}")
        ordered = [c for c in cards if c["name"] == commander] + [c for c in cards if c["name"] != commander]
        doc = {"name": key, "format": "commander", "commander": commander, "cards": ordered}
        (out / (key + ".json")).write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
        names.append(key)
    return names


def summarize(queue, records):
    expected = {d["key"]: d for d in queue["decks"]}
    observed = {}
    for record in records:
        key = record["deck_key"]
        if key not in expected or key in observed:
            raise ValueError(f"Unexpected or repeated result for {key}")
        observed[key] = record
    if set(expected) != set(observed):
        raise ValueError("Missing expected Gorge deck checks")
    output = []
    for d in queue["decks"]:
        r = observed[d["key"]]
        load = r["load_ok"] is True
        commander = r["commander_valid"] is True
        output.append({
            "key": d["key"], "name": d["name"], "color_identity": d["color_identity"],
            "oracle_complete": d["oracle_complete"], "unresolved_card_names": d["unresolved_card_names"],
            "decklist_sha256": d["decklist_sha256"],
            "load_ok": load, "commander_valid": commander,
            "cards_loaded": r["cards_loaded"], "commander_count": r["commander_count"],
            "error": r.get("error"), "rules_verified": False, "pilot_verified": False,
            "qualified_opponent": False,
        })
    return {
        "schema": "gorge-precon-import-compatibility-v1",
        "scope": "engine import and commander validation only; not rules fidelity",
        "source_oracle_sha256": queue["oracle_bulk_sha256"],
        "source_catalog_commit": queue["source_catalog_commit"],
        "tested": len(output), "import_passed": sum(d["load_ok"] and d["commander_valid"] for d in output),
        "import_failed": sum(not (d["load_ok"] and d["commander_valid"]) for d in output),
        "qualified": 0, "decks": output,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--queue", type=Path, required=True)
    p.add_argument("--deck-dir", type=Path)
    p.add_argument("--results-jsonl", type=Path)
    p.add_argument("--report", type=Path)
    a = p.parse_args()
    queue = json.loads(a.queue.read_text())
    if a.deck_dir:
        names = export(queue, a.deck_dir)
        if a.report:
            a.report.write_text(",".join(names) + "\n")
        print(json.dumps({"exported": len(names)}))
    elif a.results_jsonl and a.report:
        records = [json.loads(line) for line in a.results_jsonl.read_text().splitlines() if line.strip()]
        report = summarize(queue, records)
        a.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps({k: report[k] for k in ("tested", "import_passed", "import_failed", "qualified")}))
    else:
        p.error("Provide --deck-dir or --results-jsonl and --report")


if __name__ == "__main__":
    main()
