"""Calibration: (a) archetype trajectories without interaction, (b) random tables with interaction.
Use independent seeded replications. This prototype is for *qualitative* sanity checks.
"""
import argparse, json, statistics, random
from pathlib import Path
from collections import Counter, defaultdict
from engine import Table, ARCHETYPES, sample_archetypes
ROOT=Path(__file__).parent

def pct(xs,k):
    a=sorted(xs)
    if not a:return None
    return round(a[round((len(a)-1)*k)],2)

def summarize_goldfish(n,turns,seed):
    res={}
    for ai,arch in enumerate(ARCHETYPES):
        games=[]
        for i in range(n):
            # No opponents act on our board; three other seats are dummy passive goldfish 
            # but only the first synthetic opponent is summarized.
            g=Table([arch,'midrange','control'],seed=seed+ai*100000+i,interaction=False).run(turns)
            games.append(g.players[1])
        byturn={}
        for t in [2,4,6,8,10]:
            if t>turns:continue
            sn=[g.stats[t-1] for g in games]
            byturn[t]={
                'threat_p10_p50_p90':[pct([s['threat'] for s in sn],k) for k in [0.1,0.5,0.9]],
                'board_power_p10_p50_p90':[pct([s['board_power'] for s in sn],k) for k in [0.1,0.5,0.9]],
                'mana_p10_p50_p90':[pct([s['mana_sources'] for s in sn],k) for k in [0.1,0.5,0.9]],
                'missed_land_drop_pct':round(100*sum(s['mana_misses']>0 for s in sn)/n,1),
                'below_3_mana_sources_pct':round(100*sum(s['mana_sources']<3 for s in sn)/n,1),
            }
        res[arch]={'n':n,'trajectory':byturn,
                   'mean_cast_turn10':round(statistics.mean(g.cards_cast for g in games),1),
                   'combo_attempt_by_turn10_pct':round(100*sum(g.first_win_attempt is not None for g in games)/n,1)}
    return res

def summarize_table(n,turns,seed,interaction):
    archetype_info=defaultdict(lambda:{'life':[],'power':[],'threat':[],'board_losses':[],'attacks':[], 'mana':[]})
    event_counter=Counter(); target_ranks=Counter(); rank_exposures=Counter(); loser_ct=0
    for i in range(n):
        matchup=sample_archetypes(seed+i)
        g=Table(matchup,seed=seed+i,interaction=interaction).run(turns)
        if not g.players[0].alive:loser_ct+=1
        for p in g.players[1:]:
            d=archetype_info[p.arch]
            d['life'].append(p.life);d['power'].append(p.power());d['threat'].append(p.threat())
            d['board_losses'].append(p.creatures_lost);d['attacks'].append(p.attack_damage_dealt)
            d['mana'].append(p.active_mana())
        event_counter.update(g.counts);target_ranks.update(g.rank_target_counts);rank_exposures.update(g.rank_exposures)
    profiles={a:{'n':len(v['life']),'median_life':pct(v['life'],0.5),'median_board_power':pct(v['power'],0.5),
                 'median_threat':pct(v['threat'],0.5),'avg_creatures_lost':round(statistics.mean(v['board_losses']),2),
                 'avg_attack_damage_dealt':round(statistics.mean(v['attacks']),2),'median_mana':pct(v['mana'],0.5)} for a,v in archetype_info.items()}
    return {'tables':n,'turns':turns,'interaction':interaction,'passive_magnus_eliminated_pct':round(100*loser_ct/n,1),
           'profiles':profiles,'events_total':dict(event_counter),
           'targets_by_threat_rank':{f'{k[0]}_rank{k[1]}':v for k,v in target_ranks.items()},
           'eligible_target_opportunities':{f'{k[0]}_rank{k[1]}':v for k,v in rank_exposures.items()}}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--goldfish',type=int,default=450)
    parser.add_argument('--tables',type=int,default=300);parser.add_argument('--turns',type=int,default=10)
    parser.add_argument('--seed',type=int,default=20261028)
    parser.add_argument('--output',default=str(ROOT/'results.json'))
    args=parser.parse_args()
    results={'method':'99-card synthetic archetype bags; 3 active opponents + passive Magnus seat; no real card names for opponents',
            'goldfish':summarize_goldfish(args.goldfish,args.turns,args.seed),
            'random_tables_no_interaction':summarize_table(args.tables,args.turns,args.seed+10000000,False),
            'random_tables_with_interaction':summarize_table(args.tables,args.turns,args.seed+10000000,True)}
    Path(args.output).write_text(json.dumps(results,indent=2))
    print('Saved '+args.output)
    print('P10/P50/P90 archetype THREAT at T4, T8, T10 (goldfish):')
    for a,v in results['goldfish'].items():
        print(f'{a:14s}',*[str(v['trajectory'][t]['threat_p10_p50_p90']) for t in (4,8,10) if t<=args.turns])
    print('With-interaction events:',results['random_tables_with_interaction']['events_total'])
    print('Passive seat elimination:',results['random_tables_with_interaction']['passive_magnus_eliminated_pct'])

if __name__=='__main__':main()
