"""Reviewed flashback reuse and exile replacement over true physical zones."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.reviewed_flashback import (
    FLASHBACK,reviewed_flashback,cast_reviewed_flashback)
from commander_sim.template_resources import TemplateManaService


class ReviewedFlashbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for fixture in FIXTURES:
            for row in json.loads(fixture.snapshot_path.read_text())["cards"]:
                cls.catalog.setdefault(row["deck_name"],row["card"])
        for basic in ("Swamp","Mountain"):
            cls.catalog[basic]={"type_line":"Basic Land — "+basic}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=8)
        self.C=C
        self.mana=TemplateManaService(self.kernel,self.catalog,
            frozenset({"B","R"}))

    def add(self,name,zone,types=("sorcery",),card_id=None):
        card=self.catalog.get(name,{})
        return self.zones.add(self.C(
            card_id or card.get("oracle_id","test:"+name),
            name,frozenset(types),coverage="approx"),0,zone)

    def mana_lands(self,name,n):
        return [self.add(name,"battlefield",("land",)) for _ in range(n)]

    def cast(self,name):
        oid=self.add(name,"graveyard")
        return cast_reviewed_flashback(
            self.zones,0,oid,self.catalog,self.mana,sorcery_window=True)

    def test_strike_it_rich_casts_graveyard_card_and_exiles_source(self):
        self.mana_lands("Mountain",3)
        result=self.cast("Strike It Rich")
        self.assertEqual(len(result.mana_source_ids),3)
        self.assertEqual(len(result.created_token_ids),1)
        self.assertEqual(self.kernel.get(result.exiled_id).zone,"exile")
        self.assertEqual(self.kernel.get(result.created_token_ids[0]).card.name,
                         "Treasure")
        self.assertEqual(self.zones.ids(0,"stack"),())
        self.assertTrue(self.zones.assert_consistent())

    def test_moan_of_unhallowed_flashback_uses_zombie_blueprint(self):
        self.mana_lands("Swamp",7)
        result=self.cast("Moan of the Unhallowed")
        self.assertEqual(len(result.created_token_ids),2)
        self.assertTrue(all(self.kernel.get(x).card.name=="Zombie"
             for x in result.created_token_ids))
        self.assertTrue(self.zones.assert_consistent())

    def test_army_of_damned_flashback_makes_thirteen_tapped_zombies(self):
        self.mana_lands("Swamp",10)
        result=self.cast("Army of the Damned")
        self.assertEqual(len(result.created_token_ids),13)
        self.assertTrue(all(self.kernel.get(x).tapped
             for x in result.created_token_ids))
        self.assertTrue(self.zones.assert_consistent())

    def test_faithless_looting_reuses_real_draw_and_discard(self):
        self.mana_lands("Mountain",3)
        before=self.add("Draw One","library",("instant",))
        self.add("Draw Two","library",("sorcery",))
        result=self.cast("Faithless Looting")
        self.assertEqual(len(result.drawn_ids),2)
        self.assertEqual(len(result.discarded_old_ids),2)
        self.assertEqual(self.zones.ids(0,"hand"),())
        self.assertEqual(len(self.zones.ids(0,"graveyard")),2)
        self.assertEqual(self.kernel.get(result.exiled_id).zone,"exile")
        self.assertTrue(self.zones.assert_consistent())

    def test_countering_flashback_spell_exiles_instead_of_graveyard(self):
        self.mana_lands("Mountain",3)
        oid=self.add("Strike It Rich","graveyard")
        ticket=self.zones.cast(0,oid,reviewed_origin="graveyard",
                               exile_on_stack_exit=True)
        result=self.zones.counter(ticket)
        self.assertEqual(self.kernel.get(result).zone,"exile")
        self.assertEqual(self.zones.ids(0,"graveyard"),())
        self.assertFalse(self.kernel.flashback_pending)
        self.assertTrue(self.zones.assert_consistent())

    def test_flashback_requires_pinned_text_and_sorcery_window(self):
        self.mana_lands("Mountain",3)
        source=self.add("Strike It Rich","graveyard")
        with self.assertRaises(ValueError):
            cast_reviewed_flashback(self.zones,0,source,self.catalog,
                                     self.mana,sorcery_window=False)
        altered=dict(self.catalog)
        altered["Strike It Rich"]=dict(self.catalog["Strike It Rich"])
        altered["Strike It Rich"]["oracle_text"]="Create one token."
        with self.assertRaises(ValueError):
            cast_reviewed_flashback(self.zones,0,source,altered,
                                     self.mana,sorcery_window=True)
        self.assertIn(source,self.zones.ids(0,"graveyard"))

    def test_flashback_missing_mana_does_not_move_source(self):
        self.mana_lands("Swamp",1)
        old=self.add("Moan of the Unhallowed","graveyard")
        self.assertIsNone(cast_reviewed_flashback(
            self.zones,0,old,self.catalog,self.mana,sorcery_window=True))
        self.assertIn(old,self.zones.ids(0,"graveyard"))
        self.assertEqual(self.zones.ids(0,"stack"),())

    def test_four_supported_flashback_spell_ids_match_pinned_decks(self):
        self.assertEqual(len(FLASHBACK),4)
        for name,entry in FLASHBACK.items():
            with self.subTest(name=name):
                self.assertEqual(self.catalog[name]["oracle_id"],entry.oracle_id)
                self.assertEqual(reviewed_flashback(name,self.catalog[name]),entry)


if __name__=="__main__":
    unittest.main()
