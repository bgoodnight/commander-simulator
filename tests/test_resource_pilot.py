"""Token-to-mana sequencing must use real reviewed source/target objects."""
import unittest
from types import SimpleNamespace
from commander_sim.resource_pilot import choose_token_mana_sacrifice


def make_object(oid,name,types=(),*,zone="battlefield",token=False,cmc="{1}"):
    return SimpleNamespace(object_id=oid,zone=zone,controller=0,owner=0,
                           token=token,tapped=False,types=frozenset(types),
                           power=1,card=SimpleNamespace(name=name,
                               supertypes=frozenset(),card_id=name))


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.altar=make_object(1,"Ashnod's Altar",("artifact",))
        self.token=make_object(2,"Zombie",("creature",),token=True)
        self.spell=make_object(3,"Reviewed Four Drop",("creature",),zone="hand")
        self.land_a=make_object(4,"Swamp",("land",))
        self.land_b=make_object(5,"Swamp",("land",))
        self.cards=[self.altar,self.token,self.spell,self.land_a,self.land_b]
        self.kernel=SimpleNamespace(
            on_battlefield=lambda: (x for x in self.cards if x.zone=="battlefield"),
            objects={x.object_id:x for x in self.cards},
            get=lambda oid:next(x for x in self.cards if x.object_id==oid))
        self.zones=SimpleNamespace(kernel=self.kernel,
            ids=lambda seat,zone:tuple(x.object_id for x in self.cards if x.zone==zone))
        mode=SimpleNamespace(output=("B",),activation_generic=0,
                             activation_colors=(),life=0,damage=0)
        self.mana=SimpleNamespace(kernel=self.kernel,
            modes=lambda x:(mode,) if "land" in x.types else (),
            floating=lambda seat:(0,0,0,0,0,0),
            plan_spell=lambda seat,cost,source:None)
        self.catalog={"Reviewed Four Drop":{"mana_cost":"{3}{B}"}}

    def test_only_expendable_token_for_plausibly_reachable_spell(self):
        self.assertEqual(choose_token_mana_sacrifice(
            self.zones,0,self.catalog,self.mana,
            supported_spell=lambda x:x.object_id==3), (1,2))

    def test_does_not_sacrifice_without_reviewed_payoff_or_token(self):
        self.assertIsNone(choose_token_mana_sacrifice(
            self.zones,0,self.catalog,self.mana,
            supported_spell=lambda x:False))
        self.token.zone="graveyard"
        self.assertIsNone(choose_token_mana_sacrifice(
            self.zones,0,self.catalog,self.mana,
            supported_spell=lambda x:x.object_id==3))


    def test_small_x_drain_is_not_rejected_by_arbitrary_pilot_floor(self):
        from unittest.mock import patch
        from commander_sim.resource_pilot import plan_common_spell
        from commander_sim.reviewed_common_spells import SpellRecipe, SpellStep
        spell=make_object(6,"Generic X Drain",("sorcery",),zone="hand")
        self.cards.append(spell)
        recipe=SpellRecipe("pinned-id","Drain X","{X}{B}{B}",
                           "sorcery",(SpellStep("opponent_drain_x"),),
                           variable_x=True)
        self.catalog[spell.card.name]={"mana_cost":"{X}{B}{B}"}
        self.mana.plan_spell=lambda seat,cost,source: object() if cost=="{1}{B}{B}" else None
        life=SimpleNamespace(total=lambda seat:3)
        with patch("commander_sim.resource_pilot.assess_resources",
                   return_value=SimpleNamespace(available_fixed_mana=3)):
            result=plan_common_spell(self.zones,0,spell,recipe,
                                     self.catalog,self.mana,life)
        self.assertEqual(result,("{1}{B}{B}",1,()))

    def test_life_consuming_spell_still_respects_safety_reserve(self):
        from commander_sim.resource_pilot import plan_common_spell
        from commander_sim.reviewed_common_spells import SpellRecipe, SpellStep
        spell=make_object(6,"Generic Life Draw",("sorcery",),zone="hand")
        self.cards.append(spell)
        recipe=SpellRecipe("pinned-id","Draw and lose","{B}",
                           "sorcery",(SpellStep("draw",1),
                                       SpellStep("lose_life",2)))
        self.mana.plan_spell=lambda seat,cost,source:object()
        life=SimpleNamespace(total=lambda seat:5)
        self.assertIsNone(plan_common_spell(self.zones,0,spell,recipe,
                                            self.catalog,self.mana,life))


if __name__ == "__main__":
    unittest.main()
