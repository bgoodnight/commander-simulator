"""Repeatable Gravecrawler casts use real zones and real mana, not combos."""
import unittest

from commander_sim.early_game_runner import _load_live_kernel, run_bounded_early_game
from commander_sim.reviewed_graveyard_creatures import (
    GRAVEYARD_CREATURES, reviewed_graveyard_creature,
    graveyard_creature_cast_ready, cast_reviewed_graveyard_creature)
from commander_sim.template_resources import TemplateManaService


class PhysicalGraveyardCreatureTests(unittest.TestCase):
    def setUp(self):
        K, Z, C = _load_live_kernel()
        self.kernel = K()
        self.zones = Z(self.kernel, seed=8)
        self.C = C
        rule = GRAVEYARD_CREATURES["Gravecrawler"]
        self.catalog = {
            "Gravecrawler": {
                "oracle_id": rule.oracle_id,
                "oracle_text": rule.oracle_text,
                "mana_cost": rule.printed_cost,
                "type_line": "Creature — Zombie",
                "layout": "normal",
                "colors": ["B"]},
            "Swamp": {"type_line": "Basic Land — Swamp"}}
        self.service = TemplateManaService(
            self.kernel, self.catalog, {"B"}, zones=self.zones)

    def add(self, name, zone="battlefield", *, owner=0, subtype=None,
            oracle=None, coverage="approx"):
        is_land = name == "Swamp"
        is_crawler = name == "Gravecrawler"
        return self.zones.add(
            self.C(oracle or (
                self.catalog["Gravecrawler"]["oracle_id"]
                if is_crawler else "test:"+name),
                name, frozenset({"land"} if is_land else {"creature"}),
                subtypes=frozenset({subtype} if subtype else
                                   {"Zombie"} if is_crawler else set()),
                colors=frozenset({"B"}) if is_crawler else None,
                coverage=coverage),
            owner, zone)

    def cast(self, oid, *, sorcery_window=True):
        return cast_reviewed_graveyard_creature(
            self.zones, 0, oid, self.catalog, self.service,
            sorcery_window=sorcery_window)

    def test_cast_requires_other_controlled_zombie_and_physical_black_mana(self):
        grave = self.add("Gravecrawler", "graveyard")
        self.add("Swamp")
        self.assertIsNone(graveyard_creature_cast_ready(
            self.zones, 0, grave, self.catalog))
        with self.assertRaises(ValueError):
            self.cast(grave)
        self.add("Zombie Ally", subtype="Zombie")
        self.assertIsNotNone(graveyard_creature_cast_ready(
            self.zones, 0, grave, self.catalog))
        out = self.cast(grave)
        self.assertEqual(out.source_old_id, grave)
        self.assertEqual(len(out.paid_source_ids), 1)
        self.assertNotIn(grave, self.kernel.objects)
        self.assertEqual(self.kernel.get(out.permanent_id).zone, "battlefield")
        self.assertEqual(self.kernel.get(out.permanent_id).card.name, "Gravecrawler")
        self.assertEqual(self.zones.ids(0, "graveyard"), ())
        self.assertTrue(self.zones.assert_consistent())

    def test_repeat_after_sacrifice_with_new_mana_not_free(self):
        self.add("Zombie Ally", subtype="Zombie")
        self.add("Swamp")
        grave = self.add("Gravecrawler", "graveyard")
        first = self.cast(grave)
        next_grave = self.zones.move(
            first.permanent_id, "graveyard", "sacrifice")
        self.assertEqual(self.kernel.get(next_grave).zone, "graveyard")
        self.assertIsNone(self.cast(next_grave))
        self.add("Swamp")
        second = self.cast(next_grave)
        self.assertNotEqual(second.permanent_id, first.permanent_id)
        self.assertEqual(self.zones.ids(0, "graveyard"), ())
        self.assertEqual(
            sum(obj.card.name == "Gravecrawler"
                for obj in self.kernel.objects.values()), 1)
        casts = [event for event in self.kernel.events
                 if event.name == "spell_cast"]
        self.assertEqual(len(casts), 2)
        self.assertTrue(self.zones.assert_consistent())

    def test_wrong_subtype_or_opponent_zombie_no_permission(self):
        grave = self.add("Gravecrawler", "graveyard")
        self.add("Human Ally", subtype="Human")
        self.add("Zombie Opponent", owner=1, subtype="Zombie")
        self.assertIsNone(graveyard_creature_cast_ready(
            self.zones, 0, grave, self.catalog))
        self.add("Zombie Ally", subtype="Zombie", owner=0)
        self.assertIsNotNone(graveyard_creature_cast_ready(
            self.zones, 0, grave, self.catalog))

    def test_bad_oracle_text_and_unimplemented_object_fail_closed(self):
        grave = self.add("Gravecrawler", "graveyard")
        self.add("Zombie Ally", subtype="Zombie")
        self.add("Swamp")
        altered = dict(self.catalog["Gravecrawler"])
        altered["oracle_text"] = "Unreviewed alternate wording"
        self.assertIsNone(reviewed_graveyard_creature("Gravecrawler", altered))
        self.catalog["Gravecrawler"] = altered
        with self.assertRaises(ValueError):
            self.cast(grave)
        self.assertFalse(self.kernel.get(next(iter(
            self.zones.ids(0, "battlefield")))).tapped)
        self.assertIn(grave, self.zones.ids(0, "graveyard"))

    def test_sorcery_timing_and_no_permission_for_hand_cards(self):
        grave = self.add("Gravecrawler", "graveyard")
        hand = self.add("Gravecrawler", "hand")
        self.add("Zombie Ally", subtype="Zombie")
        self.add("Swamp")
        with self.assertRaises(ValueError):
            self.cast(grave, sorcery_window=False)
        with self.assertRaises(ValueError):
            self.cast(hand)
        self.assertIn(grave, self.zones.ids(0, "graveyard"))
        self.assertIn(hand, self.zones.ids(0, "hand"))

    def test_never_casts_if_mana_unavailable_or_card_unreviewed(self):
        grave = self.add("Gravecrawler", "graveyard")
        self.add("Zombie Ally", subtype="Zombie")
        self.assertIsNone(self.cast(grave))
        self.assertIn(grave, self.zones.ids(0, "graveyard"))
        other = self.add("Gravecrawler", "graveyard", oracle="different-id")
        self.add("Swamp")
        with self.assertRaises(ValueError):
            self.cast(other)
        self.assertIn(other, self.zones.ids(0, "graveyard"))

    def test_six_deck_bounded_runs_are_deterministic_and_conservative(self):
        for key in ("magnus_premium", "magnus_budget", "wretched_ranks",
                    "mortarion_current", "mortarion_ideal", "necron_dynasties"):
            with self.subTest(deck=key):
                a = run_bounded_early_game(key, seed=5, turns=5)
                b = run_bounded_early_game(key, seed=5, turns=5)
                self.assertEqual(a, b)
                for row, snapshot in zip(a["events"], a["state_snapshots"]):
                    casts = [e for e in row["events"]
                             if e["type"] == "reviewed_graveyard_creature_cast"]
                    resolved = [e for e in row["events"]
                                if e["type"] == "reviewed_graveyard_creature_resolved"]
                    self.assertLessEqual(len(casts), 1)
                    self.assertEqual(len(casts), len(resolved))
                    self.assertTrue(all(e["card"] == "Gravecrawler" for e in casts))
                    self.assertEqual(
                        row["library_size"] + row["hand_size"] +
                        len(snapshot["battlefield"]) + len(snapshot["graveyard"]) +
                        len(snapshot["exile"]) + row["command_zone_count"], 100)


if __name__ == "__main__":
    unittest.main()
