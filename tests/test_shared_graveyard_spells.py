"""Source-pinned multi-step graveyard spells and Technomancer physical ETB."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_enter_effects import (
    reviewed_enter_rule, execute_reviewed_enter)
from commander_sim.graveyard_recipes import (
    GraveyardRecipe, eligible_graveyard_cards,
    resolve_graveyard_recipe, select_bounded_graveyard_batch)
from commander_sim.reviewed_graveyard_spells import (
    RULES, reviewed_graveyard_spell, choose_graveyard_spell_targets,
    cast_reviewed_graveyard_spell)


class SharedGraveyardSpellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for fixture in FIXTURES:
            for entry in json.loads(fixture.snapshot_path.read_text())["cards"]:
                cls.catalog.setdefault(entry["deck_name"],entry["card"])

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K()
        self.z=Z(self.k,seed=27)
        self.C=C
        self.life=KernelLife(self.k)
        self.mana=TemplateManaService(self.k,self.catalog,
                      frozenset({"B"}),zones=self.z)

    def add(self,name,zone="graveyard",*,owner=0,types=("creature",),
            subtypes=(),card_id=None):
        row=self.catalog.get(name,{})
        return self.z.add(self.C(card_id or row.get("oracle_id","test:"+name),
                name,frozenset(types),subtypes=frozenset(subtypes),
                coverage="approx"),owner,zone)

    def mana_sources(self,n):
        return tuple(self.add("Swamp","battlefield",types=("land",))
                     for _ in range(n))

    def spell(self,name):
        return self.add(name,"hand",types=("sorcery",))

    def cast(self,source,targets,*,victim=None):
        return cast_reviewed_graveyard_spell(
            self.z,self.life,0,source,self.catalog,frozenset({"B"}),
            self.mana,target_ids=targets,sacrifice_id=victim)

    def test_four_exact_printed_spell_recipes_registered(self):
        self.assertEqual(set(RULES),{
            "Cemetery Recruitment","Dread Return","Beacon of Unrest","Victimize"})
        for name in RULES:
            raw=self.catalog[name]
            self.assertIsNotNone(reviewed_graveyard_spell(name,raw),name)
            other=dict(raw,oracle_text=raw["oracle_text"]+" Another line.")
            self.assertIsNone(reviewed_graveyard_spell(name,other))

    def test_cemetery_recruitment_returns_zombie_and_draws(self):
        source=self.spell("Cemetery Recruitment")
        zombie=self.add("Zombie target",subtypes=("Zombie",))
        self.add("Top card","library")
        self.mana_sources(2)
        outcome=self.cast(source,(zombie,))
        self.assertIsNotNone(outcome)
        self.assertEqual(len(outcome.drawn_ids),1)
        self.assertEqual(len(outcome.moved_ids),1)
        self.assertEqual(self.k.get(outcome.moved_ids[0]).zone,"hand")
        self.assertEqual(len(self.z.ids(0,"hand")),2)
        self.assertEqual(len(self.z.ids(0,"graveyard")),1)
        self.assertTrue(self.z.assert_consistent())

    def test_cemetery_non_zombie_does_not_draw(self):
        source=self.spell("Cemetery Recruitment")
        target=self.add("Ordinary creature",subtypes=("Human",))
        self.mana_sources(2)
        outcome=self.cast(source,(target,))
        self.assertEqual(outcome.drawn_ids,())
        self.assertEqual(self.k.get(outcome.moved_ids[0]).zone,"hand")
        self.assertTrue(self.z.assert_consistent())

    def test_dread_return_main_cast_reanimates_without_false_flashback(self):
        source=self.spell("Dread Return")
        target=self.add("Own creature",subtypes=("Zombie",))
        self.mana_sources(4)
        outcome=self.cast(source,(target,))
        self.assertEqual(self.k.get(outcome.moved_ids[0]).zone,"battlefield")
        self.assertEqual(self.k.get(outcome.source_resolved_id).zone,"graveyard")
        self.assertTrue(any("flashback" in x for x in outcome.limitations))
        self.assertTrue(self.z.assert_consistent())

    def test_beacon_reanimates_other_owner_and_shuffles_source(self):
        source=self.spell("Beacon of Unrest")
        enemy=self.add("Enemy artifact",owner=1,types=("artifact",))
        self.mana_sources(5)
        outcome=self.cast(source,(enemy,))
        permanent=self.k.get(outcome.moved_ids[0])
        self.assertEqual((permanent.owner,permanent.controller),(1,0))
        self.assertIn(outcome.source_resolved_id,self.z.ids(0,"library"))
        self.assertNotIn(source,self.k.objects)
        self.assertEqual(len(self.z.ids(0,"graveyard")),0)
        self.assertTrue(self.z.assert_consistent())

    def test_victimize_sacrifices_actual_creature_then_reanimates_two_tapped(self):
        source=self.spell("Victimize")
        targets=(self.add("First"),self.add("Second"))
        victim=self.add("Tokenless victim","battlefield")
        self.mana_sources(3)
        outcome=self.cast(source,targets,victim=victim)
        self.assertEqual(outcome.sacrificed_old_id,victim)
        self.assertNotIn(victim,self.k.objects)
        self.assertEqual(len(outcome.moved_ids),2)
        self.assertTrue(all(self.k.get(i).tapped for i in outcome.moved_ids))
        self.assertTrue(all(self.k.get(i).zone=="battlefield"
                            for i in outcome.moved_ids))
        self.assertTrue(self.z.assert_consistent())

    def test_victimize_requires_two_distinct_cards_and_real_sacrifice(self):
        source=self.spell("Victimize")
        first=self.add("First")
        second=self.add("Second")
        self.mana_sources(3)
        self.assertIsNone(self.cast(source,(first,second)))
        with self.assertRaises(ValueError):
            self.cast(source,(first,first),victim=first)
        self.assertIn(source,self.z.ids(0,"hand"))
        self.assertTrue(all(not self.k.get(i).tapped
                            for i in self.z.ids(0,"battlefield")))

    def test_spell_rejects_wrong_oracle_source_and_illegal_graveyard_owner(self):
        source=self.add("Dread Return","hand",types=("sorcery",),
                        card_id="bad:oracle")
        target=self.add("Enemy",owner=1)
        self.mana_sources(4)
        with self.assertRaises(ValueError):
            self.cast(source,(target,))
        normal=self.spell("Dread Return")
        with self.assertRaises(ValueError):
            self.cast(normal,(target,))
        self.assertIn(normal,self.z.ids(0,"hand"))

    def test_bounded_target_policy_uses_pinned_cmc_not_names(self):
        low=self.add("Flayed One",types=("artifact","creature"))
        mid=self.add("Lychguard",types=("artifact","creature"))
        outsider=self.add("Unknown card",types=("artifact","creature"))
        rule=GraveyardRecipe("battlefield","own",frozenset({"creature"}),
             required_types_all=frozenset({"artifact","creature"}))
        chosen=select_bounded_graveyard_batch(
             self.z,0,rule,self.catalog,max_total_mana_value=6)
        self.assertEqual(set(chosen),{low,mid})
        self.assertNotIn(outsider,chosen)
        self.assertEqual(len(eligible_graveyard_cards(self.z,0,rule)),3)

    def test_technomancer_mills_then_returns_affordable_artifact_creatures(self):
        technomancer=self.add("Technomancer","hand",
                             types=("artifact","creature"))
        source=self.z.move(technomancer,"battlefield","resolve")
        one=self.add("Flayed One",types=("artifact","creature"))
        two=self.add("Lychguard",types=("artifact","creature"))
        expensive=self.add("Technomancer",types=("artifact","creature"))
        for i in range(4):
            self.add("Filler "+str(i),"library",types=("creature",))
        entry=reviewed_enter_rule("Technomancer",self.catalog["Technomancer"])
        self.assertIsNotNone(entry)
        outcome=execute_reviewed_enter(self.z,self.life,source,self.catalog)
        self.assertEqual(outcome.operation,"mill_then_reanimate")
        self.assertEqual(len(outcome.milled_ids),3)
        self.assertEqual(set(self.k.get(oid).card.name for oid
                             in outcome.reanimated_ids),
                         {"Flayed One","Lychguard"})
        self.assertEqual(len(outcome.reanimated_ids),2)
        self.assertEqual(self.k.get(expensive).zone,"graveyard")
        self.assertTrue(self.z.assert_consistent())

    def test_required_types_all_rejects_artifact_without_creature(self):
        artifact=self.add("Artifact",types=("artifact",))
        recipe=GraveyardRecipe("battlefield","own",
             frozenset({"artifact","creature"}),
             required_types_all=frozenset({"artifact","creature"}))
        self.assertEqual(eligible_graveyard_cards(self.z,0,recipe),())
        with self.assertRaises(ValueError):
            resolve_graveyard_recipe(self.z,0,(artifact,),recipe)


if __name__=="__main__":
    unittest.main()
