"""Run with `python tests.py`; all tests intentionally require only stdlib."""
import unittest,random
from dataclasses import replace
from rules import (GameKernel,CardDefinition,Cost,Ability,Modifier,Event,Effect,ExecutionGuard,
                   SafetyLimits,SafetyStop)
from catalog import (MAGNUS,PYROMANCER,ICONOCLAST,HARMONIC,STORM_KILN,ARCHMAGE,
                     GOBLIN,BARAL,TREASURE,ELEMENTAL,SPAWN,STORMSPLITTER)
from loops import LoopResolver,LoopCertificate,SafeActionRunner,PilotSafety
from bridge import ModularTable

class CardAndRuleContracts(unittest.TestCase):
    def setUp(self):self.k=GameKernel()
    def test_card_types_are_distinct(self):
        self.assertIn('creature',MAGNUS.types);self.assertIn('Demon',MAGNUS.subtypes)
        self.assertNotIn('instant',MAGNUS.types)
    def test_keywords_flying_blocked_only_by_flyer_reach(self):
        a=self.k.add(MAGNUS,0)
        norm=self.k.add(PYROMANCER,1)
        reach=self.k.add(replace(PYROMANCER,card_id='reach',keywords=frozenset({'reach'})),1)
        flier=self.k.add(replace(PYROMANCER,card_id='flier',keywords=frozenset({'flying'})),1)
        ids={x.object_id for x in self.k.legal_blockers(a.object_id,1)}
        self.assertEqual(ids,{reach.object_id,flier.object_id})
        self.assertEqual(len(self.k.controlled(1)),3) # no live-list mutation
        self.assertNotIn(norm.object_id,ids)
    def test_hexproof_vs_self_target_and_shroud(self):
        o=self.k.add(MAGNUS,0)
        self.k.add_modifier(o.object_id,Modifier(keywords=frozenset({'hexproof'})))
        self.assertTrue(self.k.legal_target(0,o.object_id,{'creature'}))
        self.assertFalse(self.k.legal_target(1,o.object_id,{'creature'}))
        self.k.add_modifier(o.object_id,Modifier(keywords=frozenset({'shroud'})))
        self.assertFalse(self.k.legal_target(0,o.object_id,{'creature'}))
    def test_destroy_indestructible_no_effect(self):
        o=self.k.add(MAGNUS,0)
        self.k.add_modifier(o.object_id,Modifier(keywords=frozenset({'indestructible'})))
        self.assertTrue(self.k.legal_target(1,o.object_id,{'creature'}))
        self.assertIsNone(self.k.destroy(o.object_id))
        self.assertEqual(self.k.get(o.object_id).zone,'battlefield')
    def test_exile_and_sacrifice_ignore_indestructible(self):
        for op in ('exile','sacrifice'):
            o=self.k.add(MAGNUS,0)
            self.k.add_modifier(o.object_id,Modifier(keywords=frozenset({'indestructible'})))
            move=getattr(self.k,op)(o.object_id)
            self.assertIsNotNone(move)
            self.assertNotEqual(self.k.get(move.new_object_id).zone,'battlefield')
            self.assertNotIn(o.object_id,self.k.objects)
    def test_zero_toughness_ignores_indestructible(self):
        o=self.k.add(MAGNUS,0)
        self.k.add_modifier(o.object_id,Modifier(toughness=-5,keywords=frozenset({'indestructible'})))
        self.k.check_state_based()
        moved=self.k.moves[-1]
        self.assertEqual(self.k.get(moved.new_object_id).zone,'graveyard')
    def test_marked_damage_resets_at_cleanup(self):
        o=self.k.add(MAGNUS,0)
        self.k.mark_damage(o.object_id,3)
        self.assertEqual(o.damage_marked,3)
        self.k.cleanup();self.assertEqual(o.damage_marked,0)
    def test_lethal_damage_destroys_normal_not_indestructible(self):
        a=self.k.add(MAGNUS,0);b=self.k.add(PYROMANCER,1)
        self.k.add_modifier(a.object_id,Modifier(keywords=frozenset({'indestructible'})))
        self.k.mark_damage(a.object_id,10);self.k.mark_damage(b.object_id,5)
        self.assertIn(a.object_id,self.k.objects);self.assertNotIn(b.object_id,self.k.objects)
        self.assertEqual(self.k.get(self.k.moves[-1].new_object_id).zone,'graveyard')
    def test_counters_distinct_from_damage_and_temporary_modifiers(self):
        o=self.k.add(PYROMANCER,0)
        self.k.add_counter(o.object_id,'+1/+1',2)
        self.k.add_modifier(o.object_id,Modifier(4,1,expires_at='end_turn'))
        self.assertEqual((o.power,o.toughness),(8,4))
        self.k.cleanup();self.assertEqual((o.power,o.toughness),(4,3))
    def test_bounce_and_recast_have_new_object_identity(self):
        old=self.k.add(PYROMANCER,0)
        self.k.add_counter(old.object_id,'+1/+1',2)
        moved=self.k.bounce(old.object_id)
        self.assertNotIn(old.object_id,self.k.objects)
        self.assertEqual(self.k.get(moved.new_object_id).zone,'hand')
        returned=self.k.move(moved.new_object_id,'battlefield','resolve')
        new=self.k.get(returned.new_object_id)
        self.assertNotEqual(new.object_id,old.object_id)
        self.assertEqual((new.power,new.toughness),(2,1))
        with self.assertRaises(KeyError):self.k.get(old.object_id)
    def test_spell_target_cannot_follow_old_object_id(self):
        old=self.k.add(MAGNUS,0)
        moved=self.k.bounce(old.object_id)
        new=self.k.move(moved.new_object_id,'battlefield','resolve')
        with self.assertRaises(KeyError):self.k.execute(Effect.make('destroy'),1,old.object_id)
        self.assertEqual(self.k.get(new.new_object_id).zone,'battlefield')
    def test_graveyard_dies_event_and_bounce_doesnt(self):
        a=self.k.add(PYROMANCER,0);b=self.k.add(PYROMANCER,1)
        self.k.destroy(a.object_id);move=self.k.bounce(b.object_id)
        self.assertEqual([e.name for e in self.k.events].count('dies'),1)
        self.assertEqual(self.k.get(move.new_object_id).zone,'hand')
    def test_tokens_cease_after_moving_and_treasure_not_creature(self):
        a=self.k.add(ELEMENTAL,0,token=True);self.k.add(TREASURE,0,token=True)
        self.assertEqual(self.k.tokens(0),2)
        self.assertEqual(self.k.tokens(0,True),1)
        self.k.destroy(a.object_id)
        self.assertNotIn(a.object_id,self.k.objects)
        self.assertEqual(self.k.tokens(0,True),0)
    def test_commander_enters_graveyard_then_command_with_death_event(self):
        a=self.k.add(MAGNUS,0)
        moved=self.k.destroy(a.object_id,commander_choice=True)
        self.assertTrue(moved.commander_replacement)
        self.assertEqual(self.k.get(moved.new_object_id).zone,'command')
        self.assertNotIn(a.object_id,self.k.objects)
        self.assertTrue(any(e.name=='dies' for e in self.k.events))
    def test_commander_can_remain_graveyard_by_choice(self):
        a=self.k.add(MAGNUS,0)
        move=self.k.destroy(a.object_id)
        self.assertEqual(self.k.get(move.new_object_id).zone,'graveyard')
    def test_trigger_only_correct_controller(self):
        p=self.k.add(PYROMANCER,0)
        self.assertEqual(self.k.triggers(Event('spell_cast',1,spell_types=frozenset({'instant'}))),[])
        r=self.k.triggers(Event('spell_cast',0,spell_types=frozenset({'instant'})))
        self.assertEqual(len(r),1);self.assertEqual(r[0].quantity,1)
    def test_pyromancer_triggers_if_spell_cast_not_creature(self):
        self.k.add(PYROMANCER,0)
        self.assertEqual(len(self.k.triggers(Event('spell_cast',0,spell_types=frozenset({'creature'})))),0)
        self.assertEqual(len(self.k.triggers(Event('spell_cast',0,spell_types=frozenset({'sorcery'})))),1)
    def test_harmonic_doubles_shaman_not_monk(self):
        self.k.add(PYROMANCER,0);self.k.add(ICONOCLAST,0);self.k.add(HARMONIC,0)
        r=self.k.triggers(Event('spell_cast',0,spell_types=frozenset({'instant'})))
        amounts={self.k.get(t.source_id).card.name:t.quantity for t in r}
        self.assertEqual(amounts,{'Young Pyromancer':2,'Third Path Iconoclast':1})
    def test_harmonic_doubles_wizard_and_stackable(self):
        self.k.add(ARCHMAGE,0);self.k.add(HARMONIC,0);self.k.add(HARMONIC,0)
        r=self.k.triggers(Event('spell_cast',0,spell_types=frozenset({'instant'})))
        self.assertEqual(r[0].quantity,3)
    def test_kiln_responds_to_copy_and_cast(self):
        self.k.add(STORM_KILN,0)
        self.assertEqual(len(self.k.triggers(Event('spell_cast',0,spell_types=frozenset({'instant'})))),1)
        self.assertEqual(len(self.k.triggers(Event('spell_copied',0,spell_types=frozenset({'instant'})))),1)
    def test_magnus_combat_damage_trigger_source_identity(self):
        a=self.k.add(MAGNUS,0);b=self.k.add(MAGNUS,1)
        x=self.k.triggers(Event('combat_damage_player',0,a.object_id,amount=4))
        self.assertEqual(len(x),1);self.assertEqual(x[0].controller,0)
        self.assertEqual(self.k.triggers(Event('combat_damage_player',0,a.object_id,amount=0)),[])
        self.assertNotEqual(x[0].source_id,b.object_id)
    def test_trigger_cache_invalidation(self):
        self.k.add(PYROMANCER,0)
        ev=Event('spell_cast',0,spell_types=frozenset({'instant'}))
        self.assertEqual(len(self.k.triggers(ev)),1)
        self.k.add(PYROMANCER,0)
        self.assertEqual(len(self.k.triggers(ev)),2)
    def test_magnus_generic_only_creature_tokens_only(self):
        self.k.add(MAGNUS,0)
        self.k.add(ELEMENTAL,0,token=True);self.k.add(TREASURE,0,token=True)
        original=Cost(4,2,1)
        reduced=self.k.modified_cost(0,frozenset({'instant'}),original)
        self.assertEqual(reduced,Cost(3,2,1))
        self.assertEqual(self.k.modified_cost(0,frozenset({'creature'}),original),original)
        self.assertEqual(self.k.modified_cost(0,frozenset({'artifact'}),original),original)
        self.assertEqual(self.k.modified_cost(1,frozenset({'instant'}),original),original)
    def test_discount_doesnt_touch_colored_with_many_tokens(self):
        self.k.add(MAGNUS,0)
        for _ in range(10):self.k.add(ELEMENTAL,0,token=True)
        self.assertEqual(self.k.modified_cost(0,frozenset({'sorcery'}),Cost(1,2,2)),Cost(0,2,2))
    def test_discount_from_goblin_and_baral_stacks(self):
        self.k.add(GOBLIN,0);self.k.add(BARAL,0)
        self.assertEqual(self.k.modified_cost(0,frozenset({'instant'}),Cost(4,1,1)),Cost(2,1,1))
    def test_trigger_dispatch_creates_tokens(self):
        self.k.add(PYROMANCER,0);self.k.add(HARMONIC,0)
        p=self.k.triggers(Event('spell_cast',0,spell_types=frozenset({'instant'})))
        created=self.k.resolve_trigger_results(p,{'elemental_1_1':ELEMENTAL})
        self.assertEqual(len(created),2)
        self.assertEqual(self.k.tokens(0,True),2)
    def test_object_budget_halts_before_explosion(self):
        k=GameKernel(ExecutionGuard(SafetyLimits(max_objects=3)))
        for _ in range(3):k.add(ELEMENTAL,0,token=True)
        with self.assertRaises(SafetyStop):k.add(ELEMENTAL,0,token=True)
    def test_shared_effect_dispatch_respects_indestructible_and_exile(self):
        o=self.k.add(MAGNUS,0)
        self.k.add_modifier(o.object_id,Modifier(keywords=frozenset({'indestructible'})))
        self.assertIsNone(self.k.execute(Effect.make('destroy'),1,o.object_id))
        self.assertEqual(o.zone,'battlefield')
        move=self.k.execute(Effect.make('exile'),1,o.object_id)
        self.assertEqual(self.k.get(move.new_object_id).zone,'exile')
    def test_shared_effect_dispatch_rejects_unsupported(self):
        o=self.k.add(PYROMANCER,0)
        with self.assertRaises(NotImplementedError):self.k.execute(Effect.make('unknown_ability'),0,o.object_id)
    def test_shared_effect_dispatch_grant_and_counter(self):
        o=self.k.add(PYROMANCER,0)
        self.k.execute(Effect.make('add_counter',quantity=2),0,o.object_id)
        self.k.execute(Effect.make('grant_keyword',keyword='indestructible',duration='end_turn'),0,o.object_id)
        self.assertEqual((o.power,o.toughness),(4,3))
        self.assertIn('indestructible',o.keywords)
        self.k.cleanup();self.assertNotIn('indestructible',o.keywords)
    def test_simultaneous_damage_eliminations(self):
        life={0:40,1:3,2:2,3:15}
        result=self.k.damage_players(life,{1:4,2:4,3:4},source=0)
        self.assertEqual(result.eliminated,(1,2))
        self.assertEqual((life[1],life[2],life[3]),(-1,-2,11))
        self.assertEqual([e.name for e in self.k.events].count('player_eliminated'),2)
    def test_two_distinct_real_decks_share_types_and_rules(self):
        self.k.add(MAGNUS,0);self.k.add(MAGNUS,1)
        self.k.add(ELEMENTAL,0,token=True)
        self.k.add(ELEMENTAL,1,token=True);self.k.add(ELEMENTAL,1,token=True)
        cost=Cost(4,1,1)
        self.assertEqual(self.k.modified_cost(0,{'instant'},cost),Cost(3,1,1))
        self.assertEqual(self.k.modified_cost(1,{'instant'},cost),Cost(2,1,1))
    def test_custom_effect_is_scoped_to_game(self):
        other=GameKernel();self.k.register_effect('unique',lambda kernel,actor,target,effect:'registered')
        self.assertEqual(self.k.execute(Effect.make('unique'),0),'registered')
        with self.assertRaises(NotImplementedError):other.execute(Effect.make('unique'),0)
    def test_player_state_not_global(self):
        a=GameKernel();b=GameKernel();a.add(MAGNUS,0)
        self.assertEqual(len(b.objects),0)

class LoopsAndSafety(unittest.TestCase):
    def test_repeated_identical_state_halts_unresolved(self):
        r=SafeActionRunner(ExecutionGuard(SafetyLimits(max_repeated_states=2,max_seconds=10)))
        result=r.execute(1,lambda:'repeat',lambda a:True,lambda:('unchanged',))
        self.assertEqual(result['status'],'unresolved');self.assertEqual(result['reason'],'repeated_game_state')
    def test_action_budget_halts_changing_state(self):
        x=[0]
        r=SafeActionRunner(ExecutionGuard(SafetyLimits(max_actions_per_turn=5,max_seconds=10)))
        result=r.execute(1,lambda:'token',lambda a:(x.__setitem__(0,x[0]+1) or True),lambda:tuple(x))
        self.assertEqual(result['status'],'unresolved');self.assertEqual(result['reason'],'action_budget_per_turn')
    def test_validated_deterministic_lethal_skips_iterations(self):
        c=LoopCertificate('burn',True,True,True,damage_each_opponent=1,targets=(1,2,3),response_window_resolved=True)
        x=LoopResolver().evaluate(c,{1:15,2:38,3:40},50)
        self.assertEqual(x.kind,'lethal');self.assertEqual(x.cycles,40)
        self.assertEqual(x.damage,((1,40),(2,40),(3,40)))
    def test_self_deck_safety_before_lethal(self):
        c=LoopCertificate('burn_draw',True,True,True,damage_each_opponent=1,draw_per_cycle=1,targets=(1,2,3),response_window_resolved=True)
        x=LoopResolver().evaluate(c,{1:4,2:10,3:20},library_size=14)
        self.assertEqual(x.kind,'declined');self.assertEqual(x.reason,'would_deck_before_lethal')
    def test_unverified_combo_not_a_win(self):
        c=LoopCertificate('guess',False,True,True,damage_each_opponent=100,targets=(1,),response_window_resolved=True)
        self.assertEqual(LoopResolver().evaluate(c,{1:40},100).kind,'unresolved')
    def test_open_response_window_cannot_fast_forward(self):
        c=LoopCertificate('blocked',True,True,True,damage_each_opponent=10,targets=(1,),response_window_resolved=False)
        self.assertEqual(LoopResolver().evaluate(c,{1:40},100).kind,'unresolved')
    def test_pure_mana_loop_does_not_create_infinite_integer(self):
        c=LoopCertificate('mana',True,True,True,mana_gain_per_cycle=1,response_window_resolved=True)
        x=LoopResolver().evaluate(c,{1:40},100)
        self.assertEqual(x.kind,'symbolic_mana');self.assertTrue(x.symbolic_mana)
        self.assertEqual(x.cycles,0)
    def test_nonlethal_draw_capped_by_library(self):
        c=LoopCertificate('scry_draw',True,True,True,draw_per_cycle=3,response_window_resolved=True)
        x=LoopResolver().evaluate(c,{1:40},11)
        self.assertEqual((x.kind,x.cycles),('finite',3))
    def test_invalid_loop_delta_declined(self):
        c=LoopCertificate('bad',True,True,True,draw_per_cycle=-1,response_window_resolved=True)
        self.assertEqual(LoopResolver().evaluate(c,{1:40},100).kind,'declined')
    def test_unknown_opponent_blocks_lethal(self):
        c=LoopCertificate('badtargets',True,True,True,damage_each_opponent=1,targets=(1,),response_window_resolved=True)
        self.assertEqual(LoopResolver().evaluate(c,{1:40,2:40},100).kind,'unresolved')
    def test_stack_depth_budget(self):
        g=ExecutionGuard(SafetyLimits(max_stack_depth=3,max_seconds=10))
        with self.assertRaises(SafetyStop):g.check(stack_depth=4)
    def test_trigger_budget(self):
        g=ExecutionGuard(SafetyLimits(max_triggers_per_event=2,max_seconds=10))
        with self.assertRaises(SafetyStop):g.guard_trigger_count(3)

class ActualDeckAdapter(unittest.TestCase):
    def test_real_magnus_mixed_table_runs(self):
        t=ModularTable(('aggro','control','combo'),seed=102,trace=False).run(8)
        self.assertEqual(len(t.players),4)
        self.assertIsNone(t.safety_stop)
        self.assertGreater(t.shared_cost_queries,0)
    def test_shared_triggers_and_characteristics_in_mixed_table(self):
        t=ModularTable(('control','combo','tokens'),seed=404,trace=False,opening=['Sol Ring','Young Pyromancer','Preordain','Ponder','Island','Mountain','Harmonic Prodigy']).run(8)
        self.assertGreater(t.shared_triggers,0)
        self.assertEqual(t.diagnostics()['v7']['safety_stop'],None)
    def test_flying_block_doesnt_mutate_defender(self):
        t=ModularTable(('aggro','control','combo'),seed=11,trace=False)
        a=t.details
        flyer=t.add_creature(a,4,5,'Magnus the Red',keywords=('flying',))
        d=t.players[1];t.add_creature(d,2,2,'ground')
        initial=list(d.creatures)
        self.assertIsNone(t.block(d,flyer,set()))
        self.assertEqual(initial,d.creatures)
    def test_safety_guards_do_not_break_original_suites(self):
        for seed in (101,102,103):
            t=ModularTable(('aggro','control','combo'),seed=seed,trace=False).run(8)
            self.assertIsNone(t.safety_stop)

if __name__=='__main__':unittest.main(verbosity=2)
