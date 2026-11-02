"""Physical-kernel verification of reusable Mortarion death triggers."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_death_effects import ReviewedDeathEngine,capture_battlefield

class MortarionDeathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES if f.key=="mortarion_physical_final")
        cls.catalog={r["deck_name"]:r["card"] for r in json.loads(f.snapshot_path.read_text())["cards"]}
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=14)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.engine=ReviewedDeathEngine(self.zones,self.life,self.catalog)
    def add(self,name,types=("creature",),controller=0,zone="battlefield"):
        raw=self.catalog.get(name,{})
        return self.zones.add(self.C(raw.get("oracle_id","synthetic:"+name),
                              name,frozenset(types),coverage="approx"),controller,zone)
    def kill(self,oid):
        before=capture_battlefield(self.kernel)
        mark=len(self.kernel.moves)
        self.zones.move(oid,"graveyard","sacrifice")
        return self.engine.resolve_deaths(before,move_index=mark,turn=1)
    def test_blood_artist_drains_one_player_not_every_opponent(self):
        self.add("Blood Artist")
        body=self.add("Test Victim")
        resolutions=self.kill(body)
        self.assertEqual([(x.source_name,x.operation) for x in resolutions],
                         [("Blood Artist","target_drain_gain")])
        self.assertEqual([self.life.total(i) for i in range(4)],[41,39,40,40])
    def test_shambling_ghast_uses_generic_treasure_token_effect(self):
        ghast=self.add("Shambling Ghast")
        resolutions=self.kill(ghast)
        self.assertEqual(len(resolutions),1)
        self.assertEqual(resolutions[0].operation,"treasure")
        self.assertEqual(len([o for o in self.kernel.on_battlefield()
                              if o.token and o.card.name=="Treasure"]),1)
    def test_solemn_draws_on_death(self):
        solemn=self.add("Solemn Simulacrum",("artifact","creature"))
        self.add("Library filler",("instant",),zone="library")
        res=self.kill(solemn)
        self.assertEqual(len(res),1)
        self.assertEqual(len(res[0].drawn_ids),1)
    def test_syr_konrad_uses_damage_event_for_other_creature(self):
        self.add("Syr Konrad, the Grim")
        victim=self.add("Victim")
        self.kill(victim)
        self.assertEqual([self.life.total(i) for i in range(4)],[40,39,39,39])
        self.assertEqual([e.kind for e in self.kernel.life_changes],["damage"]*3)
        self.assertTrue(self.zones.assert_consistent())
if __name__=="__main__":unittest.main()
