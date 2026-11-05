"""Validate UI labels independently of stable simulation and model identifiers."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / 'data/gorge_display_labels.json'
LIBRARY = ROOT / 'data/commander_deck_library.json'

def validate_labels(labels, library, report=None):
    if labels.get('schema') != 'gorge-display-labels-v1':
        raise ValueError('Invalid Gorge display-label schema')
    def require(section, key):
        label = labels.get(section, {}).get(key)
        if not isinstance(label, str) or not label.strip() or label == key:
            raise ValueError(f'Missing human-readable {section} label for {key}')
    for deck in library.get('decks', []):
        require('decks', deck['key'])
    for kind in library.get('allowed_archetypes', []):
        require('archetypes', kind)
    for color in 'WUBRG':
        require('colors', color)
    for family in ('opponent', 'archetype', 'color', 'seat'):
        template = labels.get('predictor_families', {}).get(family)
        if not isinstance(template, str) or template.count('{value}') != 1:
            raise ValueError(f'Missing predictor display template for {family}')
    if report:
        for player, data in report.get('decks', {}).items():
            require('decks', player)
            for section, kind in (('opponents','decks'), ('archetypes','archetypes'), ('colors','colors')):
                for group in data.get('groups', {}).get(section, []):
                    require(kind, group['name'])
            for fit in data.get('regressions', {}).values():
                for item in fit.get('predictors', []):
                    for feature in item['feature'].split(' × '):
                        family, sep, key = feature.partition(':')
                        template = labels.get('predictor_families', {}).get(family)
                        if not sep or not template or template.count('{value}') != 1:
                            raise ValueError(f'Missing predictor display template for {feature}')
                        section = {'opponent':'decks', 'archetype':'archetypes', 'color':'colors'}.get(family)
                        if section:
                            require(section, key)
                        elif family == 'seat' and key not in ('1','2','3','4'):
                            raise ValueError(f'Invalid player seat {key}')
    return labels

def load_labels():
    labels = json.loads(LABELS.read_text(encoding='utf-8'))
    library = json.loads(LIBRARY.read_text(encoding='utf-8'))
    return validate_labels(labels, library)
