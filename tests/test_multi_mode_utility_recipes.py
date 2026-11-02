"""Multi-card reusable utility activations: real costs, targets, life and tokens."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES,EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel,run_bounded_early_game
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_rocks import reviewed_rock
from commander_sim.reviewed_early_cards import reviewed_creature
from commander_sim.reviewed_utility_activations import (
    UtilityRule,reviewed_utility,activate_utility)


class MultiModeUtilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        cls.by_deck={}
        for fixture in (*FIXTURES,*EXPERIMENTAL_FIXTURES):
            table={entry["deck_name"]:entry["card"] for entry in
                   json.loads(fixture.snapshot_path.read_text())["cards"]}
            cls.by_deck[fixture.key]=table
            cls.catalog.update(table)

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=29)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.mana=TemplateManaService(self.kernel,self.catalog,
                             frozenset({"B"}),zones=self.zones)

    def add(self,name,*,zone="battlefield",seat=0,types=None,
            subtypes=(),token=False,id_override=None):
        row=self.catalog.get(name,{})
        if types is None:
            head=row.get("type_line","Creature").split(" — ",1)[0]
            types=tuple(w.lower() for w in head.split() if w.lower() in
                        {"land","artifact","creature","instant","sorcery"})
        definition=self.C(id_override or row.get("oracle_id","test:"+name),
            name,frozenset(types),subtypes=frozenset(subtypes),
            coverage="approx")
        return self.zones.add(definition,seat,zone,token=token)

    def swamps(self,n):
        return [self.add("Swamp",types=("land",)) for _ in range(n)]

    def library(self,n):
        return [self.add("Library "+str(i),zone="library",types=("sorcery",))
                for i in range(n)]

    def use(self,source,*,target_id=None,tap_ready=False):
        return activate_utility(self.zones,self.life,0,source,
            self.catalog,self.mana,frozenset({"B"}),
            target_id=target_id,tap_ready=tap_ready)

    def test_hedron_archive_draw_two_with_source_payment_and_sacrifice(self):
        archive=self.add("Hedron Archive")
        self.swamps(2)
        self.library(3)
        result=self.use(archive)
        self.assertEqual(result.operation,"draw")
        self.assertEqual(len(result.drawn_ids),2)
        self.assertEqual(result.life_lost_after,0)
        self.assertEqual(len(result.new_object_ids),3)
        self.assertNotIn(archive,self.kernel.objects)
        self.assertEqual(self.kernel.get(result.new_object_ids[0]).zone,
                         "graveyard")
        self.assertTrue(self.zones.assert_consistent())

    def test_commanders_sphere_can_sacrifice_for_card_with_zero_mana(self):
        sphere=self.add("Commander's Sphere")
        self.library(1)
        out=self.use(sphere)
        self.assertEqual(out.life_paid,0)
        self.assertEqual(len(out.drawn_ids),1)
        self.assertEqual(out.paid_source_ids,())
        self.assertNotIn(sphere,self.kernel.objects)
        self.assertEqual(len(self.zones.ids(0,"hand")),1)
        self.assertTrue(self.zones.assert_consistent())

    def test_infernal_idol_draw_two_and_lose_two_after_not_as_a_cost(self):
        idol=self.add("Infernal Idol")
        self.swamps(3)
        self.library(2)
        out=self.use(idol)
        self.assertEqual(len(out.drawn_ids),2)
        self.assertEqual(out.life_paid,0)
        self.assertEqual(out.life_lost_after,2)
        self.assertEqual(self.life.total(0),38)
        self.assertEqual(self.kernel.life_changes[-1].kind,"loss")
        self.assertTrue(self.zones.assert_consistent())

    def test_cryptbreaker_taps_three_real_zombies_and_draws_loses_one(self):
        crypt=self.add("Cryptbreaker",subtypes=("Zombie",))
        first=self.add("Zombie A",subtypes=("Zombie",),token=True)
        second=self.add("Zombie B",subtypes=("Zombie",),token=True)
        self.library(2)
        out=self.use(crypt)
        self.assertEqual(out.operation,"draw")
        self.assertEqual(set(out.tapped_cost_ids),{crypt,first,second})
        self.assertEqual(len(out.drawn_ids),1)
        self.assertEqual(self.life.total(0),39)
        self.assertEqual(out.life_lost_after,1)
        self.assertTrue(all(self.kernel.get(i).tapped
                            for i in (crypt,first,second)))
        self.assertTrue(self.zones.assert_consistent())

    def test_cryptbreaker_fails_preflight_without_three_untapped_zombies(self):
        crypt=self.add("Cryptbreaker",subtypes=("Zombie",))
        self.add("Zombie",subtypes=("Zombie",))
        self.library(1)
        self.assertIsNone(self.use(crypt))
        self.assertEqual(self.life.total(0),40)
        self.assertFalse(self.kernel.get(crypt).tapped)
        self.assertTrue(self.zones.assert_consistent())

    def test_cemetery_reaper_exiles_enemy_graveyard_creature_and_makes_token(self):
        source=self.add("Cemetery Reaper",subtypes=("Zombie",))
        enemy=self.add("Enemy",seat=1,zone="graveyard",types=("creature",))
        self.swamps(3)
        self.assertIsNone(self.use(source,target_id=enemy))
        out=self.use(source,target_id=enemy,tap_ready=True)
        self.assertEqual(out.operation,"exile_graveyard_token")
        self.assertEqual(len(out.created_token_ids),1)
        self.assertEqual(len(out.new_object_ids),2)
        self.assertEqual(self.kernel.get(out.new_object_ids[0]).zone,"exile")
        zombie=self.kernel.get(out.created_token_ids[0])
        self.assertTrue(zombie.token)
        self.assertEqual(zombie.subtypes,frozenset({"Zombie"}))
        self.assertEqual((zombie.power,zombie.toughness),(2,2))
        self.assertTrue(self.kernel.get(source).tapped)
        self.assertTrue(self.zones.assert_consistent())

    def test_cemetery_reaper_rejects_noncreature_target_before_payment(self):
        source=self.add("Cemetery Reaper",subtypes=("Zombie",))
        opponent_spell=self.add("Opposing spell",seat=1,zone="graveyard",
                                types=("sorcery",))
        self.swamps(3)
        self.assertIsNone(self.use(
            source,target_id=opponent_spell,tap_ready=True))
        self.assertFalse(self.kernel.get(source).tapped)
        self.assertIn(opponent_spell,self.zones.ids(1,"graveyard"))

    def test_multiple_verified_rock_modes_share_generic_mana_templates(self):
        for name in ("Hedron Archive","Infernal Idol","Commander's Sphere"):
            raw=self.catalog[name]
            self.assertIsNotNone(reviewed_rock(name,raw,frozenset({"B"})),name)
            self.assertIsNotNone(reviewed_utility(name,raw),name)
            modified=dict(raw,oracle_id="unverified")
            self.assertIsNone(reviewed_utility(name,modified))
            self.assertIsNone(reviewed_rock(name,modified,frozenset({"B"})))

    def test_source_pinned_recursion_and_physical_body_newlines_admit(self):
        expected=(("wretched_ranks","Lord of the Undead"),
                  ("wretched_ranks","Cemetery Reaper"),
                  ("mortarion_physical_final","Plague Spitter"),
                  ("mortarion_physical_final","Plague Drone"),
                  ("mortarion_physical_final","Stuffy Doll"))
        for deck,name in expected:
            with self.subTest(deck=deck,name=name):
                row=self.by_deck[deck][name]
                self.assertTrue(reviewed_creature(deck,name,row),
                                f"Reviewed body source pin failed for {name}")
                self.assertFalse(reviewed_creature(
                    deck,name,dict(row,oracle_id="unverified")))

    def test_new_utility_parameters_fail_closed(self):
        for options in (
            {"operation":"draw","draw_count":0},
            {"operation":"draw","draw_count":8},
            {"operation":"draw","life_loss_after":-1},
            {"operation":"draw","tap_count":2},
            {"operation":"draw","tapped_subtype":"Zombie"},
            {"operation":"drain_opponents","draw_count":2},
            {"operation":"exile_graveyard_token"},
        ):
            with self.subTest(options=options),self.assertRaises(ValueError):
                UtilityRule("id","excerpt","battlefield","{1}",
                            **options)


if __name__=="__main__":
    unittest.main()
