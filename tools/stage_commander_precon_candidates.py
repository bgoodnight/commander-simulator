"""Stage authentic published Commander precons for design-of-experiments selection.

Candidate decks are NOT enabled as Gorge opponents. Download is offline setup,
never performed while running a game. Source: pinned GitHub decklists_v2 dump.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path
from urllib.request import urlopen

SOURCE_REPO = "taw/magic-preconstructed-decks-data"
SOURCE_COMMIT = "1b5a451d9146812160e27aee7c8a1e37f1395839"
SOURCE_URL = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/decks_v2.json"
MAX_RAW_BYTES = 50 * 1024 * 1024


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.casefold()).strip("-")


def collapse_cards(cards):
    if not isinstance(cards, list):
        return None
    counts = collections.Counter()
    for row in cards:
        if not isinstance(row, dict):
            return None
        name, qty = row.get("name"), row.get("count")
        if not isinstance(name, str) or not name.strip() or type(qty) is not int or qty < 1:
            return None
        counts[name] += qty
    return counts


def normalize(row):
    """Validate product identity and 100-card list, including partner commanders."""
    if not isinstance(row, dict):
        return None
    kind = str(row.get("type") or "").lower()
    if "commander" not in kind or "brawl" in kind or "display" in kind:
        return None
    title, set_code = row.get("name"), row.get("set_code")
    if not isinstance(title, str) or not title or not isinstance(set_code, str) or not set_code:
        return None
    commanders = collapse_cards(row.get("commander", []))
    main = collapse_cards(row.get("cards"))
    if main is None or not commanders:
        return None
    if sum(commanders.values()) not in (1, 2):
        return None
    overlap = set(commanders) & set(main)
    # Source dumps may either include commanders in main or separate them.
    if overlap:
        if not all(main[n] == commanders[n] for n in overlap):
            return None
        combined = main.copy()
        for n, cnt in commanders.items():
            if n not in combined:
                combined[n] = cnt
    else:
        combined = main + commanders
    if sum(combined.values()) != 100:
        return None
    if any(q > 1 for q in commanders.values()):
        return None
    # No automatically inferred color or archetype labels; these will be
    # populated from validated Oracle metadata and reviewed taxonomy later.
    deck = {
        "format": "commander",
        "commander": next(iter(commanders)) if len(commanders) == 1 else None,
        "commanders": sorted(commanders),
        "cards": [{"name": name, "count": count} for name, count in sorted(combined.items())],
    }
    return {
        "name": title, "type": row["type"], "set_code": set_code,
        "set_name": row.get("set_name"),
        "release_date": row.get("release_date"), "deck": deck,
        "commander_count": len(commanders),
        "identity_status": "source_100_card_candidate",
        "rules_status": "not_tested",
        "opponent_status": "candidate_not_enabled",
    }


def build_catalog(raw, limit=150):
    if not isinstance(raw, list):
        raise ValueError("Source must be a list of preconstructed decks")
    if limit < 100:
        raise ValueError("Catalog target must be at least 100")
    found = {}
    ignored = collections.Counter()
    for row in raw:
        norm = normalize(row)
        if norm is None:
            ignored["not_eligible_or_invalid_100_card_commander"] += 1
            continue
        key = slugify(norm["set_code"]) + "--" + slugify(norm["name"])
        if key in found:
            ignored["duplicate_identity"] += 1
            continue
        norm["key"] = key
        found[key] = norm
    # Deterministic newest-first ordering; ample diversity sampling occurs next.
    selected = sorted(found.values(), key=lambda x: (x["release_date"] or "", x["key"]), reverse=True)[:limit]
    if len(selected) < 100:
        raise ValueError(f"Only {len(selected)} valid Commander candidates; require at least 100")
    return selected, dict(ignored)


def generate(source_bytes, out, limit=150):
    if len(source_bytes) > MAX_RAW_BYTES:
        raise ValueError("Upstream source exceeded expected size limit")
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    selected, excluded = build_catalog(json.loads(source_bytes), limit=limit)
    root = Path(out)
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for row in selected:
        deck_bytes = (json.dumps(row["deck"], sort_keys=True, separators=(",", ":"))+"\n").encode()
        (root / (row["key"]+".json")).write_bytes(deck_bytes)
        entries.append({
            k: v for k, v in row.items() if k != "deck"
        } | {"deck_sha256": hashlib.sha256(deck_bytes).hexdigest()})
    report = {
        "schema": "commander-opponent-candidate-catalog-v1",
        "source": SOURCE_URL, "source_commit": SOURCE_COMMIT,
        "source_sha256": source_hash, "count": len(entries),
        "selection": "newest eligible products; not a balanced opponent panel",
        "candidates": entries, "exclusion_counts": excluded,
        "policy": "catalog only; requires Oracle metadata, stock provenance crosscheck, Gorge rules/pilot validation before activation",
    }
    (root/"catalog.json").write_text(json.dumps(report, sort_keys=True, indent=2)+"\n")
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--limit", type=int, default=150)
    p.add_argument("--source", type=Path, help="Use predownloaded raw source to permit offline reprocessing")
    args = p.parse_args()
    raw = args.source.read_bytes() if args.source else urlopen(SOURCE_URL, timeout=90).read(MAX_RAW_BYTES+1)
    result = generate(raw, args.out, limit=args.limit)
    print(json.dumps({"count":result["count"], "source_sha256":result["source_sha256"], "excluded":result["exclusion_counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
