import unittest
from copy_table import CopyTable

class CopyTargetTests(unittest.TestCase):
 def setUp(self):
  self.t=CopyTable(seed=3501);self.t.active_seat=0;self.t.phase='main';self.t.rules.mana_pools[0]=(30,30,30);self.p=self.t.details
 def give(self,name):
  c=next(c for c in self.p.hand+self.p.library if c.name==name)
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  return c
 def creature(self,seat):return self.t.add_creature(self.t.players[seat],2,2,'fixture',token=True).id
 def copy_first(self,label):
  used=[];self.give('Reiterate')
  def policy(seat,frames,choices):
   if seat==0 and not used:
    c=next((c for c in choices if c.kind=='spell' and c.action.source=='Reiterate' and not c.action.parameters['buyback'] and any(f.label==label and f.frame_id==c.action.target_object for f in frames)),None)
    if c:used.append(True);return c
   return None
  self.t.priority_policy=policy;return used
 def test_step_through_copy_retains_two_targets(self):
  a,b=self.creature(1),self.creature(2);used=self.copy_first('Step Through')
  action=self.t.step_action(self.p,self.give('Step Through'),(a,b));self.t.cast(action)
  self.assertTrue(used);self.assertNotIn(a,self.t.rules.objects);self.assertNotIn(b,self.t.rules.objects);self.t.assert_consistent()
 def test_step_through_copy_can_choose_new_targets(self):
  a,b,c,d=[self.creature(x) for x in (1,1,2,2)];self.t.copy_target_policy=lambda seat,original:(c,d);used=self.copy_first('Step Through')
  self.t.cast(self.t.step_action(self.p,self.give('Step Through'),(a,b)))
  self.assertTrue(used);self.assertTrue(all(x not in self.t.rules.objects for x in (a,b,c,d)));self.t.assert_consistent()
 def test_copied_step_one_legal_target_still_resolves(self):
  a,b,c=self.creature(1),self.creature(2),self.creature(3);self.t.copy_target_policy=lambda seat,original:(b,c);used=self.copy_first('Step Through')
  self.t.cast(self.t.step_action(self.p,self.give('Step Through'),(a,b)))
  self.assertTrue(used);self.assertTrue(all(x not in self.t.rules.objects for x in (a,b,c)));self.t.assert_consistent()
 def test_copy_abrade_preserves_damage_mode_and_changes_target(self):
  # Abrade is registered historical coverage but not in the premium deck.
  self.t.zones.add_spec(self.t.zones.specs['named:Abrade'],0,'hand',detailed=True)
  a=self.creature(1);b=self.creature(2);self.t.copy_target_policy=lambda seat,original:b;used=self.copy_first('Abrade')
  action=self.t.action_with_options(self.p,self.give('Abrade'),mode='damage',target=a)
  self.t.cast(action);self.assertTrue(used);self.assertNotIn(a,self.t.rules.objects);self.assertNotIn(b,self.t.rules.objects)
  modes=[e for e in self.t.rule_events if e[0]=='abrade_damage'];self.assertEqual(len(modes),2)
 def test_copy_counterspell_can_change_stack_target(self):
  self.give('Brainstorm');self.give('Counterspell');self.give('Reiterate');stages=[]
  def copy_target(seat,original):return next(f.frame_id for f in self.t.spell_stack.frames if f.label=='Brainstorm')
  self.t.copy_target_policy=copy_target
  def policy(seat,frames,choices):
   if seat!=0:return None
   if not stages:
    c=next((c for c in choices if c.kind=='spell' and c.action.source=='Brainstorm'),None)
   elif len(stages)==1:
    target=next(f.frame_id for f in frames if f.label=='Consider')
    c=next((c for c in choices if c.kind=='spell' and c.action.source=='Counterspell' and c.action.target_object==target),None)
   elif len(stages)==2:
    target=next(f.frame_id for f in frames if f.label=='Counterspell')
    c=next((c for c in choices if c.kind=='spell' and c.action.source=='Reiterate' and not c.action.parameters['buyback'] and c.action.target_object==target),None)
   else:return None
   if c:stages.append(True);return c
   return None
  self.t.priority_policy=policy;c=self.give('Consider');self.t.cast(self.t.action_for_card(self.p,c))
  self.assertEqual(len(stages),3);self.assertEqual(len(self.t.consider_events),0)
  self.assertIn('Consider',self.t.zones.names(0,'graveyard'));self.assertIn('Brainstorm',self.t.zones.names(0,'graveyard'));self.t.assert_consistent()
 def test_copy_reiterate_can_copy_its_target_again(self):
  self.give('Reiterate');stages=[]
  # Synthetic second Reiterate card for a declared interaction fixture.
  spec=self.t.zones.specs['named:Reiterate'];oid=self.t.zones.add_spec(spec,0,'hand',detailed=True)
  def policy(seat,frames,choices):
   if seat==0 and len(stages)<2:
    target='Consider' if not stages else 'Reiterate'
    c=next((c for c in choices if c.kind=='spell' and c.action.source=='Reiterate' and not c.action.parameters['buyback'] and any(f.label==target and f.frame_id==c.action.target_object for f in frames)),None)
    if c:stages.append(target);return c
   return None
  self.t.priority_policy=policy;c=self.give('Consider');self.t.cast(self.t.action_for_card(self.p,c))
  self.assertEqual(stages,['Consider','Reiterate']);self.assertEqual(len(self.t.consider_events),3)
if __name__=='__main__':unittest.main()
