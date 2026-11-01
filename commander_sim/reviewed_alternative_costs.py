"""Reviewed alternatives for black Phyrexian symbols and K'rrik spell costs.

No mana is created: each substitution removes one black pip and costs two
real life. Only independently reviewed printed Phyrexian symbols or a live
Oracle-pinned K'rrik can authorize this. Generic payment remains in the
existing TemplateManaService; no parallel mana engine is introduced.
"""
from dataclasses import dataclass
from .mana_costs import FixedManaCost, parse_fixed_mana_cost
from .reviewed_cost_reduction import cost_symbols

_KRRIK_ID = "cbe3a4e7-5dbe-4f58-8ee6-a1762b65acfd"
_KRRIK_TEXT = ("({B/P} can be paid with either {B} or 2 life.)\nLifelink\n"
               "For each {B} in a cost, you may pay 2 life rather than pay that mana.\n"
               "Whenever you cast a black spell, put a +1/+1 counter on K'rrik.")


def reviewed_krrik(name, raw):
    return bool(name == "K'rrik, Son of Yawgmoth"
                and isinstance(raw, dict)
                and raw.get("oracle_id") == _KRRIK_ID
                and raw.get("oracle_text") == _KRRIK_TEXT)


def controls_reviewed_krrik(kernel, catalog, seat):
    return any(obj.zone == "battlefield" and obj.controller == seat
               and obj.card.name == "K'rrik, Son of Yawgmoth"
               and obj.card.card_id == _KRRIK_ID
               and reviewed_krrik(obj.card.name, catalog.get(obj.card.name))
               for obj in kernel.objects.values())


@dataclass(frozen=True)
class BlackLifeOption:
    mana_cost: str
    life_cost: int
    substituted_symbols: int


def black_life_options(printed_mana_cost, payable_fixed_cost, *,
                       krrik_active=False, available_life=40):
    """List legal bounded spell-cost alternatives, minimum life first.

    printed_mana_cost is source-verified by the caller. We only allow
    Phyrexian B/P symbols, not an arbitrary multi/hybrid cost approximation.
    """
    if type(printed_mana_cost) is not str or "{B/P}" not in printed_mana_cost:
        printed_phyrexian = 0
    else:
        printed_phyrexian = printed_mana_cost.count("{B/P}")
    normalized = printed_mana_cost.replace("{B/P}", "{B}")
    parse_fixed_mana_cost(normalized)  # reject unreviewed hybrid/X alternatives
    cost = parse_fixed_mana_cost(payable_fixed_cost)
    black = cost.colored.count("B")
    allowable = black if krrik_active else min(black, printed_phyrexian)
    result = []
    for count in range(allowable+1):
        life = 2 * count
        if available_life <= life:
            break  # conservative: do not voluntarily pay down to zero life
        remaining = list(cost.colored)
        for _ in range(count):
            remaining.remove("B")
        result.append(BlackLifeOption(
            cost_symbols(FixedManaCost(cost.generic,tuple(remaining))),
            life,count))
    return tuple(result)
