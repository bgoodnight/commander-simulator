"""Reviewed cast-trigger effects on one actual indexed physical kernel."""
import unittest

from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.bounded_trigger_effects import (
    REVIEWED_CAST_TRIGGERS, resolve_reviewed_spell_triggers,
)


class BoundedCastTriggerTests(unittest.TestCase):
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K()
        self.z=Z(self.k,seed=29)
        self.C=C
        self.catalog={name:{"oracle_id":rows[0].card.oracle_id,
             "oracle_text":rows[0].card.oracle_text}
             for name,rows in REVIEWED_CAST_TRIGGERS.items()}

    def put(self,name,zone="battlefield",owner=0,identity=None):
        source=self.catalog[name]
        return self.z.add(self.C(identity or source["oracle_id"],name,
                       frozenset({"creature"}),coverage="approx"),
                          owner,zone)

    def cards_to_draw(self,count):
        return [self.z.add(self.C("test:"+str(i),"Draw "+str(i),
                            frozenset({"sorcery"}),coverage="approx"),0,
                            "library") for i in range(count)]

    def test_pyromancer_and_talrand_share_generic_token_emitter(self):
        pyro=self.put("Young Pyromancer")
        talrand=self.put("Talrand, Sky Summoner")
        result=resolve_reviewed_spell_triggers(
            self.z,0,self.catalog,spell_types=frozenset({"sorcery"}))
        self.assertEqual(len(result),2)
        self.assertEqual({x.source_id for x in result},{pyro,talrand})
        pyro_token=self.k.get(next(x.created_token_ids[0] for x in result
                                   if x.card_name=="Young Pyromancer"))
        drake=self.k.get(next(x.created_token_ids[0] for x in result
                              if x.card_name=="Talrand, Sky Summoner"))
        self.assertEqual(pyro_token.card.colors,frozenset({"R"}))
        self.assertEqual((drake.power,drake.toughness),(2,2))
        self.assertIn("flying",drake.keywords)
        self.assertTrue(self.z.assert_consistent())

    def test_archmage_draw_uses_actual_library_card(self):
        source=self.put("Archmage Emeritus")
        self.cards_to_draw(2)
        before=len(self.z.ids(0,"library"))
        outcomes=resolve_reviewed_spell_triggers(self.z,0,self.catalog)
        self.assertEqual(len(outcomes),1)
        self.assertEqual(outcomes[0].source_id,source)
        self.assertEqual(len(outcomes[0].drawn_ids),1)
        self.assertEqual(len(self.z.ids(0,"library")),before-1)
        self.assertEqual(len(self.z.ids(0,"hand")),1)
        self.assertTrue(self.z.assert_consistent())

    def test_kiln_magecraft_works_for_reviewed_cast_and_copy_event(self):
        self.put("Storm-Kiln Artist")
        spell=resolve_reviewed_spell_triggers(self.z,0,self.catalog,
            event="spell_cast",spell_types=frozenset({"instant"}))
        copied=resolve_reviewed_spell_triggers(self.z,0,self.catalog,
            event="spell_copied",spell_types=frozenset({"instant"}))
        self.assertEqual(len(spell),1)
        self.assertEqual(len(copied),1)
        self.assertEqual(len(self.z.ids(0,"battlefield")),3)
        self.assertTrue(all(self.k.get(x).card.name=="Treasure"
            for x in spell[0].created_token_ids+copied[0].created_token_ids))

    def test_bad_identity_or_modified_printed_text_never_executes(self):
        self.put("Young Pyromancer",identity="wrong-id")
        self.assertEqual(resolve_reviewed_spell_triggers(self.z,0,self.catalog),())
        self.catalog["Young Pyromancer"]["oracle_text"]="Unreviewed rules"
        self.assertEqual(resolve_reviewed_spell_triggers(self.z,0,self.catalog),())
        self.assertEqual(len(self.k.objects),1)

    def test_trigger_requires_spell_type_and_battlefield_source(self):
        self.put("Talrand, Sky Summoner","hand")
        self.assertEqual(resolve_reviewed_spell_triggers(self.z,0,self.catalog),())
        self.put("Young Pyromancer")
        self.assertEqual(resolve_reviewed_spell_triggers(
            self.z,0,self.catalog,spell_types=frozenset({"creature"})),())
        with self.assertRaises(ValueError):
            resolve_reviewed_spell_triggers(self.z,0,self.catalog,event="dies")

    def test_empty_draw_fails_closed_instead_of_claiming_success(self):
        self.put("Archmage Emeritus")
        with self.assertRaises(ValueError):
            resolve_reviewed_spell_triggers(self.z,0,self.catalog)
        self.assertEqual(self.z.ids(0,"hand"),())
        self.assertTrue(self.z.assert_consistent())


if __name__=="__main__":
    unittest.main()
