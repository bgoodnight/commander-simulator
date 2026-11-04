"""Public gorge snapshot projection: 40 life and hidden-information safeguards."""
import unittest
from tools.gorge_public_state import project
from tools.gorge_ui_export import convert


def fixture():
    objects=[{"object_id":i,"card_name":f"Card {i}",
              "effective_name":f"Card {i}","is_token":False}
             for i in range(1,401)]
    players=[]
    for seat in range(4):
        base=seat*100
        players.append({"seat":seat,"life":40,"lost":False,
            "mana_pool":[0,1,0,0,0,0],
            "zones":{"hand":[base+2,base+3],"library":[base+4,base+5],
                     "battlefield":[base+6],"graveyard":[],
                     "exile":[],"command":[base+1]}})
    return {
        "schema":"gorge-native-trace-v1",
        "enrichment_schema":"gorge-physical-state-v1",
        "engine":"gorge","format":"commander","seed":300,
        "chain":"test-chain","decks":["a","b","c","d"],
        "policies":["bot"]*4,"objects":objects,
        "snapshots":[{"turn":1,"active_seat":0,
                      "boundary":"first_pending_decision_of_turn",
                      "step":"upkeep","after_event_seq":5,
                      "players":players}],
        "log":{"events":[{"seq":0,"kind":0,"amount":4},
                         {"seq":1,"kind":9,"amount":1,"player":0},
                         {"seq":2,"kind":11,"obj":6,"text":"Card 6"}],
               "intents":[]},
    }


class PublicGorgeStateTest(unittest.TestCase):
    def test_public_zone_names_and_counts(self):
        data=project(fixture())
        self.assertEqual(data[0]["boundary"],"first_pending_decision_of_turn")
        self.assertEqual(data[0]["players"][0]["life"],40)
        self.assertEqual(data[0]["players"][0]["hand_count"],2)
        self.assertEqual(data[0]["players"][0]["library_count"],2)
        self.assertEqual(data[0]["players"][0]["zones"]["battlefield"][0]["name"],"Card 6")
        self.assertEqual(data[0]["players"][0]["mana_pool"],[0,1,0,0,0,0])
        self.assertNotIn("hand",data[0]["players"][0]["zones"])
        self.assertNotIn("library",data[0]["players"][0]["zones"])
        output=convert(fixture())
        self.assertEqual(output["snapshot_definition"],"first_pending_decision_of_turn")
        self.assertIn("snapshots",output)
        self.assertFalse(any(card["name"]=="Card 2"
            for snap in output["snapshots"] for player in snap["players"]
            for cards in player["zones"].values() for card in cards))

    def test_explicit_omniscient_snapshot_has_named_hands_for_all_four_bots(self):
        raw=fixture()
        projected=project(raw,include_hidden=True)
        self.assertEqual(projected[0]["players"][0]["zones"]["hand"][0]["name"],"Card 2")
        self.assertEqual(projected[0]["players"][1]["zones"]["hand"][0]["name"],"Card 102")
        self.assertEqual([c["name"] for c in projected[0]["players"][0]["zones"]["library"]],
                         ["Card 4","Card 5"])
        view=convert(raw,include_hidden=True)
        self.assertEqual(view["visibility"],"omniscient")
        self.assertEqual(view["state"]["hands"],"named_turn_entry_snapshots")
        self.assertEqual(view["snapshots"][0]["players"][3]["zones"]["hand"][1]["name"],"Card 303")
        self.assertNotIn("objects",view)
        self.assertNotIn("log",view)
        self.assertNotIn("intents",view)

    def test_20_life_game_is_not_valid_commander_benchmark(self):
        data=fixture()
        for player in data["snapshots"][0]["players"]:
            player["life"]=20
        with self.assertRaisesRegex(ValueError,"40-life"):
            project(data)

    def test_duplicate_physical_object_is_rejected(self):
        data=fixture()
        data["snapshots"][0]["players"][0]["zones"]["graveyard"]=[6]
        with self.assertRaisesRegex(ValueError,"duplicated"):
            project(data)

    def test_public_payload_does_not_carry_hidden_identifiers(self):
        output=convert(fixture())
        player=output["snapshots"][0]["players"][0]
        self.assertEqual(set(player["zones"]),
                         {"battlefield","graveyard","exile","command"})
        self.assertFalse(any(e.get("secret") for t in output["turns"]
                             for e in t["events"]))
        self.assertNotIn("intents",output)
        self.assertNotIn("objects",output)


if __name__=="__main__":
    unittest.main()
