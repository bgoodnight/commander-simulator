"""Contract tests for shared resource diagnostics / ramp-first tutor policy."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from commander_sim.resource_development import (
    assess_resources, choose_tutor_target,
)


class FakeKernel:
    def __init__(self, objects):
        self.objects = {o.object_id: o for o in objects}
    def get(self, oid):
        return self.objects[oid]


def obj(oid, name, *, zone="battlefield", types=(), tapped=False,
        token=False, card_id="test"):
    return SimpleNamespace(
        object_id=oid, zone=zone, controller=0, tapped=tapped,
        token=token, types=frozenset(types),
        card=SimpleNamespace(name=name, card_id=card_id),
    )


class FakeMana:
    def __init__(self, kernel, modes):
        self.kernel, self._modes = kernel, modes
    def modes(self, item):
        return self._modes.get(item.object_id, ())
    def floating(self, seat):
        return (0, 0, 1, 0, 0, 0)


class ResourcePolicyTests(unittest.TestCase):
    def test_source_counts_do_not_multiply_modes(self):
        land = obj(1, "Swamp", types=("land",))
        rock = obj(2, "Sol Ring", types=("artifact",))
        treasure = obj(3, "Treasure", types=("artifact",), token=True,
                       card_id="reviewed-token:Treasure")
        tapped = obj(4, "Swamp", types=("land",), tapped=True)
        kernel = FakeKernel((land, rock, treasure, tapped))
        def mode(*output):
            return SimpleNamespace(output=output, activation_generic=0,
                                   activation_colors=(), life=0, damage=0)
        service = FakeMana(kernel, {
            1: (mode("B"),), 2: (mode("C", "C"),),
            3: (mode("B"), mode("R")), 4: (mode("B"),),
        })
        r = assess_resources(kernel, service)
        self.assertEqual((r.land_sources, r.rock_sources,
                          r.treasure_sources, r.floating_mana,
                          r.available_fixed_mana), (1, 1, 1, 1, 5))

    def test_tutor_considers_only_eligible_library_ids(self):
        rock = obj(7, "Generic Rock", zone="library", types=("artifact",))
        spell = obj(8, "Nonrock", zone="library", types=("sorcery",))
        kernel = FakeKernel((rock, spell))
        zones = SimpleNamespace(kernel=kernel, ids=lambda seat, zone: (7, 8))
        effect = SimpleNamespace(enter_tapped=False, mana_modes=(
            SimpleNamespace(output=("C", "C"), life=0, damage=0, sacrifice=False),
        ))
        with patch("commander_sim.resource_development.reviewed_rock",
                   side_effect=lambda name, raw, colors:
                       (effect, "{2}") if name == "Generic Rock" else None):
            self.assertEqual(choose_tutor_target(
                zones, 0, (8, 7), {"Generic Rock": {}, "Nonrock": {}},
                ("B",)), 7)
            self.assertEqual(choose_tutor_target(
                zones, 0, (8,), {"Generic Rock": {}, "Nonrock": {}},
                ("B",)), 8)
            with self.assertRaises(ValueError):
                choose_tutor_target(zones, 0, (999,), {}, ("B",))


if __name__ == "__main__":
    unittest.main()
