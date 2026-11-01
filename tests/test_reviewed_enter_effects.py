"""Real physically entered Necron/Gisa/Mortarion permanents share ETB operations."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_enter_effects import (
    ENTER_RULES,execute_reviewed_enter,reviewed_enter_rule)
from commander_sim.reviewed_death_effects import ReviewedDeathEngine


class ReviewedEnterEffectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for fixture in FIXTURES:
            for item in json.loads(fixture.snapshot_path.read_text())["cards"]:
                cls.catalog.setdefault(item["deck_name"],item["card"])

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=22)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.death=ReviewedDeathEngine(self.zones,self.life,self.catalog)

    def add(self,name,zone="battlefield",*,types=("creature",),seat=0,
            oracle=None):
        row=self.catalog.get(name,{})
        return self.zones.add(self.C(
            oracle or row.get("oracle_id","test:"+name),name,
            frozenset(types),coverage="approx"),seat,zone)

    def enter(self,name,from_zone="hand",*,types=("creature",),seat=0):
        old=self.add(name,from_zone,types=types,seat=seat)
        return self.zones.move(old,"battlefield","resolve")

    def resolve(self,source,**kw):
        return execute_reviewed_enter(self.zones,self.life,source,self.catalog,
            death_engine=self.death,**kw)

    def test_royal_warden_uses_two_tapped_black_artifact_necron_tokens(self):
        source=self.enter("Royal Warden",types=("artifact","creature"))
        result=self.resolve(source)
        self.assertEqual(len(result.token_ids),2)
        for token_id in result.token_ids:
            token=self.kernel.get(token_id)
            self.assertTrue(token.tapped)
            self.assertEqual(token.card.colors,frozenset({"B"}))
            self.assertEqual(token.types,frozenset({"artifact","creature"}))
            self.assertIn("Necron",token.subtypes)
        self.assertTrue(self.zones.assert_consistent())

    def test_triarch_only_draws_and_loses_when_enters_from_graveyard(self):
        self.add("First",zone="library",types=("instant",))
        self.add("Second",zone="library",types=("instant",))
        from_hand=self.enter("Triarch Praetorian",types=("artifact","creature"))
        self.assertIsNone(self.resolve(from_hand))
        from_grave=self.enter("Triarch Praetorian","graveyard",
                              types=("artifact","creature"))
        result=self.resolve(from_grave)
        self.assertEqual(len(result.drawn_ids),2)
        self.assertEqual(self.life.total(0),38)
        self.assertTrue(self.zones.assert_consistent())

    def test_canoptek_optional_exile_nonland_target_keeps_land(self):
        target=self.add("Enemy",seat=1)
        land=self.add("Enemy land",seat=1,types=("land",))
        source=self.enter("Canoptek Tomb Sentinel","graveyard",
                          types=("artifact","creature"))
        with self.assertRaises(ValueError):
            self.resolve(source,choice=land)
        result=self.resolve(source,choice=target)
        self.assertEqual(self.kernel.get(result.exiled_id).zone,"exile")
        self.assertIn(land,self.kernel.objects)
        self.assertTrue(self.zones.assert_consistent())

    def test_lokhust_requires_all_players_sacrifice_choices(self):
        opponent=self.add("Enemy",seat=1)
        source=self.enter("Lokhust Heavy Destroyer",
                          types=("artifact","creature"))
        with self.assertRaises(ValueError):
            self.resolve(source)
        outcome=self.resolve(source,choice={0:source,1:opponent},turn=1)
        self.assertEqual(len(outcome.sacrificed_ids),2)
        self.assertNotIn(source,self.kernel.objects)
        self.assertNotIn(opponent,self.kernel.objects)
        self.assertTrue(self.zones.assert_consistent())

    def test_bastion_and_grave_titan_reuse_token_emitter(self):
        bastion=self.enter("Bastion of Remembrance",types=("enchantment",))
        result=self.resolve(bastion)
        soldier=self.kernel.get(result.token_ids[0])
        self.assertEqual(soldier.card.colors,frozenset({"W"}))
        self.assertEqual(soldier.subtypes,frozenset({"Human","Soldier"}))
        titan=self.enter("Grave Titan")
        out=self.resolve(titan)
        self.assertEqual(len(out.token_ids),2)
        self.assertTrue(all(self.kernel.get(t).card.name=="Zombie"
                            for t in out.token_ids))

    def test_marionette_fabricate_mandatory_choice_counter_or_servo(self):
        source=self.enter("Marionette Apprentice")
        with self.assertRaises(ValueError):
            self.resolve(source)
        out=self.resolve(source,choice="counter")
        self.assertEqual(out.token_ids,())
        self.assertEqual(self.kernel.get(source).counters["+1/+1"],1)
        other=self.enter("Marionette Apprentice")
        alternative=self.resolve(other,choice="servo")
        self.assertEqual(len(alternative.token_ids),1)
        self.assertIn("artifact",self.kernel.get(
            alternative.token_ids[0]).types)

    def test_false_identity_never_receives_named_etb_ability(self):
        fake=self.add("Royal Warden",zone="hand",oracle="unreviewed",
                      types=("artifact","creature"))
        permanent=self.zones.move(fake,"battlefield","resolve")
        with self.assertRaises(ValueError):
            self.resolve(permanent)
        self.assertEqual(len(self.zones.ids(0,"battlefield")),1)

    def test_seven_oracle_reviewed_etb_registration_records_present(self):
        self.assertEqual(len(ENTER_RULES),7)
        for name,entry in ENTER_RULES.items():
            with self.subTest(card=name):
                self.assertEqual(self.catalog[name]["oracle_id"],entry.oracle_id)
                self.assertEqual(reviewed_enter_rule(
                    name,self.catalog[name]),entry)


if __name__=="__main__":
    unittest.main()
