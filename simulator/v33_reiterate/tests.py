import unittest
from reiterate_table import ReiterateTable,NAME,RIFT

class ReiterateTests(unittest.TestCase):
 def setUp(self):
  self.t=ReiterateTable(seed=3301);self.t.active_seat=0;self.t.phase='main';self.t.rules.mana_pools[0]=(30,30,30);self.p=self.t.details
 def give(self,name):
  c=next(c for c in self.p.hand+self.p.library if c.name==name)
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  return c
 def cast(self,name):
  c=self.give(name);self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
 def response(self,orig='Consider',buyback=False,post=None):
  used=[]
  def policy(seat,frames,choices):
   if post:
    c=post(seat,frames,choices,used)
    if c:return c
   if seat==0 and not used:
    c=next((c for c in choices if c.kind=='spell' and c.action.source==NAME and c.action.parameters['buyback']==buyback and any(f.label==orig and f.frame_id==c.action.target_object for f in frames)),None)
    if c:used.append(True);return c
   return None
  self.give(NAME);self.t.priority_policy=policy;return used
 def test_default_pilot_can_select_own_spell_copy(self):
  used=[]
  def policy(seat,frames,choices):
   candidates=tuple(c for c in choices if c.kind=='spell' and c.action.source==NAME)
   if seat==0 and candidates and not used:
    chosen=self.t.choose_priority(seat,candidates);used.append(chosen is not None);return chosen
   return None
  self.give(NAME);self.t.priority_policy=policy;self.cast('Consider');self.assertEqual(used,[True])
 def test_copy_resolves_before_original(self):
  used=self.response();self.cast('Consider');self.assertTrue(used)
  self.assertEqual(len(self.t.consider_events),2);self.t.assert_consistent()
 def test_buyback_returns_reiterate(self):
  self.response(buyback=True);self.cast('Consider');self.assertIn(NAME,[c.name for c in self.p.hand]);self.t.assert_consistent()
 def test_no_buyback_goes_to_graveyard(self):
  self.response();self.cast('Consider');self.assertIn(NAME,self.t.zones.names(0,'graveyard'))
 def test_copy_is_not_cast_for_young_pyromancer(self):
  self.t.priority_policy=lambda *a:None;self.cast('Young Pyromancer');self.response();self.cast('Consider')
  self.assertEqual(sum(o.token and o.card.name=='Elemental' for o in self.t.rules.controlled(0)),2)
 def test_magecraft_triggers_for_copy(self):
  self.t.priority_policy=lambda *a:None;self.cast('Archmage Emeritus');self.response();self.cast('Consider')
  # Archmage triggers for Consider, Reiterate, and the copy.
  self.assertEqual(sum(1 for h in self.t.spell_stack.history if h[0]=='push' and 'draw' in h[-1] and h[2]=='triggered'),3)
 def test_copy_target_removed_fizzles_and_no_buyback(self):
  used=[]
  def policy(seat,frames,choices):
   if seat==0 and not used:
    c=next((c for c in choices if c.kind=='spell' and c.action.source==NAME and c.action.parameters['buyback']),None)
    if c:used.append(True);return c
   if used and len(used)==1:
    source=next((f for f in frames if f.label=='Consider'),None)
    if source:self.t.spell_stack.counter(source.frame_id,{'spell'});used.append(True)
   return None
  self.give(NAME);self.t.priority_policy=policy;self.cast('Consider')
  self.assertEqual(len(used),2);self.assertIn(NAME,self.t.zones.names(0,'graveyard'));self.assertEqual(len(self.t.consider_events),0)
 def test_overloaded_rift_copy_retains_mode(self):
  a=self.t.add_creature(self.t.players[1],2,2,'a',token=True).id
  self.response(orig=RIFT);card=self.give(RIFT);self.t.cast(self.t.rift_action(self.p,card,overload=True))
  self.assertNotIn(a,self.t.rules.objects);self.assertEqual(sum(x[0]=='cyclonic_rift' and x[2] for x in self.t.rule_events),2)
 def test_copy_can_choose_new_rift_target(self):
  a=self.t.add_creature(self.t.players[1],2,2,'a',token=True).id
  b=self.t.add_creature(self.t.players[2],2,2,'b',token=True).id
  self.t.copy_target_policy=lambda seat,original:b
  self.response(orig=RIFT);card=self.give(RIFT);self.t.cast(self.t.rift_action(self.p,card,target=a))
  events=[e for e in self.t.rule_events if e[0]=='cyclonic_rift']
  self.assertEqual([e[3] for e in events],[(b,),(a,)])
 def test_countering_copy_leaves_original(self):
  self.give('Counterspell');countered=[]
  def post(seat,frames,choices,used):
   if seat==0 and used and not countered:
    copy=next((f for f in frames if f.kind=='spell' and f.label=='Consider' and f.source_id is None),None)
    if copy:
     choice=next((c for c in choices if c.kind=='spell' and c.action.source=='Counterspell' and c.action.target_object==copy.frame_id),None)
     if choice:countered.append(True);return choice
   return None
  self.response(post=post);self.cast('Consider')
  self.assertTrue(countered);self.assertEqual(len(self.t.consider_events),1);self.t.assert_consistent()
 def test_copy_counterspell_counters_same_target(self):
  self.give('Counterspell');self.give(NAME);stages=[]
  def policy(seat,frames,choices):
   if seat!=0:return None
   if not stages:
    c=next((c for c in choices if c.kind=='spell' and c.action.source=='Counterspell' and any(f.label=='Consider' and f.frame_id==c.action.target_object for f in frames)),None)
    if c:stages.append('counter');return c
   elif len(stages)==1:
    c=next((c for c in choices if c.kind=='spell' and c.action.source==NAME and not c.action.parameters['buyback'] and any(f.label=='Counterspell' and f.frame_id==c.action.target_object for f in frames)),None)
    if c:stages.append('copy');return c
   return None
  self.t.priority_policy=policy;self.cast('Consider')
  self.assertEqual(stages,['counter','copy']);self.assertEqual(len(self.t.consider_events),0)
  self.assertGreaterEqual(self.t.spell_stack.fizzled,1);self.t.assert_consistent()
 def test_buyback_generic_reduced_by_magnus(self):
  self.t.priority_policy=lambda *a:None;commander=self.t.zones.views(0,'command')[0];self.t.cast(self.t.action_for_card(self.p,commander))
  for _ in range(3):self.t.add_creature(self.p,1,1,'fixture',token=True)
  action=self.t.reiterate_action(self.p,self.give(NAME),buyback=True);self.assertEqual((action.cost,action.parameters['R']),(3,2))
if __name__=='__main__':unittest.main()
