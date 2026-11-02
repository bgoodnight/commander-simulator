"""Source-reviewed token-to-mana choices must improve actual X payoff."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_token_spells import TokenBlueprint,create_reviewed_token_batches
from commander_sim.resource_pilot import choose_end_step_token_mana

class EndStepResourcePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture=next(f for f in EXPERIMENTAL_FIXTURES if f.key=="mortarion_physical_final")
        cls.catalog={r["deck_name"]:r["card"] for r
                     in json.loads(fixture.snapshot_path.read_text())["cards"]}
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=42)
        self.Card=C
        self.life=KernelLife(self.kernel)
        self.mana=TemplateManaService(self.kernel,self.catalog,
                                      frozenset({"B"}),zones=self.zones)
    def add(self,name,types):
        raw=self.catalog[name]
        return self.zones.add(self.Card(raw["oracle_id"],name,
            frozenset(types),coverage="approx"),0,"battlefield")
    def token(self):
        token=TokenBlueprint("Test creature",frozenset({"creature"}),
                             frozenset({"Astartes"}),frozenset({"B"}),2,2)
        return create_reviewed_token_batches(self.zones,0,(token,))[0]
    def choose(self,start=0):
        return choose_end_step_token_mana(
            self.zones,0,self.life,self.mana,self.catalog,
            life_start_index=start)
    def test_one_sacrifice_is_recommended_if_it_increases_x_by_two(self):
        self.add("Mortarion, Daemon Primarch",("creature",))
        altar=self.add("Ashnod's Altar",("artifact",))
        victim=self.token()
        self.life.lose(0,4)
        self.assertEqual(self.choose(),(altar,victim))
    def test_no_sacrifice_if_life_lost_caps_x_at_one(self):
        self.add("Mortarion, Daemon Primarch",("creature",))
        self.add("Ashnod's Altar",("artifact",))
        self.token()
        self.life.lose(0,1)
        self.assertIsNone(self.choose())
    def test_no_sacrifice_if_enough_mana_or_no_end_step_payoff(self):
        self.add("Mortarion, Daemon Primarch",("creature",))
        self.add("Ashnod's Altar",("artifact",))
        self.token()
        for _ in range(4):
            self.add("Swamp",("land",))
        self.life.lose(0,4)
        self.assertIsNone(self.choose())
if __name__=="__main__":
    unittest.main()
