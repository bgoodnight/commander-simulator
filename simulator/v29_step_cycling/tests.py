import unittest
from dataclasses import replace
from step_cycling import StepCyclingTable,STEP
from rules import Ability,Cost

class StepCyclingTests(unittest.TestCase):
 def setUp(self):
  self.t=StepCyclingTable(seed=2901);self.t.active_seat=0;self.t.phase='main';self.t.priority_policy=lambda *a:None
  self.t.rules.mana_pools[0]=(30,30,30);self.p=self.t.details
 def give(self,name):
  c=next(c for c in self.p.hand+self.p.library if c.name==name)
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  return c
 def creature(self,seat=1):return self.t.add_creature(self.t.players[seat],2,2,'test creature',token=True).id
 def action(self,*targets):return self.t.step_action(self.p,self.give(STEP),targets)
 def test_requires_two_distinct_creatures(self):
  a=self.creature()
  for targets in [(a,), (a,a), (a,999999)]:
   with self.assertRaises(ValueError):self.t.cast(self.action(*targets))
 def test_returns_both_targets(self):
  a=self.creature();b=self.creature(2)
  self.assertTrue(self.t.cast(self.action(a,b)));self.assertNotIn(a,self.t.rules.objects);self.assertNotIn(b,self.t.rules.objects);self.t.assert_consistent()
 def test_one_illegal_target_other_still_returns(self):
  a=self.creature();b=self.creature(2);used=[]
  def policy(seat,frames,choices):
   if frames and frames[-1].label==STEP and not used:
    used.append(True);self.t.world.move(a,'graveyard','destroy')
   return None
  self.t.priority_policy=policy;self.assertTrue(self.t.cast(self.action(a,b)))
  self.assertNotIn(b,self.t.rules.objects);self.assertEqual(self.t.counts['spells_fizzled'],0)
 def test_all_illegal_targets_fizzle(self):
  a=self.creature();b=self.creature();used=[]
  def policy(seat,frames,choices):
   if frames and frames[-1].label==STEP and not used:
    used.append(True);self.t.world.move(a,'graveyard','destroy');self.t.world.move(b,'graveyard','destroy')
   return None
  self.t.priority_policy=policy;self.t.cast(self.action(a,b));self.assertEqual(self.t.counts['spells_fizzled'],1)
 def test_cycling_does_not_trigger_cast_but_triggers_cycling_watcher(self):
  py=self.give('Young Pyromancer');self.t.cast(self.t.action_for_card(self.p,py))
  watcher=self.creature(0);obj=self.t.rules.get(watcher)
  obj.card=replace(obj.card,abilities=(Ability('triggered',event='cycled',op='draw',condition='controller_cycles'),));self.t.rules._dirty()
  step=self.give(STEP);before=len(self.p.hand);self.t.spell_stack.holder=0;self.t.tutor_policy=lambda r:None
  choice=next(c for c in self.t.priority_choices(0) if c.kind=='wizardcycle' and c.source_id==step.object_id)
  self.t.commit_choice(0,choice);self.t.spell_stack.resolve()
  self.assertEqual(len(self.p.hand),before);self.assertEqual(sum(o.token and o.card.name=='Elemental' for o in self.t.rules.controlled(0)),0)
  self.assertEqual(self.t.spell_stack.triggers_resolved,1);self.t.assert_consistent()
 def test_step_cast_triggers_pyromancer(self):
  py=self.give('Young Pyromancer');self.t.cast(self.t.action_for_card(self.p,py))
  a=self.creature();b=self.creature();self.t.cast(self.action(a,b))
  self.assertEqual(sum(o.token and o.card.name=='Elemental' for o in self.t.rules.controlled(0)),1)
 def test_only_owner_cycling_triggers_watcher(self):
  watcher=self.creature(1);obj=self.t.rules.get(watcher)
  obj.card=replace(obj.card,abilities=(Ability('triggered',event='cycled',op='draw',condition='controller_cycles'),));self.t.rules._dirty()
  step=self.give(STEP);self.t.spell_stack.holder=0;self.t.tutor_policy=lambda r:None
  choice=next(c for c in self.t.priority_choices(0) if c.kind=='wizardcycle' and c.source_id==step.object_id)
  self.t.commit_choice(0,choice);self.t.spell_stack.resolve();self.assertEqual(self.t.spell_stack.triggers_queued,0)
 def test_cost_reduction(self):
  med=self.give('Sapphire Medallion');self.t.cast(self.t.action_for_card(self.p,med))
  a=self.action(self.creature(),self.creature());self.assertEqual((a.cost,a.parameters['U']),(4,2))
 def test_priority_exposes_each_pair(self):
  self.give(STEP);ids=[self.creature() for _ in range(3)]
  choices=[c for c in self.t.priority_choices(0) if c.kind=='spell' and c.action.source==STEP]
  self.assertEqual({frozenset(c.action.step_targets) for c in choices},{frozenset((ids[0],ids[1])),frozenset((ids[0],ids[2])),frozenset((ids[1],ids[2]))})
if __name__=='__main__':unittest.main()
