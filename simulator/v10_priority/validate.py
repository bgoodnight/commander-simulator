"""Reproduce narrated diagnostics, conservation sweep and exploratory timings.

These are infrastructure checks, not deck-strength measurements.
"""
import argparse
import json
from pathlib import Path
import statistics
import time
from gameplay import PriorityTable
from game import ManaTable

ROOT = Path(__file__).resolve().parent
GROUPS = [('aggro', 'control', 'combo'), ('aggro', 'tokens', 'ramp_stompy'),
          ('control', 'spellslinger', 'midrange')]
CASES = [('01_original_seat', 102, 0, GROUPS[0], None),
         ('02_right_of_aggro', 104, 1, GROUPS[1], None),
         ('03_third_seat', 103, 2, GROUPS[2], None),
         ('04_forced_seat_three', 404, 3, ('control', 'combo', 'tokens'),
          ('Sol Ring', 'Young Pyromancer', 'Harmonic Prodigy', 'Ponder', 'Preordain', 'Island'))]


def check(table):
    table.assert_consistent()
    table.resources.assert_consistent()
    for payment in table.resources.payments:
        if len(payment['sources']) != len(set(payment['sources'])):
            raise AssertionError('A source paid twice in one payment')
    for player in table.players:
        actual = sum(not o.token and o.owner == player.seat for o in table.rules.objects.values())
        expected = 0 if player.eliminated_round is not None else 100 if player is table.details else 99
        if actual != expected:
            raise AssertionError((table.seed, player.seat, actual, expected))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--narratives-only', action='store_true')
    parser.add_argument('--smoke-seeds', type=int, default=100)
    parser.add_argument('--benchmark-games', type=int, default=40)
    args = parser.parse_args()
    if min(args.smoke_seeds, args.benchmark_games) < 1:
        parser.error('Counts must be positive')
    records = []
    for label, seed, seat, opponents, opening in CASES:
        providers = list(opponents); providers.insert(seat, 'magnus')
        table = PriorityTable(providers, seed=seed, trace=True, opening=opening).run(10)
        check(table)
        record = dict(case=label, seed=seed, providers=providers, forced_opening=bool(opening),
                      reason=table.win_reason, safety_stop=table.safety_stop, consistent=True,
                      magnus_life=table.details.life, magnus_casts=table.details.cards_cast)
        records.append(record)
        data = dict(record=record, rounds=table.turns, events=table.events, priority_history=table.spell_stack.history, diagnostics=table.diagnostics())
        (ROOT / (label + '.json')).write_text(json.dumps(data, indent=2) + '\n')
        lines = [f'# V10 typed-priority diagnostic: {label}', '',
                 f'Seed {seed}; Magnus seat {seat}; forced opening: {bool(opening)}.',
                 f'Result: {table.win_reason}; safety stop: {table.safety_stop}.', '',
                 'Physical-card conservation, zone indexing and battlefield projections passed.', '',
                 '## Transcript', '', '```text', *table.events, '```', '',
                 '## Boundaries', '',
                 'Mana uses physical source IDs with ordered activations. Spells, triggers and registered activations use typed priority; coarse steps, land rules and synthetic abilities remain approximate. No deck-power conclusions.']
        (ROOT / (label + '.md')).write_text('\n'.join(lines) + '\n')
    if args.narratives_only:
        print('Four priority narratives regenerated; existing sweep report retained.')
        return
    stops = []; peak_states = payment_count = activation_count = 0
    trigger_count = ability_count = pass_count = max_depth = 0
    started = time.perf_counter()
    for seat in range(4):
        for seed in range(args.smoke_seeds):
            providers = list(GROUPS[seed % len(GROUPS)]); providers.insert(seat, 'magnus')
            table = PriorityTable(providers, seed=seed).run(12)
            check(table)
            peak_states = max(peak_states, table.resources.max_states_seen)
            payment_count += len(table.resources.payments)
            activation_count += len(table.resources.activations)
            trigger_count += table.spell_stack.triggers_resolved
            ability_count += table.spell_stack.abilities_resolved
            pass_count += table.spell_stack.passes
            max_depth = max(max_depth, table.spell_stack.max_depth_seen)
            if table.safety_stop:
                stops.append(dict(seed=seed, seat=seat, reason=table.safety_stop))
    elapsed = time.perf_counter() - started
    timings = {}
    for engine in (ManaTable, PriorityTable):
        samples = []
        for seed in range(args.benchmark_games):
            started = time.perf_counter()
            engine(seed=seed).run(10)
            samples.append((time.perf_counter() - started) * 1000)
        timings[engine.__name__] = round(statistics.median(samples), 3)
    report = dict(smoke_games=args.smoke_seeds * 4, rounds_per_game=12,
                  conservation_and_consistency_passed=True, safety_stops=stops,
                  peak_planner_states=peak_states, payment_count=payment_count, activation_count=activation_count,
                  resolved_trigger_count=trigger_count, resolved_ability_count=ability_count, priority_passes=pass_count, max_stack_depth=max_depth,
                  sweep_seconds=round(elapsed, 3), narratives=records,
                  benchmark_games=args.benchmark_games, benchmark_rounds=10,
                  median_ms=timings, caveat='Local infrastructure diagnostics; no deck-strength inference')
    (ROOT / 'validation_results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
