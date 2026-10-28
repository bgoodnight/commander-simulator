"""Focused current-rule combat allocation, strike timing and audit checks."""
import unittest
from dataclasses import replace
from expanded import CombatTable
from combat_turns import CombatDriver
from rules import Modifier
from audit import build


class CombatTests(unittest.TestCase):
    def setUp(self):
        self.t = CombatTable(seed=73)
        self.t.priority_policy = lambda *args: None
        self.p = self.t.details; self.q = self.t.players[1]
        self.t.active_seat = self.p.seat
        self.c = self.t.combat_engine
        for p in self.t.players:
            for oid in self.t.zones.ids(p.seat, 'hand'): self.t.zones.move(oid, 'library')

    def creature(self, p=None, power=3, toughness=3, keywords=()):
        return self.t.add_creature(p or self.p, power, toughness, 'synthetic combat fixture',
                                   token=True, keywords=keywords)

    def board(self, power=6, toughness=6, keywords=(), blockers=((2,2),(3,3))):
        a = self.creature(power=power, toughness=toughness, keywords=keywords)
        bs = [self.creature(self.q, p, t) for p,t in blockers]
        self.t.attack_ready[self.p.seat] = {a.id}
        self.c.declare_attackers(self.p, [(a.id, self.q.seat)])
        self.c.declare_blockers([(a.id, b.id) for b in bs])
        return a, bs

    def hit(self, stage='combat_damage', checkpoint=True):
        r = self.c.damage(self.p, stage)
        if checkpoint: self.t.spell_stack.resolve()
        return r

    def keywords(self, c, *keywords):
        o = self.t.rules.get(c.id); o.card = replace(o.card, keywords=frozenset(keywords)); self.t.rules._dirty()

    def test_multiple_blockers_commit_together(self):
        a, bs = self.board()
        self.assertEqual(self.c.attacks[0].blockers, [b.id for b in bs])

    def test_duplicate_blocker_rejected_atomically(self):
        a, bs = self.board()
        before = list(self.c.attacks[0].blockers)
        with self.assertRaises(ValueError): self.c.declare_blockers([(a.id,bs[0].id)]*2)
        self.assertEqual(self.c.attacks[0].blockers, before)

    def test_one_blocker_cannot_block_two_attackers(self):
        a, bs = self.board(); b = self.creature()
        self.t.attack_ready[0].add(b.id)
        self.t.rules.get(a.id).tapped=False
        self.c.declare_attackers(self.p, [(a.id,1),(b.id,1)])
        with self.assertRaises(ValueError): self.c.declare_blockers([(a.id,bs[0].id),(b.id,bs[0].id)])
        self.assertTrue(all(not x.blocked for x in self.c.attacks))

    def test_tapped_blocker_rejected(self):
        a, bs = self.board(); self.t.rules.get(bs[0].id).tapped = True
        with self.assertRaises(ValueError): self.c.declare_blockers([(a.id,bs[0].id)])

    def test_flying_rejects_ground_in_group(self):
        a, bs = self.board(); self.keywords(a,'flying'); self.keywords(bs[0],'reach')
        with self.assertRaises(ValueError): self.c.declare_blockers([(a.id,b.id) for b in bs])

    def test_reach_and_flying_group_legal(self):
        a, bs = self.board(); self.keywords(a,'flying')
        self.keywords(bs[0],'reach'); self.keywords(bs[1],'flying')
        self.c.declare_blockers([(a.id,b.id) for b in bs])
        self.assertEqual(len(self.c.attacks[0].blockers),2)

    def test_no_assignment_order_and_nonlethal_split_legal(self):
        a, bs = self.board(power=4)
        self.t.combat_damage_policy = lambda ctx: {bs[0].id:1, bs[1].id:3}
        r = self.hit()
        self.assertEqual(r['creature_damage'][bs[0].id],1)
        self.assertIn(bs[0].id,self.t.rules.objects)
        self.assertNotIn(bs[1].id,self.t.rules.objects)

    def test_all_damage_can_go_to_one_blocker(self):
        a, bs = self.board(power=4)
        self.t.combat_damage_policy = lambda ctx: {bs[1].id:4}
        self.hit(); self.assertIn(bs[0].id,self.t.rules.objects)

    def test_nontrample_excess_stays_on_creatures(self):
        a, bs = self.board(power=8)
        r = self.hit(); self.assertEqual(sum(r['assignments'][0]['creature_damage'].values()),8)
        self.assertEqual(self.q.life,40)

    def test_multi_block_damage_simultaneous(self):
        a, bs = self.board(power=5,toughness=5)
        r = self.hit(checkpoint=False)
        self.assertEqual(r['creature_damage'][a.id],5)
        self.assertTrue(all(x.id in self.t.rules.objects for x in [a]+bs))
        self.t.spell_stack.resolve()
        self.assertTrue(all(x.id not in self.t.rules.objects for x in [a]+bs))

    def test_trample_excess_after_all_lethal(self):
        a, bs = self.board(power=8,keywords=('trample',))
        r = self.hit(); self.assertEqual(r['player_damage'],{1:3})
        self.assertEqual(self.q.life,37)

    def test_trample_respects_marked_damage(self):
        a, bs = self.board(power=6,keywords=('trample',))
        self.t.rules.get(bs[1].id).damage_marked = 2
        self.assertEqual(self.hit()['player_damage'],{1:3})

    def test_trample_indestructible_still_requires_lethal(self):
        a, bs = self.board(power=8,keywords=('trample',))
        self.keywords(bs[0],'indestructible')
        self.assertEqual(self.hit()['player_damage'],{1:3})
        self.assertIn(bs[0].id,self.t.rules.objects)

    def test_trample_can_overassign_and_deal_no_player_damage(self):
        a, bs = self.board(power=8,keywords=('trample',))
        self.t.combat_damage_policy = lambda ctx:{bs[0].id:8}
        self.hit(); self.assertEqual(self.q.life,40)

    def test_trample_insufficient_lethal_player_assignment_rejected(self):
        a, bs = self.board(power=8,keywords=('trample',))
        self.t.combat_damage_policy = lambda ctx:{bs[0].id:2,'player':6}
        with self.assertRaises(ValueError): self.hit()
        self.assertEqual(self.q.life,40)
        self.assertEqual(self.t.rules.get(a.id).damage_marked,0)

    def test_negative_assignment_rejected(self):
        a, bs = self.board()
        self.t.combat_damage_policy = lambda ctx:{bs[0].id:-1,bs[1].id:7}
        with self.assertRaises(ValueError): self.hit()

    def test_incomplete_assignment_rejected(self):
        a, bs = self.board()
        self.t.combat_damage_policy = lambda ctx:{bs[0].id:1}
        with self.assertRaises(ValueError): self.hit()

    def test_unknown_target_rejected(self):
        self.board(); self.t.combat_damage_policy = lambda ctx:{999999:ctx.power}
        with self.assertRaises(ValueError): self.hit()

    def test_noninteger_assignment_rejected(self):
        a, bs = self.board(); self.t.combat_damage_policy = lambda ctx:{bs[0].id:6.0}
        with self.assertRaises(ValueError): self.hit()

    def test_invalid_later_attacker_does_not_apply_earlier_damage(self):
        a = self.creature(); b = self.creature()
        self.t.attack_ready[0] = {a.id,b.id}
        self.c.declare_attackers(self.p,[(a.id,1),(b.id,2)]); self.c.declare_blockers([])
        self.t.combat_damage_policy = lambda ctx:{'player':ctx.power if ctx.attacker==a.id else -1}
        with self.assertRaises(ValueError): self.hit()
        self.assertEqual([self.t.players[s].life for s in (1,2)],[40,40])

    def test_removed_blocker_reduces_trample_threshold(self):
        a, bs = self.board(power=8,keywords=('trample',))
        self.t.world.move(bs[1].id,'exile','exile')
        self.assertEqual(self.hit()['player_damage'],{1:6})

    def test_all_removed_blockers_trample_hits_player(self):
        a, bs = self.board(power=8,keywords=('trample',))
        for b in bs: self.t.world.move(b.id,'exile','exile')
        self.assertEqual(self.hit()['player_damage'],{1:8})

    def test_all_removed_blockers_no_trample_no_hit(self):
        a, bs = self.board()
        for b in bs:self.t.world.move(b.id,'exile','exile')
        self.hit(); self.assertEqual(self.q.life,40)

    def test_removed_attacker_neither_deals_nor_receives(self):
        a, bs = self.board(); self.t.world.move(a.id,'exile','exile')
        self.assertEqual(self.hit()['creature_damage'],{})

    def test_tapped_blocker_still_deals_after_declaration(self):
        a, bs = self.board(); self.t.rules.get(bs[0].id).tapped = True
        self.assertEqual(self.hit()['creature_damage'][a.id],5)

    def test_no_strike_means_one_step(self):
        self.board(); self.assertFalse(self.c.begin_damage())
        CombatDriver(self.t).damage_steps(self.p)
        self.assertEqual([b['stage'] for b in self.t.combat_batches],['combat_damage'])

    def test_first_strike_kills_before_retaliation(self):
        a, bs = self.board(power=3,toughness=2,keywords=('first_strike',),blockers=((3,3),))
        self.c.begin_damage(); self.hit('first_strike_damage')
        self.assertNotIn(bs[0].id,self.t.rules.objects)
        self.hit(); self.assertIn(a.id,self.t.rules.objects)
        self.assertEqual(self.t.rules.get(a.id).damage_marked,0)

    def test_first_strike_blocker_kills_attacker(self):
        a, bs = self.board(power=3,toughness=2,blockers=((2,3),))
        self.keywords(bs[0],'first_strike'); self.c.begin_damage()
        self.hit('first_strike_damage'); self.hit()
        self.assertNotIn(a.id,self.t.rules.objects)
        self.assertEqual(self.t.rules.get(bs[0].id).damage_marked,0)

    def test_both_first_strike_trade_in_first_batch(self):
        a, bs = self.board(power=3,toughness=3,keywords=('first_strike',),blockers=((3,3),))
        self.keywords(bs[0],'first_strike'); self.c.begin_damage(); self.hit('first_strike_damage')
        self.assertNotIn(a.id,self.t.rules.objects); self.assertNotIn(bs[0].id,self.t.rules.objects)

    def test_unblocked_double_strike_hits_twice(self):
        self.board(power=3,keywords=('double_strike',),blockers=())
        CombatDriver(self.t).damage_steps(self.p); self.assertEqual(self.q.life,34)
        self.assertEqual([s[2] for s in self.t.step_history],['first_strike_damage','combat_damage'])

    def test_double_strike_trample_uses_first_step_marked_damage(self):
        a, bs = self.board(power=4,toughness=9,keywords=('double_strike','trample'),blockers=((1,6),))
        CombatDriver(self.t).damage_steps(self.p)
        self.assertEqual(self.q.life,38); self.assertNotIn(bs[0].id,self.t.rules.objects)

    def test_double_strike_no_trample_stays_blocked_after_kill(self):
        self.board(power=4,toughness=9,keywords=('double_strike',),blockers=((1,2),))
        CombatDriver(self.t).damage_steps(self.p); self.assertEqual(self.q.life,40)

    def test_double_strike_trample_hits_after_first_step_kill(self):
        self.board(power=4,toughness=9,keywords=('double_strike','trample'),blockers=((1,2),))
        CombatDriver(self.t).damage_steps(self.p); self.assertEqual(self.q.life,34)

    def test_losing_first_strike_does_not_grant_second_hit(self):
        a, bs = self.board(power=3,toughness=9,keywords=('first_strike',),blockers=())
        self.c.begin_damage(); self.hit('first_strike_damage'); self.keywords(a)
        self.hit(); self.assertEqual(self.q.life,37)

    def test_gaining_first_strike_does_not_skip_normal_hit(self):
        a, bs = self.board(power=3,toughness=9,blockers=((1,8),))
        self.keywords(bs[0],'first_strike'); self.c.begin_damage(); self.hit('first_strike_damage')
        self.keywords(a,'first_strike'); self.hit()
        self.assertEqual(self.t.rules.get(bs[0].id).damage_marked,3)

    def test_losing_double_strike_prevents_second_hit(self):
        a, bs = self.board(power=3,keywords=('double_strike',),blockers=())
        self.c.begin_damage(); self.hit('first_strike_damage'); self.keywords(a)
        self.hit(); self.assertEqual(self.q.life,37)

    def test_gaining_double_strike_after_first_strike_allows_second_hit(self):
        a, bs = self.board(power=3,keywords=('first_strike',),blockers=())
        self.c.begin_damage(); self.hit('first_strike_damage'); self.keywords(a,'double_strike')
        self.hit(); self.assertEqual(self.q.life,34)

    def test_priority_between_steps_can_remove_attacker(self):
        a, bs = self.board(power=3,keywords=('double_strike',),blockers=())
        observed = []
        def policy(seat,frames,choices):
            if self.t.step=='first_strike_damage' and a.id in self.t.rules.objects:
                observed.append(True); self.t.world.move(a.id,'exile','exile')
            return None
        self.t.priority_policy=policy
        CombatDriver(self.t).damage_steps(self.p)
        self.assertTrue(observed); self.assertEqual(self.q.life,37)

    def test_priority_runs_after_both_steps(self):
        self.board(power=1,keywords=('double_strike',),blockers=())
        observed = set()
        self.t.priority_policy=lambda *args: observed.add(self.t.step)
        CombatDriver(self.t).damage_steps(self.p)
        self.assertEqual(observed,{'first_strike_damage','combat_damage'})

    def test_zero_power_assigns_zero(self):
        self.board(power=0,blockers=()); self.hit(); self.assertEqual(self.q.life,40)

    def test_multiple_defenders_hit_simultaneously(self):
        a = self.creature(power=4); b=self.creature(power=4)
        self.t.attack_ready[0]={a.id,b.id}
        self.c.declare_attackers(self.p,[(a.id,1),(b.id,2)]); self.c.declare_blockers([])
        self.t.players[1].life=self.t.players[2].life=4
        self.hit(); self.assertTrue(all(self.t.players[s].eliminated_round is not None for s in (1,2)))

    def test_default_pilot_can_group_block(self):
        a,bs=self.board(power=5,toughness=5,blockers=((2,2),(3,2)))
        self.c.declare_blockers(); self.assertEqual(len(self.c.attacks[0].blockers),2)

    def test_block_policy_callback_validated(self):
        a,bs=self.board()
        self.t.block_assignment_policy=lambda attacks:[(a.id,bs[0].id)]
        self.c.declare_blockers(); self.assertEqual(self.c.attacks[0].blockers,[bs[0].id])

    def test_pool_empties_between_damage_steps(self):
        self.board(power=1,keywords=('double_strike',),blockers=())
        seen=[]
        def policy(*args):
            if self.t.step=='first_strike_damage':self.t.rules.mana_pools[0]=(2,0,0)
            else:seen.append(self.t.rules.mana_pools[0])
            return None
        self.t.priority_policy=policy;CombatDriver(self.t).damage_steps(self.p)
        self.assertTrue(seen);self.assertTrue(all(pool==(0,0,0) for pool in seen))

    def test_strike_removed_before_damage_does_not_create_extra_step(self):
        a,bs=self.board(keywords=('first_strike',))
        self.keywords(a);self.assertFalse(self.c.begin_damage())

    def test_double_strike_magnus_queues_two_separate_hit_triggers(self):
        self.t.rules.mana_pools[0]=(10,10,10)
        card=self.t.zones.views(0,'command')[0]
        self.assertTrue(self.t.cast(self.t.action_for_card(self.p,card)))
        a=next(c for c in self.p.creatures if c.name=='Magnus the Red')
        self.keywords(a,'flying','double_strike')
        self.t.attack_ready[0]={a.id};self.c.declare_attackers(self.p,[(a.id,1)]);self.c.declare_blockers([])
        CombatDriver(self.t).damage_steps(self.p)
        self.assertEqual(self.q.life,32)
        self.assertEqual(sum(c.name=='Spawn' for c in self.p.creatures),2)

    def test_audit_covers_exact_inventory(self):
        d=build(); self.assertEqual(d['total_cards'],100); self.assertEqual(d['unique_names'],83)
        self.assertEqual(sum(d['physical_counts'].values()),100)
        self.assertEqual({r['quantity'] for r in d['cards'] if r['name']=='Island'},{12})

    def test_audit_does_not_equate_castable_with_complete(self):
        rows={r['name']:r for r in build()['cards']}
        self.assertEqual(rows['Harmonic Prodigy']['status'],'partial')
        self.assertEqual(rows['Twincast']['status'],'unsupported')
        self.assertEqual(rows['Capsize']['status'],'supported subset')

    def test_live_game_conservation_all_seats(self):
        for seat in range(4):
            kinds=['aggro','control','combo']; kinds.insert(seat,'magnus')
            t=CombatTable(kinds,seed=103).run(3)
            self.assertIsNone(t.safety_stop); self.assertTrue(t.assert_consistent())

    def test_reproducible_live_game(self):
        a=CombatTable(seed=74).run(3);b=CombatTable(seed=74).run(3)
        self.assertEqual(a.combat_batches,b.combat_batches)
        self.assertEqual(a.step_history,b.step_history)


if __name__=='__main__':unittest.main()
