"""Forced-board interaction stories plus seeded live-game diagnostics.

Fixtures preserve the real 99-card inventories, use actual source payments and
are explicitly labeled; they are not natural opening or deck-strength results.
"""
import argparse, json, statistics, time
from pathlib import Path
from stepped import StepTable
from gameplay import PriorityTable
from driver import StepDriver
from kernel import WorldEntry

ROOT=Path(__file__).resolve().parent


def check(t):
    t.assert_consistent()
    for p in t.players:
        actual=sum(not o.token and o.owner==p.seat for o in t.rules.objects.values())
        expected=0 if p.eliminated_round is not None else 100 if p is t.details else 99
        assert actual==expected,(t.seed,p.seat,actual,expected)


def give(t,name=None,p=None,effect=None):
    p=p or t.details
    c=next(c for c in p.hand+p.library if (name is None or c.name==name) and (effect is None or c.effect==effect))
    if c not in p.hand:
        oid=t.zones.move(c.object_id,'hand');c=next(c for c in p.hand if c.object_id==oid)
    return c


def cast(t,card,p=None,**options):
    p=p or t.details;t.active_seat=p.seat;t.phase='main';t.step='precombat_main'
    a=t.action_with_options(p,card,**options) if options else t.action_for_card(p,card)
    assert t.cast(a)
    check(t)
    return a


def fixture(seed):
    t=StepTable(seed=seed,trace=True);t.priority_policy=lambda *args:None
    for p in t.players:
        for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
        wanted=['Island']*6+['Mountain']*4 if p is t.details else [None]*8
        for name in wanted:
            c=give(t,name,p,effect='none')
            oid=t.zones.move(c.object_id,'battlefield')
            t.world.views[oid]=WorldEntry(p,None,'resource')
    t.round_num=2;t.turn_serial=1;t.safe_runner.new_turn(1)
    t.note('FORCED-BOARD DIAGNOSTIC: actual deck cards moved to declared source layout; no natural-opening claim.')
    check(t);return t


def next_turn(t):
    t.turn_serial+=1;t.safe_runner.new_turn(t.turn_serial);t.resources.empty_pools()
    t.resources.untap(0);t.active_seat=0;t.phase='main';t.step='precombat_main'
    t.note('  DIAGNOSTIC NEXT TURN: untap the detailed seat\'s actual sources.')


def place(t,name):
    cast(t,give(t,name))
    return next(o.object_id for o in t.rules.on_battlefield() if o.card.name==name)


def opponent_creature(t,seat=1):
    p=t.players[seat];cast(t,give(t,p=p,effect='creature'),p)
    return p.creatures[-1].id


def abrade_story():
    a=fixture(211);target=opponent_creature(a);before=a.rules.get(target).toughness
    damage_action=cast(a,give(a,'Abrade'),mode='damage',target=target)
    damage_recorded=any(e[0]=='abrade_damage' for e in a.rule_events)
    survived=target in a.rules.objects
    # A separate conserved board exercises the other mode with the singleton.
    b=fixture(212);p=b.players[2];cast(b,give(b,p=p,effect='ramp'),p)
    rock=p.permanents[-1];name=rock.name;oid=rock.id
    artifact_action=cast(b,give(b,'Abrade'),mode='artifact',target=oid)
    assert damage_recorded and oid not in b.rules.objects and name in b.players[2].graveyard
    return dict(title='Abrade: announced modes, damage and artifact destruction',
                result=f'Creature mode marked 3 damage on a {before}-toughness creature (survived={survived}); artifact mode destroyed its chosen ramp permanent.',
                checks=dict(damage_mode=damage_recorded,artifact_destroyed=True,mode_locked=damage_action.parameters['mode']=='damage' and artifact_action.parameters['mode']=='artifact')),[a,b]


def buyback_story():
    t=fixture(213);target=opponent_creature(t,2)
    cast(t,give(t,'Capsize'),buyback=True,target=target)
    first=any(c.name=='Capsize' for c in t.details.hand)
    next_turn(t);q=t.players[2];give(t,p=q,effect='counter')
    target=next(o.object_id for o in t.rules.controlled(2,{'land'}))
    t.priority_policy=lambda seat,frames,choices:next((c for c in choices if seat==2 and c.kind=='spell' and c.action.effect=='counter'),None)
    cast(t,give(t,'Capsize'),buyback=True,target=target)
    second='Capsize' in t.details.graveyard
    assert first and second
    return dict(title='Capsize: successful buyback, then a countered recast',
                result='First cast returned the target and Capsize to hand. After an explicitly advanced untap, the second bought-back cast was countered; Capsize entered the graveyard.',
                checks=dict(successful_buyback_return=first,countered_buyback_graveyard=second)),[t]


def adaptation_story():
    t=fixture(214);icon=place(t,'Third Path Iconoclast');place(t,'Harmonic Prodigy');adapt=place(t,'Arcane Adaptation')
    wizard_before='Wizard' in t.rules.subtypes(icon);next_turn(t)
    give(t,'Capsize');give(t,'Preordain');used=[];before=t.details.token_count()
    def policy(seat,frames,choices):
        if seat==0 and frames and not used:
            c=next((c for c in choices if c.kind=='spell' and c.action.source=='Capsize' and c.action.target_object==adapt),None)
            if c:used.append(True)
            return c
    t.priority_policy=policy
    cast(t,give(t,'Preordain'))
    captured=t.details.token_count()-before
    wizard_after='Wizard' in t.rules.subtypes(icon)
    before=t.details.token_count();cast(t,give(t,'Ponder'));later=t.details.token_count()-before
    assert wizard_before and not wizard_after and captured==4 and later==1
    return dict(title='Arcane Adaptation: live Wizard types and captured triggers',
                result='Adaptation made Iconoclast a Wizard. Harmonic Prodigy doubled triggers from Preordain and the responding Capsize (4 Soldiers). Capsize bounced Adaptation; already queued triggers survived. A later Ponder produced only 1 Soldier.',
                checks=dict(wizard_while_enchantment_present=wizard_before,wizard_after_bounce=wizard_after,captured_tokens=captured,later_tokens=later)),[t]


def frantic_story():
    t=fixture(215)
    # Put two known unsupported cards on top to make the declared discard choice
    # deterministic; these cards still come from the same physical inventory.
    for name in ('Underworld Breach','Reiterate'):
        c=give(t,name);t.zones.move(c.object_id,'library')
    cast(t,give(t,'Frantic Search'))
    event=next(e for e in t.rule_events if e[0]=='frantic_search');untapped=tuple(event[2])
    cast(t,give(t,'Young Pyromancer'))
    spent=t.resources.payments[-1]['sources'];reused=set(spent)&set(untapped)
    assert len(untapped)==3 and reused
    return dict(title='Frantic Search: atomic selection, untap and source reuse',
                result=f'Drew 2, discarded 2, untapped 3 actual lands. Young Pyromancer then reused restored source IDs {sorted(reused)} in the same main phase.',
                checks=dict(discarded=event[1],untapped_lands=len(untapped),reused_source_ids=sorted(reused))),[t]


def combat_story():
    t=fixture(216);attacker=place(t,'Goblin Electromancer');blocker=opponent_creature(t,1)
    next_turn(t);t.attack_ready[0]={attacker};t.active_seat=0;t.phase='combat';t.step='declare_attackers'
    t.combat_engine.declare_attackers(t.details,[(attacker,1)])
    t.step='declare_blockers';t.combat_engine.declare_blockers([(attacker,blocker)])
    give(t,'Capsize');used=[]
    def policy(seat,frames,choices):
        if seat==0 and not used:
            c=next((c for c in choices if c.kind=='spell' and c.action.source=='Capsize' and c.action.target_object==blocker),None)
            if c:used.append(True)
            return c
    t.priority_policy=policy;t.spell_stack.holder=0;t.spell_stack.resolve()
    before=t.players[1].life;t.step='combat_damage';record=t.combat_engine.damage(t.details)
    t.spell_stack.checkpoint();check(t)
    assert used and blocker not in t.rules.objects and t.players[1].life==before and record['player_damage']=={}
    return dict(title='Combat: response after blocks and persistent blocked status',
                result='Goblin Electromancer was blocked. Capsize bounced the blocker in the post-block priority window. The attacker remained blocked and dealt zero player damage (no trample).',
                checks=dict(blocker_bounced=True,attacker_still_blocked=t.combat_engine.attacks[0].blocked,player_damage=record['player_damage'])),[t]


STORIES=[('01_abrade_modes',abrade_story),('02_capsize_buyback',buyback_story),
         ('03_adaptation_triggers',adaptation_story),('04_frantic_mana',frantic_story),('05_combat_response',combat_story)]


def write_story(label,record,tables,forced=True):
    data=dict(record=record,fixture='forced conserved board; actual source payments' if forced else 'unforced seeded live game',
              branches=[dict(events=t.events,priority=t.spell_stack.history,steps=t.step_history,
                             combat=t.combat_batches,diagnostics=t.diagnostics()) for t in tables])
    (ROOT/(label+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    lines=['# '+record['title'],'', '**Forced-board interaction diagnostic; not an unbiased opening.**' if forced else '**Unforced seeded live game; synthetic opponents and declared coverage limits apply.**', '',record['result'],'']
    for i,t in enumerate(tables,1):
        lines+=['## Branch '+str(i),'','```text',*t.events,'```','']
    (ROOT/(label+'.md')).write_text('\n'.join(lines))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke-seeds',type=int,default=50)
    parser.add_argument('--benchmark-games',type=int,default=20);parser.add_argument('--narratives-only',action='store_true')
    args=parser.parse_args()
    records=[]
    for label,story in STORIES:
        record,tables=story()
        for t in tables:check(t)
        write_story(label,record,tables);records.append(record)
        print(label,record['checks'],flush=True)
    live=[]
    for seed in (102,104):
        t=StepTable(seed=seed,trace=True).run(10);check(t)
        label='live_seed_'+str(seed)
        record=dict(title=f'Unforced live game, seed {seed}',result=f'{t.win_reason}; safety={t.safety_stop}; steps={len(t.step_history)}',
                    checks=dict(consistent=True,safety_stop=t.safety_stop))
        write_story(label,record,[t],forced=False);live.append(record)
    if args.narratives_only:return
    if min(args.smoke_seeds,args.benchmark_games)<1:parser.error('Counts must be positive')
    groups=[['aggro','control','combo'],['aggro','tokens','ramp_stompy'],['control','spellslinger','midrange']]
    stops=[];steps=batches=payments=rule_events=0;start=time.perf_counter()
    for seat in range(4):
        for seed in range(args.smoke_seeds):
            kinds=groups[seed%3].copy();kinds.insert(seat,'magnus')
            t=StepTable(kinds,seed=seed).run(12);check(t)
            steps+=len(t.step_history);batches+=len(t.combat_batches);payments+=len(t.resources.payments);rule_events+=len(t.rule_events)
            if t.safety_stop:stops.append(dict(seat=seat,seed=seed,reason=t.safety_stop))
        print('sweep seat',seat,'complete',flush=True)
    elapsed=time.perf_counter()-start;timings={}
    for engine in (PriorityTable,StepTable):
        times=[]
        for seed in range(args.benchmark_games):
            start=time.perf_counter();engine(seed=seed).run(8);times.append((time.perf_counter()-start)*1000)
        timings[engine.__name__]=round(statistics.median(times),3)
    report=dict(smoke_games=args.smoke_seeds*4,rounds=12,consistent=True,safety_stops=stops,
                steps=steps,combat_batches=batches,payments=payments,expanded_rule_events=rule_events,
                elapsed_seconds=round(elapsed,3),benchmark_games=args.benchmark_games,benchmark_rounds=8,
                median_ms=timings,forced_scenarios=records,unforced_games=live,
                caveat='Infrastructure diagnostics; not empirical Commander win rates')
    (ROOT/'validation_results.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# V11 interaction results','','Five forced-board scenarios passed. Each preserves inventories and pays from actual source objects.','',
           '| Scenario | Observed result |','|---|---|']
    for record in records:lines.append('| '+record['title']+' | '+record['result']+' |')
    lines+=['',f"Seeded sweep: {report['smoke_games']} twelve-round games; {len(stops)} safety stops; {steps} exposed steps; {batches} combat batches. Physical cards, zones, spell frames and mana pools passed consistency checks.",
            '',f'Exploratory median milliseconds per eight-round game: {timings}.',
            '', 'Ordinary timing and the declared card subsets are covered. Multiple blockers, first/double strike, trample, copied spells, broad buyback/choice/layer coverage and multiple real decks remain out of scope. No deck-power inference.']
    (ROOT/'INTERACTION_REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('forced_scenarios','unforced_games')},indent=2))


if __name__=='__main__':main()
