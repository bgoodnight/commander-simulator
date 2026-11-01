"""Seed aggregates from bounded, source-paid authentic early actions.

Comparative diagnostics for the REVIEWED action subset only. This is not a
win-rate or complete deck power model; unsupported plays can make a poor
reported board state misleading if treated as actual strategic potential.
"""
from .early_game_runner import run_bounded_early_game
from .progress_metrics import wilson_interval
from .milestone_stats import summarize_strategy_runs


def run_bounded_batch(deck_key, *, seeds=20, turns=6, mulligan="one-free", profile=None):
    if type(seeds) is not int or not 1 <= seeds <= 1000:
        raise ValueError("Requested seed count must be 1..1000")
    if type(turns) is not int or not 1 <= turns <= 10:
        raise ValueError("Turn count must be 1..10")
    runs = [run_bounded_early_game(deck_key, seed=i, turns=turns,
                                    mulligan=mulligan, profile=profile) for i in range(seeds)]
    deck_hash = runs[0]["deck_sha256"]
    if any(r["deck_sha256"] != deck_hash or r["mode"] != "bounded_authoritative_early_actions"
           for r in runs):
        raise ValueError("Cannot compare non-identical deck revision or run mode")
    checkpoints = []
    for t in range(1, turns + 1):
        rows = [r["events"][t-1] for r in runs]
        cast_by_turn = sum(any(
            e["type"] == "creature_cast" for turn in r["events"][:t]
            for e in turn["events"]) for r in runs)
        any_board = sum(row["creature_count"] > 0 for row in rows)
        checkpoints.append({
            "turn": t,
            "mean_lands_in_play": round(sum(x["land_count"] for x in rows)/seeds, 3),
            "mean_reviewed_creatures_in_play": round(
                sum(x["creature_count"] for x in rows)/seeds, 3),
            "pct_with_reviewed_creature_by_turn": round(100*cast_by_turn/seeds, 2),
            "reviewed_cast_95pct_interval": wilson_interval(cast_by_turn, seeds),
            "pct_with_creature_on_board": round(100*any_board/seeds, 2),
            "mean_hand_size": round(sum(x["hand_size"] for x in rows)/seeds, 3),
            "mean_unsupported_hand_cards": round(
                sum(len(x["unsupported_cards_in_hand"]) for x in rows)/seeds, 3),
        })
    strategic = (summarize_strategy_runs([
        {"seed": r["seed"], "deck_sha256": r["deck_sha256"],
         "report": r["deck_intelligence"]["strategy"]}
        for r in runs], checkpoints=tuple(range(1, turns + 1)))
        if profile else None)
    return {
        "mode": "bounded_real_action_batch",
        "deck_key": deck_key,
        "deck_sha256": deck_hash,
        "seed_count": seeds,
        "turns": checkpoints,
        "curated_milestones": strategic,
        "limitations": ("These actual object, land and reviewed-creature cast events "
                        "are generated from a small manually approved subset. "
                        "Unsupported cards do not cast; mana rocks, actual tutor chains, "
                        "commander casting, combat, opponents and full win conditions "
                        "are not simulated. Never interpret these measurements as "
                        "complete deck performance or win probabilities."),
    }


if __name__ == "__main__":
    import argparse
    import json
    from .reviewed_early_cards import REVIEWED_BY_DECK
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deck", choices=sorted(REVIEWED_BY_DECK), required=True)
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--turns", type=int, default=6)
    parser.add_argument("--profile", type=str, help="Optional curated strategy JSON file")
    args = parser.parse_args()
    profile = json.loads(open(args.profile, encoding="utf-8").read()) if args.profile else None
    print(json.dumps(run_bounded_batch(args.deck, seeds=args.seeds,
                                       turns=args.turns, profile=profile), indent=2))
