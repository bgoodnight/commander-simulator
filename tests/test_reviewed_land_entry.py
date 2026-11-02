"""Reviewed special lands reuse physical mana/zone entry operations."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_lands import reviewed_land
from commander_sim.reviewed_land_entry import resolve_land_entry

class MortarionLandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES if f.key=="mortarion_physical_final")
        cls.catalog={r["deck_name"]:r["card"] for r in
                     json.loads(f.snapshot_path.read_text())["cards"]}
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=21)
        self.C=C
        self.life=KernelLife(self.kernel)
    def add(self,name,zone="battlefield",seat=0,types=None):
        raw=self.catalog.get(name,{})
        if types is None:types=("land",) if "Land" in raw.get("type_line","") else ("creature",)
        return self.zones.add(self.C(raw.get("oracle_id","test:"+name),name,
             frozenset(types),coverage="approx"),seat,zone)
    def test_five_utility_lands_are_mana_source_pinned(self):
        for n, color, tapped in [
            ("Barren Moor","B",True),("Bojuka Bog","B",True),
            ("Leechridden Swamp","B",True),("Mortuary Mire","B",True),
            ("War Room","C",False)]:
            rule=reviewed_land(n,self.catalog[n],frozenset({"B"}))
            self.assertIsNotNone(rule,n)
            self.assertEqual(rule.modes(frozenset({"B"}))[0].output,(color,))
            self.assertEqual(rule.enters_tapped(0),tapped)
    def test_bojuka_bog_exiles_real_opponent_graveyard(self):
        bog=self.add("Bojuka Bog")
        card=self.add("Graveyard card",seat=1,zone="graveyard")
        out=resolve_land_entry(self.zones,self.life,bog,self.catalog,target_seat=1)
        self.assertEqual(len(out.moved_ids),1)
        self.assertEqual(len(self.zones.ids(1,"graveyard")),0)
        self.assertEqual(len(self.zones.ids(1,"exile")),1)
        self.assertTrue(self.zones.assert_consistent())
    def test_mortuary_mire_puts_creature_on_top_of_library(self):
        mire=self.add("Mortuary Mire")
        creature=self.add("Grave creature",zone="graveyard")
        out=resolve_land_entry(self.zones,self.life,mire,self.catalog,
                               target_creature_id=creature)
        self.assertEqual(len(out.moved_ids),1)
        self.assertEqual(self.zones.ids(0,"library")[-1],out.moved_ids[0])
        self.assertTrue(self.zones.assert_consistent())
    def test_necron_hidden_grotto_surveille_uses_shared_library_action(self):
        from commander_sim.deck_fixtures import FIXTURES
        from commander_sim.reviewed_land_entry import reviewed_land_entry
        deck=next(f for f in FIXTURES if f.key=="necron_dynasties")
        card=next(item["card"] for item in
                  json.loads(deck.snapshot_path.read_text())["cards"]
                  if item["deck_name"]=="Hidden Grotto")
        self.catalog["Hidden Grotto"]=card
        land=self.add("Hidden Grotto",types=("land",))
        keep=self.add("Keep",zone="library",types=("land",))
        top=self.add("Top creature",zone="library",types=("creature",))
        out=resolve_land_entry(self.zones,self.life,land,self.catalog)
        self.assertEqual(out.operation,"surveil_one")
        self.assertEqual(out.library_steps[0]["kind"],"surveil")
        self.assertEqual(len(out.moved_ids),1)
        self.assertEqual(self.kernel.get(out.moved_ids[0]).zone,"graveyard")
        self.assertEqual(self.zones.ids(0,"library"),(keep,))
        self.assertTrue(self.zones.assert_consistent())
        tampered=dict(card,oracle_text=card["oracle_text"]+" Changed.")
        self.assertIsNone(reviewed_land_entry("Hidden Grotto",tampered))

if __name__=="__main__":unittest.main()
