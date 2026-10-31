"""Seed-batch milestone statistics from authoritative Deck Intelligence turns.

Consumes M3 adapter/analyzer output; it never invents actions or outcomes.
A run ending before a checkpoint is censored, NOT treated as a failed combo
or a loss. Time-to-milestone means first *observed* turn, not an inferred
intermediate action. No Commander win-rate estimates are produced here.
"""
from .progress_metrics import wilson_interval


DEFAULT_CHECKPOINTS = (3, 5, 7, 10)


def _milestone_flags(turn):
    flags = {}
    for key in turn["key_cards"]:
        prefix = "key:" + key["id"] + ":"
        flags[prefix + "hand"] = key["hand"] > 0
        flags[prefix + "tutorable"] = key["engine_verified_tutor_access"]
        flags[prefix + "battlefield"] = key["battlefield"] > 0
        flags[prefix + "accessible"] = (key["hand"] > 0 or key["battlefield"] > 0
                                       or key["engine_verified_tutor_access"])
    for combo in turn["combos"]:
        prefix = "combo:" + combo["id"] + ":"
        flags[prefix + "pieces_accessible"] = (
            combo["pieces_accessible"] == combo["pieces_required"])
        flags[prefix + "pieces_in_play"] = (
            combo["pieces_on_battlefield"] == combo["pieces_required"])
        flags[prefix + "operational"] = combo["status"] == "engine_verified_operational"
    return flags


def summarize_strategy_runs(runs, *, checkpoints=DEFAULT_CHECKPOINTS):
    """Aggregate comparable independently seeded actual game projections.

    Each entry: seed (integer), deck_sha256 (exact pinned deck), report (the
    result of analyze_game_turns). Runs with fewer turns than a checkpoint
    count as censored there, irrespective of why the run ended. All reports
    must have identical key/group/combo IDs at the same checkpoints.
    """
    rows = list(runs)
    if not rows:
        raise ValueError("At least one game report is required")
    points = tuple(checkpoints)
    if (not points or any(type(t) is not int or t < 1 for t in points)
            or tuple(sorted(set(points))) != points):
        raise ValueError("Checkpoints must be distinct increasing positive turns")
    seen = set()
    deck_hash = None
    signature = None
    normalized = []
    for row in rows:
        if not isinstance(row, dict) or type(row.get("seed")) is not int:
            raise ValueError("Each game needs an integer seed")
        if row["seed"] in seen:
            raise ValueError("Duplicate game seed")
        seen.add(row["seed"])
        if not isinstance(row.get("deck_sha256"), str) or not row["deck_sha256"]:
            raise ValueError("Missing pinned deck revision")
        if deck_hash is None:
            deck_hash = row["deck_sha256"]
        if row["deck_sha256"] != deck_hash:
            raise ValueError("Cannot mix different deck revisions")
        report = row.get("report")
        if not isinstance(report, dict) or report.get("source") != "authoritative_game_snapshots":
            raise ValueError("Actual authoritative game analysis required")
        turns = report.get("turns")
        if not isinstance(turns, list) or not turns:
            raise ValueError("Empty game analysis")
        for index, turn in enumerate(turns, 1):
            if turn.get("turn") != index:
                raise ValueError("Expected contiguous observed turns from turn one")
            if type(turn.get("battlefield_count")) is not int or turn["battlefield_count"] < 0:
                raise ValueError("Invalid battlefield count")
            if not isinstance(turn.get("groups_on_battlefield"), dict):
                raise ValueError("Missing group counts")
            if not isinstance(turn.get("key_cards"), list) or not isinstance(turn.get("combos"), list):
                raise ValueError("Missing strategy report fields")
        first = turns[0]
        current_signature = (
            tuple(sorted(first["groups_on_battlefield"])),
            tuple(sorted(k["id"] for k in first["key_cards"])),
            tuple(sorted(c["id"] for c in first["combos"])),
        )
        if signature is None:
            signature = current_signature
        if current_signature != signature:
            raise ValueError("Strategy definitions differ across seeds")
        for turn in turns:
            if (tuple(sorted(turn["groups_on_battlefield"])) != signature[0]
                    or tuple(sorted(k["id"] for k in turn["key_cards"])) != signature[1]
                    or tuple(sorted(c["id"] for c in turn["combos"])) != signature[2]):
                raise ValueError("Strategy definitions changed within a game")
        normalized.append((row["seed"], turns))
    milestone_names = sorted(_milestone_flags(normalized[0][1][0]))
    output = []
    for checkpoint in points:
        eligible = [turns for _, turns in normalized if len(turns) >= checkpoint]
        n = len(eligible)
        milestones = {}
        for label in milestone_names:
            # "Ever by checkpoint": a target drawn on turn 2 still counts if
            # cast on turn 3. An instantaneous snapshot is not enough.
            success = sum(any(_milestone_flags(t)[label] for t in turns[:checkpoint])
                          for turns in eligible)
            milestones[label] = {
                "reached": success,
                "eligible": n,
                "rate": round(success/n, 4) if n else None,
                "confidence_interval_95pct": wilson_interval(success, n) if n else None,
            }
        output.append({
            "turn": checkpoint,
            "eligible_runs": n,
            "censored_before_checkpoint": len(normalized) - n,
            "mean_board_count": (round(sum(turns[checkpoint-1]["battlefield_count"]
                                            for turns in eligible)/n, 3) if n else None),
            "mean_group_counts": {
                name: (round(sum(turns[checkpoint-1]["groups_on_battlefield"][name]
                                 for turns in eligible)/n, 3) if n else None)
                for name in signature[0]
            },
            "milestones": milestones,
        })
    return {
        "mode": "authoritative_game_milestone_aggregate",
        "deck_sha256": deck_hash,
        "seeds": sorted(seen),
        "run_count": len(normalized),
        "checkpoints": output,
        "limitations": (
            "Descriptive board and curated milestone counts from supported game "
            "states only. Observations ending before a checkpoint are censored; "
            "intervals reflect seed sampling, not omitted rules, tutor uncertainty "
            "or opponent-model fidelity. This is not a win-rate estimate."
        ),
    }
