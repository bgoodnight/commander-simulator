"""Reproducible, unprofiled diagnostic timings; not a deck-strength benchmark."""
import argparse,json,platform,statistics,time
from pathlib import Path
from baseline import CopyTable,DECK,digest
from resources import Cost

def sample(fn,n):
 times=[];stops=[]
 for seed in range(n):
  start=time.perf_counter();result=fn(seed);times.append(round((time.perf_counter()-start)*1000,3))
  if getattr(result,'safety_stop',None):stops.append([seed,result.safety_stop])
 return {'samples_ms':times,'median_ms':round(statistics.median(times),3),'safety_stops':stops}

def action_stress(n):
 t=CopyTable(seed=9292,trace=False);seat=t.detailed_seat;t.active_seat=seat;t.phase='main'
 for oid in t.zones.ids(seat,'hand'):t.zones.move(oid,'library')
 oid=next(x for x in t.zones.ids(seat,'library') if t.rules.get(x).card.name=='Step Through');t.zones.move(oid,'hand')
 t.rules.mana_pools[seat]=(100,100,100)
 for _ in range(n):t.add_creature(t.players[1],1,1,'benchmark token',token=True)
 start=time.perf_counter();choices=t.priority_choices(seat);elapsed=(time.perf_counter()-start)*1000
 return {'tokens':n,'pairs':sum(c.kind=='spell' and c.action.source=='Step Through' for c in choices),'elapsed_ms':round(elapsed,3)}

def stress():
 t=CopyTable(seed=9393,trace=False);p=t.details;t.active_seat=p.seat;t.phase='main';t.priority_policy=lambda *a:None
 def give(name):
  c=next(c for c in p.hand+p.library if c.name==name)
  if c not in p.hand:
   oid=t.zones.move(c.object_id,'hand');c=next(c for c in p.hand if c.object_id==oid)
  return c
 t.rules.mana_pools[p.seat]=(3,0,0);card=give('Phyrexian Altar');t.cast(t.action_for_card(p,card))
 for _ in range(8):t.add_creature(p,1,1,'benchmark token',token=True)
 start=time.perf_counter();plan=t.resources.plan(p.seat,Cost(blue=4,red=4));payment_ms=(time.perf_counter()-start)*1000
 if plan is None:raise AssertionError('Stress payment unavailable')
 t.rules.mana_pools[p.seat]=(30,30,30);t.rules._dirty();give('Reiterate');used=[]
 def policy(seat,frames,choices):
  if seat==p.seat and not used:
   choice=next((c for c in choices if c.kind=='spell' and c.action.source=='Reiterate' and not c.action.parameters['buyback']),None)
   if choice:used.append(True);return choice
  return None
 t.priority_policy=policy;card=give('Consider');start=time.perf_counter();t.cast(t.action_for_card(p,card));stack_ms=(time.perf_counter()-start)*1000
 if not used or len(t.consider_events)!=2:raise AssertionError('Stress copy did not resolve')
 t.assert_consistent()
 return {'payment_tokens':8,'payment_states':plan.states,'payment_ms':round(payment_ms,3),
         'stack_copy_ms':round(stack_ms,3),'max_stack_depth':t.spell_stack.max_depth_seen}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--samples',type=int,default=4);parser.add_argument('--output',type=Path);args=parser.parse_args()
 if args.samples<1:parser.error('samples must be positive')
 out={'python':platform.python_version(),'platform':platform.platform(),'deck_sha256':__import__('hashlib').sha256(DECK.read_bytes()).hexdigest(),
  'trace':False,'samples':args.samples,'initialization':sample(lambda s:CopyTable(seed=s,trace=False),args.samples),
  'eight_round':sample(lambda s:CopyTable(seed=s,trace=False).run(8),args.samples),
  'twelve_round':sample(lambda s:CopyTable(seed=s,trace=False).run(12),args.samples),
  'target_stress':[action_stress(n) for n in (10,30,60)],'payment_and_stack_stress':stress(),
  'limitations':'Unprofiled single-process elapsed times; host load and game paths vary. No deck-strength inference. No safety budget is changed.'}
 raw=json.dumps(out,indent=2)+'\n'
 if args.output:args.output.write_text(raw)
 print(raw)
 if any(out[k]['safety_stops'] for k in ('eight_round','twelve_round')):raise SystemExit(1)
if __name__=='__main__':main()
