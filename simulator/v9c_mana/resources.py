"""Bounded ordered mana-ability planning over the live kernel's physical IDs.

Only U/R/colorless pools and U/R/generic costs. All activated sources tap;
Treasure also sacrifices. Identical source abilities are grouped to avoid
permuting interchangeable Islands. No state mutates during planning.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
import heapq
from itertools import count
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v9b_live'))
import state  # initialize versioned shared-kernel imports
from rules import Cost, Event, SafetyStop

ZERO = (0, 0, 0)  # C, U, R

@dataclass(frozen=True)
class Ability:
    output: tuple[int, int, int]
    cost: Cost = Cost()
    life: int = 0
    damage: int = 0
    sacrifice: bool = False
    def __post_init__(self):
        if len(self.output) != 3 or any(not isinstance(x, int) or x < 0 for x in self.output) or sum(self.output) == 0:
            raise ValueError('Mana output must be three nonnegative integers with a positive total')
        if min(self.life, self.damage) < 0:
            raise ValueError('Negative life or damage cost')

@dataclass(frozen=True)
class Activation:
    source_id: int
    ability: Ability
    remaining_before_output: tuple[int, int, int]

@dataclass(frozen=True)
class Plan:
    seat: int
    signature: tuple
    cost: Cost
    activations: tuple[Activation, ...]
    unused: tuple[int, int, int]
    states: int
    excluded: tuple[int, ...] = ()


def spend(pool, cost):
    """All distinct legal pools after spending, including colored activation costs."""
    c, u, r = pool
    if u < cost.blue or r < cost.red:
        return ()
    u -= cost.blue; r -= cost.red
    if c + u + r < cost.generic:
        return ()
    results = []
    # Deterministic preference: C, then R, preserving U when possible.
    for use_c in range(min(c, cost.generic), -1, -1):
        left = cost.generic - use_c
        for use_r in range(min(r, left), -1, -1):
            use_u = left - use_r
            if use_u <= u:
                results.append((c - use_c, u - use_u, r - use_r))
    return tuple(results)


def fixed(*outputs, life=0, damage=0, sacrifice=False):
    return tuple(Ability(output, life=life, damage=damage, sacrifice=sacrifice) for output in outputs)

C = (1, 0, 0); U = (0, 1, 0); R = (0, 0, 1)


class Resources:
    def __init__(self, table, max_states=20000):
        self.table = table; self.kernel = table.rules; self.max_states = max_states
        self.kernel.mana_pools = {seat: ZERO for seat in range(4)}
        self.payments = []; self.activations = []; self._cache = {}
        self.max_states_seen = 0; self.cache_hits = 0

    def pool(self, seat):
        return self.kernel.mana_pools[seat]

    def abilities(self, obj, visiting=frozenset()):
        from provider import abilities_for
        return abilities_for(self, obj, visiting)

    def sources(self, seat, ready=True):
        result = []
        for obj in self.kernel.on_battlefield():
            if obj.controller != seat or ready and obj.tapped: continue
            abilities = self.abilities(obj)
            if abilities: result.append((obj.object_id, abilities))
        return tuple(result)

    def capacity(self, seat, ready=True):
        # Read-side pilot heuristic only. Legality always uses plan(), including
        # the funding/order constraints omitted from this upper bound.
        return sum(self.pool(seat)) + sum(max(sum(a.output) - a.cost.total for a in abilities)
                                          for _, abilities in self.sources(seat, ready))

    def signature(self, seat):
        p = self.table.players[seat]
        return (seat, p.life, p.eliminated_round, self.pool(seat), self.sources(seat), self.max_states)

    def plan(self, seat, cost, excluded=()):
        if not isinstance(cost, Cost): raise TypeError('Expected U/R/generic Cost')
        excluded = tuple(sorted(set(excluded)))
        signature = self.signature(seat)
        key = signature, cost, excluded
        if key in self._cache:
            self.cache_hits += 1
            return self._cache[key]
        p = self.table.players[seat]
        if p.eliminated_round is not None: return None
        groups = defaultdict(list)
        for oid, abilities in self.sources(seat):
            if oid not in excluded: groups[abilities].append(oid)
        groups = tuple((abilities, tuple(sorted(ids))) for abilities, ids in groups.items())
        used = (0,) * len(groups)
        serial = count(); queue = [(0, 0, 0, next(serial), used, self.pool(seat), p.life, ())]
        visited = set(); states = 0
        enqueued = {(used, self.pool(seat), p.life): (0, 0, 0)}
        while queue:
            depth, harm, sacrifices, _, used, pool, life, actions = heapq.heappop(queue)
            state = used, pool, life
            if state in visited: continue
            visited.add(state); states += 1
            if states > self.max_states: raise SafetyStop('mana_search_budget')
            paid = spend(pool, cost)
            if paid:
                plan = Plan(seat, signature, cost, actions, paid[0], states, excluded)
                self.max_states_seen = max(self.max_states_seen, states)
                if len(self._cache) > 512: self._cache.clear()
                self._cache[key] = plan
                return plan
            for i, (abilities, ids) in enumerate(groups):
                if used[i] == len(ids): continue
                oid = ids[used[i]]
                for ability in abilities:
                    if ability.life and life < ability.life: continue
                    for left in spend(pool, ability.cost):
                        nxt = tuple(left[j] + ability.output[j] for j in range(3))
                        counts = list(used); counts[i] += 1
                        next_life = life - ability.life - ability.damage
                        next_state = tuple(counts), nxt, next_life
                        rank = depth + 1, harm + ability.life + ability.damage, sacrifices + int(ability.sacrifice)
                        if next_state in enqueued and enqueued[next_state] <= rank: continue
                        enqueued[next_state] = rank
                        activation = Activation(oid, ability, left)
                        heapq.heappush(queue, (*rank, next(serial), tuple(counts),
                                              nxt, next_life, actions + (activation,)))
        self.max_states_seen = max(self.max_states_seen, states)
        if len(self._cache) > 512: self._cache.clear()
        self._cache[key] = None
        return None

    def activate(self, seat, activation, defer_sba=False):
        obj = self.kernel.get(activation.source_id)
        ability = activation.ability
        p = self.table.players[seat]
        if (obj.controller != seat or obj.zone != 'battlefield' or obj.tapped
                or ability not in self.abilities(obj) or (ability.life and p.life < ability.life)
                or p.eliminated_round is not None):
            raise ValueError('Illegal mana ability activation')
        if activation.remaining_before_output not in spend(self.pool(seat), ability.cost):
            raise ValueError('Activation cost cannot be paid')
        name = obj.card.name
        obj.tapped = True
        p.life -= ability.life + ability.damage
        p.damage_taken += ability.damage
        if ability.sacrifice:
            self.table.world.move(obj.object_id, 'graveyard', 'sacrifice')
        self.kernel.mana_pools[seat] = tuple(activation.remaining_before_output[i] + ability.output[i] for i in range(3))
        self.kernel._dirty()
        self.kernel.events.append(Event('mana_added', seat, activation.source_id, amount=sum(ability.output)))
        if ability.life: self.kernel.events.append(Event('life_paid', seat, activation.source_id, amount=ability.life))
        if ability.damage:
            self.kernel.events.append(Event('damage_player', seat, activation.source_id, amount=ability.damage, metadata=(('seat', seat), ('cause', 'mana_ability'))))
            self.table.emit('damage', source=seat, target=seat, amount=ability.damage, cause='mana_ability')
        self.activations.append(dict(seat=seat, source_id=activation.source_id, source=name,
                                     output=ability.output, activation_cost=(ability.cost.generic, ability.cost.blue, ability.cost.red),
                                     life_paid=ability.life, damage=ability.damage, sacrifice=ability.sacrifice))
        self.table.note(f'    MANA P{seat}: {name} #{activation.source_id} -> {ability.output}'
                        + (' (sacrificed)' if ability.sacrifice else ''))
        if not defer_sba and p.life <= 0: self.table.eliminate(p, 'mana_ability_life')

    def pay(self, seat, cost, plan=None, excluded=()):
        excluded = tuple(sorted(set(excluded)))
        plan = plan or self.plan(seat, cost, excluded)
        if plan is None: raise ValueError('Cannot pay mana cost')
        if (plan.seat != seat or plan.cost != cost or plan.signature != self.signature(seat)
                or plan.excluded != excluded or plan != self.plan(seat, cost, excluded)):
            raise ValueError('Stale mana plan')
        # The entire ordered sequence is validated by the immutable signature.
        # Planning failure/budget stops happen before any mutation.
        for activation in plan.activations:
            self.activate(seat, activation, defer_sba=True)
        if plan.unused not in spend(self.pool(seat), cost):
            raise AssertionError('Planner and committed payment differ')
        self.kernel.mana_pools[seat] = plan.unused
        self.kernel._dirty()
        self.payments.append(dict(seat=seat, cost=(cost.generic, cost.blue, cost.red),
                                  sources=[a.source_id for a in plan.activations], unused=plan.unused))
        return plan

    def empty_pools(self):
        for seat in range(4): self.kernel.mana_pools[seat] = ZERO
        self.kernel._dirty(); self._cache.clear()

    def untap(self, seat):
        for obj in self.kernel.on_battlefield():
            if obj.controller == seat: obj.tapped = False
        self.kernel._dirty(); self._cache.clear()

    def assert_consistent(self):
        for seat, pool in self.kernel.mana_pools.items():
            if len(pool) != 3 or min(pool) < 0 or any(not isinstance(x, int) for x in pool):
                raise AssertionError('Invalid mana pool')
            if self.table.players[seat].eliminated_round is not None and pool != ZERO:
                raise AssertionError('Eliminated player retains mana')
        return True


class SourcePayment:
    def __init__(self, resources): self.resources = resources
    @staticmethod
    def cost(action):
        u = action.parameters.get('U', 0); r = action.parameters.get('R', 0)
        if action.cost < u + r: raise ValueError('Cost cannot waive colored pips')
        return Cost(action.cost - u - r, u, r)
    def can_pay(self, player, action): return self.resources.plan(player.seat, self.cost(action)) is not None
    def pay(self, player, action):
        plan = self.resources.pay(player.seat, self.cost(action))
        if hasattr(player, 'payments'):
            player.payments.append(dict(source=action.source, cost=action.cost,
                                        source_ids=[a.source_id for a in plan.activations], unused=plan.unused))
        return plan
