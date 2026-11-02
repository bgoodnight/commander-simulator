"""Turn an archived, abbreviated opponent-stress export into immutable replay-v1 data.

Presentation-only adapter: never runs gameplay, reconstructs opponent boards,
fills in missing life totals or fabricates player actions. Run with the downloaded
GitHub Actions artifact. The output is safe static JSON for Deck Lab.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

FORMAT = "commander-replay-v1"
DECK = "mortarion_physical_final"
SCENARIOS = ("balanced", "aggressive", "control", "combo", "goldfish")


def convert(source: dict, *, source_run: int, engine_commit: str, deck_sha256: str,
            source_sha256: str = "") -> dict:
    if (source.get("deck") != DECK or source.get("turn_horizon") != 10
            or set(source.get("scenarios", {})) != set(SCENARIOS)
            or type(source.get("seeds_per_scenario")) is not int
            or source["seeds_per_scenario"] < 1):
        raise ValueError("Unexpected opponent stress export or deck version")
    if (not isinstance(engine_commit, str) or len(engine_commit) != 40
            or any(c not in "0123456789abcdef" for c in engine_commit)
            or not isinstance(deck_sha256, str) or len(deck_sha256) != 64):
        raise ValueError("Commit/deck revision must be pinned")
    output = {
        "format": FORMAT, "schema_version": 1, "deck_key": DECK,
        "deck_sha256": deck_sha256,
        "source": {
            "workflow_run_id": source_run, "engine_commit": engine_commit,
            "artifact": "mortarion-opponent-pressure-scenarios",
            "original_file": "mortarion-opponent-stress.json",
            "sha256": source_sha256,
        },
        "fidelity": {
            "kind": "abbreviated_opponent_pressure_narratives",
            "scope": "rounds_not_individual_player_turns",
            "event_order": "exported_order_within_round_only",
            "sampled_games_only": True,
            "opponent_decks": False,
            "opponent_life_snapshots": False,
            "opponent_battlefield_snapshots": False,
            "pilot_life_and_counts": True,
            "individual_card_draws": False,
            "card_zone_movements": False,
            "warning": source.get("warning", ""),
        },
        "seeds_per_scenario": source["seeds_per_scenario"],
        "round_horizon": source["turn_horizon"],
        "scenarios": {},
        "review_flags": source.get("review_flags", []),
    }
    for key in SCENARIOS:
        entry = source["scenarios"][key]
        summary = entry["summary"]
        if summary.get("seeds") != source["seeds_per_scenario"]:
            raise ValueError("Scenario summary sample mismatch: " + key)
        games = []
        seen_seeds = set()
        for trace in entry["narratives"]:
            seed = trace["seed"]
            if type(seed) is not int or seed in seen_seeds or seed < 0 or seed >= summary["seeds"]:
                raise ValueError("Duplicate or out-of-range narrative seed")
            seen_seeds.add(seed)
            if trace.get("scenario") != (None if key == "goldfish" else key):
                raise ValueError("Narrative scenario does not match export")
            roles = trace.get("seat_roles", {})
            if key != "goldfish" and set(map(str, roles)) != {"1", "2", "3"}:
                raise ValueError("Expected abstract opponent roles for seats 1–3")
            seats = [{"seat": 0, "label": "Mortarion", "role": "physical deck",
                      "has_pilot_snapshots": True}]
            if key != "goldfish":
                seats += [{"seat": num, "label": "Seat " + str(num),
                           "role": roles.get(str(num), roles.get(num)),
                           "has_pilot_snapshots": False} for num in (1, 2, 3)]
            rounds = []
            previous = 0
            for turn in trace["turns"]:
                number = turn["turn"]
                if type(number) is not int or number != previous + 1 or number > source["turn_horizon"]:
                    raise ValueError("Narrative rounds are out of sequence")
                previous = number
                if not isinstance(turn.get("events"), list):
                    raise ValueError("Narrative events must be a list")
                actions = []
                for position, raw in enumerate(turn["events"]):
                    if not isinstance(raw, dict) or not isinstance(raw.get("type"), str):
                        raise ValueError("Malformed narrative event")
                    etype = raw["type"]
                    # 'opponent_life_zero.seat' identifies the defeated seat, not
                    # the acting player. Preserve it without falsely attributing it.
                    actor = (None if etype == "opponent_life_zero" else
                             raw.get("seat") if etype.startswith("opponent_") else 0)
                    if actor is not None and actor not in (0, 1, 2, 3):
                        raise ValueError("Unexpected event seat")
                    actions.append({
                        "id": f"{key}:{seed}:r{number}:a{position}",
                        "type": etype, "actor_seat": actor,
                        "target_seat": raw.get("target_seat"),
                        "affected_seat": raw.get("seat") if etype == "opponent_life_zero" else None,
                        "card_name": raw.get("card"),
                        "fields": dict(raw),  # all fields retained exactly
                        "fidelity": ("abstract" if etype.startswith(("opponent_","player_"))
                                     else "reviewed"),
                    })
                pilot_state = {
                    "life": turn.get("life"), "lands": turn.get("lands"),
                    "creatures": turn.get("creatures"),
                    "hand_size": turn.get("hand_size"),
                }
                # Optional authoritative kernel snapshots from a newer source
                # batch. Older narratives remain valid without them.
                if "pilot_zones" in turn:
                    zones = turn["pilot_zones"]
                    if (not isinstance(zones, dict)
                            or any(not isinstance(zones.get(z), list)
                                   for z in ("hand", "battlefield", "graveyard", "exile"))
                            or any(not isinstance(obj, dict)
                                   or not isinstance(obj.get("name"), str)
                                   for z in ("hand", "battlefield", "graveyard", "exile")
                                   for obj in zones[z])
                            or len(zones["hand"]) != pilot_state["hand_size"]):
                        raise ValueError("Pilot zone snapshots do not match recorded hand")
                    pilot_state["zones"] = zones
                round_record = {
                    "round": number,
                    "snapshots": {"0": pilot_state},
                    "actions": actions,
                }
                if "mana_activations" in turn:
                    activations = turn["mana_activations"]
                    if (not isinstance(activations, list)
                            or any(not isinstance(row, dict)
                                   or not isinstance(row.get("source_name"), str)
                                   or not isinstance(row.get("mana_output"), list)
                                   for row in activations)):
                        raise ValueError("Invalid committed mana source ledger")
                    round_record["mana_activations"] = activations
                rounds.append(round_record)
            games.append({
                "id": f"{key}:{seed}", "seed": seed, "scenario": key,
                "eliminated": trace.get("eliminated") is True,
                "seats": seats, "rounds": rounds,
            })
        output["scenarios"][key] = {
            "summary": summary, "narrative_sample_count": len(games), "games": games,
        }
    return output


def build(src: Path, dest: Path, *, source_run: int,
          engine_commit: str, deck_sha256: str) -> dict:
    raw = src.read_bytes()
    source = json.loads(raw)
    result = convert(source, source_run=source_run,
                     engine_commit=engine_commit, deck_sha256=deck_sha256,
                     source_sha256=hashlib.sha256(raw).hexdigest())
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":"),
                               sort_keys=True) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-run", type=int, required=True)
    parser.add_argument("--engine-commit", required=True)
    parser.add_argument("--deck-sha256", required=True)
    args = parser.parse_args()
    result = build(args.input, args.output, source_run=args.source_run,
                   engine_commit=args.engine_commit, deck_sha256=args.deck_sha256)
    print(json.dumps({"format": result["format"],
                      "scenarios": {key: {"simulated": row["summary"]["seeds"],
                                          "narratives": len(row["games"])}
                                    for key, row in result["scenarios"].items()}}))


if __name__ == "__main__":
    main()
