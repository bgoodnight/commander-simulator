"""Report executable library recipe candidates across pinned Commander decks.

Counts cards with a verified source-pinned handler or a strictly provisional
import grammar. Counts are not claims that other printed abilities work or
that a particular pilot actually cast/activated the card in a run.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from commander_sim.deck_fixtures import FIXTURES, EXPERIMENTAL_FIXTURES
from commander_sim.provisional_import import provisional_profile
from commander_sim.reviewed_draw_spells import reviewed_draw_spell
from commander_sim.reviewed_flashback import reviewed_flashback
from commander_sim.reviewed_land_entry import reviewed_land_entry
from commander_sim.reviewed_sacrifice_actions import SACRIFICE_MODES


def audit_snapshot(snapshot_path, label=None):
    snapshot = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
    if snapshot.get("problems") or not isinstance(snapshot.get("cards"), list):
        raise ValueError("Requires a complete pinned card-data snapshot")
    rows = []
    excluded_multiface = []
    for entry in snapshot["cards"]:
        raw = entry["card"]
        name = entry["deck_name"]
        if not raw.get("oracle_id"):
            raise ValueError("Missing pinned Oracle identity")
        if not raw.get("oracle_text"):
            # Scryfall stores many split, Adventure and DFC texts per face.
            # Provisional rules deliberately reject those layouts; do not
            # pretend they have a single executable Oracle spell recipe.
            if (raw.get("layout") != "normal"
                    and isinstance(raw.get("card_faces"), list)):
                excluded_multiface.append(name)
                continue
            raise ValueError("Incomplete pinned single-face Oracle text")
        reviewed = reviewed_draw_spell(name, raw)
        provisional = provisional_profile(raw)
        flashback = reviewed_flashback(name, raw)
        registered_sacrifice = SACRIFICE_MODES.get(name)
        rows_for_card = []
        if reviewed is not None:
            rows_for_card.append((
                "reviewed_hand_spell", reviewed.library_actions()))
        elif provisional is not None and provisional.library_actions:
            rows_for_card.append((
                "provisional_spell", provisional.library_actions))
        land_entry = reviewed_land_entry(name, raw)
        if land_entry is not None and land_entry.operation == "surveil_one":
            from commander_sim.library_actions import LibraryAction
            rows_for_card.append((
                "reviewed_land_entry", (LibraryAction("surveil", 1),)))
        if (flashback is not None
                and flashback.operation == "draw_discard_two"):
            from commander_sim.library_actions import LibraryAction
            rows_for_card.append((
                "reviewed_flashback",
                (LibraryAction("draw", 2), LibraryAction("discard", 2))))
        if (registered_sacrifice is not None
                and registered_sacrifice.action in {"draw", "wither_draw", "scry"}
                and registered_sacrifice.oracle_id == raw["oracle_id"]
                and registered_sacrifice.excerpt in raw["oracle_text"]):
            from commander_sim.library_actions import LibraryAction
            rows_for_card.append((
                "reviewed_sacrifice_activation",
                (LibraryAction("scry", 1)
                 if registered_sacrifice.action == "scry"
                 else LibraryAction("draw", 1),)))
        for source, actions in rows_for_card:
            rows.append({
                "card": name,
                "oracle_id": raw["oracle_id"],
                "source": source,
                "actions": [{"kind": action.kind, "count": action.count}
                            for action in actions],
            })
    return {
        "deck": label or Path(snapshot_path).stem,
        "recipe_uses": len(rows),
        "cards_with_recipes": len({row["oracle_id"] for row in rows}),
        "multiface_manual_review": sorted(excluded_multiface),
        "by_source": dict(sorted(Counter(row["source"] for row in rows).items())),
        "cards": rows,
        "warning": "Registration/admission counts, not actual casting frequency, "
                   "full printed-card coverage or comparative deck power.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--snapshot", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.all:
        result = {
            deck.key: audit_snapshot(deck.snapshot_path, deck.key)
            for deck in (*FIXTURES, *EXPERIMENTAL_FIXTURES)}
    else:
        result = audit_snapshot(args.snapshot)
    content = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    print(content, end="")


if __name__ == "__main__":
    main()
