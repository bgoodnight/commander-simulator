"""Older v9c-v35 rock sources now derive from the same reviewed templates."""
import unittest
from dataclasses import dataclass

from commander_sim.legacy_mana_adapter import reviewed_legacy_rock_modes


@dataclass(frozen=True)
class FakeCost:
    generic: int = 0
    blue: int = 0
    red: int = 0


@dataclass(frozen=True)
class FakeAbility:
    output: tuple
    cost: FakeCost = FakeCost()
    life: int = 0
    damage: int = 0
    sacrifice: bool = False


def modes(name):
    return reviewed_legacy_rock_modes(name, FakeAbility, FakeCost)


class LegacyRockMigrationTests(unittest.TestCase):
    def test_sol_ring_two_true_colorless(self):
        self.assertEqual(modes("Sol Ring"), (FakeAbility((2,0,0)),))

    def test_izzet_signet_funding_cost_and_output(self):
        self.assertEqual(modes("Izzet Signet"), (
            FakeAbility((0,1,1),FakeCost(generic=1)),))

    def test_arcane_signet_respects_old_ur_identity(self):
        self.assertEqual(modes("Arcane Signet"), (
            FakeAbility((0,1,0)),FakeAbility((0,0,1))))

    def test_mind_stone_single_colorless(self):
        self.assertEqual(modes("Mind Stone"), (FakeAbility((1,0,0)),))

    def test_talisman_damage_is_preserved(self):
        self.assertEqual(modes("Talisman of Creativity"), (
            FakeAbility((1,0,0)), FakeAbility((0,1,0),damage=1),
            FakeAbility((0,0,1),damage=1)))

    def test_unknown_rock_is_not_automatically_supported(self):
        self.assertIsNone(modes("Untested Ramp Artifact"))

    def test_unavailable_black_mana_fails_closed_in_legacy_engine(self):
        with self.assertRaises(NotImplementedError):
            modes("Charcoal Diamond")


if __name__=="__main__":
    unittest.main()
