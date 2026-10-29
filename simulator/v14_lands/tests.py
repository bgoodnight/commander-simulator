"""Land-entry boundaries, cost/priority fetch interactions and reference hashes."""
import unittest
from land_table import LandTable
from land_cards import FETCH
from rules import CardDefinition
from abilities import ActivatedSpec
from resources import Cost
from reference_state import fingerprint


class LandTests(unittest.TestCase):
    def setUp(self):
        self.t=LandTable(seed=91);self.t.priority_policy=lambda *args:None
        self.p=self.t.details;self.t.active_seat=0;self.t.phase='main'
        for p in self.t.players:
            for oid in self.t.zones.ids(p.seat,'hand'):self.t.zones.move(oid,'library')

    def give(self,name,p=None):
        p=p or self.p
        c=next(c for c in p.hand+p.library if c.name==name)
        if c not in p.hand:
            oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in p.hand if c.object_id==oid)
        return c

    def place(self,name='Island',force_tapped=False):
        c=self.give(name);return self.t.enter_land(self.p,c.object_id,force_tapped=force_tapped,cause='declared_fixture')

    def play(self,name):
        self.t.play_land(self.p,self.give(name),self.t.round_num)
        return self.t.rules.get(self.t.land_events[-1]['object_id'])

    def advance(self):
        self.t.turn_serial+=1;self.t.safe_runner.new_turn(self.t.turn_serial)
        self.t.resources.untap(0);self.t.phase='main';self.t.active_seat=0

    def fetch_setup(self,others):
        ids=[self.place() for _ in range(others)]
        f=self.play('Fabled Passage')
        return f,ids

    def fetch(self,f):return self.t.activate_ability(0,f.object_id,FETCH)
    def last_fetch(self):return next(e for e in reversed(self.t.land_events) if e['kind']=='fetch_resolved')

    def test_basic_supertypes_and_subtypes_all_zones(self):
        island=self.give('Island');mountain=self.give('Mountain')
        for c,typ in ((island,'Island'),(mountain,'Mountain')):
            o=self.t.rules.get(c.object_id);self.assertIn('basic',o.card.supertypes);self.assertEqual(o.subtypes,frozenset({typ}))

    def test_steam_vents_has_both_types_but_not_basic(self):
        o=self.t.rules.get(self.give('Steam Vents').object_id)
        self.assertEqual(o.subtypes,frozenset({'Island','Mountain'}));self.assertNotIn('basic',o.card.supertypes)

    def test_sanctuary_is_island_not_basic(self):
        o=self.t.rules.get(self.give('Mystic Sanctuary').object_id)
        self.assertEqual(o.subtypes,frozenset({'Island'}));self.assertNotIn('basic',o.card.supertypes)

    def test_blue_mana_land_is_not_automatically_island(self):
        for name in ('Command Tower','Training Center','Riverglide Pathway'):
            self.assertNotIn('Island',self.t.rules.get(self.give(name).object_id).subtypes)

    def test_steam_pay_life_untapped_not_damage(self):
        before=self.p.damage_taken;self.t.shock_land_policy=lambda r:True
        o=self.play('Steam Vents');self.assertFalse(o.tapped);self.assertEqual(self.p.life,38)
        self.assertEqual(self.p.damage_taken,before)
        self.assertTrue(any(e.name=='life_paid' and e.amount==2 for e in self.t.rules.events))

    def test_steam_decline_payment_enters_tapped(self):
        self.t.shock_land_policy=lambda r:False;o=self.play('Steam Vents')
        self.assertTrue(o.tapped);self.assertEqual(self.p.life,40)

    def test_steam_cannot_pay_more_life_than_available(self):
        self.p.life=1;self.t.shock_land_policy=lambda r:True;c=self.give('Steam Vents')
        with self.assertRaises(ValueError):self.t.play_land(self.p,c,1)
        self.assertIn(c,self.p.hand);self.assertEqual(self.p.life,1)
        self.assertNotEqual(getattr(self.p,'_land_turn',None),self.t.safe_runner.turn)

    def test_steam_can_pay_exact_life_then_lose_at_checkpoint(self):
        self.p.life=2;self.t.shock_land_policy=lambda r:True;o=self.play('Steam Vents')
        self.assertEqual(self.p.life,0);self.assertFalse(o.tapped)
        self.assertIsNone(self.p.eliminated_round)
        self.t.spell_stack.checkpoint();self.assertIsNotNone(self.p.eliminated_round)

    def test_default_steam_declines_at_low_life(self):
        self.p.life=2;o=self.play('Steam Vents');self.assertTrue(o.tapped);self.assertEqual(self.p.life,2)

    def test_invalid_shock_choice_rejected_before_movement(self):
        self.t.shock_land_policy=lambda r:1;c=self.give('Steam Vents')
        with self.assertRaises(ValueError):self.t.play_land(self.p,c,1)
        self.assertIn(c,self.p.hand)

    def test_forced_tapped_overrides_paid_shock(self):
        self.t.shock_land_policy=lambda r:True;oid=self.place('Steam Vents',True)
        self.assertTrue(self.t.rules.get(oid).tapped);self.assertEqual(self.p.life,38)

    def test_coast_with_one_other_land_tapped(self):
        self.place();self.assertTrue(self.play('Stormcarved Coast').tapped)

    def test_coast_with_two_other_lands_untapped(self):
        self.place();self.place('Mountain');self.assertFalse(self.play('Stormcarved Coast').tapped)

    def test_canal_with_two_other_lands_untapped(self):
        self.place();self.place('Mountain');self.assertFalse(self.play('Spirebluff Canal').tapped)

    def test_canal_with_three_other_lands_tapped(self):
        for _ in range(3):self.place()
        self.assertTrue(self.play('Spirebluff Canal').tapped)

    def test_sulfur_without_types_tapped(self):
        self.place('Command Tower');self.assertTrue(self.play('Sulfur Falls').tapped)

    def test_sulfur_with_basic_island_untapped(self):
        self.place();self.assertFalse(self.play('Sulfur Falls').tapped)

    def test_sulfur_with_steam_vents_untapped_even_if_tapped(self):
        self.t.shock_land_policy=lambda r:False;self.place('Steam Vents')
        self.assertFalse(self.play('Sulfur Falls').tapped)

    def test_sulfur_with_mystic_sanctuary_untapped(self):
        self.place('Mystic Sanctuary');self.assertFalse(self.play('Sulfur Falls').tapped)

    def test_sanctuary_two_other_islands_tapped(self):
        self.place();self.place();self.assertTrue(self.play('Mystic Sanctuary').tapped)

    def test_sanctuary_three_other_islands_untapped(self):
        for _ in range(3):self.place()
        self.assertFalse(self.play('Mystic Sanctuary').tapped)

    def test_sanctuary_counts_steam_as_island(self):
        self.place();self.place();self.place('Steam Vents')
        self.assertFalse(self.play('Mystic Sanctuary').tapped)

    def test_sanctuary_does_not_count_blue_sources_without_island_type(self):
        self.place();self.place();self.place('Command Tower')
        self.assertTrue(self.play('Mystic Sanctuary').tapped)

    def test_training_center_three_opponents_untapped(self):
        self.assertFalse(self.play('Training Center').tapped)

    def test_training_center_two_opponents_untapped(self):
        self.t.eliminate(self.t.players[3],'fixture');self.assertFalse(self.play('Training Center').tapped)

    def test_training_center_one_opponent_tapped(self):
        self.t.eliminate(self.t.players[3],'fixture');self.t.eliminate(self.t.players[2],'fixture')
        self.assertTrue(self.play('Training Center').tapped)

    def test_forced_tap_beats_sufficient_lands(self):
        self.place();self.place();oid=self.place('Stormcarved Coast',True)
        self.assertTrue(self.t.rules.get(oid).tapped)

    def test_pathway_selected_face_controls_mana_only(self):
        self.t.pathway_policy=lambda r:'R';o=self.play('Riverglide Pathway')
        self.assertEqual(tuple(a.output for a in self.t.resources.abilities(o)),((0,0,1),))
        self.assertFalse(o.subtypes)

    def test_invalid_pathway_face_rejected(self):
        self.t.pathway_policy=lambda r:'G'
        with self.assertRaises(ValueError):self.play('Riverglide Pathway')

    def test_passage_enters_without_automatic_fetch_or_mana(self):
        f=self.play('Fabled Passage');self.assertIn(f.object_id,self.t.rules.objects)
        self.assertEqual(self.p.lands,1);self.assertEqual(self.t.resources.abilities(f),())
        self.assertNotIn('Fabled Passage',self.p.graveyard)

    def test_fetch_tap_sacrifice_cost_before_responses(self):
        f,ids=self.fetch_setup(2);observed=[]
        def policy(seat,frames,choices):
            if frames:
                observed.append((f.object_id not in self.t.rules.objects,'Fabled Passage' in self.p.graveyard))
            return None
        self.t.priority_policy=policy;self.fetch(f)
        self.assertTrue(observed);self.assertTrue(all(a and b for a,b in observed))

    def test_tapped_passage_cannot_activate(self):
        f,ids=self.fetch_setup(0);f.tapped=True
        with self.assertRaises(ValueError):self.fetch(f)
        self.assertIn(f.object_id,self.t.rules.objects)

    def test_opponent_cannot_activate_passage(self):
        f,ids=self.fetch_setup(0);self.t.active_seat=1
        with self.assertRaises(ValueError):self.t.activate_ability(1,f.object_id,FETCH)
        self.assertIn(f.object_id,self.t.rules.objects)

    def test_passage_cannot_activate_twice(self):
        f,ids=self.fetch_setup(0);self.fetch(f)
        with self.assertRaises(ValueError):self.fetch(f)

    def test_three_lands_after_fetch_stays_tapped(self):
        f,ids=self.fetch_setup(2);self.fetch(f);r=self.last_fetch()
        self.assertEqual(r['lands_at_resolution'],3);self.assertTrue(self.t.rules.get(r['fetched_id']).tapped)

    def test_four_lands_after_fetch_untaps(self):
        f,ids=self.fetch_setup(3);self.fetch(f);r=self.last_fetch()
        self.assertEqual(r['lands_at_resolution'],4);self.assertFalse(self.t.rules.get(r['fetched_id']).tapped)

    def test_fetched_land_enters_tapped_before_untap(self):
        f,ids=self.fetch_setup(3);self.fetch(f)
        entry=next(e for e in self.t.land_events if e['kind']=='entry' and e['cause']=='basic_fetch')
        self.assertTrue(entry['tapped']);self.assertTrue(self.last_fetch()['untapped'])

    def test_fetch_can_choose_mountain(self):
        f,ids=self.fetch_setup(1)
        self.t.fetch_policy=lambda r:next(b.object_id for b in r.basics if b.name=='Mountain')
        self.fetch(f);self.assertEqual(self.t.rules.get(self.last_fetch()['fetched_id']).card.name,'Mountain')

    def test_nonbasic_island_not_searchable(self):
        f,ids=self.fetch_setup(1);steam=next(c.object_id for c in self.p.library if c.name=='Steam Vents')
        self.t.fetch_policy=lambda r:steam
        with self.assertRaises(ValueError):self.fetch(f)
        self.assertIn('Fabled Passage',self.p.graveyard)

    def test_fetch_can_fail_to_find_and_still_shuffle(self):
        f,ids=self.fetch_setup(0);self.t.fetch_policy=lambda r:None
        before=sum(x[0]=='shuffle' for x in self.t.zones.operations)
        self.fetch(f);self.assertIsNone(self.last_fetch()['fetched_id'])
        self.assertEqual(sum(x[0]=='shuffle' for x in self.t.zones.operations),before+1)

    def test_fetch_without_basics_resolves_and_shuffles(self):
        f,ids=self.fetch_setup(0)
        for oid in self.t.zones.ids(0,'library'):
            if 'basic' in self.t.rules.get(oid).card.supertypes:self.t.zones.move(oid,'graveyard')
        self.fetch(f);self.assertIsNone(self.last_fetch()['fetched_id'])
        self.assertEqual(self.p.life,40)

    def test_search_does_not_draw_or_cast_spell(self):
        f,ids=self.fetch_setup(0);before=self.p.cards_cast;hand=len(self.p.hand)
        self.fetch(f);self.assertEqual(self.p.cards_cast,before);self.assertEqual(len(self.p.hand),hand)

    def test_fetch_does_not_spend_extra_land_drop(self):
        f=self.place('Fabled Passage');self.fetch(self.t.rules.get(f))
        self.assertIsNone(getattr(self.p,'_land_turn',None))
        self.play('Island');self.assertEqual(self.p.lands,2)

    def test_land_drop_still_once_after_passage_play_and_fetch(self):
        f,ids=self.fetch_setup(0);self.fetch(f)
        with self.assertRaises(ValueError):self.play('Island')

    def test_fetched_untapped_land_can_pay_immediately(self):
        f,ids=self.fetch_setup(3);self.t.fetch_policy=lambda r:next(b.object_id for b in r.basics if b.name=='Mountain')
        self.fetch(f);obj=self.t.rules.get(self.last_fetch()['fetched_id'])
        self.assertIn(obj.object_id,{oid for oid,_ in self.t.resources.sources(0)})

    def test_fetched_tapped_land_not_ready_source(self):
        f,ids=self.fetch_setup(0);self.fetch(f);oid=self.last_fetch()['fetched_id']
        self.assertNotIn(oid,{oid for oid,_ in self.t.resources.sources(0)})

    def test_response_can_reduce_land_count_before_fetch_resolves(self):
        f,ids=self.fetch_setup(3);self.give('Capsize');used=[]
        def policy(seat,frames,choices):
            c=next((c for c in choices if seat==0 and c.kind=='spell' and c.action.source=='Capsize'
                    and c.action.target_object==ids[0] and not c.action.tags),None)
            if c and not used:used.append(True);return c
        self.t.priority_policy=policy;self.fetch(f)
        self.assertTrue(used);self.assertEqual(self.last_fetch()['lands_at_resolution'],3)
        self.assertFalse(self.last_fetch()['untapped'])

    def test_ordinary_counterspell_cannot_target_fetch_ability(self):
        f,ids=self.fetch_setup(0);self.give('Counterspell');seen=[]
        def policy(seat,frames,choices):
            if frames and all(x.kind=='activated' for x in frames):
                seen.append(any(c.kind=='spell' and c.action.source=='Counterspell' for c in choices))
            return None
        self.t.priority_policy=policy;self.fetch(f)
        self.assertTrue(seen);self.assertFalse(any(seen))

    def test_countered_fetch_keeps_sacrificed_cost_and_does_not_search(self):
        f,ids=self.fetch_setup(1);q=self.t.players[2]
        rock=self.t.add_permanent(q,'ramp',1,'Synthetic counter source')
        spec=ActivatedSpec('synthetic_counter',Cost(),operation='counter_stack',target_kinds=frozenset({'activated'}))
        self.t.register_activation(self.t.rules.get(rock.id).card.card_id,spec);used=[]
        def policy(seat,frames,choices):
            c=next((c for c in choices if seat==2 and c.kind=='activate' and c.ability==spec),None)
            if c and not used:used.append(True);return c
        self.t.priority_policy=policy;self.fetch(f)
        self.assertTrue(used);self.assertIn('Fabled Passage',self.p.graveyard)
        self.assertFalse(any(e['kind']=='fetch_resolved' for e in self.t.land_events))
        self.assertEqual(self.p.lands,1)

    def test_land_play_wrong_phase_rejected(self):
        self.t.phase='combat'
        with self.assertRaises(ValueError):self.play('Island')

    def test_fetch_can_be_activated_during_opponent_priority_window(self):
        f=self.place('Fabled Passage');self.t.active_seat=1;self.t.phase='combat';used=[]
        def policy(seat,frames,choices):
            c=next((c for c in choices if seat==0 and c.kind=='activate' and c.ability==FETCH),None)
            if c and not used:used.append(True);return c
        self.t.priority_policy=policy;self.t.spell_stack.holder=1;self.t.spell_stack.resolve()
        self.assertTrue(used);self.assertTrue(any(e['kind']=='fetch_resolved' for e in self.t.land_events))

    def test_metadata_survives_bounce_and_reentry(self):
        self.t.shock_land_policy=lambda r:False;o=self.play('Steam Vents')
        self.t.world.move(o.object_id,'hand','bounce');self.advance();again=self.play('Steam Vents')
        self.assertNotEqual(o.object_id,again.object_id);self.assertEqual(again.subtypes,frozenset({'Island','Mountain'}))
        self.assertTrue(again.tapped)

    def test_fingerprint_is_reproducible(self):
        a=LandTable(seed=95).run(3);b=LandTable(seed=95).run(3)
        self.assertEqual(fingerprint(a),fingerprint(b))

    def test_fingerprint_excludes_runtime_and_cache_statistics(self):
        a=LandTable(seed=96).run(2);before=fingerprint(a)
        a.resources.cache_hits+=100;a.safe_runner.start-=100
        self.assertEqual(fingerprint(a),before)

    def test_fingerprint_detects_changed_outcome(self):
        a=LandTable(seed=97).run(2);before=fingerprint(a);a.details.life-=1
        self.assertNotEqual(fingerprint(a),before)

    def test_all_seat_conservation(self):
        for seat in range(4):
            kinds=['aggro','control','combo'];kinds.insert(seat,'magnus');t=LandTable(kinds,seed=98).run(3)
            self.assertIsNone(t.safety_stop);self.assertTrue(t.assert_consistent())
            for p in t.players:
                self.assertEqual(sum(not o.token and o.owner==p.seat for o in t.rules.objects.values()),100 if p is t.details else 99)


if __name__=='__main__':unittest.main()
