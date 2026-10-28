"""V8 transition and integration tests; `python tests.py` (stdlib only)."""
import unittest
from dataclasses import replace
from pathlib import Path
from table import CentralTable
from kernel import CentralKernel
from stack import SharedStack
from rules import Modifier,Event,SafetyLimits,ExecutionGuard,SafetyStop
from catalog import MAGNUS,PYROMANCER,HARMONIC
import simulation as base
import integrated as detailed

class SharedWorld(unittest.TestCase):
    def setUp(self):self.t=CentralTable(seed=102,trace=False)
    def test_every_seat_uses_same_kernel_identity(self):
        t=self.t
        ids=[]
        for q in t.players:
            c=t.add_creature(q,3,3,'body',token=q.seat%2==0)
            ids.append(c.id)
            self.assertEqual(t.rules.get(c.id).controller,q.seat)
        self.assertEqual(len(set(ids)),4)
        self.assertTrue(t.world.consistent())
    def test_no_rematerialized_kernel_for_repeated_queries(self):
        t=self.t
        t.add_creature(t.details,1,1,'Young Pyromancer')
        k,_,_=t._view()
        self.assertIs(k,t.rules)
        self.assertIs(t._view()[0],k)
        self.assertEqual(len(t.rules.controlled(0,{'creature'})),1)
    def test_destroy_removes_views_but_preserves_zone_object(self):
        t=self.t;p=t.players[2]
        c=t.add_creature(p,2,2,'test',token=False)
        self.assertTrue(t.kill_creature(p,c))
        self.assertNotIn(c,p.creatures);self.assertNotIn(c.id,t.rules.objects)
        self.assertEqual(t.rules.get(t.rules.moves[-1].new_object_id).zone,'graveyard')
        self.assertTrue(t.world.consistent())
    def test_indestructible_resists_all_destroy_paths(self):
        t=self.t;c=t.add_creature(t.players[1],4,4,'test')
        t.rules.add_modifier(c.id,Modifier(keywords=frozenset({'indestructible'})))
        self.assertFalse(t.kill_creature(t.players[1],c))
        t.world.damage_pair(t.add_creature(t.players[0],7,7,'attacker'),c)
        self.assertIn(c,t.players[1].creatures)
        self.assertTrue(t.world.consistent())
    def test_sacrifice_does_not_count_as_destroy_and_ignores_indestructible(self):
        t=self.t;c=t.add_creature(t.players[1],3,3,'test')
        t.rules.add_modifier(c.id,Modifier(keywords=frozenset({'indestructible'})))
        self.assertTrue(t.world.move(c.id,'graveyard','sacrifice'))
        self.assertNotIn(c,t.players[1].creatures)
    def test_hexproof_target_spell_fizzles(self):
        t=self.t;c=t.add_creature(t.players[1],2,2,'protected')
        t.rules.add_modifier(c.id,Modifier(keywords=frozenset({'hexproof'})))
        a=base.Action(0,'opponent removal','instant','remove',2,target=1,target_object=c.id)
        t.apply(a)
        self.assertIn(c,t.players[1].creatures)
        self.assertEqual(t.counts['illegal_target_on_resolution'],1)
    def test_indestructible_pongify_still_gives_ape(self):
        t=self.t;c=t.add_creature(t.players[1],4,4,'indestructible')
        t.rules.add_modifier(c.id,Modifier(keywords=frozenset({'indestructible'})))
        a=base.Action(0,'Pongify','instant','named_pongify',1,target=1,target_object=c.id)
        t.apply(a)
        self.assertIn(c,t.players[1].creatures)
        self.assertTrue(any(x.name=='Ape (Pongify)' for x in t.players[1].creatures))
    def test_multi_permanent_target_destroy_shared(self):
        t=self.t;p=t.players[3]
        per=t.add_permanent(p,'engine',3,'Magic Engine')
        self.assertEqual(t.rules.get(per.id).zone,'battlefield')
        t.remove_permanent(p,per)
        self.assertNotIn(per,p.permanents);self.assertTrue(t.world.consistent())
    def test_linked_creature_permanent_one_id(self):
        t=self.t;p=t.players[1]
        per=t.add_permanent(p,'engine',3,'Engine Body',True)
        c=next(c for c in p.creatures if c.id==per.id)
        self.assertIsNotNone(c)
        self.assertEqual(sum(o.object_id==per.id for o in t.rules.on_battlefield()),1)
        self.assertTrue(t.kill_creature(p,c))
        self.assertNotIn(per,p.permanents)
        self.assertTrue(t.world.consistent())
    def test_commander_zone_transition_respects_replacement(self):
        t=self.t;p=t.details;c=t.add_creature(p,4,5,'Magnus the Red')
        p.commander_in_zone=False
        t.kill_creature(p,c)
        self.assertTrue(p.commander_in_zone)
        move=t.rules.moves[-2]
        self.assertEqual(t.rules.get(t.rules.moves[-1].new_object_id).zone,'command')
    def test_token_ceases_without_graveyard_object(self):
        t=self.t;c=t.add_creature(t.players[2],1,1,'Elemental',token=True)
        self.assertTrue(t.kill_creature(t.players[2],c))
        self.assertNotIn(c.id,t.rules.objects)
        self.assertTrue(t.world.consistent())
    def test_same_death_step_in_combat(self):
        t=self.t;a=t.add_creature(t.players[1],3,3,'a');b=t.add_creature(t.players[2],3,3,'b')
        t.world.damage_pair(a,b)
        self.assertEqual(len(t.players[1].creatures),0)
        self.assertEqual(len(t.players[2].creatures),0)
        self.assertTrue(t.world.consistent())
    def test_kernel_flying_and_reach_apply_to_abstract_seats(self):
        t=self.t;a=t.add_creature(t.players[1],4,4,'flyer',keywords=('flying',))
        n=t.add_creature(t.players[2],3,3,'normal')
        r=t.add_creature(t.players[2],2,2,'reach',keywords=('reach',))
        options=[o.object_id for o in t.rules.legal_blockers(a.id,2)]
        self.assertNotIn(n.id,options);self.assertIn(r.id,options)
    def test_grants_and_counters_share_single_object(self):
        t=self.t;c=t.add_creature(t.players[1],2,1,'test')
        t.rules.add_counter(c.id,'+1/+1',2);t.world.refresh(c.id)
        self.assertEqual((c.power,c.toughness),(4,3))
        t.world.modifier(c,power=5,duration='end_turn')
        self.assertEqual(c.power,9)
        t.world.cleanup();self.assertEqual(c.power,4)
    def test_player_damage_and_simultaneous_death(self):
        t=self.t;t.players[1].life=3;t.players[2].life=4
        t.damage_many({1:3,2:4},t.players[0],'spell_burst')
        self.assertEqual({x['seat'] for x in t.eliminations},{1,2})
        self.assertEqual(t.counts['multi_elimination_events'],1)
    def test_elimination_removes_objects_without_die_triggers(self):
        t=self.t;p=t.players[1];c=t.add_creature(p,2,2,'body')
        before=len([e for e in t.rules.events if e.name=='dies'])
        p.life=0;t.eliminate(p,'combat')
        self.assertNotIn(c.id,t.rules.objects)
        self.assertEqual(before,len([e for e in t.rules.events if e.name=='dies']))
        self.assertTrue(t.world.consistent())
    def test_trigger_and_static_cost_stay_kernel_backed(self):
        t=self.t;p=t.details
        t.add_creature(p,4,5,'Magnus the Red');t.add_creature(p,1,1,'Elemental',token=True)
        c=detailed.named_spec('Preordain');action=t.action_for(p,c)
        self.assertEqual(action.cost,1) # U remains; generic reduced by one
        t.add_creature(p,2,1,'Young Pyromancer');t.add_creature(p,1,3,'Harmonic Prodigy')
        from rules import Event
        q=t.rules.triggers(Event('spell_cast',0,spell_types=frozenset({'sorcery'})))
        self.assertEqual(sum(x.quantity for x in q if x.op=='create_token'),2)
    def test_noncreature_cost_not_reduced_by_magnus(self):
        t=self.t;p=t.details;t.add_creature(p,4,5,'Magnus the Red')
        c=detailed.named_spec('Storm-Kiln Artist')
        self.assertEqual(t.action_for(p,c).cost,c.mana_value)
    def test_treasure_is_kernel_artifact_token_and_spend_ceases(self):
        t=self.t;p=t.details
        token=t.world.create_treasure(p)
        self.assertEqual(t.rules.get(token.object_id).card.name,'Treasure')
        self.assertEqual(t.rules.tokens(p.seat,creatures_only=True),0)
        self.assertEqual(t.rules.tokens(p.seat,creatures_only=False),1)
        before=p.treasures
        t.world.consume_treasures(p,1)
        # This service is called after payment decrements the owner's counter.
        p.treasures-=1
        self.assertEqual(p.treasures,before-1)
        self.assertNotIn(token.object_id,t.rules.objects)
        self.assertTrue(t.world.consistent())
    def test_treasure_paid_via_shared_payment_router(self):
        t=self.t;p=t.details
        p.hand=[detailed.named_spec('Preordain')]
        p.ready_sources=[];p.floating=(0,0,0);p.mana=0
        token=t.world.create_treasure(p)
        a=t.action_for(p,p.hand[0])
        self.assertTrue(t.can_pay(p,a))
        t.pay_spell(p,p.hand[0],a)
        self.assertEqual(p.treasures,0)
        self.assertNotIn(token.object_id,t.rules.objects)
        self.assertTrue(t.world.consistent())
    def test_swan_song_rider_data_gives_flying_bird(self):
        t=self.t
        spell=base.CardSpec('Big Spell','burn',2,'sorcery','burn',{'damage':3})
        defender=t.players[1];defender.hand=[spell];defender.mana=4
        t.details.hand=[detailed.named_spec('Swan Song')]
        t.details.ready_sources=['Island']*5;t.details.mana=5
        t.players[2].hand=[];t.players[3].hand=[]
        t.response_policy=lambda frame,opts:next((o for o in opts if o[1].seat==0),None)
        a=base.Action(1,'Big Spell','sorcery','burn',2,target=3,parameters={'damage':3})
        t.cast(a)
        self.assertEqual(t.players[3].life,40)
        birds=[c for c in defender.creatures if c.name=='Bird (Swan Song)']
        self.assertEqual(len(birds),1)
        self.assertIn('flying',birds[0].keywords)
    def test_other_seats_tokens_have_shared_object_identity(self):
        t=self.t;p=t.players[2]
        token=t.world.create_treasure(p)
        self.assertTrue(token.token)
        self.assertEqual(t.rules.get(token.object_id).card.name,'Treasure')
        self.assertTrue(any(perm.id==token.object_id for perm in p.permanents))
        self.assertTrue(t.world.consistent())
    def test_no_legacy_separate_response_entrypoint(self):
        with self.assertRaises(RuntimeError):self.t.respond(base.Action(0,'test','instant','draw',1))

class SharedStackTests(unittest.TestCase):
    def setUp(self):self.t=CentralTable(seed=444,trace=False)
    def _set(self,seat,cards,mana=10):
        p=self.t.players[seat];p.hand=list(cards);p.mana=mana
        if p is self.t.details:
            p.ready_sources=['Island']*10;p.floating=(0,0,0)
        return p
    def test_counterspell_chain_uses_both_seats_and_lifo(self):
        t=self.t
        original=base.CardSpec('Original Spell','burn',3,'sorcery','burn',{'damage':5})
        counter=base.CardSpec('Stop Original','counter',2,'instant','counter',{'can_counter_types':('sorcery','instant')})
        counter2=base.CardSpec('Stop Counter','counter',2,'instant','counter',{'can_counter_types':('instant',)})
        self._set(1,[original,counter2])
        self._set(2,[counter]);self._set(3,[])
        sequence=[2,1]
        def respond(frame,options):
            if not sequence:return None
            seat=sequence.pop(0)
            return next((o for o in options if o[1].seat==seat),None)
        t.response_policy=respond
        a=base.Action(1,original.name,'sorcery','burn',3,target=3,parameters={'damage':5})
        self.assertTrue(t.cast(a))
        self.assertEqual(t.players[3].life,35) # counter-counter restored original spell
        self.assertEqual(t.spell_stack.max_depth_seen,3)
        self.assertEqual(t.counts['counter_counters'],1)
        self.assertEqual(t.spell_stack.spells_countered,1)
    def test_countered_spell_does_not_apply_effect(self):
        t=self.t
        original=base.CardSpec('Original Spell','burn',2,'sorcery','burn',{'damage':12})
        counter=base.CardSpec('Counter','counter',2,'instant','counter',{'can_counter_types':('sorcery',)})
        self._set(1,[original]);self._set(2,[counter]);self._set(3,[])
        t.response_policy=lambda frame,opts:next((o for o in opts if o[1].seat==2),None)
        a=base.Action(1,'Original Spell','sorcery','burn',2,target=3,parameters={'damage':12})
        t.cast(a)
        self.assertEqual(t.players[3].life,40)
        self.assertEqual(t.counts['spells_countered'],1)
    def test_triggers_fire_even_if_original_countered(self):
        t=self.t
        t.add_creature(t.details,2,1,'Young Pyromancer')
        orig=detailed.named_spec('Preordain');counter=base.CardSpec('Counter','counter',2,'instant','counter',{'can_counter_types':('sorcery',)})
        self._set(0,[orig]);self._set(2,[counter]);self._set(1,[]);self._set(3,[])
        t.response_policy=lambda frame,opts:next((o for o in opts if o[1].seat==2),None)
        t.cast(t.action_for(t.details,orig))
        self.assertTrue(any(c.name=='Elemental' and c.token for c in t.details.creatures))
    def test_guard_depth_cannot_infinite_counter(self):
        t=self.t;t.rules.guard.limits=SafetyLimits(max_stack_depth=2)
        t.safe_runner=t.rules.guard
        with self.assertRaises(SafetyStop):
            t.safe_runner.check(stack_depth=3)
    def test_finite_unchanged_state_repeated_guard(self):
        t=self.t
        for _ in range(3):t.safe_runner.check(('identical',))
        with self.assertRaises(SafetyStop):t.safe_runner.check(('identical',))

class IntegrationDiagnostics(unittest.TestCase):
    def test_short_four_player_seeded_games(self):
        for seed in (102,103,104,404):
            t=CentralTable(seed=seed,trace=False).run(10)
            self.assertEqual(len(t.players),4)
            self.assertTrue(t.world.consistent())
            self.assertIsNone(t.safety_stop)
            self.assertLessEqual(t.spell_stack.max_depth_seen,64)
    def test_reproducibility(self):
        a=CentralTable(seed=103,trace=False).run(8).summary()
        b=CentralTable(seed=103,trace=False).run(8).summary()
        self.assertEqual(a,b)
    def test_different_deck_players_same_shared_table(self):
        t=CentralTable(('control','tokens','ramp_stompy'),seed=16,trace=False).run(6)
        self.assertEqual(len(t.rules.controlled(1)),sum(1 for o in t.rules.on_battlefield() if o.controller==1))
        self.assertTrue(t.world.consistent())
    def test_pressure_seed_with_elimination_maintains_consistency(self):
        for seed in range(75,125):
            t=CentralTable(seed=seed,trace=False).run(12)
            self.assertTrue(t.world.consistent())

if __name__=='__main__':unittest.main(verbosity=2)
