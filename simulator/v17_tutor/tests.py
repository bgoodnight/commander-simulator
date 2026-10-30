import unittest
from tutor_table import TutorTable

class TutorTests(unittest.TestCase):
    def setUp(self):
        self.t = TutorTable(seed=901)
        self.t.priority_policy = lambda *args: None
        self.t.active_seat = 0; self.t.phase = 'main'
        self.t.rules.mana_pools[0] = (10, 10, 10)
        self.p = self.t.details
    def give(self,name):
        c=next(c for c in self.p.hand+self.p.library if c.name==name)
        if c not in self.p.hand:
            oid=self.t.zones.move(c.object_id,'hand')
            c=next(c for c in self.p.hand if c.object_id==oid)
        return c
    def cast_tutor(self):
        c=self.give('Mystical Tutor')
        self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
    def test_find_selected_spell_and_draw(self):
        self.t.tutor_policy=lambda req:next(c.object_id for c in req.cards if c.name=='Ponder')
        self.cast_tutor(); self.assertEqual(self.p.library[-1].name,'Ponder')
        self.p.draw();self.assertIn('Ponder',[c.name for c in self.p.hand]);self.t.assert_consistent()
    def test_fail_to_find_still_shuffles(self):
        self.t.tutor_policy=lambda req:None
        before=len(self.t.zones.operations);self.cast_tutor()
        self.assertTrue(any(x[0]=='shuffle' for x in self.t.zones.operations[before:]))
        self.assertIsNone(self.t.tutor_events[-1][2])
    def test_illegal_choice_rejected(self):
        oid=next(oid for oid in self.t.zones.ids(0,'library') if 'land' in self.t.rules.get(oid).types)
        self.t.tutor_policy=lambda req:oid
        with self.assertRaises(ValueError):self.cast_tutor()
    def test_available_as_instant(self):
        self.assertEqual(self.give('Mystical Tutor').card_type,'instant')

    def test_pyromancer_triggers_and_tutor_finds_spell(self):
        c=self.give('Young Pyromancer');self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
        self.t.tutor_policy=lambda req:next(c.object_id for c in req.cards if c.name=='Ponder')
        self.cast_tutor()
        self.assertEqual(sum(o.card.name=='Elemental' for o in self.t.rules.controlled(0)),1)
        self.assertEqual(self.p.library[-1].name,'Ponder')
        self.t.assert_consistent()
    def test_tutor_search_happens_at_resolution(self):
        c=self.give('Mystical Tutor');self.give('Brainstorm');chosen=[];used=[]
        self.t.tutor_policy=lambda req:(chosen.append(tuple(c.name for c in req.cards)) or None)
        def policy(seat,frames,choices):
            choice=next((c for c in choices if seat==0 and frames and c.kind=='spell' and c.action.source=='Brainstorm'),None)
            if choice and not used:used.append(True);return choice
            return None
        self.t.priority_policy=policy
        self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
        self.assertTrue(used);self.assertEqual(len(chosen),1)
        resolved=[x[2] for x in self.t.spell_stack.history if x[0]=='resolve']
        self.assertEqual(resolved[-2:],['spell','spell'])
        self.t.assert_consistent()

if __name__=='__main__':unittest.main()
