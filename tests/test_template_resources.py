"""Physical source payments from generic rock modes never create extra cards."""
import unittest
from types import SimpleNamespace

from commander_sim.template_resources import TemplateManaService


SOL = {"oracle_id": "6ad8011d-3471-4369-9d68-b264cc027487",
       "oracle_text": "{T}: Add {C}{C}.", "type_line": "Artifact",
       "mana_cost": "{1}", "layout": "normal"}
ARCANE = {"oracle_id": "0bc7f093-bef0-4f1a-852c-4b75ebf54838",
          "oracle_text": "{T}: Add one mana of any color in your commander's color identity.",
          "type_line": "Artifact", "mana_cost": "{2}", "layout": "normal"}
SIGNET = {"oracle_id": "2fda4fe7-8b0c-489c-a000-6d358e614e34",
          "oracle_text": "{1}, {T}: Add {U}{R}.",
          "type_line": "Artifact", "mana_cost": "{2}", "layout": "normal"}
DIAMOND = {"oracle_id": "1386d111-a2a7-4df1-91d7-947664126989",
           "oracle_text": "This artifact enters tapped.\n{T}: Add {B}.",
           "type_line": "Artifact", "mana_cost": "{2}", "layout": "normal"}


class FakeKernel:
    def __init__(self):
        self.objects = {}
        self.revision = 0
    def get(self, oid):
        return self.objects[oid]
    def _dirty(self):
        self.revision += 1


class TemplateResourceTests(unittest.TestCase):
    def setUp(self):
        self.k = FakeKernel()
        self.r = TemplateManaService(self.k, {
            "Sol Ring": SOL, "Arcane Signet": ARCANE,
            "Izzet Signet": SIGNET, "Charcoal Diamond": DIAMOND,
        }, {"U", "R"})

    def source(self, oid, name, *, tapped=False, controller=0, zone="battlefield"):
        self.k.objects[oid] = SimpleNamespace(
            object_id=oid, zone=zone, controller=controller, tapped=tapped,
            types=frozenset({"land"} if name in {"Island", "Mountain", "Swamp"}
                            else {"artifact"}), card=SimpleNamespace(name=name))
        return oid

    def test_sol_ring_pays_one_and_floats_excess_then_clears(self):
        self.source(1, "Sol Ring")
        result = self.r.pay(0, "{1}")
        self.assertEqual(result.source_ids, (1,))
        self.assertEqual(self.r.floating(), (0, 0, 0, 0, 0, 1))
        self.assertTrue(self.k.get(1).tapped)
        result = self.r.pay(0, "{1}")
        self.assertEqual(result.source_ids, ())
        self.assertEqual(self.r.floating(), (0, 0, 0, 0, 0, 0))
        self.r.clear()

    def test_signet_cannot_fund_itself(self):
        self.source(1, "Izzet Signet")
        self.assertIsNone(self.r.plan(0, "{U}"))
        self.source(2, "Island")
        payment = self.r.pay(0, "{U}{R}")
        self.assertEqual(payment.source_ids, (2, 1))
        self.assertTrue(self.k.get(1).tapped)

    def test_colored_mana_is_not_invented_by_sol_ring(self):
        self.source(1, "Sol Ring")
        self.assertIsNone(self.r.plan(0, "{U}"))
        self.assertIsNone(self.r.plan(0, "{B}"))

    def test_arcane_signet_modes_restricted_to_commander_identity(self):
        self.source(1, "Arcane Signet")
        self.assertIsNotNone(self.r.plan(0, "{U}"))
        self.assertIsNotNone(self.r.plan(0, "{R}"))
        self.assertIsNone(self.r.plan(0, "{B}"))

    def test_tapped_rock_and_opponent_lands_excluded(self):
        self.source(1, "Charcoal Diamond", tapped=True)
        self.source(2, "Island", controller=1)
        self.assertIsNone(self.r.plan(0, "{B}"))
        self.assertIsNone(self.r.plan(0, "{U}"))

    def test_planning_is_pure_and_fail_closed(self):
        self.source(1, "Island")
        before = self.k.revision
        self.assertIsNotNone(self.r.plan(0, "{U}"))
        self.assertEqual(before, self.k.revision)
        self.assertFalse(self.k.get(1).tapped)
        with self.assertRaises(ValueError):
            self.r.plan(0, "{X}")
        self.assertFalse(self.k.get(1).tapped)

    def test_undocumented_rock_cannot_generate_mana(self):
        self.source(1, "Mysterious Rock")
        self.assertIsNone(self.r.plan(0, "{1}"))


if __name__ == "__main__":
    unittest.main()
