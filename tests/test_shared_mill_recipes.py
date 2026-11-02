"""Reusable mill library actions, physical ETBs and exact import grammar."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.library_actions import LibraryAction, resolve_library_actions
from commander_sim.provisional_actions import cast_provisional_spell
from commander_sim.provisional_import import provisional_profile, provisional_report
from commander_sim.reviewed_enter_effects import reviewed_enter_rule, execute_reviewed_enter
from commander_sim.template_resources import TemplateManaService


def make_raw(name,text,*,card_type="Creature — Zombie",mana="{1}{B}"):
    return dict(name=name,oracle_id="beeeeeef-1234-4123-8123-1234567890ab",
                oracle_text=text,type_line=card_type,mana_cost=mana,
                layout="normal")


class SharedMillRecipesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cards={}
        for fixture in FIXTURES:
            cls.cards.update({row["deck_name"]:row["card"]
                   for row in json.loads(fixture.snapshot_path.read_text())["cards"]})

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K()
        self.z=Z(self.k,seed=23)
        self.C=C
        self.life=KernelLife(self.k)

    def add(self,name,zone,*,types=("creature",),identity=None,owner=0):
        return self.z.add(self.C(identity or "test:"+name,name,
                           frozenset(types),coverage="approx"),owner,zone)

    def tested_entry(self,name,*,library_count=5):
        row=self.cards[name]
        source=self.add(name,"hand",identity=row["oracle_id"])
        created=self.z.move(source,"battlefield","resolve")
        originals=[self.add("Library"+str(i),"library") for i in range(library_count)]
        outcome=execute_reviewed_enter(self.z,self.life,created,self.cards)
        return outcome,originals,created

    def test_mill_count_uses_physical_library_ids(self):
        originals=[self.add("Card"+str(i),"library") for i in range(4)]
        out=resolve_library_actions(self.z,0,(LibraryAction("mill",3),))
        self.assertEqual(len(out.milled_ids),3)
        self.assertEqual(out.steps[0]["kind"],"mill")
        self.assertEqual([x["card"] for x in out.steps[0]["milled"]],
                         ["Card3","Card2","Card1"])
        self.assertNotIn(originals[-1],self.k.objects)
        self.assertEqual(len(self.z.ids(0,"graveyard")),3)
        self.assertTrue(self.z.assert_consistent())

    def test_mill_is_legal_with_fewer_cards_than_requested(self):
        one=self.add("Only","library")
        out=resolve_library_actions(self.z,0,(LibraryAction("mill",7),))
        self.assertEqual(len(out.milled_ids),1)
        self.assertFalse(self.z.ids(0,"library"))
        self.assertTrue(self.z.assert_consistent())

    def test_combined_mill_draw_fails_before_zone_mutation(self):
        one=self.add("A","library")
        two=self.add("B","library")
        with self.assertRaises(ValueError):
            resolve_library_actions(self.z,0,(
                LibraryAction("mill",2),LibraryAction("draw",1)))
        self.assertEqual(self.z.ids(0,"library"),(one,two))
        self.assertFalse(self.z.ids(0,"graveyard"))

    def test_flayed_one_mills_three_as_shared_entry_recipe(self):
        out,originals,source=self.tested_entry("Flayed One")
        self.assertEqual(out.operation,"library_recipe")
        self.assertEqual(len(out.milled_ids),3)
        self.assertEqual(out.library_steps[0]["count"],3)
        self.assertEqual(len(self.z.ids(0,"library")),2)
        self.assertIn(source,self.z.ids(0,"battlefield"))
        self.assertTrue(self.z.assert_consistent())

    def test_mire_triton_mills_two_and_gains_two_life(self):
        out,originals,source=self.tested_entry("Mire Triton")
        self.assertEqual(len(out.milled_ids),2)
        self.assertEqual(self.life.total(0),42)
        self.assertEqual(len(self.z.ids(0,"library")),3)
        self.assertTrue(self.z.assert_consistent())

    def test_undead_butler_mills_three_without_inventing_death_target(self):
        out,_,source=self.tested_entry("Undead Butler")
        self.assertEqual(len(out.milled_ids),3)
        self.assertEqual(len(out.library_steps),1)
        self.assertEqual(out.token_ids,())
        self.assertTrue(self.z.assert_consistent())

    def test_reviewed_entry_requires_exact_pinned_card_identity(self):
        for name in ("Flayed One","Mire Triton","Undead Butler"):
            row=self.cards[name]
            self.assertIsNotNone(reviewed_enter_rule(name,row))
            altered=dict(row,oracle_id="00000000-1111-4111-8111-222222222222")
            self.assertIsNone(reviewed_enter_rule(name,altered))

    def test_generic_import_mill_entry_recognizes_only_simple_complete_line(self):
        raw=make_raw("New Miller","Flying\nWhen this creature enters, mill three cards.")
        profile=provisional_profile(raw)
        self.assertEqual(profile.kind,"creature_body")
        self.assertEqual(profile.entry_actions,(LibraryAction("mill",3),))
        report=provisional_report([{"deck_name":raw["name"],"card":raw}])
        self.assertEqual(report[0]["entry_actions"],[{"kind":"mill","count":3}])
        for text in (
            "When this creature enters, mill three cards, then win the game.",
            "When this creature enters, mill three cards. "
            "Return a creature card to the battlefield.",
            "When this creature enters, mill three cards.\n"
            "When this creature enters, draw a card.",
        ):
            with self.subTest(text=text):
                self.assertIsNone(provisional_profile(make_raw("Bad Miller",text)))

    def test_generic_import_mill_spell_executes_actual_cards(self):
        raw=make_raw("Simple Self Mill","Mill two cards.",
                     card_type="Sorcery",mana="{B}")
        p=provisional_profile(raw)
        self.assertEqual(p.kind,"simple_spell")
        self.assertEqual(p.library_actions,(LibraryAction("mill",2),))
        source=self.add(raw["name"],"hand",types=("sorcery",),
                        identity=raw["oracle_id"])
        self.add("Swamp","battlefield",types=("land",))
        self.add("X","library")
        self.add("Y","library")
        self.add("Z","library")
        catalog={raw["name"]:raw}
        mana=TemplateManaService(self.k,catalog,frozenset("B"),zones=self.z,
                                 provisional_mode="safe")
        result=cast_provisional_spell(self.z,self.life,0,source,catalog,
                                      frozenset("B"),mana)
        self.assertEqual(result.operation,"library_sequence")
        self.assertEqual(len(result.surveilled_ids),2)
        self.assertEqual(result.library_steps[0]["kind"],"mill")
        self.assertTrue(self.z.assert_consistent())

    def test_unsafe_mill_spell_text_never_gains_provisional_resolution(self):
        for text in ("Mill eight cards.","Target player mills three cards.",
                     "Mill three cards. Exile target creature.",
                     "Mill three cards, then draw a card."):
            with self.subTest(text=text):
                raw=make_raw("Unsafe Mill",text,card_type="Sorcery",mana="{B}")
                self.assertIsNone(provisional_profile(raw))


if __name__=="__main__":
    unittest.main()
