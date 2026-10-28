"""V9b: live authoritative zones, retaining the v8 combat/response engine.

Resource accounting and selection policy remain explicitly approximate. This
module replaces their card mutations, not their printed-card rule coverage.
"""
from __future__ import annotations
from state import (DeckProvider, IndexedKernel, LiveZones, LiveBattlefield,
                   ZonePlayer, ZoneDetailedPlayer)
from adapter import V9Table
from table import CentralTable
from stack import SharedStack
from loops import LoopResolver
from rules import Event
import simulation as base
import integrated as v6


class LiveTable(V9Table):
    player_class = ZonePlayer
    detailed_player_class = ZoneDetailedPlayer
    battlefield_class = LiveBattlefield

    def __init__(self, providers=None, seed=1, trace=False, opening=None):
        providers = tuple(p if isinstance(p, DeckProvider) else DeckProvider(p)
                          for p in (providers if providers is not None else ('magnus', 'aggro', 'control', 'combo')))
        if len(providers) != 4:
            raise ValueError('Exactly four providers required')
        detailed = [i for i, p in enumerate(providers) if p.kind == 'magnus']
        if len(detailed) != 1:
            raise NotImplementedError('Exactly one detailed Magnus seat is supported')
        kernel = IndexedKernel()
        self.zones = LiveZones(kernel, seed)
        players = []; opponent = 0
        for seat, provider in enumerate(providers):
            if provider.kind == 'magnus':
                player = self.detailed_player_class(seat, seed * 109 + 3, self.zones)
            else:
                opponent += 1
                player = self.player_class(seat, provider.kind, seed * 109 + opponent * 431 + 3,
                                    self.zones, base.synthetic_library(provider.kind, seed * 67 + opponent * 17 + 23))
            players.append(player)
        base.Table.__init__(self, [p.kind for p in providers], seed, True, trace, players)
        self.providers = providers; self.detailed_seat = detailed[0]
        self.details = players[self.detailed_seat]; self._upkeep_actor = None
        self.coverage_log = []; self.seeded_opening = bool(opening)
        self.world = self.battlefield_class(self, kernel); self.rules = kernel
        self.safe_runner = kernel.guard; self.combo_planner = LoopResolver(self.safe_runner)
        self.shared_triggers = 0; self.shared_cost_queries = 0
        self.safety_stop = None; self.pending_triggers = []; self._world_actions = 0
        self.spell_stack = SharedStack(self)
        self._spells = {}  # action identity -> authoritative pending CastTicket
        for name in ('creature', 'rock', 'selection', 'pongify'):
            self.register_effect('named_' + name, getattr(self, 'resolve_' + name))
        self.on_event(self.named_triggers)
        if opening:
            self._set_opening(opening)
        self.assert_consistent()

    def _set_opening(self, names):
        # Explicit diagnostic-only selection from the real inventory.
        p = self.details; selected = []
        for name in names:
            oid = next((x for zone in ('hand', 'library') for x in self.zones.ids(p.seat, zone)
                        if self.rules.get(x).card.name == name and x not in selected), None)
            if oid is None:
                raise ValueError('Card not in deck ' + name)
            if self.rules.get(oid).zone != 'hand':
                oid = self.zones.move(oid, 'hand')
            selected.append(oid)
        if len(selected) > 7:
            raise ValueError('Diagnostic opening exceeds seven cards')
        while len(p.hand) > 7:
            oid = next(x for x in reversed(self.zones.ids(p.seat, 'hand')) if x not in selected)
            new = self.zones.move(oid, 'library')
            ids = self.zones.order[p.seat, 'library']
            ids.insert(0, ids.pop(ids.index(new)))
        ids = self.zones.order[p.seat, 'hand']
        ids[:] = selected + [x for x in ids if x not in selected]
        if len(p.hand) < 7:
            p.draw(7 - len(p.hand))

    def pay_spell(self, p, card, action, response=False):
        if not self.can_pay(p, action):
            raise ValueError('Illegal mana payment')
        spec = card.spec
        zone = self.rules.get(card.object_id).zone
        if zone not in ('hand', 'command') or self.rules.get(card.object_id).owner != p.seat:
            raise ValueError('Spell not available')
        if card.effect == 'unsupported' or card.card_type == 'land':
            raise ValueError('Unsupported or uncastable card')
        self.pay_resources(p, action)
        ticket = self.zones.cast(p.seat, card.object_id)
        self._spells[id(action)] = ticket
        if zone == 'command':
            p.commander_casts += 1
        p.cards_cast += 1; p.mana_spent += action.cost; self.counts['casts'] += 1
        if p is self.details:
            p.coverage['approx' if spec.name in v6.APPROX else 'supported'] += 1
        self.note(f'  P{p.seat} ({p.archetype}) casts {ticket.card_name} [{action.card_type}] for {action.cost}; mana={p.mana}.')
        return True

    def pay_resources(self, p, action):
        policy = p.payment_policy
        if policy:
            previous = p.treasures
            policy.pay(p, action)
            if previous > p.treasures:
                self.world.consume_treasures(p, previous - p.treasures)
        else:
            p.mana -= action.cost

    def expected_action(self, p, card, announced=None):
        return (self.action_for(p, card) if p.payment_policy else
                base.Action(p.seat, card.name, card.card_type, card.effect,
                            card.mana_value, parameters=dict(card.parameters)))

    def cast(self, action):
        p = self.players[action.actor]
        if not p.alive:
            return False
        if action.effect == 'unsupported':
            raise ValueError('Unsupported effect cannot resolve')
        cards = p.hand + self.zones.views(p.seat, 'command')
        card = next((c for c in cards if c.name == action.source), None)
        if card is None or not self.can_pay(p, action):
            return False
        # Reject stale/fabricated costs and effects before any payment or move.
        expected = self.expected_action(p, card, action)
        if (action.card_type, action.effect, action.cost, action.parameters) != (
                expected.card_type, expected.effect, expected.cost, expected.parameters):
            raise ValueError('Action differs from current card/cost')
        self.safe_runner.check((p.seat, action.source, p.mana, tuple(c.object_id for c in p.hand)), stack_depth=1)
        self.pay_spell(p, card, action)
        self.emit('spell_cast', action)
        self.spell_stack.resolve(action)
        if not p.alive:
            self.eliminate(p, 'empty_library')
        self._world_actions += 1
        self.assert_consistent()
        return True

    def emit(self, name, action=None, **payload):
        if action is not None and name in ('spell_countered', 'spell_resolved'):
            ticket = self._spells.pop(id(action), None)
            if ticket and ticket.object_id in self.rules.objects:
                if name == 'spell_countered':
                    self.zones.counter(ticket)
                else:
                    # Permanent cards are adopted by add_creature/add_permanent
                    # during apply(); nonpermanents remain on stack until now.
                    self.zones.resolve(ticket, effect=lambda kernel, ticket: None)
            elif ticket:
                self.zones._pending.pop(ticket.object_id, None)
                self.rules.events.append(Event(name, ticket.seat, ticket.object_id, spell_types=ticket.spell_types))
        return base.Table.emit(self, name, action, **payload)

    def stack_action_active(self, action):
        ticket = self._spells.get(id(action))
        return bool(ticket and ticket.object_id in self.rules.objects)

    def apply(self, action):
        if not self.players[action.actor].alive:
            return
        ticket = self._spells.get(id(action))
        permanent = ticket and bool(ticket.spell_types & {'creature', 'artifact', 'enchantment', 'planeswalker', 'battle'})
        self.rules.adopt = ticket.object_id if permanent else None
        try:
            result = CentralTable.apply(self, action)
            if permanent and self.rules.adopt is not None:
                raise AssertionError('Permanent effect did not create its battlefield view')
            return result
        finally:
            self.rules.adopt = None

    def add_creature(self, p, *args, **kwargs):
        if p.eliminated_round is not None:
            return None
        return super().add_creature(p, *args, **kwargs)

    def resolve_counter_rider(self, response, original):
        if not self.players[original.actor].alive:
            return
        return super().resolve_counter_rider(response, original)

    def resolve_rock(self, table, action):
        p = self.players[action.actor]
        self.add_permanent(p, 'ramp', 2 if action.source == 'Sol Ring' else 1, action.source)
        self.note(f'    {action.source} increases available mana next turn.')

    def resolve_selection(self, table, action):
        p = self.players[action.actor]; name = action.source
        n = v6.SELECTION[name]
        p.draw(n)
        if not p.alive:
            self.eliminate(p, 'empty_library')
            return
        if name == 'Brainstorm':
            priority = lambda c: 1 if c.kind == 'land' and p.lands < 5 else 0 if c.effect == 'unsupported' else 2
            for c in sorted(p.hand, key=priority)[:2]:
                self.zones.move(c.object_id, 'library')
        elif name == 'Frantic Search':
            for c in sorted(p.hand, key=lambda c: c.effect != 'unsupported')[:2]:
                self.zones.discard(p.seat, c.object_id)
        self.note(f'    {name}: partial card selection ({n} drawn; exact look/scry/untap not modeled).')

    def play_land(self, p, card, turn):
        if card not in p.hand or card.kind != 'land':
            raise ValueError('Land not available')
        if getattr(p, '_land_turn', None) == self.safe_runner.turn:
            raise ValueError('Land already played this turn')
        p._land_turn = self.safe_runner.turn
        old_count = p.lands
        oid = self.zones.play_land(p.seat, card.object_id)
        from kernel import WorldEntry
        self.world.views[oid] = WorldEntry(p, None, 'resource')
        name = self.rules.get(oid).card.name
        tapped = False
        if p is self.details:
            if name == 'Fabled Passage':
                basics = [c for c in p.library if c.name in ('Island', 'Mountain')]
                if basics:
                    u = sum(n == 'Island' or ' [U]' in n for n in p.land_names)
                    r = sum(n == 'Mountain' or ' [R]' in n for n in p.land_names)
                    desired = 'Island' if u <= r else 'Mountain'
                    basic = next((c for c in basics if c.name == desired), basics[0])
                    self.world.move(oid, 'graveyard', 'sacrifice')
                    oid = self.zones.move(basic.object_id, 'battlefield')
                    self.zones.shuffle(p.seat)
                    self.world.views[oid] = WorldEntry(p, None, 'resource')
                    name = self.rules.get(oid).card.name
                    tapped = p.lands < 4
                    self.note(f'  P{p.seat} sacrifices Fabled Passage and fetches {name}.')
            elif name == 'Riverglide Pathway':
                u = sum(n == 'Island' or n.endswith('[U]') for n in p.land_names)
                r = sum(n == 'Mountain' or n.endswith('[R]') for n in p.land_names)
                name += ' [U]' if u <= r else ' [R]'
            if name == 'Mystic Sanctuary' or name == 'Stormcarved Coast' and old_count < 2 or name == 'Spirebluff Canal' and old_count >= 3:
                tapped = True
            if name == 'Sulfur Falls' and not any(n in ('Island', 'Mountain', 'Steam Vents') for n in p.land_names):
                tapped = True
            if name == 'Steam Vents':
                p.life -= 2; p.damage_taken += 2
                self.note(f'  P{p.seat} pays 2 life for Steam Vents.')
            self.rules.resource_names[oid] = name  # chosen modal face for legacy resource policy
        self.rules.get(oid).tapped = tapped
        self.emit('land_played', controller=p.seat, round=turn, object_id=oid)
        self.note(f'  P{p.seat} plays {name} ({p.lands} lands){" tapped" if tapped else ""}.')
        return name if tapped else None

    def upkeep(self, p, turn):
        self.safe_runner.new_turn(turn * 4 + p.seat)
        self.emit('turn_start', controller=p.seat, round=turn)
        for oid in self.zones.ids(p.seat, 'battlefield'):
            self.rules.get(oid).tapped = False
        for c in p.creatures:
            self.world.tap(c, False)
        p.draw()
        if not p.alive:
            self.eliminate(p, 'empty_library'); return
        if p is not self.details:
            for perm in list(p.permanents):
                if perm.kind == 'engine' and perm.entered_round < turn:
                    if p.rng.random() < base.TEM['engine']['extra_draw_chance']:
                        p.draw(); self.counts['bonus_draws'] += 1
                    if not p.alive:
                        self.eliminate(p, 'empty_library'); return
                    if p.rng.random() < base.TEM['engine']['token_chance']:
                        self.add_creature(p, 1, 1, 'engine token', token=True)
            for perm in list(p.permanents):
                if perm.kind == 'clock' and perm.entered_round < turn and self.rivals(p):
                    self.damage(self.choose_target(p, 'clock'), perm.value, p, 'persistent_finisher')
        land = next((c for c in p.hand if c.kind == 'land'), None)
        tapped = self.play_land(p, land, turn) if land else None
        if not land:
            p.land_misses += 1
        if not p.alive:
            self.eliminate(p, 'shock_land'); return
        self.refresh_resources(p, tapped)
        self.assert_consistent()

    def refresh_resources(self, p, tapped):
        if p is self.details:
            p.ready_sources = [n for n in p.land_names if n != 'Fabled Passage'] + p.rock_names + ['Treasure'] * p.treasures
            p.floating = (0, 0, 0)
            if tapped:
                p.ready_sources.remove(tapped)
            p.mana = sum(max(sum(mode) for mode in v6.ColoredPayment.modes(n)) for n in p.ready_sources)
            self.coverage_log.append({'round': self.round_num, 'hand_unsupported': [c.name for c in p.hand if c.effect == 'unsupported']})
            for c in p.hand:
                if c.effect == 'unsupported':
                    p.unsupported_seen[c.name] += 1
        else:
            p.mana = p.available_sources()

    def main(self, p):
        for _ in range(12):
            if not p.alive or len(self.alive()) <= 1:
                return
            action = p.pilot.select_action(self, p)
            if action is None:
                break
            if not self.cast(action):
                raise AssertionError('Pilot offered an illegal action')
        if len(p.hand) > 7:
            if p is self.details:
                discards = p.hand[7:]
            else:
                priority = base.CONF['priority'].get(p.archetype, [])
                ordered = sorted(p.hand, key=lambda c: (c.kind == 'land' and p.lands < 5,
                                 -(priority.index(c.kind) if c.kind in priority else 99)), reverse=True)
                discards = ordered[7:]
            for card in discards:
                self.zones.discard(p.seat, card.object_id)
        self.assert_consistent()

    def eliminate(self, p, cause):
        if p.eliminated_round is not None:
            return
        self.world.leave_game(p.seat)
        for key, ticket in list(self._spells.items()):
            if ticket.seat == p.seat:
                del self._spells[key]
        p.eliminated_round = self.round_num
        p.creatures.clear(); p.permanents.clear()
        self.clear_resources(p)
        self.eliminations.append({'round': self.round_num, 'seat': p.seat, 'archetype': p.archetype, 'cause': cause})
        self.emit('elimination', seat=p.seat, cause=cause)
        self.counts['eliminated'] += 1
        self.note(f'    ELIMINATED P{p.seat} ({p.archetype}): {cause}.')

    def clear_resources(self, p):
        p.mana = 0
        if p is self.details:
            p.ready_sources.clear()
            p.floating = (0, 0, 0); p.treasures = 0

    def assert_consistent(self):
        self.zones.assert_consistent()
        if not self.world.consistent():
            raise AssertionError('Battlefield views differ from authoritative registry')
        return True

    def run(self, max_rounds=8):
        result = super().run(max_rounds)
        self.assert_consistent()
        return result

    def diagnostics(self):
        d = super().diagnostics()
        d['known_rules_gaps'] = [
            'limited named-card subset; unsupported spells fail closed',
            'selection, scry and some land abilities remain approximations',
            'legacy colored/fungible payment; no source-ID mana/tap integration',
            'counter-only priority; cast triggers settle before responses',
            'one detailed deck; synthetic opponents and finishers',
            'no commander damage, multiblock, buyback, spell copies or verified Magnus loops',
            'historical upkeep land-play and precombat hand-size cleanup timing',
        ]
        d['v8']['limits'] = ['shared physical zones, battlefield, combat and counter stack',
                             'legacy resource policies; counter-only priority']
        d['v7']['modular_scope'] = 'typed costs/triggers/block legality; live zones supplied by v9b'
        d['v9b'] = {
            'authoritative_card_zones_in_live_game': True,
            'zone_index_consistent': self.zones.assert_consistent(),
            'kernel_view_consistent': self.world.consistent(),
            'physical_objects': len(self.rules.objects),
            'zone_counts': {str(p.seat): {zone: len(self.zones.ids(p.seat, zone))
                            for zone in sorted(self.zones.valid_zones)} for p in self.players},
            'limits': ['legacy mana/payment policies and source-name metadata',
                       'counter-only priority; cast triggers settle before responses',
                       'one detailed deck; selection/land rules still approximate'],
        }
        d['v9']['authoritative_card_zones_in_live_game'] = True
        d['v9']['migration_status'] = 'live shared card zones; legacy resource policies and counter-only priority remain'
        return d
