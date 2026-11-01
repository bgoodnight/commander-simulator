"""Shared historical v17-v35 tutor resolver; one search operation, typed options.

The historical tables retain the legal cast, event/trigger and priority logic.
Only the card-independent steps -- eligibility, ranked selection, exact-ID
movement, shuffle/re-top, event logging -- live here. Each registered card
declares its restrictions using the same EffectTemplate as the M3 backend.

No Oracle text interpretation, custom card-name branches, or new zone state.
"""
from dataclasses import dataclass
from .effect_templates import EffectTemplate


@dataclass(frozen=True)
class HistoricalSearch:
    operation: str
    effect: EffectTemplate
    event: str

    def __post_init__(self):
        if not self.event or not self.operation or self.effect.kind != "library_search":
            raise ValueError("Invalid reviewed historical search")


def _search(types, *, subtype=(), colors=(), maximum=None, destination="hand"):
    return EffectTemplate("library_search", search_types=frozenset(types),
                          search_subtypes=frozenset(subtype),
                          search_colors=frozenset(colors),
                          max_mana_value=maximum,
                          destination=destination, reveal=True, shuffle=True)


# Card-specific information is declarative, and may be validated against the
# reviewed Oracle snapshots when new source adapters are promoted.
HISTORICAL_SEARCHES = {
    "mystical_tutor": HistoricalSearch("mystical_tutor",
        _search(("instant", "sorcery"), destination="library_top"), "mystical_tutor"),
    "personal_tutor": HistoricalSearch("personal_tutor",
        _search(("sorcery",), destination="library_top"), "personal_tutor"),
    "merchant_scroll": HistoricalSearch("merchant_scroll",
        _search(("instant",), colors=("U",)), "merchant_scroll"),
    "solve_equation": HistoricalSearch("solve_equation",
        _search(("instant", "sorcery")), "solve_equation"),
    "fabricate": HistoricalSearch("fabricate",
        _search(("artifact",)), "fabricate"),
    "wizardcycling": HistoricalSearch("wizardcycling",
        _search(("any",), subtype=("Wizard",)), "wizardcycling"),
    "spellseeker": HistoricalSearch("spellseeker",
        _search(("instant", "sorcery"), maximum=2), "spellseeker"),
}


def eligible_search_ids(table, seat, effect, *, printed_colors=None, mana_value=None):
    """Evaluate reviewed restrictions on authoritative library objects.

    Missing required characteristics are UNKNOWN, not legal: e.g. Merchant
    Scroll refuses to run if any candidate instant has unverified color.
    An actual target remains subject to the existing table's timing and stack.
    """
    if not isinstance(effect, EffectTemplate) or effect.kind != "library_search":
        raise TypeError("Expected a library-search effect")
    ids = tuple(table.zones.ids(seat, "library"))
    found = []
    for oid in ids:
        obj = table.rules.get(oid)
        if "any" not in effect.search_types and not obj.types & effect.search_types:
            continue
        if effect.search_subtypes:
            subtypes = table.rules.subtypes(oid)
            if subtypes is None:
                raise NotImplementedError("Tutor subtype is unknown")
            if not effect.search_subtypes <= frozenset(subtypes):
                continue
        if effect.search_colors:
            if printed_colors is None or obj.card.name not in printed_colors:
                raise NotImplementedError("Tutor needs verified printed colors")
            if not effect.search_colors <= frozenset(printed_colors[obj.card.name]):
                continue
        if effect.max_mana_value is not None:
            if mana_value is None:
                raise NotImplementedError("Tutor needs verified printed mana value")
            value = mana_value(obj.card.name)
            if type(value) not in (int, float) or value < 0:
                raise NotImplementedError("Unverified mana value")
            if value > effect.max_mana_value:
                continue
        found.append(oid)
    return tuple(found)


def resolve_historical_search(table, seat, key, *, printed_colors=None,
                              mana_value=None):
    """Execute one reusable reviewed tutor resolution via original table APIs.

    Selection policies, full-library search, fail-to-find, shuffle, and
    library-top ordering remain the historical semantics. Return the new
    object ID for hand destinations, otherwise the selected library ID.
    """
    spec = HISTORICAL_SEARCHES[key]
    effect = spec.effect
    eligible = eligible_search_ids(table, seat, effect,
                                   printed_colors=printed_colors, mana_value=mana_value)
    request = table.selection.request(spec.operation, seat, eligible)
    ranked = sorted(request.cards, key=lambda c: -table.selection.score(seat, c))
    default = ranked[0].object_id if ranked else None
    policy = getattr(table, "tutor_policy", None)
    chosen = policy(request) if policy else default
    if chosen is not None and chosen not in eligible:
        raise ValueError("Search must choose an eligible library object or fail to find")
    name = table.rules.get(chosen).card.name if chosen is not None else None
    if effect.destination == "hand":
        new_id = table.zones.move(chosen, "hand") if chosen is not None else None
        table.zones.shuffle(seat)
        result_id = new_id
        table.tutor_events.append((spec.event, seat, result_id, name))
        table.note(f"    {spec.event.upper()} P{seat}: revealed {name}, put into hand, then shuffled.")
    elif effect.destination == "library_top":
        table.zones.shuffle(seat)
        if chosen is not None:
            order = table.zones.order[seat, "library"]
            order.remove(chosen)
            order.append(chosen)
            table.rules._dirty()
        result_id = chosen
        table.tutor_events.append((spec.event, seat, result_id, name))
        table.note(f"    {spec.event.upper()} P{seat}: revealed {name}; shuffled, then placed on top.")
    else:
        raise NotImplementedError("Historical tutor destination is not supported")
    return result_id
