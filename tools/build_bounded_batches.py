"""Regenerate the pinned six-turn batch and compact drilldown records offline."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from commander_sim.bounded_batch import run_bounded_batch
from commander_sim.early_game_runner import run_bounded_early_game

KEYS = ('magnus_premium', 'wretched_ranks', 'mortarion_current', 'necron_dynasties')
FILES = ('commander_sim/generic_cast.py', 'commander_sim/reviewed_sacrifice_actions.py',
         'commander_sim/early_game_runner.py', 'commander_sim/bounded_batch.py')

def main():
    result = {'format': 'bounded-batches-v1',
              'base_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
              'engine_files_sha256': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},
              'decks': {}}
    for key in KEYS:
        batch = run_bounded_batch(key, seeds=100, turns=6)
        runs = []
        for seed in range(100):
            run = run_bounded_early_game(key, seed=seed, turns=6)
            if run['deck_sha256'] != batch['deck_sha256']:
                raise ValueError('Deck revision changed during batch')
            compact = {k: run[k] for k in ('mode','deck_key','deck_sha256','seed')}
            compact['mulligan'] = {'policy': run['mulligan']['policy']}
            compact['events'] = [{**{k: row[k] for k in ('turn','land_count','hand_size','unsupported_cards_in_hand')},
                                  'events': [{k: e[k] for k in ('type','card') if k in e} for e in row['events']]}
                                 for row in run['events']]
            compact['state_snapshots'] = [{k: state[k] for k in ('turn','hand','battlefield')}
                                          for state in run['state_snapshots']]
            runs.append(compact)
        (ROOT/f'web/pages/data/bounded-runs-{key}.json').write_text(json.dumps(runs,separators=(',',':'))+'\n')
        result['decks'][key] = batch
        print(key, flush=True)
    (ROOT/'web/pages/data/bounded-batches.json').write_text(json.dumps(result,separators=(',',':'))+'\n')

if __name__ == '__main__':
    main()
