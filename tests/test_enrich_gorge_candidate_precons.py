"""Offline fixtures for candidate enrichment and safety boundaries."""
import json
import tempfile
import unittest
from pathlib import Path
from tools.enrich_gorge_candidate_precons import build_index, card_metrics, decode_bulk, enrich


def card(name, types, colors=(), text="", cmc=2, keywords=()):
    return {"name":name,"oracle_id":"id:"+name,"lang":"en","type_line":types,
            "color_identity":list(colors),"oracle_text":text,
            "cmc":cmc,"keywords":list(keywords),"layout":"normal"}


class CandidateEnrichmentTests(unittest.TestCase):
    def test_lookup_filters_and_ambiguous(self):
        a=card("Alpha","Creature",["G"])
        b=card("Alpha","Land",[])
        b["oracle_id"]="different-oracle-identity"
        index,ambiguous=build_index([a,b,card("Beta","Land"),{"name":"Token","layout":"token"}])
        self.assertIn("alpha",ambiguous)
        self.assertNotIn("alpha",index)
        self.assertIn("beta",index)
        self.assertNotIn("token",index)

    def test_exact_name_wins_over_card_face_alias(self):
        standalone=card("Brainstorm","Instant",["U"])
        alternate=card("Mage // Brainstorm","Creature",["U"])
        alternate["card_faces"]=[{"name":"Mage"},{"name":"Brainstorm"}]
        lookup,ambiguous=build_index([alternate,standalone])
        self.assertEqual(lookup["brainstorm"]["oracle_id"],standalone["oracle_id"])
        self.assertNotIn("brainstorm",ambiguous)

    def test_conservative_mechanic_flags(self):
        m=card("One","Artifact",[], "Tap: Add {C}. Draw a card. Create a 1/1 colorless Servo artifact creature token.",1)
        flags=card_metrics(m)
        self.assertIn("mana_rocks_proxy",flags)
        self.assertIn("draw_text_proxy",flags)
        self.assertIn("token_text_proxy",flags)
        self.assertIn("artifacts",flags)

    def test_fixture_enrichment_without_network(self):
        with tempfile.TemporaryDirectory() as td:
            catalog=Path(td)/"catalog.json"
            deck={"key":"example-2020","name":"Example","commander":"Test Commander",
                  "set_code":"abc","release_date":"2020-01-01",
                  "qualification":"not_evaluated","provenance":"stock_precon_candidate",
                  "cards":[{"name":"Test Commander","count":1},{"name":"Forest","count":99}]}
            catalog.write_text(json.dumps({
                "schema":"gorge-stock-candidate-catalog-v1",
                "source":{"commit":"abc","file":"decks_v2.json"},
                "decks":[dict(deck, key="example-"+str(i)) for i in range(100)]
            }))
            bulk=json.dumps([card("Test Commander","Legendary Creature",["G"]),
                             card("Forest","Basic Land",["G"],cmc=0)]).encode()
            result=enrich(catalog,bulk)
            self.assertEqual(result["distinct_decklists"],1)
            self.assertEqual(result["complete_deck_resolution"],1)
            self.assertEqual(result["color_identity_distribution"],{"G":1})
            self.assertEqual(result["decks"][0]["counts"]["lands"],99)
            self.assertEqual(result["decks"][0]["counts"]["creatures"],1)
            self.assertFalse(result["decks"][0]["active_opponent"])
            self.assertIsNone(result["decks"][0]["primary_archetype"])
            # Missing card metadata cannot silently create complete coverage.
            missing=enrich(catalog,json.dumps([card("Test Commander","Legendary Creature",["G"])]).encode())
            self.assertEqual(missing["decks"][0]["cards_resolved"],1)
            self.assertEqual(missing["unresolved_card_name_count"],1)

    def test_gzip_jsonl(self):
        import gzip
        raw=gzip.compress((json.dumps(card("A","Land"))+"\n"+json.dumps(card("B","Creature"))+"\n").encode())
        self.assertEqual(len(decode_bulk(raw)),2)


if __name__=="__main__":unittest.main()
