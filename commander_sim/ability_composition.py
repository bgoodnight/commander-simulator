"""Reviewed, ability-level composition and promotion for Commander cards.

This module is deliberately not a second engine. It selects one reviewed
operation *per printed ability slot*, then delegates state changes to an
existing kernel/table callback. Unregistered Oracle prose is never executable.
"""
from dataclasses import dataclass
from typing import Callable, Mapping
from uuid import UUID


MODES = frozenset({"strict", "hybrid", "observation"})
KINDS = frozenset({"mana", "spell", "activated", "triggered", "static", "keyword", "replacement"})
FIDELITIES = frozenset({"exact", "simplified"})


@dataclass(frozen=True)
class AbilitySlot:
    oracle_id: str
    face_id: str
    slot_id: str
    kind: str
    declaration: object
    source_text: str
    source_revision: str
    prereqs: frozenset[str] = frozenset()

    def __post_init__(self):
        try:
            if str(UUID(self.oracle_id)) != self.oracle_id:
                raise ValueError("Noncanonical Oracle UUID")
        except (TypeError, ValueError, AttributeError):
            raise ValueError("Ability slot requires a pinned Oracle UUID") from None
        if (not self.face_id or not self.slot_id or not self.source_text
                or not self.source_revision or self.kind not in KINDS
                or self.declaration is None
                or not isinstance(self.prereqs, frozenset)
                or any(not isinstance(p,str) or not p for p in self.prereqs)):
            raise ValueError("Invalid or incomplete reviewed ability slot")

    @property
    def key(self):
        return (self.oracle_id, self.face_id, self.slot_id)


@dataclass(frozen=True)
class AbilityHandler:
    slot_key: tuple[str, str, str]
    fidelity: str
    operation: object
    source_revision: str
    prereqs: frozenset[str] = frozenset()
    limitations: tuple[str, ...] = ()

    def __post_init__(self):
        if (len(self.slot_key) != 3 or self.fidelity not in FIDELITIES
                or self.operation is None or not self.source_revision
                or not isinstance(self.prereqs,frozenset)
                or any(not isinstance(p,str) or not p for p in self.prereqs)
                or not isinstance(self.limitations,tuple)):
            raise ValueError("Invalid ability handler")
        if self.fidelity=="simplified" and not self.limitations:
            raise ValueError("Simplified handler must describe its omissions")


@dataclass(frozen=True)
class ComposedCard:
    oracle_id: str
    oracle_text: str
    slots: tuple[AbilitySlot, ...]
    handlers: tuple[AbilityHandler, ...]

    def __post_init__(self):
        if not self.slots or not self.oracle_text:
            raise ValueError("Card requires reviewed ability slots and printed text")
        keys=set()
        for slot in self.slots:
            if slot.oracle_id!=self.oracle_id or slot.key in keys:
                raise ValueError("Duplicate or mismatched ability slot")
            keys.add(slot.key)
            if slot.source_text not in self.oracle_text:
                raise ValueError("Ability source excerpt absent from pinned Oracle text")
        seen=set()
        for h in self.handlers:
            if h.slot_key not in keys:
                raise ValueError("Handler for unknown ability slot")
            k=(h.slot_key,h.fidelity)
            if k in seen:
                raise ValueError("Multiple handlers at one fidelity for ability slot")
            seen.add(k)
            slot=next(s for s in self.slots if s.key==h.slot_key)
            if slot.source_revision!=h.source_revision:
                raise ValueError("Handler needs same reviewed source revision")
            # A promoted exact operation may be more precise than the earlier
            # simplified implementation. Require the *same reviewed effect
            # family*, not byte-identical parameters: otherwise promotion
            # could never correct a bounded approximation.
            if type(h.operation) is not type(slot.declaration):
                raise ValueError("Handler must use the reviewed operation type")
            if (hasattr(slot.declaration,"kind")
                    and h.operation.kind != slot.declaration.kind):
                raise ValueError("Handler cannot change the effect family")

    def slot(self, slot_id):
        return next((s for s in self.slots if s.slot_id==slot_id),None)

    def resolve(self, slot_id, mode, capabilities):
        if mode not in MODES:
            raise ValueError("Unknown fidelity policy")
        if not isinstance(capabilities,frozenset):
            raise TypeError("Capabilities must be an explicit immutable set")
        slot=self.slot(slot_id)
        if slot is None:
            return None
        if mode=="observation" or not slot.prereqs<=capabilities:
            return None
        by_fidelity={h.fidelity:h for h in self.handlers if h.slot_key==slot.key
                     and h.prereqs<=capabilities}
        return by_fidelity.get("exact") or (
            by_fidelity.get("simplified") if mode=="hybrid" else None)

    def coverage(self, mode, capabilities):
        return tuple((slot.slot_id,
                      (handler.fidelity if (handler:=self.resolve(
                          slot.slot_id,mode,capabilities)) else "unsupported"))
                     for slot in self.slots)


@dataclass(frozen=True)
class AbilityInvocation:
    slot_key: tuple[str,str,str]
    source_object_id: int
    fidelity: str
    source_revision: str
    outcome: str
    limitations: tuple[str,...]


class AbilityDispatcher:
    """One exact/simplified callback per reviewed ability, not per card.

    A callback supplied by the host may mutate its *existing* state; no
    callback is invoked for an unsupported slot or absent capability. The
    dispatcher never invents costs, timing, choices or permissions.
    """
    def __init__(self, card: ComposedCard, mode="strict",
                 capabilities=frozenset()):
        if mode not in MODES or not isinstance(capabilities,frozenset):
            raise ValueError("Invalid fidelity mode or capabilities")
        self.card=card
        self.mode=mode
        self.capabilities=capabilities
        self.events=[]

    def invoke(self, slot_id, source_object_id, executor: Callable):
        handler=self.card.resolve(slot_id,self.mode,self.capabilities)
        if handler is None:
            raise NotImplementedError("Unsupported reviewed ability in this mode")
        if type(source_object_id) is not int or source_object_id<0:
            raise ValueError("Physical source object ID required")
        if not callable(executor):
            raise TypeError("Host must supply executable rules operation")
        # No event is recorded on a rejected target or failed underlying action.
        result=executor(handler.operation)
        self.events.append(AbilityInvocation(handler.slot_key,source_object_id,
                          handler.fidelity,handler.source_revision,"resolved",
                          handler.limitations))
        return result


class TriggerSubscriptions:
    """Instance-local duplicate trigger guard; no global or hidden state."""
    def __init__(self):
        self._live=set()

    def subscribe(self, object_id, slot: AbilitySlot, hook):
        if (type(object_id) is not int or object_id<0 or not isinstance(slot,AbilitySlot)
                or slot.kind!="triggered" or not isinstance(hook,str) or not hook):
            raise ValueError("Invalid trigger subscription")
        token=(object_id,slot.key,hook)
        if token in self._live:
            return False
        self._live.add(token)
        return True

    def unsubscribe(self, object_id):
        old=len(self._live)
        self._live={entry for entry in self._live if entry[0]!=object_id}
        return old-len(self._live)

    def contains(self, object_id, slot, hook):
        return (object_id,slot.key,hook) in self._live


def inspected_search_card(name, *, include_historical_exact=False):
    """Compose pinned five-tutor review records into one real ability slot.

    Exact applies solely to the *already-tested historical search operation*,
    not general casting/trigger correctness or a whole-card exactness claim.
    Other cards (including nonsearch side effects) are not inferred.
    """
    from .effect_templates import compose_effect
    from .reviewed_tutors import TUTORS
    row=TUTORS.get(name)
    if row is None:
        return None
    review=row["review"]
    effect=compose_effect(review)
    kind="triggered" if name=="Spellseeker" else "spell"
    slot=AbilitySlot(review.oracle_id,"front","search",kind,effect,
                     review.oracle_text,"oracle-pinned-v1",
                     frozenset({"library_search"}))
    handlers=[AbilityHandler(slot.key,"simplified",effect,
                slot.source_revision,frozenset({"library_search"}),
                review.assumptions)]
    if include_historical_exact:
        handlers.append(AbilityHandler(slot.key,"exact",effect,
                         slot.source_revision,
                         frozenset({"library_search","historical_search"}),
                         ("Exact only for the historical verified search suboperation",)))
    return ComposedCard(review.oracle_id,review.oracle_text,(slot,),tuple(handlers))


def inspected_rock_card(name, commander_colors):
    """Compose separately identified mana/utility slots where Oracle reviewed.

    A printed extra ability without a supported handler remains visible and
    unsupported, rather than being silently omitted from the card model.
    """
    from .reviewed_rocks import ROCKS, reviewed_rock
    row=ROCKS.get(name)
    if row is None:
        return None
    review=row["review"]
    identity=dict(oracle_id=review.oracle_id,oracle_text=review.oracle_text,
                  mana_cost=row["printed_cost"],type_line="Artifact",layout="normal")
    effect,_=reviewed_rock(name,identity,commander_colors)
    mana_text=(review.oracle_text if name=="Talisman of Creativity"
               else review.oracle_text.splitlines()[0])
    mana=AbilitySlot(review.oracle_id,"front","mana", "mana",effect,
                     mana_text,"oracle-pinned-v1",frozenset({"mana_activation"}))
    handlers=[AbilityHandler(mana.key,"simplified",effect,mana.source_revision,
                             frozenset({"mana_activation"}),review.assumptions)]
    slots=[mana]
    if name in {"Mind Stone","Commander's Sphere"}:
        source="Sacrifice this artifact: Draw a card." if name=="Commander's Sphere" else (
               "{1}, {T}, Sacrifice this artifact: Draw a card.")
        slots.append(AbilitySlot(review.oracle_id,"front","sacrifice_draw",
                                "activated","draw_one_on_sacrifice",source,
                                "oracle-pinned-v1",frozenset({"sacrifice","draw"})))
    return ComposedCard(review.oracle_id,review.oracle_text,tuple(slots),tuple(handlers))
