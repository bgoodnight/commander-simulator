"""End-to-end tests of declarative abilities on the real physical kernel."""
import json
import unittest

from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_death_effects import ReviewedDeathEngine
from commander_sim.composed_abilities import ComposedAbilityEngine


class ComposedAbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture=next(f for f in EXPERIMENTAL_FIXTURES
                     if f.key=="mortarion_physical_final")
        cls.catalog={row["deck_name"]:row["card"] for row
                     in json.loads(fixture.snapshot_path.read_text())["cards"]}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=7)
        self.Card=C
        self.life=KernelLife(self.kernel)
        self.mana=TemplateManaService(self.kernel,self.catalog,
                                      frozenset({"B"}),zones=self.zones)
        self.death=ReviewedDeathEngine(self.zones,self.life,self.catalog)
        self.composed=ComposedAbilityEngine(
            self.zones,self.life,self.catalog,self.mana,self.death)

    def add(self,name,types=("creature",),subtypes=(),toughness=2,seat=0,
            oracle=None,zone="battlefield"):
        raw=self.catalog.get(name,{})
        return self.zones.add(self.Card(
            oracle or raw.get("oracle_id","test:"+name),name,
            frozenset(types),subtypes=frozenset(subtypes),
            base_power=2,base_toughness=toughness,
            coverage="approx"),seat,zone)

    def swamps(self,n):
        return [self.add("Swamp",types=("land",)) for _ in range(n)]

    def test_mortarion_end_step_x_payment_uses_actual_life_loss(self):
        commander=self.add("Mortarion, Daemon Primarch",toughness=7)
        self.swamps(3)
        start=len(self.kernel.life_changes)
        self.life.lose(0,3)
        self.life.gain(0,2)
        result=self.composed.end_step(
            active_seat=0,turn=1,life_start_index=start,
            x_choices={commander:2})
        self.assertEqual(len(result),1)
        self.assertEqual(len(result[0].created_ids),2)
        self.assertTrue(all(
            "menace" in self.kernel.get(oid).keywords
            for oid in result[0].created_ids))
        self.assertEqual(self.life.total(0),39)
        self.assertEqual(self.composed.end_step(
            active_seat=0,turn=1,life_start_index=start,
            x_choices={commander:2}),())
        self.assertTrue(self.zones.assert_consistent())

    def test_mortarion_refuses_more_x_than_life_lost(self):
        commander=self.add("Mortarion, Daemon Primarch",toughness=7)
        self.swamps(4)
        start=len(self.kernel.life_changes)
        self.life.lose(0,1)
        with self.assertRaises(ValueError):
            self.composed.end_step(active_seat=0,turn=1,
                life_start_index=start,x_choices={commander:2})

    def test_pestilence_damage_death_and_plunderer_treasure(self):
        source=self.add("Pestilence",types=("enchantment",))
        self.add("Pitiless Plunderer",toughness=3)
        self.add("Disposable",toughness=1)
        self.swamps(2)
        result=self.composed.activate(source,turn=1)
        self.assertIsNotNone(result)
        self.assertEqual([self.life.total(i) for i in range(4)],[39]*4)
        self.assertEqual(result.deaths>=1,True)
        treasures=[o for o in self.kernel.on_battlefield()
                   if o.token and o.card.name=="Treasure"]
        self.assertEqual(len(treasures),1)
        self.assertEqual(len(self.mana.modes(treasures[0])),5)
        self.assertTrue(self.zones.assert_consistent())

    def test_pestilence_cleanup_and_repeatable_wumpus_activation(self):
        pest=self.add("Pestilence",types=("enchantment",))
        self.swamps(2)
        result=self.composed.end_step(active_seat=0,turn=1,
                                      life_start_index=0)
        self.assertEqual(len(result),1)
        self.assertTrue(any(
            self.kernel.get(oid).card.name=="Pestilence"
            for oid in self.zones.ids(0,"graveyard")))
        beast=self.add("Thrashing Wumpus",toughness=3)
        self.mana.clear()
        self.assertIsNotNone(self.composed.activate(beast,turn=2))
        self.mana.clear()
        self.assertIsNotNone(self.composed.activate(beast,turn=2))
        self.assertEqual(self.life.total(0),38)

    def test_cross_card_damage_tokens_altar_plunderer_chain(self):
        from commander_sim.reviewed_sacrifice_actions import activate_reviewed_sacrifice
        mortarion=self.add("Mortarion, Daemon Primarch",toughness=7)
        pest=self.add("Pestilence",types=("enchantment",))
        altar=self.add("Ashnod's Altar",types=("artifact",))
        self.add("Pitiless Plunderer",toughness=4)
        self.add("Fodder",toughness=1)
        self.swamps(4)
        start=len(self.kernel.life_changes)
        activated=self.composed.activate(pest,turn=1)
        self.assertEqual(activated.deaths,1)
        first_treasures=[o for o in self.kernel.on_battlefield()
                         if o.card.name=="Treasure"]
        self.assertEqual(len(first_treasures),1)
        phase=self.composed.end_step(active_seat=0,turn=1,
                                    life_start_index=start,
                                    x_choices={mortarion:1})
        astartes=phase[0].created_ids[0]
        self.assertEqual(self.kernel.get(astartes).card.name,"Astartes Warrior")
        sacrificed=activate_reviewed_sacrifice(
            self.zones,self.life,altar,astartes,self.catalog,
            mana_service=self.mana,turn=1,death_engine=self.death)
        self.assertEqual(sacrificed.mana_added,("C","C"))
        self.assertEqual(sacrificed.death_trigger_count,1)
        treasures=[o for o in self.kernel.on_battlefield()
                   if o.card.name=="Treasure"]
        self.assertEqual(len(treasures),2)
        self.assertEqual(self.mana.floating()[5],2)
        self.assertTrue(self.zones.assert_consistent())

    def test_unreviewed_source_identity_fails_closed(self):
        fake=self.add("Pestilence",types=("enchantment",),
                      oracle="not-reviewed")
        self.swamps(1)
        with self.assertRaises(ValueError):
            self.composed.activate(fake,turn=1)


if __name__=="__main__":
    unittest.main()
