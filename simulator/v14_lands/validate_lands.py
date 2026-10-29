"""Source-paid land narratives, conservation sweep and pre-optimization outputs."""
import argparse,importlib.util,json,statistics,time
from pathlib import Path
from land_table import LandTable
from land_cards import FETCH
from engine_table import EngineTable
from land_coverage import write as write_coverage
from reference_state import fingerprint

ROOT=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('v11_land_validation_helpers',ROOT.parent/'v11_steps'/'validate.py')
_helpers=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_helpers)
check,give,cast=_helpers.check,_helpers.give,_helpers.cast


def fixture(seed,islands=0,mountains=0):
    t=LandTable(seed=seed,trace=True);t.priority_policy=lambda *args:None
    for p in t.players:
        for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
    t.round_num=2;t.turn_serial=1;t.safe_runner.new_turn(1)
    t.note('FORCED DIAGNOSTIC: conserved actual cards, declared battlefield/hand setup; not a natural opening.')
    for name in ['Island']*islands+['Mountain']*mountains:
        t.enter_land(t.details,give(t,name).object_id,cause='declared_fixture')
    check(t);return t


def play(t,name):
    t.active_seat=0;t.phase='main';t.play_land(t.details,give(t,name),t.round_num)
    return t.rules.get(t.land_events[-1]['object_id'])


def fetch(t,f):
    t.active_seat=0;t.phase='main';assert t.activate_ability(0,f.object_id,FETCH);check(t)
    return next(e for e in reversed(t.land_events) if e['kind']=='fetch_resolved')


def choose_island(r):return next(b.object_id for b in r.basics if b.name=='Island')


def stories():
    out=[]
    a=fixture(501);a.shock_land_policy=lambda r:False
    steam=a.enter_land(a.details,give(a,'Steam Vents').object_id,cause='declared_fixture')
    sulfur=play(a,'Sulfur Falls');cast(a,give(a,'Ponder'))
    assert a.rules.get(steam).tapped and a.details.life==40 and a.resources.activations[-1]['source_id']==sulfur.object_id
    b=fixture(502);b.shock_land_policy=lambda r:True;vents=play(b,'Steam Vents');cast(b,give(b,'Ponder'))
    assert b.details.life==38 and b.details.damage_taken==0 and b.resources.activations[-1]['source_id']==vents.object_id
    out.append(('01_shock_and_types','Life payment and typed lands produce different legal mana',
                'Branch 1 declined Steam Vents payment, leaving it tapped at 40 life. Its Island/Mountain types still let Sulfur Falls enter untapped and pay for Ponder. Branch 2 paid 2 life for Steam Vents, then used it for Ponder; life was 38 and damage taken stayed zero.',[a,b]))

    a=fixture(503,1);coast=play(a,'Stormcarved Coast');assert coast.tapped
    b=fixture(504,2);coast=play(b,'Stormcarved Coast');assert not coast.tapped
    c=fixture(505,3);canal=play(c,'Spirebluff Canal');assert canal.tapped
    d=fixture(506,2);d.enter_land(d.details,give(d,'Steam Vents').object_id,cause='declared_fixture')
    sanctuary=play(d,'Mystic Sanctuary');assert not sanctuary.tapped
    e=fixture(507);e.players[2].life=e.players[3].life=0
    e.eliminate(e.players[2],'declared_fixture');e.eliminate(e.players[3],'declared_fixture')
    training=play(e,'Training Center');assert training.tapped
    out.append(('02_entry_boundaries','Entry checks use current other lands, types and opponents',
                'Coast entered tapped with one other land and untapped with two. Canal entered tapped with three other lands. Sanctuary entered untapped with two basic Islands plus Steam Vents (an Island); its graveyard trigger remains deferred. Training Center entered tapped after the table dropped to one opponent.',[a,b,c,d,e]))

    t=fixture(508);f=play(t,'Fabled Passage');assert f.object_id in t.rules.objects and t.details.lands==1
    t.fetch_policy=choose_island;observed=[]
    def watch(seat,frames,choices):
        if frames:observed.append(f.object_id not in t.rules.objects and 'Fabled Passage' in t.details.graveyard)
        return None
    t.priority_policy=watch;r=fetch(t,f)
    assert observed and all(observed) and t.rules.get(r['fetched_id']).tapped
    assert not t.resources.sources(0)
    t.turn_serial+=1;t.safe_runner.new_turn(t.turn_serial);t.resources.untap(0)
    t.note('DIAGNOSTIC NEXT OWN TURN: actual sources untapped; no extra land drop used by fetch.')
    cast(t,give(t,'Ponder'));assert t.resources.activations[-1]['source_id']==r['fetched_id']
    out.append(('03_early_fetch','Passage costs are paid before responses; early basic stays tapped',
                'Playing Passage did not fetch. Activating it tapped/sacrificed it before anyone received priority; the ability then resolved without its source. The first fetched Island entered tapped and provided no immediate mana. After the next declared own-turn untap it paid for Ponder.',[t]))

    t=fixture(509,2,1);cast(t,give(t,'Arcane Adaptation'))
    assert not t.resources.sources(0)
    f=play(t,'Fabled Passage');t.fetch_policy=choose_island;r=fetch(t,f)
    assert r['lands_at_resolution']==4 and r['untapped']
    cast(t,give(t,'Ponder'));assert t.resources.activations[-1]['source_id']==r['fetched_id']
    out.append(('04_fourth_land','Fourth fetched land enters tapped, then untaps and pays for a spell',
                'Three actual sources paid for Adaptation and were tapped. Passage was played and sacrificed. Its fetched Island entered tapped, then untapped because the resulting battlefield had four lands. That exact new source paid for Ponder immediately; Passage itself was not counted.',[t]))

    t=fixture(510,3);f=play(t,'Fabled Passage');target=next(o.object_id for o in t.rules.controlled(0,{'land'}) if o.object_id!=f.object_id)
    give(t,'Capsize');used=[]
    def bounce(seat,frames,choices):
        c=next((c for c in choices if seat==0 and c.kind=='spell' and c.action.source=='Capsize'
                and c.action.target_object==target and not c.action.tags),None)
        if c and not used:used.append(True);return c
    t.priority_policy=bounce;t.fetch_policy=choose_island;r=fetch(t,f)
    assert used and r['lands_at_resolution']==3 and not r['untapped']
    out.append(('05_fetch_response','A response changes the resolution-time untap threshold',
                'Passage began as the fourth land and was sacrificed as a cost. With its ability waiting, source-paid Capsize bounced another Island. The fetched basic still arrived, but the resulting three-land battlefield failed the untap condition, so it stayed tapped.',[t]))

    t=fixture(511);f=play(t,'Fabled Passage');t.fetch_policy=lambda r:None
    before=len(t.details.library);r=fetch(t,f)
    assert r['fetched_id'] is None and len(t.details.library)==before
    assert any(x[0]=='shuffle' for x in t.zones.operations) and 'Fabled Passage' in t.details.graveyard
    out.append(('06_fail_to_find','Failing to find still shuffles and does not refund the sacrifice',
                'The explicit search policy chose no basic, which is legal for the hidden-zone search. Passage remained in the graveyard, no land entered, and the library was shuffled. The activation was not a spell or a draw.',[t]))

    t=fixture(512,2,1);cast(t,give(t,'Young Pyromancer'));cast(t,give(t,'Preordain'))
    count=lambda:sum(o.token and o.card.name=='Elemental' for o in t.rules.on_battlefield())
    assert count()==1 and not t.resources.sources(0)
    f=play(t,'Fabled Passage');t.fetch_policy=choose_island;r=fetch(t,f);assert count()==1
    cast(t,give(t,'Ponder'));assert count()==2 and t.resources.activations[-1]['source_id']==r['fetched_id']
    out.append(('07_cast_interaction','Land play and fetch do not trigger cast engines',
                'Preordain made one Pyromancer Elemental. Playing and activating Passage made none. The fourth fetched Island untapped and paid for Ponder, which made exactly one additional Elemental through the ordinary cast trigger.',[t]))
    for _,_,_,tables in out:
        for t in tables:check(t)
    return out


def write_story(label,title,result,tables):
    branches=[dict(events=t.events,lands=t.land_events,payments=t.resources.payments,
                   activations=t.resources.activations,priority=t.spell_stack.history,
                   final_life=[p.life for p in t.players],fingerprint=fingerprint(t)) for t in tables]
    (ROOT/(label+'.json')).write_text(json.dumps(dict(title=title,result=result,forced=True,consistent=True,branches=branches),indent=2)+'\n')
    lines=['# '+title,'','Forced conserved setup; real deck cards and source payments.','',result,'']
    for i,t in enumerate(tables,1):lines+=['## Branch '+str(i),'','```text',*t.events,'```','']
    (ROOT/(label+'.md')).write_text('\n'.join(lines))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seeds',type=int,default=50)
    parser.add_argument('--benchmark-games',type=int,default=12);args=parser.parse_args()
    if min(args.seeds,args.benchmark_games)<1:parser.error('Counts must be positive')
    audit=write_coverage();records=[]
    for label,title,result,tables in stories():
        write_story(label,title,result,tables);records.append(dict(file=label,title=title,result=result,passed=True))
        print(label,'PASS',flush=True)
    groups=[['aggro','control','combo'],['aggro','tokens','ramp_stompy'],['control','spellslinger','midrange']]
    stops=[];steps=payments=entries=fetches=0;refs=[];simulation_seconds=0;start_all=time.perf_counter()
    for seat in range(4):
        for seed in range(args.seeds):
            kinds=groups[seed%3].copy();kinds.insert(seat,'magnus')
            start=time.perf_counter();t=LandTable(kinds,seed=seed).run(12);simulation_seconds+=time.perf_counter()-start;check(t)
            steps+=len(t.step_history);payments+=len(t.resources.payments)
            entries+=sum(e['kind']=='entry' for e in t.land_events);fetches+=sum(e['kind']=='fetch_resolved' for e in t.land_events)
            refs.append(dict(providers=kinds,seed=seed,rounds=12,sha256=fingerprint(t),reason=t.win_reason,
                             life=[p.life for p in t.players],safety=t.safety_stop))
            if t.safety_stop:stops.append(dict(seat=seat,seed=seed,reason=t.safety_stop))
        print('sweep seat',seat,'complete',flush=True)
    elapsed=time.perf_counter()-start_all;timings={}
    for cls in (EngineTable,LandTable):
        samples=[]
        for seed in range(args.benchmark_games):
            start=time.perf_counter();cls(seed=seed).run(8);samples.append((time.perf_counter()-start)*1000)
        timings[cls.__name__]=round(statistics.median(samples),3)
    reference=dict(format=1,engine='v14 LandTable before additional caching',
                   meaning='Deterministic rules/zone/object/RNG/decision/payment fingerprints. Existing historical caches remain; no new caching added.',cases=refs)
    (ROOT/'REFERENCE_CASES.json').write_text(json.dumps(reference,indent=2)+'\n')
    history=[]
    for version,path,engine in [('v12','v12_combat','CombatTable'),('v13','v13_engines','EngineTable')]:
        old=json.loads((ROOT.parent/path/'validation_results.json').read_text())
        history.append(dict(version=version,engine=engine,games=old['benchmark_games'],rounds=old['benchmark_rounds'],
                            median_ms=old['median_ms'][engine],measurement='historical; host load/time differs'))
    history.append(dict(version='v14',engine='LandTable',games=args.benchmark_games,rounds=8,median_ms=timings['LandTable'],
                        comparator_median_ms=timings['EngineTable'],measurement='same invocation; changed rules alter trajectories'))
    (ROOT/'PERFORMANCE_HISTORY.json').write_text(json.dumps(dict(new_caching=False,entries=history),indent=2)+'\n')
    d=dict(games=len(refs),rounds=12,consistent=True,safety_stops=stops,steps=steps,payments=payments,
           land_entries=entries,fetch_resolutions=fetches,simulation_seconds=round(simulation_seconds,3),
           elapsed_with_reference_seconds=round(elapsed,3),reference_cases=len(refs),new_caching=False,
           benchmark_games=args.benchmark_games,benchmark_rounds=8,median_ms=timings,audit_counts=audit['unique_counts'],
           targeted_scenarios=records,caveat='Infrastructure diagnostics with one detailed deck and synthetic opponents; no win-rate inference.')
    (ROOT/'validation_results.json').write_text(json.dumps(d,indent=2)+'\n')
    lines=['# V14 land interaction results','',f"All {len(records)} targeted narratives passed. Companion JSON includes actual source payments, land events, priority and final reference fingerprints.",'','| Scenario | Observed result |','|---|---|']
    lines += [f"| [{r['title']}]({r['file']}.md) | {r['result']} |" for r in records]
    lines+=['',f"Sweep: {d['games']} twelve-round games; {len(stops)} safety stops; {steps} steps; {payments} source payments; {entries} land entries; {fetches} fetch resolutions. All independent consistency/conservation checks passed.",'',
            f'Exploratory median milliseconds per eight-round game ({args.benchmark_games} samples/engine): {timings}. No additional caching was introduced. Historical figures are preserved separately; rules and host load change trajectories/timing.','',
            f'{len(refs)} deterministic reference fingerprints are saved in REFERENCE_CASES.json for future optimization equivalence checks. Reference serialization is outside benchmark timing.','',d['caveat'],'']
    (ROOT/'INTERACTION_REPORT.md').write_text('\n'.join(lines));print(json.dumps(d,indent=2))


if __name__=='__main__':main()
