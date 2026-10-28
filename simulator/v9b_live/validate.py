"""Reproduce narrated diagnostics, conservation sweep and exploratory timings.

These are infrastructure checks, not deck-strength measurements.
"""
import argparse
import json
from pathlib import Path
import statistics
import time
from live import LiveTable
from adapter import V9Table

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
    for player in table.players:
        actual = sum(not o.token and o.owner == player.seat for o in table.rules.objects.values())
        expected = 0 if player.eliminated_round is not None else 100 if player is table.details else 99
        if actual != expected:
            raise AssertionError((table.seed, player.seat, actual, expected))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke-seeds', type=int, default=100)
    parser.add_argument('--benchmark-games', type=int, default=40)
    args = parser.parse_args()
    if min(args.smoke_seeds, args.benchmark_games) < 1:
        parser.error('Counts must be positive')
    records = []
    for label, seed, seat, opponents, opening in CASES:
        providers = list(opponents); providers.insert(seat, 'magnus')
        table = LiveTable(providers, seed=seed, trace=True, opening=opening).run(10)
        check(table)
        record = dict(case=label, seed=seed, providers=providers, forced_opening=bool(opening),
                      reason=table.win_reason, safety_stop=table.safety_stop, consistent=True,
                      magnus_life=table.details.life, magnus_casts=table.details.cards_cast)
        records.append(record)
        data = dict(record=record, rounds=table.turns, events=table.events, diagnostics=table.diagnostics())
        (ROOT / (label + '.json')).write_text(json.dumps(data, indent=2) + '\n')
        lines = [f'# V9b live-zone diagnostic: {label}', '',
                 f'Seed {seed}; Magnus seat {seat}; forced opening: {bool(opening)}.',
                 f'Result: {table.win_reason}; safety stop: {table.safety_stop}.', '',
                 'Physical-card conservation, zone indexing and battlefield projections passed.', '',
                 '## Transcript', '', '```text', *table.events, '```', '',
                 '## Boundaries', '',
                 'Mana uses legacy resource policies. Priority is counter-only; selection, land rules and synthetic opponents remain approximate. No deck-power conclusions.']
        (ROOT / (label + '.md')).write_text('\n'.join(lines) + '\n')
    stops = []
    started = time.perf_counter()
    for seat in range(4):
        for seed in range(args.smoke_seeds):
            providers = list(GROUPS[seed % len(GROUPS)]); providers.insert(seat, 'magnus')
            table = LiveTable(providers, seed=seed).run(12)
            check(table)
            if table.safety_stop:
                stops.append(dict(seed=seed, seat=seat, reason=table.safety_stop))
    elapsed = time.perf_counter() - started
    timings = {}
    for engine in (V9Table, LiveTable):
        samples = []
        for seed in range(args.benchmark_games):
            started = time.perf_counter()
            engine(seed=seed).run(10)
            samples.append((time.perf_counter() - started) * 1000)
        timings[engine.__name__] = round(statistics.median(samples), 3)
    report = dict(smoke_games=args.smoke_seeds * 4, rounds_per_game=12,
                  conservation_and_consistency_passed=True, safety_stops=stops,
                  sweep_seconds=round(elapsed, 3), narratives=records,
                  benchmark_games=args.benchmark_games, benchmark_rounds=10,
                  median_ms=timings, caveat='Local infrastructure diagnostics; no deck-strength inference')
    (ROOT / 'validation_results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
