import unittest
from verify_cards import verify

class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.deck={('Commander','Magnus the Red'):1,('Library','Island'):2}
        self.cards=[{'name':'Magnus the Red','oracle_id':'a','type_line':'Legendary Creature', 'color_identity':['U','R'],'legalities':{'commander':'legal'}},
                    {'name':'Island','oracle_id':'b','type_line':'Basic Land — Island','color_identity':['U'],'legalities':{'commander':'legal'}}]
    def test_valid_record_set(self):
        result=verify(self.deck,self.cards)
        self.assertTrue(result['all_metadata_verified']);self.assertTrue(result['commander_legality_verified'])
        self.assertEqual(result['deck_card_count'],3)
    def test_missing_and_duplicate_fail_closed(self):
        self.assertFalse(verify(self.deck,self.cards[:1])['all_metadata_verified'])
        result=verify(self.deck,self.cards+[self.cards[0]])
        self.assertEqual(next(x for x in result['cards'] if x['name']=='Magnus the Red')['status'],'ambiguous')
    def test_out_of_identity_and_unknown_legality_are_not_validated(self):
        self.cards[1]['color_identity']=['G']
        result=verify(self.deck,self.cards)
        self.assertFalse(result['all_metadata_verified'])
        self.cards[1]['color_identity']=['U'];del self.cards[1]['legalities']
        self.assertFalse(verify(self.deck,self.cards)['commander_legality_verified'])
    def test_absent_oracle_identity_is_not_verified(self):
        del self.cards[0]['oracle_id']
        self.assertFalse(verify(self.deck,self.cards)['all_metadata_verified'])

    def test_double_faced_name_and_ambiguous_alias(self):
        self.cards[1]['name']='Island // Other Face'
        self.cards[1]['card_faces']=[{'name':'Island'},{'name':'Other Face'}]
        self.assertTrue(verify(self.deck,self.cards)['all_metadata_verified'])
        self.cards.append({'name':'Different // Island','oracle_id':'c','type_line':'Land',
                           'color_identity':[],'legalities':{'commander':'legal'},
                           'card_faces':[{'name':'Island'}]})
        self.assertFalse(verify(self.deck,self.cards)['all_metadata_verified'])

if __name__=='__main__':unittest.main()
