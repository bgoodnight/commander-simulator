"""Validate a private R2 analytic extraction; emit counts only (never private rows)."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise ValueError(f"Missing extraction output: {path.name}")
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def validate(root: Path, run_attempt: str, hero: str) -> dict:
    acquisition = json.loads((root / "acquisition-report.json").read_text())
    games = load_jsonl(root / "hero_features.jsonl")
    landmarks = load_jsonl(root / "landmarks.jsonl")
    events = load_jsonl(root / "event-features.jsonl")
    table = load_jsonl(root / "analytic_features.jsonl")
    cards = load_jsonl(root / "card_exposures.jsonl")
    if acquisition.get("hero") != hero or acquisition.get("run_attempt") != run_attempt:
        raise ValueError("Acquisition source identity mismatch")
    seeds = [g.get("seed") for g in games]
    if any(type(s) is not int for s in seeds) or len(set(seeds)) != len(seeds):
        raise ValueError("Invalid or duplicate game identities")
    if not seeds or len(seeds) != acquisition.get("attempts"):
        raise ValueError("Game count differs from authenticated acquisition")
    expected = {(s, turn) for s in seeds for turn in (4, 8, 12)}
    def keyed(rows: list[dict], label: str) -> dict:
        result = {}
        for row in rows:
            key = (row.get("seed"), row.get("landmark_global_turn"))
            if key in result:
                raise ValueError(f"Duplicate {label} landmark")
            result[key] = row
        if set(result) != expected:
            raise ValueError(f"{label} does not cover exact source game/turn keys")
        return result
    ls, es, ts = keyed(landmarks, "snapshots"), keyed(events, "events"), keyed(table, "analytic table")
    observed = 0
    for key in expected:
        l, e, t = ls[key], es[key], ts[key]
        if l.get("hero") != hero or e.get("hero") != hero or t.get("deck") != hero:
            raise ValueError("Cross-hero join")
        present = l.get("landmark_observed") is True
        if present != (e.get("landmark_observed") is True) or present != (t.get("landmark_observed") is True):
            raise ValueError("Landmark presence mismatch")
        if present and (l.get("source_event_seq") != e.get("event_cutoff_seq")
                        or l.get("source_event_seq") != t.get("source_event_seq")):
            raise ValueError("Event cutoff mismatch")
        if t.get("model_eligible") is not False:
            raise ValueError("Unapproved analytic record became model eligible")
        observed += int(present)
    for c in cards:
        key = (c.get("seed"), c.get("landmark_global_turn"))
        if key not in expected or not ls[key].get("landmark_observed"):
            raise ValueError("Card evidence has no observed source snapshot")
        if c.get("source_event_seq") != ls[key].get("source_event_seq"):
            raise ValueError("Card evidence extends beyond source cutoff")
        if c.get("run_attempt") != run_attempt or c.get("model_eligible") is not False:
            raise ValueError("Card provenance or approval mismatch")
    return {
        "schema": "gorge-private-analytics-validation-v1",
        "hero": hero, "run_attempt": run_attempt,
        "games": len(games), "expected_landmarks": len(expected),
        "observed_landmarks": observed, "event_rows": len(events),
        "joined_rows": len(table), "sparse_card_rows": len(cards),
        "checks": "passed", "production_eligible": False,
        "contains_private_game_rows": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--hero", required=True)
    p.add_argument("--run-attempt", required=True)
    p.add_argument("--report", required=True, type=Path)
    a = p.parse_args()
    result = validate(a.root, a.run_attempt, a.hero)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
