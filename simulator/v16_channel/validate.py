"""Focused channel stories and all-seat state-conservation sweep."""
import importlib.util, json, statistics, time
from pathlib import Path
from channel_table import ChannelTable, OTAWARA, SOKENZAN
from utility_table import UtilityTable

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('helpers', ROOT.parent/'v11_steps'/'validate.py')
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)

def fixture(seed, lands):
    t = ChannelTable(seed=seed, trace=True)
    t.priority_policy = lambda *args: None
    for p in t.players:
        for oid in t.zones.ids(p.seat, 'hand'): t.zones.move(oid, 'library')
    for name in lands: t.enter_land(t.details, h.give(t, name).object_id, cause='declared_fixture')
    t.active_seat=0; t.phase='main'; t.spell_stack.holder=0
    return t

def use(t, name, target=None):
    oid=h.give(t,name).object_id
    c=next(c for c in t.priority_choices(0) if c.kind=='channel' and c.source_id==oid and c.target_frame==target)
    t.commit_choice(0,c)


def main():
    narratives=[]
    t=fixture(1601,['Mountain']*4);use(t,SOKENZAN.name)
    assert len(t.resources.payments)>0
    t.spell_stack.resolve();h.check(t)
    assert len([o for o in t.rules.controlled(0) if o.card.name=='Spirit'])==2
    narratives.append(('Sokenzan creates Spirits', 'Four actual Mountains pay for channel; the discarded land remains in the graveyard and two hasty Spirit tokens enter.',t))
    t=fixture(1602,['Island']*4)
    target=t.add_creature(t.players[1],2,2,'fixture target',token=True)
    use(t,OTAWARA.name,target.id)
    t.note('SYNTHETIC RESPONSE: target destroyed while the channel ability waits.')
    t.world.move(target.id,'graveyard','destroy');t.spell_stack.resolve();h.check(t)
    assert t.spell_stack.fizzled==1 and len(t.resources.payments)>0
    narratives.append(('Otawara target removed', 'Four actual Islands pay for channel; a synthetic response removes the target and the waiting ability fails its legality check.',t))
    lines=['# V16 channel interaction report','','Forced fixtures; actual land payments. The target removal is explicitly synthetic.','']
    for title,desc,t in narratives:
        lines += ['## '+title,'',desc,'','```text',*t.events,'```','']
    groups=[['aggro','control','combo'],['aggro','tokens','ramp_stompy'],['control','spellslinger','midrange']]
    start=time.perf_counter();stops=[];actions=0
    for seat in range(4):
        for seed in range(50):
            kinds=groups[seed%3].copy();kinds.insert(seat,'magnus')
            t=ChannelTable(kinds,seed=seed).run(12);h.check(t)
            actions+=sum(x[0]=='push' and x[2]=='activated' and 'channel_' in x[4] for x in t.spell_stack.history)
            if t.safety_stop:stops.append([seat,seed,t.safety_stop])
        print('seat',seat,'complete',flush=True)
    elapsed=round(time.perf_counter()-start,3);times={}
    for cls in (UtilityTable,ChannelTable):
        values=[]
        for seed in range(12):
            start=time.perf_counter();cls(seed=seed).run(8);values.append((time.perf_counter()-start)*1000)
        times[cls.__name__]=round(statistics.median(values),3)
    data={'games':200,'rounds':12,'safety_stops':stops,'channel_activations':actions,'elapsed_seconds':elapsed,'median_ms_8_rounds_12_samples':times}
    (ROOT/'validation_results.json').write_text(json.dumps(data,indent=2)+'\n')
    lines += [f"200 games: {len(stops)} safety stops; {actions} channel activations. Median eight-round milliseconds: {times}. Different game trajectories limit comparisons.",'', 'Token color is not represented in the current kernel.','']
    (ROOT/'INTERACTION_REPORT.md').write_text('\n'.join(lines))
    print(json.dumps(data),flush=True)
    if stops: raise RuntimeError('Sweep safety stops')
if __name__=='__main__':main()
