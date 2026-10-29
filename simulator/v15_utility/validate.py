"""Real-source interaction narratives and independent all-seat smoke games."""
import argparse,importlib.util,json,statistics,time
from pathlib import Path
from utility_table import UtilityTable
from utility_cards import ISLET,RIPTIDE
from land_table import LandTable
from resources import Activation
from coverage import write as write_coverage

ROOT=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('v11_story_helpers',ROOT.parent/'v11_steps'/'validate.py')
_h=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_h)
check,give,cast=_h.check,_h.give,_h.cast

def fixture(seed,islands=0,mountains=0):
 t=UtilityTable(seed=seed,trace=True);t.priority_policy=lambda *args:None
 for p in t.players:
  for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
 t.round_num=2;t.turn_serial=1;t.safe_runner.new_turn(1)
 t.note('FORCED DIAGNOSTIC: declared actual card/source layout; not a natural opening.')
 for name in ['Island']*islands+['Mountain']*mountains:
  t.enter_land(t.details,give(t,name).object_id,cause='declared_fixture')
 check(t);return t

def land(t,name,forced=False):return t.enter_land(t.details,give(t,name).object_id,force_tapped=forced,cause='declared_fixture')
def placed(t,name):
 cast(t,give(t,name));return next(o for o in t.rules.on_battlefield() if o.card.name==name and not o.token)
def setup_wizard(t):
 placed(t,'Arcane Adaptation');placed(t,'Harmonic Prodigy');wizard=placed(t,'Third Path Iconoclast')
 src=land(t,'Riptide Laboratory');t.turn_serial+=1;t.safe_runner.new_turn(t.turn_serial);t.resources.untap(0)
 t.note('DIAGNOSTIC NEXT OWN TURN: actual land sources untapped.')
 return src,wizard

def stories():
 out=[]
 t=fixture(601,3,1);placed(t,'Young Pyromancer');cast(t,give(t,'Ponder'))
 assert sum(c.name=='Elemental' for c in t.details.creatures)==1
 sanctuary=land(t,'Mystic Sanctuary');t.spell_stack.resolve()
 assert t.details.library[-1].name=='Ponder';t.details.draw();cast(t,give(t,'Ponder'))
 assert sum(c.name=='Elemental' for c in t.details.creatures)==2;check(t)
 out.append(('01_sanctuary_reuse','Sanctuary returns Ponder for a second cast',
 'Three other Islands let Sanctuary enter untapped. Its triggered ability targeted the previously cast Ponder in the graveyard and put it on top. The diagnostic draw and a second source-paid cast produced another Pyromancer Elemental: two in total.',t))

 t=fixture(602,3);cast(t,give(t,'Ponder'));grave=next(oid for oid in t.zones.ids(0,'graveyard') if t.rules.get(oid).card.name=='Ponder')
 src=land(t,'Mystic Sanctuary');t.spell_stack.checkpoint()
 t.note('SYNTHETIC RESPONSE FIXTURE: move the targeted graveyard card to exile while the trigger is waiting.')
 t.zones.move(grave,'exile');t.spell_stack.resolve();assert t.spell_stack.fizzled==1;check(t)
 out.append(('02_target_lost','Sanctuary target leaving the graveyard causes the trigger to fail',
 'The trigger chose Ponder when placed on the stack. A declared synthetic response moved that exact graveyard object to exile; on resolution the trigger had no legal target and did not return it. No printed graveyard-exile card was added by this scenario.',t))

 t=fixture(603,2);src=land(t,'Fiery Islet');ability=next(a for a in t.resources.abilities(t.rules.get(src)) if a.output==(0,1,0))
 t.resources.activate(0,Activation(src,ability,t.resources.pool(0)));assert t.details.life==39
 t.resources.empty_pools();t.turn_serial+=1;t.safe_runner.new_turn(t.turn_serial);t.resources.untap(0)
 t.note('DIAGNOSTIC NEXT OWN TURN: pool emptied and sources untapped.')
 before=len(t.details.hand);t.active_seat=0;t.phase='main';t.activate_ability(0,src,ISLET)
 assert len(t.details.hand)==before+1 and 'Fiery Islet' in t.details.graveyard and t.details.damage_taken==0;check(t)
 out.append(('03_islet_modes','Fiery Islet pays life for mana, then later sacrifices to draw',
 'An actual Fiery Islet mana activation produced U and paid one life without damage. After a declared next-turn untap, a different land paid the one-mana draw-ability cost; Islet was tapped and sacrificed before the card was drawn.',t))

 t=fixture(604,3);src=land(t,'Fiery Islet');give(t,'Brainstorm');used=[]
 def respond(seat,frames,choices):
  c=next((c for c in choices if seat==0 and frames and c.kind=='spell' and c.action.source=='Brainstorm'),None)
  if c and not used:used.append(True);return c
 t.priority_policy=respond;t.active_seat=0;t.phase='main';t.activate_ability(0,src,ISLET)
 assert used and len(t.details.hand)==2 and 'Fiery Islet' in t.details.graveyard;check(t)
 out.append(('04_islet_response','A spell resolves before the waiting Islet draw',
 'The Islet draw ability paid its source and mana costs. Brainstorm was cast in response, completing its draw and put-back choices before the Islet ability resolved and drew its card.',t))

 t=fixture(605,8,4);src,wizard=setup_wizard(t);give(t,'Capsize');used=[]
 def respond(seat,frames,choices):
  c=next((c for c in choices if seat==0 and frames and c.kind=='spell' and c.action.source=='Capsize'
          and c.action.target_object==wizard.object_id and not c.action.tags),None)
  if c and not used:used.append(True);return c
 t.priority_policy=respond;t.active_seat=0;t.phase='main';t.activate_ability(0,src,RIPTIDE,wizard.object_id)
 assert used and t.spell_stack.fizzled==1 and any(c.name=='Third Path Iconoclast' for c in t.details.hand)
 assert sum(c.name=='Soldier' for c in t.details.creatures)==2;check(t)
 out.append(('05_riptide_response','Riptide, Adaptation, Harmonic and a response',
 'Adaptation made Iconoclast a Wizard, enabling Riptide. In response, Capsize bounced that same creature; the Riptide ability then failed its target check. Capsize had already triggered the adapted Iconoclast twice through Harmonic, creating two Soldiers.',t))

 t=fixture(606,8,4);src,wizard=setup_wizard(t)
 adaptation=next(o.object_id for o in t.rules.on_battlefield() if o.card.name=='Arcane Adaptation');give(t,'Capsize');used=[]
 def respond2(seat,frames,choices):
  c=next((c for c in choices if seat==0 and frames and c.kind=='spell' and c.action.source=='Capsize'
          and c.action.target_object==adaptation and not c.action.tags),None)
  if c and not used:used.append(True);return c
 t.priority_policy=respond2;t.active_seat=0;t.phase='main';t.activate_ability(0,src,RIPTIDE,wizard.object_id)
 assert used and wizard.object_id in t.rules.objects and 'Wizard' not in t.rules.subtypes(wizard.object_id)
 assert t.spell_stack.fizzled==1;check(t)
 out.append(('06_type_removed','Removing Adaptation makes the Riptide target illegal',
 'Capsize returned Adaptation while the Riptide ability waited. Iconoclast remained on the battlefield but lost the Wizard subtype; Riptide rechecked its target and failed without returning it.',t))
 return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=50);p.add_argument('--benchmark-games',type=int,default=12);a=p.parse_args()
 if min(a.seeds,a.benchmark_games)<1:p.error('Counts must be positive')
 audit=write_coverage();records=[]
 for label,title,result,t in stories():
  records.append(dict(file=label,title=title,result=result,passed=True))
  data=dict(title=title,result=result,forced=True,events=t.events,utility_events=t.utility_events,priority=t.spell_stack.history,payments=t.resources.payments,activations=t.resources.activations)
  (ROOT/(label+'.json')).write_text(json.dumps(data,indent=2)+'\n')
  (ROOT/(label+'.md')).write_text('\n'.join(['# '+title,'','Forced conserved setup; actual sources; synthetic response explicitly marked where used.','',result,'','```text',*t.events,'```','']))
  print(label,'PASS',flush=True)
 groups=[['aggro','control','combo'],['aggro','tokens','ramp_stompy'],['control','spellslinger','midrange']]
 stops=[];steps=payments=events=0;start=time.perf_counter()
 for seat in range(4):
  for seed in range(a.seeds):
   kinds=groups[seed%3].copy();kinds.insert(seat,'magnus');t=UtilityTable(kinds,seed=seed).run(12);check(t)
   steps+=len(t.step_history);payments+=len(t.resources.payments);events+=len(t.utility_events)
   if t.safety_stop:stops.append(dict(seat=seat,seed=seed,reason=t.safety_stop))
  print('sweep seat',seat,'complete',flush=True)
 elapsed=time.perf_counter()-start;timings={}
 for cls in (LandTable,UtilityTable):
  samples=[]
  for seed in range(a.benchmark_games):
   start=time.perf_counter();cls(seed=seed).run(8);samples.append((time.perf_counter()-start)*1000)
  timings[cls.__name__]=round(statistics.median(samples),3)
 d=dict(games=a.seeds*4,rounds=12,consistent=True,safety_stops=stops,steps=steps,payments=payments,utility_events=events,elapsed_seconds=round(elapsed,3),benchmark_games=a.benchmark_games,benchmark_rounds=8,median_ms=timings,new_caching=False,audit_counts=audit['unique_counts'],narratives=records)
 (ROOT/'validation_results.json').write_text(json.dumps(d,indent=2)+'\n')
 history=json.loads((ROOT.parent/'v14_lands'/'PERFORMANCE_HISTORY.json').read_text())
 history['entries'].append(dict(version='v15',engine='UtilityTable',games=a.benchmark_games,rounds=8,
                                median_ms=timings['UtilityTable'],comparator_median_ms=timings['LandTable'],
                                measurement='same invocation; changed rules alter trajectories'))
 (ROOT/'PERFORMANCE_HISTORY.json').write_text(json.dumps(history,indent=2)+'\n')
 lines=['# V15 utility interactions','',f"Six forced narratives passed; {d['games']} twelve-round games passed consistency checks with {len(stops)} safety stops.",'','| Scenario | Result |','|---|---|']
 lines += [f"| [{r['title']}]({r['file']}.md) | {r['result']} |" for r in records]
 lines+=['',f'Median eight-round milliseconds ({a.benchmark_games} samples per engine): {timings}. Game trajectories differ; this is an exploratory comparison.','', 'One detailed deck and synthetic opponents; no deck win-rate conclusions.','']
 (ROOT/'INTERACTION_REPORT.md').write_text('\n'.join(lines));print(json.dumps(d,indent=2))
if __name__=='__main__':main()
