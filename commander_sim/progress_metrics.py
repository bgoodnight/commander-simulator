"""Reproducible early-game development diagnostics, NOT game win rates.

All inputs must be honest M1 observation records. This aggregates measured
turn-level availability over seeds. No casts, opponent choices, damage,
combat, triggers, or wins are inferred. Use actual-game events only when the
M3 gameplay runner exists.
"""
from __future__ import annotations
from math import sqrt


def wilson_interval(successes, n, z=1.96):
    """Approximate 95% binomial confidence interval; independent seed trials."""
    if type(successes) is not int or type(n) is not int or n <= 0 or not 0 <= successes <= n:
        raise ValueError('Invalid binomial count')
    p = successes / n
    denom = 1 + z*z/n
    center = (p + z*z/(2*n))/denom
    width = z*sqrt(p*(1-p)/n + z*z/(4*n*n))/denom
    return [round(max(0, center-width), 4), round(min(1, center+width), 4)]


def summarize_observed_progress(observations):
    """Summarize exact turn-aligned observations from one deck/hash.

    Count source-payable cards only if the existing observation reported a
    fixed-cost source payment preview. These are not legally castable spells.
    """
    rows = list(observations)
    if not rows:
        raise ValueError('At least one observation is required')
    first = rows[0]
    if first.get('mode') != 'observation':
        raise ValueError('Only offline observations can be summarized here')
    required = ('deck_sha256', 'commander', 'turns', 'opening_hand_policy')
    if any(not first.get(k) for k in required):
        raise ValueError('Missing observation provenance')
    turns = first['turns']
    if type(turns) is not int or turns < 1 or turns > 100:
        raise ValueError('Invalid turn count')
    seeds = set()
    for row in rows:
        if row.get('mode') != 'observation' or any(row.get(k) != first[k] for k in required):
            raise ValueError('Cannot mix deck, mode, or opening-hand policy')
        seed = row.get('seed')
        if type(seed) is not int or seed in seeds:
            raise ValueError('Seeds must be unique integers')
        seeds.add(seed)
        trace = row.get('trace')
        if not isinstance(trace, list) or len(trace) != turns:
            raise ValueError('Incomplete turn trace')
        for index, turn in enumerate(trace, 1):
            if turn.get('turn') != index or not isinstance(turn.get('modeled_sources'), list):
                raise ValueError('Invalid turn alignment or source trace')
            if not isinstance(turn.get('source_paid_mana_preview'), list):
                raise ValueError('Missing source-payment preview')
            if turn.get('playable_now') != []:
                raise ValueError('Unexpected claimed legal plays in observation')
    n = len(rows)
    output = []
    for i in range(turns):
        trace = [row['trace'][i] for row in rows]
        land_drops = sum(bool(t.get('land_played')) for t in trace)
        has_sources = sum(bool(t['modeled_sources']) for t in trace)
        has_preview = sum(bool(t['source_paid_mana_preview']) for t in trace)
        output.append({
            'turn': i + 1,
            'land_drop_rate': round(land_drops/n, 4),
            'land_drop_95pct_interval': wilson_interval(land_drops, n),
            'source_available_rate': round(has_sources/n, 4),
            'source_paid_candidate_rate': round(has_preview/n, 4),
            'source_paid_candidate_95pct_interval': wilson_interval(has_preview, n),
            'mean_modeled_sources': round(sum(len(t['modeled_sources']) for t in trace)/n, 3),
            'mean_printed_cost_candidates': round(sum(len(t['source_paid_mana_preview']) for t in trace)/n, 3),
        })
    return {
        'mode': 'early_game_observation_aggregate',
        'commander': first['commander'],
        'deck_sha256': first['deck_sha256'],
        'opening_hand_policy': first['opening_hand_policy'],
        'seed_count': n,
        'seeds': sorted(seeds),
        'turns': output,
        'limitations': (
            'Early land and known printed-cost affordability only. '
            'No legal spell casting, spell effects, combat, opponent actions, '
            'tutoring, reliable gameplay outcomes, or win-rate estimates. '
            'Wilson intervals reflect sampled seeds, not omitted-model uncertainty.'
        ),
    }


def run_fixture_progress(key, *, seeds=100, turns=6, mulligan='one-free'):
    """Offline seed batch; uses the same pinned M1 inventory and observation."""
    if type(seeds) is not int or not 1 <= seeds <= 10000:
        raise ValueError('Seed count must be 1..10000')
    if type(turns) is not int or not 1 <= turns <= 20:
        raise ValueError('Turn count must be 1..20')
    from .fixture_inventory import fixture_observation
    return summarize_observed_progress(
        fixture_observation(key, seed=seed, turns=turns, mulligan=mulligan)
        for seed in range(seeds)
    )


if __name__ == '__main__':
    import argparse
    import json
    from .deck_fixtures import FIXTURES
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deck', choices=[f.key for f in FIXTURES], required=True)
    parser.add_argument('--seeds', type=int, default=100)
    parser.add_argument('--turns', type=int, default=6)
    parser.add_argument('--mulligan', choices=('keep', 'one-free'), default='one-free')
    opts = parser.parse_args()
    print(json.dumps(run_fixture_progress(opts.deck, seeds=opts.seeds,
                                         turns=opts.turns, mulligan=opts.mulligan), indent=2))
