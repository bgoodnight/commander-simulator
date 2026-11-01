"""Reusable early-game resource assessment and tutor targeting policy.

Policy is deliberately separate from Magic rules. All candidates must first
pass the existing Oracle-pinned eligibility and physical payment checks.
This module never grants a cast, search, mana ability, or activated ability.
"""
from dataclasses import dataclass

from .reviewed_rocks import reviewed_rock


@dataclass(frozen=True)
class ResourceSnapshot:
    land_sources: int
    rock_sources: int
    treasure_sources: int
    floating_mana: int
    available_fixed_mana: int

    @property
    def reusable_sources(self):
        return self.land_sources + self.rock_sources


def assess_resources(kernel, mana_service, seat=0):
    """Count authoritative, untapped sources without consuming them.

    available_fixed_mana is a conservative upper bound for independently
    activatable simple mana modes, not a promise that a particular colored
    spell is payable. Sacrifice engines and conditional costs are excluded.
    """
    if mana_service.kernel is not kernel:
        raise ValueError("Resource snapshot requires the active mana service")
    lands = rocks = treasures = mana = 0
    for obj in kernel.objects.values():
        if obj.zone != "battlefield" or obj.controller != seat or obj.tapped:
            continue
        modes = mana_service.modes(obj)
        if not modes:
            continue
        simple = [m for m in modes if not m.activation_generic
                  and not m.activation_colors and not m.life and not m.damage]
        if not simple:
            continue
        value = max(len(m.output) for m in simple)
        mana += value
        if "land" in obj.types:
            lands += 1
        elif obj.token and obj.card.card_id == "reviewed-token:Treasure":
            treasures += 1
        elif "artifact" in obj.types:
            rocks += 1
    floating = sum(mana_service.floating(seat))
    return ResourceSnapshot(lands, rocks, treasures, floating, mana + floating)


def choose_tutor_target(zones, seat, eligible_ids, catalog, commander_colors,
                        *, preference="ramp"):
    """Rank only eligible *physical* library objects.

    Ramp-first is a policy, not an invented tutor effect. This generalizes
    across every tutor type: restrictions and destinations are enforced by the
    existing reviewed search templates before calling this function.
    """
    if preference not in {"ramp", "neutral"}:
        raise ValueError("Unknown tutor preference")
    if not eligible_ids:
        return None
    valid = set(zones.ids(seat, "library"))
    if any(type(i) is not int or i not in valid for i in eligible_ids):
        raise ValueError("Tutor candidates must be physical library IDs")
    def rank(oid):
        obj = zones.kernel.get(oid)
        raw = catalog.get(obj.card.name)
        rock = reviewed_rock(obj.card.name, raw, commander_colors) if raw else None
        if preference == "ramp" and rock is not None:
            # Prefer efficient, immediately reusable sources. Sol Ring's
            # two-mana output is a general property, not a name exception.
            effect, cost = rock
            production = max((len(mode.output) for mode in effect.mana_modes
                              if not mode.life and not mode.damage and not mode.sacrifice),
                             default=0)
            return (0, -production, effect.enter_tapped, cost, obj.card.name, oid)
        return (1, 0, False, "", obj.card.name, oid)
    return min(eligible_ids, key=rank)
