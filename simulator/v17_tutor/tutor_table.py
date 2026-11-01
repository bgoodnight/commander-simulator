"""Mystical Tutor library search on the channel-aware table."""
from pathlib import Path
from dataclasses import replace
from types import MappingProxyType
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v16_channel'))
from channel_table import ChannelTable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from commander_sim.legacy_tutor_ops import resolve_historical_search

class TutorTable(ChannelTable):
    def __init__(self, *args, **kwargs):
        self.tutor_events = []
        super().__init__(*args, **kwargs)
        key = 'named:Mystical Tutor'
        spec = self.zones.specs[key]
        self.zones.specs[key] = replace(spec, card_type='instant', effect='named_mystical_tutor',
                                        parameters=MappingProxyType({'coverage':'verified_subset'}))
        for obj in self.rules.objects.values():
            if obj.card.card_id == key:
                obj.card = replace(obj.card, types=frozenset({'instant'}), coverage='verified_subset')
        self.rules._dirty()
        self.register_effect('named_mystical_tutor', self.resolve_mystical_tutor)

    def resolve_mystical_tutor(self, table, action):
        return resolve_historical_search(self, action.actor, 'mystical_tutor')
