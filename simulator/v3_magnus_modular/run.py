"""Run two narrated games (or optional paired-policy batches)."""
from engine import Catalog
from pilot import Pilot
from pathlib import Path
import argparse,json,statistics
ROOT=Path(__file__).parent

def narrate(g):
    s=g.summary();head=['# Simulated game',f'**Seed:** {s["seed"]} · **Pilot:** {s["policy"]} · **Scenario:** {s["scenario"]}',
    f'**First Magnus:** {s["first_magnus"] or "not by cutoff"} · **Selection spells cast:** {s["selection_cast"]} · **Total instant/sorcery casts:** {s["spells_cast"]} · **First combo-ready turn:** {s["first_combo"] or "none"}',
    f'**Mulligan:** {s["mulligans"]} · **Mana spent:** {s["total_mana_paid"]} · **Generic mana discounted:** {s["generic_saved"]}',
    '', '## Turn-by-turn trace','']
    return '\n'.join(head+s['trace'])+'\n'

def batch(pilot,n=100,seed=20261028,turns=8):
    result={}
    for policy in ('rush','delay_one'):
        values=[pilot.run(seed+i,policy,turns=turns,trace=False).summary() for i in range(n)]
        result[policy]={
            'trials':n,'seed_range':[seed,seed+n-1],
            'magnus_by_t5_pct':round(100*sum(v['first_magnus'] is not None and v['first_magnus']<=5 for v in values)/n,1),
            'magnus_by_t6_pct':round(100*sum(v['first_magnus'] is not None and v['first_magnus']<=6 for v in values)/n,1),
            'mean_selection_spells_t8':round(statistics.mean(v['selection_cast'] for v in values),2),
            'mean_instants_sorceries_t8':round(statistics.mean(v['spells_cast'] for v in values),2),
            'combo_ready_t8_pct':round(100*sum(v['first_combo'] is not None for v in values)/n,1),
            'mean_mana_spent_t8':round(statistics.mean(v['total_mana_paid'] for v in values),2)
        }
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,default=20261028)
    parser.add_argument('--turns',type=int,default=8)
    parser.add_argument('--trials',type=int,default=0)
    args=parser.parse_args()
    cat=Catalog();pilot=Pilot(cat)
    for seed,policy,scenario,filename in [(args.seed,'rush','none','game1_rush.md'),(args.seed,'delay_one','one_removal_t5','game2_delay_with_removal.md')]:
        g=pilot.run(seed,policy,scenario,args.turns,trace=True)
        (ROOT/filename).write_text(narrate(g))
        print(filename, 'Magnus',g.first_magnus,'spells',g.instant_sorcery_cast,'tokens',g.token_count(),'turn',g.turn)
    if args.trials:
        result=batch(pilot,args.trials,args.seed,args.turns)
        (ROOT/'batch_smoke.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result,indent=2))
