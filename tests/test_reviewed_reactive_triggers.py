"""Physical token and life events compose into generic reactive triggers."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_token_spells import TokenBlueprint,create_reviewed_token_batches
from commander_sim.reviewed_reactive_triggers import ReactiveTriggerEngine

class ReactiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES if f.key=="mortarion_physical_final")
        cls.catalog={r["deck_name"]:r["card"] for r in
                     json.loads(f.snapshot_path.read_text())["cards"]}
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=19)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.events=ReactiveTriggerEngine(self.zones,self.life,self.catalog)
    def creature(self,name):
        raw=self.catalog[name]
        return self.zones.add(self.C(raw["oracle_id"],name,
                              frozenset({"creature"}),coverage="approx"),0)
    def token(self):
        blueprint=TokenBlueprint("Test token",frozenset({"creature"}),
                                 frozenset({"Zombie"}),frozenset({"B"}),1,1)
        return create_reviewed_token_batches(self.zones,0,(blueprint,))[0]
    def test_token_create_sacrifice_and_leave_trigger_distinctly(self):
        self.creature("Mirkwood Bats")
        self.creature("Nadier's Nightblade")
        tok=self.token()
        first=self.events.resolve()
        self.assertEqual([x.source_name for x in first],["Mirkwood Bats"])
        self.assertEqual([self.life.total(i) for i in range(4)],[40,39,39,39])
        self.zones.move(tok,"graveyard","sacrifice")
        second=self.events.resolve()
        self.assertEqual({x.source_name for x in second},
                         {"Mirkwood Bats","Nadier's Nightblade"})
        self.assertEqual([self.life.total(i) for i in range(4)],[41,37,37,37])
        self.assertEqual(self.events.resolve(),())
        self.assertTrue(self.zones.assert_consistent())
    def test_vito_responds_to_life_gain_once_per_change(self):
        self.creature("Vito, Thorn of the Dusk Rose")
        self.life.gain(0,4)
        out=self.events.resolve()
        self.assertEqual(len(out),1)
        self.assertEqual((self.life.total(0),self.life.total(1)),(44,36))
        self.assertEqual(self.events.resolve(),())
    def test_invalid_source_identity_not_registered(self):
        fake=self.C("bad-oracle","Mirkwood Bats",frozenset({"creature"}),
                    coverage="approx")
        self.zones.add(fake,0)
        self.token()
        self.assertEqual(self.events.resolve(),())
if __name__=="__main__": unittest.main()
