"""Actual paid tutor -> search -> resolve on one authoritative physical kernel."""
import unittest

from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.reviewed_tutor_cast import (
    eligible_reviewed_tutor_targets, cast_and_resolve_reviewed_tutor,
)
from commander_sim.template_resources import TemplateManaService


FABRICATE={
    "oracle_id":"422e1869-134f-463d-9fa1-86b66a998b3e",
    "oracle_text":"Search your library for an artifact card, reveal it, put it into your hand, then shuffle.",
    "mana_cost":"{2}{U}","type_line":"Sorcery","layout":"normal",
    "cmc":3,"colors":["U"],
}
MYSTICAL={
    "oracle_id":"fb81f95c-70f8-4eb7-8d15-15d0ae23ec03",
    "oracle_text":"Search your library for an instant or sorcery card, reveal it, then shuffle and put that card on top.",
    "mana_cost":"{U}","type_line":"Instant","layout":"normal",
    "cmc":1,"colors":["U"],
}


class PaidReviewedTutorTests(unittest.TestCase):
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K()
        self.z=Z(self.k,seed=11)
        self.C=C
        self.metadata={
            "Fabricate":FABRICATE,"Mystical Tutor":MYSTICAL,
            "Island":{"type_line":"Basic Land — Island","colors":[],"cmc":0},
            "Sol Ring":{"type_line":"Artifact","cmc":1,"colors":[]},
            "Blue Instant":{"type_line":"Instant","cmc":2,"colors":["U"]},
            "Red Sorcery":{"type_line":"Sorcery","cmc":2,"colors":["R"]},
        }
        self.mana=TemplateManaService(self.k,self.metadata,frozenset({"U","R"}))

    def add(self,name,zone,types,*,identity=None):
        return self.z.add(self.C(identity or self.metadata.get(name,{}).get(
             "oracle_id","test:"+name),name,frozenset(types),
             coverage="approx"),0,zone)

    def islands(self,count):
        return [self.add("Island","battlefield",{"land"}) for _ in range(count)]

    def test_fabricate_pays_real_sources_resolves_artifact_to_hand(self):
        islands=self.islands(3)
        spell=self.add("Fabricate","hand",{"sorcery"})
        target=self.add("Sol Ring","library",{"artifact"})
        result=cast_and_resolve_reviewed_tutor(
            self.z,0,spell,self.metadata,{"U","R"},self.mana,target_id=target)
        self.assertEqual(result.target_name,"Sol Ring")
        self.assertEqual(result.target_destination,"hand")
        self.assertEqual(self.k.get(result.target_new_id).zone,"hand")
        self.assertEqual(self.k.get(result.source_graveyard_id).zone,"graveyard")
        self.assertEqual(len(result.paid_source_ids),3)
        self.assertEqual(sum(self.k.get(i).tapped for i in islands),3)
        self.assertTrue(self.z.assert_consistent())
        self.assertEqual(len(self.k.objects),5)

    def test_mystical_shuffles_then_puts_selected_exact_id_on_top(self):
        self.islands(1)
        spell=self.add("Mystical Tutor","hand",{"instant"})
        candidate=self.add("Blue Instant","library",{"instant"})
        other=self.add("Red Sorcery","library",{"sorcery"})
        result=cast_and_resolve_reviewed_tutor(
            self.z,0,spell,self.metadata,{"U","R"},self.mana,target_id=candidate)
        self.assertEqual(result.target_destination,"library_top")
        self.assertEqual(result.target_old_id,result.target_new_id)
        self.assertEqual(self.z.ids(0,"library")[-1],candidate)
        self.assertIn(other,self.z.ids(0,"library"))
        self.assertTrue(self.z.assert_consistent())

    def test_unreviewed_tutor_name_or_target_does_not_pay(self):
        island=self.islands(1)[0]
        spell=self.add("Mystical Tutor","hand",{"instant"})
        illegal=self.add("Sol Ring","library",{"artifact"})
        with self.assertRaises(ValueError):
            cast_and_resolve_reviewed_tutor(
                self.z,0,spell,self.metadata,{"U","R"},self.mana,target_id=illegal)
        self.assertFalse(self.k.get(island).tapped)
        self.assertIn(spell,self.z.ids(0,"hand"))
        self.assertIn(illegal,self.z.ids(0,"library"))

    def test_insufficient_mana_keeps_spell_in_hand(self):
        self.islands(1)
        spell=self.add("Fabricate","hand",{"sorcery"})
        candidate=self.add("Sol Ring","library",{"artifact"})
        self.assertIsNone(cast_and_resolve_reviewed_tutor(
            self.z,0,spell,self.metadata,{"U","R"},self.mana,target_id=candidate))
        self.assertIn(spell,self.z.ids(0,"hand"))
        self.assertEqual(self.z.ids(0,"stack"),())

    def test_eligibility_is_live_and_restrictions_checked_before_payment(self):
        self.islands(3)
        spell=self.add("Fabricate","hand",{"sorcery"})
        rock=self.add("Sol Ring","library",{"artifact"})
        instant=self.add("Blue Instant","library",{"instant"})
        self.assertEqual(eligible_reviewed_tutor_targets(
            self.z,0,"Fabricate",self.metadata),(rock,))
        self.z.move(rock,"hand")
        self.assertEqual(eligible_reviewed_tutor_targets(
            self.z,0,"Fabricate",self.metadata),())
        self.assertIn(instant,self.z.ids(0,"library"))
        self.assertIn(spell,self.z.ids(0,"hand"))


if __name__=="__main__":
    unittest.main()
