import unittest
from commander_sim.queries import Match, ObjectView, Query, target_legality

class QueryTests(unittest.TestCase):
    def view(self, **changes):
        data = dict(object_id=1, owner=0, controller=0, zone='library',
                    types=frozenset({'creature'}), subtypes=frozenset({'Zombie'}),
                    colors=frozenset({'B'}), mana_value=4, power=2, toughness=3,
                    keywords=frozenset(), token=False)
        data.update(changes)
        return ObjectView(**data)

    def test_combined_tutor_characteristics(self):
        query=Query(zones=frozenset({'library'}),types_all=frozenset({'creature'}),
                    subtypes_all=frozenset({'Zombie'}),max_power=2)
        self.assertIs(query.matches(self.view()),Match.YES)
        self.assertIs(query.matches(self.view(power=3)),Match.NO)
        self.assertIs(query.matches(self.view(zone='graveyard')),Match.NO)

    def test_unknown_does_not_match_as_true(self):
        query=Query(color='B',max_mana_value=4)
        self.assertIs(query.matches(self.view(colors=None)),Match.UNKNOWN)
        self.assertIs(query.matches(self.view(mana_value=None)),Match.UNKNOWN)
        self.assertIs(query.matches(self.view(colors=None,mana_value=5)),Match.NO)

    def test_target_restrictions_are_conservative(self):
        self.assertIs(target_legality(self.view(),source_controller=1),Match.UNKNOWN)
        self.assertIs(target_legality(self.view(),source_controller=1,restrictions_complete=True),Match.YES)
        self.assertIs(target_legality(self.view(keywords=frozenset({'hexproof'})),source_controller=1,restrictions_complete=True),Match.NO)
        self.assertIs(target_legality(self.view(keywords=frozenset({'ward'})),source_controller=1,restrictions_complete=True),Match.UNKNOWN)
        self.assertIs(target_legality(self.view(keywords=frozenset({'shroud'})),source_controller=0,restrictions_complete=True),Match.NO)

if __name__=='__main__':unittest.main()
