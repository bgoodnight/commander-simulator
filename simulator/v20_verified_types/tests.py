import unittest
from verified_table import VerifiedTable,read_types

class VerifiedTypesTests(unittest.TestCase):
    def setUp(self):
        self.t=VerifiedTable(seed=921);self.t.active_seat=0;self.t.phase='main';self.t.priority_policy=lambda *args:None
        self.t.rules.mana_pools[0]=(10,10,10);self.p=self.t.details
    def test_all_deck_names_verified(self):
        self.assertEqual(len(read_types()),82);self.assertTrue(self.t.tutor_library_known(0))
        self.t.assert_consistent()
    def test_corrects_preexisting_type_errors(self):
        names={'Chaos Warp':'instant','Muddle the Mixture':'instant','Underworld Breach':'enchantment','Frostboil Snarl':'land'}
        for name,typ in names.items():
            o=next(o for o in self.t.rules.objects.values() if o.owner==0 and o.card.name==name)
            self.assertIn(typ,o.types)
    def test_unsupported_cards_remain_unsupported(self):
        c=next(c for c in self.p.hand+self.p.library if c.name=='Fabricate')
        self.assertEqual(c.effect,'unsupported')
    def test_mystical_tutor_can_find_previously_unknown_instant(self):
        target=next(o.object_id for o in self.t.rules.objects.values() if o.owner==0 and o.card.name=='Consider')
        if self.t.rules.get(target).zone!='library':target=self.t.zones.move(target,'library')
        card=next(c for c in self.p.hand+self.p.library if c.name=='Mystical Tutor')
        if card not in self.p.hand:
            oid=self.t.zones.move(card.object_id,'hand');card=next(c for c in self.p.hand if c.object_id==oid)
        self.t.tutor_policy=lambda req:next(c.object_id for c in req.cards if c.name=='Consider')
        self.assertTrue(self.t.cast(self.t.action_for_card(self.p,card)))
        self.assertEqual(self.p.library[-1].name,'Consider');self.t.assert_consistent()

if __name__=='__main__':unittest.main()
