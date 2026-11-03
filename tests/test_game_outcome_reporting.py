"""Four-seat life changes, modeled eliminations and UI outcome batch contracts."""
import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from commander_sim.early_game_runner import _load_live_kernel, run_bounded_early_game
from commander_sim.kernel_life import LifeChange, KernelLife
from commander_sim.opponent_stress import BoundedOpponentPressure
from commander_sim.outcome_reporting import LifeOutcomeRecorder
from tools.build_game_outcomes import generate, summarize_games, write_batch, FORMAT


class LifeOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.observer=LifeOutcomeRecorder({0:40,1:40,2:40,3:40},
                                           opponent_model=True)

    def record(self,round_id,*items):
        current=dict(self.observer.current)
        for seat,amount,kind,source in items:
            current[seat]+=amount if kind=="gain" else -amount
        return self.observer.record_round(round_id,
            [LifeChange(*item) for item in items],current)

    def test_ordered_life_events_preserve_damage_vs_loss_and_source_id(self):
        row=self.record(1,(1,4,"damage",71),(0,2,"loss",None),
                        (0,3,"gain",87))
        self.assertEqual(row["life_totals"],{0:41,1:36,2:40,3:40})
        self.assertEqual([r["delta"] for r in row["life_changes"]],
                         [-4,-2,3])
        self.assertEqual([r["source_object_id"] for r in row["life_changes"]],
                         [71,None,87])
        self.assertEqual([r["kind"] for r in row["life_changes"]],
                         ["damage","loss","gain"])
        self.assertEqual(row["new_eliminations"],[])
        self.assertEqual(len(self.observer.history),2)

    def test_win_only_after_all_three_modeled_opponents_reach_zero(self):
        first=self.record(1,(1,40,"loss",9),(2,40,"damage",8))
        self.assertEqual(self.observer.outcome(requested_rounds=10)["status"],
                         "unresolved")
        self.assertEqual(first["alive_seats"],[0,3])
        last=self.record(2,(3,41,"damage",7))
        result=self.observer.outcome(requested_rounds=10)
        self.assertEqual((result["status"],result["winner_seat"]),
                         ("win",0))
        self.assertTrue(result["complete"])
        self.assertEqual([x["seat"] for x in result["eliminations"]],[1,2,3])
        self.assertEqual([x["round"] for x in result["eliminations"]],[1,1,2])
        self.assertEqual(len(last["new_eliminations"]),1)

    def test_pilot_defeat_is_loss_without_invented_winner(self):
        self.record(1,(0,40,"damage",None))
        result=self.observer.outcome(requested_rounds=20)
        self.assertEqual(result["status"],"loss")
        self.assertEqual(result["reason"],"pilot_life_zero")
        self.assertIsNone(result["winner_seat"])
        self.assertEqual(result["surviving_seats"],[1,2,3])

    def test_simultaneous_zero_life_is_draw(self):
        self.record(1,*[(s,40,"loss",None) for s in range(4)])
        result=self.observer.outcome(requested_rounds=30)
        self.assertEqual(result["status"],"draw")
        self.assertIsNone(result["winner_seat"])
        self.assertTrue(result["complete"])

    def test_surviving_pilot_and_opponents_at_horizon_is_unresolved(self):
        self.record(1,(1,3,"loss",None))
        result=self.observer.outcome(requested_rounds=1)
        self.assertEqual(result["status"],"unresolved")
        self.assertEqual(result["reason"],"round_limit")
        self.assertFalse(result["complete"])

    def test_goldfish_must_not_report_a_win_even_if_opponents_lose_life(self):
        recorder=LifeOutcomeRecorder({0:40,1:40,2:40,3:40})
        recorder.record_round(1,
            [LifeChange(s,40,"loss",None) for s in (1,2,3)],
            {0:40,1:0,2:0,3:0})
        result=recorder.outcome(requested_rounds=1)
        self.assertEqual(result["status"],"not_evaluated")
        self.assertIsNone(result["winner_seat"])
        self.assertEqual(result["reason"],"no_opponent_game_model")

    def test_later_life_gain_does_not_restore_eliminated_seat(self):
        self.record(1,(2,40,"damage",111))
        second=self.record(2,(2,50,"gain",222))
        self.assertNotIn(2,second["alive_seats"])
        result=self.observer.outcome(requested_rounds=20)
        self.assertEqual(result["status"],"unresolved")
        self.assertEqual(len(result["post_elimination_life_effects"]),1)
        self.assertEqual(result["post_elimination_life_effects"][0]["after"],50)

    def test_reject_broken_ledger_and_invalid_round_numbers(self):
        with self.assertRaises(AssertionError):
            self.observer.record_round(1,[LifeChange(1,1,"damage",None)],
                                        {0:40,1:40,2:40,3:40})
        with self.assertRaises(ValueError):
            self.observer.record_round(2,[],dict(self.observer.current))
        with self.assertRaises(ValueError):
            LifeOutcomeRecorder({0:40,1:40,2:40})
        with self.assertRaises(ValueError):
            self.observer.outcome(requested_rounds=0)


class GameBatchTests(unittest.TestCase):
    @staticmethod
    def fake(deck_key, *, seed, turns, opponent_scenario, provisional_mode,
             pilot_style="adaptive"):
        rec=LifeOutcomeRecorder({0:40,1:40,2:40,3:40},opponent_model=True)
        if seed%3==0:
            change=[LifeChange(i,40,"damage",100+i) for i in (1,2,3)]
        elif seed%3==1:
            change=[LifeChange(0,40,"loss",None)]
        else:
            change=[LifeChange(1,5,"damage",22)]
        totals={i:40 for i in range(4)}
        for item in change:
            totals[item.seat]-=item.amount
        rec.record_round(1,change,totals)
        if seed%3==2:
            rec.record_round(2,[],totals)
        return {
            "deck_key":deck_key,"seed":seed,"deck_sha256":"test-sha",
            "mode":"bounded_three_opponent_pressure",
            "opponent_roles":{1:"aggro",2:"control",3:"value"},
            "outcome":rec.outcome(requested_rounds=turns),
            "completed_rounds":len(rec.history)-1,
            "life_history":rec.history,
            "events":[{"turn":i,"events":[]} for i in range(1,len(rec.history))],
            "state_snapshots":[{"turn":i} for i in range(1,len(rec.history))],
        }

    def test_separate_batch_contract_counts_wins_losses_and_censoring(self):
        result=generate("necron_dynasties",seeds=3,rounds=20,
                        runner=self.fake,examples=1)
        self.assertEqual(result["format"],FORMAT)
        self.assertEqual(result["requested_rounds"],20)
        self.assertFalse(result["outcomes_are_competitive_win_rates"])
        counts=result["summary"]["outcome_counts"]
        self.assertEqual((counts["win"],counts["loss"],counts["unresolved"]),
                         (1,1,1))
        self.assertEqual(result["summary"]["right_censored_games"],1)
        self.assertEqual(result["summary"]["median_rounds_to_modeled_terminal"],1)
        self.assertEqual(len(result["runs"]),3)
        self.assertEqual(len(result["example_replays"]),1)
        trend=result["summary"]["life_by_round"]
        self.assertEqual([r["observed_games"] for r in trend],[3,3,1])
        self.assertEqual(trend[0]["median_life"]["0"],40)
        self.assertEqual(trend[1]["alive_games"]["0"],2)
        self.assertNotIn("win_rate",result["summary"])

    def test_complete_observations_are_separate_from_ui_outcomes(self):
        def detailed(deck_key, **kw):
            record=self.fake(deck_key,**kw)
            record["mulligan"]={"opening_hand":["Swamp"]*6+["Blood Artist"],
                                "initial_hand":["Swamp"]*7,"taken":False}
            for i,turn in enumerate(record["events"]):
                turn["events"]=[{"type":"cast","card":"Blood Artist"}]
                turn["pilot_decisions"]=[{"role":"legal_cast","source":"scorer"}]
                turn["mana_payment_events"]=[]
                record["state_snapshots"][i]["hand"]=["Swamp"]
                record["state_snapshots"][i]["battlefield"]=["Blood Artist"]
            return record
        with TemporaryDirectory() as folder:
            source=Path(folder)/"outcome.json"
            archive=Path(folder)/"observations.jsonl"
            batch=write_batch(source,"necron_dynasties",seeds=3,rounds=20,
                              runner=detailed,observation_output=archive)
            observations=[json.loads(line) for line in archive.read_text().splitlines()]
            self.assertEqual(len(observations),3)
            self.assertEqual([x["seed"] for x in observations],[0,1,2])
            self.assertEqual(observations[0]["mulligan"]["opening_hand"][-1],
                             "Blood Artist")
            self.assertEqual(observations[0]["turn_records"][0]["events"][0]["card"],
                             "Blood Artist")
            self.assertEqual(observations[0]["state_snapshots"][0]["hand"],
                             ["Swamp"])
            self.assertEqual(len(batch["runs"]),3)
            self.assertNotIn("turn_records",batch["runs"][0])
            self.assertEqual(batch["runs"][0]["opening_hand"][-1],"Blood Artist")
            self.assertEqual(batch["runs"][0]["ui_observations"][0]["hand"],["Swamp"])
            self.assertTrue(source.is_file())

    def test_observation_export_fails_closed_if_runner_did_not_record_hand(self):
        with TemporaryDirectory() as folder:
            source=Path(folder)/"outcome.json"
            archive=Path(folder)/"observations.jsonl"
            with self.assertRaisesRegex(ValueError,"authoritative"):
                write_batch(source,"necron_dynasties",seeds=2,rounds=20,
                            runner=self.fake,observation_output=archive)
            self.assertFalse(source.exists())
            self.assertFalse(archive.exists())

    def test_batch_runtime_failure_identifies_exact_seed_and_cohort(self):
        def faulty(deck_key, **kwargs):
            if kwargs["seed"]==2:
                raise ValueError("inconsistent reviewed interaction")
            return self.fake(deck_key,**kwargs)
        with self.assertRaisesRegex(
                RuntimeError,r"deck=necron_dynasties scenario=random seed=2 rounds=20"):
            generate("necron_dynasties",seeds=3,rounds=20,runner=faulty)

    def test_batch_invalid_configuration_fails_closed(self):
        for kwargs in ({"rounds":31},{"seeds":0},{"scenario":"real_decks"},
                       {"examples":4},{"start_seed":-1}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                generate("wretched_ranks",runner=self.fake,**kwargs)
        with self.assertRaises(ValueError):
            generate("unknown",runner=self.fake)

    def test_batch_survival_denominator_only_counts_observed_rounds(self):
        result=generate("necron_dynasties",seeds=6,rounds=20,runner=self.fake)
        trend=result["summary"]["life_by_round"]
        self.assertEqual([row["observed_games"] for row in trend],[6,6,2])
        self.assertEqual(trend[-1]["round"],2)

    def test_longer_goldfish_simulation_preserves_four_seats_but_no_outcome(self):
        run=run_bounded_early_game("wretched_ranks",seed=2,turns=12)
        self.assertEqual(run["completed_rounds"],12)
        self.assertEqual(len(run["events"]),12)
        self.assertEqual(len(run["life_history"]),13)
        self.assertEqual(run["outcome"]["status"],"not_evaluated")
        self.assertEqual(run["outcome"]["requested_rounds"],12)
        for index,row in enumerate(run["events"],start=1):
            self.assertEqual(len(row["life_totals"]),4)
            self.assertEqual(row["life_totals"],
                             run["life_history"][index]["life_totals"])
            self.assertEqual(row["life_changes"],
                             run["life_history"][index]["life_changes"])
        self.assertNotIn("win_rate",run)

    def test_longer_abstract_game_has_outcome_and_card_conservation(self):
        run=run_bounded_early_game(
            "mortarion_physical_final",seed=3,turns=12,
            opponent_scenario="balanced")
        self.assertEqual(run["outcome"]["requested_rounds"],12)
        self.assertEqual(run["outcome"]["completed_rounds"],
                         len(run["events"]))
        self.assertEqual(len(run["life_history"]),len(run["events"])+1)
        self.assertEqual(run["outcome"]["fidelity"],
                         "abstract_opponent_pressure_not_real_decks")
        self.assertIn(run["outcome"]["status"],
                      {"win","loss","draw","unresolved"})
        if run["outcome"]["status"] in {"win","loss","draw"}:
            self.assertLessEqual(run["completed_rounds"],12)


class EliminatedOpponentsTests(unittest.TestCase):
    def test_opponent_with_zero_life_cannot_act_and_leaves_kernel(self):
        K,Z,C=_load_live_kernel()
        kernel=K()
        zones=Z(kernel,seed=71)
        life=KernelLife(kernel)
        pressure=BoundedOpponentPressure(
            zones,life,{},None,None,C,
            seed=2,scenario="aggressive")
        self.assertGreater(len(zones.ids(1,"library")),0)
        life.lose(1,40)
        events=pressure.advance(1)
        self.assertTrue(all(obj.owner!=1 for obj in kernel.objects.values()))
        self.assertTrue(any(x.operation=="life_zero" and x.seat==1
                            for x in events))
        self.assertFalse(any(x.seat==1 and x.operation!="life_zero"
                             for x in events))
        self.assertEqual(pressure._board(1),[])
        self.assertTrue(zones.assert_consistent())


if __name__=="__main__":
    unittest.main()
