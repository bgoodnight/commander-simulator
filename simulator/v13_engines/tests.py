"""Ordered selection, cast/counter triggers, dynamic power and delayed expiry."""
import unittest
from dataclasses import replace
from engine_table import EngineTable
from engine_turns import EngineDriver
from rules import Event,Modifier,TriggerResult,CardDefinition
from abilities import ActivatedSpec
from resources import Cost


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.t=EngineTable(seed=81);self.t.priority_policy=lambda *args:None
        self.p=self.t.details;self.q=self.t.players[1]
        for p in self.t.players:
            for oid in self.t.zones.ids(p.seat,'hand'):self.t.zones.move(oid,'library')
            self.t.rules.mana_pools[p.seat]=(40,40,40)

    def give(self,name=None,p=None,effect=None):
        p=p or self.p
        c=next(c for c in p.hand+p.library if (name is None or c.name==name) and (effect is None or c.effect==effect))
        if c not in p.hand:
            oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in p.hand if c.object_id==oid)
        return c

    def cast(self,name=None,p=None,card=None):
        p=p or self.p;c=card or self.give(name,p)
        self.t.active_seat=p.seat;self.t.phase='main'
        self.assertTrue(self.t.cast(self.t.action_for_card(p,c)))

    def place(self,name):
        self.cast(name)
        return next(o for o in self.t.rules.on_battlefield() if o.card.name==name and not o.token)

    def top(self,names,only=False):
        ids=[]
        for name in names:
            oid=next(c.object_id for c in self.p.library if c.name==name and c.object_id not in ids)
            ids.append(oid)
        if only:
            for oid in self.t.zones.ids(0,'library'):
                if oid not in ids:self.t.zones.move(oid,'graveyard')
        order=self.t.zones.order[0,'library'];order[:]=[x for x in order if x not in ids]+list(reversed(ids))
        return tuple(ids)

    def look_names(self,n):return tuple(self.t.rules.get(x).card.name for x in self.t.selection.look(0,n))
    def copies(self):return [o for o in self.t.rules.on_battlefield() if o.card.name=='Stormsplitter' and o.token]
    def event(self,op):return [e for e in self.t.engine_events if e[0]==op]

    def test_impulse_chooses_from_four_and_orders_bottom(self):
        ids=self.top(['Island','Mountain','Abrade','Capsize'])
        self.t.selection_policy=lambda r:(ids[2],) if r.kind=='look_to_hand' else (ids[3],ids[1],ids[0])
        self.t.selection.resolve('Impulse',0)
        self.assertIn('Abrade',[c.name for c in self.p.hand])
        self.assertEqual(self.t.zones.ids(0,'library')[:3],(ids[0],ids[1],ids[3]))

    def test_impulse_does_not_draw_top_card(self):
        ids=self.top(['Island','Mountain','Abrade','Capsize'])
        self.t.selection_policy=lambda r:(ids[2],) if r.kind=='look_to_hand' else tuple(c.object_id for c in r.cards)
        self.t.selection.resolve('Impulse',0)
        self.assertNotIn(ids[0],self.t.zones.ids(0,'hand'))
        self.assertEqual(len(self.p.hand),1)

    def test_impulse_empty_library_no_loss(self):
        self.top([],only=True);self.t.selection.resolve('Impulse',0)
        self.assertEqual(self.p.life,40)

    def test_impulse_one_card_put_to_hand_not_empty_draw(self):
        self.top(['Island'],only=True);self.t.selection.resolve('Impulse',0)
        self.assertEqual((len(self.p.hand),self.p.life),(1,40))

    def test_telling_time_hand_top_bottom(self):
        ids=self.top(['Island','Mountain','Abrade'])
        self.t.selection_policy=lambda r:(ids[2],) if r.kind=='look_to_hand' else (ids[0],)
        self.t.selection.resolve('Telling Time',0)
        self.assertEqual([c.name for c in self.p.hand],['Abrade'])
        self.assertEqual(self.look_names(1),('Island',))
        self.assertEqual(self.t.zones.ids(0,'library')[0],ids[1])

    def test_telling_time_two_cards_follow_instruction_order(self):
        self.top(['Abrade','Island'],only=True);self.t.selection.resolve('Telling Time',0)
        self.assertEqual(len(self.p.hand),1);self.assertEqual(len(self.p.library),1)
        self.assertEqual(self.p.life,40)

    def test_telling_time_one_card_goes_to_hand(self):
        self.top(['Island'],only=True);self.t.selection.resolve('Telling Time',0)
        self.assertEqual((len(self.p.hand),len(self.p.library),self.p.life),(1,0,40))

    def test_telling_time_empty_does_not_draw(self):
        self.top([],only=True);self.t.selection.resolve('Telling Time',0)
        self.assertEqual(self.p.life,40)

    def test_preordain_bottom_both_then_draw_next(self):
        ids=self.top(['Island','Mountain','Abrade'])
        self.t.selection_policy=lambda r:{'top':(),'bottom':ids[:2]}
        self.t.selection.resolve('Preordain',0)
        self.assertEqual([c.name for c in self.p.hand],['Abrade'])
        self.assertEqual(self.t.zones.ids(0,'library')[:2],tuple(reversed(ids[:2])))

    def test_preordain_reorders_top_before_draw(self):
        ids=self.top(['Island','Abrade'])
        self.t.selection_policy=lambda r:{'top':tuple(reversed(ids)),'bottom':()}
        self.t.selection.resolve('Preordain',0)
        self.assertEqual([c.name for c in self.p.hand],['Abrade'])
        self.assertEqual(self.look_names(1),('Island',))

    def test_preordain_one_card_bottom_still_draws_it(self):
        ids=self.top(['Island'],only=True)
        self.t.selection_policy=lambda r:{'top':(),'bottom':ids}
        self.t.selection.resolve('Preordain',0)
        self.assertEqual([c.name for c in self.p.hand],['Island'])
        self.assertEqual(self.p.life,40)

    def test_preordain_empty_draw_marks_loss(self):
        self.top([],only=True);self.t.selection.resolve('Preordain',0)
        self.assertEqual(self.p.life,0)

    def test_ponder_order_then_draw(self):
        ids=self.top(['Island','Mountain','Abrade'])
        self.t.selection_policy=lambda r:(ids[2],ids[0],ids[1]) if r.kind=='ponder_order' else False
        self.t.selection.resolve('Ponder',0)
        self.assertEqual([c.name for c in self.p.hand],['Abrade'])
        self.assertEqual(self.look_names(2),('Island','Mountain'))

    def test_ponder_can_shuffle_after_looking(self):
        self.top(['Island','Mountain','Abrade'])
        self.t.selection_policy=lambda r:tuple(c.object_id for c in r.cards) if r.kind=='ponder_order' else True
        self.t.selection.resolve('Ponder',0)
        self.assertTrue(any(x[0]=='shuffle' for x in self.t.zones.operations))
        self.assertEqual(len(self.p.hand),1)

    def test_ponder_short_library(self):
        self.top(['Abrade'],only=True);self.t.selection.resolve('Ponder',0)
        self.assertEqual([c.name for c in self.p.hand],['Abrade'])
        self.assertEqual(self.p.life,40)

    def test_ponder_empty_draw_marks_loss(self):
        self.top([],only=True);self.t.selection.resolve('Ponder',0)
        self.assertEqual(self.p.life,0)

    def test_brainstorm_draws_three_puts_two_in_requested_order(self):
        self.top(['Island','Mountain','Abrade'])
        self.t.selection_policy=lambda r:tuple(c.object_id for name in ('Mountain','Island') for c in r.cards if c.name==name)
        self.t.selection.resolve('Brainstorm',0)
        self.assertEqual([c.name for c in self.p.hand],['Abrade'])
        self.assertEqual(self.look_names(2),('Mountain','Island'))

    def test_brainstorm_can_put_back_old_hand_cards(self):
        self.give('Capsize');self.give('Ponder');self.top(['Island','Mountain','Abrade'])
        self.t.selection_policy=lambda r:tuple(c.object_id for name in ('Capsize','Ponder') for c in r.cards if c.name==name)
        self.t.selection.resolve('Brainstorm',0)
        self.assertEqual(self.look_names(2),('Capsize','Ponder'))
        self.assertEqual(len(self.p.hand),3)

    def test_brainstorm_failed_draw_still_puts_back_before_sba(self):
        self.top(['Island'],only=True)
        self.t.selection.resolve('Brainstorm',0)
        self.assertEqual(self.p.life,0);self.assertEqual(len(self.p.hand),0)
        self.assertEqual(self.look_names(1),('Island',))

    def test_brainstorm_no_priority_during_put_back(self):
        self.top(['Island','Mountain','Abrade']);spell=self.give('Brainstorm');other=self.give('Ponder')
        seen=[]
        def policy(r):
            seen.append(self.t.spell_stack.resolving)
            with self.assertRaises(ValueError):self.t.cast(self.t.action_for_card(self.p,other))
            return tuple(c.object_id for c in r.cards[:2])
        self.t.selection_policy=policy;self.cast(card=spell)
        self.assertEqual(seen,[True])

    def test_scry_duplicate_rejected_without_reordering(self):
        ids=self.top(['Island','Abrade']);before=self.t.zones.ids(0,'library')
        self.t.selection_policy=lambda r:{'top':(ids[0],ids[0]),'bottom':()}
        with self.assertRaises(ValueError):self.t.selection.scry(0,2)
        self.assertEqual(self.t.zones.ids(0,'library'),before)

    def test_look_unknown_choice_rejected(self):
        self.top(['Island','Abrade']);self.t.selection_policy=lambda r:(999999,)
        with self.assertRaises(ValueError):self.t.selection.resolve('Impulse',0)

    def test_ponder_incomplete_order_rejected(self):
        self.top(['Island','Abrade']);self.t.selection_policy=lambda r:()
        with self.assertRaises(ValueError):self.t.selection.resolve('Ponder',0)

    def test_ponder_shuffle_must_be_boolean(self):
        self.top(['Island']);self.t.selection_policy=lambda r:tuple(c.object_id for c in r.cards) if r.kind=='ponder_order' else 1
        with self.assertRaises(ValueError):self.t.selection.resolve('Ponder',0)

    def test_choice_exposes_only_looked_at_cards(self):
        self.top(['Island','Mountain','Abrade','Capsize']);seen=[]
        def policy(r):
            seen.append(len(r.cards));return tuple(c.object_id for c in r.cards[:r.count])
        self.t.selection_policy=policy;self.t.selection.resolve('Impulse',0)
        self.assertEqual(seen,[4,3])

    def test_frantic_discard_policy_and_actual_lands_only(self):
        self.top(['Island','Mountain']);rock=self.place('Sol Ring')
        self.t.rules.get(rock.object_id).tapped=True
        self.t.selection_policy=lambda r:tuple(c.object_id for c in r.cards[:r.count])
        self.t.selection.resolve('Frantic Search',0)
        self.assertEqual(len(self.p.hand),0);self.assertTrue(self.t.rules.get(rock.object_id).tapped)

    def test_single_harmonic_prowess_is_not_self_doubled(self):
        h=self.place('Harmonic Prodigy');self.cast('Sol Ring')
        self.assertEqual((h.power,h.toughness),(2,4));self.assertEqual(len(self.event('prowess')),1)

    def test_harmonic_prowess_noncreature_includes_enchantment(self):
        h=self.place('Harmonic Prodigy');self.cast('Arcane Adaptation')
        self.assertEqual(h.power,2)

    def test_harmonic_creature_cast_does_not_trigger_prowess(self):
        h=self.place('Harmonic Prodigy');self.cast('Young Pyromancer')
        self.assertEqual(h.power,1)

    def test_prowess_persists_when_spell_countered(self):
        h=self.place('Harmonic Prodigy');self.give(p=self.t.players[2],effect='counter')
        used=[]
        def policy(seat,frames,choices):
            c=next((c for c in choices if seat==2 and c.kind=='spell' and c.action.effect=='counter'),None)
            if c and not used:used.append(True);return c
        self.t.priority_policy=policy;self.cast('Ponder')
        self.assertTrue(used);self.assertEqual(h.power,2)

    def test_prowess_expires_in_cleanup(self):
        h=self.place('Harmonic Prodigy');self.cast('Ponder');self.t.cleanup_step(self.p)
        self.assertEqual((h.power,h.toughness),(1,3))

    def test_other_harmonic_doubles_prowess(self):
        h=self.place('Harmonic Prodigy')
        c=self.t.add_creature(self.p,1,3,'Harmonic Prodigy',token=True)
        self.cast('Sol Ring')
        self.assertEqual(h.power,3);self.assertEqual(self.t.rules.get(c.id).power,3)

    def test_harmonic_shaman_self_can_be_doubled(self):
        h=self.place('Harmonic Prodigy');h.card=replace(h.card,subtypes=h.card.subtypes|{'Shaman'});self.t.rules._dirty()
        self.cast('Sol Ring');self.assertEqual(h.power,3)

    def test_prowess_captured_source_does_not_follow_bounce(self):
        h=self.place('Harmonic Prodigy')
        self.t._apply_pending(self.t.rules.triggers(Event('spell_cast',0,spell_types=frozenset({'artifact'}))))
        self.t.world.move(h.object_id,'hand','bounce');self.t.spell_stack.resolve()
        self.assertFalse(self.event('prowess'))

    def test_storm_kiln_counts_live_artifacts(self):
        a=self.place('Storm-Kiln Artist');self.assertEqual(a.power,2)
        self.place('Sol Ring');self.assertEqual(a.power,3)
        token=self.t.world.create_treasure(self.p);self.assertEqual(a.power,4)
        self.t.world.move(token.object_id,'exile','exile');self.assertEqual(a.power,3)

    def test_storm_kiln_counts_artifact_creature_tokens(self):
        a=self.place('Storm-Kiln Artist');self.place('Third Path Iconoclast');self.cast('Ponder')
        # Ponder creates one Treasure and one artifact Soldier.
        self.assertEqual(a.power,4)

    def test_storm_kiln_excludes_enemy_and_nonbattlefield_artifacts(self):
        a=self.place('Storm-Kiln Artist');self.t.world.create_treasure(self.q);self.give('Sol Ring')
        self.assertEqual(a.power,2)

    def test_storm_kiln_token_sacrifice_reduces_power_immediately(self):
        a=self.place('Storm-Kiln Artist');token=self.t.world.create_treasure(self.p)
        self.assertEqual(a.power,3)
        self.t.world.move(token.object_id,'graveyard','sacrifice')
        self.assertEqual(a.power,2)

    def test_storm_kiln_pilot_projection_updates_at_checkpoint(self):
        a=self.place('Storm-Kiln Artist');self.t.world.create_treasure(self.p);self.t.spell_stack.checkpoint()
        view=next(c for c in self.p.creatures if c.id==a.object_id);self.assertEqual(view.power,3)

    def test_storm_kiln_magecraft_descriptor_handles_copy_event(self):
        self.place('Storm-Kiln Artist')
        self.t._apply_pending(self.t.rules.triggers(Event('spell_copied',0,spell_types=frozenset({'instant'}))))
        self.t.spell_stack.resolve();self.assertEqual(self.p.treasures,1)

    def counter_with_baral(self,harmonic=False):
        self.place('Baral, Chief of Compliance')
        if harmonic:self.place('Harmonic Prodigy')
        self.give('Counterspell');used=[]
        def policy(seat,frames,choices):
            c=next((c for c in choices if seat==0 and c.kind=='spell' and c.action.source=='Counterspell'),None)
            if c and not used:used.append(True);return c
        self.t.priority_policy=policy;self.cast(p=self.q,card=self.give(p=self.q,effect='creature'))
        self.assertTrue(used)

    def test_baral_loots_after_successful_own_counter(self):
        self.counter_with_baral();self.assertEqual(len(self.event('loot')),1)
        self.assertTrue(self.event('loot')[0][2])

    def test_live_baral_trigger_uses_reviewed_ability_dispatcher(self):
        self.counter_with_baral()
        calls=[x for x in self.t.live_ability_bridge.invocations
               if x.slot_key[2]=='optional_loot']
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0].fidelity,'exact')
        self.assertEqual(len(self.event('loot')),1)

    def test_live_doubled_baral_triggers_invoke_distinct_frames(self):
        self.counter_with_baral(harmonic=True)
        calls=[x for x in self.t.live_ability_bridge.invocations
               if x.slot_key[2]=='optional_loot']
        self.assertEqual(len(calls),2)
        self.assertEqual(len(self.event('loot')),2)

    def test_live_magecraft_dispatches_both_cast_and_copy_hooks(self):
        mage=self.place('Archmage Emeritus')
        for event in ('spell_cast','spell_copied'):
            self.t._apply_pending(self.t.rules.triggers(
                Event(event,0,spell_types=frozenset({'instant'}))))
            self.t.spell_stack.resolve()
        calls=[x for x in self.t.live_ability_bridge.invocations
               if x.slot_key[2]=='draw']
        self.assertEqual(len(calls),2)
        self.assertTrue(all(x.source_object_id==mage.object_id for x in calls))
        self.assertTrue(all(x.fidelity=='exact' for x in calls))
        self.assertEqual(sum(1 for x in self.t.live_ability_bridge.subscriptions._live
            if x[0]==mage.object_id),2)

    def test_live_baral_pending_trigger_survives_source_departure(self):
        b=self.place('Baral, Chief of Compliance')
        self.t.emit('spell_countered_by',controller=0,countered_frame=999)
        self.t.world.move(b.object_id,'hand','bounce')
        self.t.spell_stack.resolve()
        self.assertEqual(len(self.event('loot')),1)
        self.assertEqual(len([x for x in self.t.live_ability_bridge.invocations
            if x.source_object_id==b.object_id]),1)
        self.assertNotIn(b.object_id,self.t.live_ability_bridge._sources)

    def test_baral_loot_is_optional(self):
        self.t.loot_policy=lambda *args:False;self.counter_with_baral()
        self.assertEqual(self.event('loot'),[('loot',0,False)])
        self.assertFalse(any(x['kind']=='baral_discard' for x in self.t.selection.history))

    def test_harmonic_doubles_baral_loot(self):
        self.counter_with_baral(harmonic=True);self.assertEqual(len(self.event('loot')),2)

    def test_opponent_counter_does_not_trigger_our_baral(self):
        self.place('Baral, Chief of Compliance');self.give(p=self.t.players[2],effect='counter');used=[]
        def policy(seat,frames,choices):
            c=next((c for c in choices if seat==2 and c.kind=='spell' and c.action.effect=='counter'),None)
            if c and not used:used.append(True);return c
        self.t.priority_policy=policy;self.cast('Ponder');self.assertFalse(self.event('loot'))

    def test_failed_counter_does_not_trigger_baral(self):
        self.place('Baral, Chief of Compliance')
        self.assertIsNone(self.t.spell_stack.counter(999999,{'spell'},0))
        self.t.spell_stack.resolve();self.assertFalse(self.event('loot'))

    def test_target_fizzle_is_not_a_counter_for_baral(self):
        self.place('Baral, Chief of Compliance');target=self.place('Young Pyromancer');self.give('Capsize')
        q=self.t.players[2];card=self.give(p=q,effect='remove');used=[]
        def policy(seat,frames,choices):
            c=next((c for c in choices if seat==0 and c.kind=='spell' and c.action.source=='Capsize'
                    and c.action.target_object==target.object_id and not c.action.tags),None)
            if c and not used:used.append(True);return c
        self.t.priority_policy=policy;self.t.active_seat=q.seat;self.t.phase='main'
        action=self.t.action_for_card(q,card);action.target=0;action.target_object=target.object_id
        self.assertTrue(self.t.cast(action));self.assertTrue(used)
        self.assertEqual(self.t.spell_stack.fizzled,1);self.assertFalse(self.event('loot'))

    def test_countered_counterspell_does_not_loot_for_baral(self):
        self.place('Baral, Chief of Compliance');self.give('Counterspell')
        self.give(p=self.t.players[2],effect='counter');used=set()
        def policy(seat,frames,choices):
            if seat in used:return None
            candidates=[c for c in choices if c.kind=='spell' and c.action.effect=='counter']
            if seat==0:
                c=next((c for c in candidates if c.action.source=='Counterspell'),None)
            elif seat==2:
                c=next((c for c in candidates if self.t.spell_stack.get(c.action.target_object).action.source=='Counterspell'),None)
            else:c=None
            if c:used.add(seat)
            return c
        self.t.priority_policy=policy;self.cast(p=self.q,card=self.give(p=self.q,effect='creature'))
        self.assertEqual(used,{0,2});self.assertFalse(self.event('loot'))

    def test_countering_trigger_does_not_trigger_baral(self):
        self.place('Baral, Chief of Compliance');self.t.begin_end_step()
        self.t.spell_stack.trigger(TriggerResult(999,0,'draw'));self.t.spell_stack.checkpoint()
        frame=self.t.spell_stack.frames[-1]
        self.t.spell_stack.counter(frame.frame_id,{'triggered'},0);self.t.spell_stack.resolve()
        self.assertFalse(self.event('loot'))

    def test_activated_spell_counter_triggers_baral(self):
        self.place('Baral, Chief of Compliance');rock=self.place('Sol Ring')
        spec=ActivatedSpec('synthetic_counter_fixture',Cost(),operation='counter_stack',target_kinds=frozenset({'spell'}))
        self.t.register_activation(rock.card.card_id,spec);used=[]
        def policy(seat,frames,choices):
            c=next((c for c in choices if seat==0 and c.kind=='activate' and c.ability==spec),None)
            if c and not used:used.append(True);return c
        self.t.priority_policy=policy;self.cast(p=self.q,card=self.give(p=self.q,effect='creature'))
        self.assertTrue(used);self.assertEqual(len(self.event('loot')),1)

    def test_baral_trigger_survives_source_leaving(self):
        b=self.place('Baral, Chief of Compliance')
        self.t.emit('spell_countered_by',controller=0,countered_frame=999)
        self.t.world.move(b.object_id,'hand','bounce');self.t.spell_stack.resolve()
        self.assertEqual(len(self.event('loot')),1)

    def test_baral_discard_can_choose_drawn_card(self):
        self.t.selection_policy=lambda r:(r.cards[-1].object_id,)
        self.counter_with_baral();self.assertTrue(any(r['kind']=='baral_discard' for r in self.t.selection.history))

    def test_stormsplitter_uses_otter_subtype(self):
        s=self.place('Stormsplitter');self.assertEqual(s.card.subtypes,frozenset({'Otter','Wizard'}))

    def test_stormsplitter_copies_retain_trigger_and_grow(self):
        self.place('Stormsplitter');self.cast('Ponder');self.assertEqual(len(self.copies()),1)
        self.cast('Preordain');self.assertEqual(len(self.copies()),3)
        self.assertEqual(len(self.t.delayed_exiles),3)

    def test_harmonic_doubles_each_stormsplitter_copy_trigger(self):
        self.place('Stormsplitter');self.place('Harmonic Prodigy');self.cast('Ponder')
        self.assertEqual(len(self.copies()),2)
        self.cast('Preordain');self.assertEqual(len(self.copies()),8)

    def test_copy_ignores_counters_modifiers_and_tapped_state(self):
        s=self.place('Stormsplitter');self.t.rules.add_counter(s.object_id,'+1/+1',2)
        self.t.rules.add_modifier(s.object_id,Modifier(3,3));s.tapped=True
        self.cast('Ponder');copy=self.copies()[0]
        self.assertEqual((copy.power,copy.toughness,copy.tapped),(1,4,False))
        self.assertEqual(copy.counters['+1/+1'],0);self.assertIn('haste',copy.keywords)

    def test_source_leaves_before_copy_trigger_lki_used(self):
        s=self.place('Stormsplitter')
        self.t._apply_pending(self.t.rules.triggers(Event('spell_cast',0,spell_types=frozenset({'instant'}))))
        self.t.world.move(s.object_id,'hand','bounce');self.t.spell_stack.resolve()
        self.assertEqual(len(self.copies()),1)

    def test_copy_exiles_at_end_step_before_cleanup(self):
        self.place('Stormsplitter');self.cast('Ponder');self.assertEqual(len(self.copies()),1)
        EngineDriver(self.t).window('end','ending')
        self.assertEqual(len(self.copies()),0);self.assertEqual(len(self.event('delayed_exile')),1)

    def test_end_step_copy_waits_for_next_end_step(self):
        s=self.place('Stormsplitter');EngineDriver(self.t).window('end','ending')
        self.t.resolve_trigger(TriggerResult(s.object_id,0,'copy_source_until_end',args=(('copiable',s.card),)))
        self.t.cleanup_step(self.p);self.assertEqual(len(self.copies()),1)
        EngineDriver(self.t).window('end','ending');self.assertFalse(self.copies())

    def test_delayed_exile_is_not_doubled_by_harmonic(self):
        self.place('Stormsplitter');self.place('Harmonic Prodigy');self.cast('Ponder')
        EngineDriver(self.t).window('end','ending')
        self.assertEqual(len(self.event('delayed_exile')),2)

    def test_delayed_exile_tracks_only_original_object(self):
        self.place('Stormsplitter');self.cast('Ponder');old=self.copies()[0]
        self.t.world.move(old.object_id,'hand','bounce')
        EngineDriver(self.t).window('end','ending')
        self.assertFalse(self.copies());self.assertEqual(len(self.event('delayed_exile')),1)

    def test_countered_delayed_exile_does_not_retry_in_cleanup(self):
        self.place('Stormsplitter');self.cast('Ponder')
        self.t.begin_end_step();self.t.spell_stack.checkpoint()
        frame=next(f for f in self.t.spell_stack.frames if f.trigger.op=='exile_object')
        self.t.spell_stack.counter(frame.frame_id,{'triggered'},1);self.t.spell_stack.resolve()
        self.t.cleanup_step(self.p);self.assertEqual(len(self.copies()),1)
        EngineDriver(self.t).window('end','ending');self.assertEqual(len(self.copies()),1)

    def test_next_opponent_end_step_can_expire_token(self):
        s=self.place('Stormsplitter');self.t.active_seat=1;self.t.step='combat_damage'
        self.t.resolve_trigger(TriggerResult(s.object_id,0,'copy_source_until_end',args=(('copiable',s.card),)))
        EngineDriver(self.t).window('end','ending');self.assertFalse(self.copies())

    def test_invalid_optional_loot_choice_rejected(self):
        self.t.loot_policy=lambda *args:1
        with self.assertRaises(ValueError):self.t.resolve_trigger(TriggerResult(999,0,'optional_loot'))

    def test_invalid_put_back_choice_rejected_before_movement(self):
        a=self.give('Abrade');self.give('Capsize');before=self.t.zones.ids(0,'hand')
        self.t.selection_policy=lambda r:(a.object_id,a.object_id)
        with self.assertRaises(ValueError):self.t.selection.put_back(0,2)
        self.assertEqual(self.t.zones.ids(0,'hand'),before)

    def test_dynamic_power_used_by_simultaneous_combat(self):
        a=self.place('Storm-Kiln Artist');self.t.world.create_treasure(self.p)
        self.t.attack_ready[0]={a.object_id};self.t.active_seat=0
        self.t.combat_engine.declare_attackers(self.p,[(a.object_id,1)])
        self.t.combat_engine.declare_blockers([])
        r=self.t.combat_engine.damage(self.p)
        self.assertEqual(r['player_damage'],{1:3})

    def test_copy_event_triggers_magecraft_but_not_cast_only_abilities(self):
        self.place('Archmage Emeritus');self.place('Storm-Kiln Artist')
        h=self.place('Harmonic Prodigy');self.place('Stormsplitter')
        before=len(self.p.hand)
        self.t._apply_pending(self.t.rules.triggers(Event('spell_copied',0,spell_types=frozenset({'instant'}))))
        self.t.spell_stack.resolve()
        self.assertEqual(len(self.p.hand)-before,2)
        self.assertEqual(self.p.treasures,2)
        self.assertEqual(h.power,1);self.assertEqual(len(self.copies()),0)

    def test_selection_preserves_physical_inventory(self):
        for name in ('Brainstorm','Ponder','Preordain','Telling Time','Impulse','Frantic Search'):
            self.t.selection.resolve(name,0);self.t.assert_consistent()
        self.assertEqual(sum(not o.token and o.owner==0 for o in self.t.rules.objects.values()),100)

    def test_engine_sweep_conservation_all_seats(self):
        for seat in range(4):
            kinds=['aggro','control','combo'];kinds.insert(seat,'magnus')
            t=EngineTable(kinds,seed=82).run(3)
            self.assertIsNone(t.safety_stop);self.assertTrue(t.assert_consistent())

    def test_reproducible_live_selection_and_triggers(self):
        a=EngineTable(seed=83).run(5);b=EngineTable(seed=83).run(5)
        self.assertEqual(a.selection.history,b.selection.history)
        self.assertEqual(a.engine_events,b.engine_events)
        self.assertEqual(a.combat_batches,b.combat_batches)


if __name__=='__main__':unittest.main()
