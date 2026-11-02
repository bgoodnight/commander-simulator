"""Generic physical command-zone casting and source-paid tax contracts."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_commander_cast import commander_cost,cast_commander

class CommanderCastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES if f.key=="mortarion_physical_final")
        cls.catalog={r["deck_name"]:r["card"] for r in
                     json.loads(f.snapshot_path.read_text())["cards"]}
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=31)
        self.C=C
        self.mana=TemplateManaService(self.kernel,self.catalog,
                                      frozenset({"B"}),zones=self.zones)
    def commander(self,oid=None):
        raw=self.catalog["Mortarion, Daemon Primarch"]
        return self.zones.add(self.C(oid or raw["oracle_id"],
            "Mortarion, Daemon Primarch",frozenset({"creature"}),
            supertypes=frozenset({"commander"}),coverage="approx"),
            0,"command")
    def lands(self,n):
        for _ in range(n):
            self.zones.add(self.C(self.catalog["Swamp"]["oracle_id"],
                "Swamp",frozenset({"land"}),coverage="approx"),0,"battlefield")
    def test_commander_source_cast_is_physical_and_taxed(self):
        oid=self.commander()
        self.lands(6)
        first=cast_commander(self.zones,0,oid,self.catalog,self.mana)
        self.assertIsNotNone(first)
        self.assertEqual(first.commander_tax,0)
        self.assertEqual(len(self.zones.ids(0,"command")),0)
        self.assertEqual(len(self.kernel.objects),7)
        new=self.zones.move(first.physical_id,"command","resolve")
        self.assertEqual(commander_cost(self.kernel,self.kernel.get(new),
                                        self.catalog),"{7}{B}")
        self.mana.clear()
        for obj in self.kernel.on_battlefield():
            obj.tapped=False
        self.lands(2)
        second=cast_commander(self.zones,0,new,self.catalog,self.mana)
        self.assertEqual(second.commander_tax,2)
        self.assertEqual(second.previous_casts,1)
        self.assertEqual(len(self.zones.ids(0,"command")),0)
        self.assertTrue(self.zones.assert_consistent())
    def test_bad_oracle_identity_refused(self):
        oid=self.commander(oid="bad-id")
        self.assertIsNone(commander_cost(self.kernel,self.kernel.get(oid),
                                         self.catalog))
        with self.assertRaises(ValueError):
            cast_commander(self.zones,0,oid,self.catalog,self.mana)
if __name__=="__main__":unittest.main()
