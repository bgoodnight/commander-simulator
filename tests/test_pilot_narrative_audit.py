"""Regression tests for purely observational pilot narrative audits."""
import unittest

from tools.audit_pilot_narratives import (
    FORMAT,run_audit,summarize_run)


def fake_run(deck,*,seed,turns,opponent_scenario,pilot_style,
             provisional_mode):
    return {
        "deck_key":deck,"deck_sha256":"test-sha",
        "seed":seed,"opponent_scenario":opponent_scenario,
        "provisional_mode":provisional_mode,"pilot_style":pilot_style,
        "pilot_signals":{"nonland_cards":65},
        "completed_rounds":2,
        "outcome":{"status":"unresolved"},
        "life_totals":{0:35,1:40,2:40,3:40},
        "events":[
            {"turn":1,"events":[{"type":"draw","card":"X"},
                     {"type":"creature_cast","card":"Creature"}],
             "pilot_decisions":[{
                 "round":1,"kind":"creature","card":"Creature",
                 "source_object_id":10,"candidate_count":2,
                 "score":48,"role":"creature","factors":["base:creature"],
                 "personality":pilot_style,
                 "fidelity":"ordering_only_verified_legal_candidates"}],
             "resource_start":{"available_fixed_mana":2},
             "hand_size":6,"creature_count":1,"land_count":2,
             "unsupported_cards_in_hand":["Unknown Card"],
             "cleanup_discard_count":0,
             "life_totals":{0:40,1:40,2:40,3:40},
             "alive_seats":[0,1,2,3],"life_changes":[]},
            {"turn":2,"events":[{"type":"draw","card":"Y"}],
             "pilot_decisions":[],
             "resource_start":{"available_fixed_mana":2},
             "hand_size":6,"creature_count":1,"land_count":2,
             "unsupported_cards_in_hand":["A","B","C"],
             "cleanup_discard_count":0,
             "life_totals":{0:35,1:40,2:40,3:40},
             "alive_seats":[0,1,2,3],
             "life_changes":[{"seat":0,"delta":-5}]},
        ],
    }


class NarrativeAuditTests(unittest.TestCase):
    def test_observes_real_event_and_decision_counts_without_inference(self):
        run=fake_run("necron_dynasties",seed=0,turns=12,
                     opponent_scenario="mixed",pilot_style="adaptive",
                     provisional_mode="safe")
        data=summarize_run(run)
        self.assertEqual(data["decisions_by_role"],{"creature":1})
        self.assertEqual(data["event_counts"],{"creature_cast":1,"draw":2})
        self.assertEqual(data["turns_without_main_actions"],1)
        self.assertEqual(data["review_turns"],[{
            "turn":2,"signals":["idle_with_unimplemented_hand"]}])
        self.assertEqual(len(data["sample_timeline"]),2)
        self.assertEqual(data["sample_timeline"][0]["pilot_choices"][0]["score"],48)

    def test_optional_combat_trace_preserves_preexisting_audits(self):
        run=fake_run("necron_dynasties",seed=0,turns=2,
                     opponent_scenario="mixed",pilot_style="tempo",
                     provisional_mode="safe")
        self.assertEqual(summarize_run(run)["attackers_committed"],0)
        self.assertIsNone(summarize_run(run)["sample_timeline"][0]["pilot_combat"])
        run["events"][0]["pilot_combat"]={
            "style":"tempo","reserve":0,"attack_limit":4,
            "factors":["personality:tempo"],
            "candidate_attackers":3,"selected_attackers":3,
            "target_seat":2}
        data=summarize_run(run)
        self.assertEqual(data["attackers_committed"],3)
        self.assertEqual(data["sample_timeline"][0]["pilot_combat"]["style"],
                         "tempo")

    def test_audit_summarizes_all_supported_decks_deterministically(self):
        result=run_audit(("wretched_ranks","necron_dynasties"),seeds=2,
                         rounds=12,runner=fake_run)
        self.assertEqual(result["format"],FORMAT)
        self.assertEqual(len(result["runs"]),4)
        self.assertEqual(result["deck_summaries"]["wretched_ranks"][
            "outcomes"],{"unresolved":2})
        self.assertEqual(result["deck_summaries"]["wretched_ranks"][
            "idle_turns"],2)
        self.assertEqual(result["deck_summaries"]["wretched_ranks"][
            "median_completed_rounds"],2)
        repeat=run_audit(("wretched_ranks","necron_dynasties"),seeds=2,
                         rounds=12,runner=fake_run)
        self.assertEqual(result,repeat)

    def test_audit_filters_unsupported_seen_cards_by_frequency(self):
        result=run_audit(("necron_dynasties",),seeds=2,
                         rounds=12,runner=fake_run)
        top=result["deck_summaries"]["necron_dynasties"][
            "priority_unmodeled_cards"]
        self.assertEqual(top[0],{"card":"Unknown Card","observed_turns":2})
        self.assertEqual(sum(e["observed_turns"] for e in top),8)

    def test_reject_invalid_audit_parameters(self):
        for options in ({"seeds":0},{"rounds":31},{"style":"named_commander"},
                        {"scenario":"unknown"},{"provisional_mode":"unsafe"}):
            with self.subTest(options=options),self.assertRaises(ValueError):
                run_audit(("necron_dynasties",),runner=fake_run,**options)
        with self.assertRaises(ValueError):
            run_audit((),runner=fake_run)
        with self.assertRaises(ValueError):
            run_audit(("unknown",),runner=fake_run)

    def test_truncating_timeline_never_changes_aggregate_counts(self):
        run=fake_run("necron_dynasties",seed=0,turns=12,
                     opponent_scenario="mixed",pilot_style="adaptive",
                     provisional_mode="safe")
        one=summarize_run(run,turn_examples=1)
        two=summarize_run(run,turn_examples=12)
        self.assertEqual(len(one["sample_timeline"]),1)
        self.assertEqual(len(two["sample_timeline"]),2)
        for key in ("event_counts","decisions_by_role",
                    "turns_without_main_actions","review_turns"):
            self.assertEqual(one[key],two[key])


if __name__=="__main__":
    unittest.main()
