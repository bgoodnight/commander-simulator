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
from .mana_costs import UnsupportedManaCost
from .deck_fixtures import FIXTURES, EXPERIMENTAL_FIXTURES, SHARED_CATALOG
from .generic_cast import ReviewedCreatureCast, cast_reviewed_permanent
from .kernel_reporting import project_kernel_turn
from .board_features import analyze_authoritative_run
from .reviewed_early_cards import REVIEWED_BY_DECK, LIMITATIONS, reviewed_creature
from .snapshots import validate_snapshot
from .mana_kernel_bridge import _reviewed_modes
from .reviewed_rocks import reviewed_rock
from .reviewed_lands import reviewed_land
from .reviewed_tutors import reviewed_tutor
from .reviewed_tutor_cast import (eligible_reviewed_tutor_targets,
                                  cast_and_resolve_reviewed_tutor)
from .reviewed_draw_spells import (reviewed_draw_spell, cast_and_resolve_reviewed_draw_spell)
from .reviewed_token_spells import (reviewed_token_spell,
                                   cast_and_resolve_reviewed_token_spell)
from .bounded_trigger_effects import resolve_reviewed_spell_triggers
from .kernel_life import KernelLife
from .reviewed_phase_effects import ReviewedPhaseEngine,reviewed_phase_permanent
from .composed_abilities import ComposedAbilityEngine, reviewed_composed_permanent, ABILITIES
from .reviewed_commander_cast import commander_cost, cast_commander
from .reviewed_reactive_triggers import ReactiveTriggerEngine
from .reviewed_death_effects import ReviewedDeathEngine
from .reviewed_enter_effects import reviewed_enter_rule, execute_reviewed_enter
from .reviewed_unearth import reviewed_unearth, activate_reviewed_unearth, expire_reviewed_unearth
from .reviewed_flashback import reviewed_flashback, cast_reviewed_flashback
from .reviewed_graveyard_creatures import (
    reviewed_graveyard_creature, graveyard_creature_cast_ready,
    cast_reviewed_graveyard_creature)
from .reviewed_nonhand_cast_triggers import resolve_reviewed_nonhand_cast_triggers
from .reviewed_sacrifice_actions import (
    SACRIFICE_MODES, reviewed_sacrifice_artifact,
    activate_reviewed_sacrifice)
from .template_resources import TemplateManaService
from .resource_development import assess_resources, choose_tutor_target
from .resource_pilot import choose_token_mana_sacrifice, plan_common_spell, ritual_enables_spell
from .reviewed_common_spells import reviewed_common_spell, cast_common_spell
from .reviewed_ramp import reviewed_ramp, reviewed_ritual, cast_ritual, activate_land_ramp, resolve_enter_ramp
from .hand_cleanup import cleanup_hand
from .reviewed_escape import (reviewed_breach, escape_candidates,
    cast_reviewed_escape_token_spell, sacrifice_breach_at_end_step)
from .reviewed_buyback import reviewed_buyback, buyback_total_cost, cast_reviewed_buyback
from .reviewed_spell_copy import reviewed_copy_spell,cast_reiterate_copy,REITERATE

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
    fixture = next((x for x in (*FIXTURES, *EXPERIMENTAL_FIXTURES) if x.key == deck_key), None)
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
    # Pinned, source-verified ETB effects with safe bounded hand-cast paths.
    enter_hand_casts = {"Bastion of Remembrance", "Grave Titan",
                        "Marionette Apprentice", "Royal Warden",
                        "Triarch Praetorian", "Canoptek Tomb Sentinel"}
    def approved_enter_hand_cast(name):
        return name in enter_hand_casts and reviewed_enter_rule(name, raw_by_name[name]) is not None
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
        reviewed = ((section == "Commander" and all(
                        rule.oracle_id==identity.oracle_id and
                        rule.oracle_excerpt in raw_by_name[name].get("oracle_text","")
                        for rule in ABILITIES.get(name,())) and bool(ABILITIES.get(name)))
                    or reviewed_creature(deck_key, name, raw_by_name[name])
                    or reviewed_rock(name, raw_by_name[name], colors) is not None
                    or reviewed_land(name, raw_by_name[name], colors) is not None
                    or (tutor_review is not None
                        and tutor_review[2] in {"instant", "sorcery"})
                    or reviewed_token_spell(name, raw_by_name[name]) is not None
                    or reviewed_draw_spell(name,raw_by_name[name]) is not None
                    # Graveyard flashback permission is independently reviewed,
                    # even if no ordinary hand-cast recipe exists (Looting).
                    or reviewed_flashback(name, raw_by_name[name]) is not None
                    or reviewed_graveyard_creature(name, raw_by_name[name]) is not None
                    or reviewed_phase_permanent(name, raw_by_name[name])
                    or reviewed_composed_permanent(name,raw_by_name[name])
                    or reviewed_sacrifice_artifact(name,raw_by_name[name])
                    or reviewed_ramp(name,raw_by_name[name]) is not None
                    or reviewed_ritual(name,raw_by_name[name])
                    or reviewed_common_spell(name,raw_by_name[name]) is not None
                    or approved_enter_hand_cast(name)
                    or reviewed_breach(name,raw_by_name[name])
                    or reviewed_buyback(name,raw_by_name[name]) is not None
                    or reviewed_copy_spell(name,raw_by_name[name]) is not None)
        definition = CardDefinition(
            identity.oracle_id, name, types, subtypes=subtypes,
            supertypes=frozenset({"commander"}) if section == "Commander" else frozenset(),
            base_power=power, base_toughness=toughness,
            keywords=keywords, colors=colors_printed,
            coverage="approx" if reviewed else "unimplemented")
        for _ in range(quantity):
            zones.add(definition, 0, "command" if section == "Commander" else "library")

    mana_service = TemplateManaService(kernel, raw_by_name, colors, zones=zones)
    life = KernelLife(kernel)
    phase_engine = ReviewedPhaseEngine(zones, life, raw_by_name)
    death_engine = ReviewedDeathEngine(zones, life, raw_by_name)
    composed_engine = ComposedAbilityEngine(zones, life, raw_by_name,
                                           mana_service, death_engine)
    reactive_engine = ReactiveTriggerEngine(zones,life,raw_by_name)
    entered_on_turn = {}
    if len(kernel.objects) != 100:
        raise AssertionError("Pinned 100-card zone conservation failed at loading")
    zones.shuffle(0)
    zones.draw(0, 7)
    initial_hand = list(zones.names(0, "hand"))
    def supported_land(oid):
        obj=kernel.get(oid)
        if "land" not in obj.types:
            return False
        return bool(_reviewed_modes(obj.card.name,colors)
                    or reviewed_land(obj.card.name,raw_by_name[obj.card.name],colors)
                    or (obj.card.name == 'Myriad Landscape' and reviewed_ramp(obj.card.name,raw_by_name[obj.card.name])))
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
        mana_ledger_start = len(mana_service.mana_events)
        life_ledger_start = len(life.kernel.life_changes)
        turn_kernel_event_index=len(kernel.events)
        events = []
        def resolve_reactive():
            for triggered in reactive_engine.resolve():
                events.append({
                    "type":"reviewed_reactive_trigger",
                    "source":triggered.source_name,
                    "source_object_id":triggered.source_id,
                    "trigger_event":triggered.event,
                    "operation":triggered.operation,
                    "quantity":triggered.quantity,
                    "fidelity":"bounded_event_dispatch"})
        def approved_spell_triggers(ticket):
            """Execute only vetted cast triggers after an actual source cast."""
            source = kernel.get(ticket.object_id)
            nonhand = resolve_reviewed_nonhand_cast_triggers(
                zones, 0, ticket, raw_by_name)
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
                    for effect in effects] + [
                {"type":"reviewed_nonhand_cast_trigger",
                 "source":trigger["card"],
                 "source_graveyard_id":trigger["source_graveyard_id"],
                 "object_id":trigger["object_id"],
                 "triggered_by_stack_id":trigger["triggered_by_stack_id"],
                 "origin":trigger["origin"],
                 "fidelity":"bounded_no_opponent_priority"}
                for trigger in nonhand]
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
        resolve_reactive()
        drawn, okay = zones.draw(0, 1)  # Seat is explicitly not the starting seat.
        if not okay:
            raise ValueError("Library depleted before supported turn horizon")
        events.append({"type": "draw", "card": kernel.get(drawn[0]).card.name,
                       "object_id": drawn[0]})
        playable_lands = [oid for oid in zones.ids(0, "hand") if supported_land(oid)]
        if playable_lands:
            land_id = playable_lands[0]
            name = kernel.get(land_id).card.name
            other_lands=sum("land" in obj.types and obj.zone=="battlefield"
                            and obj.controller==0 for obj in kernel.objects.values())
            land_review=reviewed_land(name,raw_by_name[name],colors)
            new_id = zones.play_land(0, land_id)
            if ((land_review is not None and land_review.enters_tapped(other_lands))
                    or (name == 'Myriad Landscape' and reviewed_ramp(name,raw_by_name[name]) is not None)):
                kernel.get(new_id).tapped=True
                kernel._dirty()
            events.append({"type": "land_play", "card": name,
                           "from_object_id": land_id, "object_id": new_id,
                           "fidelity":"reviewed_partial_land" if land_review else "reviewed_basic_land",
                           "entered_tapped":bool(kernel.get(new_id).tapped),
                           "unsupported_abilities":list(land_review.ignored) if land_review else []})
        resource_start = assess_resources(kernel, mana_service, 0).__dict__
        # Main-phase resource policy: trade only expendable creature tokens for
        # mana when a reviewed hand spell is blocked but plausibly reachable.
        def supported_mana_payoff(obj):
            name = obj.card.name
            raw = raw_by_name.get(name)
            return bool(raw and (
                reviewed_creature(deck_key,name,raw)
                or reviewed_rock(name,raw,colors) is not None
                or reviewed_phase_permanent(name,raw)
                or approved_enter_hand_cast(name)
                or reviewed_ramp(name,raw) is not None))
        for _ in range(4):
            selected = choose_token_mana_sacrifice(
                zones,0,raw_by_name,mana_service,
                supported_spell=supported_mana_payoff,
                max_sacrifices=4)
            if selected is None:
                break
            source_id,victim_id = selected
            source_name=kernel.get(source_id).card.name
            mode=SACRIFICE_MODES[source_name]
            outcome=activate_reviewed_sacrifice(
                zones,life,source_id,victim_id,raw_by_name,
                mana_service=mana_service,turn=turn,tap_ready=True,
                death_engine=death_engine,
                mana_color="B" if mode.action=="any_color_mana" else None)
            if outcome is None:
                break
            events.append({"type":"reviewed_precast_mana_sacrifice",
                           "card":outcome.source_name,
                           "mana_added":list(outcome.mana_added),
                           "death_trigger_count":outcome.death_trigger_count,
                           "victim_object_id":victim_id,
                           "fidelity":"bounded_resource_sequencing"})
        resource_after_precast = assess_resources(kernel, mana_service, 0).__dict__
        copied_this_turn=set()
        # Reuse the same source-paid action for approved artifacts and creatures.
        # Prefer affordable ramp rocks before creatures: a limited pilot policy.
        while True:
            resolve_reactive()
            options = []
            # Command-zone casting uses the same physical mana service and
            # a reusable two-generic-per-previous-cast tax.
            for commander_id in zones.ids(0,"command"):
                cmd=kernel.get(commander_id)
                cost=commander_cost(kernel,cmd,raw_by_name)
                if cost is None:
                    continue
                preview=mana_service.plan_spell(0,cost,cmd)
                if preview is not None:
                    options.append((1,len(preview.source_ids),cmd.card.name,
                                    commander_id,"commander",cost,None))
            for oid in zones.ids(0, "hand"):
                obj = kernel.get(oid)
                name = obj.card.name
                raw = raw_by_name[name]
                is_creature = reviewed_creature(deck_key, name, raw)
                rock = reviewed_rock(name, raw, colors)
                token_spell = reviewed_token_spell(name, raw)
                draw_spell = reviewed_draw_spell(name,raw)
                phase_enchantment = (reviewed_phase_permanent(name, raw)
                                     or reviewed_breach(name, raw)
                                     or reviewed_composed_permanent(name,raw))
                sacrifice_artifact = reviewed_sacrifice_artifact(name, raw)
                entering = approved_enter_hand_cast(name)
                ramp = reviewed_ramp(name,raw) if "land" not in obj.types else None
                ritual = reviewed_ritual(name,raw)
                common = reviewed_common_spell(name,raw)
                common_plan = (plan_common_spell(zones,0,obj,common,raw_by_name,mana_service,life)
                               if common is not None else None)
                if ritual and not ritual_enables_spell(zones,0,obj,raw_by_name,mana_service):
                    continue
                tutor = reviewed_tutor(name, raw)
                eligible = (eligible_reviewed_tutor_targets(zones, 0, name, raw_by_name)
                            if tutor and tutor[2] in {"instant", "sorcery"} else ())
                if (not is_creature and rock is None and not eligible
                        and token_spell is None and draw_spell is None and not phase_enchantment
                        and not sacrifice_artifact and not entering and not ramp and not ritual
                        and not common_plan):
                    continue
                cost = common_plan[0] if common_plan else registry.get(name).primary_face().mana_cost
                payment = mana_service.plan_spell(0, cost, obj)
                if payment is not None:
                    kind = ("common_spell" if common_plan else
                            "ritual" if ritual else
                            "artifact" if rock is not None or sacrifice_artifact or (ramp and name == "Wayfarer\u0027s Bauble") else
                            "enchantment" if phase_enchantment or (entering and "Enchantment" in raw.get("type_line","").split(" — ",1)[0]) else
                            "tutor" if eligible else
                            "draw_spell" if draw_spell is not None else
                            "token_spell" if token_spell is not None else "creature")
                    target = (common_plan[1:] if common_plan else
                              choose_tutor_target(zones, 0, eligible, raw_by_name, colors) if eligible else None)
                    # Reviewed trigger creatures precede spells so their
                    # shared effects may fire on subsequent actual casts.
                    options.append((0 if rock is not None or ritual else
                                    1 if is_creature else
                                    2 if sacrifice_artifact else
                                    3 if phase_enchantment or entering else
                                    4 if eligible else 5,
                                    len(payment.source_ids), name, oid, kind, cost, target))
            if not options:
                break
            _, _, name, oid, kind, cost, target = min(options)
            if kind == "commander":
                triggered=[]
                outcome=cast_commander(zones,0,oid,raw_by_name,mana_service,
                    on_cast=lambda ticket:triggered.extend(
                        approved_spell_triggers(ticket)))
                if outcome is None:
                    raise AssertionError("Reviewed commander payment changed")
                entered_on_turn[outcome.physical_id]=turn
                events.extend(triggered)
                events.append({"type":"reviewed_commander_cast",
                    "card":outcome.card_name,"object_id":outcome.physical_id,
                    "paid_source_ids":list(outcome.paid_source_ids),
                    "commander_tax":outcome.commander_tax,
                    "fidelity":"reviewed_command_zone"})
                continue
            if kind == "common_spell":
                x, victims = target
                triggered=[]
                result=cast_common_spell(
                    zones,life,0,oid,raw_by_name,colors,mana_service,
                    x=x,sacrifice_ids=victims,death_engine=death_engine,turn=turn,
                    on_cast=lambda ticket: triggered.extend(approved_spell_triggers(ticket)))
                if result is None:
                    raise AssertionError("Reviewed common spell payment became unavailable")
                events.extend(triggered)
                events.append({"type":"reviewed_common_spell_resolved",
                               "card":result.name,"x":x,
                               "drawn_ids":list(result.drawn_ids),
                               "created_token_ids":list(result.created_token_ids),
                               "sacrificed_ids":list(result.sacrificed_ids),
                               "life_lost":result.life_lost,
                               "paid_source_ids":list(result.paid_source_ids),
                               "fidelity":"bounded_common_spell"})
                continue
            if kind == "ritual":
                result = cast_ritual(zones, 0, oid, raw_by_name, colors, mana_service)
                if result is None:
                    raise AssertionError("Reviewed ritual payment changed")
                events.append({"type":"reviewed_ritual_cast","card":name,
                               "graveyard_id":result,"mana_added":["B","B","B"],
                               "fidelity":"reviewed_shared_mana"})
                continue
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
            if kind == "draw_spell":
                triggered=[]
                result=cast_and_resolve_reviewed_draw_spell(
                    zones,0,oid,raw_by_name,colors,mana_service,
                    on_cast=lambda ticket:triggered.extend(
                        approved_spell_triggers(ticket)))
                if result is None:
                    raise AssertionError("Source-paid draw spell became unavailable")
                events.append({"type":"reviewed_draw_spell_cast",
                               "card":name,
                               "stack_object_id":result.source_stack_id,
                               "source_object_ids":list(result.mana_source_ids),
                               "fidelity":"reviewed_physical_draw"})
                events.extend(triggered)
                events.append({"type":"reviewed_draw_spell_resolved",
                               "card":name,
                               "source_graveyard_id":result.source_graveyard_id,
                               "drawn_ids":list(result.drawn_ids),
                               "unsupported_abilities":list(result.limitations),
                               "fidelity":"reviewed_physical_draw"})
                continue
            if kind == "token_spell":
                triggered=[]
                def cast_copy_response(ticket):
                    triggered.extend(approved_spell_triggers(ticket))
                    # Exactly one bounded response per turn; the original
                    # remains pending on the real stack until its own resolve.
                    if copied_this_turn:
                        return
                    for copy_id in zones.ids(0,"hand"):
                        copy_obj=kernel.get(copy_id)
                        if (copy_obj.card.coverage=="unimplemented"
                                or reviewed_copy_spell(copy_obj.card.name,
                                        raw_by_name[copy_obj.card.name]) is None):
                            continue
                        extra=buyback_total_cost(REITERATE,True)
                        afford_buyback=(mana_service.plan_spell(
                            0,extra,copy_obj) is not None)
                        if (not afford_buyback and mana_service.plan_spell(
                                0,REITERATE.mana_cost,copy_obj) is None):
                            continue
                        response_triggers=[]
                        copied=cast_reiterate_copy(
                            zones,0,copy_id,ticket,raw_by_name,mana_service,
                            buyback=afford_buyback,casting_window=True,
                            on_cast=lambda copy_ticket:response_triggers.extend(
                                approved_spell_triggers(copy_ticket)),
                            on_copy=lambda original:response_triggers.extend(
                                {"type":"reviewed_trigger_resolved",
                                 "source":effect.card_name,
                                 "source_object_id":effect.source_id,
                                 "ability_slot":effect.slot_id,
                                 "created_token_ids":list(effect.created_token_ids),
                                 "drawn_ids":list(effect.drawn_ids),
                                 "fidelity":"bounded_reviewed_copy"}
                                for effect in resolve_reviewed_spell_triggers(
                                    zones,0,raw_by_name,event="spell_copied",
                                    spell_types=frozenset({"sorcery"}))))
                        if copied is None:
                            raise AssertionError("Reviewed response payment invalidated")
                        copied_this_turn.add(copy_id)
                        triggered.append({
                            "type":"reviewed_spell_copy_cast","card":"Reiterate",
                            "copier_source_id":copied.copier_old_id,
                            "copied_spell":copied.copied_card_name,
                            "original_stack_id":copied.original_target_stack_id,
                            "buyback":copied.bought_back,
                            "paid_source_ids":list(copied.mana_source_ids),
                            "fidelity":"bounded_reviewed_copy"})
                        triggered.extend(response_triggers)
                        triggered.append({
                            "type":"reviewed_spell_copy_resolved",
                            "card":"Reiterate",
                            "copied_spell":copied.copied_card_name,
                            "created_token_ids":list(copied.created_token_ids),
                            "copy_effect_source_id":copied.copy_effect_source_id,
                            "destination":copied.copier_destination,
                            "destination_object_id":copied.copier_destination_id,
                            "fidelity":"bounded_reviewed_copy"})
                        break
                result = cast_and_resolve_reviewed_token_spell(
                    zones, 0, oid, raw_by_name, colors, mana_service,
                    on_cast=cast_copy_response)
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
                if rock is not None and rock[0].enter_tapped:
                    kernel.get(resolved_id).tapped = True
                    kernel._dirty()
            events.append({"type": kind + "_resolved", "card": name,
                           "object_id": resolved_id, "fidelity": "limited_generic_resolution"})
            if name == "Solemn Simulacrum" and reviewed_ramp(name,raw_by_name[name]):
                moved = resolve_enter_ramp(zones,0,resolved_id,raw_by_name)
                events.append({"type":"reviewed_enter_ramp","card":name,
                               "land_ids":list(moved or ()),"fidelity":"reviewed_shared_basic_search"})
            if approved_enter_hand_cast(name) and not reviewed_enter_rule(name,raw_by_name[name]).only_from_graveyard:
                rule = reviewed_enter_rule(name, raw_by_name[name])
                # The pilot explicitly chooses the Servo fabricate mode.
                choice = "servo" if rule.operation == "fabricate_one" else None
                entered = execute_reviewed_enter(
                    zones, life, resolved_id, raw_by_name, choice=choice,
                    death_engine=death_engine, turn=turn)
                if entered is None:
                    raise AssertionError("Reviewed ETB was not executed")
                events.append({"type":"reviewed_enter_resolved",
                               "card":name,"source_object_id":resolved_id,
                               "ability_operation":entered.operation,
                               "created_token_ids":list(entered.token_ids),
                               "drawn_ids":list(entered.drawn_ids),
                               "fidelity":"bounded_no_opponent_priority"})
        # Shared ramp activation uses actual paid sources and shuffled basic lands.
        for source in list(kernel.on_battlefield()):
            if source.controller == 0 and source.card.name in {"Wayfarer's Bauble", "Myriad Landscape"}:
                moved = activate_land_ramp(zones, 0, source.object_id, raw_by_name, mana_service)
                if moved:
                    events.append({"type":"reviewed_land_ramp","card":source.card.name,
                                   "land_ids":list(moved),"fidelity":"reviewed_shared_basic_search"})
        resolve_reactive()
        # One reviewed instant spell per turn in the verified main-phase
        # window. Optional buyback is preferred only when fully payable.
        buyback_options=[]
        if zones.ids(0,"library"):
            for oid in zones.ids(0,"hand"):
                obj=kernel.get(oid)
                rule=reviewed_buyback(obj.card.name,raw_by_name.get(obj.card.name))
                if rule is None or obj.card.coverage=="unimplemented":
                    continue
                with_buyback=buyback_total_cost(rule,True)
                if mana_service.plan_spell(0,with_buyback,obj) is not None:
                    buyback_options.append((obj.card.name,oid,True))
                elif mana_service.plan_spell(0,rule.mana_cost,obj) is not None:
                    buyback_options.append((obj.card.name,oid,False))
        if buyback_options:
            _,oid,use_buyback=min(buyback_options)
            triggered=[]
            cast=cast_reviewed_buyback(
                zones,0,oid,raw_by_name,mana_service,
                buyback=use_buyback,casting_window=True,
                on_cast=lambda ticket:triggered.extend(approved_spell_triggers(ticket)))
            if cast is None:
                raise AssertionError("Reviewed buyback plan invalidated")
            events.append({"type":"reviewed_buyback_cast","card":cast.card_name,
                           "source_object_id":cast.source_old_id,
                           "paid_buyback":cast.bought_back,
                           "source_object_ids":list(cast.paid_source_ids),
                           "fidelity":"bounded_reviewed_buyback"})
            events.extend(triggered)
            events.append({"type":"reviewed_buyback_resolved","card":cast.card_name,
                           "destination":cast.destination,
                           "destination_object_id":cast.destination_id,
                           "drawn_ids":list(cast.drawn_ids),
                           "fidelity":"bounded_reviewed_buyback"})
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
            if mode.action in {'colorless_mana','any_color_mana','black_mana_by_value'}:
                continue  # no speculative late sacrifice after casting window
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
                death_engine=death_engine,scry_to_bottom=False,
                mana_color=("R" if "R" in colors else
                            "B" if "B" in colors else
                            next(iter(sorted(colors))))
                            if mode.action=="any_color_mana" else None)
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
        # One verified conditional graveyard creature cast per turn. Do not
        # create a synthetic loop: recursion must draw on real mana and a
        # currently controlled creature of the required subtype. The bounded
        # pilot caps discretionary choices, while the primitive is reusable.
        gy_creature_options=[]
        for grave_id in zones.ids(0,"graveyard"):
            source=kernel.get(grave_id)
            rule=graveyard_creature_cast_ready(
                zones,0,grave_id,raw_by_name)
            if (rule is not None
                    and mana_service.plan_spell(
                        0,rule.printed_cost,source) is not None):
                gy_creature_options.append((source.card.name,grave_id))
        if gy_creature_options:
            _,grave_id=min(gy_creature_options)
            result=cast_reviewed_graveyard_creature(
                zones,0,grave_id,raw_by_name,mana_service,
                sorcery_window=True,
                on_cast=lambda ticket:events.extend(approved_spell_triggers(ticket)))
            if result is None:
                raise AssertionError("Reviewed graveyard cast payment invalidated")
            entered_on_turn[result.permanent_id]=turn
            events.append({
                "type":"reviewed_graveyard_creature_cast",
                "card":result.card_name,
                "source_graveyard_id":result.source_old_id,
                "stack_object_id":result.stack_id,
                "source_object_ids":list(result.paid_source_ids),
                "fidelity":"bounded_reviewed_graveyard_cast"})
            events.append({
                "type":"reviewed_graveyard_creature_resolved",
                "card":result.card_name,
                "object_id":result.permanent_id,
                "fidelity":"bounded_reviewed_graveyard_cast"})
        # Reuse the reviewed paid graveyard spell path, with cast triggers
        # tied to the real stack ticket and exile on resolution.
        flashback_options=[]
        for grave_id in zones.ids(0,"graveyard"):
            spell=kernel.get(grave_id)
            review=reviewed_flashback(spell.card.name,raw_by_name.get(spell.card.name))
            if review and mana_service.plan_spell(0,review.alternate_cost,spell) is not None:
                if (review.operation!="draw_discard_two"
                        or len(zones.ids(0,"library"))>=2):
                    flashback_options.append((review.alternate_cost,spell.card.name,grave_id))
        if flashback_options:
            _,_,grave_id=min(flashback_options)
            triggered=[]
            result=cast_reviewed_flashback(
                zones,0,grave_id,raw_by_name,mana_service,
                sorcery_window=True,on_cast=lambda ticket:triggered.extend(
                    approved_spell_triggers(ticket)))
            if result is None:
                raise AssertionError("Flashback payment invalidated")
            events.append({"type":"reviewed_flashback_cast",
                           "card":result.card_name,
                           "source_graveyard_id":result.source_old_id,
                           "source_object_ids":list(result.mana_source_ids),
                           "fidelity":"bounded_no_opponent_priority"})
            events.extend(triggered)
            events.append({"type":"reviewed_flashback_resolved",
                           "card":result.card_name,"exiled_object_id":result.exiled_id,
                           "created_token_ids":list(result.created_token_ids),
                           "drawn_ids":list(result.drawn_ids),
                           "fidelity":"bounded_no_opponent_priority"})
        # A genuine Breach grants a shared escape permission while present.
        # The bounded pilot chooses at most one independently reviewed spell,
        # paying its printed cost and exiling THREE other physical cards.
        escape_options=[]
        for grave_id in zones.ids(0,"graveyard"):
            spell=kernel.get(grave_id)
            if reviewed_token_spell(spell.card.name,raw_by_name.get(spell.card.name)) is None:
                continue
            fodder=escape_candidates(zones,0,grave_id,raw_by_name,mana_service)
            if len(fodder)>=3:
                escape_options.append((spell.card.name,grave_id,fodder))
        if escape_options:
            _,source_id,fodder=min(escape_options)
            triggered=[]
            result=cast_reviewed_escape_token_spell(
                zones,0,source_id,raw_by_name,mana_service,
                exile_ids=tuple(fodder[:3]),sorcery_window=True,
                on_cast=lambda ticket:triggered.extend(
                    approved_spell_triggers(ticket)))
            events.append({"type":"reviewed_escape_cast","card":result.card_name,
                           "source_graveyard_id":result.source_old_id,
                           "source_object_ids":list(result.paid_source_ids),
                           "exiled_other_object_ids":list(result.exiled_other_ids),
                           "stack_object_id":result.stack_id,
                           "fidelity":"bounded_physical_escape"})
            events.extend(triggered)
            events.append({"type":"reviewed_escape_resolved","card":result.card_name,
                           "graveyard_object_id":result.graveyard_id,
                           "created_token_ids":list(result.created_token_ids),
                           "fidelity":"bounded_physical_escape"})
        # One conservative, source-paid graveyard activation per turn.
        # This uses the existing physical unearth replacement map, not a
        # shadow battlefield. Opponent-choice Lokhust is deferred.
        unearth_options=[]
        for grave_id in zones.ids(0,"graveyard"):
            source=kernel.get(grave_id)
            review=reviewed_unearth(source.card.name,raw_by_name.get(source.card.name))
            if review is None or source.card.name=="Lokhust Heavy Destroyer":
                continue
            if source.card.name=="Triarch Praetorian" and len(zones.ids(0,"library"))<2:
                continue
            if mana_service.plan(0,review.cost) is not None:
                unearth_options.append((review.cost,source.card.name,grave_id))
        if unearth_options:
            _,_,grave_id=min(unearth_options)
            result=activate_reviewed_unearth(
                zones,0,grave_id,raw_by_name,mana_service,
                sorcery_window=True,life=life,death_engine=death_engine,
                turn=turn)
            if result is None:
                raise AssertionError("Unearth payment invalidated")
            entered_on_turn[result.permanent_id]=turn
            events.append({"type":"reviewed_unearth_resolved",
                           "card":result.card_name,
                           "source_graveyard_id":result.source_old_id,
                           "object_id":result.permanent_id,
                           "source_object_ids":list(result.paid_source_ids),
                           "enter_operation":(result.enter_result.operation
                                              if result.enter_result else None),
                           "created_token_ids":(list(result.enter_result.token_ids)
                                                if result.enter_result else []),
                           "fidelity":"bounded_no_opponent_priority"})
        death_count=sum(ev.name=="dies" for ev in
                        kernel.events[turn_kernel_event_index:])
        # Resolve approved composed end-step abilities. The bounded pilot
        # supplies no optional X choice; it does not invent a strategy.
        for composed in composed_engine.end_step(
                active_seat=0, turn=turn, life_start_index=life_ledger_start):
            events.append({
                "type":"reviewed_composed_end_step",
                "source_object_id":composed.source_id,
                "effect":composed.operation,
                "created_token_ids":list(composed.created_ids),
                "death_trigger_count":composed.deaths,
                "fidelity":"bounded_no_opponent_priority"})
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
        resolve_reactive()
        # Unearthed cards remaining here leave at the next end step.
        # Exits earlier in the turn were already replaced by the kernel.
        for old_id,exiled_id in expire_reviewed_unearth(zones):
            events.append({"type":"reviewed_unearth_expired",
                           "object_id":old_id,"exiled_object_id":exiled_id,
                           "fidelity":"bounded_no_opponent_priority"})
        # Underworld Breach is sacrificed at the beginning of the end step.
        # This bounded phase host resolves the trigger before cleanup.
        for old_id,new_id in sacrifice_breach_at_end_step(zones,0,raw_by_name):
            events.append({"type":"reviewed_breach_sacrificed",
                           "source_object_id":old_id,
                           "graveyard_object_id":new_id,
                           "fidelity":"bounded_no_opponent_priority"})
        # Generic reusable *feasibility* fallback for every unreviewed card.
        # This is a read-only source-paid preview over existing physical
        # objects. It never invents a legal cast, effect, zone move, target,
        # priority pass, or mana spent. Thus future imported cards remain
        # useful in diagnostic traces without granting unknown abilities.
        candidates_seen=set()
        for oid in zones.ids(0, "hand"):
            obj=kernel.get(oid)
            name=obj.card.name
            if name in candidates_seen or "land" in obj.types:
                continue
            candidates_seen.add(name)
            if obj.card.coverage!="unimplemented":
                continue
            try:
                printed=registry.get(name).primary_face().mana_cost
                payment=mana_service.plan_spell(0,printed,obj)
            except (NotImplementedError,UnsupportedManaCost):
                continue
            if payment is not None:
                events.append({
                    "type":"source_paid_candidate",
                    "card":name,
                    "object_id":oid,
                    "source_object_ids":list(payment.source_ids),
                    "fidelity":"payment_preview_only",
                    "effect_status":"unsupported",
                    "limitations":("Cost feasibility is not casting permission; "
                                   "timing, targets, mandatory abilities, "
                                   "priority and resolution were not assessed")
                })
        resolve_reactive()
        # Cleanup follows all end-step abilities; use actual kernel movement.
        # The limited pilot already spent available main-phase mana and cast
        # supported spells before this point, avoiding excess hand cards when
        # possible. Cleanup discards follow a modest board-aware ranking.
        def hand_action_supported(obj):
            name = obj.card.name
            raw = raw_by_name[name]
            return bool(
                supported_land(obj.object_id)
                or reviewed_creature(deck_key, name, raw)
                or reviewed_rock(name, raw, colors) is not None
                or reviewed_token_spell(name, raw) is not None
                or reviewed_draw_spell(name,raw) is not None
                or reviewed_tutor(name, raw) is not None
                or reviewed_phase_permanent(name, raw)
                or reviewed_composed_permanent(name,raw)
                or reviewed_sacrifice_artifact(name, raw)
                or reviewed_ramp(name,raw) is not None
                or reviewed_ritual(name,raw)
                or reviewed_common_spell(name,raw) is not None
                or approved_enter_hand_cast(name)
                or reviewed_breach(name,raw)
                or reviewed_buyback(name,raw))
        cleanup = cleanup_hand(
            zones, 0, raw_by_name, supported_action=hand_action_supported)
        for choice in cleanup.discarded:
            events.append({
                "type": "cleanup_discard", "card": choice.name,
                "from_object_id": choice.old_id,
                "graveyard_object_id": choice.graveyard_id,
                "hand_before_cleanup": cleanup.hand_before,
                "maximum_hand_size": cleanup.maximum_hand_size,
                "utility_score": choice.utility_score,
                "policy": "bounded_board_utility_v1",
                "fidelity": "physical_cleanup_no_discard_triggers"})
        if cleanup.maximum_hand_size is not None:
            assert cleanup.hand_after <= cleanup.maximum_hand_size
        resolve_reactive()
        floating_end = list(mana_service.floating())
        resource_end = assess_resources(kernel, mana_service, 0).__dict__
        mana_service.clear()
        if (not zones.assert_consistent()
                or sum(not obj.token for obj in kernel.objects.values()) != 100):
            raise AssertionError("Physical non-token card conservation failed")
        state = project_kernel_turn(zones, 0, turn, catalog)
        states.append(state)
        actions_by_turn.append({
            "turn": turn, "events": events, "hand_size": len(zones.ids(0, "hand")),
            "hand_size_before_cleanup": cleanup.hand_before,
            "maximum_hand_size": cleanup.maximum_hand_size,
            "cleanup_discard_count": len(cleanup.discarded),
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
            "resource_start": resource_start,
            "resource_after_precast": resource_after_precast,
            "resource_end": resource_end,
            "mana_payment_events": list(mana_service.mana_events[mana_ledger_start:]),
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
                and reviewed_draw_spell(kernel.get(oid).card.name,
                    raw_by_name[kernel.get(oid).card.name]) is None
                and not reviewed_phase_permanent(kernel.get(oid).card.name,
                    raw_by_name[kernel.get(oid).card.name])
                and not reviewed_sacrifice_artifact(kernel.get(oid).card.name,
                    raw_by_name[kernel.get(oid).card.name])
                and reviewed_ramp(kernel.get(oid).card.name,
                    raw_by_name[kernel.get(oid).card.name]) is None
                and not reviewed_ritual(kernel.get(oid).card.name,
                    raw_by_name[kernel.get(oid).card.name])
                and not approved_enter_hand_cast(kernel.get(oid).card.name)
                and reviewed_buyback(kernel.get(oid).card.name,
                    raw_by_name[kernel.get(oid).card.name]) is None
                and reviewed_copy_spell(kernel.get(oid).card.name,
                    raw_by_name[kernel.get(oid).card.name]) is None
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
    parser.add_argument("--deck", choices=sorted(f.key for f in (*FIXTURES, *EXPERIMENTAL_FIXTURES)), required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--turns", type=int, default=6)
    parser.add_argument("--mulligan", choices=("one-free", "keep"), default="one-free")
    parser.add_argument("--profile", type=Path, help="Optional curated strategy JSON file")
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf-8")) if args.profile else None
    print(json.dumps(run_bounded_early_game(args.deck, seed=args.seed, turns=args.turns,
                                             mulligan=args.mulligan, profile=profile), indent=2))
