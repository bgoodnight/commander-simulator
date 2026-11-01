"""Kernel-backed reporting is a view, never a second game state."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulator/v9b_live"))
from state import IndexedKernel, LiveZones
from rules import CardDefinition
from commander_sim.kernel_reporting import project_kernel_turn
from commander_sim.feature_tracking import analyze_game_turns


CATALOG = {
    "Swamp": {"type_line": "Basic Land — Swamp", "keywords": []},
    "Zombie": {"type_line": "Creature — Zombie", "keywords": []},
    "Wizard": {"type_line": "Creature — Wizard", "keywords": []},
    "Tutor": {"type_line": "Sorcery", "keywords": []},
}


class KernelReportingTests(unittest.TestCase):
    def setUp(self):
        self.k = IndexedKernel()
        self.z = LiveZones(self.k)
        self.profile = {
            "key_cards": [{"id": "zombie", "card": "Zombie"}],
            "groups": [{"id": "creatures", "cards": ["Zombie", "Wizard"]}],
            "combos": [],
        }

    def add(self, name, owner=0, zone="hand", token=False, controller=None):
        kind = "land" if name == "Swamp" else "creature"
        definition = CardDefinition("test:" + name, name, frozenset({kind}))
        oid = self.z.add(definition, owner, zone, token=token)
        if controller is not None:
            self.k.get(oid).controller = controller
        return oid

    def project(self, seat=0, turn=1, **kwargs):
        return project_kernel_turn(self.z, seat, turn, CATALOG, **kwargs)

    def test_read_only_projection_preserves_ids_and_state(self):
        swamp = self.add("Swamp", zone="battlefield")
        zombie = self.add("Zombie", zone="hand")
        before = tuple(sorted(self.k.objects))
        state = self.project()
        self.assertEqual([x["object_id"] for x in state["object_views"]["battlefield"]], [swamp])
        self.assertEqual([x["object_id"] for x in state["object_views"]["hand"]], [zombie])
        self.assertEqual(tuple(sorted(self.k.objects)), before)
        self.assertEqual(self.k.get(zombie).zone, "hand")
        self.assertEqual(state["source"], "authoritative_game")

    def test_battlefield_uses_controller_not_owner(self):
        own = self.add("Zombie", owner=0, zone="battlefield", controller=1)
        stolen = self.add("Wizard", owner=1, zone="battlefield", controller=0)
        self.assertEqual(self.project(0)["battlefield"], ["Wizard"])
        self.assertEqual(self.project(1)["battlefield"], ["Zombie"])
        self.assertEqual(self.k.get(own).owner, 0)
        self.assertEqual(self.k.get(stolen).owner, 1)

    def test_nonbattlefield_private_zones_are_owner_scoped(self):
        self.add("Zombie", owner=0, zone="graveyard")
        self.add("Wizard", owner=0, zone="exile")
        self.add("Tutor", owner=1, zone="hand")
        self.assertEqual(self.project(0)["graveyard"], ["Zombie"])
        self.assertEqual(self.project(0)["exile"], ["Wizard"])
        self.assertEqual(self.project(1)["exile"], [])
        self.assertEqual(self.project(0)["hand"], [])
        self.assertEqual(self.project(1)["hand"], ["Tutor"])

    def test_uncatalogued_token_is_explicitly_untracked(self):
        oid = self.add("Synthetic Zombie", zone="battlefield", token=True)
        state = self.project()
        self.assertEqual(state["battlefield"], [])
        self.assertEqual(state["untracked_tokens"], [{"object_id": oid, "name": "Synthetic Zombie"}])
        self.assertIn(oid, self.k.objects)

    def test_unknown_nontoken_fails_closed(self):
        self.add("Unverified Creature", zone="battlefield")
        with self.assertRaises(ValueError):
            self.project()

    def test_unverified_tutor_entry_rejected(self):
        with self.assertRaises(ValueError):
            self.project(verified_tutor_access=[
                {"tutor": "Tutor", "target": "Zombie", "destination": "hand", "verified": False}
            ])

    def test_adapter_feeds_strategy_analyzer(self):
        self.add("Zombie", zone="hand")
        a = self.project(turn=1)
        oid = self.z.ids(0, "hand")[0]
        self.z.move(oid, "battlefield")
        b = self.project(turn=2)
        result = analyze_game_turns(CATALOG, self.profile, [a, b])
        self.assertEqual(result["turns"][0]["key_cards"][0]["hand"], 1)
        self.assertEqual(result["turns"][1]["key_cards"][0]["battlefield"], 1)
        self.assertEqual(result["turns"][1]["groups_on_battlefield"]["creatures"], 1)

    def test_invalid_seat_turn_fails(self):
        with self.assertRaises(ValueError):
            self.project(seat=4)
        with self.assertRaises(ValueError):
            self.project(turn=0)


if __name__ == "__main__":
    unittest.main()
