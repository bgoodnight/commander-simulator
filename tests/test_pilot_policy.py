"""Generic source-neutral pilot ranking: hard constraints are upstream."""
import copy
import unittest

from commander_sim.pilot_policy import (
    STYLES,DeckSignals,PilotContext,choose_legal_option,
    infer_deck_signals,rank_legal_action,choose_combat_posture,
    infer_pilot_archetype,ARCHETYPES)
from commander_sim.early_game_runner import run_bounded_early_game


def catalog_row(text,types="Creature — Wizard",cost="{2}{U}"):
    return {"oracle_text":text,"type_line":types,"mana_cost":cost,
            "oracle_id":"22222222-2222-4222-8222-222222222222",
            "layout":"normal"}


class GeneralPilotPolicyTests(unittest.TestCase):
    def setUp(self):
        self.context=PilotContext(
            round=3,life=38,hand_size=6,lands=3,mana_sources=3,
            graveyard_creatures=0,friendly_creatures=1,opposing_creatures=2)
        self.synergy=DeckSignals(65,tuple(sorted({
            "spell_engine":13,"graveyard":5,"sacrifice":4,
            "tokens":11,"artifacts":8,"combat":0}.items())),("flying",))
        self.empty=DeckSignals(65,tuple(sorted({
            "spell_engine":0,"graveyard":0,"sacrifice":0,
            "tokens":0,"artifacts":0,"combat":0}.items())),())

    def test_inference_uses_quantities_and_ignores_land_text(self):
        catalog={
            "Spell Mage":catalog_row(
                "Whenever you cast an instant or sorcery spell, create a 1/1 token.\nFlying"),
            "Grave Worker":catalog_row(
                "Sacrifice a creature: Return target creature card from your graveyard to hand."),
            "Swamp":catalog_row("{T}: Add {B}.","Basic Land — Swamp",""),
            "Unknown":dict(catalog_row("Whenever you cast an instant or sorcery spell."),
                           oracle_text=None),
        }
        deck=(("Commander","Spell Mage",1),("Deck","Spell Mage",4),
              ("Deck","Grave Worker",2),("Deck","Swamp",15),
              ("Deck","Unknown",1))
        out=infer_deck_signals(deck,catalog)
        self.assertEqual(out.nonland_cards,7)
        self.assertEqual(out.count("spell_engine"),5)
        self.assertEqual(out.count("tokens"),5)
        self.assertEqual(out.count("graveyard"),2)
        self.assertEqual(out.count("sacrifice"),2)
        self.assertTrue(out.dense("spell_engine"))
        self.assertIn("flying",out.keywords)

    def test_non_mana_artifact_keeps_its_permanent_role(self):
        artifact=catalog_row(
            "At the beginning of your upkeep, scry 1.","Artifact","{2}")
        rank=rank_legal_action("artifact",artifact,self.context,self.empty)
        other=rank_legal_action("unreviewed_other",artifact,
                                self.context,self.empty)
        self.assertEqual(rank.category,"artifact")
        self.assertGreater(rank.score,other.score)

    def test_combat_posture_uses_same_personality_and_deck_signals(self):
        base=choose_combat_posture(
            life=14,opposing_creatures=6,style="balanced")
        tempo=choose_combat_posture(
            life=14,opposing_creatures=6,style="tempo")
        cautious=choose_combat_posture(
            life=14,opposing_creatures=6,style="conservative")
        self.assertEqual((base.reserve,base.attack_limit),(2,3))
        self.assertEqual((tempo.reserve,tempo.attack_limit),(1,4))
        self.assertEqual((cautious.reserve,cautious.attack_limit),(3,2))
        combat_rich=DeckSignals(65,(
            ("artifacts",0),("combat",8),("graveyard",0),
            ("sacrifice",0),("spell_engine",0),("tokens",0)),())
        adaptive=choose_combat_posture(
            life=14,opposing_creatures=6,style="adaptive",
            signals=combat_rich)
        self.assertEqual((adaptive.reserve,adaptive.attack_limit),(1,4))
        self.assertIn("deck_combat_density",adaptive.factors)
        with self.assertRaises(ValueError):
            choose_combat_posture(
                life=20,opposing_creatures=1,style="named_commander")
        with self.assertRaises(ValueError):
            choose_combat_posture(life=20,opposing_creatures=-1)

    def test_archetype_inference_uses_deck_functions_without_names(self):
        evidence=DeckSignals(65,tuple(sorted({
            "sacrifice":15,"death_triggers":10,"tokens":8,
            "graveyard":5,"recursion":4,"artifacts":3,"combat":2,
            "spell_engine":1,"spells":8,"removal":2}.items())),())
        auto=infer_pilot_archetype(evidence)
        self.assertEqual(auto.primary,"aristocrats")
        self.assertEqual(auto.selected,"auto")
        self.assertGreater(auto.as_dict()["scores"]["aristocrats"],
                           auto.as_dict()["scores"]["spellslinger"])
        manual=infer_pilot_archetype(evidence,"control")
        self.assertEqual(manual.primary,"control")
        self.assertEqual(manual.evidence,auto.evidence)
        with self.assertRaises(ValueError):
            infer_pilot_archetype(evidence,"named_commander_script")

    def test_archetype_weights_only_rank_verified_options(self):
        option=(0,2,"Useful Engine",5,"creature","{2}{B}",None)
        row=catalog_row("Whenever a creature you control dies, draw a card.")
        base,base_score=choose_legal_option(
            [option],self.context,self.empty,{"Useful Engine":row},
            archetype="midrange")
        chosen,special=choose_legal_option(
            [option],self.context,self.empty,{"Useful Engine":row},
            archetype="aristocrats")
        self.assertEqual(base,chosen)
        self.assertGreater(special.score,base_score.score)
        self.assertIn("archetype:aristocrats",special.factors)

    def test_physical_mortarion_automatically_selects_aristocrats(self):
        run=run_bounded_early_game(
            "mortarion_physical_final",seed=5,turns=3,
            pilot_archetype="auto")
        self.assertEqual(run["pilot_archetype"]["primary"],"aristocrats")
        self.assertGreater(run["pilot_archetype"]["evidence"]["death_triggers"],5)
        override=run_bounded_early_game(
            "mortarion_physical_final",seed=5,turns=2,
            pilot_archetype="control")
        self.assertEqual(override["pilot_archetype"]["primary"],"control")
        with self.assertRaises(ValueError):
            run_bounded_early_game("mortarion_physical_final",
                                   turns=1,pilot_archetype="commander_only")

    def test_early_mana_development_beats_otherwise_equal_body(self):
        rock=catalog_row("{T}: Add {C}{C}.","Artifact","{1}")
        creature=catalog_row("Ward {2}.")
        ramp=rank_legal_action("artifact",rock,self.context,self.empty)
        body=rank_legal_action("creature",creature,self.context,self.empty)
        self.assertGreater(ramp.score,body.score)
        self.assertIn("early_mana_development",ramp.factors)

    def test_late_ramp_has_diminishing_returns(self):
        late=PilotContext(round=12,life=35,hand_size=5,lands=10,
              mana_sources=11,graveyard_creatures=2,friendly_creatures=7,
              opposing_creatures=4)
        rock=catalog_row("{T}: Add {B}.","Artifact","{2}")
        low=rank_legal_action("artifact",rock,self.context,self.empty)
        high=rank_legal_action("artifact",rock,late,self.empty)
        self.assertGreater(low.score,high.score)

    def test_spell_trigger_engine_responds_to_deck_not_commander(self):
        engine=catalog_row(
            "Whenever you cast an instant or sorcery spell, draw a card.")
        dense=rank_legal_action("creature",engine,self.context,self.synergy)
        sparse=rank_legal_action("creature",engine,self.context,self.empty)
        self.assertGreater(dense.score,sparse.score)
        self.assertIn("spell_trigger_density",dense.factors)

    def test_growing_graveyard_density_changes_reanimate_value(self):
        spell=catalog_row("Return target creature from a graveyard to battlefield.",
                          "Sorcery","{2}{B}")
        ctx=PilotContext(round=7,life=25,hand_size=4,lands=6,mana_sources=6,
              graveyard_creatures=5,friendly_creatures=2,opposing_creatures=4)
        a=rank_legal_action("graveyard_spell",spell,ctx,self.synergy)
        b=rank_legal_action("graveyard_spell",spell,ctx,self.empty)
        self.assertGreater(a.score,b.score)

    def test_low_life_prioritizes_defensive_removal(self):
        danger=PilotContext(round=8,life=11,hand_size=4,lands=7,mana_sources=6,
            graveyard_creatures=3,friendly_creatures=2,opposing_creatures=5)
        spell=catalog_row("Destroy target creature.","Instant","{1}{B}")
        low=rank_legal_action("removal_spell",spell,danger,self.synergy)
        safe=rank_legal_action("removal_spell",spell,self.context,self.synergy)
        self.assertGreater(low.score,safe.score)
        self.assertIn("defensive_removal",low.factors)

    def test_low_hand_promotes_card_draw(self):
        empty=PilotContext(round=6,life=37,hand_size=2,lands=5,mana_sources=5,
              graveyard_creatures=1,friendly_creatures=2,opposing_creatures=2)
        draw=catalog_row("Draw two cards.","Sorcery","{2}{U}")
        low=rank_legal_action("draw_spell",draw,empty,self.empty)
        full=rank_legal_action("draw_spell",draw,self.context,self.empty)
        self.assertGreater(low.score,full.score)

    def test_styles_change_weights_but_cannot_grant_actions(self):
        row=catalog_row("Whenever you cast an instant or sorcery spell, draw a card.")
        balanced=rank_legal_action("creature",row,self.context,self.synergy,
                                   style="balanced")
        engine=rank_legal_action("creature",row,self.context,self.synergy,
                                 style="engine")
        self.assertGreater(engine.score,balanced.score)
        with self.assertRaises(ValueError):
            rank_legal_action("creature",row,self.context,self.synergy,
                              style="infinite_combo")
        option=(0,2,"Wizard",5,"creature","{2}{U}",None)
        chosen,score=choose_legal_option([option],self.context,self.synergy,
                                         {"Wizard":row},style="tempo")
        self.assertEqual(chosen,option)
        self.assertEqual(score.category,"engine")

    def test_source_name_changes_do_not_change_action_order(self):
        engine=catalog_row("Whenever you cast an instant or sorcery spell, draw a card.")
        rock=catalog_row("{T}: Add {C}{C}.","Artifact","{1}")
        options=[
            (0,2,"A",3,"creature","{2}{U}",None),
            (0,1,"B",5,"artifact","{1}",None),
        ]
        initial,_=choose_legal_option(
            options,self.context,self.synergy,{"A":engine,"B":rock})
        renamed=[(x[0],x[1],("X" if x[2]=="A" else "Y"),x[3],
                  x[4],x[5],x[6]) for x in options]
        other,_=choose_legal_option(renamed,self.context,self.synergy,
                                   {"X":engine,"Y":rock})
        self.assertEqual(initial[3],other[3])

    def test_option_order_does_not_affect_decision_or_tie_break(self):
        options=[(1,2,"Z",12,"creature","{1}",None),
                 (1,2,"A",20,"creature","{1}",None)]
        c={"Z":catalog_row("Ward {2}."),
           "A":catalog_row("Ward {2}.")}
        x,_=choose_legal_option(options,self.context,self.empty,c)
        y,_=choose_legal_option(list(reversed(options)),self.context,self.empty,c)
        self.assertEqual(x,y)
        self.assertEqual(x[2],"A")

    def test_unaffordable_card_cannot_be_selected_by_scoring(self):
        # The scorer can only rank supplied already-approved candidates.
        options=[(2,1,"Available",3,"creature","{1}",None)]
        c={"Available":catalog_row("Flying."),
           "Unpayable":catalog_row(
               "Whenever you cast an instant or sorcery spell, draw a card.")}
        selected,_=choose_legal_option(options,self.context,self.synergy,c)
        self.assertEqual(selected[2],"Available")

    def test_invalid_context_rejected_and_no_empty_action_invented(self):
        with self.assertRaises(ValueError):
            PilotContext(round=0,life=40,hand_size=5,lands=1,
                mana_sources=1,graveyard_creatures=0,friendly_creatures=0,
                opposing_creatures=0)
        self.assertEqual(
            choose_legal_option([],self.context,self.empty,{}),(None,None))
        with self.assertRaises(ValueError):
            choose_legal_option([(0,0,"A")],self.context,self.empty,{})

    def test_four_decks_have_deck_derived_signals_and_cast_evidence(self):
        for deck in ("wretched_ranks","necron_dynasties",
                     "magnus_premium","mortarion_current"):
            with self.subTest(deck=deck):
                run=run_bounded_early_game(
                    deck,seed=5,turns=5,pilot_style="adaptive")
                self.assertEqual(run["pilot_style"],"adaptive")
                self.assertGreater(run["pilot_signals"]["nonland_cards"],40)
                self.assertEqual(len(run["events"]),5)
                for row in run["events"]:
                    for decision in row["pilot_decisions"]:
                        self.assertEqual(decision["personality"],"adaptive")
                        self.assertGreater(decision["candidate_count"],0)
                        self.assertIn("base:",decision["factors"][0])
                self.assertEqual(len(run["state_snapshots"]),5)

    def test_deterministic_choice_trace_per_style_and_seed(self):
        a=run_bounded_early_game(
            "magnus_budget",seed=7,turns=4,pilot_style="engine")
        b=run_bounded_early_game(
            "magnus_budget",seed=7,turns=4,pilot_style="engine")
        self.assertEqual(
            [r["pilot_decisions"] for r in a["events"]],
            [r["pilot_decisions"] for r in b["events"]])
        self.assertEqual(a["life_totals"],b["life_totals"])
        self.assertEqual(a["pilot_style"],"engine")
        with self.assertRaises(ValueError):
            run_bounded_early_game(
                "magnus_budget",seed=7,turns=2,pilot_style="magnus_only")


if __name__=="__main__":
    unittest.main()
