import unittest
from collections import Counter
from budget_table import BudgetTable,load_deck,card_spec

class BudgetDeckTests(unittest.TestCase):
    def test_list_count_and_commander(self):
        cards=load_deck();self.assertEqual(sum(cards.values()),100)
        self.assertEqual(cards['Commander','Magnus the Red'],1)
        self.assertEqual(cards['Library','Island'],14);self.assertEqual(cards['Library','Mountain'],6)
    def test_game_inventory_is_exact(self):
        t=BudgetTable(seed=3)
        observed=Counter((('Commander' if o.zone=='command' else 'Library'),o.card.name)
                         for o in t.rules.objects.values() if o.owner==t.detailed_seat and not o.token)
        self.assertEqual(observed,load_deck());t.assert_consistent()
    def test_unknown_card_fails_closed(self):
        t=BudgetTable(seed=3)
        obj=next(o for o in t.rules.objects.values() if o.card.name=='Fabricate')
        self.assertEqual(t.zones.specs[obj.card.card_id].effect,'unsupported')
        self.assertEqual(obj.card.coverage,'unimplemented')
    def test_legacy_deck_remains_unchanged(self):
        from tutor_table import TutorTable
        old=TutorTable(seed=3)
        self.assertFalse(any(o.card.name=='Fabricate' for o in old.rules.objects.values()))

    def test_tutor_fails_closed_on_unknown_library_types(self):
        t=BudgetTable(seed=3)
        p=t.details
        c=next(c for c in p.hand+p.library if c.name=='Mystical Tutor')
        if c not in p.hand:
            oid=t.zones.move(c.object_id,'hand');c=next(c for c in p.hand if c.object_id==oid)
        self.assertFalse(t.tutor_library_known(p.seat))
        with self.assertRaises(NotImplementedError): t.cast(t.action_for_card(p,c))

if __name__=='__main__':unittest.main()
