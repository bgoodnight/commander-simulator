import unittest
from commander_sim.decks import DeckProvider

class DeckProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = DeckProvider.bundled()

    def test_presets(self):
        for preset in ('premium', 'budget'):
            with self.subTest(preset=preset):
                deck = self.provider.preset(preset)
                self.assertEqual(deck.commander, 'Magnus the Red')
                self.assertEqual(deck.count, 100)
                self.assertEqual(sum(q for s, _, q in deck.cards if s == 'Library'), 99)

    def test_unknown_preset(self):
        with self.assertRaisesRegex(ValueError, 'Unknown deck preset'):
            self.provider.preset('invented')

    def test_missing_metadata_fails_closed(self):
        text = 'Commander\n1 Magnus the Red\nLibrary\n99 Unknown Card\n'
        with self.assertRaisesRegex(ValueError, 'Unverified card identity'):
            self.provider.parse(text)

    def test_duplicate_across_sections_rejected(self):
        text = 'Commander\n1 Magnus the Red\nLibrary\n1 Magnus the Red\n98 Island\n'
        with self.assertRaisesRegex(ValueError, 'Duplicate nonbasic'):
            self.provider.parse(text)

    def test_bad_count_and_commander(self):
        for text in ('Commander\n1 Magnus the Red\nLibrary\n98 Island',
                     'Commander\n1 Island\nLibrary\n99 Island'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.provider.parse(text)

    def test_missing_and_outside_identity(self):
        row = {'name':'Mystery', 'oracle_id':'a', 'type_line':'Creature',
               'color_identity':['B'], 'commander_legality':'legal'}
        records = list({r['name']: r for r in self.provider._records.values()}.values()) + [row]
        provider = DeckProvider(records)
        with self.assertRaisesRegex(ValueError, 'outside commander color identity'):
            provider.parse('Commander\n1 Magnus the Red\nLibrary\n1 Mystery\n98 Island')
        row.pop('color_identity')
        with self.assertRaisesRegex(ValueError, 'Incomplete card metadata'):
            DeckProvider([r for r in records if r['name'] != 'Mystery'] + [row]).parse(
                'Commander\n1 Magnus the Red\nLibrary\n1 Mystery\n98 Island')

    def test_parser_rejects_invalid_entries(self):
        for line in ('0 Island', '-1 Island', 'Island', '1 Island  ' + '\nBogus'):
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.provider.parse('Commander\n1 Magnus the Red\nLibrary\n' + line)

    def test_standalone_comments_are_allowed_but_not_card_entries(self):
        text = ('# Verified source and deck description\n'
                'Commander\n1 Magnus the Red\n'
                '# 100 physical cards including commander\n'
                'Library\n# Lands (99)\n99 Island\n')
        deck = self.provider.parse(text)
        self.assertEqual(deck.count, 100)
        self.assertIn(('Library', 'Island', 99), deck.cards)
        with self.assertRaisesRegex(ValueError, 'Invalid deck entry'):
            self.provider.parse(text + 'not a valid card entry\n')

    def test_descriptive_sections_and_adventure_oracle_name(self):
        text = ('Commander\n1 Magnus the Red\nCreatures (0)\n'
                'Lands (99)\n1 Lindblum, Industrial Regency // Mage Siege\n98 Island\n')
        deck = self.provider.parse(text)
        self.assertIn(('Library', 'Lindblum, Industrial Regency', 1), deck.cards)
        with self.assertRaisesRegex(ValueError, 'Section count'):
            self.provider.parse(text.replace('Lands (99)', 'Lands (98)'))

if __name__ == '__main__':
    unittest.main()
