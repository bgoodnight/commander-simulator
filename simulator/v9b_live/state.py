"""Live zone index and immutable pilot projections over the ONE game kernel.

Zone order contains IDs only. CardSpec is immutable definition metadata, never a
second hand/library inventory. All kernel add/move paths maintain the index,
including combat deaths, token creation and commander replacement recursion.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v9_kernel'))
from adapter import DeckProvider
from zones import KernelZones
from kernel import CentralKernel, Battlefield
from rules import CardDefinition, Cost
from catalog import BY_NAME
import simulation as base
import integrated as v6


class IndexedKernel(CentralKernel):
    def __init__(self):
        super().__init__()
        self.order = defaultdict(list)
        self.adopt = None
        self.resource_names = {}
        # Object-ID keyed exile replacement for reviewed unearth activation.
        # This is existing-kernel state, not a second zone index.
        self.unearth_pending = {}
        # Active graveyard-cast flashback stack object IDs: on every exit from
        # stack, exile replaces other zones, including countered spells.
        self.flashback_pending = set()

    def add(self, card, owner, controller=None, zone='battlefield', token=False):
        # A permanent's normal effect creates its legacy view. Adopt the spell's
        # physical object at that boundary instead of minting a second card.
        candidate = self.adopt
        if candidate is not None and not token and zone == 'battlefield':
            original = self.get(candidate)
            if original.owner == owner and original.card.name == card.name:
                self.adopt = None  # move() calls add() internally
                definition = replace(original.card, types=original.types | card.types,
                                     base_power=card.base_power, base_toughness=card.base_toughness,
                                     keywords=original.card.keywords | card.keywords)
                original.card = definition
                return self.get(self.move(candidate, 'battlefield', 'resolve').new_object_id)
        obj = super().add(card, owner, controller, zone, token)
        self.order[owner, zone].append(obj.object_id)
        return obj

    def move(self, oid, to_zone, reason, commander_choice=False):
        obj = self.get(oid)
        old_key = obj.owner, obj.zone
        if obj.zone == 'stack' and oid in self.flashback_pending:
            if to_zone != 'stack':
                to_zone, reason = 'exile', 'exile'
        if obj.zone == 'battlefield' and oid in self.unearth_pending:
            # Restore printed characteristics before the zone-change new
            # object is constructed; haste does not persist in the graveyard.
            obj.card = self.unearth_pending[oid]
            if to_zone != 'battlefield':
                # Unearth replaces *any* attempt to leave with exile, not just
                # death. This excludes phase-out, which isn't a zone move.
                to_zone, reason = 'exile', 'exile'
        if obj.zone == 'battlefield' and reason == 'state_based' and 'commander' in obj.card.supertypes:
            commander_choice = True
        result = super().move(oid, to_zone, reason, commander_choice)
        if result is not None:
            self.order[old_key].remove(oid)
            self.resource_names.pop(oid, None)
            self.unearth_pending.pop(oid, None)
            self.flashback_pending.discard(oid)
        return result

    def remove_owned(self, seat):
        for oid, obj in list(self.objects.items()):
            if obj.owner == seat:
                self.order[obj.owner, obj.zone].remove(oid)
                del self.objects[oid]
                self.resource_names.pop(oid, None)
        self._dirty()


@dataclass(frozen=True)
class CardView:
    zones: object
    object_id: int
    definition_id: str

    @property
    def spec(self):
        return self.zones.specs[self.definition_id]

    def __getattr__(self, name):
        return getattr(self.spec, name)


class LiveZones(KernelZones):
    def __init__(self, kernel, seed=1):
        super().__init__(kernel, seed=seed)
        self.order = kernel.order
        self.specs = {}

    def register(self, spec, detailed=False):
        def freeze(value):
            if isinstance(value, dict):
                return MappingProxyType({key: freeze(item) for key, item in value.items()})
            if isinstance(value, (list, tuple)):
                return tuple(freeze(item) for item in value)
            return value
        spec = replace(spec, parameters=freeze(spec.parameters), colored_cost=freeze(spec.colored_cost))
        prefix = 'named:' if detailed else 'abstract:'
        key = prefix + spec.name
        if key not in self.specs:
            self.specs[key] = spec
        elif self.specs[key] != spec:
            raise ValueError('Conflicting card definition ' + spec.name)
        known = BY_NAME.get(spec.name) if detailed else None
        if known:
            return replace(known, card_id=key)
        types = {spec.card_type}
        if spec.parameters.get('is_creature'):
            types.add('creature')
        return CardDefinition(
            key, spec.name, frozenset(types),
            cost=Cost(max(0, spec.mana_value - sum(spec.colored_cost.values())),
                      spec.colored_cost.get('U', 0), spec.colored_cost.get('R', 0)),
            base_power=spec.parameters.get('power', 2) if 'creature' in types else 0,
            base_toughness=spec.parameters.get('toughness', 2) if 'creature' in types else 0,
            coverage='unimplemented' if spec.effect == 'unsupported' else 'approx')

    def add(self, definition, owner, zone='library', token=False):
        self._checkseat(owner)
        if zone not in self.valid_zones or token and zone != 'battlefield':
            raise ValueError('Invalid initial card zone')
        return self.kernel.add(definition, owner, zone=zone, token=token).object_id

    @property
    def valid_zones(self):
        from zones import CARD_ZONES
        return CARD_ZONES

    def add_spec(self, spec, seat, zone='library', detailed=False):
        return self.add(self.register(spec, detailed), seat, zone)

    def move(self, oid, to_zone, reason='resolve', commander_choice=False):
        old = self.kernel.get(oid)
        owner, source = old.owner, old.zone
        transition = self.kernel.move(oid, to_zone, reason, commander_choice)
        if transition is None:
            return oid
        self.operations.append((reason, owner, oid, transition.new_object_id, source, transition.new_zone))
        return transition.new_object_id

    def views(self, seat, zone):
        return tuple(CardView(self, oid, self.kernel.get(oid).card.card_id) for oid in self.ids(seat, zone))

    def leave_game(self, seat):
        self._checkseat(seat)
        self.kernel.remove_owned(seat)
        for oid, ticket in list(self._pending.items()):
            if ticket.seat == seat:
                del self._pending[oid]
        self.operations.append(('leave_game', seat))


class LiveBattlefield(Battlefield):
    def __init__(self, table, kernel):
        super().__init__(table)
        self.kernel = kernel

    def create_permanent(self, p, *args, **kwargs):
        adopting = self.kernel.adopt is not None
        permanent = super().create_permanent(p, *args, **kwargs)
        if not adopting:
            # Synthetic sorcery finishers can install persistent clock effects.
            # These are explicitly synthetic tokens, not extra physical cards.
            self.kernel.get(permanent.id).token = True
        return permanent

    def leave_game(self, seat):
        self.table.zones.leave_game(seat)
        for oid, entry in list(self.views.items()):
            if entry.player.seat == seat:
                del self.views[oid]
                self.transitions += 1

    def cleanup(self):
        before = {oid: self.kernel.get(oid).card.name for oid in self.views}
        super().cleanup()
        self._after_movement(list(before), before)

    def _after_movement(self, ids, prior_names):
        removed_sources = [(self.views[oid].player, prior_names.get(oid)) for oid in ids
                           if oid in self.views and oid not in self.kernel.objects]
        result = super()._after_movement(ids, prior_names)
        for player, name in removed_sources:
            if not getattr(self.table,'source_backed_mana',False) and player is self.table.details and name in player.ready_sources:
                player.ready_sources.remove(name)
                player.mana = min(player.mana, sum(max(map(sum, v6.ColoredPayment.modes(n)))
                                  for n in player.ready_sources) + sum(player.floating))
        return result


class ZonePlayerMixin:
    """Read-only zone properties; initialization accepts only empty inventories."""
    @property
    def hand(self):
        return self.zones.views(self.seat, 'hand') if hasattr(self, 'zones') else ()

    @hand.setter
    def hand(self, value):
        if hasattr(self, 'zones') or value:
            raise TypeError('Use explicit zone operations for hand changes')

    @property
    def library(self):
        return self.zones.views(self.seat, 'library') if hasattr(self, 'zones') else ()

    @library.setter
    def library(self, value):
        if hasattr(self, 'zones') or value:
            raise TypeError('Use explicit zone operations for library changes')

    @property
    def graveyard(self):
        return self.zones.names(self.seat, 'graveyard')

    @property
    def commander_in_zone(self):
        return bool(self.zones.ids(self.seat, 'command'))

    @commander_in_zone.setter
    def commander_in_zone(self, value):
        if bool(value) != self.commander_in_zone:
            raise AssertionError('Commander flag disagrees with registry')

    @property
    def lands(self):
        if not hasattr(self, 'zones'):
            return 0
        return sum('land' in self.zones.kernel.get(x).types for x in self.zones.ids(self.seat, 'battlefield'))

    @lands.setter
    def lands(self, value):
        if value:
            raise TypeError('Land count is a projection')

    def draw(self, n=1):
        ids, okay = self.zones.draw(self.seat, n)
        if not okay:
            self.life = 0  # caller processes elimination in its normal SBA window
        return ids

    def mulligan(self):
        # Historical one-free-mulligan policy, now shuffling the same physical
        # cards rather than discarding an inventory and creating a new deck.
        for oid in self.zones.ids(self.seat, 'hand'):
            self.zones.move(oid, 'library')
        self.zones.shuffle(self.seat)
        self.draw(7)
        self.mulligans += 1


class ZonePlayer(ZonePlayerMixin, base.Player):
    def __init__(self, seat, kind, seed, zones, library):
        base.Player.__init__(self, seat, kind, seed, [], base.PriorityPilot())
        self.zones = zones
        for card in library:
            zones.add_spec(card, seat)
        self.draw(7)
        if not 2 <= sum(c.kind == 'land' for c in self.hand) <= 5:
            self.mulligan()


class ZoneDetailedPlayer(ZonePlayerMixin, v6.DetailedPlayer):
    @property
    def land_names(self):
        return [self.zones.kernel.resource_names.get(oid, self.zones.kernel.get(oid).card.name)
                for oid in self.zones.ids(self.seat, 'battlefield')
                if 'land' in self.zones.kernel.get(oid).types]

    @property
    def rock_names(self):
        return [self.zones.kernel.get(oid).card.name for oid in self.zones.ids(self.seat, 'battlefield')
                if self.zones.kernel.get(oid).card.name in v6.ROCKS]

    def __init__(self, seat, seed, zones):
        from collections import Counter
        base.Player.__init__(self, seat, 'magnus', seed, [], v6.MagnusPilot())
        self.zones = zones
        self.payment_policy = v6.ColoredPayment()
        self.ready_sources = []; self.floating = (0, 0, 0)
        self.commander_casts = 0; self.payments = []; self.treasures = 0
        self.coverage = Counter(); self.unsupported_seen = Counter()
        self.block_policy = 'never'
        for card in v6.shuffled_library(seed + 601):
            zones.add_spec(card, seat, detailed=True)
        zones.add_spec(v6.named_spec('Magnus the Red'), seat, 'command', detailed=True)
        self.draw(7)
        if not 2 <= sum(c.kind == 'land' for c in self.hand) <= 5:
            self.mulligan()
