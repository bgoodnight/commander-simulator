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
from .provisional_import import provisional_profile, provisional_report
from .provisional_actions import cast_provisional_spell
from .library_actions import required_library_cards_for_draws, resolve_library_actions
from .kernel_reporting import project_kernel_turn
from .board_features import analyze_authoritative_run
from .reviewed_early_cards import REVIEWED_BY_DECK, LIMITATIONS, reviewed_creature
from .snapshots import validate_snapshot
from .mana_kernel_bridge import _reviewed_modes
from .reviewed_rocks import reviewed_rock
from .reviewed_lands import reviewed_land
from .reviewed_land_entry import reviewed_land_entry, resolve_land_entry
from .reviewed_utility_activations import reviewed_utility, activate_utility
from .reviewed_tutors import reviewed_tutor
from .reviewed_tutor_cast import (eligible_reviewed_tutor_targets,
                                  cast_and_resolve_reviewed_tutor)
from .reviewed_draw_spells import (reviewed_draw_spell, cast_and_resolve_reviewed_draw_spell)
from .reviewed_token_spells import (reviewed_token_spell,
                                   cast_and_resolve_reviewed_token_spell)
from .bounded_trigger_effects import resolve_reviewed_spell_triggers
from .kernel_life import KernelLife
from .outcome_reporting import LifeOutcomeRecorder
from .physical_common_effects import EmptyLibraryDraw
from .reviewed_phase_effects import ReviewedPhaseEngine,reviewed_phase_permanent
from .composed_abilities import ComposedAbilityEngine, reviewed_composed_permanent, ABILITIES
from .reviewed_commander_cast import commander_cost, cast_commander
from .reviewed_reactive_triggers import ReactiveTriggerEngine
from .reviewed_entry_choices import reviewed_entry_choice, set_reviewed_entry_choice
from .reviewed_attachments import AttachmentEngine,reviewed_attachment
from .reviewed_zone_spells import ZoneSpellEngine,reviewed_zone_spell
from .reviewed_graveyard_spells import (
    reviewed_graveyard_spell,choose_graveyard_spell_targets,
    cast_reviewed_graveyard_spell)
from .reviewed_activated_utilities import activate_reviewed,reviewed_activation
from .reviewed_cast_reactions import resolve_cast_reactions
from .opponent_stress import BoundedOpponentPressure
from .reviewed_death_effects import ReviewedDeathEngine
from .reviewed_enter_effects import reviewed_enter_rule, execute_reviewed_enter
from .reviewed_entry_chains import resolve_reviewed_entry_chain, bounded_entry_choice
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
from .pilot_policy import (
    STYLES,ARCHETYPES,PilotContext,infer_deck_signals,
    infer_pilot_archetype,choose_legal_option)
from .pilot_tactics import choose_discretionary_sacrifice
from .resource_pilot import (choose_token_mana_sacrifice, plan_common_spell,
                             ritual_enables_spell, choose_composed_activation,
                             choose_variable_end_step_payments,
                             choose_utility_activation, choose_end_step_token_mana,
                             choose_reviewed_removal, choose_composed_x_activation,
                             choose_attachment_use,choose_temporary_reanimation)
from .reviewed_common_spells import reviewed_common_spell, cast_common_spell
from .reviewed_removal_spells import reviewed_removal, cast_removal
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


def _printed_supertypes(type_line, *, commander=False):
    """Preserve official supertypes on verified physical card definitions.

    The identity loader historically projected types and subtypes but not the
    printed Legendary supertype. A graveyard's 'all legendary creature cards'
    requirement must use the actual printed characteristic, never a card
    name or deck-specific list.
    """
    if not isinstance(type_line,str):
        raise TypeError("Printed type line must be verified text")
    supertype_words=frozenset({"basic","legendary","snow","world","ongoing"})
    printed=frozenset(word.lower()
                      for word in type_line.split(" — ",1)[0].split()
                      if word.lower() in supertype_words)
    return printed | (frozenset({"commander"}) if commander else frozenset())


def _load_live_kernel():
    # Historical version modules aren't packaged; use the established isolated
    # v9b physical-zone kernel. This is NOT another state/zone implementation.
    legacy_path = str(ROOT / "simulator" / "v9b_live")
    if legacy_path not in sys.path:
        sys.path.insert(0, legacy_path)
    from state import IndexedKernel, LiveZones
    from rules import CardDefinition
    return IndexedKernel, LiveZones, CardDefinition


def run_bounded_early_game(deck_key, *, seed=0, turns=6, mulligan="one-free", profile=None, opponent_scenario=None, provisional_mode="off",pilot_style="adaptive",pilot_archetype="auto"):
    """Play a small reviewed set of actual land, rock and creature actions.

    A deterministic, conservative fixed pilot draws, plays one supported land,
    and casts affordable reviewed rocks/ordinary creatures from hand without
    pretending to implement printed abilities. All 100 physical cards occupy
    the same kernel; no observation-mode synthetic battlefield exists.
    """
    if type(seed) is not int or type(turns) is not int or not 1 <= turns <= 30:
        raise ValueError("Expected integer seed and 1..30 rounds")
    if mulligan not in ("one-free", "keep"):
        raise ValueError("Unknown mulligan policy")
    if pilot_style not in STYLES:
        raise ValueError("Unknown deterministic pilot personality")
    if pilot_archetype not in ARCHETYPES:
        raise ValueError("Unknown pilot archetype")
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
    pilot_signals=infer_deck_signals(snapshot.deck.cards,raw_by_name)
    pilot_strategy=infer_pilot_archetype(pilot_signals,pilot_archetype)
    if provisional_mode not in {'off','safe'}:
        raise ValueError('Unknown provisional mode')
    provisional_by_name = ({name: provisional_profile(raw) for name,raw in raw_by_name.items()}
        if provisional_mode=='safe' else {})
    # Pinned, source-verified ETB effects with safe bounded hand-cast paths.
    enter_hand_casts = {"Bastion of Remembrance", "Grave Titan", "Massacre Wurm",
                        "Flayed One", "Mire Triton", "Undead Butler",
                        "Technomancer", "Lord of Change", "Woe Strider",
                        "Canoptek Scarab Swarm",
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
                    or reviewed_attachment(name,raw_by_name[name]) is not None
                    or reviewed_zone_spell(name,raw_by_name[name]) is not None
                    or reviewed_graveyard_spell(name,raw_by_name[name]) is not None
                    or reviewed_activation(name,raw_by_name[name]) is not None
                    or (reviewed_utility(name,raw_by_name[name]) is not None
                        and reviewed_utility(name,raw_by_name[name]).source_zone=="battlefield"
                        and "enchantment" in types)
                    or reviewed_sacrifice_artifact(name,raw_by_name[name])
                    or reviewed_ramp(name,raw_by_name[name]) is not None
                    or reviewed_ritual(name,raw_by_name[name])
                    or reviewed_common_spell(name,raw_by_name[name]) is not None
                    or reviewed_removal(name,raw_by_name[name]) is not None
                    or approved_enter_hand_cast(name)
                    or reviewed_breach(name,raw_by_name[name])
                    or reviewed_buyback(name,raw_by_name[name]) is not None
                    or reviewed_copy_spell(name,raw_by_name[name]) is not None
                    or provisional_by_name.get(name) is not None)
        definition = CardDefinition(
            identity.oracle_id, name, types, subtypes=subtypes,
            supertypes=_printed_supertypes(
                face.type_line if face is not None else raw_by_name[name].get("type_line",""),
                commander=(section=="Commander")),
            base_power=power, base_toughness=toughness,
            keywords=keywords, colors=colors_printed,
            coverage="approx" if reviewed else "unimplemented")
        for _ in range(quantity):
            zones.add(definition, 0, "command" if section == "Commander" else "library")

    mana_service = TemplateManaService(kernel, raw_by_name, colors, zones=zones,
                                       provisional_mode=provisional_mode)
    def preview_spell(*args,**kwargs):
        """Fail closed on bounded speculative mana search, never commit it."""
        try:
            return mana_service.plan_spell(*args,**kwargs)
        except ValueError as err:
            if str(err)!="Bounded mana search exhausted; no action committed":
                raise
            return None
    life = KernelLife(kernel)
    life.install_reviewed_replacements(raw_by_name)
    phase_engine = ReviewedPhaseEngine(zones, life, raw_by_name)
    death_engine = ReviewedDeathEngine(
        zones, life, raw_by_name, provisional_mode=provisional_mode)
    composed_engine = ComposedAbilityEngine(zones, life, raw_by_name,
                                           mana_service, death_engine)
    reactive_engine = ReactiveTriggerEngine(zones,life,raw_by_name)
    attachment_engine=AttachmentEngine(
        zones,life,raw_by_name,mana_service,death_engine)
    death_engine.attachments=attachment_engine
    zone_engine=ZoneSpellEngine(zones,life,raw_by_name,
                               mana_service,death_engine)
    death_engine.zone_spells=zone_engine
    opponent_pressure = (BoundedOpponentPressure(
        zones,life,raw_by_name,death_engine,phase_engine,CardDefinition,
        seed=seed,scenario=opponent_scenario,
        attachment_engine=attachment_engine)
        if opponent_scenario is not None else None)
    if opponent_pressure is not None:
        opponent_pressure.zone_spells=zone_engine
    entered_on_turn = {}
    if sum(o.owner==0 and not o.token for o in kernel.objects.values()) != 100:
        raise AssertionError("Pinned 100-card zone conservation failed at loading")
    zones.shuffle(0)
    zones.draw(0, 7)
    initial_hand = list(zones.names(0, "hand"))
    def supported_land(oid):
        obj=kernel.get(oid)
        if "land" not in obj.types:
            return False
        provisional=provisional_by_name.get(obj.card.name)
        return bool(_reviewed_modes(obj.card.name,colors)
                    or reviewed_land(obj.card.name,raw_by_name[obj.card.name],colors)
                    or (provisional is not None and provisional.kind=="land_mana"
                        and obj.card.card_id==provisional.oracle_id)
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
    outcome_recorder=LifeOutcomeRecorder(
        dict(life.kernel.life_totals),
        opponent_model=(opponent_pressure is not None))
    for turn in range(1, turns + 1):
        mana_service.clear()
        mana_ledger_start = len(mana_service.mana_events)
        life_ledger_start = len(life.kernel.life_changes)
        turn_kernel_event_index=len(kernel.events)
        events = []
        def finish_failed_draw(error):
            """Close this incomplete turn with real observed loss provenance.

            No fake life damage, synthetic actions, or following opponent turns.
            The game remains an ordinary terminal outcome for the batch/UI.
            """
            if error.seat!=0:
                raise error  # This runner only drives seat-zero mandatory draws.
            events.append({
                "type":"mandatory_draw_empty_library",
                "seat":error.seat,"source_object_id":error.source_id,
                "attempted_draws":error.attempted,
                "available_cards":error.available,
                "phase":error.phase,
                "fidelity":"bounded_verified_game_loss"})
            round_life=outcome_recorder.record_round(
                turn,life.kernel.life_changes[life_ledger_start:],
                dict(life.kernel.life_totals))
            outcome_recorder.record_game_loss(
                turn,0,reason="empty_library_draw",
                source_object_id=error.source_id)
            state=project_kernel_turn(zones,0,turn,catalog)
            states.append(state)
            resource=assess_resources(kernel,mana_service,0).__dict__
            actions_by_turn.append({
                "turn":turn,"events":events,
                "hand_size":len(zones.ids(0,"hand")),
                "hand_size_before_cleanup":len(zones.ids(0,"hand")),
                "maximum_hand_size":None,"cleanup_discard_count":0,
                "library_size":len(zones.ids(0,"library")),
                "command_zone_count":len(zones.ids(0,"command")),
                "land_count":sum("land" in o.types and o.zone=="battlefield"
                                  for o in kernel.objects.values()),
                "creature_count":sum("creature" in o.types and
                                     o.zone=="battlefield" and o.controller==0
                                     for o in kernel.objects.values()),
                "mana_rock_count":0,
                "floating_at_end_of_main":list(mana_service.floating()),
                "resource_start":resource,"resource_after_precast":resource,
                "resource_end":resource,
                "mana_payment_events":list(mana_service.mana_events[mana_ledger_start:]),
                "life_totals":dict(life.kernel.life_totals),
                "pilot_combat":None,"pilot_decisions":[],
                "life_totals_start":dict(outcome_recorder.history[-2]["life_totals"]),
                "life_changes":list(round_life["life_changes"]),
                "eliminations":list(outcome_recorder.history[-1]["new_eliminations"]),
                "alive_seats":list(outcome_recorder.history[-1]["alive_seats"]),
                "unsupported_cards_in_hand":[],
                "terminal_phase":error.phase})
        def append_reanimation_entry_chain(ids):
            if not ids:
                return
            for oid in ids:
                obj=kernel.objects.get(oid)
                if obj is not None and obj.zone=="battlefield":
                    entered_on_turn[oid]=turn
            chain=resolve_reviewed_entry_chain(
                zones,life,ids,raw_by_name,
                death_engine=death_engine,turn=turn,max_triggers=12)
            for entry in chain.resolved:
                for revived in entry.reanimated_ids:
                    entered_on_turn[revived]=turn
                events.append({
                    "type":"reviewed_reanimation_enter_resolved",
                    "card":entry.source_name,"source_object_id":entry.source_id,
                    "ability_operation":entry.operation,
                    "created_token_ids":list(entry.token_ids),
                    "drawn_ids":list(entry.drawn_ids),
                    "milled_ids":list(entry.milled_ids),
                    "reanimated_ids":list(entry.reanimated_ids),
                    "exiled_ids":list(entry.exiled_ids),
                    "target_seat":entry.target_seat,
                    "library_actions":list(entry.library_steps),
                    "fidelity":"bounded_reviewed_etb_queue_no_priority"})
            if chain.deferred_ids:
                events.append({
                    "type":"reviewed_entry_chain_deferred",
                    "source_object_ids":list(chain.deferred_ids),
                    "reason":"finite_reviewed_trigger_budget",
                    "fidelity":"bounded_incomplete"})

        beginning_creature_ids=frozenset(
            obj.object_id for obj in kernel.on_battlefield()
            if obj.controller==0 and "creature" in obj.types)
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
        def respond_to_removal(target_id,opponent_seat,pressure_turn,kind):
            # Reviewed instant response, not a full priority stack.
            # Save a meaningful nontoken creature only against destruction.
            if kind!="destroy" or target_id not in kernel.objects:
                return
            target=kernel.get(target_id)
            if (target.controller!=0 or target.token
                    or "creature" not in target.types or
                    (target.power+target.toughness<4
                     and "commander" not in target.card.supertypes)):
                return
            # Prefer reusable zero-mana protection of this exact source
            # to spending a hand card; the sacrificed creature is a real cost.
            rule=reviewed_activation(target.card.name,
                                     raw_by_name.get(target.card.name))
            if rule is not None and rule.operation=="keyword_self_until_end":
                victims=[o for o in kernel.on_battlefield()
                         if o.controller==0 and o.object_id!=target_id
                         and "creature" in o.types]
                if victims:
                    victim=min(victims,key=lambda o:(
                        0 if o.token else 1,
                        o.power+o.toughness,o.object_id))
                    saved=activate_reviewed(
                        zones,life,mana_service,death_engine,raw_by_name,
                        target_id,sacrifice_id=victim.object_id,
                        turn=pressure_turn)
                    if saved is not None:
                        events.append({"type":"reviewed_activated_response",
                            "source_object_id":target_id,
                            "sacrificed_object_id":victim.object_id,
                            "operation":saved.operation,
                            "against_seat":opponent_seat})
                        return
            for spell_id in tuple(zones.ids(0,"hand")):
                spell=kernel.get(spell_id)
                review=reviewed_zone_spell(
                    spell.card.name,raw_by_name.get(spell.card.name))
                if review is None or review.operation!="return_when_dies":
                    continue
                outcome=zone_engine.cast(
                    0,spell_id,target_id,turn=pressure_turn,
                    on_cast=lambda ticket:events.extend(
                        approved_spell_triggers(ticket)),
                    expires_at_seat=opponent_seat)
                if outcome is not None:
                    events.append({
                        "type":"reviewed_instant_response",
                        "card":outcome.name,
                        "target_object_id":target_id,
                        "against_seat":opponent_seat,
                        "fidelity":"bounded_single_response_window"})
                    break
        if opponent_pressure is not None:
            opponent_pressure.before_removal=respond_to_removal
        def approved_spell_triggers(ticket):
            """Execute only vetted cast triggers after an actual source cast."""
            source = kernel.get(ticket.object_id)
            reactions=resolve_cast_reactions(
                zones,0,raw_by_name,source_spell=source)
            nonhand = resolve_reviewed_nonhand_cast_triggers(
                zones, 0, ticket, raw_by_name)
            effects = resolve_reviewed_spell_triggers(
                zones, 0, raw_by_name, event="spell_cast",
                spell_types=frozenset(source.types))
            return [{"type":"reviewed_cast_reaction",
                     "source_object_id":reaction.source_id,
                     "operation":reaction.operation,
                     "quantity":reaction.quantity,
                     "fidelity":"bounded_verified_cast"}
                    for reaction in reactions] + [{"type":"reviewed_trigger_resolved",
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
        # Upkeep sacrifice costs and continuous statics operate on the same
        # physical sources before optional later phase triggers resolve.
        attachment_engine.sync(turn=turn)
        for paid_upkeep in attachment_engine.upkeep(0,turn=turn):
            events.append({"type":"reviewed_attachment_upkeep",
                           "operation":paid_upkeep.operation,
                           "source_object_id":paid_upkeep.source_id,
                           "target_object_id":paid_upkeep.target_id})
        # Upkeep happens after untap but before the ordinary draw.
        try:
            upkeep_triggers=phase_engine.resolve(
                phase="upkeep",active_seat=0,round_id=turn)
        except EmptyLibraryDraw as error:
            finish_failed_draw(error)
            break
        for triggered in upkeep_triggers:
            events.append({
                "type":"reviewed_phase_resolved","phase":"upkeep",
                "source":triggered.source_name,"source_object_id":triggered.source_id,
                "ability_slot":triggered.slot_id,
                "created_token_ids":list(triggered.created_token_ids),
                "drawn_ids":list(triggered.drawn_ids),
                "returned_object_id":triggered.returned_id,
                "fidelity":"bounded_no_opponent_priority"})
        for composed in composed_engine.upkeep(active_seat=0,turn=turn):
            events.append({
                "type":"reviewed_composed_upkeep",
                "source_object_id":composed.source_id,
                "operation":composed.operation,
                "created_token_ids":list(composed.created_ids),
                "life_lost":composed.life_lost,
                "death_trigger_count":composed.deaths,
                "fidelity":"bounded_composed_upkeep"})
        resolve_reactive()
        drawn, okay = zones.draw(0, 1)  # Seat is explicitly not the starting seat.
        if not okay:
            finish_failed_draw(EmptyLibraryDraw(
                0,attempted=1,available=0,phase="draw_step"))
            break
        events.append({"type": "draw", "card": kernel.get(drawn[0]).card.name,
                       "object_id": drawn[0]})
        playable_lands = [oid for oid in zones.ids(0, "hand") if supported_land(oid)]
        other_lands_now=sum("land" in obj.types and obj.zone=="battlefield"
                            and obj.controller==0 for obj in kernel.objects.values())
        playable_lands.sort(key=lambda oid: (
            bool(reviewed_land(kernel.get(oid).card.name,
                               raw_by_name[kernel.get(oid).card.name],colors)
                 and reviewed_land(kernel.get(oid).card.name,
                                   raw_by_name[kernel.get(oid).card.name],colors).enters_tapped(other_lands_now))
            or kernel.get(oid).card.name=="Myriad Landscape",
            oid))
        if playable_lands:
            land_id = playable_lands[0]
            name = kernel.get(land_id).card.name
            other_lands=sum("land" in obj.types and obj.zone=="battlefield"
                            and obj.controller==0 for obj in kernel.objects.values())
            land_review=reviewed_land(name,raw_by_name[name],colors)
            provisional_land=provisional_by_name.get(name)
            provisional_land=(provisional_land
                              if provisional_land is not None
                              and provisional_land.kind=="land_mana" else None)
            new_id = zones.play_land(0, land_id)
            if ((land_review is not None and land_review.enters_tapped(other_lands))
                    or (provisional_land is not None and provisional_land.enter_tapped)
                    or (name == 'Myriad Landscape' and reviewed_ramp(name,raw_by_name[name]) is not None)):
                kernel.get(new_id).tapped=True
                kernel._dirty()
            events.append({"type": "land_play", "card": name,
                           "from_object_id": land_id, "object_id": new_id,
                           "fidelity":"reviewed_partial_land" if land_review else
                                "provisional_partial" if provisional_land else
                                "reviewed_basic_land",
                           "entered_tapped":bool(kernel.get(new_id).tapped),
                           "unsupported_abilities":list(land_review.ignored) if land_review else
                               list(provisional_land.omissions) if provisional_land else []})
            entry_rule=reviewed_land_entry(name,raw_by_name[name])
            if entry_rule is not None:
                recycle=None
                if entry_rule.operation=="graveyard_creature_to_library_top":
                    choices=[oid for oid in zones.ids(0,"graveyard")
                             if "creature" in kernel.get(oid).types]
                    usable=[oid for oid in choices if reviewed_creature(
                        deck_key,kernel.get(oid).card.name,
                        raw_by_name[kernel.get(oid).card.name])]
                    if usable:
                        recycle=max(usable,key=lambda oid: (
                            raw_by_name[kernel.get(oid).card.name].get("cmc",0),-oid))
                etb=resolve_land_entry(zones,life,new_id,raw_by_name,
                                       target_creature_id=recycle)
                events.append({"type":"reviewed_land_entry",
                               "card":name,"operation":etb.operation,
                               "moved_ids":list(etb.moved_ids),
                               "library_actions":list(etb.library_steps),
                               "fidelity":"bounded_shared_land_entry"})
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
        pilot_decisions=[]
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
                preview=preview_spell(0,cost,cmd)
                if preview is not None:
                    options.append((1,len(preview.source_ids),cmd.card.name,
                                    commander_id,"commander",cost,None))
            for oid in zones.ids(0, "hand"):
                obj = kernel.get(oid)
                name = obj.card.name
                raw = raw_by_name[name]
                provisional=provisional_by_name.get(name)
                is_creature = bool(reviewed_creature(deck_key, name, raw)
                                   or (provisional is not None and
                                       provisional.kind=="creature_body"))
                rock = reviewed_rock(name, raw, colors)
                provisional_rock=bool(provisional is not None
                                      and provisional.kind in {"artifact_mana",
                                                               "artifact_body"})
                provisional_spell=bool(provisional is not None and
                    provisional.kind=="simple_spell"
                    and reviewed_common_spell(name,raw) is None
                    and reviewed_draw_spell(name,raw) is None)
                if (provisional is not None
                        and provisional.kind=="creature_body"
                        and provisional.entry_actions
                        and len(zones.ids(0,"library")) <
                            required_library_cards_for_draws(provisional.entry_actions)):
                    # Mill-only ETBs are legal with an empty library. Reject
                    # only when a later mandatory draw cannot be completed
                    # in the bounded no-library-loss host.
                    continue
                if provisional_spell:
                    # A speculative preview cannot commit a draw from an
                    # empty library or a source-paid spell that kills its
                    # own controller. Filter before the spell is chosen.
                    draw_need = (required_library_cards_for_draws(provisional.library_actions)
                                 if provisional.library_actions else
                                 provisional.amount if provisional.mode in {"draw","draw_lose"}
                                 else 0)
                    if len(zones.ids(0,"library")) < draw_need:
                        continue
                    if (provisional.life_amount
                            and life.total(0)<=provisional.life_amount):
                        continue
                token_spell = reviewed_token_spell(name, raw)
                draw_spell = reviewed_draw_spell(name,raw)
                attachment_rule=reviewed_attachment(name,raw)
                aura_target=None
                if attachment_rule is not None and attachment_rule.scope=="opponent_aura":
                    enemy_targets=[o for o in kernel.on_battlefield()
                                   if o.controller!=0 and "creature" in o.types
                                   and kernel.legal_target(
                                       0,o.object_id,frozenset({"creature"}))]
                    if enemy_targets:
                        aura_target=max(enemy_targets,
                                        key=lambda o:(o.power,o.toughness,-o.object_id)).object_id
                    else:
                        continue
                phase_enchantment = ((reviewed_activation(name,raw) is not None
                                     and "enchantment" in obj.types)
                                     or reviewed_phase_permanent(name, raw)
                                     or reviewed_breach(name, raw)
                                     or reviewed_composed_permanent(name,raw)
                or reviewed_attachment(name,raw) is not None
                or reviewed_zone_spell(name,raw) is not None
                or reviewed_activation(name,raw) is not None
                                     or (reviewed_utility(name,raw) is not None
                                         and reviewed_utility(name,raw).source_zone=="battlefield"
                                         and "enchantment" in obj.types))
                sacrifice_artifact = reviewed_sacrifice_artifact(name, raw)
                entering = approved_enter_hand_cast(name)
                if entering:
                    reviewed_entry=reviewed_enter_rule(name,raw)
                    required=required_library_cards_for_draws(
                        reviewed_entry.library_actions)
                    if required>len(zones.ids(0,"library")):
                        continue
                ramp = reviewed_ramp(name,raw) if "land" not in obj.types else None
                ritual = reviewed_ritual(name,raw)
                common = reviewed_common_spell(name,raw)
                removal = reviewed_removal(name,raw)
                zone_rule=reviewed_zone_spell(name,raw)
                gy_rule=reviewed_graveyard_spell(name,raw)
                gy_targets=(choose_graveyard_spell_targets(
                    zones,0,gy_rule,raw_by_name) if gy_rule is not None else ())
                gy_victim=None
                if gy_rule is not None and gy_rule.sacrifice_creature:
                    candidates=[o for o in kernel.on_battlefield()
                        if o.controller==0 and "creature" in o.types
                        and "commander" not in o.card.supertypes]
                    if candidates:
                        gy_victim=min(candidates,key=lambda o:(
                            not o.token,o.power,o.object_id)).object_id
                gy_ready=(gy_rule is not None and
                    len(gy_targets)==gy_rule.target_count
                    and (not gy_rule.sacrifice_creature or gy_victim is not None)
                    and (not gy_rule.conditional_draw_subtype
                         or not any(gy_rule.conditional_draw_subtype in
                             kernel.get(i).subtypes for i in gy_targets)
                         or bool(zones.ids(0,"library"))))
                zone_target=None
                if zone_rule is not None:
                    if zone_rule.operation=="opponent_graveyard_theft":
                        valid_targets=[o for o in kernel.objects.values()
                                       if zone_engine.valid_target(
                                           0,zone_rule,o.object_id)]
                        if valid_targets:
                            best=max(valid_targets,
                                key=lambda o:(o.power+o.toughness,-o.object_id))
                            zone_target=best.object_id
                    # Protective instants are reserved for real destroy
                    # responses rather than spent fruitlessly in main phase.
                removal_plan = (choose_reviewed_removal(
                    zones,0,life,removal,turn=turn) if removal is not None else None)
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
                        and not common_plan and removal_plan is None
                        and attachment_rule is None and zone_target is None and not gy_ready
                        and not provisional_rock and not provisional_spell):
                    continue
                cost = common_plan[0] if common_plan else registry.get(name).primary_face().mana_cost
                payment = preview_spell(0, cost, obj)
                if payment is not None:
                    kind = ("zone_spell" if zone_target is not None else
                            "graveyard_spell" if gy_ready else
                            "provisional_spell" if provisional_spell else
                            "removal_spell" if removal_plan is not None else
                            "common_spell" if common_plan else
                            "ritual" if ritual else
                            "artifact" if rock is not None or provisional_rock or sacrifice_artifact or (attachment_rule is not None and "artifact" in obj.types) or (ramp and name == "Wayfarer\u0027s Bauble") else
                            "enchantment" if "enchantment" in obj.types and (phase_enchantment or attachment_rule is not None or entering) else
                            "tutor" if eligible else
                            "draw_spell" if draw_spell is not None else
                            "token_spell" if token_spell is not None else "creature")
                    # A source-verified card may have a reviewed ability
                    # while still lacking an executable spell-resolution path.
                    # Never treat an instant as an ordinary creature cast.
                    if (kind in {"artifact","creature","enchantment"}
                            and kind not in obj.types):
                        continue
                    target = (zone_target if zone_target is not None else
                              (gy_targets,gy_victim) if gy_ready else
                              aura_target if aura_target is not None else
                              removal_plan if removal_plan is not None else
                              common_plan[1:] if common_plan else
                              choose_tutor_target(zones, 0, eligible, raw_by_name, colors) if eligible else None)
                    # Reviewed trigger creatures precede spells so their
                    # shared effects may fire on subsequent actual casts.
                    options.append((0 if rock is not None or (provisional is not None and provisional.kind=="artifact_mana") or ritual else
                                    1 if is_creature else
                                    2 if removal_plan is not None and life.total(0)<=18 else
                                    2 if sacrifice_artifact else
                                    3 if phase_enchantment or entering else
                                    4 if eligible else 5,
                                    len(payment.source_ids), name, oid, kind, cost, target))
            if not options:
                break
            context=PilotContext(
                round=turn,life=life.total(0),
                hand_size=len(zones.ids(0,"hand")),
                lands=sum("land" in obj.types and obj.controller==0
                          for obj in kernel.on_battlefield()),
                mana_sources=assess_resources(kernel,mana_service,0).available_fixed_mana,
                graveyard_creatures=sum("creature" in kernel.get(gy).types
                    for gy in zones.ids(0,"graveyard")),
                friendly_creatures=sum("creature" in obj.types and obj.controller==0
                    for obj in kernel.on_battlefield()),
                opposing_creatures=sum("creature" in obj.types and obj.controller!=0
                    and life.total(obj.controller)>0
                    for obj in kernel.on_battlefield()))
            selected,rank=choose_legal_option(
                options,context,pilot_signals,raw_by_name,style=pilot_style,
                archetype=pilot_strategy.primary)
            _, _, name, oid, kind, cost, target = selected
            pilot_decisions.append({
                "round":turn,"kind":kind,"card":name,
                "source_object_id":oid,"candidate_count":len(options),
                "score":rank.score,"role":rank.category,
                "factors":list(rank.factors),"personality":pilot_style,
                "archetype":pilot_strategy.primary,
                "fidelity":"ordering_only_verified_legal_candidates"})
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
            if kind == "provisional_spell":
                triggered=[]
                outcome=cast_provisional_spell(
                    zones,life,0,oid,raw_by_name,colors,mana_service,
                    on_cast=lambda ticket:triggered.extend(
                        approved_spell_triggers(ticket)))
                if outcome is None:
                    raise AssertionError("Provisional spell became unpayable")
                events.extend(triggered)
                events.append({
                    "type":"provisional_spell_resolved",
                    "card":outcome.name,
                    "operation":outcome.operation,
                    "amount":outcome.count,
                    "drawn_ids":list(outcome.drawn_ids),
                    "created_token_ids":list(outcome.created_token_ids),
                    "library_actions":list(outcome.library_steps),
                    "discarded_ids":list(outcome.discarded_ids),
                    "surveilled_ids":list(outcome.surveilled_ids),
                    "paid_source_ids":list(outcome.paid_source_ids),
                    "graveyard_object_id":outcome.resolved_zone_id,
                    "fidelity":"provisional_partial"})
                continue
            if kind == "graveyard_spell":
                selected,sacrifice_id=target
                triggered=[]
                resolved=cast_reviewed_graveyard_spell(
                    zones,life,0,oid,raw_by_name,colors,mana_service,
                    target_ids=selected,sacrifice_id=sacrifice_id,
                    death_engine=death_engine,turn=turn,
                    on_cast=lambda ticket:triggered.extend(
                        approved_spell_triggers(ticket)))
                if resolved is None:
                    raise AssertionError("Reviewed graveyard spell became unavailable")
                events.extend(triggered)
                events.append({"type":"reviewed_graveyard_spell_cast",
                    "card":name,"stack_object_id":resolved.source_stack_id,
                    "paid_source_ids":list(resolved.paid_source_ids),
                    "fidelity":"bounded_reviewed_graveyard_spell"})
                events.append({"type":"reviewed_graveyard_spell_resolved",
                    "card":name,"source_object_id":resolved.source_resolved_id,
                    "target_ids":list(resolved.target_ids),
                    "moved_ids":list(resolved.moved_ids),
                    "sacrificed_old_id":resolved.sacrificed_old_id,
                    "drawn_ids":list(resolved.drawn_ids),
                    "unsupported_abilities":list(resolved.limitations),
                    "fidelity":"bounded_reviewed_graveyard_spell"})
                append_reanimation_entry_chain(resolved.moved_ids)
                continue
            if kind == "zone_spell":
                returned=zone_engine.cast(
                    0,oid,target,turn=turn,
                    on_cast=lambda ticket:events.extend(
                        approved_spell_triggers(ticket)))
                if returned is None:
                    raise AssertionError("Reviewed zone spell payment changed")
                events.append({
                    "type":"reviewed_zone_spell_resolved",
                    "card":returned.name,"operation":returned.operation,
                    "target_object_id":returned.target_id,
                    "moved_ids":list(returned.moved_ids),
                    "fidelity":"bounded_reviewed_zone_spell"})
                append_reanimation_entry_chain(returned.moved_ids)
                continue
            if kind == "removal_spell":
                target_id,x=target
                triggered=[]
                outcome=cast_removal(
                    zones,life,0,oid,raw_by_name,colors,mana_service,
                    target_id=target_id,x=x,death_engine=death_engine,
                    turn=turn,
                    on_cast=lambda ticket:triggered.extend(
                        approved_spell_triggers(ticket)))
                if outcome is None:
                    raise AssertionError("Reviewed removal payment changed")
                events.extend(triggered)
                events.append({
                    "type":"reviewed_removal_resolved",
                    "card":outcome.card_name,
                    "target_object_id":target_id,
                    "x_life_paid":outcome.x_life_paid,
                    "affected_object_ids":list(outcome.affected_ids),
                    "destroyed_count":outcome.destroyed_count,
                    "fidelity":"bounded_reviewed_removal_no_priority"})
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
                               "created_token_ids":list(result.created_token_ids),
                               "library_actions":list(result.library_steps),
                               "discarded_ids":list(result.discarded_ids),
                               "surveilled_ids":list(result.surveilled_ids),
                               "bottomed_ids":list(result.bottomed_ids),
                               "returned_ids":list(result.returned_ids),
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
                        afford_buyback=(preview_spell(
                            0,extra,copy_obj) is not None)
                        if (not afford_buyback and preview_spell(
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
            try:
                committed = cast_reviewed_permanent(
                    zones, 0, oid, review, colors, mana_service=mana_service,
                    permanent_type=kind)
            except ValueError as error:
                if str(error)=="Not an approved reviewed permanent":
                    raise AssertionError(
                        "Reviewed cast kind or admission mismatch: "
                        +repr((name,kind,tuple(kernel.get(oid).types),
                               kernel.get(oid).card.coverage))) from error
                raise
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
            selected_attachment=reviewed_attachment(name,raw_by_name[name])
            if kind=="enchantment" and selected_attachment is not None and selected_attachment.scope=="opponent_aura":
                attached=attachment_engine.bind(
                    resolved_id,target,sorcery_window=True,already_paid=True)
                if attached is None:
                    raise AssertionError("Aura target ceased being legal before entry")
                events.append({"type":"reviewed_aura_attached",
                               "source_object_id":resolved_id,
                               "target_object_id":target})
            entry_choice=reviewed_entry_choice(name,raw_by_name[name])
            if entry_choice is not None:
                # A legal explicit player choice made as the reviewed source
                # enters. Targeting policy is provisional, rules operation
                # remains general and can accept any seat chosen by host.
                target_seat=next(seat for seat in sorted(life.kernel.life_totals)
                                 if seat!=0)
                set_reviewed_entry_choice(
                    zones,resolved_id,raw_by_name,player=target_seat)
                events.append({
                    "type":"reviewed_as_enters_player_choice",
                    "source_object_id":resolved_id,
                    "chosen_player":target_seat,
                    "fidelity":"bounded_explicit_entry_choice"})
            if kind == "artifact":
                rock = reviewed_rock(name, raw_by_name[name], colors)
                provisional_artifact=provisional_by_name.get(name)
                if ((rock is not None and rock[0].enter_tapped) or
                        (provisional_artifact is not None and
                         provisional_artifact.enter_tapped)):
                    kernel.get(resolved_id).tapped = True
                    kernel._dirty()
            implicit=provisional_by_name.get(name)
            implicit_only=(implicit is not None and
                          not reviewed_creature(deck_key,name,raw_by_name[name])
                          and reviewed_rock(name,raw_by_name[name],colors) is None
                          and not approved_enter_hand_cast(name))
            events.append({"type": kind + "_resolved", "card": name,
                           "object_id": resolved_id,
                           "fidelity":"provisional_partial" if implicit_only else
                                      "limited_generic_resolution",
                           "unmodeled_abilities":list(implicit.omissions)
                               if implicit_only else []})
            if (kind=="creature" and implicit_only
                    and implicit.entry_actions):
                entry=resolve_library_actions(zones,0,implicit.entry_actions)
                events.append({"type":"provisional_enter_resolved",
                    "card":name,"source_object_id":resolved_id,
                    "milled_ids":list(entry.milled_ids),
                    "drawn_ids":list(entry.drawn_ids),
                    "discarded_ids":list(entry.discarded_ids),
                    "library_actions":list(entry.steps),
                    "fidelity":"provisional_partial"})
            if name == "Solemn Simulacrum" and reviewed_ramp(name,raw_by_name[name]):
                moved = resolve_enter_ramp(zones,0,resolved_id,raw_by_name)
                events.append({"type":"reviewed_enter_ramp","card":name,
                               "land_ids":list(moved or ()),"fidelity":"reviewed_shared_basic_search"})
            if approved_enter_hand_cast(name) and not reviewed_enter_rule(name,raw_by_name[name]).only_from_graveyard:
                rule = reviewed_enter_rule(name, raw_by_name[name])
                # Shared policy chooses among reviewed legal ETB options.
                choice = bounded_entry_choice(rule,kernel.get(resolved_id),zones,life)
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
                               "milled_ids":list(entered.milled_ids),
                               "library_actions":list(entered.library_steps),
                               "reanimated_ids":list(entered.reanimated_ids),
                               "exiled_ids":list(entered.exiled_ids),
                               "target_seat":entered.target_seat,
                               "fidelity":"bounded_no_opponent_priority"})
                append_reanimation_entry_chain(entered.reanimated_ids)
        attachment_engine.sync(turn=turn)
        # Reviewed equipment is sorcery-speed and uses the same mana service
        # as any other activated permanent. The pilot chooses one good target.
        equip_choice=choose_attachment_use(
            zones,0,attachment_engine,mana_service,raw_by_name)
        if equip_choice is not None:
            source_id,target_id=equip_choice
            equipped=attachment_engine.bind(
                source_id,target_id,sorcery_window=True)
            if equipped is not None:
                events.append({"type":"reviewed_attachment_equipped",
                    "source_object_id":source_id,"target_object_id":target_id,
                    "paid_source_ids":list(equipped.paid_source_ids)})
        # Shared temporary resurrection uses the existing unearth-style
        # haste/exile replacement machinery, not shadow game objects.
        resurrection=choose_temporary_reanimation(
            zones,0,attachment_engine,mana_service,raw_by_name)
        if resurrection is not None:
            source_id,target_id=resurrection
            rec=attachment_engine.resurrect(
                source_id,target_id,turn=turn,sorcery_window=True)
            if rec is not None:
                events.append({"type":"reviewed_attachment_reanimated",
                    "source_object_id":source_id,"target_object_id":rec.target_id,
                    "paid_source_ids":list(rec.paid_source_ids)})
        # Shared ramp activation uses actual paid sources and shuffled basic lands.
        for source in list(kernel.on_battlefield()):
            if source.controller == 0 and source.card.name in {"Wayfarer's Bauble", "Myriad Landscape"}:
                moved = activate_land_ramp(zones, 0, source.object_id, raw_by_name, mana_service)
                if moved:
                    events.append({"type":"reviewed_land_ramp","card":source.card.name,
                                   "land_ids":list(moved),"fidelity":"reviewed_shared_basic_search"})
        # Generic paid utility abilities may convert spare mana into a real
        # creature recursion, a draw, or a legal black permanent drain.
        action=choose_utility_activation(
            zones,0,life,mana_service,raw_by_name,
            hand_cast_reviewed=lambda obj: reviewed_creature(
                deck_key,obj.card.name,raw_by_name[obj.card.name]),
            tap_ready=lambda source: (
                entered_on_turn.get(source.object_id,0)<turn
                or "haste" in source.keywords))
        if action is not None:
            source_id,target_id=action
            utility=activate_utility(zones,life,0,source_id,raw_by_name,
                mana_service,colors,target_id=target_id,
                death_engine=death_engine,turn=turn,
                tap_ready=(entered_on_turn.get(source_id,0)<turn
                           or "haste" in kernel.get(source_id).keywords))
            if utility is not None:
                events.append({"type":"reviewed_utility_activated",
                    "card":utility.source_name,
                    "operation":utility.operation,
                    "moved_ids":list(utility.new_object_ids),
                    "created_token_ids":list(utility.created_token_ids),
                    "tapped_cost_ids":list(utility.tapped_cost_ids),
                    "drawn_ids":list(utility.drawn_ids),
                    "paid_source_ids":list(utility.paid_source_ids),
                    "life_paid":utility.life_paid,
                    "life_lost_after":utility.life_lost_after,
                    "fidelity":"bounded_utility_policy"})
        # Generic composed-ability policy is separate from the rule executor.
        # A single conservative paid activation may generate useful life loss.
        x_activation=choose_composed_x_activation(
            zones,0,life,mana_service,raw_by_name)
        activation=(None if x_activation is not None else
                    choose_composed_activation(
                        zones,0,life,mana_service,raw_by_name))
        if x_activation is not None or activation is not None:
            source_id,x=x_activation if x_activation is not None else (activation,0)
            outcome=composed_engine.activate(source_id,turn=turn,x=x)
            if outcome is not None:
                events.append({"type":"reviewed_composed_activated",
                    "source_object_id":source_id,
                    "operation":outcome.operation,
                    "x":x,
                    "life_changes":outcome.life_lost,
                    "death_trigger_count":outcome.deaths,
                    "fidelity":"bounded_generic_activation_policy"})
        # One generic tap-based composed activation per turn when the
        # physical source entered on an earlier turn and its entry choice
        # was made. Do not activate a newly summoned creature without haste.
        for source in sorted(tuple(kernel.on_battlefield()),
                             key=lambda obj:obj.object_id):
            if source.controller!=0 or source.tapped:
                continue
            if entered_on_turn.get(source.object_id,0)>=turn and "haste" not in source.keywords:
                continue
            raw=raw_by_name.get(source.card.name,{})
            if raw.get("oracle_id")!=source.card.card_id:
                continue
            if (source.object_id not in getattr(kernel,"reviewed_player_choices",{})
                    or not any(
                        rule.event=="activate" and rule.payment.tap
                        and rule.oracle_excerpt in raw.get("oracle_text","")
                        for rule in ABILITIES.get(source.card.name,()))):
                continue
            activated=composed_engine.activate(
                source.object_id,turn=turn,tap_ready=True)
            if activated is not None:
                events.append({
                    "type":"reviewed_composed_tap_activation",
                    "source_object_id":source.object_id,
                    "operation":activated.operation,
                    "fidelity":"bounded_explicit_tap_ready"})
            break
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
                if preview_spell(0,with_buyback,obj) is not None:
                    buyback_options.append((obj.card.name,oid,True))
                elif preview_spell(0,rule.mana_cost,obj) is not None:
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
        # One optional sacrifice, scored against live reviewed death triggers.
        # Never sacrifice a useful body just because a free outlet exists.
        sacrifice_choice=choose_discretionary_sacrifice(
            zones,0,life,mana_service,raw_by_name,death_engine,
            turn=turn,entered_on_turn=entered_on_turn,
            archetype=pilot_strategy.primary)
        if sacrifice_choice is not None:
            source=kernel.get(sacrifice_choice.source_id)
            mode=SACRIFICE_MODES[source.card.name]
            resolved=activate_reviewed_sacrifice(
                zones,life,sacrifice_choice.source_id,
                sacrifice_choice.victim_id,raw_by_name,
                mana_service=mana_service,turn=turn,
                tap_ready=(not source.tapped and (
                    "creature" not in source.types
                    or entered_on_turn.get(source.object_id,0)<turn
                    or "haste" in source.keywords)),
                death_engine=death_engine,scry_to_bottom=False)
            if resolved is None:
                raise AssertionError("Reviewed sacrifice choice became unavailable")
            events.append({
                "type":"reviewed_sacrifice_activated","card":resolved.source_name,
                "source_object_id":resolved.source_id,
                "victim_object_id":resolved.victim_old_id,
                "ability_operation":resolved.operation,
                "created_token_ids":list(resolved.token_ids),
                "drawn_ids":list(resolved.drawn_ids),
                "mana_added":list(resolved.mana_added),
                "death_trigger_count":resolved.death_trigger_count,
                "fidelity":"bounded_reviewed_effect_scored"})
            pilot_decisions.append({
                "round":turn,"kind":"sacrifice","card":resolved.source_name,
                "source_object_id":resolved.source_id,
                "victim_object_id":resolved.victim_old_id,
                "candidate_count":1,"score":sacrifice_choice.score,
                "role":"sacrifice",
                "factors":list(sacrifice_choice.factors),
                "personality":pilot_style,
                "archetype":pilot_strategy.primary,
                "fidelity":"reviewed_activated_sacrifice_choice"})
            resolve_reactive()
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
                    and preview_spell(
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
            if review and preview_spell(0,review.alternate_cost,spell) is not None:
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
        # Use remaining resources for one sensible generic utility effect
        # before combat. These are authorized typed effect descriptors, not
        # specific card scripts. Defend life before paying costly activations.
        for source in sorted(tuple(kernel.on_battlefield()),
                             key=lambda o:o.object_id):
            rule=reviewed_activation(
                source.card.name,raw_by_name.get(source.card.name))
            if source.controller!=0 or rule is None:
                continue
            choice={}
            if rule.operation=="counter_target":
                enemy_power=max((o.power for o in kernel.on_battlefield()
                    if o.controller!=0 and "creature" in o.types),default=0)
                candidates=[o for o in kernel.on_battlefield()
                    if o.controller==0 and "creature" in o.types
                    and not o.token and o.toughness<=enemy_power
                    and o.power+o.toughness>=5]
                if life.total(0)<=20 or not candidates:
                    continue
                best=max(candidates,key=lambda o:(
                    int("commander" in o.card.supertypes),
                    o.power+o.toughness,-o.object_id))
                choice["target_id"]=best.object_id
            elif rule.operation=="mill_all":
                if (not opponent_pressure or turn<4
                        or not any(zones.ids(seat,"library")
                                   for seat in (1,2,3))):
                    continue
            elif rule.operation=="keyword_own_until_end":
                if (opponent_pressure is None or life.total(0)>33
                        or sum(o.controller==0 and "creature" in o.types
                               for o in kernel.on_battlefield())<2):
                    continue
            else:
                continue
            outcome=activate_reviewed(
                zones,life,mana_service,death_engine,raw_by_name,
                source.object_id,turn=turn,**choice)
            if outcome is not None:
                events.append({"type":"reviewed_generic_activated",
                               "source_object_id":source.object_id,
                               "operation":outcome.operation,
                               "affected_ids":list(outcome.affected_ids),
                               "life_paid":outcome.life_paid})
                resolve_reactive()
        # Physical pilot attacks once with a conservative board-aware policy.
        # Opposing seats are sampled using the same threat weights as their
        # attacks on one another; no privileged target at seat zero.
        if opponent_pressure is not None:
            for combat in opponent_pressure.player_combat(
                    turn,beginning_creature_ids=beginning_creature_ids,
                    style=pilot_style,signals=pilot_signals):
                events.append({
                    "type":"player_"+combat.operation,
                    "object_id":combat.object_id,
                    "target_seat":combat.target_seat,
                    "amount":combat.amount,
                    "fidelity":"bounded_physical_combat"})
            attachment_engine.sync(turn=turn)
            resolve_reactive()
        death_count=sum(ev.name=="dies" for ev in
                        kernel.events[turn_kernel_event_index:])
        # Resolve approved composed end-step abilities. The bounded pilot
        # supplies no optional X choice; it does not invent a strategy.
        # The beginning-of-end-step trigger is already on the stack. In a
        # reviewed priority window, convert expendable creature tokens to
        # mana only when that increases the legal X payoff by more than the
        # single token spent. No cross-phase mana carryover is assumed.
        for _ in range(3):
            choice=choose_end_step_token_mana(
                zones,0,life,mana_service,raw_by_name,
                life_start_index=life_ledger_start)
            if choice is None:
                break
            source_id,victim_id=choice
            source=kernel.get(source_id)
            mode=SACRIFICE_MODES[source.card.name]
            sacrificed=activate_reviewed_sacrifice(
                zones,life,source_id,victim_id,raw_by_name,
                mana_service=mana_service,turn=turn,tap_ready=True,
                death_engine=death_engine,
                mana_color="B" if mode.action=="any_color_mana" else None)
            if sacrificed is None:
                break
            events.append({"type":"reviewed_end_step_mana_sacrifice",
                           "card":sacrificed.source_name,
                           "victim_object_id":sacrificed.victim_old_id,
                           "mana_added":list(sacrificed.mana_added),
                           "fidelity":"bounded_x_payoff"})
            resolve_reactive()
        chosen_x=choose_variable_end_step_payments(
            zones,0,life,mana_service,raw_by_name,life_ledger_start)
        for composed in composed_engine.end_step(
                active_seat=0, turn=turn, life_start_index=life_ledger_start,
                x_choices=chosen_x):
            events.append({
                "type":"reviewed_composed_end_step",
                "source_object_id":composed.source_id,
                "effect":composed.operation,
                "created_token_ids":list(composed.created_ids),
                "death_trigger_count":composed.deaths,
                "fidelity":"bounded_no_opponent_priority"})
        try:
            end_step_triggers=phase_engine.resolve(
                phase="end_step",active_seat=0,round_id=turn,
                death_count=death_count)
        except EmptyLibraryDraw as error:
            finish_failed_draw(error)
            break
        for triggered in end_step_triggers:
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
                payment=preview_spell(0,printed,obj)
            except (NotImplementedError,UnsupportedManaCost):
                continue
            except ValueError as error:
                # This is a *diagnostic-only* preview for an unsupported
                # spell, not a legal action. The bounded mana planner may
                # exhaust its search budget in high-resource board states.
                # Preserve the game and report uncertainty; never classify
                # the spell as castable or silently swallow unrelated errors.
                if str(error)!="Bounded mana search exhausted; no action committed":
                    raise
                events.append({
                    "type":"unsupported_mana_preview_exhausted",
                    "card":name,"object_id":oid,
                    "effect_status":"unsupported",
                    "fidelity":"payment_preview_inconclusive"})
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
        attachment_engine.sync(turn=turn)
        zone_engine.expire(turn,active_seat=0)
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
                or reviewed_utility(name,raw) is not None
                or reviewed_sacrifice_artifact(name, raw)
                or reviewed_ramp(name,raw) is not None
                or reviewed_ritual(name,raw)
                or reviewed_common_spell(name,raw) is not None
                or reviewed_removal(name,raw) is not None
                or reviewed_zone_spell(name,raw) is not None
                or reviewed_graveyard_spell(name,raw) is not None
                or reviewed_attachment(name,raw) is not None
                or reviewed_activation(name,raw) is not None
                or approved_enter_hand_cast(name)
                or reviewed_breach(name,raw)
                or reviewed_buyback(name,raw) is not None
                or reviewed_copy_spell(name,raw) is not None
                or provisional_by_name.get(name) is not None)
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
        # End-of-turn damage and temporary modifiers must not leak into the
        # next player's turn. This uses the kernel's existing cleanup/SBAs.
        kernel.cleanup()
        floating_end = list(mana_service.floating())
        resource_end = assess_resources(kernel, mana_service, 0).__dict__
        mana_service.clear()
        if (not zones.assert_consistent()
                or sum(not obj.token and obj.owner==0
                       for obj in kernel.objects.values()) != 100):
            raise AssertionError("Physical non-token card conservation failed")
        if opponent_pressure is not None:
            for pressure_event in opponent_pressure.advance(turn):
                events.append({
                    "type":"opponent_"+pressure_event.operation,
                    "seat":pressure_event.seat,
                    "role":pressure_event.role,
                    "amount":pressure_event.amount,
                    "object_id":pressure_event.object_id,
                    "target_seat":pressure_event.target_seat,
                    "fidelity":"abstract_opponent_pressure_not_card_exact"})
            resolve_reactive()
        # An opponent's explicitly abstract non-token creature can be
        # controlled by Mortarion after Nurgle's Conscription. It is not in
        # the pinned Mortarion catalog; identify its simulated provenance
        # separately instead of inventing a real card name or rules profile.
        if opponent_pressure is not None:
            for foreign in kernel.on_battlefield():
                if (foreign.controller==0 and foreign.owner!=0
                        and foreign.card.card_id.startswith("stress:")):
                    catalog.setdefault(foreign.card.name,{
                        "type_line":"Creature",
                        "keywords":list(foreign.keywords),
                        "fidelity":"abstract_opponent_card"})
        round_life=outcome_recorder.record_round(
            turn,life.kernel.life_changes[life_ledger_start:],
            dict(life.kernel.life_totals))
        state = project_kernel_turn(zones, 0, turn, catalog)
        states.append(state)
        actions_by_turn.append({
            "turn": turn, "events": events, "hand_size": len(zones.ids(0, "hand")),
            "hand_size_before_cleanup": cleanup.hand_before,
            "maximum_hand_size": cleanup.maximum_hand_size,
            "cleanup_discard_count": len(cleanup.discarded),
            "library_size": len(zones.ids(0, "library")),
            "command_zone_count": len(zones.ids(0, "command")),
            "land_count": sum("land" in o.types and o.zone == "battlefield"
                              for o in kernel.objects.values()),
            "creature_count": sum("creature" in o.types and o.zone == "battlefield" and o.controller==0
                                  for o in kernel.objects.values()),
            "mana_rock_count": sum("artifact" in o.types and o.zone == "battlefield"
                                  and not o.token and o.card.name in raw_by_name
                                  and (reviewed_rock(o.card.name, raw_by_name[o.card.name], colors) is not None
                                       or (provisional_by_name.get(o.card.name) is not None
                                           and provisional_by_name[o.card.name].kind=="artifact_mana"))
                                  for o in kernel.objects.values()),
            "floating_at_end_of_main": floating_end,
            "resource_start": resource_start,
            "resource_after_precast": resource_after_precast,
            "resource_end": resource_end,
            "mana_payment_events": list(mana_service.mana_events[mana_ledger_start:]),
            "life_totals":dict(life.kernel.life_totals),
            "pilot_combat":(dict(opponent_pressure.last_player_combat_decision)
                                if opponent_pressure is not None else None),
            "pilot_decisions":list(pilot_decisions),
            "life_totals_start":dict(outcome_recorder.history[-2]["life_totals"]),
            "life_changes":list(round_life["life_changes"]),
            "eliminations":list(round_life["new_eliminations"]),
            "alive_seats":list(round_life["alive_seats"]),
            "unsupported_cards_in_hand": sorted(
                kernel.get(oid).card.name for oid in zones.ids(0, "hand")
                if not hand_action_supported(kernel.get(oid))),
        })
        if outcome_recorder.outcome(requested_rounds=turns)["complete"]:
            break
    analysis = analyze_authoritative_run(catalog, profile or {}, states)
    return {
        "mode": "bounded_authoritative_early_actions"
                if opponent_pressure is None else "bounded_three_opponent_pressure",
        "opponent_scenario":opponent_scenario,
        "opponent_roles":dict(opponent_pressure.roles) if opponent_pressure else {},
        "seat_zero_defeated":opponent_pressure.defeated if opponent_pressure else False,
        "completed_turns":len(states),
        "completed_rounds":len(states),
        "life_history":list(outcome_recorder.history),
        "outcome":outcome_recorder.outcome(requested_rounds=turns),
        "deck_key": deck_key,
        "pilot_style":pilot_style,
        "pilot_archetype":pilot_strategy.as_dict(),
        "pilot_signals":pilot_signals.as_dict(),
        "provisional_mode":provisional_mode,
        "provisional_import_report":(
            provisional_report(pinned) if provisional_mode=="safe" else []),
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
    parser.add_argument("--provisional-mode",choices=("off","safe"),default="off",
                        help="Enable safe import-derived, explicitly partial card actions")
    parser.add_argument("--pilot-style",choices=STYLES,default="adaptive",
                        help="Deterministic deck-derived legal-action personality")
    parser.add_argument("--pilot-archetype",choices=ARCHETYPES,default="auto",
                        help="Deck-derived strategy or explicit generic archetype")
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf-8")) if args.profile else None
    print(json.dumps(run_bounded_early_game(args.deck, seed=args.seed, turns=args.turns,
                                             mulligan=args.mulligan, profile=profile,
                                             provisional_mode=args.provisional_mode,
                                             pilot_style=args.pilot_style,
                                             pilot_archetype=args.pilot_archetype), indent=2))
