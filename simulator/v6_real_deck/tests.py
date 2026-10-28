"""Focused v6 regression tests; run with python tests.py, no external dependencies."""
import unittest
from integrated import MixedTable, ColoredPayment, named_spec, SUPPORTED, CAT, DECK

class RealDeckIntegration(unittest.TestCase):
    def table(self,seed=3):
        t=MixedTable(seed=seed,trace=False);t.interactive=False;t.round_num=4
        return t
    def setup_mana(self,p,names):
        p.land_names=list(names);p.lands=len(names)
        p.ready_sources=list(names);p.floating=(0,0,0)
        p.mana=sum(max(sum(x) for x in ColoredPayment.modes(n)) for n in names)
    def inject_and_cast(self,t,name):
        p=t.details;p.hand.append(named_spec(name));a=t.action_for(p,named_spec(name))
        self.assertTrue(p.payment_policy.can_pay(p,a),f'{name}: {a.cost}, sources {p.ready_sources}')
        self.assertTrue(t.cast(a));return a
    def test_99_plus_commander(self):
        t=self.table();p=t.details
        self.assertEqual(len(p.library)+len(p.hand),99)
        self.assertEqual(DECK['commander'],'Magnus the Red')
        self.assertFalse(any(c.name=='Magnus the Red' for c in p.hand+p.library))
    def test_partial_coverage_explicit(self):
        t=self.table();d=t.diagnostics()
        self.assertGreater(len(d['unsupported_definitions']),25)
        self.assertIn('Chaos Mutation',d['unsupported_definitions'])
        self.assertIn('Young Pyromancer',SUPPORTED)
    def test_blue_red_pips_enforced(self):
        t=self.table();p=t.details
        self.setup_mana(p,['Mountain']*5)
        self.assertFalse(p.payment_policy.can_pay(p,t.action_for(p,named_spec('Counterspell'))))
        self.assertFalse(p.payment_policy.can_pay(p,t.action_for(p,named_spec('Magnus the Red'))))
        self.setup_mana(p,['Island','Mountain','Mountain','Mountain','Mountain'])
        self.assertTrue(p.payment_policy.can_pay(p,t.action_for(p,named_spec('Magnus the Red'))))
    def test_colored_mana_consumed(self):
        t=self.table();p=t.details;self.setup_mana(p,['Island','Mountain'])
        self.inject_and_cast(t,'Preordain')
        self.assertFalse(p.payment_policy.can_pay(p,t.action_for(p,named_spec('Counterspell'))))
        self.assertGreaterEqual(p.mana,0)
    def test_sol_ring_two_colorless_not_blue(self):
        t=self.table();p=t.details;self.setup_mana(p,['Sol Ring'])
        self.assertFalse(p.payment_policy.can_pay(p,t.action_for(p,named_spec('Preordain'))))
        self.assertTrue(p.payment_policy.can_pay(p,t.action_for(p,named_spec('Sol Ring'))))
    def test_signet_needs_activation_mana(self):
        t=self.table();p=t.details;self.setup_mana(p,['Izzet Signet'])
        self.assertFalse(p.payment_policy.can_pay(p,t.action_for(p,named_spec('Young Pyromancer'))))
        self.setup_mana(p,['Izzet Signet','Island'])
        self.assertTrue(p.payment_policy.can_pay(p,t.action_for(p,named_spec('Young Pyromancer'))))
    def test_young_pyromancer_cast_trigger(self):
        t=self.table();p=t.details;self.setup_mana(p,['Island','Mountain','Island','Mountain'])
        self.inject_and_cast(t,'Young Pyromancer');self.inject_and_cast(t,'Preordain')
        self.assertEqual(p.token_count(),1)
    def test_harmonic_doubles_shaman_cast_trigger(self):
        t=self.table();p=t.details;self.setup_mana(p,['Island','Mountain'])
        t.add_creature(p,2,1,'Young Pyromancer');t.add_creature(p,1,3,'Harmonic Prodigy')
        self.inject_and_cast(t,'Preordain')
        self.assertEqual(p.token_count(),2)
    def test_magnus_discount_only_generic(self):
        t=self.table();p=t.details;self.setup_mana(p,['Island','Island','Island'])
        a=t.action_for(p,named_spec('Frantic Search'));self.assertEqual(a.cost,3)
        t.add_creature(p,4,5,'Magnus the Red')
        t.add_creature(p,1,1,'Elemental',token=True);t.add_creature(p,1,1,'Elemental',token=True)
        a=t.action_for(p,named_spec('Frantic Search'));self.assertEqual(a.cost,1)
        self.setup_mana(p,['Mountain']*4)
        self.assertFalse(p.payment_policy.can_pay(p,a))
    def test_pongify_destroys_and_replaces(self):
        t=self.table();p=t.details;q=t.players[1]
        self.setup_mana(p,['Island'])
        big=t.add_creature(q,7,7,'Big beast')
        self.inject_and_cast(t,'Pongify')
        self.assertFalse(any(c.id==big.id for c in q.creatures))
        self.assertTrue(any(c.name=='Ape (Pongify)' and c.power==3 for c in q.creatures))
    def test_magnus_commander_zone_and_tax(self):
        t=self.table();p=t.details;self.setup_mana(p,['Island','Mountain']+['Island']*5)
        a=t.action_for(p,named_spec('Magnus the Red'))
        self.assertEqual(a.cost,5)
        self.assertTrue(t.cast(a));self.assertEqual(p.commander_casts,1)
        c=next(c for c in p.creatures if c.name=='Magnus the Red')
        t.kill_creature(p,c);self.assertTrue(p.commander_in_zone)
        a=t.action_for(p,named_spec('Magnus the Red'))
        self.assertEqual(a.cost,7)
    def test_magnus_combat_spawn(self):
        t=self.table();p=t.details;q=t.players[1]
        t.current_attacker='Magnus the Red';t.damage(q,4,p,'combat')
        self.assertTrue(any(c.name=='Spawn' and c.power==3 for c in p.creatures))
    def test_flying_ground_cannot_block(self):
        t=self.table();a=t.details;b=t.players[1]
        flyer=t.add_creature(a,4,5,'Magnus the Red',keywords=('flying',))
        t.add_creature(b,5,5,'ground')
        self.assertIsNone(t.block(b,flyer,set()))
        t.add_creature(b,5,5,'flyer',keywords=('flying',))
        self.assertIsNotNone(t.block(b,flyer,set()))
    def test_stormsplitter_copy_expires(self):
        t=self.table();p=t.details;self.setup_mana(p,['Island'])
        t.add_creature(p,1,4,'Stormsplitter',keywords=('haste',))
        self.inject_and_cast(t,'Preordain')
        self.assertEqual(sum(c.name=='Stormsplitter' for c in p.creatures),2)
        t._cleanup_expiring()
        self.assertEqual(sum(c.name=='Stormsplitter' for c in p.creatures),1)
    def test_treasure_produces_colored_once(self):
        t=self.table();p=t.details;self.setup_mana(p,['Island'])
        t.add_creature(p,2,2,'Storm-Kiln Artist')
        self.inject_and_cast(t,'Preordain')
        self.assertEqual(p.treasures,1)
        p.hand.append(named_spec('Preordain'))
        self.assertTrue(p.payment_policy.can_pay(p,t.action_for(p,named_spec('Preordain'))))
        # Spell cast creates another Treasure, so check initial payment itself consumed one.
        self.assertTrue(t.cast(t.action_for(p,named_spec('Preordain'))))
        self.assertEqual(p.treasures,1)
    def test_untapped_conditions_and_shock_land(self):
        t=self.table();p=t.details
        t.round_num=1
        p.hand=[named_spec('Steam Vents')];p.life=40
        t.upkeep(p,1)
        self.assertIn('Steam Vents',p.ready_sources)
        self.assertEqual(p.life,38)
        t.round_num=2;p.hand=[named_spec('Stormcarved Coast')];t.upkeep(p,2)
        self.assertIn('Stormcarved Coast',p.land_names)
        self.assertNotIn('Stormcarved Coast',p.ready_sources)
    def test_countered_commander_stays_in_zone_tax_applies(self):
        t=self.table();p=t.details
        self.setup_mana(p,['Island']*5+['Mountain'])
        t.respond=lambda a:True
        self.assertTrue(t.cast(t.action_for(p,named_spec('Magnus the Red'))))
        self.assertTrue(p.commander_in_zone)
        self.assertEqual(p.commander_casts,1)
        self.assertEqual(t.action_for(p,named_spec('Magnus the Red')).cost,7)
    def test_response_counter_pays_blue_and_triggers_pyromancer(self):
        from integrated import base
        t=self.table();p=t.details;self.setup_mana(p,['Island','Island'])
        p.hand=[c for c in p.hand if c.effect!='counter'];p.hand.append(named_spec('Counterspell'))
        t.add_creature(p,2,1,'Young Pyromancer')
        t.interactive=True;t.rng.random=lambda:0.0
        for q in t.players[1:]:q.hand=[c for c in q.hand if c.effect!='counter']
        original=base.Action(1,'Opponent removal','instant','remove',2,target=0)
        self.assertTrue(t.respond(original))
        self.assertEqual(p.counters_used,1)
        self.assertEqual(p.token_count(),1)
        self.assertEqual(p.mana,0)
    def test_engine_creature_not_suicide_attacking(self):
        t=self.table();p=t.details;t.round_num=4;t.interactive=True
        c=t.add_creature(p,2,1,'Young Pyromancer');c.entered_round=1
        t.combat(p)
        self.assertIn(c,p.creatures)
        self.assertFalse(c.tapped)
    def test_reproducible_four_player_game(self):
        a=MixedTable(seed=137,trace=False).run(8)
        b=MixedTable(seed=137,trace=False).run(8)
        self.assertEqual(a.summary(),b.summary())
        self.assertEqual(a.diagnostics(),b.diagnostics())
    def test_unsupported_card_never_cast_as_generic(self):
        t=self.table();p=t.details;self.setup_mana(p,['Island']*10+['Mountain']*10)
        p.hand.append(named_spec('Chaos Mutation'))
        self.assertNotEqual(t.action_for(p,named_spec('Chaos Mutation')).effect,'named_selection')
        self.assertTrue(all(c.source!='Chaos Mutation' for c in [t.action_for(p,c) for c in p.hand if c.effect!='unsupported']))

if __name__=='__main__':unittest.main(verbosity=2)
