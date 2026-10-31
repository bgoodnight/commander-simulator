"""Pure ability-slot registration and fidelity selection.

This module NEVER executes card effects, reads Scryfall, or changes game state.
It provides an explicit, testable seam for future rules-engine integration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Mode(str, Enum):
    STRICT = "strict"
    OBSERVATION = "observation"
    HYBRID = "hybrid"


class Fidelity(str, Enum):
    EXACT = "exact"
    SIMPLIFIED = "simplified"


@dataclass(frozen=True)
class AbilityKey:
    """Stable printed-ability identity; a different ability has a different key."""

    oracle_id: str
    face_id: str
    slot_id: str

    def __post_init__(self):
        if any(not isinstance(x, str) or not x.strip()
               for x in (self.oracle_id, self.face_id, self.slot_id)):
            raise ValueError("Ability key must have nonempty Oracle, face and slot IDs")


@dataclass(frozen=True)
class AbilitySlot:
    """Reviewed declaration, not inferred from card type or role label."""

    key: AbilityKey
    kind: str
    required_capabilities: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self):
        if not isinstance(self.key, AbilityKey):
            raise TypeError("Expected AbilityKey")
        if not isinstance(self.kind, str) or not self.kind.strip():
            raise ValueError("Ability kind is required")
        object.__setattr__(self, "required_capabilities", frozenset(self.required_capabilities))


@dataclass(frozen=True)
class AbilityHandler:
    """A descriptor for one reviewed implementation; not executable rules text.

    operation_id names a future typed effect composition, not a Python callback
    or Oracle-text expression.
    """

    key: AbilityKey
    fidelity: Fidelity
    operation_id: str
    source_revision: str
    required_capabilities: frozenset[str] = field(default_factory=frozenset)
    assumptions: tuple[str, ...] = ()
    reviewed: bool = False

    def __post_init__(self):
        if not isinstance(self.key, AbilityKey) or not isinstance(self.fidelity, Fidelity):
            raise TypeError("Handler requires AbilityKey and Fidelity")
        if any(not isinstance(x, str) or not x.strip()
               for x in (self.operation_id, self.source_revision)):
            raise ValueError("Handler must identify operation and source revision")
        object.__setattr__(self, "required_capabilities", frozenset(self.required_capabilities))
        object.__setattr__(self, "assumptions", tuple(self.assumptions))
        if self.fidelity is Fidelity.SIMPLIFIED:
            if not self.reviewed or not self.assumptions or any(
                not isinstance(a, str) or not a.strip() for a in self.assumptions
            ):
                raise ValueError("Simplified handlers require explicit review and assumptions")


@dataclass(frozen=True)
class Resolution:
    """Selected at most one handler for one slot; no operation is executed."""

    key: AbilityKey
    mode: Mode
    handler: AbilityHandler | None
    reason: str


class AbilityCatalog:
    """Per-deck-independent ability slots and handlers, frozen before gameplay.

    Exact and simplified implementations can coexist as descriptors, but
    resolution picks at most one for a particular ability slot and mode.
    A separate keyword or triggered ability keeps its own independent slot.
    """

    def __init__(self):
        self._slots: dict[AbilityKey, AbilitySlot] = {}
        self._handlers: dict[tuple[AbilityKey, Fidelity], AbilityHandler] = {}
        self._frozen = False

    def register_slot(self, slot: AbilitySlot):
        if self._frozen:
            raise RuntimeError("Ability catalog is frozen")
        if not isinstance(slot, AbilitySlot):
            raise TypeError("Expected AbilitySlot")
        if slot.key in self._slots:
            raise ValueError(f"Duplicate ability slot: {slot.key}")
        self._slots[slot.key] = slot

    def register_handler(self, handler: AbilityHandler):
        if self._frozen:
            raise RuntimeError("Ability catalog is frozen")
        if not isinstance(handler, AbilityHandler):
            raise TypeError("Expected AbilityHandler")
        if handler.key not in self._slots:
            raise KeyError(f"Unregistered ability slot: {handler.key}")
        key = (handler.key, handler.fidelity)
        if key in self._handlers:
            raise ValueError(f"Duplicate fidelity handler for slot: {key}")
        self._handlers[key] = handler

    def freeze(self):
        """Prevent subsequent registry edits during a simulated game."""
        self._frozen = True

    def resolve(self, key: AbilityKey, mode: Mode | str,
                capabilities: frozenset[str] = frozenset()) -> Resolution:
        mode = Mode(mode)
        slot = self._slots[key]  # missing identity is an error, not an inferred ability
        if mode is Mode.OBSERVATION:
            return Resolution(key, mode, None, "observation_only")
        capabilities = frozenset(capabilities)
        if not slot.required_capabilities <= capabilities:
            return Resolution(key, mode, None, "missing_slot_capabilities")
        candidates = ((Fidelity.EXACT, Fidelity.SIMPLIFIED)
                      if mode is Mode.HYBRID else (Fidelity.EXACT,))
        missing = False
        for fidelity in candidates:
            handler = self._handlers.get((key, fidelity))
            if handler is None:
                continue
            if not handler.required_capabilities <= capabilities:
                missing = True
                continue
            return Resolution(key, mode, handler, "selected")
        return Resolution(key, mode, None,
                          "missing_handler_capabilities" if missing else "unsupported")
