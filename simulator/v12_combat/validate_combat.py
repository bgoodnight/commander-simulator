"""Explicit synthetic combat fixtures, real-source responses and live sweep.

No named trample/strike cards are added by these fixtures. Physical deck
inventories stay conserved; fixture creatures are explicitly synthetic tokens.
"""
import argparse
import json
import statistics
import time
from dataclasses import replace
from pathlib import Path
from expanded import CombatTable
from stepped import StepTable
from combat_turns import CombatDriver
from kernel import WorldEntry
import importlib.util
_spec=importlib.util.spec_from_file_location('v11_validation_helpers',Path(__file__).resolve().parents[1]/'v11_steps'/'validate.py')
_helpers=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_helpers)
check,give,cast=_helpers.check,_helpers.give,_helpers.cast
from audit import write as write_audit

ROOT=Path(__file__).resolve().parent


def fixture(seed):
    t=CombatTable(seed=seed,trace=True);t.priority_policy=lambda *args:None
    for p in t.players:
        for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
        names=['Island']*6+['Mountain']*4 if p is t.details else [None]*8
        for name in names:
            card=give(t,name,p,effect='none');oid=t.zones.move(card.object_id,'battlefield')
            t.world.views[oid]=WorldEntry(p,None,'resource')
    t.round_num=2;t.turn_serial=1;t.safe_runner.new_turn(1)
    t.active_seat=0;t.phase='combat'
    t.note('FORCED DIAGNOSTIC: actual deck source layout; declared synthetic combat tokens/keyword grants. Not a natural opening or newly supported named card.')
    check(t);return t


def board(t,power,toughness,keywords,blockers):
    a=t.add_creature(t.details,power,toughness,'Synthetic attacker',token=True,keywords=keywords)
    bs=[t.add_creature(t.players[1],p,th,'Synthetic blocker',token=True) for p,th in blockers]
    t.attack_ready[0]={a.id};t.active_seat=0;t.phase='combat'
    t.combat_engine.declare_attackers(t.details,[(a.id,1)])
    t.combat_engine.declare_blockers([(a.id,b.id) for b in bs])
    return a,bs


def response_policy(t,spell,target,step):
    give(t,spell);used=[]
    def policy(seat,frames,choices):
        if seat!=0 or t.step!=step or frames or used:return None
        choice=next((c for c in choices if c.kind=='spell' and c.action.source==spell
                     and c.action.target_object==target
                     and (not c.action.tags if spell=='Capsize' else c.action.parameters.get('mode')=='damage')),None)
        if choice:used.append(True)
        return choice
    t.priority_policy=policy
    return used


def stories():
    result=[]
    t=fixture(301);a,bs=board(t,4,8,(),[(2,3),(3,4)])
    t.combat_damage_policy=lambda ctx:{bs[0].id:1,bs[1].id:3}
    CombatDriver(t).damage_steps(t.details);check(t)
    assert all(b.id in t.rules.objects for b in bs) and t.rules.get(a.id).damage_marked==5
    result.append(('01_free_assignment','Multiple blockers: legal nonlethal split',
                   'The 4/8 attacker assigned 1 and 3 damage to 2/3 and 3/4 blockers. Both survived; their simultaneous return damage marked 5 on the attacker. No damage assignment order was imposed.',t))

    t=fixture(302);a,bs=board(t,8,8,('trample',),[(2,2),(3,3)])
    used=response_policy(t,'Capsize',bs[1].id,'declare_blockers')
    t.step='declare_blockers';t.spell_stack.resolve()
    CombatDriver(t).damage_steps(t.details);check(t)
    assert used and t.players[1].life==34 and bs[1].id not in t.rules.objects
    result.append(('02_trample_bounce','Trample recalculates after blocker bounce',
                   'After two blockers were declared, Capsize bounced the 3/3 token (it ceased to exist). The 8-power trampler assigned 2 to the remaining 2/2 and 6 to the defending player. Capsize paid from actual lands.',t))

    t=fixture(303);a,bs=board(t,4,8,('double_strike','trample'),[(1,6)])
    CombatDriver(t).damage_steps(t.details);check(t)
    assert t.players[1].life==38 and bs[0].id not in t.rules.objects
    result.append(('03_two_step_trample','Double strike uses damage marked in the first step',
                   'First-strike damage marked 4 on the 1/6 blocker. In the normal damage step, another 2 was lethal; the remaining 2 trampled through. The blocker dealt 1 back only in the normal step.',t))

    t=fixture(304);a,bs=board(t,3,8,('double_strike',),[(1,5)])
    used=response_policy(t,'Abrade',bs[0].id,'first_strike_damage')
    CombatDriver(t).damage_steps(t.details);check(t)
    assert used and bs[0].id not in t.rules.objects and t.players[1].life==40
    result.append(('04_abrade_between_steps','Abrade between damage steps preserves blocked status',
                   'The double-striker marked 3 in the first step. Abrade then dealt 3 using actual source mana, killing the 1/5 blocker before it could retaliate. The attacker remained blocked and had no trample, so its second step dealt no player damage.',t))

    t=fixture(305);card=t.zones.views(0,'command')[0]
    cast(t,card);a=next(c for c in t.details.creatures if c.name=='Magnus the Red')
    obj=t.rules.get(a.id);obj.card=replace(obj.card,keywords=obj.card.keywords|{'double_strike'});t.rules._dirty()
    t.note('SYNTHETIC KEYWORD GRANT: double_strike added to the actual Magnus object for trigger testing; no printed grant card claimed.')
    t.attack_ready[0]={a.id};t.active_seat=0;t.phase='combat'
    t.combat_engine.declare_attackers(t.details,[(a.id,1)]);t.combat_engine.declare_blockers([])
    CombatDriver(t).damage_steps(t.details);check(t)
    assert t.players[1].life==32 and sum(c.name=='Spawn' for c in t.details.creatures)==2
    result.append(('05_magnus_two_hits','Two damage steps create two Magnus triggers',
                   'Actual Magnus received an explicitly synthetic double-strike grant. Each 4-damage hit queued its own printed token trigger. Priority resolved one Spawn after each step: 8 player damage, 2 Spawn total.',t))

    t=fixture(306);card=t.zones.views(0,'command')[0]
    cast(t,card);a=next(c for c in t.details.creatures if c.name=='Magnus the Red')
    obj=t.rules.get(a.id);obj.card=replace(obj.card,keywords=obj.card.keywords|{'double_strike'});t.rules._dirty()
    t.note('SYNTHETIC KEYWORD GRANT: double_strike on Magnus; source-paid self-bounce is the interruption under test.')
    t.attack_ready[0]={a.id};t.active_seat=0;t.phase='combat'
    t.combat_engine.declare_attackers(t.details,[(a.id,1)]);t.combat_engine.declare_blockers([])
    used=response_policy(t,'Capsize',a.id,'first_strike_damage')
    CombatDriver(t).damage_steps(t.details);check(t)
    assert used and t.players[1].life==36 and sum(c.name=='Spawn' for c in t.details.creatures)==1
    assert any(c.name=='Magnus the Red' for c in t.details.hand)
    result.append(('06_magnus_interrupted','Capsize after first hit prevents the second hit',
                   'The first 4-damage hit resolved its Spawn trigger. Capsize then returned Magnus to hand using actual lands and the token discount. The scheduled normal damage step still occurred, but the departed attacker dealt nothing: 4 damage, 1 Spawn.',t))
    return result


def write_story(label,title,outcome,t):
    payload=dict(title=title,forced=True,outcome=outcome,consistent=True,
                 fixture_limits='Synthetic combat tokens or keyword grants; real-source spell costs; conserved physical inventories.',
                 combat_batches=t.combat_batches,steps=t.step_history,payments=t.resources.payments,
                 priority=t.spell_stack.history,narrative=t.events)
    # Existing trace storage is the table transcript, not an independent event state.
    (ROOT/(label+'.json')).write_text(json.dumps(payload,indent=2,default=str)+'\n')
    lines=['# '+title,'','Forced diagnostic with declared synthetic combat setup. Physical decks remain conserved; spell responses use actual sources.','',outcome,'','## Narrative','']
    lines += ['```text',*t.events,'```']
    (ROOT/(label+'.md')).write_text('\n'.join(lines)+'\n')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seeds',type=int,default=50)
    parser.add_argument('--benchmark-games',type=int,default=12);args=parser.parse_args()
    if min(args.seeds,args.benchmark_games)<1:parser.error('Counts must be positive')
    audit=write_audit();records=[]
    for label,title,outcome,t in stories():
        write_story(label,title,outcome,t);records.append(dict(file=label,title=title,result=outcome,passed=True))
        print(label,'PASS',flush=True)
    groups=[['aggro','control','combo'],['aggro','tokens','ramp_stompy'],['control','spellslinger','midrange']]
    stops=[];steps=batches=multi=payments=0;start=time.perf_counter()
    for seat in range(4):
        for seed in range(args.seeds):
            kinds=groups[seed%3].copy();kinds.insert(seat,'magnus')
            t=CombatTable(kinds,seed=seed).run(12);check(t)
            steps+=len(t.step_history);batches+=len(t.combat_batches);payments+=len(t.resources.payments)
            multi+=sum(any(len(a[3])>1 for a in b['attackers']) for b in t.combat_batches)
            if t.safety_stop:stops.append(dict(seat=seat,seed=seed,reason=t.safety_stop))
        print('sweep seat',seat,'complete',flush=True)
    elapsed=time.perf_counter()-start;timings={}
    for cls in (StepTable,CombatTable):
        samples=[]
        for seed in range(args.benchmark_games):
            start=time.perf_counter();cls(seed=seed).run(8);samples.append((time.perf_counter()-start)*1000)
        timings[cls.__name__]=round(statistics.median(samples),3)
    data=dict(games=4*args.seeds,rounds=12,consistent=True,safety_stops=stops,steps=steps,
              damage_batches=batches,multi_block_batches=multi,payments=payments,elapsed_seconds=round(elapsed,3),
              benchmark_games=args.benchmark_games,benchmark_rounds=8,median_ms=timings,
              audit_counts=audit['unique_counts'],targeted_scenarios=records,
              caveat='Synthetic strike/trample fixtures validate mechanics; unforced detailed deck has no newly enabled keyword cards. No win-rate inference.')
    (ROOT/'validation_results.json').write_text(json.dumps(data,indent=2)+'\n')
    lines=['# V12 interaction results','',f"All {len(records)} targeted scenarios passed. See the linked Markdown stories and companion JSON for exact source payments, stack history and damage batches.",'','| Scenario | Observed result |','|---|---|']
    lines += [f"| [{r['title']}]({r['file']}.md) | {r['result']} |" for r in records]
    lines += ['',f"Live sweep: {data['games']} twelve-round games, all four Magnus seats; {len(stops)} safety stops; {steps} steps; {batches} damage batches including {multi} with multiple declared blockers; {payments} source payments. Physical cards, zones, spell frames and mana pools passed consistency checks.",'',
              f'Exploratory median milliseconds per eight-round game ({args.benchmark_games} samples/engine): {timings}. Changed blocking decisions change trajectories, so this is not an isolated microbenchmark.','',data['caveat'],'']
    (ROOT/'INTERACTION_REPORT.md').write_text('\n'.join(lines));print(json.dumps(data,indent=2))


if __name__=='__main__':main()
