"""Five Oracle-pinned fixed token recipes on the original physical kernel."""
import unittest

from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.reviewed_token_spells import (
    TOKEN_SPELLS, reviewed_token_spell, cast_and_resolve_reviewed_token_spell,
)
from commander_sim.template_resources import TemplateManaService


class ReviewedTokenSpellsTests(unittest.TestCase):
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.k=K()
        self.z=Z(self.k,seed=42)
        self.C=C
        self.raw={name:dict(oracle_id=recipe.oracle_id,
            oracle_text=recipe.oracle_text,mana_cost=recipe.mana_cost,
            type_line="Sorcery",layout="normal") for name,recipe in TOKEN_SPELLS.items()}
        self.raw.update({
            "Swamp":{"type_line":"Basic Land — Swamp","mana_cost":"",
                     "oracle_text":"","layout":"normal"},
            "Island":{"type_line":"Basic Land — Island","mana_cost":"",
                      "oracle_text":"","layout":"normal"},
            "Mountain":{"type_line":"Basic Land — Mountain","mana_cost":"",
                        "oracle_text":"","layout":"normal"},
        })

    def card(self,name,zone,kind):
        identity=self.raw.get(name,{})
        return self.z.add(self.C(identity.get("oracle_id","test:"+name),
                                 name,frozenset({kind}),coverage="approx"),0,zone)

    def lands(self,kind,n):
        return [self.card(kind,"battlefield","land") for _ in range(n)]

    def run_spell(self,name,colors):
        oid=self.card(name,"hand","sorcery")
        service=TemplateManaService(self.k,self.raw,frozenset(colors))
        return cast_and_resolve_reviewed_token_spell(
            self.z,0,oid,self.raw,frozenset(colors),service)

    def test_ral_creates_two_real_elementals_after_source_paid_cast(self):
        self.lands("Mountain",1)
        self.lands("Island",1)
        out=self.run_spell("Ral's Reinforcements",{"U","R"})
        self.assertEqual(len(out.token_ids),2)
        self.assertEqual(len(out.paid_source_ids),2)
        self.assertTrue(all(self.k.get(x).card.name=="Elemental"
                            and self.k.get(x).token for x in out.token_ids))
        self.assertTrue(all(self.k.get(x).colors==frozenset({"U","R"})
                            for x in out.token_ids)) if hasattr(self.k.get(out.token_ids[0]),"colors") else None
        self.assertEqual(self.k.get(out.source_graveyard_id).zone,"graveyard")
        self.assertTrue(self.z.assert_consistent())

    def test_hard_evidence_composes_two_distinct_reviewed_batches(self):
        self.lands("Island",1)
        out=self.run_spell("Hard Evidence",{"U","R"})
        self.assertEqual([self.k.get(x).card.name for x in out.token_ids],
                         ["Crab","Clue"])
        self.assertEqual(self.k.get(out.token_ids[0]).toughness,3)
        self.assertIn("artifact",self.k.get(out.token_ids[1]).types)
        self.assertIn("Clue activated ability unavailable in bounded runner",
                      out.limitations)
        self.assertTrue(self.z.assert_consistent())

    def test_strike_it_rich_treasure_exists_without_invented_mana(self):
        self.lands("Mountain",1)
        out=self.run_spell("Strike It Rich",{"R"})
        self.assertEqual(len(out.token_ids),1)
        self.assertTrue(self.k.get(out.token_ids[0]).token)
        service=TemplateManaService(self.k,self.raw,frozenset({"R"}))
        self.assertEqual(service.modes(self.k.get(out.token_ids[0])),())
        self.assertIn("Flashback casting unavailable",out.limitations)

    def test_moan_of_unhallowed_creates_two_black_zombies(self):
        self.lands("Swamp",4)
        out=self.run_spell("Moan of the Unhallowed",{"B"})
        self.assertEqual(len(out.token_ids),2)
        self.assertEqual({self.k.get(x).card.colors for x in out.token_ids},
                         {frozenset({"B"})})
        self.assertTrue(all(self.k.get(x).card.base_power==2 for x in out.token_ids))

    def test_army_creates_exact_thirteen_tapped_zombies(self):
        self.lands("Swamp",8)
        out=self.run_spell("Army of the Damned",{"B"})
        self.assertEqual(len(out.token_ids),13)
        self.assertTrue(all(self.k.get(x).tapped for x in out.token_ids))
        self.assertTrue(all(self.k.get(x).card.colors==frozenset({"B"})
                            for x in out.token_ids))
        self.assertTrue(self.z.assert_consistent())

    def test_unreviewed_text_or_missing_cost_causes_no_action(self):
        self.lands("Mountain",1)
        bad=dict(self.raw["Strike It Rich"])
        bad["oracle_text"]="Create fifty Treasures."
        original=self.raw["Strike It Rich"]
        self.raw["Strike It Rich"]=bad
        self.assertIsNone(reviewed_token_spell("Strike It Rich",bad))
        source=self.card("Strike It Rich","hand","sorcery")
        service=TemplateManaService(self.k,self.raw,frozenset({"R"}))
        with self.assertRaises(ValueError):
            cast_and_resolve_reviewed_token_spell(
                self.z,0,source,self.raw,{"R"},service)
        self.assertIn(source,self.z.ids(0,"hand"))
        self.assertEqual(self.z.ids(0,"stack"),())
        self.raw["Strike It Rich"]=original

    def test_without_enough_mana_spell_remains_in_hand(self):
        self.lands("Swamp",1)
        source=self.card("Army of the Damned","hand","sorcery")
        service=TemplateManaService(self.k,self.raw,frozenset({"B"}))
        outcome=cast_and_resolve_reviewed_token_spell(
            self.z,0,source,self.raw,{"B"},service)
        self.assertIsNone(outcome)
        self.assertIn(source,self.z.ids(0,"hand"))
        self.assertEqual(self.z.ids(0,"battlefield").__len__(),1)


if __name__=="__main__":
    unittest.main()
