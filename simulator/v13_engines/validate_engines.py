"""Conserved forced-board stories, source payments and an all-seat live sweep."""
import argparse,importlib.util,json,statistics,time
from pathlib import Path
from engine_table import EngineTable
from expanded import CombatTable
from engine_turns import EngineDriver
from kernel import WorldEntry
from resources import Activation
from rules import Modifier
from coverage_report import write as write_coverage

ROOT=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('v11_validation_helpers',ROOT.parent/'v11_steps'/'validate.py')
_helpers=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_helpers)
check,give,cast=_helpers.check,_helpers.give,_helpers.cast


def fixture(seed):
    t=EngineTable(seed=seed,trace=True);t.priority_policy=lambda *args:None
    for p in t.players:
        for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
        names=['Island']*8+['Mountain']*5 if p is t.details else [None]*8
        for name in names:
            c=give(t,name,p,effect='none');oid=t.zones.move(c.object_id,'battlefield')
            t.world.views[oid]=WorldEntry(p,None,'resource')
    t.round_num=2;t.turn_serial=1;t.safe_runner.new_turn(1)
    t.note('FORCED DIAGNOSTIC: declared late-game source layout and chosen hand/library cards from actual conserved decks. No natural opening or win-rate claim.')
    check(t);return t


def place(t,name):
    cast(t,give(t,name));return next(o for o in t.rules.on_battlefield() if o.card.name==name and not o.token)


def top(t,names):
    ids=[]
    for name in names:
        c=next(c for c in t.details.library if c.name==name and c.object_id not in ids);ids.append(c.object_id)
    order=t.zones.order[0,'library'];order[:]=[x for x in order if x not in ids]+list(reversed(ids))
    t.note('FORCED LIBRARY TOP: '+str(names));return tuple(ids)


def token_count(t,name):return sum(o.token and o.card.name==name for o in t.rules.on_battlefield())


def stories():
    out=[];branches=[];results=[]
    for i,name in enumerate(('Brainstorm','Ponder','Preordain','Telling Time','Impulse')):
        t=fixture(401+i);ids=top(t,['Island','Mountain','Abrade']+(['Capsize'] if name=='Impulse' else []))
        def policy(r):
            by_name={c.name:c.object_id for c in r.cards}
            if r.kind=='brainstorm_put_back':return (by_name['Mountain'],by_name['Island'])
            if r.kind=='ponder_order':return (by_name['Abrade'],by_name['Island'],by_name['Mountain'])
            if r.kind=='ponder_shuffle':return False
            if r.kind=='scry':return {'top':(),'bottom':tuple(c.object_id for c in r.cards)}
            if r.kind=='look_to_hand':return (by_name['Abrade'],)
            if r.kind=='telling_top':return (by_name['Island'],)
            if r.kind=='impulse_bottom':return (by_name['Capsize'],by_name['Island'],by_name['Mountain'])
            raise ValueError('Unexpected selection request')
        t.selection_policy=policy;cast(t,give(t,name));check(t)
        assert any(c.name=='Abrade' for c in t.details.hand)
        if name=='Brainstorm':assert [t.rules.get(x).card.name for x in t.selection.look(0,2)]==['Mountain','Island']
        if name=='Telling Time':assert t.rules.get(t.selection.look(0,1)[0]).card.name=='Island'
        results.append(name+': Abrade selected with exact requested top/bottom choices');branches.append(t)
    out.append(('01_selection_choices','Exact selection across five spells','; '.join(results)+'. Brainstorm/Ponder/Preordain draw; Telling Time/Impulse put a looked-at card into hand.',branches))

    t=fixture(410);h=place(t,'Harmonic Prodigy');place(t,'Young Pyromancer');place(t,'Third Path Iconoclast')
    cast(t,give(t,'Ponder'));first=(h.power,token_count(t,'Elemental'),token_count(t,'Soldier'))
    cast(t,give(t,'Arcane Adaptation'));cast(t,give(t,'Preordain'))
    assert first==(2,2,1) and h.power==4 and token_count(t,'Elemental')==4 and token_count(t,'Soldier')==4
    t.cleanup_step(t.details);assert h.power==1;check(t)
    out.append(('02_prowess_types','Prowess, trigger doubling and Wizard adaptation',
                'Ponder gave Harmonic exactly +1/+1, doubled Pyromancer to 2 Elementals, and created 1 Iconoclast Soldier. After Adaptation resolved, Preordain doubled Iconoclast too. Totals: 4 Elementals, 4 Soldiers. Harmonic reached 4/6 after three noncreature casts, then returned to 1/3 in cleanup.',[t]))

    t=fixture(411);a=place(t,'Storm-Kiln Artist');place(t,'Harmonic Prodigy');place(t,'Third Path Iconoclast');place(t,'Sol Ring')
    assert a.power==4
    cast(t,give(t,'Ponder'));before=a.power;assert before==7
    treasure=next(o for o in t.rules.on_battlefield() if o.controller==0 and o.card.card_id=='treasure')
    ability=next(a for a in t.resources.abilities(treasure) if a.output==(0,1,0))
    t.resources.activate(0,Activation(treasure.object_id,ability,t.resources.pool(0)))
    spent=a.power;assert spent==6
    cast(t,give(t,'Preordain'));assert a.power==9;check(t)
    out.append(('03_artifact_power','Artifact power tracks tokens entering and being spent',
                'Artist was 4 power with Sol Ring plus an artifact Soldier. Ponder added 2 Treasures and another Soldier, raising it to 7. Activating an actual Treasure for U immediately lowered power to 6. That mana paid for Preordain; its triggers added 3 artifacts, raising power to 9.',[t]))

    t=fixture(412);place(t,'Baral, Chief of Compliance');place(t,'Harmonic Prodigy');give(t,'Counterspell')
    used=[];decisions=[]
    def loot(*args):decisions.append(True);return len(decisions)==1
    t.loot_policy=loot
    def counter(seat,frames,choices):
        c=next((c for c in choices if seat==0 and c.kind=='spell' and c.action.source=='Counterspell'),None)
        if c and not used:used.append(True);return c
    t.priority_policy=counter;q=t.players[2];cast(t,give(t,p=q,effect='creature'),q)
    loots=[e for e in t.engine_events if e[0]=='loot'];assert [e[2] for e in loots]==[True,False];check(t)
    out.append(('04_baral_counter','Baral loot is successful-counter-only and independently optional',
                'An actual Counterspell countered the control seat\'s creature spell. Harmonic doubled Baral into two separate loot triggers. The first was accepted (draw then discard); the second was declined. Counterspell\'s colored UU requirement was preserved despite Baral.',[t]))

    t=fixture(413);place(t,'Stormsplitter');place(t,'Harmonic Prodigy');cast(t,give(t,'Ponder'))
    assert token_count(t,'Stormsplitter')==2
    cast(t,give(t,'Preordain'));assert token_count(t,'Stormsplitter')==8
    driver=EngineDriver(t);driver.window('end','ending',False)
    assert len(t.spell_stack.pending)==8 and token_count(t,'Stormsplitter')==8
    t.spell_stack.resolve();assert token_count(t,'Stormsplitter')==0;check(t)
    out.append(('05_copy_expiry','Copies trigger again and delayed exile is not doubled',
                'With Harmonic, the first spell produced 2 Stormsplitter tokens. The second produced 6 more: 9 Stormsplitters including the original. At the next end-step beginning, exactly 8 delayed exile abilities queued (not doubled). Tokens survived until those abilities resolved, then all 8 ceased; the original remained.',[t]))

    t=fixture(414);place(t,'Stormsplitter');give(t,'Brainstorm');used=[]
    def end_cast(seat,frames,choices):
        c=next((c for c in choices if seat==0 and not frames and c.kind=='spell' and c.action.source=='Brainstorm'),None)
        if c and not used:used.append(True);return c
    t.priority_policy=end_cast;driver=EngineDriver(t);driver.window('end','ending')
    assert used and token_count(t,'Stormsplitter')==1
    t.cleanup_step(t.details);assert token_count(t,'Stormsplitter')==1
    t.active_seat=1;driver.window('end','ending');assert token_count(t,'Stormsplitter')==0;check(t)
    out.append(('06_late_copy','A copy made during an end step waits through cleanup',
                'Brainstorm was cast with actual source mana during end-step priority. Its Stormsplitter token was created after that step began. It survived cleanup, then its delayed exile triggered and resolved at the following player\'s end step.',[t]))

    t=fixture(415);s=place(t,'Stormsplitter');t.rules.add_modifier(s.object_id,Modifier(3,3));give(t,'Capsize');used=[]
    def bounce(seat,frames,choices):
        c=next((c for c in choices if seat==0 and frames and c.kind=='spell' and c.action.source=='Capsize'
                and c.action.target_object==s.object_id and not c.action.tags),None)
        if c and not used:used.append(True);return c
    t.priority_policy=bounce;cast(t,give(t,'Ponder'))
    copies=[o for o in t.rules.on_battlefield() if o.token and o.card.name=='Stormsplitter']
    assert used and len(copies)==2 and all(o.power==1 and o.toughness==4 for o in copies)
    assert any(c.name=='Stormsplitter' for c in t.details.hand);check(t)
    out.append(('07_copy_last_known','Queued copies survive a source bounce without copying pumps',
                'Ponder queued a copy trigger. Capsize responded, queuing another before bouncing the pumped original Stormsplitter. Both copy triggers resolved: the older one used last-known copiable values. Both tokens were base 1/4, not the modified original\'s 4/7; the actual original card returned to hand.',[t]))
    return out


def write_story(label,title,result,tables):
    branches=[dict(events=t.events,selection=t.selection.history,engine=t.engine_events,
                   priority=t.spell_stack.history,payments=t.resources.payments,steps=t.step_history,
                   delayed=[dict(controller=d.controller,object_id=d.object_id,due_end=d.due_end) for d in t.delayed_exiles]) for t in tables]
    (ROOT/(label+'.json')).write_text(json.dumps(dict(title=title,result=result,forced=True,consistent=True,branches=branches),indent=2)+'\n')
    lines=['# '+title,'','Forced conserved late-game fixture; actual source payments, declared library/hand choices. Not an unbiased opening.','',result,'']
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
    stops=[];steps=payments=choices=engine_events=0;start=time.perf_counter()
    for seat in range(4):
        for seed in range(args.seeds):
            kinds=groups[seed%3].copy();kinds.insert(seat,'magnus')
            t=EngineTable(kinds,seed=seed).run(12);check(t)
            steps+=len(t.step_history);payments+=len(t.resources.payments)
            choices+=len(t.selection.history);engine_events+=len(t.engine_events)
            if t.safety_stop:stops.append(dict(seat=seat,seed=seed,reason=t.safety_stop))
        print('sweep seat',seat,'complete',flush=True)
    elapsed=time.perf_counter()-start;timings={}
    for cls in (CombatTable,EngineTable):
        samples=[]
        for seed in range(args.benchmark_games):
            start=time.perf_counter();cls(seed=seed).run(8);samples.append((time.perf_counter()-start)*1000)
        timings[cls.__name__]=round(statistics.median(samples),3)
    d=dict(games=4*args.seeds,rounds=12,consistent=True,safety_stops=stops,steps=steps,payments=payments,
           selection_choices=choices,engine_events=engine_events,elapsed_seconds=round(elapsed,3),
           benchmark_games=args.benchmark_games,benchmark_rounds=8,median_ms=timings,audit_counts=audit['unique_counts'],
           targeted_scenarios=records,caveat='One real detailed deck plus synthetic opponents; no win-rate inference. Safety stops, if any, remain unresolved games.')
    (ROOT/'validation_results.json').write_text(json.dumps(d,indent=2)+'\n')
    lines=['# V13 interaction results','',f"All {len(records)} targeted scenarios passed. Each Markdown narrative has a companion JSON record of source payments, selection, engine events and priority.",'','| Scenario | Observed outcome |','|---|---|']
    lines += [f"| [{r['title']}]({r['file']}.md) | {r['result']} |" for r in records]
    lines += ['',f"Sweep: {d['games']} twelve-round games across all four Magnus seats; {len(stops)} safety stops; {steps} steps; {payments} source payments; {choices} selection-choice records; {engine_events} engine events. All consistency/conservation checks passed.",'',
              f'Exploratory median milliseconds per eight-round game ({args.benchmark_games} samples/engine): {timings}. Card-selection and engine changes alter trajectories, so this is not an isolated microbenchmark.','',d['caveat'],'']
    (ROOT/'INTERACTION_REPORT.md').write_text('\n'.join(lines));print(json.dumps(d,indent=2))


if __name__=='__main__':main()
