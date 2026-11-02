"""Real-zone three-opponent pressure; does not assert full multiplayer rules."""
import json
import unittest

from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel, run_bounded_early_game
from commander_sim.kernel_life import KernelLife
from commander_sim.opponent_stress import BoundedOpponentPressure
from commander_sim.reviewed_death_effects import ReviewedDeathEngine
from commander_sim.reviewed_phase_effects import ReviewedPhaseEngine


class OpponentPressureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture=next(f for f in EXPERIMENTAL_FIXTURES
                     if f.key=="mortarion_physical_final")
        cls.catalog={entry["deck_name"]:entry["card"] for entry in
            json.loads(fixture.snapshot_path.read_text())["cards"]}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=8)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.death=ReviewedDeathEngine(self.zones,self.life,self.catalog)
        self.phase=ReviewedPhaseEngine(self.zones,self.life,self.catalog)

    def stress(self,scenario="balanced",seed=1):
        return BoundedOpponentPressure(
            self.zones,self.life,self.catalog,self.death,self.phase,self.C,
            scenario=scenario,seed=seed)

    def test_opponent_roles_shuffled_but_pinned_to_three_real_seats(self):
        adversary=self.stress(seed=1)
        self.assertEqual(set(adversary.roles),{1,2,3})
        self.assertEqual(set(adversary.roles.values()),{"aggro","control","value"})
        result=adversary.advance(1)
        self.assertTrue(any(x.operation=="abstract_creature" for x in result))
        self.assertTrue(self.zones.assert_consistent())
        self.assertTrue(all(o.token for o in self.kernel.objects.values()))

    def test_opponent_upkeeps_trigger_real_reviewed_ophiomancer(self):
        raw=self.catalog["Ophiomancer"]
        self.zones.add(self.C(raw["oracle_id"],"Ophiomancer",
                         frozenset({"creature"}),coverage="approx"),
                         0,"battlefield")
        r=self.stress().advance(1)
        self.assertEqual(sum(x.operation=="reviewed_opponent_upkeep"
                             for x in r),1)
        snakes=[o for o in self.kernel.on_battlefield()
                if o.card.name=="Snake" and o.controller==0]
        self.assertEqual(len(snakes),1)

    def test_pressure_exile_does_not_create_false_death_events(self):
        raw=self.catalog["Mortarion, Daemon Primarch"]
        commander=self.zones.add(self.C(raw["oracle_id"],
            "Mortarion, Daemon Primarch",frozenset({"creature"}),
            supertypes=frozenset({"commander"}),coverage="approx"),
            0,"battlefield")
        adv=self.stress(scenario="control",seed=4)
        for turn in range(1,10):
            adv.advance(turn)
        if any(x.operation=="abstract_exile" and x.object_id==commander
               for x in adv.events):
            self.assertFalse(any(x.name=="dies" and x.source_id==commander
                                 for x in self.kernel.events))
        self.assertTrue(self.zones.assert_consistent())

    def test_unsupported_opponent_scenario_fails_closed(self):
        with self.assertRaises(ValueError):
            self.stress("infinite_cheating")

    def test_bounded_physical_mortarion_accepts_seeded_opponent_stress(self):
        r=run_bounded_early_game("mortarion_physical_final",
                                 seed=3,turns=4,opponent_scenario="balanced")
        self.assertEqual(r["opponent_scenario"],"balanced")
        self.assertTrue(1<=r["completed_turns"]<=4)
        self.assertEqual(len(r["opponent_roles"]),3)
        self.assertTrue(any(e["type"].startswith("opponent_")
               for turn in r["events"] for e in turn["events"]))


if __name__=="__main__":
    unittest.main()
