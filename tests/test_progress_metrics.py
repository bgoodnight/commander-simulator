"""Honest progress metrics: observations never become fabricated games."""
import unittest

from commander_sim.progress_metrics import (
    run_fixture_progress, summarize_observed_progress, wilson_interval,
)


def observation(seed, *, payable=False, land=True):
    return {
        'mode': 'observation', 'commander': 'Ghoulcaller Gisa',
        'deck_sha256': 'test-pinned-hash', 'seed': seed, 'turns': 1,
        'opening_hand_policy': 'keep seven',
        'trace': [{
            'turn': 1, 'land_played': 'Swamp' if land else None,
            'modeled_sources': [{'card': 'Swamp', 'colors': ['B']}] if land else [],
            'source_paid_mana_preview': [{'card': 'Example'}] if payable else [],
            'playable_now': [],
        }]
    }


class ProgressMetricTests(unittest.TestCase):
    def test_aggregates_real_observation_indicators_only(self):
        result = summarize_observed_progress([
            observation(1, payable=True), observation(2, land=False),
            observation(3, payable=True)])
        turn = result['turns'][0]
        self.assertEqual(result['seed_count'], 3)
        self.assertEqual(turn['land_drop_rate'], 0.6667)
        self.assertEqual(turn['source_paid_candidate_rate'], 0.6667)
        self.assertEqual(turn['mean_printed_cost_candidates'], 0.667)
        self.assertNotIn('win_rate', result)
        self.assertIn('No legal spell casting', result['limitations'])

    def test_reproducible_seed_order_invariant(self):
        a, b = observation(10, payable=True), observation(2)
        x = summarize_observed_progress([a, b])
        self.assertEqual(x, summarize_observed_progress([b, a]))
        self.assertEqual(x['seeds'], [2, 10])

    def test_rejects_deck_and_policy_mixture(self):
        a, b = observation(0), observation(1)
        b['deck_sha256'] = 'different'
        with self.assertRaises(ValueError):
            summarize_observed_progress([a, b])
        b['deck_sha256'] = a['deck_sha256']
        b['opening_hand_policy'] = 'one free'
        with self.assertRaises(ValueError):
            summarize_observed_progress([a, b])

    def test_rejects_duplicate_seeds_or_fake_legal_plays(self):
        with self.assertRaises(ValueError):
            summarize_observed_progress([observation(1), observation(1)])
        row = observation(3)
        row['trace'][0]['playable_now'] = ['cast']
        with self.assertRaises(ValueError):
            summarize_observed_progress([row])

    def test_wilson_range_is_bounded(self):
        self.assertEqual(wilson_interval(0, 10)[0], 0)
        self.assertEqual(wilson_interval(10, 10)[1], 1)
        with self.assertRaises(ValueError):
            wilson_interval(1, 0)

    def test_real_pinned_fixture_two_seed_smoke(self):
        a = run_fixture_progress('wretched_ranks', seeds=2, turns=2)
        b = run_fixture_progress('wretched_ranks', seeds=2, turns=2)
        self.assertEqual(a, b)
        self.assertEqual(a['seed_count'], 2)
        self.assertEqual(len(a['turns']), 2)
        self.assertEqual(a['mode'], 'early_game_observation_aggregate')


if __name__ == '__main__':
    unittest.main()
