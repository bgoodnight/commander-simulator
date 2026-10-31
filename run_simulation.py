"""Run the current simulator with the premium deck, or the preserved budget deck."""
import argparse,json,sys
from functools import partial
from pathlib import Path
from commander_sim.decks import DeckProvider
sys.path.insert(0,str(Path(__file__).resolve().parent/'simulator'/'v35_copy_targets'))
from copy_table import CopyTable
from premium_table import PremiumPlayer

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    choice=parser.add_mutually_exclusive_group()
    choice.add_argument('--deck',choices=('premium','budget'),default=None)
    choice.add_argument('--deck-file',type=Path)
    parser.add_argument('--seed',type=int,default=0)
    parser.add_argument('--rounds',type=int,default=8)
    args=parser.parse_args()
    if args.rounds<1:parser.error('rounds must be positive')
    provider=DeckProvider.bundled()
    try:
        deck=provider.load(args.deck_file) if args.deck_file else provider.preset(args.deck or 'premium')
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    deck_label=str(args.deck_file) if args.deck_file else args.deck or 'premium'
    table=CopyTable(seed=args.seed,detailed_factory=partial(PremiumPlayer,deck=deck)).run(args.rounds)
    table.assert_consistent()
    print(json.dumps({'deck':deck_label,'seed':args.seed,'round_limit':args.rounds,
        'safety_stop':table.safety_stop,'life':[p.life for p in table.players],
        'note':'Incomplete card/rules coverage and heuristic opponents; not a deck-strength estimate.'},indent=2))
    if table.safety_stop:raise SystemExit(1)
if __name__=='__main__':main()
