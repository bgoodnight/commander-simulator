"""Bounded loop execution and safe, explicit symbolic shortcut contracts.

The solver never guesses a loop from card names or declares a win from mana alone.
A caller must provide a separately verified repeatable cycle and an available
response window; otherwise the result is unresolved/declined.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from math import ceil
from rules import ExecutionGuard, SafetyStop

@dataclass(frozen=True)
class LoopCertificate:
    key:str
    # Issued by a validated rules-specific combo evaluator, NOT the pilot's claim.
    validated:bool
    preserves_required_pieces:bool
    resources_sustain_cycle:bool
    # positive damage is to EACH specified opponent after all replacements/prevention
    damage_each_opponent:int=0
    draw_per_cycle:int=0
    mana_gain_per_cycle:int=0
    creates_creatures_per_cycle:int=0
    targets:tuple[int,...]=()
    response_window_resolved:bool=False
    opaque_effects:bool=False

@dataclass(frozen=True)
class LoopOutcome:
    kind:str        # lethal / symbolic_mana / finite / declined / unresolved
    cycles:int=0
    reason:str=''
    damage:tuple[tuple[int,int],...]=()
    symbolic_mana:bool=False

@dataclass
class PilotSafety:
    """Pilot policy: don't deck yourself for a speculative card advantage loop."""
    min_library_reserve:int=1
    stop_when_lethal:bool=True
    max_nonlethal_cycles:int=64

class LoopResolver:
    def __init__(self,guard:ExecutionGuard|None=None,policy:PilotSafety|None=None):
        self.guard=guard or ExecutionGuard();self.policy=policy or PilotSafety()
    def evaluate(self,certificate:LoopCertificate,life:dict[int,int],library_size:int):
        c=certificate
        if not (c.validated and c.preserves_required_pieces and c.resources_sustain_cycle):
            return LoopOutcome('unresolved',reason='loop_not_proven_repeatable')
        if c.opaque_effects:return LoopOutcome('unresolved',reason='opaque_effect_needs_manual_handler')
        if not c.response_window_resolved:return LoopOutcome('unresolved',reason='opponents_have_unresolved_response_window')
        if c.draw_per_cycle<0 or c.damage_each_opponent<0 or c.mana_gain_per_cycle<0:return LoopOutcome('declined',reason='invalid_negative_loop_delta')
        if c.targets and set(c.targets)!=set(life):return LoopOutcome('unresolved',reason='unaccounted_opponents')
        if not c.targets and (c.damage_each_opponent or c.creates_creatures_per_cycle):
            return LoopOutcome('unresolved',reason='ambiguous_targets')
        if c.damage_each_opponent>0 and life:
            cycles=max(ceil(h/c.damage_each_opponent) for h in life.values() if h>0) if any(h>0 for h in life.values()) else 0
            if cycles*c.draw_per_cycle>max(0,library_size-self.policy.min_library_reserve):
                return LoopOutcome('declined',reason='would_deck_before_lethal')
            # This represents a mathematical proof of lethal, not iteration. The
            # table MUST still apply actual damage/replacements and elimination.
            return LoopOutcome('lethal',cycles=cycles,damage=tuple(sorted((p,cycles*c.damage_each_opponent) for p in life)))
        if c.mana_gain_per_cycle>0 and c.draw_per_cycle==0 and c.creates_creatures_per_cycle==0:
            # No infinity-valued integers; future costs query a symbolic flag.
            return LoopOutcome('symbolic_mana',symbolic_mana=True,reason='arbitrary_finite_mana_available')
        if c.draw_per_cycle:
            n=min(self.policy.max_nonlethal_cycles,max(0,(library_size-self.policy.min_library_reserve)//c.draw_per_cycle))
            if n==0:return LoopOutcome('declined',reason='prevent_self_deck')
            return LoopOutcome('finite',cycles=n,reason='bounded_by_library_and_pilot_policy')
        return LoopOutcome('declined',reason='nonlethal_loop_has_no_useful_bounded_payoff')

class SafeActionRunner:
    """Shared turn/stack/action guard for any pilot and any game seat.

    If a pilot repeats an identical full public+private state, stop unresolved.
    The fingerprint must include hidden resources used by the actor, including
    hand/library positions, rather than board alone.
    """
    def __init__(self,guard:ExecutionGuard|None=None):self.guard=guard or ExecutionGuard()
    def execute(self,turn,action_supplier,apply_action,fingerprint):
        self.guard.new_turn(turn);count=0
        try:
            while True:
                action=action_supplier()
                if action is None:return {'status':'complete','actions':count}
                self.guard.check((fingerprint(),repr(action)))
                if not apply_action(action):return {'status':'unresolved','reason':'illegal_or_failed_action','actions':count}
                count+=1
        except SafetyStop as exc:
            return {'status':'unresolved','reason':exc.reason,'actions':count}
