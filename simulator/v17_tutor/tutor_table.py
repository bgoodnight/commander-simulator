"""Mystical Tutor library search on the channel-aware table."""
from pathlib import Path
from dataclasses import replace
from types import MappingProxyType
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v16_channel'))
from channel_table import ChannelTable

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
        seat = action.actor
        eligible = tuple(oid for oid in self.zones.ids(seat, 'library')
                         if self.rules.get(oid).types & {'instant','sorcery'})
        request = self.selection.request('mystical_tutor', seat, eligible)
        ranked = sorted(request.cards, key=lambda c: -self.selection.score(seat, c))
        default = ranked[0].object_id if ranked else None
        policy = getattr(self, 'tutor_policy', None)
        chosen = policy(request) if policy else default
        if chosen is not None and chosen not in eligible:
            raise ValueError('Mystical Tutor must select an instant or sorcery in the library, or fail to find')
        name = self.rules.get(chosen).card.name if chosen is not None else None
        self.zones.shuffle(seat)
        if chosen is not None:
            order = self.zones.order[seat, 'library']
            order.remove(chosen); order.append(chosen)
            self.rules._dirty()
        self.tutor_events.append(('mystical_tutor', seat, chosen, name))
        self.note(f'    MYSTICAL TUTOR P{seat}: revealed {name}; shuffled, then placed on top.')
