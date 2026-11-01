"""Per-slot composition contracts, promotion and backend integration."""
import unittest
from dataclasses import replace

from commander_sim.ability_composition import (
    AbilitySlot, AbilityHandler, ComposedCard, AbilityDispatcher,
    TriggerSubscriptions, inspected_search_card, inspected_rock_card,
)
from commander_sim.legacy_tutor_ops import HISTORICAL_SEARCHES
from commander_sim.effect_templates import compose_effect
from commander_sim.reviewed_tutors import TUTORS

OID="422e1869-134f-463d-9fa1-86b66a998b3e"


def ability(slot_id, kind="triggered", operation="make_token", required=frozenset(),
            text="Trigger one."):
    return AbilitySlot(OID,"front",slot_id,kind,operation,text,"source-v1",required)


def handler(slot, fidelity, required=frozenset(), limitations=()):
    return AbilityHandler(slot.key,fidelity,slot.declaration,slot.source_revision,
                          required,limitations)


class AbilityCompositionTests(unittest.TestCase):
    def test_two_ability_slots_resolve_independently(self):
        token=ability("token")
        draw=ability("draw",operation="draw_one",text="Trigger two.")
        card=ComposedCard(OID,"Trigger one.\nTrigger two.",(token,draw),
            (handler(token,"simplified",limitations=("Partial triggers",)),
             handler(draw,"exact")))
        self.assertEqual(card.coverage("strict",frozenset()),
                         (("token","unsupported"),("draw","exact")))
        self.assertEqual(card.coverage("hybrid",frozenset()),
                         (("token","simplified"),("draw","exact")))

    def test_promotion_supersedes_only_matching_slot(self):
        token=ability("token")
        draw=ability("draw",operation="draw_one",text="Trigger two.")
        both=ComposedCard(OID,"Trigger one.\nTrigger two.",(token,draw),
            (handler(token,"simplified",limitations=("partial",)),
             handler(token,"exact"),
             handler(draw,"simplified",limitations=("partial draw",))))
        self.assertEqual(both.coverage("hybrid",frozenset()),
                         (("token","exact"),("draw","simplified")))
        self.assertEqual(both.coverage("strict",frozenset()),
                         (("token","exact"),("draw","unsupported")))

    def test_missing_prereqs_fail_closed(self):
        slot=ability("token",required=frozenset({"triggers","tokens"}))
        card=ComposedCard(OID,"Trigger one.",(slot,),
            (handler(slot,"exact",frozenset({"tokens"})),))
        self.assertIsNone(card.resolve("token","strict",frozenset({"tokens"})))
        self.assertEqual(card.resolve("token","strict",
            frozenset({"tokens","triggers"})).fidelity,"exact")

    def test_observation_cannot_execute_reviewed_handler(self):
        slot=ability("token")
        card=ComposedCard(OID,"Trigger one.",(slot,),(handler(slot,"exact"),))
        dispatch=AbilityDispatcher(card,"observation")
        actions=[]
        with self.assertRaises(NotImplementedError):
            dispatch.invoke("token",42,lambda op:actions.append(op))
        self.assertEqual(actions,[])
        self.assertEqual(dispatch.events,[])

    def test_single_callback_and_provenance_on_success(self):
        slot=ability("token")
        card=ComposedCard(OID,"Trigger one.",(slot,),
            (handler(slot,"simplified",limitations=("bounded trigger",)),))
        dispatch=AbilityDispatcher(card,"hybrid")
        actual=[]
        self.assertEqual(dispatch.invoke("token",18,lambda x:actual.append(x) or 27),27)
        self.assertEqual(actual,["make_token"])
        self.assertEqual(len(dispatch.events),1)
        self.assertEqual(dispatch.events[0].slot_key,slot.key)
        self.assertEqual(dispatch.events[0].fidelity,"simplified")
        self.assertEqual(dispatch.events[0].source_object_id,18)

    def test_invalid_callback_does_not_generate_false_event(self):
        slot=ability("token")
        card=ComposedCard(OID,"Trigger one.",(slot,),(handler(slot,"exact"),))
        dispatch=AbilityDispatcher(card)
        def fail(_):
            raise ValueError("Illegal target")
        with self.assertRaises(ValueError):
            dispatch.invoke("token",18,fail)
        self.assertEqual(dispatch.events,[])

    def test_trigger_registration_is_idempotent_and_cleans_zone_departure(self):
        slot=ability("token")
        subs=TriggerSubscriptions()
        self.assertTrue(subs.subscribe(9,slot,"spell_cast"))
        self.assertFalse(subs.subscribe(9,slot,"spell_cast"))
        self.assertTrue(subs.subscribe(10,slot,"spell_cast"))
        self.assertEqual(subs.unsubscribe(9),1)
        self.assertFalse(subs.contains(9,slot,"spell_cast"))
        self.assertTrue(subs.subscribe(9,slot,"spell_cast"))
        self.assertTrue(subs.contains(10,slot,"spell_cast"))

    def test_unknown_slot_and_duplicate_handler_fails_closed(self):
        slot=ability("token")
        with self.assertRaises(ValueError):
            ComposedCard(OID,"Trigger one.",(slot,),
                 (handler(slot,"exact"),handler(slot,"exact")))
        with self.assertRaises(ValueError):
            ComposedCard(OID,"Trigger one.",(slot,),
                 (handler(slot,"simplified",limitations=("x",)),
                  handler(slot,"simplified",limitations=("y",))))
        with self.assertRaises(ValueError):
            ComposedCard(OID,"Trigger one.",(slot,slot),())
        card=ComposedCard(OID,"Trigger one.",(slot,),())
        self.assertIsNone(card.resolve("unknown","hybrid",frozenset()))

    def test_unreviewed_source_excerpt_and_unchecked_handler_rejected(self):
        slot=ability("token")
        with self.assertRaises(ValueError):
            ComposedCard(OID,"Different words.",(slot,),())
        bad=replace(handler(slot,"exact"),source_revision="different")
        with self.assertRaises(ValueError):
            ComposedCard(OID,"Trigger one.",(slot,),(bad,))
        bad_op=replace(handler(slot,"exact"),operation="wrong")
        with self.assertRaises(ValueError):
            ComposedCard(OID,"Trigger one.",(slot,),(bad_op,))

    def test_mind_stone_contains_explicit_unsupported_sacrifice_draw(self):
        card=inspected_rock_card("Mind Stone",frozenset({"U","R"}))
        self.assertEqual(card.coverage("hybrid",frozenset({"mana_activation","sacrifice","draw"})),
                         (("mana","simplified"),("sacrifice_draw","unsupported")))
        self.assertIsNone(card.resolve("sacrifice_draw","strict",
                                      frozenset({"mana_activation","sacrifice","draw"})))
        self.assertEqual(inspected_rock_card("Untested Rock",frozenset({"U"})),None)

    def test_rock_commander_color_modes_remain_configured(self):
        card=inspected_rock_card("Arcane Signet",frozenset({"U","R"}))
        mana=card.resolve("mana","hybrid",frozenset({"mana_activation"}))
        self.assertEqual({mode.output for mode in mana.operation.mana_modes},
                         {("U",),("R",)})

    def test_five_historical_tutors_use_reviewed_slot_configs(self):
        names={"fabricate":"Fabricate","solve_equation":"Solve the Equation",
               "merchant_scroll":"Merchant Scroll","spellseeker":"Spellseeker",
               "mystical_tutor":"Mystical Tutor"}
        for key,name in names.items():
            with self.subTest(card=name):
                card=inspected_search_card(name,include_historical_exact=True)
                h=card.resolve("search","strict",
                               frozenset({"library_search","historical_search"}))
                self.assertIsNotNone(h)
                self.assertEqual(HISTORICAL_SEARCHES[key].effect,
                                 h.operation)
                self.assertEqual(h.operation,compose_effect(TUTORS[name]["review"]))
                self.assertIsNone(card.resolve("search","strict",frozenset({"library_search"})))
                self.assertEqual(card.resolve("search","hybrid",
                    frozenset({"library_search"})).fidelity,"simplified")

    def test_invalid_modes_and_unregistered_card_are_not_executable(self):
        self.assertIsNone(inspected_search_card("Invented Tutor"))
        card=inspected_search_card("Fabricate")
        with self.assertRaises(ValueError):
            card.resolve("search","not-a-mode",frozenset())
        with self.assertRaises(ValueError):
            AbilityDispatcher(card,"not-a-mode")

    def test_invalid_trigger_subscription_rejected(self):
        slot=ability("spell","spell")
        with self.assertRaises(ValueError):
            TriggerSubscriptions().subscribe(1,slot,"spell_cast")


if __name__=="__main__":
    unittest.main()
