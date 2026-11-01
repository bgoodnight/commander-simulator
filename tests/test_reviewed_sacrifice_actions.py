"""Reviewed sacrifice outlets reuse one physical cost/effect/death pipeline."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_death_effects import ReviewedDeathEngine
from commander_sim.reviewed_sacrifice_actions import (
    SACRIFICE_MODES, activate_reviewed_sacrifice)
from commander_sim.template_resources import TemplateManaService


class ReviewedSacrificeActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for fixture in FIXTURES:
            for row in json.loads(fixture.snapshot_path.read_text())["cards"]:
                cls.catalog.setdefault(row["deck_name"],row["card"])
        cls.catalog["Swamp"]={"type_line":"Basic Land — Swamp"}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=23)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.mana=TemplateManaService(self.kernel,self.catalog,
                                      frozenset({"B"}))
        self.deaths=ReviewedDeathEngine(self.zones,self.life,self.catalog)

    def add(self,name,*,types=("creature",),subtypes=(),power=2,toughness=2,
            controller=0,colors=None,zone="battlefield",oracle=None):
        card=self.catalog.get(name)
        return self.zones.add(self.C(
            oracle or (card["oracle_id"] if card and "oracle_id" in card else
                       "test:"+name),name,frozenset(types),
            subtypes=frozenset(subtypes),base_power=power,
            base_toughness=toughness,colors=(
                frozenset(colors) if colors is not None else None),
            coverage="approx"),controller,zone)

    def activate(self,source,victim,**kwargs):
        return activate_reviewed_sacrifice(
            self.zones,self.life,source,victim,self.catalog,
            mana_service=self.mana,death_engine=self.deaths,**kwargs)

    def test_ghoulcaller_gisa_sacrifices_one_creature_to_make_power_zombies(self):
        gisa=self.add("Ghoulcaller Gisa")
        victim=self.add("Victim",power=3)
        swamp=self.add("Swamp",types=("land",))
        outcome=self.activate(gisa,victim,tap_ready=True)
        self.assertEqual(outcome.operation,"zombies_by_power")
        self.assertEqual(len(outcome.token_ids),3)
        self.assertTrue(self.kernel.get(swamp).tapped)
        self.assertTrue(self.kernel.get(gisa).tapped)
        self.assertNotIn(victim,self.kernel.objects)
        self.assertTrue(all(self.kernel.get(x).card.name=="Zombie"
                            for x in outcome.token_ids))
        self.assertTrue(self.zones.assert_consistent())

    def test_gisa_unpaid_or_not_ready_does_not_sacrifice(self):
        gisa=self.add("Ghoulcaller Gisa")
        victim=self.add("Victim")
        with self.assertRaises(ValueError):
            self.activate(gisa,victim)
        self.assertIsNone(self.activate(gisa,victim,tap_ready=True))
        self.assertIn(victim,self.kernel.objects)
        self.assertFalse(self.kernel.get(gisa).tapped)

    def test_carrion_feeder_gets_counter_and_plunderer_sees_death(self):
        feeder=self.add("Carrion Feeder")
        self.add("Pitiless Plunderer")
        victim=self.add("Victim")
        out=self.activate(feeder,victim)
        self.assertEqual(out.operation,"self_counter")
        self.assertEqual(self.kernel.get(feeder).counters["+1/+1"],1)
        self.assertEqual(out.death_trigger_count,1)
        self.assertEqual(sum(o.token and o.card.name=="Treasure"
                             for o in self.kernel.on_battlefield()),1)

    def test_ayara_requires_other_black_creature_and_draws_card(self):
        ayara=self.add("Ayara, First of Locthwain")
        victim=self.add("Victim",colors={"B"})
        wrong=self.add("Wrong",colors={"U"})
        self.add("Draw target",types=("instant",),zone="library")
        with self.assertRaises(ValueError):
            self.activate(ayara,wrong,tap_ready=True)
        out=self.activate(ayara,victim,tap_ready=True)
        self.assertEqual(len(out.drawn_ids),1)
        self.assertEqual(len(self.zones.ids(0,"hand")),1)
        self.assertTrue(self.kernel.get(ayara).tapped)

    def test_ashnod_altar_floats_two_real_colorless(self):
        altar=self.add("Ashnod's Altar",types=("artifact",))
        victim=self.add("Victim")
        out=self.activate(altar,victim)
        self.assertEqual(out.mana_added,("C","C"))
        self.assertEqual(self.mana.floating(0)[5],2)
        self.assertTrue(self.zones.assert_consistent())

    def test_szeras_floats_black_equal_to_mana_value(self):
        source=self.add("Illuminor Szeras",types=("artifact","creature"))
        victim=self.add("Ghoulcaller Gisa",power=4)
        self.assertEqual(int(self.catalog["Ghoulcaller Gisa"]["cmc"]),5)
        out=self.activate(source,victim,tap_ready=True)
        self.assertEqual(len(out.mana_added),5)
        self.assertEqual(self.mana.floating(0)[2],5)

    def test_viscera_seer_and_woe_strider_reuse_same_scry(self):
        seer=self.add("Viscera Seer")
        victim=self.add("Victim")
        bottom=self.add("First",types=("sorcery",),zone="library")
        top=self.add("Second",types=("sorcery",),zone="library")
        out=self.activate(seer,victim,scry_to_bottom=True)
        self.assertEqual(out.scry_bottomed,(top,))
        self.assertEqual(self.zones.ids(0,"library"),(top,bottom))
        strider=self.add("Woe Strider")
        v2=self.add("Other")
        out2=self.activate(strider,v2,scry_to_bottom=False)
        self.assertEqual(out2.scry_bottomed,())
        self.assertTrue(self.zones.assert_consistent())

    def test_yawgmoth_pays_life_adds_minus_counter_and_draws(self):
        yawgmoth=self.add("Yawgmoth, Thran Physician")
        victim=self.add("Victim")
        target=self.add("Opponent",controller=1)
        self.add("Draw target",types=("instant",),zone="library")
        out=self.activate(yawgmoth,victim,target_id=target)
        self.assertEqual(out.operation,"wither_draw")
        self.assertEqual(self.life.total(0),39)
        self.assertEqual(self.kernel.get(target).counters["-1/-1"],1)
        self.assertEqual(len(out.drawn_ids),1)
        self.assertTrue(self.zones.assert_consistent())

    def test_unreviewed_source_and_illegal_target_cannot_pay_sacrifice(self):
        source=self.add("Yawgmoth, Thran Physician")
        victim=self.add("Victim")
        artifact=self.add("Artifact",types=("artifact",))
        self.add("Draw target",types=("instant",),zone="library")
        with self.assertRaises(ValueError):
            self.activate(source,victim,target_id=artifact)
        self.assertIn(victim,self.kernel.objects)
        self.assertEqual(self.life.total(0),40)
        fake=self.add("Carrion Feeder",oracle="unreviewed")
        with self.assertRaises(ValueError):
            self.activate(fake,victim)
        self.assertIn(victim,self.kernel.objects)

    def test_sacrifice_source_self_allowed_only_for_unrestricted_cost(self):
        source=self.add("Carrion Feeder")
        out=self.activate(source,source)
        self.assertNotIn(source,self.kernel.objects)
        self.assertEqual(out.operation,"self_counter")
        gisa=self.add("Ghoulcaller Gisa")
        self.add("Swamp",types=("land",))
        with self.assertRaises(ValueError):
            self.activate(gisa,gisa,tap_ready=True)
        self.assertIn(gisa,self.kernel.objects)

    def test_all_eight_named_modes_have_reviewed_oracle_sources(self):
        self.assertEqual(len(SACRIFICE_MODES),8)
        for name,mode in SACRIFICE_MODES.items():
            with self.subTest(name=name):
                row=self.catalog[name]
                self.assertEqual(row["oracle_id"],mode.oracle_id)
                self.assertIn(mode.excerpt,row["oracle_text"])


if __name__=="__main__":
    unittest.main()
