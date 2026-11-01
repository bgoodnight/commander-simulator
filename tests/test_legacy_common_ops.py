"""Generic effect operations reuse authoritative table services, not card names."""
import unittest
from types import SimpleNamespace as NS

from commander_sim.legacy_common_ops import (
    DrawDiscard, TokenBatch, GenericDiscount,
    apply_draw_discard, apply_token_batch, apply_generic_discount,
)


class Player:
    def __init__(self):
        self.draws = []
    def draw(self, count=1):
        self.draws.append(count)


class Selection:
    def __init__(self):
        self.calls = []
    def discard(self, seat, n, kind):
        self.calls.append((seat,n,kind))


class Table:
    def __init__(self):
        self.players = [Player(), Player()]
        self.tokens = []
    def add_creature(self, player, power, toughness, name, token=False, **kw):
        row = (player is self.players[0], power,toughness,name,token,kw)
        self.tokens.append(row)
        return NS(id=len(self.tokens),name=name)


class CommonEffectOpsTests(unittest.TestCase):
    def test_draw_and_discard_in_sequence_and_with_existing_services(self):
        table = Table()
        selection = Selection()
        apply_draw_discard(table,0,DrawDiscard(2,2,"frantic_discard"),selection=selection)
        self.assertEqual(table.players[0].draws,[2])
        self.assertEqual(selection.calls,[(0,2,"frantic_discard")])

    def test_standalone_draw_does_not_create_discard(self):
        table = Table()
        apply_draw_discard(table,1,DrawDiscard(1))
        self.assertEqual(table.players[1].draws,[1])
        self.assertEqual(table.players[0].draws,[])

    def test_discard_requires_authoritative_selection_before_any_draw(self):
        table = Table()
        with self.assertRaises(ValueError):
            apply_draw_discard(table,0,DrawDiscard(2,1))
        self.assertEqual(table.players[0].draws,[])

    def test_draw_discard_rejects_bad_counts(self):
        for spec in ((-1,0),(1,-1),(True,0)):
            with self.subTest(spec=spec),self.assertRaises(ValueError):
                DrawDiscard(*spec)

    def test_token_batch_forwards_definition_and_creates_exact_count(self):
        table = Table()
        definition = NS(name="Elemental",colors=frozenset({"U","R"}))
        batch=TokenBatch(2,1,1,"Elemental",definition)
        tokens=apply_token_batch(table,0,batch)
        self.assertEqual(len(tokens),2)
        self.assertEqual([x.id for x in tokens],[1,2])
        self.assertEqual([t[5]["definition"] for t in table.tokens],[definition]*2)

    def test_zero_token_batch_is_safe_noop(self):
        table = Table()
        self.assertEqual(apply_token_batch(table,0,TokenBatch(0,1,1,"Zombie")),())
        self.assertEqual(table.tokens,[])

    def test_bad_token_metadata_fails_before_mutation(self):
        table=Table()
        with self.assertRaises(ValueError):
            TokenBatch(-1,1,1,"Zombie")
        self.assertEqual(table.tokens,[])

    def test_discounts_preserve_colored_pips_and_stack(self):
        action=NS(source="Spell",cost=7,parameters={"U":2,"R":1})
        sources=[NS(card=NS(name="Sapphire Medallion")) for _ in range(2)]
        self.assertIs(action,apply_generic_discount(
            action,sources,GenericDiscount(2,"U","Sapphire Medallion"),
            {"Spell":("U",)}))
        self.assertEqual(action.cost,3)

    def test_discounts_do_not_touch_other_colored_spells(self):
        action=NS(source="Red Spell",cost=5,parameters={"U":0,"R":1})
        sources=[NS(card=NS(name="Sapphire Medallion"))]
        apply_generic_discount(action,sources,GenericDiscount(1,"U","Sapphire Medallion"),
                               {"Red Spell":("R",)})
        self.assertEqual(action.cost,5)

    def test_discount_rejects_invalid_parameters(self):
        for amount in (-1,True):
            with self.subTest(amount=amount),self.assertRaises(ValueError):
                GenericDiscount(amount,"U","Sapphire Medallion")


if __name__=="__main__":
    unittest.main()
