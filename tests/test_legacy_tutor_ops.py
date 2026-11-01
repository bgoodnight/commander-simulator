"""Legacy v17-v35 tutors use one composable search contract.

These fixtures isolate the generic selection, verified characteristic
filter and physical-zone semantics independently of historical tables.
Version-specific replay tests separately prove Magnus behavior remains equal.
"""
import unittest
from types import SimpleNamespace as NS

from commander_sim.legacy_tutor_ops import (
    HISTORICAL_SEARCHES, eligible_search_ids, resolve_historical_search,
)
from commander_sim.effect_templates import compose_effect
from commander_sim.reviewed_tutors import TUTORS


class FakeSelection:
    def request(self, kind, seat, eligible):
        return NS(cards=[NS(object_id=x) for x in eligible], kind=kind, seat=seat)
    def score(self, seat, obj):
        return float(obj.object_id)


class FakeRules:
    def __init__(self, cards):
        self.cards=cards
        self.dirty=0
    def get(self, oid):
        return self.cards[oid]
    def subtypes(self, oid):
        return self.cards[oid].card.subtypes
    def _dirty(self):
        self.dirty+=1


class FakeZones:
    def __init__(self, cards, order):
        self.cards=cards
        self.order={(0, "library"):list(order), (0, "hand"):[]}
        self.shuffles=0
    def ids(self,seat,zone):
        return tuple(self.order[(seat,zone)])
    def move(self,oid,to_zone):
        self.order[(0,"library")].remove(oid)
        new=oid+1000
        self.cards[new]=self.cards.pop(oid)
        self.order[(0,to_zone)].append(new)
        return new
    def shuffle(self,seat):
        self.shuffles+=1
        self.order[(seat,"library")].reverse()


class SharedTutorTests(unittest.TestCase):
    def setUp(self):
        self.cards={
            1:NS(types=frozenset({"artifact"}),card=NS(name="Rock",subtypes=frozenset())),
            2:NS(types=frozenset({"instant"}),card=NS(name="Blue Spell",subtypes=frozenset())),
            3:NS(types=frozenset({"instant"}),card=NS(name="Red Spell",subtypes=frozenset())),
            4:NS(types=frozenset({"sorcery"}),card=NS(name="Expensive",subtypes=frozenset())),
            5:NS(types=frozenset({"creature"}),card=NS(name="Wizard",subtypes=frozenset({"Wizard"}))),
        }
        self.z=FakeZones(self.cards, [1,2,3,4,5])
        self.table=NS(zones=self.z,rules=FakeRules(self.cards),selection=FakeSelection(),
                      tutor_events=[],notes=[])
        self.table.note=self.table.notes.append

    def test_seven_old_cards_are_declarative(self):
        self.assertEqual(set(HISTORICAL_SEARCHES),{
            "mystical_tutor","personal_tutor","merchant_scroll",
            "solve_equation","fabricate","wizardcycling","spellseeker"})
        self.assertEqual(HISTORICAL_SEARCHES["personal_tutor"].effect.destination,
                         "library_top")
        self.assertEqual(HISTORICAL_SEARCHES["spellseeker"].effect.max_mana_value,2)

    def test_shared_registered_tutor_configs_have_single_source_of_truth(self):
        names = {
            "mystical_tutor": "Mystical Tutor",
            "merchant_scroll": "Merchant Scroll",
            "solve_equation": "Solve the Equation",
            "fabricate": "Fabricate",
            "spellseeker": "Spellseeker",
        }
        for key, printed in names.items():
            with self.subTest(card=printed):
                self.assertEqual(HISTORICAL_SEARCHES[key].effect,
                                 compose_effect(TUTORS[printed]["review"]))

    def test_fabricate_moves_one_exact_card_then_shuffles(self):
        result=resolve_historical_search(self.table,0,"fabricate")
        self.assertEqual(result,1001)
        self.assertEqual(self.z.ids(0,"hand"),(1001,))
        self.assertEqual(self.z.shuffles,1)
        self.assertEqual(self.table.tutor_events[-1],("fabricate",0,1001,"Rock"))

    def test_mystical_tutor_does_not_move_card_from_library(self):
        result=resolve_historical_search(self.table,0,"mystical_tutor")
        self.assertEqual(result,4)
        self.assertEqual(self.z.ids(0,"hand"),())
        self.assertEqual(self.z.ids(0,"library")[-1],4)
        self.assertEqual(self.z.shuffles,1)

    def test_merchant_color_filter_fails_closed_without_metadata(self):
        with self.assertRaises(NotImplementedError):
            resolve_historical_search(self.table,0,"merchant_scroll")
        self.assertEqual(self.z.shuffles,0)
        found=eligible_search_ids(self.table,0,HISTORICAL_SEARCHES["merchant_scroll"].effect,
                    printed_colors={"Blue Spell":("U",),"Red Spell":("R",)})
        self.assertEqual(found,(2,))

    def test_spellseeker_restricts_mana_value(self):
        mv={"Blue Spell":2,"Red Spell":3,"Expensive":5}
        result=resolve_historical_search(self.table,0,"spellseeker",
                   mana_value=lambda name:mv[name])
        self.assertEqual(result,1002)
        self.assertEqual(self.table.tutor_events[0][0],"spellseeker")

    def test_wizardcycling_uses_subtype_not_name_or_role(self):
        self.assertEqual(eligible_search_ids(self.table,0,
            HISTORICAL_SEARCHES["wizardcycling"].effect),(5,))

    def test_invalid_policy_rejected_before_zone_mutation(self):
        self.table.tutor_policy=lambda request:5
        with self.assertRaises(ValueError):
            resolve_historical_search(self.table,0,"fabricate")
        self.assertEqual(self.z.shuffles,0)
        self.assertEqual(self.z.ids(0,"hand"),())

    def test_optional_fail_to_find_still_shuffles(self):
        self.table.tutor_policy=lambda request:None
        result=resolve_historical_search(self.table,0,"personal_tutor")
        self.assertIsNone(result)
        self.assertEqual(self.z.shuffles,1)
        self.assertEqual(self.table.tutor_events[-1],("personal_tutor",0,None,None))


if __name__=="__main__":
    unittest.main()
