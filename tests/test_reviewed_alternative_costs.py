"""Black Phyrexian costs and reviewed K'rrik are cost alternatives, not mana."""
import unittest
from types import SimpleNamespace
from commander_sim.reviewed_alternative_costs import (
    black_life_options, reviewed_krrik, controls_reviewed_krrik,
)


class BlackLifePaymentTests(unittest.TestCase):
    def test_phyrexian_printed_symbol_substitutions(self):
        options=black_life_options("{4}{B/P}{B/P}{B/P}",
                                   "{4}{B}{B}{B}",available_life=40)
        self.assertEqual([(x.mana_cost,x.life_cost) for x in options],
                         [("{4}{B}{B}{B}",0),("{4}{B}{B}",2),
                          ("{4}{B}",4),("{4}",6)])

    def test_krrik_substitutes_normal_black_symbols_with_life_bound(self):
        options=black_life_options("{2}{B}{B}","{2}{B}{B}",
                                   krrik_active=True,available_life=4)
        self.assertEqual([x.life_cost for x in options],[0,2])
        self.assertEqual(options[1].mana_cost,"{2}{B}")

    def test_live_krrik_requires_pinned_identity_and_text(self):
        raw={"oracle_id":"cbe3a4e7-5dbe-4f58-8ee6-a1762b65acfd",
             "oracle_text":"({B/P} can be paid with either {B} or 2 life.)\nLifelink\nFor each {B} in a cost, you may pay 2 life rather than pay that mana.\nWhenever you cast a black spell, put a +1/+1 counter on K'rrik."}
        self.assertTrue(reviewed_krrik("K'rrik, Son of Yawgmoth",raw))
        obj=SimpleNamespace(zone="battlefield",controller=0,
             card=SimpleNamespace(name="K'rrik, Son of Yawgmoth",
                  card_id=raw["oracle_id"]))
        kernel=SimpleNamespace(objects={1:obj})
        self.assertTrue(controls_reviewed_krrik(kernel,
                        {"K'rrik, Son of Yawgmoth":raw},0))
        obj.card.card_id="incorrect"
        self.assertFalse(controls_reviewed_krrik(kernel,
                         {"K'rrik, Son of Yawgmoth":raw},0))


if __name__=="__main__":
    unittest.main()
