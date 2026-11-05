"""Publication rejects missing UI names before users see internal IDs."""
import copy
import unittest
from tools.gorge_display_labels import load_labels, validate_labels

class DisplayLabelsTest(unittest.TestCase):
    def setUp(self):
        self.labels = load_labels()
        self.library = {'decks':[{'key':'cavalry-charge'}], 'allowed_archetypes':['face_down']}

    def test_missing_deck_and_archetype_labels_fail_closed(self):
        for section, key in [('decks','cavalry-charge'), ('archetypes','face_down')]:
            labels = copy.deepcopy(self.labels)
            del labels[section][key]
            with self.assertRaisesRegex(ValueError, 'Missing human-readable'):
                validate_labels(labels, self.library)

    def test_unknown_model_feature_rejected_before_publication(self):
        report = {'decks':{'cavalry-charge':{'groups':{}, 'regressions':{
            'test':{'predictors':[{'feature':'future_predictor:foo'}]}}}}}
        with self.assertRaisesRegex(ValueError, 'Missing predictor display template'):
            validate_labels(self.labels, self.library, report)
        report['decks']['cavalry-charge']['regressions']['test']['predictors'] = [
            {'feature':'opponent:cavalry-charge'}, {'feature':'color:U'}, {'feature':'seat:2'}]
        validate_labels(self.labels, self.library, report)

if __name__ == '__main__':
    unittest.main()
