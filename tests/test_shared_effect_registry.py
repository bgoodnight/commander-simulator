"""Shared effect catalog does not duplicate or broaden execution authority."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.named_effect_coverage import REGISTRATIONS, named_effect_coverage
from commander_sim.shared_effect_registry import (
    EFFECT_FAMILIES, effect_registrations, named_registrations,
    operation_index, registered_sources)


class SharedEffectCatalogTests(unittest.TestCase):
    def test_all_registered_operations_have_exactly_one_family(self):
        sources=dict(registered_sources())
        groups=[kind for kinds in EFFECT_FAMILIES.values() for kind in kinds]
        self.assertEqual(len(groups),len(set(groups)))
        self.assertEqual(set(sources),set(groups))
        self.assertEqual(len(sources),len(operation_index()))

    def test_coverage_report_consumes_shared_registrations(self):
        self.assertEqual(REGISTRATIONS,named_registrations())
        report=named_effect_coverage()
        self.assertEqual(report["shared_effect_family_count"],
                         len(EFFECT_FAMILIES))
        self.assertEqual(report["shared_effect_operation_count"],
                         len(operation_index()))
        self.assertEqual(report["full_card_coverage_confirmed"],0)
        self.assertTrue(all(row["status"] in {"partial","not_registered"}
            for deck in report["decks"].values()
            for row in deck["cards"].values()))

    def test_bindings_are_source_pinned_for_all_six_deck_variants(self):
        by_identity={(entry.name,entry.oracle_id)
                     for entry in effect_registrations()}
        report=named_effect_coverage()
        for fixture in FIXTURES:
            for name,row in report["decks"][fixture.key]["cards"].items():
                if row["reviewed_suboperations"]:
                    self.assertIn((name,row["oracle_id"]),by_identity)
                else:
                    self.assertNotIn((name,row["oracle_id"]),by_identity)

    def test_cross_deck_effect_family_reuse_is_measurable(self):
        report=named_effect_coverage()
        families=report["shared_effect_families"]
        for family in ("mana_and_cost","triggers_and_timing",
                       "zone_and_graveyard","activated_and_attachments"):
            self.assertGreater(families[family]["deck_variant_count"],1)
        for name,stats in families.items():
            self.assertEqual(stats["deck_variant_count"],
                             len(stats["deck_variants"]))
            self.assertEqual(stats["deck_variants"],
                             tuple(sorted(set(stats["deck_variants"]))))

    def test_same_card_can_have_several_independent_effect_slots(self):
        report=named_effect_coverage()
        # Shard has distinct attack and artifact-departure registrations.
        necron=report["decks"]["necron_dynasties"]["cards"]
        operations=set(necron["Shard of the Void Dragon"]["reviewed_suboperations"])
        self.assertIn("attack_zone_trigger",operations)
        self.assertIn("artifact_departure_trigger",operations)
        self.assertEqual(necron["Shard of the Void Dragon"]["status"],"partial")

    def test_registry_is_reproducible_and_read_only(self):
        a=tuple((x.operation,x.oracle_id,x.name,x.family)
                for x in effect_registrations())
        b=tuple((x.operation,x.oracle_id,x.name,x.family)
                for x in effect_registrations())
        self.assertEqual(a,b)
        with self.assertRaises(TypeError):
            EFFECT_FAMILIES["new"]="unexpected"
        with self.assertRaises(TypeError):
            operation_index()["new"]=()


if __name__=="__main__":
    unittest.main()
