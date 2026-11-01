"""Bounded real-action early turns over six pinned 100-card Commander decks.

This is a deliberately limited no-opponent physical-kernel slice, NOT the
historical v35 full multiplayer priority/stack driver. Cards never acquire
executable effects solely from printed Oracle text or inferred role tags.

All six decks may play reviewed lands and mana rocks with real source payment.
Specifically reviewed creatures, instant/sorcery tutors and token-producing
sorceries may be cast from hand and resolve on the same authoritative zones.
Four pinned spell-cast trigger effects have limited execution after such
paid casts. Unsupported abilities remain unavailable; there is no universal
priority, combat, replacement-effect, flashback, death-trigger or win-rate
engine here.
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
from .reviewed_tutors import reviewed_tutor
from .reviewed_tutor_cast import (eligible_reviewed_tutor_targets,
                                  cast_and_resolve_reviewed_tutor)
from .reviewed_token_spells import (reviewed_token_spell,
                                   cast_and_resolve_reviewed_token_spell)
from .bounded_trigger_effects import resolve_reviewed_spell_triggers
from .kernel_life import KernelLife
from .reviewed_phase_effects import ReviewedPhaseEngine,reviewed_phase_permanent
from .reviewed_death_effects import ReviewedDeathEngine
from .reviewed_sacrifice_actions import (
    SACRIFICE_MODES, reviewed_sacrifice_artifact,
    activate_reviewed_sacrifice)
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
    # Every fully pinned deck may exercise common reviewed lands and rocks.
    # Decks without a verified creature subset retain *zero* creature casts;
    # they are not granted behavior merely by being in this fixture catalog.

    pinned = pinned_deck_entries(fixture.deck_path, fixture.manifest_path, SHARED_CATALOG)
    snapshot = validate_snapshot(fixture.deck_path, fixture.snapshot_path,
                                 commander=fixture.commander)
    from .identities import CardRegistry
    registry = CardRegistry(snapshot)
    colors = registry.get(fixture.commander).color_identity
    raw_by_name = {entry["deck_name"]: entry["card"] for entry in pinned}
    # Catalog is a per-deck immutable identity projection for the feature
    # tracker. It includes all imported cards, not just supported casts.
    catalog = {name: {"type_line": card.get("type_line") or " // ".join(
                          face.get("type_line", "") for face in card.get("card_faces", [])),
                      "keywords": list(card.get("keywords", []))}
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
        tutor_review = reviewed_tutor(name, raw_by_name[name])
        reviewed = (reviewed_creature(deck_key, name, raw_by_name[name])
                    or reviewed_rock(name, raw_by_name[name], colors) is not None
                    or (tutor_review is not None
                        and tutor_review[2] in {"instant", "sorcery"})
                    or reviewed_token_spell(name, raw_by_name[name]) is not None
                    or reviewed_phase_permanent(name, raw_by_name[name])
                    or reviewed_sacrifice_artifact(name,raw_by_name[name]))
        definition = CardDefinition(
            identity.oracle_id, name, types, subtypes=subtypes,
            supertypes=frozenset({"commander"}) if section == "Commander" else frozenset(),
            base_power=power, base_toughness=toughness,
            keywords=keywords, colors=colors_printed,
            coverage="approx" if reviewed else "unimplemented")
        for _ in range(quantity):
            zones.add(definition, 0, "command" if section == "Commander" else "library")

    mana_service = TemplateManaService(kernel, raw_by_name, colors)
    life = KernelLife(kernel)
    phase_engine = ReviewedPhaseEngine(zones, life, raw_by_name)
    death_engine = ReviewedDeathEngine(zones, life, raw_by_name)
    entered_on_turn = {}
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
        turn_kernel_event_index=len(kernel.events)
        events = []
        def approved_spell_triggers(ticket):
            """Execute only vetted cast triggers after an actual source cast."""
            source = kernel.get(ticket.object_id)
            effects = resolve_reviewed_spell_triggers(
                zones, 0, raw_by_name, event="spell_cast",
                spell_types=frozenset(source.types))
            return [{"type":"reviewed_trigger_resolved",
                     "source":effect.card_name,
                     "source_object_id":effect.source_id,
                     "ability_slot":effect.slot_id,
                     "created_token_ids":list(effect.created_token_ids),
                     "drawn_ids":list(effect.drawn_ids),
                     "fidelity":"bounded_no_opponent_priority"}
                    for effect in effects]
        for obj in kernel.objects.values():
            if obj.controller == 0 and obj.zone == "battlefield" and obj.tapped:
                obj.tapped = False
                events.append({"type": "untap", "object_id": obj.object_id,
                               "card": obj.card.name})
        if events:
            kernel._dirty()
        # Upkeep happens after untap but before the ordinary draw.
        for triggered in phase_engine.resolve(
                phase="upkeep",active_seat=0,round_id=turn):
            events.append({
                "type":"reviewed_phase_resolved","phase":"upkeep",
                "source":triggered.source_name,"source_object_id":triggered.source_id,
                "ability_slot":triggered.slot_id,
                "created_token_ids":list(triggered.created_token_ids),
                "drawn_ids":list(triggered.drawn_ids),
                "returned_object_id":triggered.returned_id,
                "fidelity":"bounded_no_opponent_priority"})
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
                token_spell = reviewed_token_spell(name, raw)
                phase_enchantment = reviewed_phase_permanent(name, raw)
                sacrifice_artifact = reviewed_sacrifice_artifact(name, raw)
                tutor = reviewed_tutor(name, raw)
                eligible = (eligible_reviewed_tutor_targets(zones, 0, name, raw_by_name)
                            if tutor and tutor[2] in {"instant", "sorcery"} else ())
                if (not is_creature and rock is None and not eligible
                        and token_spell is None and not phase_enchantment
                        and not sacrifice_artifact):
                    continue
                cost = registry.get(name).primary_face().mana_cost
                payment = mana_service.plan(0, cost)
                if payment is not None:
                    kind = ("artifact" if rock is not None or sacrifice_artifact else
                            "enchantment" if phase_enchantment else
                            "tutor" if eligible else
                            "token_spell" if token_spell is not None else "creature")
                    target = (min(eligible, key=lambda target_id: (
                        0 if kernel.get(target_id).card.name == "Sol Ring" else
                        1 if reviewed_rock(kernel.get(target_id).card.name,
                                            raw_by_name[kernel.get(target_id).card.name],
                                            colors) is not None else
                        2 if reviewed_creature(deck_key,
                             kernel.get(target_id).card.name,
                             raw_by_name[kernel.get(target_id).card.name]) else 3,
                        target_id)) if eligible else None)
                    # Reviewed trigger creatures precede spells so their
                    # shared effects may fire on subsequent actual casts.
                    options.append((0 if rock is not None else
                                    1 if is_creature else
                                    2 if sacrifice_artifact else
                                    3 if phase_enchantment else
                                    4 if eligible else 5,
                                    len(payment.source_ids), name, oid, kind, cost, target))
            if not options:
                break
            _, _, name, oid, kind, cost, target = min(options)
            if kind == "tutor":
                triggered=[]
                result = cast_and_resolve_reviewed_tutor(
                    zones, 0, oid, raw_by_name, colors, mana_service,
                    target_id=target,
                    on_cast=lambda ticket: triggered.extend(
                        approved_spell_triggers(ticket)))
                if result is None:
                    raise AssertionError("Tutor payment changed without an action")
                events.append({"type": "tutor_cast", "card": name,
                               "stack_object_id": result.source_stack_id,
                               "source_object_ids": list(result.paid_source_ids),
                               "fidelity": "bounded_reviewed_search"})
                events.extend(triggered)
                events.append({"type": "tutor_resolved", "card": name,
                               "source_graveyard_id": result.source_graveyard_id,
                               "target_name": result.target_name,
                               "target_object_id": result.target_new_id,
                               "destination": result.target_destination,
                               "fidelity": "bounded_reviewed_search"})
                continue
            if kind == "token_spell":
                triggered=[]
                result = cast_and_resolve_reviewed_token_spell(
                    zones, 0, oid, raw_by_name, colors, mana_service,
                    on_cast=lambda ticket: triggered.extend(
                        approved_spell_triggers(ticket)))
                if result is None:
                    raise AssertionError("Token spell payment changed without an action")
                events.append({"type": "token_spell_cast", "card": name,
                               "stack_object_id": result.source_stack_id,
                               "source_object_ids": list(result.paid_source_ids),
                               "fidelity": "bounded_reviewed_token_effect"})
                events.extend(triggered)
                events.append({"type": "token_spell_resolved", "card": name,
                               "source_graveyard_id": result.source_graveyard_id,
                               "created_token_ids": list(result.token_ids),
                               "created_token_count": len(result.token_ids),
                               "unsupported_abilities": list(result.limitations),
                               "fidelity": "bounded_reviewed_token_effect"})
                continue
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
            entered_on_turn[resolved_id]=turn
            if kind == "artifact":
                rock = reviewed_rock(name, raw_by_name[name], colors)
                if rock[0].enter_tapped:
                    kernel.get(resolved_id).tapped = True
                    kernel._dirty()
            events.append({"type": kind + "_resolved", "card": name,
                           "object_id": resolved_id, "fidelity": "limited_generic_resolution"})
        # No-opponent, single-action-per-reviewed-source sacrifice policy.
        # Sacrifices are costs paid from real battlefield objects; they can
        # activate reviewed death triggers, never fabricated combo events.
        used_sacrifice_sources=set()
        for source in sorted(list(kernel.on_battlefield()),key=lambda x:x.object_id):
            if (source.object_id in used_sacrifice_sources
                    or source.object_id not in kernel.objects
                    or source.controller!=0
                    or source.card.name not in SACRIFICE_MODES):
                continue
            mode=SACRIFICE_MODES[source.card.name]
            if mode.tap and (source.tapped or
                ("creature" in source.types
                 and entered_on_turn.get(source.object_id,0)>=turn
                 and "haste" not in source.keywords)):
                continue
            victims=[obj for obj in kernel.on_battlefield()
                if obj.controller==0 and "creature" in obj.types
                and "commander" not in obj.card.supertypes
                and (not mode.sacrifice_other or obj.object_id!=source.object_id)
                and (not mode.victim_color or (
                    obj.card.colors is not None
                    and mode.victim_color in obj.card.colors))]
            if not victims:
                continue
            # Sacrifice small expendable tokens first; don't choose a combo
            # sacrifice across multiple iterations of the same ability.
            victims.sort(key=lambda obj: (
                0 if obj.token else 1,
                0 if obj.object_id!=source.object_id else 2,
                obj.power,obj.object_id))
            victim=victims[0]
            resolved=activate_reviewed_sacrifice(
                zones,life,source.object_id,victim.object_id,raw_by_name,
                mana_service=mana_service,turn=turn,
                tap_ready=(not source.tapped and (
                    "creature" not in source.types
                    or entered_on_turn.get(source.object_id,0)<turn
                    or "haste" in source.keywords)),
                death_engine=death_engine,scry_to_bottom=False)
            if resolved is None:
                continue
            used_sacrifice_sources.add(source.object_id)
            events.append({
                "type":"reviewed_sacrifice_activated","card":resolved.source_name,
                "source_object_id":resolved.source_id,
                "victim_object_id":resolved.victim_old_id,
                "ability_operation":resolved.operation,
                "created_token_ids":list(resolved.token_ids),
                "drawn_ids":list(resolved.drawn_ids),
                "mana_added":list(resolved.mana_added),
                "death_trigger_count":resolved.death_trigger_count,
                "fidelity":"bounded_no_opponent_priority"})
        death_count=sum(ev.name=="dies" for ev in
                        kernel.events[turn_kernel_event_index:])
        for triggered in phase_engine.resolve(
                phase="end_step",active_seat=0,round_id=turn,
                death_count=death_count):
            events.append({
                "type":"reviewed_phase_resolved","phase":"end_step",
                "source":triggered.source_name,"source_object_id":triggered.source_id,
                "ability_slot":triggered.slot_id,
                "created_token_ids":list(triggered.created_token_ids),
                "drawn_ids":list(triggered.drawn_ids),
                "returned_object_id":triggered.returned_id,
                "fidelity":"bounded_no_opponent_priority"})
        floating_end = list(mana_service.floating())
        mana_service.clear()
        if (not zones.assert_consistent()
                or sum(not obj.token for obj in kernel.objects.values()) != 100):
            raise AssertionError("Physical non-token card conservation failed")
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
                                  and not o.token and o.card.name in raw_by_name
                                  and reviewed_rock(o.card.name, raw_by_name[o.card.name], colors) is not None
                                  for o in kernel.objects.values()),
            "floating_at_end_of_main": floating_end,
            "life_totals":dict(life.kernel.life_totals),
            "unsupported_cards_in_hand": sorted(
                kernel.get(oid).card.name for oid in zones.ids(0, "hand")
                if not reviewed_creature(deck_key, kernel.get(oid).card.name,
                                         raw_by_name[kernel.get(oid).card.name])
                and reviewed_rock(kernel.get(oid).card.name,
                                  raw_by_name[kernel.get(oid).card.name], colors) is None
                and not (reviewed_tutor(kernel.get(oid).card.name,
                                        raw_by_name[kernel.get(oid).card.name])
                         and reviewed_tutor(kernel.get(oid).card.name,
                                            raw_by_name[kernel.get(oid).card.name])[2]
                         in {"instant", "sorcery"})
                and reviewed_token_spell(kernel.get(oid).card.name,
                    raw_by_name[kernel.get(oid).card.name]) is None
                and not reviewed_phase_permanent(kernel.get(oid).card.name,
                    raw_by_name[kernel.get(oid).card.name])
                and not reviewed_sacrifice_artifact(kernel.get(oid).card.name,
                    raw_by_name[kernel.get(oid).card.name])
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
        "life_totals":dict(life.kernel.life_totals),
        "state_snapshots": states,
        "deck_intelligence": analysis,
        "first_unmodeled_choice": ("turn 1: opponent priority, other spells, and " 
                                 "strategic tutor decisions remain unavailable"),
        "limits": LIMITATIONS,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deck", choices=sorted(f.key for f in FIXTURES), required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--turns", type=int, default=6)
    parser.add_argument("--mulligan", choices=("one-free", "keep"), default="one-free")
    parser.add_argument("--profile", type=Path, help="Optional curated strategy JSON file")
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf-8")) if args.profile else None
    print(json.dumps(run_bounded_early_game(args.deck, seed=args.seed, turns=args.turns,
                                             mulligan=args.mulligan, profile=profile), indent=2))
