import unittest
from tools.select_gorge_precon_panel import report, select, quantile, summary


def make_row(i):
    colors=(["B"] if i%3==0 else ["U","R"] if i%3==1 else ["G"])
    return {
        "key":f"deck-{i:03}", "name":f"Deck {i}", "commander":f"Commander {i}",
        "color_identity":colors,"release_date":f"{2011+i%15}-01-01",
        "card_name_coverage":1.0 if i%7 else .97,
        "cards_resolved":100 if i%7 else 97,
        "nonland_mean_mana_value":2+(i%5)/2,
        "counts":{"creatures":15+i%35,"lands":34+i%8,
                  "token_text_proxy":i%12,"counterspell_text_proxy":i%5},
        "is_duplicate_variant":False,"active_opponent":False,
    }


class PanelTests(unittest.TestCase):
    def test_quantiles(self):
        self.assertEqual(quantile([3,1,2],.5),2)
        self.assertEqual(quantile([1,3],.5),2)

    def test_select_distinct_and_reproducible(self):
        rows=[make_row(i) for i in range(110)]
        a,_=select(rows,20)
        b,_=select(list(reversed(rows)),20)
        self.assertEqual([r["key"] for r in a],[r["key"] for r in b])
        self.assertEqual(len({r["key"] for r in a}),20)
        self.assertEqual({tuple(r["color_identity"]) for r in a},
                         {("B",),("U","R"),("G",)})
        self.assertTrue(all(not r["active_opponent"] for r in a))

    def test_summary_distribution_counts(self):
        rows=[make_row(i) for i in range(100)]
        d=summary(rows)
        self.assertEqual(d["creatures"]["n"],100)
        self.assertGreater(d["creatures"]["p90"],d["creatures"]["p10"])
        self.assertLessEqual(d["counterspell_text_proxy"]["positive"],100)

    def test_report_does_not_activate_or_certify(self):
        rows=[make_row(i) for i in range(104)]
        payload={"schema":"gorge-precon-card-metadata-enrichment-v1",
                 "decks":rows,"oracle_bulk_sha256":"fixture","source_catalog_commit":"abc",
                 "as_of":"2026-11-05"}
        res=report(payload,panel_size=20)
        self.assertEqual(len(res["shortlist"]),20)
        self.assertEqual(res["status"],"provisional_not_gorge_qualified")
        self.assertEqual(len(res["unresolved_candidates"]),15)
        self.assertIn("all_candidate_feature_distribution",res)

    def test_fail_closed_on_wrong_schema_and_active_opponent(self):
        payload={"schema":"gorge-precon-card-metadata-enrichment-v1",
                 "decks":[make_row(i) for i in range(101)],
                 "oracle_bulk_sha256":"fixture","source_catalog_commit":"abc",
                 "as_of":"2026-11-05"}
        payload["decks"][0]["active_opponent"]=True
        with self.assertRaisesRegex(ValueError,"activate"):
            report(payload,20)


if __name__=="__main__":
    unittest.main()
