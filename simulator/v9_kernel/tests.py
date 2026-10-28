"""Bounded v9 infrastructure tests; no unimplemented rules claimed as passing."""
from __future__ import annotations
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT.parent/'v8_central'))
from adapter import V9Table,DeckProvider
from kernel import CentralKernel
from zones import KernelZones
from mana import TypedMana,ManaMode
from rules import CardDefinition,Cost,SafetyStop
from simulation import CardSpec


def card(name,kind='sorcery',coverage='verified_subset',abilities=()):
    return CardDefinition(name.lower().replace(' ','-'),name,frozenset({kind}),
                          abilities=abilities,coverage=coverage)

class SeatTests(unittest.TestCase):
    def test_four_providers_required(self):
        with self.assertRaises(ValueError):V9Table(['magnus','aggro'])
    def test_invalid_provider_rejected(self):
        with self.assertRaises(ValueError):V9Table(['magnus','unknown','control','combo'])
    def test_multiple_real_decks_fail_closed(self):
        with self.assertRaises(NotImplementedError):V9Table(['magnus','magnus','aggro','control'])
    def test_zero_real_decks_fail_closed(self):
        with self.assertRaises(NotImplementedError):V9Table(['aggro','control','combo','tokens'])
    def test_pilot_provider_policy_rejected(self):
        with self.assertRaises(NotImplementedError):DeckProvider('magnus','experimental')
    def test_real_seat_moves_everywhere(self):
        for detailed in range(4):
            names=['aggro','control','combo'];names.insert(detailed,'magnus')
            t=V9Table(names,seed=104,trace=False).run(8)
            self.assertIs(t.details,t.players[detailed]);self.assertEqual(t.details.seat,detailed)
            self.assertTrue(t.world.consistent())
            self.assertTrue(t.diagnostics()['v9']['kernel_view_consistent'])
            self.assertEqual([p.seat for p in t.players],[0,1,2,3])
    def test_named_magnus_static_rule_when_seat_two(self):
        t=V9Table(['control','aggro','magnus','combo'],seed=14)
        p=t.details
        t.add_creature(p,4,5,'Magnus the Red')
        t.add_creature(p,1,1,'Elemental',token=True)
        from integrated import named_spec
        a=t.action_for(p,named_spec('Preordain'))
        self.assertEqual(a.cost,1)
        self.assertEqual(t.rules.tokens(2,creatures_only=True),1)
    def test_named_spell_countered_in_other_seat(self):
        from integrated import named_spec
        from simulation import Action,CardSpec
        t=V9Table(['aggro','control','magnus','combo'],seed=444)
        p=t.details;op=t.players[0]
        p.hand=[named_spec('Preordain')];p.ready_sources=['Island']*4;p.mana=4
        op.hand=[CardSpec('Counterspell','counter',2,'instant','counter',{'can_counter_types':('instant','sorcery')})];op.mana=6
        for other in (t.players[1],t.players[3]):other.hand=[]
        t.response_policy=lambda top,opts:next((o for o in opts if o[1] is op),None)
        a=t.action_for(p,p.hand[0]);t.cast(a)
        self.assertEqual(t.spell_stack.spells_countered,1)
        self.assertTrue(t.world.consistent())
    def test_report_not_claim_two_detailed_or_full_zones(self):
        d=V9Table().diagnostics()['v9']
        self.assertFalse(d['multi_detailed_games_supported'])
        self.assertFalse(d['authoritative_card_zones_in_live_game'])

class ZoneTests(unittest.TestCase):
    def setUp(self):self.z=KernelZones(seed=123)
    def test_two_detailed_lists_separate_and_same_kernel(self):
        for seat in (1,3):
            self.z.add(card('Island','land'),seat)
            self.z.add(card('Counterspell','instant'),seat)
            self.assertEqual(len(self.z.ids(seat,'library')),2)
        self.assertEqual(len(self.z.kernel.objects),4)
        a,_=self.z.draw(1,1);b,_=self.z.draw(3,1)
        self.assertNotEqual(a[0],b[0]);self.assertTrue(self.z.assert_consistent())
    def test_draw_has_fresh_object_identity(self):
        before=self.z.add(card('Preordain'),2)
        (after,),okay=self.z.draw(2)
        self.assertTrue(okay);self.assertNotEqual(before,after)
        self.assertNotIn(before,self.z.kernel.objects)
        self.assertEqual(self.z.ids(2,'hand'),(after,))
    def test_draw_empty_returns_loss_signal_not_card(self):
        draw,ok=self.z.draw(1)
        self.assertFalse(ok);self.assertEqual(draw,())
        self.assertEqual(self.z.operations[-1],('draw_from_empty',1))
    def test_discard_and_mill_correct_zones(self):
        x=self.z.add(card('A'),0);y=self.z.add(card('B'),0)
        self.z.draw(0);hand_id=self.z.ids(0,'hand')[0]
        self.z.discard(0,hand_id);self.z.mill(0)
        self.assertEqual(set(self.z.names(0,'graveyard')),{'A','B'})
        self.assertTrue(self.z.assert_consistent())
    def test_search_shuffle_reproducible(self):
        for instance in range(2):
            z=KernelZones(seed=333)
            for i in range(30):z.add(card('Card '+str(i)),1)
            got=z.search_to_hand(1,lambda d:d.name=='Card 4')
            self.assertEqual(z.kernel.get(got).card.name,'Card 4')
            if instance==0:self._first=z.names(1,'library')
            else:self.assertEqual(z.names(1,'library'),self._first)
    def test_cast_trigger_distinct_from_resolution(self):
        original=self.z.add(card('Probe','instant'),1,'hand')
        ticket=self.z.cast(1,original)
        self.assertEqual(self.z.kernel.get(ticket.object_id).zone,'stack')
        self.assertEqual([e.name for e in self.z.kernel.events].count('spell_cast'),1)
        self.assertEqual([e.name for e in self.z.kernel.events].count('spell_resolved'),0)
        with self.assertRaises(NotImplementedError):self.z.resolve(ticket)
        new=self.z.resolve(ticket,effect=lambda k,t:None)
        self.assertEqual(self.z.kernel.get(new).zone,'graveyard')
        self.assertEqual([e.name for e in self.z.kernel.events].count('spell_resolved'),1)
        self.assertTrue(self.z.assert_consistent())
    def test_counter_moves_without_normal_effect(self):
        old=self.z.add(card('Test instant','instant'),2,'hand')
        ticket=self.z.cast(2,old)
        new=self.z.counter(ticket)
        self.assertNotIn(ticket.object_id,self.z.kernel.objects)
        self.assertEqual(self.z.kernel.get(new).zone,'graveyard')
        self.assertEqual([e.name for e in self.z.kernel.events].count('spell_resolved'),0)
        self.assertEqual([e.name for e in self.z.kernel.events].count('spell_countered'),1)
        self.assertTrue(self.z.assert_consistent())
    def test_permanent_resolves_to_same_kernel(self):
        old=self.z.add(card('Creature','creature'),0,'hand')
        ticket=self.z.cast(0,old)
        new=self.z.resolve(ticket)
        self.assertEqual(self.z.kernel.get(new).zone,'battlefield')
        self.assertNotEqual(new,old)
        self.assertTrue(self.z.assert_consistent())
    def test_land_cannot_be_cast(self):
        x=self.z.add(card('Island','land'),0,'hand')
        with self.assertRaises(ValueError):self.z.cast(0,x)
        y=self.z.play_land(0,x)
        self.assertEqual(self.z.kernel.get(y).zone,'battlefield')
    def test_unimplemented_spell_remains_in_hand(self):
        x=self.z.add(card('Mystic Speculation','sorcery','unimplemented'),1,'hand')
        with self.assertRaises(NotImplementedError):self.z.cast(1,x)
        self.assertIn(x,self.z.ids(1,'hand'))
    def test_countered_commander_returns_to_command(self):
        d=CardDefinition('c','Commander',frozenset({'creature'}),supertypes=frozenset({'commander'}))
        x=self.z.add(d,3,'command')
        self.z.move(x,'hand')
        ticket=self.z.cast(3,self.z.ids(3,'hand')[0]);new=self.z.counter(ticket)
        self.assertEqual(self.z.kernel.get(new).zone,'command')
        self.assertTrue(self.z.assert_consistent())
    def test_player_leaves_without_false_death(self):
        x=self.z.add(card('Thing','creature'),0,'battlefield')
        self.z.add(card('Thing2','sorcery'),0,'hand')
        self.z.add(card('Other','sorcery'),1,'hand')
        before=sum(e.name=='dies' for e in self.z.kernel.events)
        self.z.leave_game(0)
        self.assertEqual(before,sum(e.name=='dies' for e in self.z.kernel.events))
        self.assertEqual(len(self.z.kernel.objects),1)
        self.assertTrue(self.z.assert_consistent())
    def test_cannot_duplicate_zone_card(self):
        x=self.z.add(card('Thing'),1)
        self.z.order[1,'hand'].append(x)
        with self.assertRaises(AssertionError):self.z.assert_consistent()
    def test_no_tokens_in_library(self):
        with self.assertRaises(ValueError):self.z.add(card('Creature','creature'),1,'library',token=True)

class ManaTests(unittest.TestCase):
    def setUp(self):self.m=TypedMana(max_states=10000)
    def test_colored_not_reduced_by_generic(self):
        self.m.add_source(2,'Mountain',[ManaMode(red=1)])
        self.assertIsNone(self.m.plan(2,Cost(generic=0,blue=1)))
    def test_identical_policy_all_seats(self):
        for seat in range(4):
            mana=TypedMana(max_states=10000)
            mana.add_source(seat,'Island',[ManaMode(blue=1)])
            mana.add_source(seat,'Mountain',[ManaMode(red=1)])
            mana.add_source(seat,'Sol Ring',[ManaMode(colorless=2)],kind='artifact')
            plan=mana.pay(seat,Cost(generic=2,blue=1,red=1))
            self.assertEqual(len(plan.activations),3)
            self.assertIsNone(mana.plan(seat,Cost(blue=1)))
            mana.untap(seat)
            self.assertIsNotNone(mana.plan(seat,Cost(blue=1)))
    def test_mode_selection_for_dual_land(self):
        oid=self.m.add_source(3,'Steam Vents',[ManaMode(blue=1),ManaMode(red=1)])
        p=self.m.pay(3,Cost(red=1))
        self.assertEqual(p.activations[0][1],ManaMode(red=1))
        self.assertTrue(self.m.kernel.get(oid).tapped)
    def test_cannot_pay_with_opponent_sources(self):
        self.m.add_source(1,'Island',[ManaMode(blue=1)])
        self.assertIsNone(self.m.plan(0,Cost(blue=1)))
    def test_mana_solver_limit_fails_closed(self):
        for i in range(8):self.m.add_source(1,'Mountain'+str(i),[ManaMode(red=1)])
        self.m.max_states=3
        with self.assertRaises(SafetyStop):self.m.plan(1,Cost(blue=1))
    def test_no_zero_mana_source(self):
        with self.assertRaises(ValueError):self.m.add_source(0,'empty',[ManaMode()])

if __name__=='__main__':unittest.main(verbosity=2)
