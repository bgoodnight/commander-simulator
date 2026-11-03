"""Combat damage-to-player recipes preserve physical cards and token rules."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.reviewed_combat_damage import (
    reviewed_combat_damage, resolve_combat_damage_player)


class CombatDamageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = {}
        for fixture in FIXTURES:
            for row in json.loads(fixture.snapshot_path.read_text())["cards"]:
                cls.catalog.setdefault(row["deck_name"], row["card"])

    def setUp(self):
        K, Z, C = _load_live_kernel()
        self.k = K()
        self.z = Z(self.k, seed=18)
        self.C = C

    def add(self, name, *, types=("creature",), owner=0,
            zone="battlefield", verified=True):
        raw = self.catalog.get(name, {})
        oid = raw.get("oracle_id", "test:" + name) if verified else "unknown:" + name
        return self.z.add(self.C(
            oid, name, frozenset(types), base_power=4, base_toughness=4,
            coverage="approx"), owner, zone)

    def hit(self, source, victim=1, amount=3, **kwargs):
        return resolve_combat_damage_player(
            self.z, self.catalog, source, victim, amount, **kwargs)

    def test_magnus_creates_red_spawn_on_player_hit(self):
        magnus = self.add("Magnus the Red")
        out = self.hit(magnus)
        self.assertEqual(len(out.token_ids), 1)
        spawn = self.k.get(out.token_ids[0])
        self.assertEqual(spawn.card.name, "Spawn")
        self.assertEqual((spawn.power, spawn.toughness), (3, 3))
        self.assertEqual(spawn.controller, 0)
        self.assertEqual(spawn.card.colors, frozenset({"R"}))
        self.assertTrue(self.z.assert_consistent())

    def test_reaver_discard_then_create_tapped_zombie(self):
        reaver = self.add("Liliana's Reaver")
        hand = self.add("Card in victim hand", owner=2, zone="hand")
        out = self.hit(reaver, 2)
        self.assertEqual(len(out.discarded_ids), 1)
        self.assertEqual(self.k.get(out.discarded_ids[0]).card.name,
                         "Card in victim hand")
        self.assertEqual(self.k.get(out.discarded_ids[0]).zone, "graveyard")
        self.assertNotIn(hand, self.k.objects)
        zombie = self.k.get(out.token_ids[0])
        self.assertTrue(zombie.tapped)
        self.assertEqual((zombie.power, zombie.toughness), (2, 2))
        self.assertEqual(zombie.controller, 0)
        self.assertTrue(self.z.assert_consistent())

    def test_empty_hand_still_creates_reaver_zombie(self):
        reaver = self.add("Liliana's Reaver")
        out = self.hit(reaver, 1)
        self.assertEqual(out.discarded_ids, ())
        self.assertEqual(len(out.token_ids), 1)

    def test_invalid_discard_choice_is_nonmutating(self):
        reaver = self.add("Liliana's Reaver")
        card = self.add("Victim hand", owner=1, zone="hand")
        with self.assertRaises(ValueError):
            self.hit(reaver, 1, choose_discard=lambda seat, ids: -1)
        self.assertIn(card, self.z.ids(1, "hand"))
        self.assertEqual(len(tuple(o for o in self.k.on_battlefield()
                                   if o.token)), 0)

    def test_no_trigger_for_zero_damage_or_self_hit_or_invalid_source(self):
        reaver = self.add("Liliana's Reaver")
        self.assertIsNone(self.hit(reaver, amount=0))
        self.assertIsNone(self.hit(reaver, victim=0))
        fake = self.add("Magnus the Red", verified=False)
        self.assertIsNone(self.hit(fake))
        self.assertFalse(any(o.token for o in self.k.on_battlefield()))

    def test_tomb_blade_sacrifices_one_opponent_creature(self):
        from commander_sim.kernel_life import KernelLife
        from commander_sim.reviewed_death_effects import ReviewedDeathEngine
        blade = self.add("Tomb Blade")
        a = self.add("Opposing creature A", owner=1)
        b = self.add("Opposing creature B", owner=1)
        life = KernelLife(self.k)
        deaths = ReviewedDeathEngine(self.z, life, self.catalog)
        out = self.hit(blade, life=life, death_engine=deaths)
        self.assertEqual(out.sacrificed_ids, (a,))
        self.assertNotIn(a, self.k.objects)
        self.assertIn(b, self.k.objects)
        self.assertEqual(out.life_lost, 0)
        self.assertTrue(self.z.assert_consistent())

    def test_tomb_blade_player_can_choose_life_loss_instead(self):
        from commander_sim.kernel_life import KernelLife
        blade = self.add("Tomb Blade")
        self.add("Opposing creature A", owner=1)
        self.add("Opposing creature B", owner=1)
        life = KernelLife(self.k)
        out = self.hit(blade, life=life,
                       choose_sacrifice=lambda seat, options: None)
        self.assertEqual(out.sacrificed_ids, ())
        self.assertEqual(out.life_lost, 2)
        self.assertEqual(life.total(1), 38)
        self.assertTrue(self.z.assert_consistent())

    def test_tomb_blade_invalid_choice_does_not_mutate_board(self):
        from commander_sim.kernel_life import KernelLife
        blade = self.add("Tomb Blade")
        creature = self.add("Opposing creature", owner=1)
        life = KernelLife(self.k)
        with self.assertRaises(ValueError):
            self.hit(blade, life=life,
                     choose_sacrifice=lambda seat, options: blade)
        self.assertIn(creature, self.k.objects)
        self.assertEqual(life.total(1), 40)

    def test_tomb_blade_no_creatures_means_no_life_loss(self):
        from commander_sim.kernel_life import KernelLife
        blade = self.add("Tomb Blade")
        life = KernelLife(self.k)
        out = self.hit(blade, life=life)
        self.assertEqual(out.sacrificed_ids, ())
        self.assertEqual(out.life_lost, 0)
        self.assertEqual(life.total(1), 40)

    def test_changed_oracle_revision_disables_reviewed_recipe(self):
        raw = dict(self.catalog["Magnus the Red"])
        raw["oracle_text"] = "unreviewed new text"
        self.assertIsNone(reviewed_combat_damage("Magnus the Red", raw))

    def test_damage_from_opponent_seat_creates_opponent_owned_token(self):
        magnus = self.add("Magnus the Red", owner=2)
        out = self.hit(magnus, victim=0)
        self.assertEqual(self.k.get(out.token_ids[0]).controller, 2)
        self.assertTrue(self.z.assert_consistent())


if __name__ == "__main__":
    unittest.main()
