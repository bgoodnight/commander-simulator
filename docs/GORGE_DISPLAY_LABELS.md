# Results display labels

Simulation deck keys, archetype keys and model feature identifiers are stable
source identifiers. Never change them merely to alter how a label appears.

Before adding a deck or archetype to `data/commander_deck_library.json`, add its
reviewed display name to `data/gorge_display_labels.json`. The entries map deck
keys to the deck's public name; the separately curated commander metadata remains
a card name. Keep punctuation and capitalization faithful to the source. Add a
predictor-family template when a new model feature family is introduced.

The Pages build validates the catalog and the generated cohort report against
this registry and stops if a displayed deck, archetype, color, or predictor family
is missing a label. It writes a small cache-versioned presentation data file and
loads the common formatting helpers before the results render. UI helpers preserve
source IDs and provide a readable fallback for old local or incomplete recordings;
the fallback is not an approved label and does not bypass the publication check.

Run `python -m unittest tests.test_gorge_display_labels` and
`node --test tests/pages_display_names.test.cjs`, then build Pages with
`python tools/build_pages_deck_lab.py --output <directory>`. If a new modeling
contract requires different parsing or derived interaction labels, extend both the
validator and presentation helpers together and cover the new shape in tests.
