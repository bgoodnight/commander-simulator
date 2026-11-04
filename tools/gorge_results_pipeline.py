"""Validated, incremental Gorge native -> public replay and analytics pipeline.

Simulation execution is separate. This tool consumes an existing Actions
artifact (native traces and game summaries), NEVER runs Gorge, and NEVER
publishes anything. A second, manually approved workflow ships the generated
files to Pages. Native logs, intents and object catalogs stay outside output.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil

from tools.gorge_ui_export import convert
from tools.validate_gorge_enrichment import validate_trace

SCHEMA = "gorge-omniscient-replay-manifest-v1"
CONVERTER_VERSION = "gorge-results-pipeline-v1"
NAME = re.compile(r"gorge-seed-([0-9]+)\.ui\.json\Z")


def canonical_bytes(doc):
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load_summaries(path):
    rows = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        seed = row.get("seed")
        if type(seed) is not int or seed in rows:
            raise ValueError("Invalid or duplicate Gorge result seed")
        if not (row.get("finished") and row.get("replay_verified")
                and not row.get("error")):
            raise ValueError(f"Gorge game {seed} was not fully verified")
        if not isinstance(row.get("decks"), list) or len(row["decks"]) != 4:
            raise ValueError("Gorge game requires four actual decks")
        rows[seed] = row
    if not rows:
        raise ValueError("No Gorge game summaries")
    return rows


def validate_existing(root):
    manifest_file = root / "manifest.json"
    if not manifest_file.is_file():
        return {}, {}
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if (manifest.get("schema") != SCHEMA or
            manifest.get("visibility") != "omniscient" or
            manifest.get("synthetic_simulation_only") is not True):
        raise ValueError("Existing replay catalog has incompatible visibility")
    existing = {}
    for row in manifest.get("games", []):
        name = row.get("file", "")
        if not NAME.fullmatch(name) or name in existing:
            raise ValueError("Invalid or duplicate existing replay")
        path = root / name
        if not path.is_file():
            raise ValueError("Missing existing replay " + name)
        content = json.loads(path.read_text(encoding="utf-8"))
        if not public_replay_is_safe(content, row):
            raise ValueError("Unsafe or mismatched existing replay " + name)
        existing[name] = row
    old_analytics = {}
    path = root / "analytics.json"
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") == "gorge-batch-analytics-v1":
            old_analytics = {r["seed"]: r for r in data.get("games", [])
                             if type(r.get("seed")) is int}
    return existing, old_analytics


def public_replay_is_safe(doc, entry):
    return (doc.get("schema") == "gorge-ui-replay-v1" and
            doc.get("engine") == "gorge" and
            doc.get("visibility") == "omniscient" and
            doc.get("synthetic_simulation_only") is True and
            doc.get("seed") == entry.get("seed") and
            doc.get("chain") == entry.get("chain") and
            doc.get("decks") == entry.get("decks") and
            isinstance(doc.get("snapshots"), list) and
            len(doc["snapshots"]) > 0 and
            all(k not in doc for k in ("log", "objects", "intents")) and
            all(s.get("boundary") == "first_pending_decision_of_turn"
                for s in doc["snapshots"]))


def project_batch(*, native_dir, summaries, out, existing_dir=None,
                  max_replays=20, include_hidden=True, pod_dir=None):
    if not include_hidden:
        raise ValueError("This manifest requires explicit synthetic omniscient projection")
    if type(max_replays) is not int or max_replays < 0 or max_replays > 500:
        raise ValueError("Replay retention limit must be 0..500")
    native_dir, out = Path(native_dir), Path(out)
    old_dir = Path(existing_dir) if existing_dir else None
    existing, old_analytics = validate_existing(old_dir) if old_dir else ({}, {})
    rows = load_summaries(summaries)
    traces = {}
    for path in sorted(native_dir.glob("gorge-seed-*.json")):
        match = re.fullmatch(r"gorge-seed-([0-9]+)\.json", path.name)
        if not match:
            continue
        seed = int(match.group(1))
        if seed in traces or seed not in rows:
            raise ValueError("Unexpected or duplicate raw trace")
        traces[seed] = path
    if set(rows) != set(traces):
        raise ValueError(f"Missing source traces for {sorted(set(rows)-set(traces))}")
    out.mkdir(parents=True, exist_ok=True)
    # Preserve earlier catalog entries and replay bytes, without rewriting
    # their original provenance or falsely attaching new analytics.
    manifest_rows = dict(existing)
    for name in existing:
        source, target = old_dir / name, out / name
        if source.resolve() != target.resolve():
            shutil.copyfile(source, target)
    # Small, independent game summaries are always retained for ALL games,
    # including games not selected for detailed replay storage.
    analytics = dict(old_analytics)
    retained = set(sorted(rows)[:max_replays])
    configs = {}
    library = None
    if pod_dir is not None:
        from tools.commander_deck_library import load_library
        library = load_library()
        for path in sorted(Path(pod_dir).glob("*-pod.json")):
            pod = json.loads(path.read_text(encoding="utf-8"))
            hero = pod.get("hero")
            if not isinstance(hero, str) or hero in configs:
                raise ValueError("Invalid or duplicate player pod metadata")
            configs[hero] = pod
    for seed, summary in sorted(rows.items()):
        trace_path = traces[seed]
        raw = trace_path.read_bytes()
        source = json.loads(raw)
        validation = validate_trace(source)
        if (source.get("seed") != seed or summary["seed"] != seed or
                source.get("decks") != summary["decks"] or
                source.get("chain") != summary.get("replay_chain") or
                source.get("policies") != summary.get("policies") or
                source.get("engine") != "gorge"):
            raise ValueError(f"Game {seed} source does not match its verified summary")
        event_counts = Counter(str(event["kind"]) for event
                               in source["log"]["events"])
        winner = summary.get("winner_seat")
        if winner is not None and (type(winner) is not int or winner not in range(4)):
            raise ValueError(f"Invalid source winner seat for game {seed}")
        if winner is not None and summary.get("draw"):
            raise ValueError("A drawn game cannot also have a winner")
        seat_metadata = None
        hero_seat = summary.get("hero_seat")
        if configs and hero_seat is not None:
            from tools.commander_deck_library import (
                validate_pod, matchup_annotations,
            )
            if (type(hero_seat) is not int or hero_seat not in range(4)
                    or source.get("hero_seat") != hero_seat
                    or source.get("opponent_mode") is not True):
                raise ValueError(f"Unverified designated player seat for seed {seed}")
            hero = summary["decks"][hero_seat]
            pod = configs.get(hero)
            if pod is None:
                raise ValueError(f"No validated deck metadata for {hero}")
            validate_pod(library, hero, pod["opponent_pool"])
            if (any(key not in pod["opponent_pool"] for i,key
                    in enumerate(summary["decks"]) if i!=hero_seat)
                    or len(set(summary["decks"]))!=4):
                raise ValueError("A custom or duplicate deck entered an opponent seat")
            hashes = pod["deck_sha256"]
            seat_metadata = [
                {**annotation, "seat": i, "deck_sha256": hashes[key]}
                for i, (key, annotation) in enumerate(zip(
                    summary["decks"], matchup_annotations(library, summary["decks"], hero=hero)))
            ]
        analytics[seed] = {
            "seed": seed, "decks": summary["decks"],
            "policies": summary["policies"],
            "native_source_sha256": digest(raw),
            "chain": source["chain"], "finished": True,
            "replay_verified": True,
            "draw": bool(summary.get("draw")),
            "winner_seat": winner,
            "turns": summary.get("turns"),
            "events": validation["source_events"],
            "intent_count": len(source["log"]["intents"]),
            "native_event_kinds": dict(sorted(event_counts.items())),
            "snapshot_count": validation["turn_boundaries"],
            "snapshot_boundary": validation["snapshot_definition"],
            "deck_role_note": "Decks are actual recorded seats, not inferred opponent classifications",
            **({"player_seat": hero_seat,
                "seat_metadata": seat_metadata,
                "metadata_version": library["metadata_version"]}
               if seat_metadata is not None else {}),
        }
        if seed not in retained:
            continue
        filename = f"gorge-seed-{seed}.ui.json"
        previous = existing.get(filename)
        if (previous is not None and
                previous.get("native_sha256") == digest(raw) and
                previous.get("converter_version") == CONVERTER_VERSION and
                previous.get("ui_sha256") == digest((out / filename).read_bytes())):
            continue
        view = convert(source, include_hidden=True)
        entry = {
            "file": filename, "seed": seed, "decks": source["decks"],
            "chain": source["chain"], "turns": len(view["snapshots"]),
            "source": "gorge-40-life",
            "native_sha256": digest(raw),
            "converter_version": CONVERTER_VERSION,
            **({"player_seat": hero_seat, "player_deck": hero,
                "simulated_at": summary.get("simulated_at") or
                    summary.get("run_at") or __import__("datetime").datetime.now(
                        __import__("datetime").timezone.utc).isoformat()}
               if seat_metadata is not None else {}),
        }
        if not public_replay_is_safe(view, entry):
            raise ValueError(f"Game {seed} conversion failed provenance validation")
        encoded = canonical_bytes(view)
        (out / filename).write_bytes(encoded)
        entry["ui_sha256"] = digest(encoded)
        manifest_rows[filename] = entry
    # Fail on catalog collisions, do not silently replace an unrelated run
    # with the same seed but a different source trace.
    seen = {}
    for name, row in manifest_rows.items():
        if row["seed"] in seen and seen[row["seed"]] != name:
            raise ValueError("Two catalog files share a seed")
        seen[row["seed"]] = name
        if not public_replay_is_safe(json.loads((out / name).read_text()), row):
            raise ValueError("Published replay fidelity check failed: " + name)
    catalog = {
        "schema": SCHEMA, "visibility": "omniscient",
        "synthetic_simulation_only": True,
        "catalog_version": 2,
        "converter_version": CONVERTER_VERSION,
        "games": sorted(manifest_rows.values(), key=lambda row: row["seed"]),
        "analytics_file": "analytics.json",
        "replay_retention": {"from_this_batch": len(retained),
                             "native_traces_published": False},
    }
    batch = {"schema": "gorge-batch-analytics-v1",
             "description": "Verified source game metrics, no inferred card or win actions",
             "games": [analytics[k] for k in sorted(analytics)]}
    (out / "manifest.json").write_bytes(canonical_bytes(catalog))
    (out / "analytics.json").write_bytes(canonical_bytes(batch))
    return {"converted": len(retained), "summaries": len(rows),
            "catalog_games": len(manifest_rows),
            "analytics_games": len(analytics),
            "output": str(out)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-dir", required=True, type=Path)
    p.add_argument("--runs", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--existing-dir", type=Path)
    p.add_argument("--max-replays", type=int, default=20)
    p.add_argument("--include-hidden", action="store_true")
    p.add_argument("--pod-dir", type=Path,
                   help="Validated role and deck-hash configurations for player-only pods")
    a = p.parse_args()
    print(json.dumps(project_batch(
        native_dir=a.native_dir, summaries=a.runs, out=a.out,
        existing_dir=a.existing_dir, max_replays=a.max_replays,
        include_hidden=a.include_hidden, pod_dir=a.pod_dir), sort_keys=True))

if __name__ == "__main__":
    main()
