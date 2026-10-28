"""Calibrate four-active-player archetypes and save reproducible summary files."""
import argparse, json, statistics, collections, random, time
from pathlib import Path
from simulation import Table,ARCHETYPES,sample_matchup,ROOT

def pct(x,total):return round(100*x/total,1) if total else None

def describe(results):
    completed=[x for x in results if x['ending_round'] is not None]
    return {'games':len(results),'completed':len(completed),'completion_pct':pct(len(completed),len(results)),
            'median_finish_round':statistics.median(x['ending_round'] for x in completed) if completed else None,
            'p10_finish_round':sorted(x['ending_round'] for x in completed)[max(0,int(len(completed)*.1))] if completed else None,
            'p90_finish_round':sorted(x['ending_round'] for x in completed)[min(len(completed)-1,int(len(completed)*.9))] if completed else None,
            'censored_at_turn_limit':len(results)-len(completed),
            'win_causes':dict(collections.Counter(x['outcome'] for x in results)),
            'multi_elim_games':sum(x['metrics'].get('multi_elimination_events',0)>0 for x in results),
            'first_elimination_round_median':statistics.median(min(e['round'] for e in x['eliminations']) for x in results if x['eliminations'])}

def run(mixed=2000,mirrors=120,controlled=180,limit=30,seed=20261028):
    t0=time.time();mixed_games=[];seats=collections.Counter();entries=collections.Counter();wins=collections.Counter()
    for i in range(mixed):
        m=sample_matchup(seed+i)
        result=Table(m,seed=seed+i).run(limit).summary();mixed_games.append(result)
        for a in m:entries[a]+=1
        if result['winner_archetype']:
            wins[result['winner_archetype']]+=1;seats[result['winner']]+=1
    mirror_rows={}
    for j,a in enumerate(ARCHETYPES):
        games=[Table([a]*4,seed=seed+100000+j*2000+i).run(limit).summary() for i in range(mirrors)]
        data=describe(games)
        data['seat_wins']=dict(collections.Counter(x['winner'] for x in games if x['winner'] is not None))
        mirror_rows[a]=data
    matchups={
      'aggro_control_combo_ramp':['aggro','control','combo','ramp_stompy'],
      'aggro_aggro_control_combo':['aggro','aggro','control','combo'],
      'tokens_tokens_control_combo':['tokens','tokens','control','combo'],
      'control_spellslinger_combo_midrange':['control','spellslinger','combo','midrange'],
      'aggro_tokens_ramp_midrange':['aggro','tokens','ramp_stompy','midrange'],
      'control_control_combo_spellslinger':['control','control','combo','spellslinger']
    }
    controlled_rows={}
    for j,(name,types) in enumerate(matchups.items()):
        games=[Table(types,seed=seed+200000+j*2000+i).run(limit).summary() for i in range(controlled)]
        d=describe(games)
        d.update(archetypes=types,winner_archetypes=dict(collections.Counter(x['winner_archetype'] or 'unresolved' for x in games)))
        controlled_rows[name]=d
    return {
      'meta':{'mixed_trials':mixed,'mirror_trials_per_type':mirrors,'controlled_trials_per_matchup':controlled,
              'seed':seed,'max_rounds':limit,'runtime_seconds':round(time.time()-t0,2)},
      'random_tables':{'summary':describe(mixed_games),
                       'archetypes':{a:{'seat_exposures':entries[a],'wins':wins[a],
                                         'wins_per_seat_pct':pct(wins[a],entries[a])} for a in ARCHETYPES},
                       'winning_seats':dict(seats)},
      'mirrors':mirror_rows,'controlled':controlled_rows
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mixed',type=int,default=2000);ap.add_argument('--mirrors',type=int,default=120)
    ap.add_argument('--controlled',type=int,default=180);ap.add_argument('--limit',type=int,default=30)
    ap.add_argument('--seed',type=int,default=20261028)
    a=ap.parse_args();results=run(a.mixed,a.mirrors,a.controlled,a.limit,a.seed)
    dest=ROOT/'results_v5.json';dest.write_text(json.dumps(results,indent=2))
    print('Wrote',dest)
    print('Time:',results['meta']['runtime_seconds'],'seconds')
    print('Mixed:',results['random_tables']['summary'])
    print('Archetype seat win rates:')
    for name,vals in results['random_tables']['archetypes'].items():print(' ',name, vals['wins_per_seat_pct'])
    print('Mirrors:')
    for name,vals in results['mirrors'].items():print(' ',name,vals['median_finish_round'],vals['completion_pct'])
if __name__=='__main__':main()
