"""One read-only backend report for automatic and curated live turn features.

The same authoritative snapshots feed both branches. Printed keywords are
descriptive labels, not inferred triggers or abilities; uncatalogued tokens
are explicitly separate and never assigned fabricated characteristics.
"""
from collections import Counter

from .feature_tracking import _check_catalog, analyze_game_turns, printed_features


def analyze_board_features(catalog, states):
    """Count verified printed types, subtypes and keywords actually on board."""
    _check_catalog(catalog)
    if not isinstance(states, list) or not states:
        raise ValueError("At least one authoritative turn snapshot is required")
    last = 0
    turns = []
    for state in states:
        if not isinstance(state, dict) or state.get("source") != "authoritative_game":
            raise ValueError("Printed board statistics require actual game snapshots")
        turn = state.get("turn")
        if type(turn) is not int or turn <= last:
            raise ValueError("Non-increasing turn numbers")
        last = turn
        names = state.get("battlefield")
        if not isinstance(names, list):
            raise ValueError("Missing controlled battlefield")
        counts = Counter(names)
        metadata = printed_features(catalog, counts)
        unknown = state.get("untracked_tokens", [])
        if not isinstance(unknown, list) or any(
            not isinstance(item, dict) or type(item.get("object_id")) is not int
            or not isinstance(item.get("name"), str)
            for item in unknown
        ):
            raise ValueError("Invalid untracked token records")
        turns.append({
            "turn": turn,
            "catalogued_battlefield_count": len(names),
            "untracked_token_count": len(unknown),
            "printed_features": metadata["counts"],
            "untracked_tokens": list(unknown),
        })
    return {
        "source": "authoritative_printed_board_features",
        "turns": turns,
        "limitations": ("Printed metadata only, and only for catalogued cards. "
                        "This does not measure keyword effects, triggered abilities, "
                        "synergy quality, or unreviewed tokens."),
    }


def analyze_authoritative_run(catalog, profile, states):
    """Unified reusable JSON object for a future UI or M3 result service."""
    return {
        "source": "authoritative_deck_intelligence",
        "strategy": analyze_game_turns(catalog, profile, states),
        "automatic": analyze_board_features(catalog, states),
        "limitations": ("This analyzes game states provided by the existing kernel. "
                        "The backend does not fabricate turns, tutor legality, "
                        "combo resolutions, opponent decisions, or wins."),
    }
