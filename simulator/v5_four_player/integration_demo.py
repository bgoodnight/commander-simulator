"""Demonstrates the shared action/event interface using named actual-card examples.
This does NOT simulate the real Magnus deck or claim complete card-text support.
"""
from simulation import Table,CardSpec,Action

def demonstrate():
    t=Table(['aggro','control','combo','ramp_stompy'],seed=42,trace=True)
    p=t.players[0];q=t.players[1];p.mana=8
    p.hand=[
        CardSpec('Young Pyromancer','actual_card',2,'creature','creature',{'power':2,'toughness':1},{'R':1}),
        CardSpec('Preordain','actual_card',1,'sorcery','draw',{'cards':1},{'U':1}),
        CardSpec('Pongify','actual_card',1,'instant','pongify',{}, {'U':1}),
    ]
    q.creatures=[]
    victim=t.add_creature(q,7,7,'Opposing 7/7',False)
    def pyro_trigger(table,event,action,data):
        if (event=='spell_cast' and action is not None and action.actor==p.seat and
            action.card_type in ('instant','sorcery') and
            any(c.name=='Young Pyromancer' for c in p.creatures)):
            table.add_creature(p,1,1,'Pyromancer Elemental',token=True)
    def pongify(table,action):
        target=table.players[action.target]
        original=next((c for c in target.creatures if c.id==action.target_object),None)
        if original:
            table.kill_creature(target,original)
            table.add_creature(target,3,3,'Pongify Ape',token=True)
    t.on_event(pyro_trigger);t.register_effect('pongify',pongify)
    assert t.cast(t.build_action(p,p.hand[0]))
    assert t.cast(t.build_action(p,next(c for c in p.hand if c.name=='Preordain')))
    pong=t.build_action(p,next(c for c in p.hand if c.name=='Pongify'))
    pong.target=q.seat;pong.target_object=victim.id
    assert t.cast(pong)
    assert any(c.name=='Pongify Ape' for c in q.creatures)
    assert sum(c.name=='Pyromancer Elemental' for c in p.creatures)==2
    return {'source':['Young Pyromancer','Preordain','Pongify'],
            'effects':['pre-resolution cast triggers','draw on resolve','creature-to-Ape removal'],
            'trace':t.events,'p_creatures':[c.name for c in p.creatures],
            'q_creatures':[c.name for c in q.creatures]}
if __name__=='__main__':
    import json
    from simulation import ROOT
    data=demonstrate();(ROOT/'integration_demo_results.json').write_text(json.dumps(data,indent=2))
    print(json.dumps(data,indent=2))
