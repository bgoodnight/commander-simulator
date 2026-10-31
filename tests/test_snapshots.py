import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from commander_sim.snapshots import validate_snapshot

ROOT=Path(__file__).resolve().parents[1]
DECK=ROOT/'decklists/fixtures/magnus_flameslinger_v0_7_pre_delivery.txt'
SNAPSHOT=ROOT/'simulator/card_data/flameslinger_v0_7_scryfall.json'

class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(SNAPSHOT.read_text())

    def validate_modified(self, change):
        change(self.data)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'snapshot.json';path.write_text(json.dumps(self.data))
            return validate_snapshot(DECK,path)

    def test_authentic_deck_and_adventure_faces(self):
        result=validate_snapshot(DECK,SNAPSHOT)
        self.assertEqual(result.deck.count,100)
        self.assertEqual(len(result.cards),76)
        self.assertIn(('Library','Lindblum, Industrial Regency',1),result.deck.cards)
        self.assertEqual(result.deck.commander,'Magnus the Red')

    def test_non_adventure_front_face_alias_is_valid(self):
        text = DECK.read_text(encoding='utf-8')
        full = '1 Lindblum, Industrial Regency // Mage Siege'
        front = '1 Lindblum, Industrial Regency'
        self.assertIn(full, text)
        edited = text.replace(full, front)
        data = self.data
        entry = next(item for item in data['cards']
                     if item['deck_name'] == 'Lindblum, Industrial Regency // Mage Siege')
        entry['deck_name'] = 'Lindblum, Industrial Regency'
        entry['card']['layout'] = 'modal_dfc'
        data['deck_sha256'] = hashlib.sha256(edited.encode('utf-8')).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            deck_path = Path(tmp) / 'front_face.txt'
            snapshot_path = Path(tmp) / 'front_face.json'
            deck_path.write_text(edited, encoding='utf-8')
            snapshot_path.write_text(json.dumps(data), encoding='utf-8')
            result = validate_snapshot(deck_path, snapshot_path)
        self.assertIn(('Library', 'Lindblum, Industrial Regency', 1), result.deck.cards)
        self.assertEqual(result.deck.count, 100)

    def test_rejects_wrong_deck_hash_and_incomplete_fetch(self):
        for change in (lambda d:d.update(deck_sha256='bad'),
                       lambda d:d.update(problems=[{'name':'missing'}]),
                       lambda d:d.update(distinct_requested=77)):
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.validate_modified(change)
            self.setUp()

    def test_outside_identity_and_invalid_metadata_fail_closed(self):
        for change in (lambda c:c.update(color_identity=['G']),lambda c:c.pop('oracle_id'),
                       lambda c:c.update(legalities={'commander':'banned'})):
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.validate_modified(lambda d:change(d['cards'][1]['card']))
            self.setUp()

    def test_unmatched_card_name_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'name mismatch'):
            self.validate_modified(lambda d:d['cards'][0].update(deck_name='Unknown'))

if __name__=='__main__':unittest.main()
