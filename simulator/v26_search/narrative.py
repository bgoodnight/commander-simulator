"""Two source-paid tutor chains with Young Pyromancer."""
import importlib.util
from pathlib import Path
from search_table import SearchTable,MERCHANT,SOLVE
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('helpers',root.parent/'v11_steps'/'validate.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
t=SearchTable(seed=2602,trace=True);t.priority_policy=lambda *a:None
for p in t.players:
 for oid in t.zones.ids(p.seat,'hand'):t.zones.move(oid,'library')
for name in ['Island']*8+['Mountain']*4:t.enter_land(t.details,h.give(t,name).object_id,cause='declared_fixture')
h.cast(t,h.give(t,'Young Pyromancer'))
def tutor(req):
 name={'merchant_scroll':'Consider','solve_equation':"Ral's Reinforcements"}[req.kind]
 return next(c.object_id for c in req.cards if c.name==name)
t.tutor_policy=tutor
h.cast(t,h.give(t,MERCHANT));assert 'Consider' in [c.name for c in t.details.hand]
h.cast(t,h.give(t,'Consider'))
h.cast(t,h.give(t,SOLVE));assert "Ral's Reinforcements" in [c.name for c in t.details.hand]
h.cast(t,h.give(t,"Ral's Reinforcements"))
assert sum(o.token and o.card.name=='Elemental' for o in t.rules.controlled(0))==6
h.check(t)
(root/'INTERACTION_REPORT.md').write_text('\n'.join(['# Merchant Scroll, Solve the Equation, and Young Pyromancer','','Forced fixture with actual land payments. Merchant Scroll found Consider directly to hand; Solve the Equation found Ral’s Reinforcements directly to hand. Casting all four spells triggered Young Pyromancer four times; Reinforcements added two more Elementals, for six total.','', '```text',*t.events,'```','']))
print('source-paid search chains passed')
