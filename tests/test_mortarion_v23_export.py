import unittest
from collections import Counter

from commander_sim.deck_fixtures import USER_FIXTURES
from tools.export_gorge_decks import export_deck


class MortarionV23ExportTest(unittest.TestCase):
    def test_export_has_submitted_commander_and_singleton_deck(self):
        fixture = next(f for f in USER_FIXTURES if f.key == "mortarion_v2_3")
        deck = export_deck(fixture)
        counts = Counter({card["name"]: card["count"] for card in deck["cards"]})
        self.assertEqual(sum(counts.values()), 100)
        self.assertEqual(deck["cards"][0], {"name": "Mortarion, Daemon Primarch", "count": 1})
        self.assertEqual(counts["Swamp"], 30)
        self.assertTrue(all(n == 1 for name, n in counts.items() if name != "Swamp"))
        for name in ("Thrashing Wumpus", "Basilisk Collar", "Eldrazi Monument",
                     "Soul of New Phyrexia", "Liliana's Contract"):
            self.assertEqual(counts[name], 1)


if __name__ == "__main__":
    unittest.main()
