"""Run the current simulator with the premium deck, or the preserved budget deck."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'simulator'/'v32_cyclonic_rift'))
from rift_table import RiftTable
from altar_table import AltarTable

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deck',choices=('premium','budget'),default='premium')
    parser.add_argument('--seed',type=int,default=0)
    parser.add_argument('--rounds',type=int,default=8)
    args=parser.parse_args()
    if args.rounds<1:parser.error('rounds must be positive')
    table=(RiftTable if args.deck=='premium' else AltarTable)(seed=args.seed).run(args.rounds)
    table.assert_consistent()
    print(json.dumps({'deck':args.deck,'seed':args.seed,'round_limit':args.rounds,
        'safety_stop':table.safety_stop,'life':[p.life for p in table.players],
        'note':'Incomplete card/rules coverage and heuristic opponents; not a deck-strength estimate.'},indent=2))
    if table.safety_stop:raise SystemExit(1)
if __name__=='__main__':main()
