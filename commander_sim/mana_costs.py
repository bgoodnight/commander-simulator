"""Conservative source-backed mana-cost *feasibility* for shared M2 rules.

This is a pure payment-planning service, not a second game engine and not a
spell-cast action. No object taps, zones, events, or abilities are mutated.
Only printed fixed {W}{U}{B}{R}{G}{C} and {N} costs are supported. Effects,
alternative/additional costs, Commander tax, reducers, timing, targets, and
mana abilities beyond the caller's reviewed sources remain unimplemented.
The authoritative kernel must validate those separately before casting.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import re

SYMBOLS = "WUBRGC"


class UnsupportedManaCost(ValueError):
    """Cost cannot be safely evaluated by the fixed-source planner."""


@dataclass(frozen=True)
class FixedManaCost:
    generic: int
    colored: tuple[str, ...]

    def __post_init__(self):
        if type(self.generic) is not int or self.generic < 0:
            raise ValueError("Generic mana must be a nonnegative integer")
        if any(symbol not in SYMBOLS for symbol in self.colored):
            raise ValueError("Unrecognized single-color mana requirement")

    @property
    def mana_value(self):
        return self.generic + len(self.colored)


def parse_fixed_mana_cost(value: str) -> FixedManaCost:
    """Fail closed on X, hybrids, phyrexian, snow, half and unknown symbols."""
    if not isinstance(value, str) or not value:
        raise UnsupportedManaCost("Missing printed mana cost")
    chunks = re.findall(r"\{([^{}]*)\}", value)
    if not chunks or "".join("{" + x + "}" for x in chunks) != value:
        raise UnsupportedManaCost("Malformed mana cost")
    generic = 0
    colored = []
    for x in chunks:
        if x in SYMBOLS:
            colored.append(x)
        elif re.fullmatch(r"0|[1-9]\d*", x):
            generic += int(x)
        else:
            raise UnsupportedManaCost("Unsupported mana symbol {" + x + "}")
    return FixedManaCost(generic, tuple(colored))


def plan_source_payment(cost: FixedManaCost, sources) -> tuple[int, ...] | None:
    """Choose distinct source indices for pips then generic mana.

    sources is an ordered collection of reviewed available per-source mana
    choices (e.g., a Swamp is {"B"}, a Command Tower is {"U","R"}).
    A source is activated at most once. Return the activation indices, ordered
    by pip then generic, or None if no assignment exists. This planning does
    not claim the spell is legally castable.
    """
    if not isinstance(cost, FixedManaCost):
        raise TypeError("Expected FixedManaCost")
    checked = []
    for options in sources:
        if isinstance(options, str):
            raise ValueError("A source must list mana choices, not a string")
        opts = frozenset(options)
        if not opts or any(x not in SYMBOLS for x in opts):
            raise ValueError("Source contains no recognized mana choices")
        checked.append(opts)
    if len(checked) < cost.mana_value:
        return None
    # Smaller choice sets first prevents a flexible Command Tower being spent
    # before a basic land that can only supply a single pip.
    requirements = tuple(sorted(cost.colored,
                                key=lambda c: (sum(c in opts for opts in checked), c)))
    if any(not any(symbol in opts for opts in checked) for symbol in requirements):
        return None

    @lru_cache(None)
    def choose(pip, used):
        if pip == len(requirements):
            remaining = tuple(i for i in range(len(checked))
                              if not used & (1 << i))
            if len(remaining) >= cost.generic:
                return remaining[:cost.generic]
            return None
        symbol = requirements[pip]
        for index, options in enumerate(checked):
            if symbol not in options or used & (1 << index):
                continue
            suffix = choose(pip + 1, used | (1 << index))
            if suffix is not None:
                return (index,) + suffix
        return None

    return choose(0, 0)
