"""End-to-end pinned M3 bounded actions on the actual IndexedKernel."""
import unittest

from commander_sim.early_game_runner import run_bounded_early_game


class BoundedEarlyGameTests(unittest.TestCase):
    def test_wretched_ranks_deterministic_zone_based_turns(self):
        a = run_bounded_early_game("wretched_ranks", seed=18, turns=6)
        b = run_bounded_early_game("wretched_ranks", seed=18, turns=6)
        self.assertEqual(a, b)
        self.assertEqual(a["mode"], "bounded_authoritative_early_actions")
        self.assertEqual(len(a["state_snapshots"]), 6)
        self.assertEqual([x["turn"] for x in a["events"]], list(range(1, 7)))
        self.assertEqual(a["deck_intelligence"]["automatic"]["source"],
                         "authoritative_printed_board_features")
        self.assertNotIn("win_rate", a)

    def test_magnus_premium_uses_same_shared_runner(self):
        result = run_bounded_early_game("magnus_premium", seed=17, turns=6)
        self.assertEqual(result["commander"], "Magnus the Red")
        self.assertEqual(len(result["state_snapshots"]), 6)
        self.assertTrue(all(state["source"] == "authoritative_game"
                            for state in result["state_snapshots"]))
        self.assertIn("combat", result["limits"])
        self.assertIn("opponent", result["limits"])

    def test_creature_casts_have_actual_source_and_resolution_events(self):
        # Sweep reproducible random hands; a reviewed subset must actually cast.
        plays = []
        for seed in range(12):
            result = run_bounded_early_game("wretched_ranks", seed=seed, turns=6)
            for turn in result["events"]:
                events = turn["events"]
                casts = [event for event in events if event["type"] == "creature_cast"]
                resolutions = [event for event in events if event["type"] == "creature_resolved"]
                self.assertEqual(len(casts), len(resolutions))
                for cast in casts:
                    self.assertTrue(cast["source_object_ids"])
                    self.assertEqual(cast["fidelity"], "limited_generic_cast")
                plays.extend(casts)
        self.assertGreater(len(plays), 0)

    def test_no_unsupported_casts_and_all_100_cards_remain_in_zones(self):
        for deck in ("wretched_ranks", "magnus_premium", "magnus_budget"):
            report = run_bounded_early_game(deck, seed=3, turns=6)
            for turn, state in zip(report["events"], report["state_snapshots"]):
                total = (turn["library_size"] + turn["hand_size"]
                         + len(state["battlefield"])
                         + len(state["graveyard"]) + 1)  # commander
                self.assertEqual(total, 100)
                self.assertTrue(all(event["type"] in {
                    "draw", "untap", "land_play", "creature_cast", "creature_resolved",
                    "artifact_cast", "artifact_resolved",
                    "tutor_cast", "tutor_resolved",
                    "token_spell_cast", "token_spell_resolved",
                    "reviewed_trigger_resolved", "reviewed_phase_resolved",
                    "enchantment_cast", "enchantment_resolved",
                    "reviewed_sacrifice_activated", "reviewed_enter_resolved",
                } for event in turn["events"]))

    def test_magnus_reviewed_tutors_pay_and_move_actual_cards(self):
        seen=[]
        for seed in range(12):
            run=run_bounded_early_game("magnus_premium",seed=seed,turns=6)
            for turn in run["events"]:
                casts=[event for event in turn["events"] if event["type"]=="tutor_cast"]
                resolved=[event for event in turn["events"] if event["type"]=="tutor_resolved"]
                self.assertEqual(len(casts),len(resolved))
                for cast,answer in zip(casts,resolved):
                    self.assertEqual(cast["card"],answer["card"])
                    self.assertEqual(cast["fidelity"],"bounded_reviewed_search")
                    self.assertIn(answer["destination"],{"hand","library_top"})
                    self.assertTrue(cast["source_object_ids"])
                seen.extend(resolved)
        self.assertGreater(len(seen),0)

    def test_tutor_seed_replays_keep_physical_zone_conservation(self):
        for seed in (0,3,8):
            a=run_bounded_early_game("magnus_budget",seed=seed,turns=6)
            b=run_bounded_early_game("magnus_budget",seed=seed,turns=6)
            self.assertEqual(a,b)
            for turn,state in zip(a["events"],a["state_snapshots"]):
                self.assertEqual(
                    turn["library_size"]+turn["hand_size"]+len(state["battlefield"])
                    +len(state["graveyard"])+1,100)
            self.assertNotIn("win_rate",a)

    def test_all_six_pinned_decks_share_reviewed_land_rock_runner(self):
        for deck in ("magnus_premium","magnus_budget","wretched_ranks",
                     "mortarion_current","mortarion_ideal","necron_dynasties"):
            with self.subTest(deck=deck):
                run=run_bounded_early_game(deck,seed=4,turns=4)
                self.assertEqual(len(run["state_snapshots"]),4)
                self.assertEqual(run["deck_key"],deck)
                self.assertNotIn("win_rate",run)
                for row,state in zip(run["events"],run["state_snapshots"]):
                    self.assertEqual(row["hand_size"]+row["library_size"]
                        +len(state["battlefield"])+len(state["graveyard"])+1,100)
                # A named creature only casts when its whole entry/cast is
                # independently reviewed, including the Necron Szeras slice.
                for turn in run["events"]:
                    for event in turn["events"]:
                        if event["type"] == "reviewed_enter_resolved":
                            self.assertIn(event["card"], {
                                "Bastion of Remembrance", "Grave Titan",
                                "Marionette Apprentice"})
                            self.assertEqual(event["fidelity"],
                                             "bounded_no_opponent_priority")
                            self.assertGreater(len(event["created_token_ids"]), 0)
                self.assertTrue(all(event["card"]!="Unsupported Invented Card"
                    for turn in run["events"] for event in turn["events"]
                    if event["type"]=="creature_cast"))

    def test_reviewed_token_spells_create_physical_objects_not_false_mana(self):
        created=[]
        for seed in range(16):
            report=run_bounded_early_game("magnus_premium",seed=seed,turns=6)
            for turn,state in zip(report["events"],report["state_snapshots"]):
                casts=[x for x in turn["events"] if x["type"]=="token_spell_cast"]
                resolved=[x for x in turn["events"] if x["type"]=="token_spell_resolved"]
                self.assertEqual(len(casts),len(resolved))
                for event in resolved:
                    self.assertEqual(event["created_token_count"],
                                     len(event["created_token_ids"]))
                    self.assertGreater(event["created_token_count"],0)
                    self.assertEqual(event["fidelity"],"bounded_reviewed_token_effect")
                created.extend(resolved)
                self.assertEqual(
                    turn["hand_size"]+turn["library_size"]+
                    len(state["battlefield"])+len(state["graveyard"])+1,100)
        self.assertGreater(len(created),0)

    def test_bounded_spell_triggers_have_authoritative_sources_and_outputs(self):
        for seed in range(12):
            report=run_bounded_early_game("magnus_premium",seed=seed,turns=6)
            for turn,state in zip(report["events"],report["state_snapshots"]):
                for event in turn["events"]:
                    if event["type"]!="reviewed_trigger_resolved":
                        continue
                    self.assertIn(event["source"],
                        {"Young Pyromancer","Talrand, Sky Summoner",
                         "Archmage Emeritus","Storm-Kiln Artist"})
                    self.assertEqual(event["fidelity"],"bounded_no_opponent_priority")
                    self.assertTrue(event["created_token_ids"] or event["drawn_ids"])
                self.assertEqual(
                    turn["hand_size"]+turn["library_size"]+
                    len(state["battlefield"])+len(state["graveyard"])+1,100)

    def test_reviewed_phase_permanents_and_life_totals_share_kernel(self):
        for deck in ("wretched_ranks","mortarion_current","mortarion_ideal"):
            for seed in (0,2,4):
                run=run_bounded_early_game(deck,seed=seed,turns=6)
                self.assertEqual(set(run["life_totals"]),{0,1,2,3})
                self.assertEqual(len(run["events"]),6)
                for turn in run["events"]:
                    self.assertEqual(set(turn["life_totals"]),{0,1,2,3})
                    for event in turn["events"]:
                        if event["type"]=="reviewed_phase_resolved":
                            self.assertIn(event["phase"],{"upkeep","end_step"})
                            self.assertIn(event["source_object_id"],range(1,2000))
                            self.assertEqual(event["fidelity"],
                                             "bounded_no_opponent_priority")

    def test_invalid_deck_or_horizon_fails_closed(self):
        for key, turns in (("unsupported_deck", 6), ("wretched_ranks", 0),
                           ("wretched_ranks", 11)):
            with self.assertRaises(ValueError):
                run_bounded_early_game(key, turns=turns)


if __name__ == "__main__":
    unittest.main()
