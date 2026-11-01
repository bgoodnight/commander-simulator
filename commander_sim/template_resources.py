"""Six-color payment bridge for reviewed generic mana templates on physical IDs.

Uses the existing kernel as the only authoritative battlefield and mana-pool
owner. This is a small extension for the bounded early-game runner, not a new
full MTG resource/priority engine. It shares FixedManaCost and typed reviewed
mana modes; supports multi-pip rocks and funded Signets, with unused floating
mana retained until the phase boundary. Damage/life/sacrifice modes are not
activated until the host provides those rules.
"""
from dataclasses import dataclass
from heapq import heappush, heappop
from itertools import count

from .effect_templates import ManaMode
from .mana_costs import FixedManaCost, parse_fixed_mana_cost
from .mana_kernel_bridge import _reviewed_modes
from .reviewed_rocks import reviewed_rock
from .reviewed_lands import reviewed_land
from .reviewed_cost_reduction import reduced_fixed_cost, cost_symbols

ORDER = "WUBRGC"
ZERO = (0, 0, 0, 0, 0, 0)


def _add(pool, pips):
    out = list(pool)
    for pip in pips:
        out[ORDER.index(pip)] += 1
    return tuple(out)


def _spend(pool, cost):
    """All lawful residual pools after colored/true-C then generic spending."""
    if not isinstance(cost, FixedManaCost):
        raise TypeError("Expected fixed mana cost")
    remaining = list(pool)
    for pip in cost.colored:
        i = ORDER.index(pip)
        if not remaining[i]:
            return ()
        remaining[i] -= 1
    if sum(remaining) < cost.generic:
        return ()
    results = []
    # Prefer C for generic, preserving flexible colored mana when possible.
    def spend_generic(index, left, state):
        if index == len(ORDER):
            if left == 0:
                results.append(tuple(state))
            return
        for take in range(min(state[index], left), -1, -1):
            new = list(state)
            new[index] -= take
            spend_generic(index + 1, left-take, new)
    # Put C first to avoid bias toward spending W/U/B/R/G for generic.
    indices = [5, 0, 1, 2, 3, 4]
    def recurse(j, left, state):
        if j == len(indices):
            if left == 0:
                results.append(tuple(state))
            return
        i = indices[j]
        for take in range(min(state[i], left), -1, -1):
            next_state = list(state)
            next_state[i] -= take
            recurse(j+1, left-take, next_state)
    recurse(0, cost.generic, remaining)
    return tuple(dict.fromkeys(results))


@dataclass(frozen=True)
class PlannedActivation:
    object_id: int
    mode: ManaMode


@dataclass(frozen=True)
class ResourcePayment:
    source_ids: tuple[int, ...]
    activations: tuple[PlannedActivation, ...]
    floating_after: tuple[int, ...]
    search_states: int


class TemplateManaService:
    """One source-ID payment planner for reviewed lands and mana-rock templates."""

    def __init__(self, kernel, card_metadata, commander_colors, *, max_states=16000,
                 zones=None):
        colors = frozenset(commander_colors)
        if not colors or any(x not in "WUBRG" for x in colors):
            raise ValueError("Invalid commander identity")
        if zones is not None and zones.kernel is not kernel:
            raise ValueError("Mana zones must share the authoritative kernel")
        self.kernel = kernel
        self.zones = zones
        self.card_metadata = card_metadata
        self.colors = colors
        self.max_states = max_states
        if not hasattr(kernel, "mana_pools"):
            kernel.mana_pools = {seat: ZERO for seat in range(4)}

    def floating(self, seat=0):
        return self.kernel.mana_pools[seat]

    def clear(self):
        for seat in range(4):
            self.kernel.mana_pools[seat] = ZERO
        self.kernel._dirty()

    def modes(self, obj):
        if obj.zone != "battlefield":
            return ()
        name = obj.card.name
        # This is the *reviewed token blueprint identity*, not a name match:
        # a printed card or arbitrary token named Treasure is not admitted.
        if (self.zones is not None and obj.token
                and obj.card.card_id == "reviewed-token:Treasure"
                and name == "Treasure"
                and "artifact" in obj.types and "Treasure" in obj.subtypes):
            return tuple(ManaMode((color,), tap=True, sacrifice=True)
                         for color in "WUBRG")
        if "land" in obj.types:
            basic=tuple(ManaMode((c,)) for c in sorted(_reviewed_modes(name, self.colors)))
            if basic:
                return basic
            raw=self.card_metadata.get(name)
            reviewed=reviewed_land(name,raw,self.colors)
            if reviewed is not None:
                return reviewed.modes(self.colors)
            # Shared review: Myriad Landscape's ordinary colorless tap mode.
            if name == "Myriad Landscape":
                from .reviewed_ramp import reviewed_ramp
                if reviewed_ramp(name,raw) is not None and obj.card.card_id == raw["oracle_id"]:
                    return (ManaMode(("C",)),)
            return ()
        if "artifact" in obj.types:
            card = self.card_metadata.get(name)
            if card is None:
                return ()
            reviewed = reviewed_rock(name, card, self.colors)
            if reviewed is not None:
                return tuple(mode for mode in reviewed[0].mana_modes
                             if mode.tap and not (mode.life or mode.damage or mode.sacrifice))
        return ()

    def spell_cost(self, seat, mana_cost, source):
        """Cost of a verified spell given live, independently reviewed reducers.

        This is a snapshot calculation, not an effect that grants casting
        permission. Unknown spell metadata cannot receive a reduction.
        """
        original = parse_fixed_mana_cost(mana_cost)
        if (source is None or not hasattr(source, "card")
                or type(seat) is not int or not 0 <= seat < 4
                or source.owner != seat):
            raise ValueError("Invalid physical spell source")
        raw = self.card_metadata.get(source.card.name)
        if (not isinstance(raw, dict)
                or raw.get("oracle_id") != source.card.card_id):
            return cost_symbols(original), ()
        printed = raw.get("colors")
        if not isinstance(printed, list):
            printed = list(source.card.colors or ())
        colors = frozenset(printed)
        spell_types = frozenset(source.types)
        cost, evidence = reduced_fixed_cost(
            self.kernel, self.card_metadata, seat, mana_cost,
            spell_types=spell_types, spell_colors=colors)
        return cost_symbols(cost), evidence

    def plan_spell(self, seat, mana_cost, source):
        payable, _ = self.spell_cost(seat, mana_cost, source)
        return self.plan(seat, payable)

    def pay_spell(self, seat, mana_cost, source):
        payable, _ = self.spell_cost(seat, mana_cost, source)
        return self.pay(seat, payable)

    def plan(self, seat, mana_cost, *, excluded_source_ids=()):
        cost = parse_fixed_mana_cost(mana_cost)
        excluded_source_ids = frozenset(excluded_source_ids)
        if any(type(oid) is not int for oid in excluded_source_ids):
            raise ValueError('Excluded source IDs must be integers')
        if type(seat) is not int or not 0 <= seat < 4:
            raise ValueError("Invalid seat")
        candidates = sorted((obj.object_id, self.modes(obj))
                            for obj in self.kernel.objects.values()
                            if obj.zone == "battlefield" and obj.controller == seat and not obj.tapped
                            and obj.object_id not in excluded_source_ids)
        candidates = [(oid, modes) for oid, modes in candidates if modes]
        initial = self.floating(seat)
        serial = count()
        heap = [(0, next(serial), 0, initial, ())]
        visited = set()
        states = 0
        while heap:
            depth, _, used, pool, actions = heappop(heap)
            if (used, pool) in visited:
                continue
            visited.add((used, pool))
            states += 1
            if states > self.max_states:
                raise ValueError("Bounded mana search exhausted; no action committed")
            paid = _spend(pool, cost)
            if paid:
                return ResourcePayment(tuple(action.object_id for action in actions),
                                       actions, paid[0], states)
            for idx, (oid, modes) in enumerate(candidates):
                if used & (1 << idx):
                    continue
                for mode in modes:
                    activation_cost = FixedManaCost(mode.activation_generic,
                                                    mode.activation_colors)
                    for funded in _spend(pool, activation_cost):
                        next_pool = _add(funded, mode.output)
                        heappush(heap, (depth+1, next(serial),
                                        used | (1 << idx), next_pool,
                                        actions + (PlannedActivation(oid, mode),)))
        return None

    def pay(self, seat, mana_cost, *, excluded_source_ids=()):
        """Commit an affordable plan from authoritative physical source IDs."""
        plan = self.plan(seat, mana_cost, excluded_source_ids=excluded_source_ids)
        if plan is None:
            return None
        # No callback between planning and commit: one synchronous turn driver.
        for action in plan.activations:
            obj = self.kernel.get(action.object_id)
            if (obj.zone != "battlefield" or obj.controller != seat or obj.tapped
                    or action.mode not in self.modes(obj)):
                raise ValueError("Stale source payment")
        for action in plan.activations:
            if action.mode.sacrifice:
                if self.zones is None:
                    raise ValueError("Sacrifice mode requires matching physical zones")
                self.zones.move(action.object_id, "graveyard", "sacrifice")
            else:
                self.kernel.get(action.object_id).tapped = True
        self.kernel.mana_pools[seat] = plan.floating_after
        self.kernel._dirty()
        return plan
