"""Source-reviewed spell templates use physical mana, life, cards and tokens."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_death_effects import ReviewedDeathEngine
from commander_sim.reviewed_common_spells import (
    reviewed_common_spell, cast_common_spell)
from commander_sim.reviewed_cast_reactions import resolve_cast_reactions

class ReviewedCommonSpellsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES if f.key=="mortarion_physical_final")
        cls.catalog={row["deck_name"]:row["card"]
                     for row in json.loads(f.snapshot_path.read_text())["cards"]}
    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=5)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.mana=TemplateManaService(self.kernel,self.catalog,
                                      frozenset({"B"}),zones=self.zones)
        self.death=ReviewedDeathEngine(self.zones,self.life,self.catalog)
    def add(self,name,zone="battlefield",types=None,seat=0):
        raw=self.catalog.get(name,{})
        if types is None:
            types=frozenset(raw.get("type_line","Creature").split(" — ",1)[0].lower().split()) & {
                "land","instant","sorcery","artifact","creature","enchantment"}
        return self.zones.add(self.C(raw.get("oracle_id","mock:"+name),name,
                 frozenset(types),coverage="approx"),seat,zone)
    def fill(self,count):
        for n in range(count):
            self.add("Draw"+str(n),zone="library",types=("instant",))
    def run_spell(self,name,**kwargs):
        oid=self.add(name,zone="hand")
        return cast_common_spell(self.zones,self.life,0,oid,self.catalog,
            frozenset({"B"}),self.mana,death_engine=self.death,**kwargs)
    def test_sign_in_blood_uses_real_draw_and_life_loss(self):
        self.add("Swamp",types=("land",))
        self.add("Swamp",types=("land",))
        self.fill(3)
        result=self.run_spell("Sign in Blood")
        self.assertEqual(len(result.drawn_ids),2)
        self.assertEqual(self.life.total(0),38)
        self.assertTrue(self.zones.assert_consistent())
    def test_exsanguinate_x_spends_actual_mana_and_gains_actual_life(self):
        for i in range(5):
            self.add("Swamp",types=("land",))
        result=self.run_spell("Exsanguinate",x=3)
        self.assertEqual([self.life.total(i) for i in range(4)],
                         [49,37,37,37])
        self.assertEqual(result.sacrificed_ids,())
        self.assertIsNone(self.mana.plan(0,"{B}"))
        self.assertTrue(self.zones.assert_consistent())
    def test_dispute_additional_sacrifice_draw_and_treasure(self):
        self.add("Swamp",types=("land",))
        self.add("Swamp",types=("land",))
        self.add("Pitiless Plunderer")
        sacrifice=self.add("Fodder",types=("creature",))
        self.fill(3)
        out=self.run_spell("Deadly Dispute",sacrifice_ids=(sacrifice,))
        self.assertEqual(len(out.drawn_ids),2)
        self.assertEqual(len(out.created_token_ids),1)
        tokens=[o for o in self.kernel.on_battlefield()
                if o.token and o.card.name=="Treasure"]
        self.assertEqual(len(tokens),2) # Plunderer + Dispute
        self.assertTrue(self.zones.assert_consistent())
    def test_additional_sacrifice_is_paid_before_cast_trigger(self):
        for _ in range(2):
            self.add("Swamp",types=("land",))
        sacrifice=self.add("Fodder",types=("creature",))
        self.fill(3)
        observed=[]
        def on_cast(ticket):
            # The payment cannot be preempted by triggered abilities that
            # react to a spell cast and change the same battlefield object.
            observed.append(sacrifice not in self.kernel.objects)
            self.assertIn(ticket.object_id,self.kernel.objects)
            # The actual cast is still recorded even after additional
            # sacrifice movement emitted intervening kernel events.
            reactions=resolve_cast_reactions(
                self.zones,0,self.catalog,
                source_spell=self.kernel.get(ticket.object_id))
            self.assertEqual(reactions,())
        result=self.run_spell(
            "Deadly Dispute",sacrifice_ids=(sacrifice,),on_cast=on_cast)
        self.assertEqual(observed,[True])
        self.assertIn(sacrifice,result.sacrificed_ids)
        self.assertEqual(len(result.drawn_ids),2)
        self.assertTrue(self.zones.assert_consistent())

    def test_one_treasure_cannot_pay_mana_and_additional_sacrifice_cost(self):
        from commander_sim.resource_pilot import plan_common_spell
        self.add("Swamp",types=("land",))
        treasure=self.zones.add(self.C(
            "reviewed-token:Treasure","Treasure",frozenset({"artifact"}),
            subtypes=frozenset({"Treasure"}),coverage="approx"),
            0,"battlefield",token=True)
        self.fill(4)
        source_id=self.add("Deadly Dispute",zone="hand")
        source=self.kernel.get(source_id)
        recipe=reviewed_common_spell("Deadly Dispute",self.catalog["Deadly Dispute"])
        # Without reserving the physical victim, Treasure would produce the
        # missing generic mana, then be incorrectly sacrificed a second time.
        self.assertIsNotNone(self.mana.plan_spell(0,"{1}{B}",source))
        self.assertIsNone(self.mana.plan_spell(
            0,"{1}{B}",source,excluded_source_ids=(treasure,)))
        self.assertIsNone(plan_common_spell(
            self.zones,0,source,recipe,self.catalog,self.mana,self.life))
        self.assertIsNone(cast_common_spell(
            self.zones,self.life,0,source_id,self.catalog,frozenset({"B"}),
            self.mana,sacrifice_ids=(treasure,),death_engine=self.death))
        self.assertIn(treasure,self.kernel.objects)
        self.assertIn(source_id,self.zones.ids(0,"hand"))
        self.assertTrue(self.zones.assert_consistent())
        # Adding a second land funds the spell independently of the victim.
        self.add("Swamp",types=("land",))
        self.assertIsNotNone(plan_common_spell(
            self.zones,0,source,recipe,self.catalog,self.mana,self.life))
        paid=cast_common_spell(
            self.zones,self.life,0,source_id,self.catalog,frozenset({"B"}),
            self.mana,sacrifice_ids=(treasure,),death_engine=self.death)
        self.assertIsNotNone(paid)
        self.assertNotIn(treasure,paid.paid_source_ids)
        self.assertEqual(paid.sacrificed_ids,(treasure,))
        self.assertEqual(len(paid.drawn_ids),2)
        self.assertTrue(self.zones.assert_consistent())

    def test_plumb_optional_sacrifice_repeats_draw_and_life(self):
        self.add("Swamp",types=("land",))
        self.add("Swamp",types=("land",))
        a=self.add("A",types=("creature",))
        b=self.add("B",types=("creature",))
        self.fill(5)
        out=self.run_spell("Plumb the Forbidden",sacrifice_ids=(a,b))
        self.assertEqual(len(out.drawn_ids),3)
        self.assertEqual(self.life.total(0),37)
        self.assertTrue(self.zones.assert_consistent())
    def test_unreviewed_spells_and_missing_sacrifice_fail_closed(self):
        self.assertIsNone(reviewed_common_spell("Sign in Blood",
                 dict(self.catalog["Sign in Blood"],oracle_text="Draw ten.")))
        self.add("Swamp",types=("land",))
        self.add("Swamp",types=("land",))
        with self.assertRaises(ValueError):
            self.run_spell("Deadly Dispute")
if __name__=="__main__":unittest.main()
