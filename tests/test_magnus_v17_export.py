import unittest
from collections import Counter

from commander_sim.deck_fixtures import USER_FIXTURES
from tools.export_gorge_decks import export_deck


class MagnusV17ExportTest(unittest.TestCase):
    def test_export_has_submitted_commander_and_singleton_deck(self):
        fixture = next(f for f in USER_FIXTURES if f.key == "magnus_v1_7")
        deck = export_deck(fixture)
        counts = Counter({card["name"]: card["count"] for card in deck["cards"]})
        self.assertEqual(sum(counts.values()), 100)
        self.assertEqual(deck["cards"][0], {"name": "Magnus the Red", "count": 1})
        self.assertEqual(counts["Island"], 12)
        self.assertEqual(counts["Mountain"], 8)
        self.assertTrue(all(n == 1 for name, n in counts.items()
                            if name not in {"Island", "Mountain"}))
        self.assertEqual(counts["Phyrexian Altar"], 1)


if __name__ == "__main__":
    unittest.main()
