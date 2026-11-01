"""Bounded M3 live early turns over actual 99-card pinned decks and kernel zones.

This is a deliberately limited *real-action slice*, NOT the v35 full multiplayer
turn driver. Cards never get executable behavior from printed metadata alone.
Only reviewed basic/Command Tower land plays, mana-rock casts and a small
exact Oracle/text-reviewed creature subset are permitted; unsupported card
effects remain blocked. No combat, opponent turns, tutor casting, priority,
general triggers, arbitrary activated abilities, or win rates.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

from .card_cache import pinned_deck_entries
from .deck_fixtures import FIXTURES, SHARED_CATALOG
from .generic_cast import ReviewedCreatureCast, cast_reviewed_permanent
from .kernel_reporting import project_kernel_turn
from .board_features import analyze_authoritative_run
from .reviewed_early_cards import REVIEWED_BY_DECK, LIMITATIONS, reviewed_creature
from .snapshots import validate_snapshot
from .mana_kernel_bridge import _reviewed_modes
from .reviewed_rocks import reviewed_rock
from .template_resources import TemplateManaService

ROOT = Path(__file__).resolve().parents[1]


def _live_types(face):
    """Use already verified characteristics, not regexes over abilities."""
    return frozenset(face.types)


def _load_live_kernel():
    # Historical version modules aren't packaged; use the established isolated
    # v9b physical-zone kernel. This is NOT another state/zone implementation.
    legacy_path = str(ROOT / "simulator" / "v9b_live")
    if legacy_path not in sys.path:
        sys.path.insert(0, legacy_path)
    from state import IndexedKernel, LiveZones
    from rules import CardDefinition
    return IndexedKernel, LiveZones, CardDefinition


def run_bounded_early_game(deck_key, *, seed=0, turns=6, mulligan="one-free", profile=None):
    """Play a small reviewed set of actual land, rock and creature actions.

    A deterministic, conservative fixed pilot draws, plays one supported land,
    and casts affordable reviewed rocks/ordinary creatures from hand without
    pretending to implement printed abilities. All 100 physical cards occupy
    the same kernel; no observation-mode synthetic battlefield exists.
    """
    if type(seed) is not int or type(turns) is not int or not 1 <= turns <= 10:
        raise ValueError("Expected integer seed and 1..10 turns")
    if mulligan not in ("one-free", "keep"):
        raise ValueError("Unknown mulligan policy")
    fixture = next((x for x in FIXTURES if x.key == deck_key), None)
    if fixture is None:
        raise ValueError("Unknown pinned deck fixture")
    if deck_key not in REVIEWED_BY_DECK:
        raise ValueError("Deck has no individually reviewed creature-cast slice")

    pinned = pinned_deck_entries(fixture.deck_path, fixture.manifest_path, SHARED_CATALOG)
    snapshot = validate_snapshot(fixture.deck_path, fixture.snapshot_path,
                                 commander=fixture.commander)
    from .identities import CardRegistry
    registry = CardRegistry(snapshot)
    colors = registry.get(fixture.commander).color_identity
    raw_by_name = {entry["deck_name"]: entry["card"] for entry in pinned}
    # Catalog is a per-deck immutable identity projection for the feature
    # tracker. It includes all imported cards, not just supported casts.
    catalog = {name: {"type_line": card["type_line"],
                      "keywords": list(card["keywords"])}
               for name, card in raw_by_name.items()}
    IndexedKernel, LiveZones, CardDefinition = _load_live_kernel()
    kernel = IndexedKernel()
    zones = LiveZones(kernel, seed=seed)
    for section, name, quantity in snapshot.deck.cards:
        identity = registry.get(name)
        try:
            face = identity.primary_face()
        except NotImplementedError:
            face = None
        if face is None:
            # Unsupported layouts still have a physical card object and their
            # original printed type, but get no castable behavior.
            raw = raw_by_name[name]
            types = frozenset(word.lower() for word in raw["type_line"].split(" — ", 1)[0].split()
                              if word.lower() in {"land", "creature", "artifact", "instant",
                                                  "sorcery", "enchantment", "planeswalker", "battle"})
            if not types:
                raise ValueError("No verified printed card type for " + name)
            subtypes = frozenset()
            power = toughness = 0
            keywords = frozenset()
            colors_printed = None
        else:
            types = _live_types(face)
            subtypes = face.subtypes
            power, toughness = face.power or 0, face.toughness or 0
            keywords = face.keywords or frozenset()
            colors_printed = face.colors
        reviewed = (reviewed_creature(deck_key, name, raw_by_name[name])
                    or reviewed_rock(name, raw_by_name[name], colors) is not None)
        definition = CardDefinition(
            identity.oracle_id, name, types, subtypes=subtypes,
            supertypes=frozenset({"commander"}) if section == "Commander" else frozenset(),
            base_power=power, base_toughness=toughness,
            keywords=keywords, colors=colors_printed,
            coverage="approx" if reviewed else "unimplemented")
        for _ in range(quantity):
            zones.add(definition, 0, "command" if section == "Commander" else "library")

    mana_service = TemplateManaService(kernel, raw_by_name, colors)
    if len(kernel.objects) != 100:
        raise AssertionError("Pinned 100-card zone conservation failed at loading")
    zones.shuffle(0)
    zones.draw(0, 7)
    initial_hand = list(zones.names(0, "hand"))
    supported_land = lambda oid: bool(
        "land" in kernel.get(oid).types
        and _reviewed_modes(kernel.get(oid).card.name, colors))
    possible_lands = sum(supported_land(oid) for oid in zones.ids(0, "hand"))
    mulligan_taken = mulligan == "one-free" and not 2 <= possible_lands <= 5
    if mulligan_taken:
        for oid in tuple(zones.ids(0, "hand")):
            zones.move(oid, "library", "resolve")
        zones.shuffle(0)
        zones.draw(0, 7)
    opening_hand = list(zones.names(0, "hand"))

    actions_by_turn = []
    states = []
    for turn in range(1, turns + 1):
        mana_service.clear()
        events = []
        for obj in kernel.objects.values():
            if obj.controller == 0 and obj.zone == "battlefield" and obj.tapped:
                obj.tapped = False
                events.append({"type": "untap", "object_id": obj.object_id,
                               "card": obj.card.name})
        if events:
            kernel._dirty()
        drawn, okay = zones.draw(0, 1)  # Seat is explicitly not the starting seat.
        if not okay:
            raise ValueError("Library depleted before supported turn horizon")
        events.append({"type": "draw", "card": kernel.get(drawn[0]).card.name,
                       "object_id": drawn[0]})
        playable_lands = [oid for oid in zones.ids(0, "hand") if supported_land(oid)]
        if playable_lands:
            land_id = playable_lands[0]
            name = kernel.get(land_id).card.name
            new_id = zones.play_land(0, land_id)
            events.append({"type": "land_play", "card": name,
                           "from_object_id": land_id, "object_id": new_id})
        # Reuse the same source-paid action for approved artifacts and creatures.
        # Prefer affordable ramp rocks before creatures: a limited pilot policy.
        while True:
            options = []
            for oid in zones.ids(0, "hand"):
                obj = kernel.get(oid)
                name = obj.card.name
                raw = raw_by_name[name]
                is_creature = reviewed_creature(deck_key, name, raw)
                rock = reviewed_rock(name, raw, colors)
                if not is_creature and rock is None:
                    continue
                cost = registry.get(name).primary_face().mana_cost
                payment = mana_service.plan(0, cost)
                if payment is not None:
                    kind = "creature" if is_creature else "artifact"
                    options.append((0 if rock is not None else 1,
                                    len(payment.source_ids), name, oid, kind, cost))
            if not options:
                break
            _, _, name, oid, kind, cost = min(options)
            review = ReviewedCreatureCast(
                kernel.get(oid).card.card_id, cost, True,
                ("Other printed abilities remain unsupported",))
            committed = cast_reviewed_permanent(
                zones, 0, oid, review, colors, mana_service=mana_service,
                permanent_type=kind)
            if committed is None:
                raise AssertionError("Payment feasibility changed without an action")
            events.append({
                "type": kind + "_cast", "card": name,
                "stack_object_id": committed.ticket.object_id,
                "source_object_ids": list(committed.paid_source_ids),
                "floating_after_payment": list(mana_service.floating()),
                "fidelity": "limited_generic_cast",
                "unsupported_abilities": list(committed.unresolved_later_abilities),
            })
            resolved_id = zones.resolve(committed.ticket)
            if kind == "artifact":
                rock = reviewed_rock(name, raw_by_name[name], colors)
                if rock[0].enter_tapped:
                    kernel.get(resolved_id).tapped = True
                    kernel._dirty()
            events.append({"type": kind + "_resolved", "card": name,
                           "object_id": resolved_id, "fidelity": "limited_generic_resolution"})
        floating_end = list(mana_service.floating())
        mana_service.clear()
        if not zones.assert_consistent() or len(kernel.objects) != 100:
            raise AssertionError("Physical object conservation failed")
        state = project_kernel_turn(zones, 0, turn, catalog)
        states.append(state)
        actions_by_turn.append({
            "turn": turn, "events": events, "hand_size": len(zones.ids(0, "hand")),
            "library_size": len(zones.ids(0, "library")),
            "land_count": sum("land" in o.types and o.zone == "battlefield"
                              for o in kernel.objects.values()),
            "creature_count": sum("creature" in o.types and o.zone == "battlefield"
                                  for o in kernel.objects.values()),
            "mana_rock_count": sum("artifact" in o.types and o.zone == "battlefield"
                                  and reviewed_rock(o.card.name, raw_by_name[o.card.name], colors) is not None
                                  for o in kernel.objects.values()),
            "floating_at_end_of_main": floating_end,
            "unsupported_cards_in_hand": sorted(
                kernel.get(oid).card.name for oid in zones.ids(0, "hand")
                if not reviewed_creature(deck_key, kernel.get(oid).card.name,
                                         raw_by_name[kernel.get(oid).card.name])
                and reviewed_rock(kernel.get(oid).card.name,
                                  raw_by_name[kernel.get(oid).card.name], colors) is None
                and not supported_land(oid)),
        })
    analysis = analyze_authoritative_run(catalog, profile or {}, states)
    return {
        "mode": "bounded_authoritative_early_actions",
        "deck_key": deck_key,
        "commander": fixture.commander,
        "deck_sha256": snapshot.deck_sha256,
        "seed": seed,
        "turns": turns,
        "mulligan": {"policy": mulligan, "taken": mulligan_taken,
                     "initial_hand": initial_hand, "opening_hand": opening_hand},
        "events": actions_by_turn,
        "state_snapshots": states,
        "deck_intelligence": analysis,
        "first_unmodeled_choice": "turn 1: full land, spell, tutor and opponent decisions unavailable",
        "limits": LIMITATIONS,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deck", choices=sorted(REVIEWED_BY_DECK), required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--turns", type=int, default=6)
    parser.add_argument("--mulligan", choices=("one-free", "keep"), default="one-free")
    parser.add_argument("--profile", type=Path, help="Optional curated strategy JSON file")
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf-8")) if args.profile else None
    print(json.dumps(run_bounded_early_game(args.deck, seed=args.seed, turns=args.turns,
                                             mulligan=args.mulligan, profile=profile), indent=2))
