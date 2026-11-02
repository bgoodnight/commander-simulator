"""Generic optional sacrifice choices from physical reviewed action evidence."""
import unittest
from types import SimpleNamespace

from commander_sim.pilot_tactics import choose_discretionary_sacrifice
from commander_sim.reviewed_sacrifice_actions import SACRIFICE_MODES
from commander_sim.reviewed_death_effects import DEATH_RULES


def permanent(oid,name,oracle_id,*,token=False,power=1,types=("creature",)):
    return SimpleNamespace(
        object_id=oid,owner=0,controller=0,zone="battlefield",
        tapped=False,token=token,types=frozenset(types),
        subtypes=frozenset(),keywords=frozenset(),power=power,
        card=SimpleNamespace(name=name,card_id=oracle_id,
                             supertypes=frozenset(),colors=frozenset({"B"})))


class TacticalSacrificeTests(unittest.TestCase):
    def setUp(self):
        mode=SACRIFICE_MODES["Viscera Seer"]
        self.outlet=permanent(1,"Viscera Seer",mode.oracle_id)
        self.token=permanent(2,"Expendable creature","test:token",token=True)
        self.cards=[self.outlet,self.token]
        self.catalog={"Viscera Seer":{
            "oracle_id":mode.oracle_id,"oracle_text":mode.excerpt}}
        self.kernel=SimpleNamespace(
            on_battlefield=lambda: tuple(o for o in self.cards
                                        if o.zone=="battlefield"))
        self.zones=SimpleNamespace(
            kernel=self.kernel,
            ids=lambda seat,zone:tuple(range(10))
                if zone=="library" else tuple(range(3))
                if zone=="hand" else ())
        self.life=SimpleNamespace(
            kernel=self.kernel,total=lambda seat:40)
        self.mana=SimpleNamespace(kernel=self.kernel)
        self.death=SimpleNamespace(zones=self.zones,_once=set())

    def add_trigger(self,name,oid):
        rule=DEATH_RULES[name][0]
        self.cards.append(permanent(oid,name,rule.oracle_id))
        self.catalog[name]={"oracle_id":rule.oracle_id,
                            "oracle_text":rule.excerpt}
        return rule

    def choose(self):
        return choose_discretionary_sacrifice(
            self.zones,0,self.life,self.mana,self.catalog,self.death,
            turn=4,entered_on_turn={},archetype="aristocrats")

    def test_scry_outlet_does_not_automatically_sacrifice_a_creature(self):
        self.assertIsNone(self.choose())

    def test_real_death_payoffs_enable_profitable_token_sacrifice(self):
        self.add_trigger("Blood Artist",3)
        self.add_trigger("Bastion of Remembrance",4)
        choice=self.choose()
        self.assertIsNotNone(choice)
        self.assertEqual((choice.source_id,choice.victim_id),(1,2))
        self.assertEqual(choice.trigger_count,2)
        self.assertGreaterEqual(choice.score,2)
        self.assertTrue(any(x.startswith("reviewed_death_triggers:")
                            for x in choice.factors))

    def test_once_per_turn_ability_no_longer_counted_after_firing(self):
        self.add_trigger("Blood Artist",3)
        once=self.add_trigger("Morbid Opportunist",4)
        self.assertIsNotNone(self.choose())
        self.death._once.add((4,4,once.slot_id))
        self.assertIsNone(self.choose())

    def test_no_named_card_evaluation_or_unverified_trigger_permission(self):
        self.add_trigger("Blood Artist",3)
        self.add_trigger("Bastion of Remembrance",4)
        self.catalog["Bastion of Remembrance"]["oracle_text"]="Not reviewed"
        # A single other trigger is insufficient to spend this token.
        self.assertIsNone(self.choose())

    def test_non_token_large_body_is_not_spent_for_one_scry(self):
        self.token.token=False
        self.token.power=5
        self.assertIsNone(self.choose())


if __name__=="__main__":
    unittest.main()
