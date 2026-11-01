"""Opt-in adapter binding reviewed ability slots to the historical live stack.

The existing GameKernel discovers triggers; its priority stack orders and
resolves them. This adapter registers only pinned, already-supported
triggers and invokes their old host operations via AbilityDispatcher.
No Oracle parser, duplicate trigger generator or second mutable game state.
"""
from dataclasses import dataclass

from .ability_composition import (AbilitySlot, AbilityHandler, ComposedCard,
                                  AbilityDispatcher, TriggerSubscriptions)
from .legacy_common_ops import DrawDiscard


_BARAL_ID = "baf80db7-2ca8-4bfc-b5b6-25ed51878dd7"
_BARAL_TEXT = ("Instant and sorcery spells you cast cost {1} less to cast.\n"
               "Whenever a spell or ability you control counters a spell, you may draw a card. "
               "If you do, discard a card.")
_MAGE_ID = "8305d576-21d8-4ce7-8eda-a7cd9793aca5"
_MAGE_TEXT = "Magecraft — Whenever you cast or copy an instant or sorcery spell, draw a card."
_PYRO_ID = "5fac139a-07d3-4e6c-98e3-d98b199f7a6f"
_PYRO_TEXT = "Whenever you cast an instant or sorcery spell, create a 1/1 red Elemental creature token."
_KILN_ID = "a145ff8c-5812-4bcb-bd16-9839dc25121d"
_KILN_TEXT = ("This creature gets +1/+0 for each artifact you control.\n"
              "Magecraft — Whenever you cast or copy an instant or sorcery spell, create a Treasure token. "
              '(It\'s an artifact with "{T}, Sacrifice this token: Add one mana of any color.")')
_CAPABILITIES = frozenset({"historical_trigger_stack", "draw", "discard", "selection", "token_creation"})


@dataclass(frozen=True)
class TriggerToken:
    token_id: str
    count: int = 1

    def __post_init__(self):
        if not isinstance(self.token_id, str) or not self.token_id or type(self.count) is not int or self.count<1:
            raise ValueError("Invalid reviewed triggered token parameters")


def _reviewed_trigger(oracle_id, oracle_text, source_excerpt, kind, operation,
                      required):
    slot = AbilitySlot(oracle_id, "front", kind, "triggered", operation,
                       source_excerpt, "pinned-oracle-m1",
                       frozenset(required))
    return ComposedCard(
        oracle_id, oracle_text, (slot,),
        (AbilityHandler(slot.key, "exact", operation, slot.source_revision,
                        frozenset(required)),))


BARAL_LOOT = _reviewed_trigger(
    _BARAL_ID, _BARAL_TEXT,
    "Whenever a spell or ability you control counters a spell, you may draw a card. "
    "If you do, discard a card.",
    "optional_loot", DrawDiscard(1, 1, "baral_discard"),
    {"historical_trigger_stack", "draw", "discard", "selection"})
MAGECRAFT_DRAW = _reviewed_trigger(
    _MAGE_ID, _MAGE_TEXT, _MAGE_TEXT, "draw",
    DrawDiscard(1), {"historical_trigger_stack", "draw"})

PYROMANCER_TOKEN = _reviewed_trigger(
    _PYRO_ID, _PYRO_TEXT, _PYRO_TEXT, "create_token",
    TriggerToken("elemental_1_1"), {"historical_trigger_stack", "token_creation"})
KILN_TREASURE = _reviewed_trigger(
    _KILN_ID, _KILN_TEXT,
    'Magecraft — Whenever you cast or copy an instant or sorcery spell, create a Treasure token.',
    "create_token", TriggerToken("treasure"),
    {"historical_trigger_stack", "token_creation"})

# Explicitly reviewed historical names; never infer behavior from "Wizard",
# a card role, or raw Oracle text. Event hooks come from the existing kernel.
TRIGGER_CARDS = {
    "named:Baral, Chief of Compliance": (BARAL_LOOT, "optional_loot"),
    "named:Archmage Emeritus": (MAGECRAFT_DRAW, "draw"),
    "named:Young Pyromancer": (PYROMANCER_TOKEN, "create_token"),
    "named:Storm-Kiln Artist": (KILN_TREASURE, "create_token"),
}


class LiveTriggerBridge:
    def __init__(self, kernel, *, mode="strict"):
        self.kernel = kernel
        self.mode = mode
        self.subscriptions = TriggerSubscriptions()
        self._sources = {}
        self.invocations = []

    def _eligible(self, obj):
        if obj is None or obj.zone != "battlefield":
            return None
        registration = TRIGGER_CARDS.get(obj.card.card_id)
        if registration is None or obj.card.name != obj.card.card_id[6:]:
            return None
        card, operation = registration
        effect = card.slots[0].declaration
        hooks = tuple(a.event for a in obj.card.abilities
                      if a.kind == "triggered" and a.op == operation and a.event
                      and (not isinstance(effect, TriggerToken)
                           or dict(a.args).get("token_id") == effect.token_id))
        if not hooks:
            return None
        return card, operation, hooks

    def register(self, obj):
        """Register each unique source/slot/event hook; idempotent per object."""
        eligibility = self._eligible(obj)
        if eligibility is None:
            return False
        card, operation, hooks = eligibility
        if obj.object_id not in self._sources:
            self._sources[obj.object_id] = (
                operation, AbilityDispatcher(card, self.mode, _CAPABILITIES))
        for hook in hooks:
            self.subscriptions.subscribe(obj.object_id, card.slots[0], hook)
        return True

    def queued(self, item):
        obj = self.kernel.objects.get(item.source_id)
        if obj is not None:
            self.register(obj)
        entry = self._sources.get(item.source_id)
        return bool(entry and entry[0] == item.op)

    def execute(self, item, executor):
        """Resolve one *already queued* stack trigger using the existing host.

        The kernel has already determined trigger count, targets and timing.
        A doubled trigger has two separate stack frames, hence two separate
        executions. Departed sources are held as last-known registrations
        until their pending trigger frames have completed.
        """
        entry = self._sources.get(item.source_id)
        if entry is None or entry[0] != item.op:
            return False
        operation, dispatcher = entry
        declaration = dispatcher.card.slots[0].declaration
        if isinstance(declaration, TriggerToken):
            if (dict(item.args).get("token_id") != declaration.token_id
                    or item.quantity != 1):
                raise ValueError("Live token trigger does not match pinned parameters")
        before = len(dispatcher.events)
        dispatcher.invoke(operation, item.source_id, executor)
        self.invocations.extend(dispatcher.events[before:])
        return True

    def reconcile(self, pending_source_ids=()):
        """Discard departed source registrations after queued stack work ends.

        Caller supplies source IDs of unresolved pending/stack trigger frames.
        This does not suppress later independent triggers from a live source.
        """
        pending = set(pending_source_ids)
        departed = tuple(oid for oid in self._sources
                         if oid not in pending and
                         (oid not in self.kernel.objects or
                          self.kernel.objects[oid].zone != "battlefield"))
        for oid in departed:
            self.subscriptions.unsubscribe(oid)
            del self._sources[oid]
        return departed
