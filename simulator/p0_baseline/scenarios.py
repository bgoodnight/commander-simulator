"""Explicit decisions and semantic checkpoints for integration replays."""
from baseline import CopyTable,digest,reference_payload,canonical


def scenario(name):
 t=CopyTable(seed=6060,trace=False);p=t.details;t.active_seat=p.seat;t.phase='main';t.priority_policy=lambda *a:None
 t.rules.mana_pools[p.seat]=(30,30,30);decisions=[]
 def give(card_name):
  c=next(c for c in p.hand+p.library if c.name==card_name)
  if c not in p.hand:
   oid=t.zones.move(c.object_id,'hand');c=next(c for c in p.hand if c.object_id==oid)
  return c
 def cast(card_name):
  c=give(card_name);assert t.cast(t.action_for_card(p,c))
 if name=='tutor_to_rift':
  c=give('Cyclonic Rift');t.zones.move(c.object_id,'library')
  def tutor(request):
   oid=next(c.object_id for c in request.cards if c.name=='Cyclonic Rift')
   decisions.append([request.kind,oid]);return oid
  t.tutor_policy=tutor;cast('Merchant Scroll')
  assert 'Cyclonic Rift' in [c.name for c in p.hand]
 elif name=='copy_and_buyback':
  give('Reiterate');used=[]
  def priority(seat,frames,choices):
   if seat==p.seat and not used:
    c=next((c for c in choices if c.kind=='spell' and c.action.source=='Reiterate' and c.action.parameters.get('buyback') and any(f.label=='Consider' and f.frame_id==c.action.target_object for f in frames)),None)
    if c:used.append(True);decisions.append(['reiterate_buyback',c.action.target_object]);return c
   return None
  t.priority_policy=priority;cast('Consider')
  assert used and len(t.consider_events)==2 and 'Reiterate' in [c.name for c in p.hand]
 elif name=='adventure_harmonic':
  cast('Harmonic Prodigy');land=give('Lindblum, Industrial Regency');decisions.append(['cast_adventure',land.object_id]);t.spell_stack.holder=p.seat;t.cast_adventure(p.seat,land.object_id)
  cast('Consider');oid=next(iter(t.adventure_exiled));decisions.append(['play_adventure_land',oid]);t.play_adventure_land(p.seat,oid)
  assert [x.life for x in t.players]==[40,38,38,38]
 else:raise ValueError('Unknown scenario '+name)
 t.assert_consistent()
 payload=reference_payload(t);payload['scenario_extension']=canonical(dict(decisions=decisions,adventure_exiled=sorted(t.adventure_exiled),tutor_events=t.tutor_events,rule_events=t.rule_events,consider_events=t.consider_events))
 return {'decisions':decisions,'sha256':digest(payload),'life':[p.life for p in t.players]}
