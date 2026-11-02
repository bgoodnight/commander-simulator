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
        self.assertTrue(any(o.owner in {1,2,3} and not o.token
                            and o.zone=="library" for o in self.kernel.objects.values()))

    def test_opponent_upkeeps_trigger_real_reviewed_ophiomancer(self):
        raw=self.catalog["Ophiomancer"]
        self.zones.add(self.C(raw["oracle_id"],"Ophiomancer",
                         frozenset({"creature"}),
                         base_power=2,base_toughness=2,coverage="approx"),
                         0,"battlefield")
        r=self.stress().advance(1)
        self.assertEqual(sum(x.operation=="reviewed_opponent_upkeep"
                             and x.amount>0 for x in r),1)
        self.assertEqual(sum(x.operation=="reviewed_opponent_upkeep"
                             for x in r),3)
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

    def test_opponent_attack_uses_real_blocker_not_unblocked_proxy(self):
        defender=self.zones.add(self.C(
            "test:defender","Guard",frozenset({"creature"}),
            base_power=3,base_toughness=4,coverage="approx"),
            0,"battlefield")
        adv=self.stress("aggressive",seed=7)
        # A prior-turn creature can attack; newly spawned ones cannot.
        attacker=self.zones.add(self.C("test:attacker","Attacker",
            frozenset({"creature"}),base_power=2,base_toughness=2,
            coverage="approx"),1,"battlefield",token=True)
        adv._born[attacker]=0
        before=self.life.total(0)
        adv._combat(1,"aggro",turn=1,defender=0)
        self.assertEqual(self.life.total(0),before)
        self.assertTrue(any(x.operation=="abstract_blocked_combat"
                            and x.object_id==attacker for x in adv.events))
        self.assertIn(defender,self.kernel.objects)
        self.assertNotIn(attacker,self.kernel.objects)
        self.assertTrue(self.zones.assert_consistent())

    def test_negative_power_blocker_deals_zero_combat_damage(self):
        # A -2/4 creature can still block but must not submit -2 damage
        # to the shared kernel. This was uncovered by long Mortarion runs
        # containing signed creature-power modifiers.
        blocker=self.zones.add(self.C(
            "test:negative-power","Weakened Blocker",frozenset({"creature"}),
            base_power=-2,base_toughness=4,coverage="approx"),
            0,"battlefield")
        opponent=self.stress("aggressive",seed=7)
        attacker=self.zones.add(self.C(
            "test:ordinary-attacker","Ordinary Attacker",frozenset({"creature"}),
            base_power=2,base_toughness=2,coverage="approx"),
            1,"battlefield",token=True)
        opponent._born[attacker]=0
        before=self.life.total(0)
        opponent._combat(1,"aggro",turn=1,defender=0)
        self.assertEqual(self.life.total(0),before)
        self.assertIn(blocker,self.kernel.objects)
        self.assertIn(attacker,self.kernel.objects)
        self.assertEqual(self.kernel.get(attacker).damage_marked,0)
        self.assertEqual(self.kernel.get(blocker).damage_marked,2)
        self.assertTrue(self.zones.assert_consistent())

    def test_control_opponent_uses_capable_attacker_not_oldest(self):
        adv=self.stress("control",seed=4)
        weak=self.zones.add(self.C(
            "test:weak","Older Weak Body",frozenset({"creature"}),
            base_power=1,base_toughness=1,coverage="approx"),
            1,"battlefield",token=True)
        strong=self.zones.add(self.C(
            "test:strong","Later Flying Body",frozenset({"creature"}),
            base_power=4,base_toughness=4,
            keywords=frozenset({"flying"}),coverage="approx"),
            1,"battlefield",token=True)
        adv._born[weak]=adv._born[strong]=0
        adv._combat(1,"control",turn=1,defender=0)
        attacks=[x for x in adv.events
                 if x.operation=="abstract_unblocked_damage"]
        self.assertEqual(len(attacks),1)
        self.assertEqual(attacks[0].object_id,strong)
        self.assertTrue(self.zones.assert_consistent())

    def test_player_combat_posture_changes_attacks_without_changing_legality(self):
        for style,expected in (("tempo",4),("conservative",2)):
            with self.subTest(style=style):
                self.setUp()
                adv=self.stress("balanced",seed=3)
                ready=[]
                for i in range(5):
                    ready.append(self.zones.add(self.C(
                        "test:body:"+str(i),"Friendly "+str(i),
                        frozenset({"creature"}),base_power=2,
                        base_toughness=2,coverage="approx"),
                        0,"battlefield",token=True))
                outcome=adv.player_combat(
                    2,beginning_creature_ids=tuple(ready),style=style)
                attacks=[x for x in outcome
                         if x.operation=="abstract_unblocked_damage"]
                self.assertEqual(len(attacks),expected)
                self.assertEqual(
                    adv.last_player_combat_decision["selected_attackers"],
                    expected)
                self.assertEqual(adv.last_player_combat_decision["style"],style)
                self.assertTrue(self.zones.assert_consistent())

    def test_deathtouch_block_kills_larger_attacker(self):
        self.zones.add(self.C("test:snake","Test Snake",
            frozenset({"creature"}),base_power=1,base_toughness=1,
            keywords=frozenset({"deathtouch"}),coverage="approx"),
            0,"battlefield")
        adv=self.stress("aggressive",seed=3)
        attacker=self.zones.add(self.C(
            "test:attacker","Attacker",frozenset({"creature"}),
            base_power=2,base_toughness=2,coverage="approx"),
            1,"battlefield",token=True)
        adv._born[attacker]=0
        adv._combat(1,"aggro",turn=1,defender=0)
        self.assertNotIn(attacker,self.kernel.objects)
        self.assertTrue(self.zones.assert_consistent())


    def test_target_priority_not_fixed_on_seat_zero(self):
        # In symmetric worlds every non-actor seat must be targetable.
        picked={0:0,2:0,3:0}
        for seed in range(90):
            self.setUp()  # independent board; do not accumulate fake libraries
            a=self.stress("balanced",seed=seed)
            actor=1
            for _ in range(4):
                seat=a._target_seat(actor,"control")
                picked[seat]+=1
        self.assertTrue(all(picked[seat]>15 for seat in picked),picked)
        self.assertEqual(sum(picked.values()),360)

    def test_exile_target_can_be_another_opponent(self):
        body=self.zones.add(self.C("test:body","Other seat threat",
            frozenset({"creature"}),base_power=3,base_toughness=4,
            coverage="approx"),2,"battlefield")
        a=self.stress("control",seed=4)
        chosen=a._exile_one(1,3,"control")
        self.assertTrue(chosen)
        self.assertEqual(a.events[-1].target_seat,2)
        self.assertNotIn(body,self.kernel.objects)

    def test_removal_priority_favors_high_threat_across_seats(self):
        """A commander should compete globally, not lose a seat lottery."""
        selections={0:0,2:0,3:0}
        for seed in range(96):
            self.setUp()
            # Same large creature on each eligible seat; one extra
            # commander threat on seat 3, never seat zero.
            for seat in (0,2,3):
                self.zones.add(self.C(
                    "test:body:"+str(seat),"Comparable threat",
                    frozenset({"creature"}),base_power=3,base_toughness=3,
                    coverage="approx"),seat,"battlefield")
            self.zones.add(self.C(
                "test:leader","High-threat commander",
                frozenset({"creature"}),supertypes=frozenset({"commander"}),
                base_power=5,base_toughness=5,coverage="approx"),
                3,"battlefield")
            a=self.stress("control",seed=seed)
            self.assertTrue(a._exile_one(1,3,"control"))
            selections[a.events[-1].target_seat]+=1
        self.assertGreater(selections[3],selections[0],selections)
        self.assertGreater(selections[3],selections[2],selections)
        self.assertGreater(selections[0],0,selections)
        self.assertGreater(selections[2],0,selections)

    def test_removal_priority_is_not_fixed_on_physical_player_seat(self):
        """Symmetric permanent threats receive attention on all seats."""
        selections={0:0,2:0,3:0}
        for seed in range(96):
            self.setUp()
            for seat in (0,2,3):
                self.zones.add(self.C(
                    "test:threat:"+str(seat),"Equal threat",
                    frozenset({"creature"}),base_power=4,base_toughness=4,
                    coverage="approx"),seat,"battlefield")
            a=self.stress("control",seed=seed)
            self.assertTrue(a._exile_one(1,3,"control"))
            selections[a.events[-1].target_seat]+=1
        self.assertTrue(all(count>=12 for count in selections.values()),
                        selections)

    def test_unsupported_opponent_scenario_fails_closed(self):
        with self.assertRaises(ValueError):
            self.stress("infinite_cheating")

    def test_opponent_attacker_untaps_and_attacks_again_on_next_turn(self):
        adv=self.stress("aggressive",seed=3)
        aggro=next(seat for seat,role in adv.roles.items() if role=="aggro")
        adv._spawn(aggro,0,"aggro")
        attacker=adv.events[-1].object_id
        adv.advance(1)
        self.assertTrue(self.kernel.get(attacker).tapped)
        attacks=lambda:sum(x.operation in {
                            "abstract_unblocked_damage",
                            "abstract_blocked_combat"}
                          and x.object_id==attacker for x in adv.events)
        before=attacks()
        adv.advance(2)
        self.assertEqual(attacks(),before+1)
        self.assertTrue(self.zones.assert_consistent())

    def test_opponent_exile_uses_finite_interaction_budgets(self):
        body=self.zones.add(self.C("test:target","Durable Test Target",
            frozenset({"creature"}),base_power=2,base_toughness=9,
            coverage="approx"),0,"battlefield")
        adversary=self.stress("control",seed=2)
        for turn in range(1,11):
            adversary.advance(turn)
        spent={}
        for event in adversary.events:
            if event.operation=="abstract_exile":
                spent[event.seat]=spent.get(event.seat,0)+1
        for seat,role in adversary.roles.items():
            limit=2 if role=="control" else 1 if role=="value" else 0
            self.assertLessEqual(spent.get(seat,0),limit)
        self.assertTrue(self.zones.assert_consistent())

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
