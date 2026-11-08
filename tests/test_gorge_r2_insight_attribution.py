import unittest

from tools.gorge_r2_insight_evidence import verify_hero_attribution


class NativeInsightAttributionTests(unittest.TestCase):
    def test_opponent_spell_cannot_be_counted_as_mortarion_play(self):
        deck = {"cards": [
            {"name": "Sol Ring", "oracle_id": "1"},
            {"name": "Phyrexian Altar", "oracle_id": "2"},
        ]}
        cards = {"1": {"face_names": []}, "2": {"face_names": []}}
        features = {"categories": {
            "played": [{"name": "Sol Ring"}, {"name": "Exclude"}],
            "activated": [{"name": "Phyrexian Altar"}]
        }}
        with self.assertRaisesRegex(ValueError, "Opponent or unknown card"):
            verify_hero_attribution(features, deck, cards)
        features["categories"]["played"].pop()
        verify_hero_attribution(features, deck, cards)

    def test_alternate_face_name_is_allowed(self):
        deck = {"cards": [{"name": "Front Face", "oracle_id": "1"}]}
        cards = {"1": {"face_names": ["Back Face"]}}
        verify_hero_attribution({"categories": {
            "played": [{"name": "Back Face"}]}}, deck, cards)


if __name__ == "__main__":
    unittest.main()
