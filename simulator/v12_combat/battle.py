"""Current-rule multi-block allocation, trample and two combat damage steps.

No damage assignment order: a pure allocation policy chooses at damage time.
Each blocker still blocks one attacker. Deathtouch/lifelink/prevention and
planeswalker/battle attacks are outside this milestone.
"""
from dataclasses import dataclass
from combat import Combat
from rules import Event


@dataclass(frozen=True)
class Allocation:
    controller: int
    stage: str
    attacker: int
    defender: int
    power: int
    blockers: tuple[int, ...]
    lethal: tuple[int, ...]
    player_allowed: bool


class ExpandedCombat(Combat):
    def __init__(self, table):
        super().__init__(table)
        self.early_ids = frozenset()
        self.two_steps = False

    def live_attacker(self, attack):
        t = self.t; obj = t.rules.objects.get(attack.attacker)
        return obj if (obj and obj.zone == 'battlefield' and 'creature' in obj.types
                       and obj.controller == t.active_seat and t.players[attack.defender].alive) else None

    def live_blockers(self, attack):
        return tuple(self.t.rules.get(oid) for oid in attack.blockers if oid in self.t.rules.objects
                     and self.t.rules.get(oid).zone == 'battlefield'
                     and self.t.rules.get(oid).controller == attack.defender
                     and 'creature' in self.t.rules.get(oid).types)

    def declare_attackers(self, player, selection=None):
        self.early_ids = frozenset(); self.two_steps = False
        return super().declare_attackers(player, selection)

    def declare_blockers(self, selection=None):
        t = self.t; proposed = []; used = set()
        if selection is None:
            policy = getattr(t, 'block_assignment_policy', None)
            if policy:
                # Callback receives immutable IDs; engine checks all assignments before committing.
                selection = policy(tuple((a.attacker, a.defender) for a in self.attacks))
            else:
                for a in self.attacks:
                    attacker = self.live_attacker(a); defender = t.players[a.defender]
                    if not attacker or defender.block_policy == 'never': continue
                    legal = t.rules.legal_blockers(a.attacker, a.defender, used)
                    view = next(c for p in t.players for c in p.creatures if c.id == a.attacker)
                    first = t.block(defender, view, used)
                    chosen = [first.id] if first and first.id in {o.object_id for o in legal} else []
                    if not chosen:
                        group = []
                        for obj in sorted(legal, key=lambda o: (-o.power, o.object_id)):
                            group.append(obj)
                            if sum(max(0, o.power) for o in group) >= max(0, attacker.toughness-attacker.damage_marked):
                                chosen = [o.object_id for o in group]; break
                    proposed.extend((a.attacker, oid) for oid in chosen); used.update(chosen)
                selection = proposed
        proposed = list(selection); used.clear()
        for attacker, blocker in proposed:
            a = next((a for a in self.attacks if a.attacker == attacker), None)
            if a is None or not self.live_attacker(a) or blocker in used:
                raise ValueError('Invalid or duplicate blocker assignment')
            if blocker not in {o.object_id for o in t.rules.legal_blockers(attacker, a.defender)}:
                raise ValueError('Illegal blocker')
            used.add(blocker)
        for a in self.attacks:
            a.blockers = [b for attacker, b in proposed if attacker == a.attacker]
            a.blocked = bool(a.blockers)
        for attacker, blocker in proposed:
            t.counts['blocks'] += 1
            t.note(f'    BLOCK: #{blocker} blocks #{attacker}.')
        return tuple(self.attacks)

    def participants(self):
        result = {}
        for a in self.attacks:
            obj = self.live_attacker(a)
            if obj: result[obj.object_id] = obj
            # A blocker remains in combat if the attacker has left, but deals no damage.
            for obj in self.live_blockers(a): result[obj.object_id] = obj
        return result

    def begin_damage(self):
        self.early_ids = frozenset(oid for oid, obj in self.participants().items()
                                   if obj.keywords.intersection({'first_strike', 'double_strike'}))
        self.two_steps = bool(self.early_ids)
        return self.two_steps

    def deals_in(self, obj, stage):
        if stage == 'first_strike_damage': return obj.object_id in self.early_ids
        return not self.two_steps or obj.object_id not in self.early_ids or 'double_strike' in obj.keywords

    def allocate(self, a, attacker, blockers, stage):
        power = max(0, attacker.power)
        trample = 'trample' in attacker.keywords
        allowed = not a.blocked or trample
        context = Allocation(attacker.controller, stage, attacker.object_id, a.defender, power,
                             tuple(o.object_id for o in blockers),
                             tuple(max(0, o.toughness-o.damage_marked) for o in blockers), allowed)
        policy = getattr(self.t, 'combat_damage_policy', None)
        if policy:
            allocation = dict(policy(context))
        else:
            allocation = {}; remaining = power
            for oid, lethal in zip(context.blockers, context.lethal):
                amount = min(remaining, lethal); allocation[oid] = amount; remaining -= amount
            if allowed: allocation['player'] = remaining
            elif blockers: allocation[blockers[-1].object_id] += remaining
        legal = set(context.blockers) | ({'player'} if allowed else set())
        if any(k not in legal or type(v) is not int or v < 0 for k, v in allocation.items()):
            raise ValueError('Invalid combat damage target or quantity')
        expected = power if blockers or allowed else 0
        if sum(allocation.values()) != expected: raise ValueError('Combat damage must assign all available power')
        if allocation.get('player', 0) and any(allocation.get(oid, 0) < lethal
                                               for oid, lethal in zip(context.blockers, context.lethal)):
            raise ValueError('Trample requires lethal assigned to every blocker')
        return allocation

    def damage(self, player, stage='combat_damage'):
        if stage not in ('combat_damage', 'first_strike_damage'): raise ValueError('Unknown damage step')
        if stage == 'first_strike_damage' and not self.two_steps: raise ValueError('No first-strike step scheduled')
        t = self.t; creatures = {}; players = {}; assignments = []; hits = []
        # Build and validate the entire batch before any damage, life or trigger mutation.
        for a in self.attacks:
            attacker = self.live_attacker(a)
            if not attacker: continue
            blockers = self.live_blockers(a)
            if self.deals_in(attacker, stage):
                allocation = self.allocate(a, attacker, blockers, stage)
                assignments.append(dict(source=attacker.object_id, controller=attacker.controller,
                                        creature_damage={k: v for k, v in allocation.items() if k != 'player'},
                                        player_damage=allocation.get('player', 0), defender=a.defender))
                for oid, amount in allocation.items():
                    if oid == 'player':
                        players[a.defender] = players.get(a.defender, 0)+amount
                        if amount: hits.append((attacker.object_id, attacker.controller, a.defender, amount))
                    else: creatures[oid] = creatures.get(oid, 0)+amount
            for blocker in blockers:
                if self.deals_in(blocker, stage):
                    amount = max(0, blocker.power)
                    creatures[attacker.object_id] = creatures.get(attacker.object_id, 0)+amount
                    assignments.append(dict(source=blocker.object_id, controller=blocker.controller,
                                            creature_damage={attacker.object_id: amount}, player_damage=0))
        for entry in assignments:
            for oid, amount in entry['creature_damage'].items():
                t.rules.get(oid).damage_marked += amount
                t.rules.events.append(Event('damage_creature', entry['controller'], entry['source'],
                                            target_id=oid, amount=amount))
        lives = {p.seat: p.life for p in t.players}
        result = t.rules.damage_players(lives, players, player.seat)
        for seat, amount in players.items():
            target = t.players[seat]; target.life = lives[seat]; target.damage_taken += amount
            player.damage_dealt += amount
            t.emit('damage', source=player.seat, target=seat, amount=amount, cause='combat')
        if len(result.eliminated) > 1: t.counts['multi_elimination_events'] += 1
        for oid, controller, seat, amount in hits:
            t._apply_pending(t.rules.triggers(Event('combat_damage_player', controller, oid, amount=amount)))
        t.rules._dirty()
        record = dict(stage=stage, attackers=[(a.attacker, a.defender, a.blocked, list(a.blockers)) for a in self.attacks],
                      assignments=assignments, creature_damage=creatures, player_damage=players)
        t.combat_batches.append(record)
        t.note(f'    COMBAT DAMAGE {stage}: creatures={creatures}; players={players}.')
        return record
