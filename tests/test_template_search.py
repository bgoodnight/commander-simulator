"""Reusable tutor actions: real library objects, type/color/MV restrictions."""
import unittest

from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.template_search import legal_search_targets, execute_reviewed_search_to_hand

FABRICATE = {
    "oracle_id": "422e1869-134f-463d-9fa1-86b66a998b3e",
    "oracle_text": "Search your library for an artifact card, reveal it, put it into your hand, then shuffle.",
    "mana_cost": "{2}{U}", "type_line": "Sorcery", "layout": "normal"}
MERCHANT = {
    "oracle_id": "86cebe2a-95e7-4f22-99cc-e805aeaf347e",
    "oracle_text": "Search your library for a blue instant card, reveal that card, put it into your hand, then shuffle.",
    "mana_cost": "{1}{U}", "type_line": "Sorcery", "layout": "normal"}
SPELLSEEKER = {
    "oracle_id": "47a785ed-8095-4685-8daa-02c4e2b0ffcd",
    "oracle_text": "When this creature enters, you may search your library for an instant or sorcery card with mana value 2 or less, reveal it, put it into your hand, then shuffle.",
    "mana_cost": "{2}{U}", "type_line": "Creature — Human Wizard", "layout": "normal"}
MYSTICAL = {
    "oracle_id": "fb81f95c-70f8-4eb7-8d15-15d0ae23ec03",
    "oracle_text": "Search your library for an instant or sorcery card, reveal it, then shuffle and put that card on top.",
    "mana_cost": "{U}", "type_line": "Instant", "layout": "normal"}


class TutorTemplateTests(unittest.TestCase):
    def setUp(self):
        K, Zones, Card = _load_live_kernel()
        self.k, self.z, self.Card = K(), None, Card
        self.z = Zones(self.k, seed=17)
        self.catalog = {
            "Fabricate": FABRICATE,
            "Merchant Scroll": MERCHANT,
            "Spellseeker": SPELLSEEKER,
            "Mystical Tutor": MYSTICAL,
            "Sol Ring": {"type_line": "Artifact", "cmc": 1, "colors": []},
            "Island": {"type_line": "Basic Land — Island", "cmc": 0, "colors": []},
            "Blue Instant": {"type_line": "Instant", "cmc": 2, "colors": ["U"]},
            "Red Instant": {"type_line": "Instant", "cmc": 1, "colors": ["R"]},
            "Big Sorcery": {"type_line": "Sorcery", "cmc": 5, "colors": ["U"]},
        }

    def add(self, name, zone, *, card_id=None, owner=0, types=None):
        if types is None:
            type_head = self.catalog[name]["type_line"].split(" — ", 1)[0].lower().split()
            types = frozenset(x for x in type_head
                              if x in {"artifact", "creature", "sorcery", "instant", "land"})
        return self.z.add(self.Card(card_id or ("test:" + name), name, types,
                                    coverage="approx"), owner, zone)

    def tutor_on_stack(self, name):
        oid = self.add(name, "hand", card_id=self.catalog[name]["oracle_id"])
        return self.z.cast(0, oid).object_id

    def test_fabricate_searches_exact_artifact_object_and_shuffles(self):
        source = self.tutor_on_stack("Fabricate")
        rock = self.add("Sol Ring", "library")
        self.add("Island", "library")
        self.assertEqual(legal_search_targets(self.z, 0, source, self.catalog), (rock,))
        result = execute_reviewed_search_to_hand(self.z, 0, source, rock, self.catalog)
        self.assertEqual(result.target_old_id, rock)
        self.assertNotEqual(result.target_new_id, rock)
        self.assertEqual(self.k.get(result.target_new_id).zone, "hand")
        self.assertEqual(self.k.get(result.target_new_id).card.name, "Sol Ring")
        self.assertTrue(result.shuffled)
        self.assertTrue(self.z.assert_consistent())

    def test_merchant_scroll_checks_actual_card_color_not_identity(self):
        source = self.tutor_on_stack("Merchant Scroll")
        blue = self.add("Blue Instant", "library")
        self.add("Red Instant", "library")
        self.assertEqual(legal_search_targets(self.z, 0, source, self.catalog), (blue,))

    def test_spellseeker_mana_value_two_cap(self):
        source = self.add("Spellseeker", "battlefield",
                          card_id=SPELLSEEKER["oracle_id"])
        good = self.add("Blue Instant", "library")
        self.add("Big Sorcery", "library")
        self.assertEqual(legal_search_targets(self.z, 0, source, self.catalog), (good,))

    def test_unreviewed_search_source_or_zone_rejected(self):
        source = self.add("Fabricate", "hand", card_id=FABRICATE["oracle_id"])
        self.add("Sol Ring", "library")
        with self.assertRaises(ValueError):
            legal_search_targets(self.z, 0, source, self.catalog)
        self.assertEqual(self.z.names(0, "hand"), ("Fabricate",))

    def test_invalid_target_does_not_move_any_object(self):
        source = self.tutor_on_stack("Fabricate")
        wrong = self.add("Island", "library")
        before = set(self.k.objects)
        with self.assertRaises(ValueError):
            execute_reviewed_search_to_hand(self.z, 0, source, wrong, self.catalog)
        self.assertEqual(set(self.k.objects), before)
        self.assertEqual(self.k.get(wrong).zone, "library")

    def test_unimplemented_library_top_destination_fails_without_mutation(self):
        source = self.tutor_on_stack("Mystical Tutor")
        target = self.add("Blue Instant", "library")
        with self.assertRaises(NotImplementedError):
            execute_reviewed_search_to_hand(self.z, 0, source, target, self.catalog)
        self.assertEqual(self.k.get(target).zone, "library")


if __name__ == "__main__":
    unittest.main()
