"""V9c source-backed live resources; v9b zones and the v8 shared stack remain."""
from resources import Resources, SourcePayment, ZERO
from state import ZonePlayer, ZoneDetailedPlayer, LiveBattlefield
from live import LiveTable
from kernel import WorldEntry
from catalog import TREASURE
import simulation as base


class SourcePlayerMixin:
    @property
    def mana(self):
        return self.resources.capacity(self.seat) if hasattr(self, 'resources') else 0
    @mana.setter
    def mana(self, value):
        if hasattr(self, 'resources'): raise TypeError('Mana capacity is a read-only projection')
    @property
    def ready_sources(self):
        if not hasattr(self, 'resources'): return ()
        return tuple(self.zones.kernel.get(oid).card.name for oid, _ in self.resources.sources(self.seat))
    @ready_sources.setter
    def ready_sources(self, value):
        if hasattr(self, 'resources'): raise TypeError('Use source objects')
    @property
    def floating(self):
        if not hasattr(self, 'resources'): return (0, 0, 0)
        c, u, r = self.resources.pool(self.seat)
        return u, r, c  # legacy reporting order only
    @floating.setter
    def floating(self, value):
        if hasattr(self, 'resources'): raise TypeError('Use the kernel mana pool')
    @property
    def treasures(self):
        return sum(o.token and o.card.card_id == 'treasure' for o in self.zones.kernel.on_battlefield()
                   if o.controller == self.seat) if hasattr(self, 'zones') else 0
    @treasures.setter
    def treasures(self, value):
        if hasattr(self, 'resources'): raise TypeError('Use Treasure objects')
    def available_sources(self):
        return self.resources.capacity(self.seat, ready=False) if hasattr(self, 'resources') else 0
    def snapshot(self, round_num):
        result = base.Player.snapshot(self, round_num)
        result.update(mana_pool=self.resources.pool(self.seat),
                      ready_source_ids=[oid for oid, _ in self.resources.sources(self.seat)],
                      mana_capacity_upper_bound=self.mana)
        if self.archetype == 'magnus':
            result.update(tokens=self.token_count(), named_hand=[c.name for c in self.hand],
                          commander_zone=self.commander_in_zone, commander_casts=self.commander_casts,
                          unsupported_in_hand=sum(c.effect == 'unsupported' for c in self.hand))
        return result


class SourcePlayer(SourcePlayerMixin, ZonePlayer): pass
class SourceDetailedPlayer(SourcePlayerMixin, ZoneDetailedPlayer): pass


class SourceBattlefield(LiveBattlefield):
    def create_treasure(self, player):
        obj = self.kernel.add(TREASURE, player.seat, token=True)
        self.views[obj.object_id] = WorldEntry(player, None, 'resource')
        self.permanents_entered += 1
        return obj


class ManaTable(LiveTable):
    source_backed_mana = True
    player_class = SourcePlayer
    detailed_player_class = SourceDetailedPlayer
    battlefield_class = SourceBattlefield

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resources = Resources(self)
        for player in self.players:
            player.resources = self.resources
            player.payment_policy = SourcePayment(self.resources)
        self.assert_consistent()

    def action_for_card(self, player, card):
        return self.action_for(player, card) if player is self.details else self.build_action(player, card)

    def expected_action(self, player, card, announced=None):
        return (self.action_for(player, card) if player is self.details else
                base.Action(player.seat, card.name, card.card_type, card.effect,
                            card.mana_value, parameters=dict(card.parameters)))

    def pay_resources(self, player, action):
        player.payment_policy.pay(player, action)

    def refresh_resources(self, player, tapped):
        # No scalar refill: untapped physical objects and pool are authoritative.
        if player is self.details:
            self.coverage_log.append({'round': self.round_num,
                                      'hand_unsupported': [c.name for c in player.hand if c.effect == 'unsupported']})
            for card in player.hand:
                if card.effect == 'unsupported': player.unsupported_seen[card.name] += 1
        self.rules._dirty()

    def clear_resources(self, player):
        if hasattr(self, 'resources'):
            self.rules.mana_pools[player.seat] = ZERO
            self.resources._cache.clear()

    def upkeep(self, player, turn):
        self.resources.empty_pools()
        self.resources.untap(player.seat)
        return super().upkeep(player, turn)

    def main(self, player):
        try: return super().main(player)
        finally: self.resources.empty_pools()  # main phase -> combat

    def combat(self, player):
        try: return super().combat(player)
        finally: self.resources.empty_pools()  # combat -> end/cleanup in limited driver

    def emit(self, name, action=None, **payload):
        if name == 'spell_cast' and action is not None:
            player = self.players[action.actor]
            if player.life <= 0:
                self.eliminate(player, 'mana_ability_life')
        return super().emit(name, action, **payload)

    def resolve_rock(self, table, action):
        player = self.players[action.actor]
        self.add_permanent(player, 'ramp', 2 if action.source == 'Sol Ring' else 1, action.source)
        self.note(f'    {action.source} enters untapped; its mana ability is immediately available.')

    def assert_consistent(self):
        super().assert_consistent()
        if hasattr(self, 'resources'): self.resources.assert_consistent()
        return True

    def diagnostics(self):
        d = super().diagnostics()
        d['known_rules_gaps'] = [x for x in d['known_rules_gaps'] if 'legacy colored' not in x]
        d['known_rules_gaps'] += ['only U/R/colorless mana and U/R/generic costs; other mana text fails closed',
                                 'counter-only priority and coarse phase driver remain']
        d['v9']['migration_status'] = 'live shared card zones and source-ID mana; counter-only priority remains'
        d['v9b']['limits'][0] = 'source-ID mana supplied by v9c; synthetic abilities remain approximate'
        d['v8']['limits'] = ['shared card zones, combat, source-ID mana and counter stack',
                             'counter-only priority; synthetic/land-rule approximations']
        d['v9c'] = dict(source_backed_live_payment=True,
                        pools={str(seat): self.resources.pool(seat) for seat in range(4)},
                        payments=self.resources.payments, activations=self.resources.activations,
                        planner_max_states=self.resources.max_states_seen,
                        planner_budget=self.resources.max_states, cache_hits=self.resources.cache_hits,
                        limits=['counter-only priority; cast triggers settle before responses',
                                'one detailed deck; U/R/colorless source subset; synthetic sources approximate'])
        return d
