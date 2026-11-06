"""Combine verified per-shard native card features across a versioned R2 cohort.

Sidecars are opt-in: missing features never become fabricated zero counts.
The original extractor's seed-scoped observations are rekeyed by approved game
identity to prevent collisions when multiple batches reuse the same seed.
No private events, hands, or recordings are published in this report.
"""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from pathlib import Path

from tools.gorge_card_insights import KINDS, merge_shards

SCHEMA = "gorge-r2-card-feature-evidence-v1"


def sha(data: bytes):
    return hashlib.sha256(data).hexdigest()


class FullCohortCardInsights:
    def __init__(self):
        self.entries = []
        self.pending = []
        self.input_hashes = []

    def add(self, folder: Path, manifest_bytes: bytes, games_bytes: bytes,
            ui_bytes: bytes, approved_rows: list):
        """Register exact approved games, or explicitly mark missing insights."""
        if not approved_rows:
            return
        path = folder / "card-insights.v1.json"
        if not path.is_file():
            self.pending.append({"batch": approved_rows[0]["batch_id"],
                                 "deck": approved_rows[0]["deck"],
                                 "count": len(approved_rows)})
            return
        data = path.read_bytes()
        envelope = json.loads(data)
        if (envelope.get("schema") != SCHEMA or
            envelope.get("manifest_sha256") != sha(manifest_bytes) or
            envelope.get("games_sha256") != sha(games_bytes) or
            envelope.get("ui_sha256") != sha(ui_bytes)):
            raise ValueError("Card features do not match verified R2 source")
        features = envelope.get("features")
        if not isinstance(features, dict) or features.get("schema") != "gorge-card-insights-shard-v1":
            raise ValueError("Invalid native feature shard")
        pairs = features.get("seed_chains")
        expected = {(row["seed"], row["chain"]) for row in approved_rows}
        if (not isinstance(pairs, list) or
            len(pairs) != len(approved_rows) or
            len({tuple(pair) for pair in pairs}) != len(pairs) or
            {tuple(pair) for pair in pairs} != expected or
            features.get("completed_verified_games") != len(approved_rows)):
            raise ValueError("Incomplete or incorrect feature coverage")
        source_ids = {row["game_id"]: row["source_sha256"] for row in approved_rows}
        if envelope.get("source_recordings") != source_ids:
            raise ValueError("Native source digests are not exact")
        deck = approved_rows[0]["deck"]
        projection = json.loads(ui_bytes)
        if features.get("deck_sha256") != projection.get("ui_deck_sha256"):
            raise ValueError("Card features use the wrong UI deck revision")
        if features.get("deck") != deck or any(row["deck"] != deck for row in approved_rows):
            raise ValueError("Feature deck mismatch")
        if not isinstance(features.get("categories"), dict) or set(features["categories"]) != set(KINDS):
            raise ValueError("Missing native feature categories")
        # No inference from public replay observations. Only exact native features.
        self.entries.append((approved_rows, features))
        self.input_hashes.append(sha(data))

    def report(self, deck: str, approved_rows: list):
        """Return a full-cohort report only if every approved game is covered."""
        requested = {row["game_id"] for row in approved_rows}
        covering = [(rows, features) for rows, features in self.entries
                    if rows[0]["deck"] == deck]
        covered = {row["game_id"] for rows, _ in covering for row in rows}
        if covered != requested:
            return None
        # Merge requires unique integer seeds. Assign stable IDs in sorted game-ID
        # order, then rewrite every seed-scoped feature reference consistently.
        order = {gid: i for i, gid in enumerate(sorted(requested))}
        authoritative = []
        with tempfile.TemporaryDirectory(prefix="gorge-insight-merge-") as tmp:
            paths = []
            for i, (rows, source) in enumerate(covering):
                by_seed = {row["seed"]: row for row in rows}
                mapped = {seed: order[row["game_id"]] for seed, row in by_seed.items()}
                for row in rows:
                    authoritative.append({
                        "seed": mapped[row["seed"]], "chain": row["chain"],
                        "decks": json.loads(row["decks_json"]),
                        "player_seat": row["hero_seat"], "player_deck": deck
                    })
                feature = copy.deepcopy(source)
                feature["seed_chains"] = [[mapped[seed], chain] for seed, chain in source["seed_chains"]]
                for items in feature["categories"].values():
                    if not isinstance(items, list):
                        raise ValueError("Invalid card feature collection")
                    for item in items:
                        for field in ("counts", "events"):
                            item[field] = [[mapped[seed], value] for seed, value in item.get(field, [])]
                        item["seen"] = [mapped[seed] for seed in item.get("seen", [])]
                path = Path(tmp) / f"{i:06d}.json"
                path.write_text(json.dumps(feature))
                paths.append(path)
            all_reports = merge_shards(paths, authoritative)
        result = all_reports["decks"].get(deck)
        if result is None or result["verified_games"] != len(approved_rows):
            raise ValueError("Incomplete merged card insights")
        # Examples use globally reassigned IDs and are not actionable replay
        # references. Only a separately verified game-id crosswalk can link them.
        for items in result["categories"].values():
            for item in items:
                item["exampleEvents"] = []
                item["exampleSeenSeeds"] = []
        return result
