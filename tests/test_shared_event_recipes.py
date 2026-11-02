"""Parameterized death-event recipes and physical graveyard transitions."""
import copy
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.graveyard_recipes import (
    GraveyardRecipe, eligible_graveyard_cards, resolve_graveyard_recipe)
from commander_sim.death_recipes import (
    DeathPredicate, DeathEffectStep, provisional_death_recipe)
from commander_sim.reviewed_death_effects import (
    DEATH_RULES, ReviewedDeathEngine, capture_battlefield)
from commander_sim.provisional_import import provisional_profile, provisional_report


class SharedEffectRecipeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for fixture in FIXTURES:
            for item in json.loads(fixture.snapshot_path.read_text())["cards"]:
                cls.catalog.setdefault(item["deck_name"],item["card"])

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=57)
        self.life=KernelLife(self.kernel)
        self.Card=C

    def add(self,name,zone="graveyard",seat=0,types=("creature",),
            subtypes=(),supertypes=(),token=False,oid=None):
        raw=self.catalog.get(name,{})
        definition=self.Card(oid or raw.get("oracle_id","test:"+name),
                  name,frozenset(types),subtypes=frozenset(subtypes),
                  supertypes=frozenset(supertypes),coverage="approx")
        return self.zones.add(definition,seat,zone,token=token)

    def test_invalid_graveyard_descriptor_fails_before_moves(self):
        for args in (
            {"destination":"stack"},
            {"destination":"battlefield","ownership":"enemy"},
            {"destination":"hand","enter_tapped":True},
            {"destination":"exile","controller_on_entry":"actor"},
            {"destination":"battlefield","enter_counters":("+1/+1",-1)},
            {"destination":"battlefield","enter_counters":("",1)},
            {"destination":"battlefield","required_subtypes":{"Zombie"}},
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                GraveyardRecipe(**args)
        self.assertFalse(self.kernel.objects)

    def test_graveyard_whole_batch_prevalidation_prevents_partial_moves(self):
        zombie=self.add("Our zombie")
        opponent=self.add("Opposing zombie",seat=1)
        recipe=GraveyardRecipe("hand","own",frozenset({"creature"}))
        with self.assertRaises(ValueError):
            resolve_graveyard_recipe(self.zones,0,(zombie,opponent),recipe)
        self.assertIn(zombie,self.zones.ids(0,"graveyard"))
        self.assertIn(opponent,self.zones.ids(1,"graveyard"))
        self.assertTrue(self.zones.assert_consistent())

    def test_graveyard_own_to_hand_keeps_physical_identity(self):
        original=self.add("Zombie")
        spell=self.add("Spell",types=("sorcery",))
        recipe=GraveyardRecipe("hand","own",frozenset({"creature"}))
        self.assertEqual(eligible_graveyard_cards(self.zones,0,recipe),(original,))
        result=resolve_graveyard_recipe(self.zones,0,(original,),recipe)
        self.assertNotIn(original,self.kernel.objects)
        self.assertEqual(self.kernel.get(result[0].new_id).zone,"hand")
        self.assertEqual(self.kernel.get(result[0].new_id).card.name,"Zombie")
        self.assertIn(spell,self.zones.ids(0,"graveyard"))
        self.assertTrue(self.zones.assert_consistent())

    def test_library_return_is_top_first_and_no_duplication(self):
        one=self.add("One")
        two=self.add("Two")
        baseline=self.add("Baseline",zone="library")
        result=resolve_graveyard_recipe(self.zones,0,(one,two),
                                         GraveyardRecipe("library","own"))
        self.assertEqual(tuple(reversed(self.zones.ids(0,"library")[-2:])),
                         (result[0].new_id,result[1].new_id))
        self.assertIn(baseline,self.zones.ids(0,"library"))
        self.assertEqual(len(self.zones.ids(0,"graveyard")),0)
        self.assertTrue(self.zones.assert_consistent())

    def test_opponent_creature_theft_preserves_owner_and_taps(self):
        target=self.add("Enemy",seat=2)
        left=self.add("Other",seat=2,types=("artifact",))
        rule=GraveyardRecipe("battlefield","opponent",frozenset({"creature"}),
                              controller_on_entry="actor",enter_tapped=True)
        result=resolve_graveyard_recipe(self.zones,0,(target,),rule)
        obj=self.kernel.get(result[0].new_id)
        self.assertEqual((obj.owner,obj.controller,obj.tapped),(2,0,True))
        exiled=resolve_graveyard_recipe(self.zones,0,(left,),
                                        GraveyardRecipe("exile","opponent"))
        self.assertEqual(self.kernel.get(exiled[0].new_id).zone,"exile")
        self.assertTrue(self.zones.assert_consistent())

    def test_graveyard_subtype_supertype_and_counter_arguments(self):
        legendary=self.add("Lord",subtypes=("Zombie",),supertypes=("legendary",))
        ordinary=self.add("Normal Zombie",subtypes=("Zombie",))
        rule=GraveyardRecipe("battlefield","own",frozenset({"creature"}),
            frozenset({"Zombie"}),frozenset({"legendary"}),
            enter_counters=("+1/+1",2))
        self.assertEqual(eligible_graveyard_cards(self.zones,0,rule),(legendary,))
        result=resolve_graveyard_recipe(self.zones,0,(legendary,),rule)
        obj=self.kernel.get(result[0].new_id)
        self.assertEqual(obj.counters["+1/+1"],2)
        self.assertFalse(obj.tapped)
        self.assertIn(ordinary,self.zones.ids(0,"graveyard"))
        self.assertTrue(self.zones.assert_consistent())

    def test_graveyard_disallows_duplicate_ids_and_non_graveyard(self):
        creature=self.add("Creature")
        hand=self.add("Other",zone="hand")
        recipe=GraveyardRecipe("hand","own")
        for selected in ((creature,creature),(hand,),(-1,)):
            with self.subTest(ids=selected),self.assertRaises(ValueError):
                resolve_graveyard_recipe(self.zones,0,selected,recipe)
        self.assertIn(creature,self.zones.ids(0,"graveyard"))

    def test_death_filter_parameters_apply_to_lki(self):
        source=self.add("Source",zone="battlefield",subtypes=("Zombie",))
        victim=self.add("Victim",zone="battlefield",subtypes=("Zombie",))
        token=self.add("Token",zone="battlefield",subtypes=("Zombie",),token=True)
        enemy=self.add("Enemy",zone="battlefield",seat=1,subtypes=("Zombie",))
        pre=capture_battlefield(self.kernel)
        predicate=DeathPredicate("own",frozenset({"creature"}),
                                  subtype="Zombie",exclude_source=True,
                                  nontoken_only=True)
        self.assertTrue(predicate.matches(pre[source],pre[victim]))
        for other in (source,token,enemy):
            self.assertFalse(predicate.matches(pre[source],pre[other]))
        with self.assertRaises(ValueError):
            DeathPredicate("self",exclude_source=True)

    def test_midnight_reaper_uses_two_ordered_damage_and_draw_steps(self):
        reaper=self.add("Midnight Reaper",zone="battlefield")
        victim=self.add("Friendly",zone="battlefield")
        self.add("Drawn card",zone="library")
        engine=ReviewedDeathEngine(self.zones,self.life,self.catalog)
        before=capture_battlefield(self.kernel)
        start=len(self.kernel.moves)
        self.zones.move(victim,"graveyard","sacrifice")
        outcomes=engine.resolve_deaths(before,move_index=start,turn=1)
        self.assertEqual(len(outcomes),1)
        self.assertEqual(outcomes[0].source_name,"Midnight Reaper")
        self.assertEqual(outcomes[0].operation,"sequence")
        self.assertEqual(len(outcomes[0].drawn_ids),1)
        self.assertEqual(self.life.total(0),39)
        self.assertTrue(self.zones.assert_consistent())
        self.assertEqual(len(DEATH_RULES["Midnight Reaper"][0].action.steps),2)

    def test_midnight_reaper_excludes_tokens_and_enemy_creatures(self):
        self.add("Midnight Reaper",zone="battlefield")
        enemy=self.add("Enemy",zone="battlefield",seat=1)
        token=self.add("Token",zone="battlefield",token=True)
        engine=ReviewedDeathEngine(self.zones,self.life,self.catalog)
        before=capture_battlefield(self.kernel)
        start=len(self.kernel.moves)
        self.zones.move(enemy,"graveyard","destroy")
        self.zones.move(token,"graveyard","sacrifice")
        self.assertEqual(engine.resolve_deaths(before,move_index=start,turn=1),())
        self.assertEqual(self.life.total(0),40)

    def test_provisional_death_body_is_opt_in_and_identity_pinned(self):
        text="Flying\nWhen this creature dies, draw a card."
        source={"name":"Future Phoenix","oracle_id":"a11a11a1-1111-4111-8111-111111111111",
                "oracle_text":text,"type_line":"Creature — Phoenix",
                "mana_cost":"{2}{R}","layout":"normal"}
        self.assertEqual(provisional_profile(source).kind,"creature_body")
        catalog=dict(self.catalog,**{"Future Phoenix":source})
        obj=self.add("Future Phoenix",zone="battlefield",oid="a11a11a1-1111-4111-8111-111111111111")
        self.add("Drawn",zone="library")
        strict=ReviewedDeathEngine(self.zones,self.life,catalog)
        safe=ReviewedDeathEngine(self.zones,self.life,catalog,provisional_mode="safe")
        before=capture_battlefield(self.kernel)
        start=len(self.kernel.moves)
        self.zones.move(obj,"graveyard","destroy")
        self.assertEqual(strict.resolve_deaths(before,move_index=start,turn=1),())
        result=safe.resolve_deaths(before,move_index=start,turn=1)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0].operation,"sequence")
        self.assertEqual(len(result[0].drawn_ids),1)
        self.assertTrue(self.zones.assert_consistent())

    def test_provisional_death_drain_uses_same_generic_condition(self):
        printed=("Whenever another creature you control dies, "
                 "each opponent loses 1 life.")
        card={"name":"Future Drain","oracle_id":"b22b22b2-2222-4222-8222-222222222222",
              "oracle_text":printed,"type_line":"Creature — Horror",
              "mana_cost":"{1}{B}","layout":"normal"}
        self.assertIsNotNone(provisional_death_recipe(printed))
        catalog=dict(self.catalog,**{"Future Drain":card})
        source=self.add("Future Drain",zone="battlefield",oid="b22b22b2-2222-4222-8222-222222222222")
        friend=self.add("Friend",zone="battlefield")
        opponent=self.add("Enemy",zone="battlefield",seat=1)
        engine=ReviewedDeathEngine(self.zones,self.life,catalog,provisional_mode="safe")
        before=capture_battlefield(self.kernel)
        start=len(self.kernel.moves)
        self.zones.move(opponent,"graveyard","destroy")
        self.assertEqual(engine.resolve_deaths(before,move_index=start,turn=1),())
        before=capture_battlefield(self.kernel)
        start=len(self.kernel.moves)
        self.zones.move(friend,"graveyard","sacrifice")
        result=engine.resolve_deaths(before,move_index=start,turn=1)
        self.assertEqual(len(result),1)
        self.assertEqual([self.life.total(i) for i in range(4)],
                         [40,39,39,39])
        self.assertEqual(result[0].source_id,source)

    def test_provisional_death_rejects_multi_trigger_and_extra_etb(self):
        for oracle in (
            "When this creature dies, draw a card.\n"
            "Whenever this creature dies, gain 2 life.",
            "Whenever another creature you control dies, you win the game.",
            "When this creature dies, draw a card and win the game.",
        ):
            self.assertIsNone(provisional_death_recipe(oracle))
        invalid={"name":"Unsafe Phoenix","oracle_id":"future:unsafe",
                 "oracle_text":"When this creature enters, sacrifice a creature.\n"
                    "When this creature dies, draw a card.",
                 "mana_cost":"{2}{R}","type_line":"Creature — Phoenix",
                 "layout":"normal"}
        self.assertIsNone(provisional_profile(invalid))

    def test_import_report_lists_trigger_arguments_without_granting_full_rules(self):
        row={"name":"New Buddy","oracle_id":"test:buddy",
             "oracle_text":"When this creature dies, draw a card.",
             "type_line":"Creature — Human","layout":"normal",
             "mana_cost":"{2}"}
        report=provisional_report([{"deck_name":"New Buddy","card":row}])
        trigger=report[0]["provisional_death_trigger"]
        self.assertEqual(trigger["scope"]["relation"],"self")
        self.assertEqual(trigger["steps"],[{"kind":"draw","count":1}])
        self.assertEqual(report[0]["fidelity"],"provisional_partial")
        self.assertEqual(report[0]["status"],"provisional")


if __name__=="__main__":
    unittest.main()
