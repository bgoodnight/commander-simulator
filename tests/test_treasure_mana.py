"""Reviewed Treasure mana conversion uses authoritative physical token sacrifices."""
import unittest

from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.reviewed_token_spells import TokenBlueprint, create_reviewed_token_batches
from commander_sim.template_resources import TemplateManaService


TREASURE = TokenBlueprint("Treasure", frozenset({"artifact"}),
                          frozenset({"Treasure"}), frozenset(), 0, 0)


class TreasureManaTests(unittest.TestCase):
    def setUp(self):
        K, Z, C = _load_live_kernel()
        self.kernel = K()
        self.zones = Z(self.kernel, seed=7)
        self.Card = C
        self.service = TemplateManaService(
            self.kernel, {}, {"U", "R"}, zones=self.zones)

    def token(self, seat=0):
        return create_reviewed_token_batches(self.zones, seat, (TREASURE,))[0]

    def test_treasure_sacrifices_physical_token_for_chosen_color(self):
        old = self.token()
        payment = self.service.pay(0, "{R}")
        self.assertEqual(payment.source_ids, (old,))
        self.assertNotIn(old, self.kernel.objects)
        self.assertEqual(self.zones.ids(0, "battlefield"), ())
        self.assertEqual(self.zones.ids(0, "graveyard"), ())
        self.assertTrue(any(e.name == "token_ceased" for e in self.kernel.events))
        self.assertTrue(self.zones.assert_consistent())
        self.assertIsNone(self.service.plan(0, "{R}"))

    def test_colors_are_choices_not_five_simultaneous_pips(self):
        old = self.token()
        self.assertIsNotNone(self.service.plan(0, "{U}"))
        self.assertIsNotNone(self.service.plan(0, "{R}"))
        self.assertIsNone(self.service.plan(0, "{U}{R}"))
        payment = self.service.pay(0, "{U}")
        self.assertEqual(payment.source_ids, (old,))
        self.assertIsNone(self.service.plan(0, "{R}"))

    def test_two_tokens_support_two_pips_and_never_duplicate(self):
        ids = (self.token(), self.token())
        payment = self.service.pay(0, "{U}{R}")
        self.assertEqual(set(payment.source_ids), set(ids))
        self.assertFalse(any(i in self.kernel.objects for i in ids))
        self.assertIsNone(self.service.plan(0, "{1}"))

    def test_fake_name_or_wrong_blueprint_cannot_pay(self):
        fake = self.zones.add(self.Card(
            "not-reviewed:Treasure", "Treasure",
            frozenset({"artifact"}), subtypes=frozenset({"Treasure"})),
            0, "battlefield", token=True)
        self.assertIsNone(self.service.plan(0, "{U}"))
        self.assertIn(fake, self.kernel.objects)

    def test_opponent_owned_token_and_lack_of_zone_host_rejected(self):
        self.token(seat=1)
        self.assertIsNone(self.service.plan(0, "{U}"))
        self.assertIsNotNone(self.service.plan(1, "{U}"))
        without_host = TemplateManaService(self.kernel, {}, {"U", "R"})
        self.assertIsNone(without_host.plan(1, "{U}"))

    def test_treasure_funds_real_spell_resolution(self):
        from commander_sim.reviewed_token_spells import (
            TOKEN_SPELLS, cast_and_resolve_reviewed_token_spell)
        raw = {}
        for name in ("Strike It Rich", "Hard Evidence"):
            recipe = TOKEN_SPELLS[name]
            raw[name] = {"oracle_id": recipe.oracle_id,
                         "oracle_text": recipe.oracle_text,
                         "mana_cost": recipe.mana_cost,
                         "type_line": "Sorcery", "layout": "normal"}
        raw["Mountain"] = {"type_line": "Basic Land — Mountain"}
        mountain = self.zones.add(self.Card(
            "test:mountain", "Mountain", frozenset({"land"})),
            0, "battlefield")
        service = TemplateManaService(
            self.kernel, raw, {"U", "R"}, zones=self.zones)
        strike = self.zones.add(self.Card(
            TOKEN_SPELLS["Strike It Rich"].oracle_id, "Strike It Rich",
            frozenset({"sorcery"}), coverage="approx"), 0, "hand")
        first = cast_and_resolve_reviewed_token_spell(
            self.zones, 0, strike, raw, {"U", "R"}, service)
        self.assertEqual(len(first.token_ids), 1)
        treasure_id = first.token_ids[0]
        self.assertTrue(self.kernel.get(mountain).tapped)
        # The Mountain is still tapped; only the genuine Treasure can pay U.
        evidence = self.zones.add(self.Card(
            TOKEN_SPELLS["Hard Evidence"].oracle_id, "Hard Evidence",
            frozenset({"sorcery"}), coverage="approx"), 0, "hand")
        second = cast_and_resolve_reviewed_token_spell(
            self.zones, 0, evidence, raw, {"U", "R"}, service)
        self.assertEqual(second.paid_source_ids, (treasure_id,))
        self.assertEqual([self.kernel.get(i).card.name
                          for i in second.token_ids], ["Crab", "Clue"])
        self.assertNotIn(treasure_id, self.kernel.objects)
        self.assertTrue(self.zones.assert_consistent())

    def test_preview_is_pure_and_rejects_tapped_token(self):
        token = self.token()
        before = tuple(self.zones.ids(0, "battlefield"))
        self.assertIsNotNone(self.service.plan(0, "{U}"))
        self.assertEqual(tuple(self.zones.ids(0, "battlefield")), before)
        self.assertIn(token, self.kernel.objects)
        self.kernel.get(token).tapped = True
        self.assertIsNone(self.service.plan(0, "{U}"))


if __name__ == "__main__":
    unittest.main()
