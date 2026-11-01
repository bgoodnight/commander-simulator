"""Reviewed generic cost reductions combine without granting unsupported plays."""
import unittest

from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.reviewed_cost_reduction import (
    REDUCERS, reduced_fixed_cost, reduction_for_spell)
from commander_sim.reviewed_token_spells import (
    TOKEN_SPELLS, TokenBlueprint, create_reviewed_token_batches,
    cast_and_resolve_reviewed_token_spell)
from commander_sim.template_resources import TemplateManaService


class ReviewedCostReductionTests(unittest.TestCase):
    def setUp(self):
        K, Z, C = _load_live_kernel()
        self.k = K()
        self.z = Z(self.k, seed=19)
        self.C = C
        self.raw = {}
        for name, rule in REDUCERS.items():
            self.raw[name] = {
                "oracle_id": rule.oracle_id, "oracle_text": rule.excerpt,
                "colors": ["U"] if name == "Baral, Chief of Compliance" else [],
            }
        for name, row in TOKEN_SPELLS.items():
            self.raw[name] = {
                "oracle_id": row.oracle_id, "oracle_text": row.oracle_text,
                "mana_cost": row.mana_cost, "type_line": "Sorcery",
                "layout": "normal", "colors": ["R"] if name == "Ral's Reinforcements" else ["U"],
            }
        self.raw["Mountain"] = {"type_line": "Basic Land — Mountain"}
        self.service = TemplateManaService(self.k, self.raw, {"U", "R"}, zones=self.z)

    def add(self, name, types, zone="battlefield", owner=0, *, token=False,
            colors=frozenset()):
        return self.z.add(self.C(
            self.raw.get(name, {}).get("oracle_id", "test:" + name),
            name, frozenset(types), colors=colors, coverage="approx"),
            owner, zone, token=token)

    def source(self, name):
        return self.add(name, ("creature",) if name != "Sapphire Medallion"
                        else ("artifact",))

    def test_baral_reduces_generic_but_not_colored_requirements(self):
        baral = self.source("Baral, Chief of Compliance")
        cost, sources = reduced_fixed_cost(
            self.k, self.raw, 0, "{2}{U}{R}",
            spell_types=frozenset({"instant"}), spell_colors=frozenset({"U","R"}))
        self.assertEqual((cost.generic, cost.colored), (1, ("U", "R")))
        self.assertEqual(sources, ((baral, "Baral, Chief of Compliance", 1),))
        self.assertEqual(reduced_fixed_cost(
            self.k, self.raw, 0, "{U}{R}",
            spell_types=frozenset({"sorcery"}),
            spell_colors=frozenset({"U","R"}))[0].generic, 0)

    def test_multiple_sources_stack_and_generic_floors_at_zero(self):
        self.source("Baral, Chief of Compliance")
        self.source("Goblin Electromancer")
        self.source("Stormcatch Mentor")
        cost, evidence = reduced_fixed_cost(
            self.k, self.raw, 0, "{2}{R}",
            spell_types=frozenset({"sorcery"}), spell_colors=frozenset({"R"}))
        self.assertEqual(cost.generic, 0)
        self.assertEqual(cost.colored, ("R",))
        self.assertEqual(sum(row[2] for row in evidence), 3)

    def test_magnus_counts_controlled_creature_tokens_and_changes_dynamically(self):
        self.source("Magnus the Red")
        token = TokenBlueprint("Zombie", frozenset({"creature"}),
                               frozenset({"Zombie"}), frozenset({"B"}), 2, 2, count=2)
        ids = create_reviewed_token_batches(self.z, 0, (token,))
        cost, evidence = reduced_fixed_cost(
            self.k, self.raw, 0, "{4}{R}",
            spell_types=frozenset({"instant"}), spell_colors=frozenset({"R"}))
        self.assertEqual(cost.generic, 2)
        self.assertEqual(evidence[0][2], 2)
        self.z.move(ids[0], "graveyard", "sacrifice")
        cost, _ = reduced_fixed_cost(
            self.k, self.raw, 0, "{4}{R}",
            spell_types=frozenset({"instant"}), spell_colors=frozenset({"R"}))
        self.assertEqual(cost.generic, 3)

    def test_sapphire_applies_to_blue_spells_not_red_or_colorless(self):
        self.source("Sapphire Medallion")
        blue, _ = reduced_fixed_cost(
            self.k, self.raw, 0, "{3}{U}",
            spell_types=frozenset({"instant"}), spell_colors=frozenset({"U"}))
        red, evidence = reduced_fixed_cost(
            self.k, self.raw, 0, "{3}{R}",
            spell_types=frozenset({"instant"}), spell_colors=frozenset({"R"}))
        self.assertEqual(blue.generic, 2)
        self.assertEqual(red.generic, 3)
        self.assertEqual(evidence, ())

    def test_source_identity_or_battlefield_control_mismatch_fails_closed(self):
        fake = self.add("Baral, Chief of Compliance", ("creature",), owner=1)
        self.assertEqual(reduction_for_spell(
            self.k, self.raw, 0, spell_types=frozenset({"sorcery"}),
            spell_colors=frozenset({"U"})), ())
        self.k.get(fake).controller = 0
        self.raw["Baral, Chief of Compliance"]["oracle_text"] = "Invalid"
        self.assertEqual(reduction_for_spell(
            self.k, self.raw, 0, spell_types=frozenset({"sorcery"}),
            spell_colors=frozenset({"U"})), ())

    def test_creatures_do_not_receive_instant_sorcery_reductions(self):
        self.source("Baral, Chief of Compliance")
        cost, evidence = reduced_fixed_cost(
            self.k, self.raw, 0, "{4}{R}",
            spell_types=frozenset({"creature"}), spell_colors=frozenset({"R"}))
        self.assertEqual(cost.generic, 4)
        self.assertEqual(evidence, ())

    def test_reduction_funds_real_spell_without_fabricated_mana(self):
        self.source("Baral, Chief of Compliance")
        self.add("Mountain", ("land",))
        spell = self.add("Ral's Reinforcements", ("sorcery",), "hand",
                         colors=frozenset({"R"}))
        paid, sources = self.service.spell_cost(0, "{1}{R}", self.k.get(spell))
        self.assertEqual(paid, "{0}{R}")
        self.assertEqual(sources[0][1], "Baral, Chief of Compliance")
        result = cast_and_resolve_reviewed_token_spell(
            self.z, 0, spell, self.raw, {"U","R"}, self.service)
        self.assertIsNotNone(result)
        self.assertEqual(len(result.token_ids), 2)
        self.assertEqual(len(result.paid_source_ids), 1)
        self.assertTrue(self.z.assert_consistent())


if __name__ == "__main__":
    unittest.main()
