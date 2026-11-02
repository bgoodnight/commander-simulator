"""Generic source-pinned import fallback: no card-name admission and no fake effects."""
import copy
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel, run_bounded_early_game
from commander_sim.kernel_life import KernelLife
from commander_sim.provisional_actions import cast_provisional_spell
from commander_sim.provisional_import import provisional_profile,provisional_report
from commander_sim.template_resources import TemplateManaService


def card(name="New Card", *, mana="{2}{B}", types="Creature",
         text="Flying", layout="normal"):
    return {
        "name":name,"oracle_id":"pinned:"+name,"oracle_text":text,
        "type_line":types,"mana_cost":mana,"layout":layout,
        "keywords":["Flying"] if "Flying" in text else []}


class ProvisionalImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshots={}
        for fixture in FIXTURES:
            cls.snapshots[fixture.key]={
                item["deck_name"]:item["card"]
                for item in json.loads(fixture.snapshot_path.read_text())["cards"]}

    def test_keyword_body_and_pending_death_ability_stay_partial(self):
        raw=card(text="Flying\nWhenever this creature dies, draw a card.")
        result=provisional_profile(raw)
        self.assertEqual(result.kind,"creature_body")
        self.assertEqual(result.fidelity,"provisional_partial")
        self.assertTrue(result.omissions)

    def test_mandatory_enter_effect_never_disappears(self):
        self.assertIsNone(provisional_profile(
            card(text="When this creature enters, draw a card.")))
        self.assertIsNone(provisional_profile(
            card(text="As this creature enters, choose a color.")))

    def test_conditional_casting_and_complex_mana_fail_closed(self):
        self.assertIsNone(provisional_profile(card(
            text="As an additional cost to cast this spell, sacrifice a creature.\nFlying")))
        self.assertIsNone(provisional_profile(card(mana="{X}{B}")))
        self.assertIsNone(provisional_profile(card(layout="transform")))

    def test_multi_effect_spell_does_not_gain_free_draw(self):
        raw=card(types="Sorcery",text="Draw two cards. You win the game.")
        self.assertIsNone(provisional_profile(raw))

    def test_source_pinned_real_deck_simple_draw_life(self):
        for name,count in (("Night's Whisper",2),("Ambition's Cost",3)):
            raw=self.snapshots["wretched_ranks"][name]
            result=provisional_profile(raw)
            self.assertEqual(result.kind,"simple_spell",name)
            self.assertEqual(result.mode,"draw_lose")
            self.assertEqual(result.amount,count)
            self.assertEqual(result.life_amount,count)

    def test_convoke_is_not_silently_paid_as_regular_spell(self):
        raw=self.snapshots["magnus_premium"]["Meeting of Minds"]
        self.assertIsNone(provisional_profile(raw))

    def test_lands_and_artifacts_use_same_typed_mana_modes(self):
        land=card(name="New Land",types="Land",mana="",
                  text="This land enters tapped.\n{T}: Add {G}.")
        artifact=card(name="New Mana Rock",types="Artifact",mana="{2}",
                      text="This artifact enters tapped.\n{T}: Add {C}{C}.")
        first=provisional_profile(land)
        second=provisional_profile(artifact)
        self.assertEqual((first.kind,first.mana_modes[0].output,
                          first.enter_tapped),("land_mana",("G",),True))
        self.assertEqual((second.kind,second.mana_modes[0].output,
                          second.enter_tapped),("artifact_mana",("C","C"),True))

    def test_conditional_mana_must_not_produce_unrestricted_modes(self):
        restricted=card(name="Conditional",types="Artifact",
             mana="{2}",text="{T}: Add {B}. Spend this mana only to cast Zombie spells.")
        p=provisional_profile(restricted)
        self.assertTrue(p is None or p.kind!="artifact_mana")
        restricted2=card(name="Conditional2",types="Land",mana="",
                         text="{T}: Add {B} only if you control a Zombie.")
        p2=provisional_profile(restricted2)
        self.assertTrue(p2 is None or p2.kind!="land_mana")

    def test_import_report_marks_unrecognized_source_as_unimplemented(self):
        rows=[{"deck_name":"Simple","card":card(name="Simple")},
              {"deck_name":"Complex","card":card(name="Complex",
                text="When this creature enters, destroy target land.")}]
        results=provisional_report(rows)
        self.assertEqual([x["status"] for x in results],
                         ["provisional","manual_review_needed"])
        self.assertEqual(results[0]["fidelity"],"provisional_partial")

    def test_mana_service_uses_opt_in_identity_pinned_rock(self):
        K,Z,C=_load_live_kernel()
        k=K()
        z=Z(k,seed=15)
        rock=card(name="Unreviewed Simple Rock",types="Artifact",
                  mana="{2}",text="{T}: Add {C}{C}.")
        metadata={rock["name"]:rock}
        oid=z.add(C(rock["oracle_id"],rock["name"],frozenset({"artifact"}),
                    coverage="approx"),0,"battlefield")
        off=TemplateManaService(k,metadata,frozenset({"B"}),zones=z)
        safe=TemplateManaService(k,metadata,frozenset({"B"}),zones=z,
                                 provisional_mode="safe")
        self.assertEqual(off.modes(k.get(oid)),())
        self.assertEqual(safe.modes(k.get(oid))[0].output,("C","C"))
        k.get(oid).card=C("wrong-id",rock["name"],frozenset({"artifact"}),
                          coverage="approx")
        self.assertEqual(safe.modes(k.get(oid)),())

    def test_simple_life_draw_spell_physically_pays_and_resolves(self):
        K,Z,C=_load_live_kernel()
        k=K()
        z=Z(k,seed=20)
        life=KernelLife(k)
        source=card(name="Example Night Whisper",types="Sorcery",mana="{1}{B}",
                    text="You draw two cards and lose 2 life.")
        catalog={source["name"]:source}
        source_id=z.add(C(source["oracle_id"],source["name"],
                          frozenset({"sorcery"}),coverage="approx"),0,"hand")
        for i in range(2):
            z.add(C("test:swamp:"+str(i),"Swamp",frozenset({"land"}),
                    coverage="approx"),0,"battlefield")
        for i in range(3):
            z.add(C("test:library:"+str(i),"Filler"+str(i),
                    frozenset({"creature"}),coverage="unimplemented"),0,"library")
        mana=TemplateManaService(k,catalog,frozenset({"B"}),zones=z,
                                 provisional_mode="safe")
        outcome=cast_provisional_spell(
            z,life,0,source_id,catalog,frozenset({"B"}),mana)
        self.assertIsNotNone(outcome)
        self.assertEqual(outcome.operation,"draw_lose")
        self.assertEqual(len(outcome.drawn_ids),2)
        self.assertEqual(life.total(0),38)
        self.assertNotIn(source_id,k.objects)
        self.assertEqual(len(z.ids(0,"graveyard")),1)
        self.assertTrue(z.assert_consistent())

    def test_cast_rejects_source_identity_change(self):
        K,Z,C=_load_live_kernel()
        k=K()
        z=Z(k,seed=20)
        life=KernelLife(k)
        raw=card(name="Safe Draw",types="Sorcery",mana="{B}",text="Draw a card.")
        oid=z.add(C("imposter",raw["name"],frozenset({"sorcery"}),
                    coverage="approx"),0,"hand")
        mana=TemplateManaService(k,{raw["name"]:raw},
             frozenset({"B"}),zones=z,provisional_mode="safe")
        with self.assertRaises(ValueError):
            cast_provisional_spell(z,life,0,oid,{raw["name"]:raw},
                                   frozenset({"B"}),mana)

    def test_four_commander_deck_families_import_report_without_side_effect(self):
        for name in ("magnus_premium","wretched_ranks",
                     "mortarion_current","necron_dynasties"):
            catalog=self.snapshots[name]
            report=provisional_report(
                [{"deck_name":card_name,"card":raw}
                 for card_name,raw in catalog.items()])
            self.assertEqual(len(report),len(catalog))
            self.assertTrue(any(x["status"]=="provisional" for x in report),name)
            self.assertTrue(any(x["status"]=="manual_review_needed" for x in report),name)

    def test_runner_opt_in_does_not_rewrite_existing_baseline(self):
        off=run_bounded_early_game("wretched_ranks",seed=2,turns=3)
        on=run_bounded_early_game("wretched_ranks",seed=2,turns=3,
                                  provisional_mode="safe")
        self.assertEqual(off["provisional_import_report"],[])
        self.assertEqual(on["provisional_mode"],"safe")
        self.assertGreater(len(on["provisional_import_report"]),20)
        self.assertTrue(any(x["card"]=="Night's Whisper" and
             x["kind"]=="simple_spell"
             for x in on["provisional_import_report"]))
        self.assertEqual(off["deck_sha256"],on["deck_sha256"])
        self.assertEqual(off["mulligan"]["opening_hand"],
                         on["mulligan"]["opening_hand"])

if __name__=="__main__":
    unittest.main()
