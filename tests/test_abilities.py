"""P0.65 pure selection contracts; no live card mechanics claimed."""
import unittest

from commander_sim.abilities import (
    AbilityCatalog, AbilityHandler, AbilityKey, AbilitySlot, Fidelity, Mode,
)


class AbilityCompositionTests(unittest.TestCase):
    def setUp(self):
        self.catalog = AbilityCatalog()
        self.tutor = AbilityKey("oracle-tutor", "front", "search")
        self.keyword = AbilityKey("oracle-creature", "front", "double_strike")
        self.etb = AbilityKey("oracle-creature", "front", "etb")
        for key, kind in ((self.tutor, "spell"), (self.keyword, "keyword"),
                          (self.etb, "triggered")):
            self.catalog.register_slot(AbilitySlot(key, kind))

    def simplified(self, key=None, *, caps=frozenset()):
        return AbilityHandler(key or self.tutor, Fidelity.SIMPLIFIED,
                              "common.search_creature", "reviewed-v1",
                              required_capabilities=caps,
                              assumptions=("Search restrictions simplified to creatures",),
                              reviewed=True)

    def exact(self, key=None, *, operation="card.tutor_exact", caps=frozenset()):
        return AbilityHandler(key or self.tutor, Fidelity.EXACT,
                              operation, "oracle-review-v2",
                              required_capabilities=caps)

    def test_hybrid_fallback_and_strict_fail_closed(self):
        simple = self.simplified()
        self.catalog.register_handler(simple)
        self.assertIs(self.catalog.resolve(self.tutor, Mode.HYBRID).handler, simple)
        self.assertIsNone(self.catalog.resolve(self.tutor, Mode.STRICT).handler)
        self.assertEqual(self.catalog.resolve(self.tutor, Mode.STRICT).reason, "unsupported")
        self.assertIsNone(self.catalog.resolve(self.tutor, Mode.OBSERVATION).handler)

    def test_promoted_exact_replaces_only_its_simplified_slot(self):
        simple = self.simplified()
        self.catalog.register_handler(simple)
        other_keyword = self.exact(self.keyword, operation="rules.double_strike")
        other_etb = self.simplified(self.etb)
        self.catalog.register_handler(other_keyword)
        self.catalog.register_handler(other_etb)
        self.assertEqual(self.catalog.resolve(self.tutor, "hybrid").handler, simple)
        promoted = self.exact()
        self.catalog.register_handler(promoted)
        self.catalog.freeze()
        self.assertIs(self.catalog.resolve(self.tutor, "hybrid").handler, promoted)
        self.assertIs(self.catalog.resolve(self.tutor, "strict").handler, promoted)
        self.assertIs(self.catalog.resolve(self.keyword, "hybrid").handler, other_keyword)
        self.assertIs(self.catalog.resolve(self.etb, "hybrid").handler, other_etb)
        self.assertIsNone(self.catalog.resolve(self.etb, "strict").handler)

    def test_missing_shared_capability_blocks_or_selects_reviewed_fallback(self):
        self.catalog.register_handler(self.exact(caps=frozenset({"advanced_search"})))
        self.catalog.register_handler(self.simplified(caps=frozenset({"ordinary_search"})))
        self.assertIsNone(self.catalog.resolve(self.tutor, Mode.STRICT).handler)
        self.assertIsNone(self.catalog.resolve(self.tutor, Mode.HYBRID).handler)
        self.assertIs(
            self.catalog.resolve(self.tutor, Mode.HYBRID, {"ordinary_search"}).handler,
            self.catalog.resolve(self.tutor, Mode.HYBRID, frozenset({"ordinary_search"})).handler,
        )
        self.assertEqual(
            self.catalog.resolve(self.tutor, Mode.HYBRID, {"ordinary_search"}).handler.fidelity,
            Fidelity.SIMPLIFIED,
        )
        self.assertEqual(
            self.catalog.resolve(self.tutor, Mode.HYBRID, {"ordinary_search", "advanced_search"}).handler.fidelity,
            Fidelity.EXACT,
        )

    def test_slot_prerequisite_blocks_even_reviewed_simplified_behavior(self):
        key = AbilityKey("oracle-sacrifice", "front", "activated")
        self.catalog.register_slot(AbilitySlot(key, "activated", frozenset({"cost_payment"})))
        self.catalog.register_handler(self.simplified(key))
        self.assertEqual(self.catalog.resolve(key, Mode.HYBRID).reason, "missing_slot_capabilities")
        self.assertIsNone(self.catalog.resolve(key, Mode.HYBRID).handler)
        self.assertIsNotNone(self.catalog.resolve(key, Mode.HYBRID, {"cost_payment"}).handler)

    def test_unregistered_and_duplicate_handlers_are_rejected(self):
        self.catalog.register_handler(self.simplified())
        with self.assertRaises(ValueError):
            self.catalog.register_handler(self.simplified())
        with self.assertRaises(ValueError):
            self.catalog.register_slot(AbilitySlot(self.tutor, "spell"))
        with self.assertRaises(KeyError):
            self.catalog.register_handler(self.exact(AbilityKey("unknown", "front", "a1")))

    def test_unsafe_unreviewed_simplification_rejected(self):
        with self.assertRaisesRegex(ValueError, "review and assumptions"):
            AbilityHandler(self.tutor, Fidelity.SIMPLIFIED, "generic.search", "revision")
        with self.assertRaisesRegex(ValueError, "review and assumptions"):
            AbilityHandler(self.tutor, Fidelity.SIMPLIFIED, "generic.search", "revision",
                           assumptions=("not exact",), reviewed=False)

    def test_freeze_prevents_runtime_registry_mutation(self):
        self.catalog.freeze()
        with self.assertRaises(RuntimeError):
            self.catalog.register_handler(self.exact())
        with self.assertRaises(RuntimeError):
            self.catalog.register_slot(AbilitySlot(AbilityKey("new", "front", "a1"), "spell"))

    def test_unknown_mode_and_invalid_identity_rejected(self):
        with self.assertRaises(ValueError):
            self.catalog.resolve(self.tutor, "make_up_abilities")
        with self.assertRaises(ValueError):
            AbilityKey("", "front", "a1")
        with self.assertRaises(KeyError):
            self.catalog.resolve(AbilityKey("unknown", "front", "a1"), Mode.HYBRID)


if __name__ == "__main__":
    unittest.main()
