"""Validate and publish bounded modeled outcomes for automatic static Deck Lab loading.

Consumes ONLY offline runs produced by tools/build_game_outcomes.py; does not
simulate, fetch cards, or infer opponent identities. Replaces the current
published outcome library as one validated release, preserving no stale runs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from commander_sim.deck_fixtures import FIXTURES, EXPERIMENTAL_FIXTURES
from commander_sim.deck_lab_api import deck_detail
from commander_sim.opponent_stress import SCENARIOS, OPPONENT_TYPES
from commander_sim.pilot_policy import STYLES
from tools.build_game_outcomes import FORMAT, OUTCOME_STATES

PUBLIC_FORMAT = "commander-modeled-outcomes-library-v1"
MAX_FILES = 64
MAX_SEEDS_PER_FILE = 200
KEYS = frozenset(f.key for f in (*FIXTURES, *EXPERIMENTAL_FIXTURES))
SAFE_FILE = re.compile(r"[a-zA-Z0-9_.-]+\.json\Z")
SHA = re.compile(r"[a-f0-9]{40}\Z")
HASH = re.compile(r"[a-f0-9]{64}\Z")


def _read_json(path):
    data = Path(path).read_bytes()
    return json.loads(data), data


def _valid_life(row, index):
    if not isinstance(row, dict) or row.get("round") != index:
        return False
    life = row.get("life_totals")
    if not isinstance(life, dict):
        return False
    if not all(type(life.get(str(seat))) in (int, float)
               and math.isfinite(life[str(seat)]) for seat in range(4)):
        return False
    return (isinstance(row.get("alive_seats"), list)
            and isinstance(row.get("life_changes"), list)
            and isinstance(row.get("new_eliminations"), list))


def validate_batch(batch, *, deck_hashes):
    """Fail closed on wrong identity, invented outcomes or malformed horizons."""
    if not isinstance(batch, dict):
        raise ValueError("Invalid modeled outcome batch")
    key = batch.get("deck_key")
    requested = batch.get("requested_rounds")
    runs = batch.get("runs")
    if (batch.get("format") != FORMAT
            or batch.get("schema_version") != 1
            or key not in deck_hashes
            or batch.get("deck_sha256") != deck_hashes[key]
            or batch.get("scenario") not in SCENARIOS
            or batch.get("pilot_style") not in STYLES
            or batch.get("provisional_mode") not in ("off", "safe")
            or batch.get("opponent_fidelity") !=
               "abstract_opponent_pressure_not_card_exact"
            or batch.get("outcomes_are_competitive_win_rates") is not False
            or type(requested) is not int or not 1 <= requested <= 30
            or not isinstance(runs, list)
            or not 1 <= len(runs) <= MAX_SEEDS_PER_FILE
            or batch.get("seed_count") != len(runs)):
        raise ValueError("Invalid modeled outcome provenance, revision or configuration")
    seeds = set()
    counts = {status: 0 for status in OUTCOME_STATES}
    for run in runs:
        if not isinstance(run, dict):
            raise ValueError("Invalid outcome run record")
        seed, completed = run.get("seed"), run.get("completed_rounds")
        outcome, history = run.get("outcome"), run.get("life_history")
        if (type(seed) is not int or seed < 0 or seed in seeds
                or type(completed) is not int or not 1 <= completed <= requested
                or not isinstance(outcome, dict)
                or outcome.get("status") not in OUTCOME_STATES
                or outcome.get("completed_rounds") != completed
                or outcome.get("requested_rounds") != requested
                or outcome.get("complete") is not
                   (outcome["status"] in ("win", "loss", "draw"))
                or not isinstance(history, list)
                or len(history) != completed + 1
                or any(not _valid_life(row, i) for i, row in enumerate(history))):
            raise ValueError("Invalid outcome run chronology, duplicate seed or censoring")
        roles = run.get("opponent_roles")
        if batch["scenario"] == "random":
            if (not isinstance(roles, dict)
                    or {str(seat) for seat in roles} != {"1", "2", "3"}
                    or any(role not in OPPONENT_TYPES for role in roles.values())):
                raise ValueError("Invalid independently assigned opponent roles")
        composition = run.get("opponent_composition")
        if composition is not None:
            if (not isinstance(roles, dict)
                    or not isinstance(composition, list)
                    or composition != sorted(roles.values())):
                raise ValueError("Opponent composition disagrees with seat roles")
        # Additive, optional card-discovery provenance. Absence in historical
        # batches is missing evidence, not a zero for every card.
        opening=run.get("opening_hand")
        if opening is not None and (
                not isinstance(opening,list) or len(opening)!=7
                or any(not isinstance(name,str) or not name.strip()
                       or len(name)>256 for name in opening)):
            raise ValueError("Invalid kept opening-hand provenance")
        seeds.add(seed)
        counts[outcome["status"]] += 1
    summary = batch.get("summary")
    if (not isinstance(summary, dict)
            or summary.get("outcome_counts") != counts
            or summary.get("total_games") != len(runs)):
        raise ValueError("Outcome summary does not match recorded runs")
    replays = batch.get("example_replays", [])
    if (not isinstance(replays, list) or len(replays) > 3
            or any(not isinstance(e, dict) or e.get("seed") not in seeds
                   or not isinstance(e.get("events"), list)
                   or not isinstance(e.get("state_snapshots"), list)
                   for e in replays)):
        raise ValueError("Invalid or unpinned example replays")
    return key


def _filename(batch):
    return (
        f'{batch["deck_key"]}-{batch["scenario"]}-'
        f'{batch["pilot_style"]}-{batch["provisional_mode"]}-'
        f'r{batch["requested_rounds"]}.json'
    )


def _hashes():
    """Use the very same pinned deck revision as the static Pages exporter."""
    return {key: deck_detail(key)["deck_sha256"] for key in sorted(KEYS)}


def validate_library(directory, *, deck_hashes=None):
    directory = Path(directory)
    index, _ = _read_json(directory / "manifest.json")
    files = index.get("files")
    by_deck = index.get("by_deck")
    checksums = index.get("sha256")
    if (index.get("format") != PUBLIC_FORMAT
            or index.get("schema_version") != 1
            or not isinstance(index.get("engine_commit"), str)
            or not SHA.fullmatch(index["engine_commit"])
            or not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES
            or len(files) != len(set(files))
            or not isinstance(by_deck, dict)
            or not isinstance(checksums, dict)
            or set(checksums) != set(files)
            or any(not isinstance(file, str) or not SAFE_FILE.fullmatch(file)
                   or file == "manifest.json" for file in files)):
        raise ValueError("Invalid published long-game index")
    expected = _hashes() if deck_hashes is None else deck_hashes
    actual = {}
    for filename in files:
        batch, data = _read_json(directory / filename)
        if hashlib.sha256(data).hexdigest() != checksums[filename]:
            raise ValueError("Published long-game checksum mismatch")
        key = validate_batch(batch, deck_hashes=expected)
        if filename != _filename(batch):
            raise ValueError("Published long-game filename is not canonical")
        actual.setdefault(key, []).append(filename)
    normalized = {key: sorted(names) for key, names in actual.items()}
    if not normalized or by_deck != normalized:
        raise ValueError("Published deck index does not match outcome files")
    if sorted(files) != files:
        raise ValueError("Published files must be deterministically sorted")
    return index


def publish(source, output, *, engine_commit, deck_hashes=None):
    if not isinstance(engine_commit, str) or not SHA.fullmatch(engine_commit):
        raise ValueError("Engine commit must be an exact Git SHA")
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve():
        raise ValueError("Published files must be separate from inputs")
    paths = sorted(source.glob("*.json"))
    if not 1 <= len(paths) <= MAX_FILES:
        raise ValueError("Expected 1–64 modeled outcome JSON files")
    expected = _hashes() if deck_hashes is None else deck_hashes
    staged = {}
    indexed = {}
    for path in paths:
        batch, data = _read_json(path)
        key = validate_batch(batch, deck_hashes=expected)
        name = _filename(batch)
        if name in staged:
            raise ValueError("Duplicate modeled outcome cohort: " + name)
        staged[name] = data
        indexed.setdefault(key, []).append(name)
    names = sorted(staged)
    index = {
        "format": PUBLIC_FORMAT, "schema_version": 1,
        "engine_commit": engine_commit,
        "files": names,
        "by_deck": {key: sorted(files) for key, files in sorted(indexed.items())},
        "sha256": {name: hashlib.sha256(staged[name]).hexdigest()
                   for name in names},
    }
    # Validate the whole candidate before replacing the previously published
    # index. The CI workflow will commit this directory only after checks pass.
    import tempfile
    with tempfile.TemporaryDirectory(prefix="game-outcomes-") as temporary:
        candidate = Path(temporary)
        for name in names:
            (candidate / name).write_bytes(staged[name])
        (candidate / "manifest.json").write_text(
            json.dumps(index, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8")
        validate_library(candidate, deck_hashes=expected)
        if output.exists():
            shutil.rmtree(output)
        shutil.copytree(candidate, output)
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--engine-commit", required=True)
    args = parser.parse_args()
    result = publish(args.source, args.output, engine_commit=args.engine_commit)
    print(json.dumps({"engine_commit": result["engine_commit"],
                      "decks": len(result["by_deck"]),
                      "batches": len(result["files"])}, indent=2))


if __name__ == "__main__":
    main()
