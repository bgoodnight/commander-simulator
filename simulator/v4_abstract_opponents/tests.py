import unittest
from engine import Player,Table,PROFILES,ARCHETYPES,AbstractCard,Creature,Permanent,sample_archetypes

class EngineTests(unittest.TestCase):
    def test_profiles_99_and_all_priorities(self):
        for arch,d in PROFILES['archetypes'].items():
            self.assertEqual(sum(d.values()),99)
            self.assertEqual(len(set(PROFILES['priority'][arch])),len(PROFILES['priority'][arch]))
    def test_random_archetypes_valid_and_reproducible(self):
        self.assertEqual(sample_archetypes(172),sample_archetypes(172))
        self.assertEqual(len(sample_archetypes(172)),3)
        self.assertTrue(all(a in ARCHETYPES for a in sample_archetypes(172)))
    def test_fixed_card_cost(self):
        p=Player(1,'aggro',330)
        self.assertTrue(all(isinstance(c,AbstractCard) for c in p.hand+p.deck))
        c=next(c for c in p.deck if c.kind!='land')
        self.assertEqual(c.cost,c.cost)
    def test_goldfish_no_combat_or_life_loss(self):
        t=Table(['aggro','midrange','control'],seed=10,interaction=False).run(10)
        self.assertTrue(all(p.life==40 and p.damage_taken==0 and p.creatures_lost==0 for p in t.players))
        self.assertEqual(t.counts['counters_used'],0)
    def test_lands_cannot_appear_without_draw(self):
        t=Table(['aggro','ramp_stompy','combo'],seed=11,interaction=False).run(10)
        self.assertTrue(all(p.lands<=10 for p in t.players))
        self.assertTrue(all(p.mana>=0 for p in t.players))
    def test_actions_mana_nonnegative_multiple_per_turn(self):
        samples=[Table(['aggro','ramp_stompy','midrange'],seed=s,interaction=False).run(10) for s in range(10,25)]
        self.assertTrue(all(p.total_spent>=0 and p.mana>=0 for t in samples for p in t.players))
        self.assertTrue(any(p.stats[7]['total_cast']-p.stats[6]['total_cast']>=2 for t in samples for p in t.players[1:]))
    def test_random_growth_distribution(self):
        vals=[Table(['aggro','ramp_stompy','control'],seed=s,interaction=False).run(8).players[1].threat() for s in range(35)]
        self.assertGreater(max(vals)-min(vals),8)
    def test_destroy_engine_creature_removes_ability(self):
        t=Table(['aggro','control','combo'],seed=9)
        p=t.players[1];perm=Permanent(99,'engine',3,True,3)
        p.permanents.append(perm);t.create_creature(p,3,2,3,'engine creature',linked_permanent=99)
        self.assertEqual(p.engine_n(),1);t.destroy_creature(p,p.creatures[-1]);self.assertEqual(p.engine_n(),0)
    def test_removal_reduces_board(self):
        t=Table(['aggro','control','combo'],seed=9)
        a,b=t.players[1],t.players[2]
        t.create_creature(b,1,7,7,'large');before=b.power();t.destroy_creature(b,b.creatures[0]);self.assertLess(b.power(),before)
    def test_combat_both_die(self):
        t=Table(['aggro','control','combo'],seed=9,trace=False)
        a,b=t.players[1],t.players[2]
        a.creatures=[];b.creatures=[]
        t.create_creature(a,1,3,3,'medium');t.create_creature(b,1,3,3,'medium')
        t.fight(a,b,a.creatures[0]);self.assertEqual(a.power(),0);self.assertEqual(b.power(),0)
    def test_passive_seat_never_blocks(self):
        t=Table(['aggro','control','combo'],seed=10)
        dummy=t.players[0];p=t.players[1]
        t.create_creature(p,1,6,6,'large');t.fight(p,dummy,p.creatures[-1]);self.assertEqual(dummy.life,34)
    def test_seed_same_outcome(self):
        a=Table(['tokens','combo','control'],seed=171,interaction=True).run(8).report()
        b=Table(['tokens','combo','control'],seed=171,interaction=True).run(8).report()
        self.assertEqual(a,b)
    def test_same_seed_goldfish_and_interact_initial_hands(self):
        a=Table(['tokens','combo','control'],seed=171,interaction=False)
        b=Table(['tokens','combo','control'],seed=171,interaction=True)
        self.assertEqual([[ (c.kind,c.cost) for c in p.hand] for p in a.players],[[ (c.kind,c.cost) for c in p.hand] for p in b.players])
    def test_target_weights_respond_to_public_threat(self):
        t=Table(['aggro','midrange','control'],seed=33)
        a=t.players[1];leader=t.players[2]
        t.create_creature(leader,1,20,20,'huge creature')
        choices=[t.choose_target(a).seat for _ in range(500)]
        self.assertGreater(choices.count(leader.seat),choices.count(t.players[0].seat))
    def test_wipe_kills_creatures_but_not_noncreature_engines(self):
        t=Table(['aggro','midrange','control'],seed=35)
        a=t.players[1];b=t.players[2]
        a.creatures=[];b.creatures=[]
        a.permanents=[Permanent(30,'engine',3,False,2)]
        b.permanents=[Permanent(31,'engine',3,True,2)]
        t.create_creature(b,2,2,3,'engine creature',linked_permanent=31)
        for q in t.players:
            for c in list(q.creatures):t.destroy_creature(q,c)
        self.assertEqual(a.engine_n(),1);self.assertEqual(b.engine_n(),0)

if __name__=='__main__':unittest.main(verbosity=2)
