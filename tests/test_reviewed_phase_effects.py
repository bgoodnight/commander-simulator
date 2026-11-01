"""Shared upkeep/end-step effect contracts on real Commander kernel zones."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.reviewed_phase_effects import (
    PHASE_RULES, ReviewedPhaseEngine)


class ReviewedPhaseEffectsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog={}
        for fixture in FIXTURES:
            for row in json.loads(fixture.snapshot_path.read_text())["cards"]:
                cls.catalog.setdefault(row["deck_name"],row["card"])

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=17)
        self.Card=C
        self.life=KernelLife(self.kernel)
        self.engine=ReviewedPhaseEngine(self.zones,self.life,self.catalog)

    def card(self,name,types=("creature",),subtypes=(),controller=0,
             zone="battlefield",oracle=None,keywords=()):
        meta=self.catalog.get(name,{})
        return self.zones.add(self.Card(
            oracle or meta.get("oracle_id","test:"+name),name,
            frozenset(types),subtypes=frozenset(subtypes),
            keywords=frozenset(keywords),coverage="approx"),controller,zone)

    def draw_cards(self,n,seat=0):
        for i in range(n):
            self.card("Draw "+str(seat)+" "+str(i),types=("instant",),
                      controller=seat,zone="library")

    def phase(self,name="upkeep",seat=0,round_id=1,**kwargs):
        return self.engine.resolve(phase=name,active_seat=seat,
                                   round_id=round_id,**kwargs)

    def test_arena_draws_and_loses_life_once_per_upkeep(self):
        arena=self.card("Phyrexian Arena",types=("enchantment",))
        self.draw_cards(2)
        result=self.phase()
        self.assertEqual(len(result),1)
        self.assertEqual(result[0].source_id,arena)
        self.assertEqual(len(result[0].drawn_ids),1)
        self.assertEqual(self.life.total(0),39)
        self.assertEqual(self.phase(),())
        self.assertEqual(self.life.total(0),39)
        self.assertEqual(len(self.phase(round_id=2)),1)
        self.assertTrue(self.zones.assert_consistent())

    def test_graveborn_muse_counts_current_zombies_not_copies_of_text(self):
        self.card("Graveborn Muse",subtypes=("Zombie","Spirit"))
        self.card("Other Zombie",subtypes=("Zombie",))
        self.draw_cards(3)
        result=self.phase()
        self.assertEqual(len(result[0].drawn_ids),2)
        self.assertEqual(self.life.total(0),38)
        self.assertEqual(len(self.zones.ids(0,"hand")),2)

    def test_endless_ranks_creates_half_zombies_rounding_down(self):
        self.card("Endless Ranks of the Dead",types=("enchantment",))
        for i in range(5):
            self.card("Zombie "+str(i),subtypes=("Zombie",))
        result=self.phase()
        self.assertEqual(len(result),1)
        self.assertEqual(len(result[0].created_token_ids),2)
        self.assertTrue(all(self.kernel.get(x).token
             and self.kernel.get(x).card.name=="Zombie"
             for x in result[0].created_token_ids))

    def test_ophiomancer_responds_to_each_player_upkeep_unless_snake_exists(self):
        self.card("Ophiomancer")
        first=self.phase(seat=1)
        self.assertEqual(len(first[0].created_token_ids),1)
        snake=self.kernel.get(first[0].created_token_ids[0])
        self.assertIn("deathtouch",snake.keywords)
        second=self.phase(seat=2)
        self.assertEqual(second[0].created_token_ids,())
        self.assertEqual(len(self.phase(seat=1)),0)
        self.assertTrue(self.zones.assert_consistent())

    def test_jadar_creates_one_decayed_zombie_only_when_absent(self):
        self.card("Jadar, Ghoulcaller of Nephalia")
        first=self.phase("end_step")
        self.assertEqual(len(first[0].created_token_ids),1)
        zombie=self.kernel.get(first[0].created_token_ids[0])
        self.assertIn("decayed",zombie.keywords)
        second=self.phase("end_step",round_id=2)
        self.assertEqual(second[0].created_token_ids,())

    def test_great_unclean_one_drains_then_counts_lower_life_opponents(self):
        self.card("Great Unclean One")
        self.life.lose(1,5)
        result=self.phase("end_step")
        self.assertEqual([self.life.total(i) for i in range(4)],
                         [40,33,38,38])
        self.assertEqual(len(result[0].created_token_ids),3)
        self.assertTrue(all(self.kernel.get(x).card.name=="Plaguebearer of Nurgle"
                             for x in result[0].created_token_ids))

    def test_tallyman_one_or_seven_cards_based_on_death_count(self):
        self.card("Tallyman of Nurgle")
        self.draw_cards(10)
        self.assertEqual(len(self.phase("end_step",death_count=0)[0].drawn_ids),0)
        two=self.phase("end_step",death_count=1,round_id=2)[0]
        self.assertEqual(len(two.drawn_ids),1)
        seven=self.phase("end_step",death_count=7,round_id=3)[0]
        self.assertEqual(len(seven.drawn_ids),7)
        self.assertEqual(self.life.total(0),32)

    def test_cemetery_only_returns_owned_creature_with_four_in_graveyard(self):
        source=self.card("Oversold Cemetery",types=("enchantment",))
        creatures=[self.card("Grave "+str(i),zone="graveyard")
                   for i in range(4)]
        out=self.phase(choices={source:creatures[2]})
        self.assertEqual(len(out),1)
        returned=out[0].returned_id
        self.assertIsNotNone(returned)
        self.assertEqual(self.kernel.get(returned).zone,"hand")
        self.assertTrue(self.zones.assert_consistent())

    def test_changed_oracle_identity_has_no_execution_rights(self):
        self.card("Phyrexian Arena",types=("enchantment",),oracle="unreviewed")
        self.draw_cards(2)
        self.assertEqual(self.phase(),())
        self.assertEqual(self.life.total(0),40)
        self.assertEqual(len(PHASE_RULES),8)

    def test_empty_library_mandatory_draw_prevents_partial_life_change(self):
        self.card("Phyrexian Arena",types=("enchantment",))
        with self.assertRaises(NotImplementedError):
            self.phase()
        self.assertEqual(self.life.total(0),40)
        self.assertFalse(self.engine.invocations)


if __name__=="__main__":
    unittest.main()
