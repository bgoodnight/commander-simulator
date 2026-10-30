"""Hand-based channel abilities on the shared priority stack."""
from pathlib import Path
from dataclasses import dataclass, replace
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v15_utility'))
from utility_table import UtilityTable
from priority import Choice
from gameplay import PriorityBattlefield
from rules import Event
from channel_costs import channel_cost

@dataclass(frozen=True)
class ChannelAbility:
    name: str
    @property
    def key(self): return 'channel_' + self.name.split(',')[0].lower()

OTAWARA = ChannelAbility('Otawara, Soaring City')
SOKENZAN = ChannelAbility('Sokenzan, Crucible of Defiance')
ABILITIES = {a.name: a for a in (OTAWARA, SOKENZAN)}
TARGET_TYPES = frozenset({'artifact','creature','enchantment','planeswalker'})

class ChannelBattlefield(PriorityBattlefield):
    def _definition(self, name, power, toughness, keywords, kind='creature', engine=False):
        card = super()._definition(name, power, toughness, keywords, kind, engine)
        return replace(card, subtypes=frozenset({'Spirit'})) if name == 'Spirit' and kind == 'creature' else card

class ChannelTable(UtilityTable):
    battlefield_class = ChannelBattlefield

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The historical Baral definition omitted its legendary supertype.
        name = 'Baral, Chief of Compliance'
        definition = self.upgraded_definitions[name]
        definition = replace(definition, supertypes=definition.supertypes | {'legendary'})
        self.upgraded_definitions[name] = definition
        for obj in self.rules.objects.values():
            if obj.card.name == name:
                obj.card = replace(obj.card, supertypes=obj.card.supertypes | {'legendary'})
        self.rules._dirty()
    def channel_target_legal(self, seat, target):
        return target in self.rules.objects and self.rules.legal_target(seat, target, TARGET_TYPES)

    def channel_available(self, seat, oid, ability, target=None):
        obj = self.rules.objects.get(oid)
        if not obj or obj.zone != 'hand' or obj.owner != seat or obj.card.name != ability.name:
            return False
        if ability == OTAWARA and not self.channel_target_legal(seat, target): return False
        if ability == SOKENZAN and target is not None: return False
        cost = channel_cost(ability.name, self.rules.controlled(seat))
        return self.resources.plan(seat, cost) is not None

    def priority_choices(self, seat):
        choices = list(super().priority_choices(seat))
        for oid in self.zones.ids(seat, 'hand'):
            ability = ABILITIES.get(self.rules.get(oid).card.name)
            if not ability: continue
            targets = [o.object_id for o in self.rules.on_battlefield()] if ability == OTAWARA else [None]
            for target in targets:
                if self.channel_available(seat, oid, ability, target):
                    choices.append(Choice('channel', source_id=oid, ability=ability, target_frame=target))
        return tuple(choices)

    def choose_priority(self, seat, choices):
        selected = super().choose_priority(seat, choices)
        if selected is not None: return selected
        if seat == self.active_seat and self.phase == 'main' and not self.spell_stack.frames:
            return next((c for c in choices if c.kind == 'channel' and
                         (c.ability == SOKENZAN or self.rules.get(c.target_frame).controller != seat)), None)
        return None

    def commit_choice(self, seat, choice):
        if choice.kind != 'channel': return super().commit_choice(seat, choice)
        if self.spell_stack.resolving or self.spell_stack.holder != seat: raise ValueError('No priority')
        if not self.channel_available(seat, choice.source_id, choice.ability, choice.target_frame):
            raise ValueError('Illegal channel activation')
        cost = channel_cost(choice.ability.name, self.rules.controlled(seat))
        self.resources.pay(seat, cost)
        self.zones.move(choice.source_id, 'graveyard', 'discard')
        self.spell_stack.activated(seat, choice.source_id, choice.ability, choice.target_frame, choice.ability.key)
        self.rules.events.append(Event('ability_activated', seat, choice.source_id))
        self.emit('ability_activated', controller=seat, source_id=choice.source_id, ability=choice.ability.key)

    def resolve_activation(self, frame):
        if frame.ability not in (OTAWARA, SOKENZAN): return super().resolve_activation(frame)
        if frame.ability == OTAWARA:
            if not self.channel_target_legal(frame.controller, frame.target_frame): return False
            self.world.move(frame.target_frame, 'hand', 'bounce')
        else:
            for _ in range(2):
                self.add_creature(self.players[frame.controller], 1, 1, 'Spirit', token=True, keywords=('haste',))
        self.rules.events.append(Event('ability_resolved', frame.controller, frame.source_id))
        self.emit('ability_resolved', controller=frame.controller, source_id=frame.source_id, ability=frame.ability.key)
        return True
