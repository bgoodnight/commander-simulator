import unittest
from dataclasses import replace
from utility_table import UtilityTable
from utility_cards import ISLET,RIPTIDE
from rules import Cost

class UtilityTests(unittest.TestCase):
    def setUp(self):
        self.t=UtilityTable(seed=211);self.t.priority_policy=lambda *args:None
        self.p=self.t.details;self.t.active_seat=0;self.t.phase='main'
        for p in self.t.players:
            for oid in self.t.zones.ids(p.seat,'hand'):self.t.zones.move(oid,'library')

    def give(self,name):
        c=next(c for c in self.p.hand+self.p.library if c.name==name)
        if c not in self.p.hand:
            oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
        return c
    def land(self,name='Island'):
        return self.t.enter_land(self.p,self.give(name).object_id,cause='fixture')
    def grave(self,name='Ponder'):
        return self.t.zones.move(self.give(name).object_id,'graveyard')
    def sanctuary(self,n=3,force=False):
        for _ in range(n):self.land()
        return self.t.enter_land(self.p,self.give('Mystic Sanctuary').object_id,force_tapped=force,cause='fixture')
    def cast(self,name):
        for seat in range(4):self.t.rules.mana_pools[seat]=(20,20,20)
        self.t.active_seat=0;self.t.phase='main';c=self.give(name)
        self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
        return next(o for o in self.t.rules.on_battlefield() if o.card.name==name)
    def wizard(self):return self.cast('Goblin Electromancer')
    def riptide(self):
        oid=self.land('Riptide Laboratory');self.t.rules.mana_pools[0]=(10,10,10);return oid
    def activate(self,oid,spec,target=None):return self.t.activate_ability(0,oid,spec,target)

    def test_untapped_entry_queues_trigger(self):
        self.grave();self.sanctuary();self.assertEqual(len(self.t.spell_stack.pending),1)
    def test_tapped_entry_no_trigger(self):
        self.grave();self.sanctuary(2);self.assertFalse(self.t.spell_stack.pending)
    def test_forced_tapped_entry_no_trigger(self):
        self.grave();self.sanctuary(3,True);self.assertFalse(self.t.spell_stack.pending)
    def test_untap_after_entry_does_not_trigger(self):
        self.grave();oid=self.sanctuary(2);self.t.rules.get(oid).tapped=False;self.t.spell_stack.resolve();self.assertFalse(self.t.utility_events)
    def test_no_target_does_not_place_ability(self):
        self.sanctuary();self.t.spell_stack.resolve();self.assertTrue(any(e[0]=='sanctuary_no_target' for e in self.t.utility_events))
    def test_instant_or_sorcery_returns_to_top(self):
        target=self.grave('Ponder');self.sanctuary();self.t.spell_stack.resolve()
        self.assertEqual(self.p.library[-1].name,'Ponder');self.assertNotIn(target,self.t.rules.objects)
    def test_choice_is_optional_at_resolution(self):
        target=self.grave();self.sanctuary();self.t.sanctuary_return_policy=lambda *args:False
        self.t.spell_stack.resolve();self.assertIn(target,self.t.zones.ids(0,'graveyard'))
    def test_target_chosen_when_trigger_placed(self):
        first=self.grave('Ponder');self.sanctuary();second=self.grave('Preordain')
        self.t.sanctuary_target_policy=lambda r:second
        self.t.spell_stack.resolve();self.assertEqual(self.p.library[-1].name,'Preordain')
        self.assertIn(first,self.t.zones.ids(0,'graveyard'))
    def test_target_policy_cannot_choose_creature(self):
        self.grave();bad=self.grave('Young Pyromancer');self.sanctuary();self.t.sanctuary_target_policy=lambda r:bad
        with self.assertRaises(ValueError):self.t.spell_stack.checkpoint()
    def test_target_change_zone_fizzles(self):
        target=self.grave();self.sanctuary();self.t.spell_stack.checkpoint()
        self.t.zones.move(target,'exile');self.t.spell_stack.resolve()
        self.assertEqual(self.t.spell_stack.fizzled,1)
        self.assertFalse(any(e[0]=='sanctuary_resolved' for e in self.t.utility_events))
    def test_returned_card_new_identity_does_not_follow_target(self):
        target=self.grave();self.sanctuary();self.t.spell_stack.checkpoint()
        new=self.t.zones.move(target,'hand');self.t.zones.move(new,'graveyard')
        self.t.spell_stack.resolve();self.assertEqual(self.t.spell_stack.fizzled,1)
    def test_source_bounce_does_not_cancel_trigger(self):
        self.grave();source=self.sanctuary();self.t.spell_stack.checkpoint()
        self.t.world.move(source,'hand','bounce');self.t.spell_stack.resolve()
        self.assertEqual(self.p.library[-1].name,'Ponder')
    def test_sanctuary_target_own_graveyard_only(self):
        other=self.t.players[1];card=other.library[0];target=self.t.zones.move(card.object_id,'graveyard')
        self.assertFalse(self.t.sanctuary_target_legal(0,target))
    def test_sanctuary_selects_between_spells(self):
        a=self.grave('Ponder');b=self.grave('Brainstorm');self.sanctuary()
        self.t.sanctuary_target_policy=lambda r:a;self.t.spell_stack.resolve()
        self.assertEqual(self.p.library[-1].name,'Ponder');self.assertIn(b,self.t.zones.ids(0,'graveyard'))
    def test_riptide_requires_wizard_creature_you_control(self):
        oid=self.riptide();creature=self.t.add_creature(self.p,2,2,'fixture',token=True)
        self.assertFalse(self.t.activation_available(0,oid,RIPTIDE,creature.id))
    def test_riptide_uses_derived_wizard_subtype(self):
        self.cast('Arcane Adaptation');target=self.t.add_creature(self.p,2,2,'fixture',token=True)
        oid=self.riptide();self.assertTrue(self.t.activation_available(0,oid,RIPTIDE,target.id))
    def test_riptide_returns_wizard(self):
        w=self.wizard();oid=self.riptide();self.activate(oid,RIPTIDE,w.object_id)
        self.assertIn('Goblin Electromancer',[c.name for c in self.p.hand]);self.assertTrue(self.t.rules.get(oid).tapped)
    def test_riptide_token_ceases(self):
        self.cast('Arcane Adaptation');w=self.t.add_creature(self.p,2,2,'fixture',token=True)
        oid=self.riptide();self.activate(oid,RIPTIDE,w.id);self.assertNotIn(w.id,self.t.rules.objects)
    def test_riptide_no_other_controller(self):
        other=self.t.add_creature(self.t.players[1],1,1,'fixture',token=True)
        self.t.rules.get(other.id).card=replace(self.t.rules.get(other.id).card,subtypes=frozenset({'Wizard'}))
        oid=self.riptide();self.assertFalse(self.t.activation_available(0,oid,RIPTIDE,other.id))
    def test_riptide_reserves_own_tap_for_cost(self):
        w=self.wizard();oid=self.land('Riptide Laboratory');self.t.rules.mana_pools[0]=(0,0,0)
        self.assertFalse(self.t.activation_available(0,oid,RIPTIDE,w.object_id))
    def test_riptide_colored_mana_required(self):
        w=self.wizard();oid=self.land('Riptide Laboratory');self.t.rules.mana_pools[0]=(10,0,0)
        self.assertFalse(self.t.activation_available(0,oid,RIPTIDE,w.object_id))
    def test_riptide_exact_one_generic_and_one_blue_cost(self):
        w=self.wizard();oid=self.land('Riptide Laboratory');self.t.rules.mana_pools[0]=(1,1,0)
        self.assertTrue(self.t.activation_available(0,oid,RIPTIDE,w.object_id))
        self.t.rules.mana_pools[0]=(0,1,0)
        self.assertFalse(self.t.activation_available(0,oid,RIPTIDE,w.object_id))
    def test_riptide_can_target_noncreature_wizard_permanent(self):
        perm=self.t.add_permanent(self.p,'ramp',1,'Synthetic typal artifact')
        obj=self.t.rules.get(perm.id);obj.card=replace(obj.card,subtypes=frozenset({'Wizard'}))
        oid=self.riptide();self.assertTrue(self.t.activation_available(0,oid,RIPTIDE,obj.object_id))
        self.assertTrue(any(c.kind=='activate' and c.ability==RIPTIDE and c.target_frame==obj.object_id
                            for c in self.t.priority_choices(0)))
        self.activate(oid,RIPTIDE,obj.object_id);self.assertNotIn(obj.object_id,self.t.rules.objects)

    def test_riptide_tapped_source_rejected(self):
        w=self.wizard();oid=self.riptide();self.t.rules.get(oid).tapped=True
        self.assertFalse(self.t.activation_available(0,oid,RIPTIDE,w.object_id))
    def test_riptide_target_leaves_before_resolution(self):
        w=self.wizard();oid=self.riptide();used=[]
        def policy(seat,frames,choices):
            if frames and not used:
                used.append(True);self.t.world.move(w.object_id,'exile','exile')
            return None
        self.t.priority_policy=policy;self.activate(oid,RIPTIDE,w.object_id)
        self.assertTrue(used);self.assertEqual(self.t.spell_stack.fizzled,1);self.assertTrue(self.t.rules.get(oid).tapped)
    def test_riptide_target_loses_wizard_before_resolution(self):
        w=self.wizard();oid=self.riptide();used=[]
        def policy(seat,frames,choices):
            if frames and not used:
                used.append(True);w.card=replace(w.card,subtypes=frozenset({'Goblin'}));self.t.rules._dirty()
            return None
        self.t.priority_policy=policy;self.activate(oid,RIPTIDE,w.object_id);self.assertEqual(self.t.spell_stack.fizzled,1)
    def test_riptide_own_hexproof_legal_shroud_not(self):
        w=self.wizard();oid=self.riptide();w.card=replace(w.card,keywords=frozenset({'hexproof'}))
        self.assertTrue(self.t.activation_available(0,oid,RIPTIDE,w.object_id))
        w.card=replace(w.card,keywords=frozenset({'shroud'}));self.assertFalse(self.t.activation_available(0,oid,RIPTIDE,w.object_id))
    def test_riptide_legal_choices_are_exposed(self):
        w=self.wizard();oid=self.riptide();choices=self.t.priority_choices(0)
        self.assertTrue(any(c.kind=='activate' and c.ability==RIPTIDE and c.target_frame==w.object_id for c in choices))
    def test_islet_tap_sacrifice_and_draw(self):
        oid=self.land('Fiery Islet');self.land();self.t.rules.mana_pools[0]=(0,0,0)
        before=len(self.p.hand);self.activate(oid,ISLET)
        self.assertEqual(len(self.p.hand),before+1);self.assertIn('Fiery Islet',self.p.graveyard)
    def test_islet_cannot_pay_cost_using_itself(self):
        oid=self.land('Fiery Islet');self.t.rules.mana_pools[0]=(0,0,0)
        self.assertFalse(self.t.activation_available(0,oid,ISLET))
    def test_islet_floating_mana_can_pay(self):
        oid=self.land('Fiery Islet');self.t.rules.mana_pools[0]=(1,0,0)
        self.assertTrue(self.t.activation_available(0,oid,ISLET))
    def test_islet_tapped_cannot_activate(self):
        oid=self.land('Fiery Islet');self.t.rules.get(oid).tapped=True;self.t.rules.mana_pools[0]=(1,0,0)
        self.assertFalse(self.t.activation_available(0,oid,ISLET))
    def test_islet_cost_paid_before_responses(self):
        oid=self.land('Fiery Islet');self.t.rules.mana_pools[0]=(1,0,0);seen=[]
        def policy(seat,frames,choices):
            if frames:seen.append(oid not in self.t.rules.objects and 'Fiery Islet' in self.p.graveyard)
            return None
        self.t.priority_policy=policy;self.activate(oid,ISLET);self.assertTrue(seen and all(seen))
    def test_islet_ability_not_spell_or_cast_trigger(self):
        self.cast('Young Pyromancer');oid=self.land('Fiery Islet');self.t.rules.mana_pools[0]=(1,0,0)
        before=sum(c.token for c in self.p.creatures);self.activate(oid,ISLET)
        self.assertEqual(sum(c.token for c in self.p.creatures),before)
    def test_islet_existing_mana_mode_still_costs_one_life(self):
        oid=self.land('Fiery Islet');self.assertTrue(all(a.life==1 for a in self.t.resources.abilities(self.t.rules.get(oid))))
    def test_islet_empty_library_loses_after_draw(self):
        oid=self.land('Fiery Islet');self.t.rules.mana_pools[0]=(1,0,0)
        for x in self.t.zones.ids(0,'library'):self.t.zones.move(x,'graveyard')
        self.activate(oid,ISLET);self.assertIsNotNone(self.p.eliminated_round)
    def test_detailed_deck_portable_all_seats(self):
        for seat in range(4):
            kinds=['aggro','control','combo'];kinds.insert(seat,'magnus')
            t=UtilityTable(kinds,seed=212).run(3);self.assertIsNone(t.safety_stop);self.assertTrue(t.assert_consistent())
    def test_reproducibility(self):
        a=UtilityTable(seed=213).run(3);b=UtilityTable(seed=213).run(3)
        self.assertEqual(a.utility_events,b.utility_events);self.assertEqual(a.step_history,b.step_history)

if __name__=='__main__':unittest.main()
