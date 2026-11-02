"""Reusable parameterized library recipes: physical actions, safe imports and pinned cards."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.library_actions import (
    LibraryAction, bounded_library_choice, required_draws, resolve_library_actions,
)
from commander_sim.provisional_import import provisional_profile
from commander_sim.provisional_actions import cast_provisional_spell
from commander_sim.reviewed_draw_spells import (
    reviewed_draw_spell, cast_and_resolve_reviewed_draw_spell,
)
from commander_sim.template_resources import TemplateManaService


def raw(name, text, *, card_type="Sorcery", cost="{U}"):
    return dict(name=name, oracle_id="test:"+name, oracle_text=text,
                mana_cost=cost, type_line=card_type, layout="normal")


def fixture():
    K, Z, C = _load_live_kernel()
    k = K()
    z = Z(k, seed=39)
    return k, z, C


def add(z, C, name, zone, *, types=("creature",), card_id=None):
    return z.add(C(card_id or "test:"+name, name, frozenset(types),
                   coverage="approx"), 0, zone)


class LibraryActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cards = {}
        for fixture_item in FIXTURES:
            data = json.loads(fixture_item.snapshot_path.read_text())
            cls.cards.update({entry["deck_name"]: entry["card"]
                              for entry in data["cards"]})

    def test_parameters_are_typed_and_draws_counted(self):
        steps = (LibraryAction("surveil", 2), LibraryAction("draw", 2),
                 LibraryAction("discard", 1))
        self.assertEqual(required_draws(steps), 2)
        for kind, value in (("destroy", 1), ("scry", -1),
                            ("shuffle", 1), ("discard", 0), ("draw", 8)):
            with self.subTest(kind=kind, value=value):
                with self.assertRaises(ValueError):
                    LibraryAction(kind, value)

    def test_scry_bottom_then_draw_uses_real_library_order(self):
        k, z, C = fixture()
        add(z, C, "First", "library")
        land = add(z, C, "Island", "library", types=("land",))
        spell = add(z, C, "Top Spell", "library")
        def choose(kind, available, count, zones, seat):
            if kind == "scry":
                self.assertEqual(available, (spell, land))
                return {"bottom": (spell,), "top": (land,)}
            raise AssertionError(kind)
        outcome = resolve_library_actions(
            z, 0, (LibraryAction("scry", 2), LibraryAction("draw", 1)),
            select=choose)
        self.assertEqual(outcome.bottomed_ids, (spell,))
        self.assertEqual(k.get(outcome.drawn_ids[0]).card.name, "Island")
        self.assertEqual(z.ids(0, "library")[0], spell)
        self.assertEqual([x["kind"] for x in outcome.steps], ["scry", "draw"])
        self.assertTrue(z.assert_consistent())

    def test_surveille_moves_inspected_cards_only_without_shuffling(self):
        k, z, C = fixture()
        first = add(z, C, "Bottom", "library")
        middle = add(z, C, "Draw Next", "library")
        top = add(z, C, "Mill Top", "library")
        def choose(kind, visible, count, zones, seat):
            self.assertEqual(kind, "surveil")
            self.assertEqual(visible, (top,))
            return (top,)
        outcome = resolve_library_actions(
            z, 0, (LibraryAction("surveil", 1), LibraryAction("draw", 1)),
            select=choose)
        self.assertEqual(k.get(outcome.milled_ids[0]).zone, "graveyard")
        self.assertEqual(k.get(outcome.drawn_ids[0]).card.name, "Draw Next")
        self.assertEqual(z.ids(0, "library"), (first,))
        self.assertTrue(z.assert_consistent())

    def test_brainstorm_return_order_does_not_duplicate_cards(self):
        k, z, C = fixture()
        original = add(z, C, "Old Hand", "hand")
        for name in ("A", "B", "C", "D"):
            add(z, C, name, "library")
        def choose(kind, available, count, zones, seat):
            self.assertEqual(kind, "put_back")
            self.assertEqual(count, 2)
            return tuple(available[-2:][::-1])
        result = resolve_library_actions(
            z, 0, (LibraryAction("draw", 3), LibraryAction("put_back", 2)),
            select=choose)
        self.assertEqual(len(result.drawn_ids), 3)
        self.assertEqual(len(result.returned_ids), 2)
        self.assertEqual(tuple(z.ids(0, "library")[-2:]),
                         tuple(reversed(result.returned_ids)))
        self.assertIn(original, z.ids(0, "hand"))
        self.assertEqual(len(z.ids(0, "hand")), 2)
        self.assertTrue(z.assert_consistent())

    def test_optional_shuffle_only_from_an_explicit_bool(self):
        k, z, C = fixture()
        for n in range(5):
            add(z, C, "L"+str(n), "library")
        seen = tuple(reversed(z.ids(0, "library")[-3:]))
        def choose(kind, available, count, zones, seat):
            return tuple(reversed(available)) if kind=="reorder_top" else True
        result = resolve_library_actions(
            z, 0, (LibraryAction("reorder_top", 3),
                   LibraryAction("shuffle")), select=choose)
        self.assertEqual(result.steps[-1]["shuffled"], True)
        self.assertEqual(set(z.ids(0, "library")), set(range(1, 6)))
        self.assertTrue(z.assert_consistent())

    def test_failed_preflight_does_not_commit_draw_or_mana(self):
        k, z, C = fixture()
        lone = add(z, C, "Only", "library")
        with self.assertRaises(ValueError):
            resolve_library_actions(z, 0, (LibraryAction("draw", 2),))
        self.assertEqual(z.ids(0, "library"), (lone,))

    def test_invalid_choice_rejected_before_surveil_move(self):
        k, z, C = fixture()
        first = add(z, C, "First", "library")
        top = add(z, C, "Top", "library")
        def wrong(*args):
            return (first,)
        with self.assertRaises(ValueError):
            resolve_library_actions(z, 0,
                (LibraryAction("surveil", 1),), select=wrong)
        self.assertEqual(z.ids(0, "library"), (first, top))

    def test_bounded_scry_does_not_bottom_last_needed_card(self):
        k, z, C = fixture()
        lone = add(z, C, "Nonland", "library")
        add(z, C, "Island", "battlefield", types=("land",))
        result = resolve_library_actions(z, 0, (
            LibraryAction("scry", 1), LibraryAction("draw", 1)))
        self.assertEqual(result.bottomed_ids, ())
        self.assertEqual(len(result.drawn_ids), 1)
        self.assertEqual(len(z.ids(0, "library")), 0)

    def test_source_pinned_five_cards_reuse_same_operations(self):
        expectations = {
            "Ponder": ("reorder_top", "shuffle", "draw"),
            "Preordain": ("scry", "draw"),
            "Consider": ("surveil", "draw"),
            "Brainstorm": ("draw", "put_back"),
            "Faithless Looting": ("draw", "discard"),
        }
        for name, kinds in expectations.items():
            with self.subTest(name=name):
                card = self.cards[name]
                review = reviewed_draw_spell(name, card)
                self.assertIsNotNone(review)
                self.assertEqual(tuple(x.kind for x in review.library_actions()), kinds)
                mismatched = dict(card, oracle_text=card["oracle_text"]+" Additional text.")
                self.assertIsNone(reviewed_draw_spell(name, mismatched))

    def test_new_import_parses_only_complete_simple_sequences(self):
        candidates = {
            "Scry 2, then draw a card.": ("scry", "draw"),
            "Surveil 1.\nDraw a card.": ("surveil", "draw"),
            "Draw two cards, then discard a card.": ("draw", "discard"),
            "Scry 1.": ("scry",),
            "Surveil 2.": ("surveil",),
        }
        for oracle, kinds in candidates.items():
            with self.subTest(oracle=oracle):
                p = provisional_profile(raw("Novel Card", oracle))
                self.assertIsNotNone(p)
                self.assertEqual(p.kind, "simple_spell")
                self.assertEqual(p.mode, "library_sequence")
                self.assertEqual(tuple(x.kind for x in p.library_actions), kinds)
        for oracle in (
            "Draw two cards, then discard a card. You win the game.",
            "Draw two cards, then discard a card.\nOverload {1}{U}",
            "Surveil 1.\nDraw a card.\nExile target permanent.",
            "Scry 2, then draw a card. (Reminder text requires review.)",
            "Surveil 8.",
        ):
            with self.subTest(oracle=oracle):
                self.assertIsNone(provisional_profile(raw("Unsafe Card", oracle)))

    def test_physical_new_import_surveillance_and_draw(self):
        k, z, C = fixture()
        card = raw("New Insight", "Surveil 1.\nDraw a card.")
        source = add(z, C, card["name"], "hand",
                     types=("sorcery",), card_id=card["oracle_id"])
        add(z, C, "Island", "battlefield", types=("land",))
        add(z, C, "Bottom", "library")
        add(z, C, "Drawn", "library", types=("land",))
        add(z, C, "Milled", "library")
        catalog = {card["name"]: card}
        mana = TemplateManaService(
            k, catalog, frozenset({"U"}), zones=z, provisional_mode="safe")
        result = cast_provisional_spell(
            z, KernelLife(k), 0, source, catalog, frozenset({"U"}), mana)
        self.assertEqual(result.operation, "library_sequence")
        self.assertEqual([x["kind"] for x in result.library_steps], ["surveil", "draw"])
        self.assertEqual(len(result.surveilled_ids), 1)
        self.assertEqual(k.get(result.surveilled_ids[0]).zone, "graveyard")
        self.assertEqual(k.get(result.drawn_ids[0]).card.name, "Drawn")
        self.assertTrue(z.assert_consistent())

    def test_reviewed_preordain_and_faithless_are_parameter_only(self):
        for name, col, deck_cards in (
            ("Preordain", "U", [("Bottom", ("creature",)),
                                 ("Island", ("land",)), ("Top", ("creature",))]),
            ("Faithless Looting", "R", [("A", ("creature",)),
                                        ("B", ("land",)), ("C", ("creature",))]),
        ):
            with self.subTest(name=name):
                k, z, C = fixture()
                card = self.cards[name]
                oid = add(z, C, name, "hand",
                          types=(card["type_line"].lower(),),
                          card_id=card["oracle_id"])
                add(z, C, "Island" if col=="U" else "Mountain",
                    "battlefield", types=("land",))
                for n, ts in deck_cards:
                    add(z, C, n, "library", types=ts)
                mana = TemplateManaService(
                    k, {name: card}, frozenset({col}), zones=z)
                result = cast_and_resolve_reviewed_draw_spell(
                    z, 0, oid, {name: card}, frozenset({col}), mana)
                self.assertIsNotNone(result)
                self.assertTrue(result.library_steps)
                if name=="Preordain":
                    self.assertEqual(result.library_steps[0]["kind"], "scry")
                else:
                    self.assertEqual(len(result.discarded_ids), 2)
                self.assertTrue(z.assert_consistent())


if __name__ == "__main__":
    unittest.main()
