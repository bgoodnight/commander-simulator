"""Shared reviewed virtual-spell-copy creation and retarget mechanics.

Historical v33/v35 rules retain priority, timing, target legality and stack
ownership. This module is a reusable effect composition, NOT a new spell
stack. Unknown retarget families fail closed rather than silently granting
new target-changing permissions.
"""
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class CopyTargetRule:
    """How a reviewed copy may keep or change its printed targets."""
    mode: str

    def __post_init__(self):
        if self.mode not in {"single_permanent", "counterspell",
                             "copy_spell", "two_creatures"}:
            raise ValueError("Unrecognized copy target operation")


COPY_TARGET_RULES = {
    "named_cyclonic_rift": CopyTargetRule("single_permanent"),
    "named_capsize": CopyTargetRule("single_permanent"),
    "named_abrade": CopyTargetRule("single_permanent"),
    "counter": CopyTargetRule("counterspell"),
    "named_reiterate": CopyTargetRule("copy_spell"),
    "named_step_through": CopyTargetRule("two_creatures"),
}


def prepare_reviewed_spell_copy(table, original, seat, *,
                                allowed_effects, counter_types):
    """Copy an existing action and apply legal *changed* targets only.

    The table still verifies the original spell frame is copyable. Retarget
    choices come exclusively from the historical policy; this operation
    validates each requested replacement using real stack/object predicates.
    """
    copied = replace(original, actor=seat)
    policy = getattr(table, "copy_target_policy", None)
    if original.effect not in allowed_effects:
        return copied
    rule = COPY_TARGET_RULES.get(original.effect)
    if rule is None:
        raise ValueError("Unreviewed copy targeting category")
    if rule.mode == "two_creatures":
        old = getattr(original, "step_targets", ())
        chosen = tuple(policy(seat, original)) if policy else old
        if len(chosen) != 2 or len(set(chosen)) != 2:
            raise ValueError("Copy requires two distinct targets")
        legal = table.legal_step_targets(seat)
        if any(new != prior and new not in legal
               for new, prior in zip(chosen, old)):
            raise ValueError("Illegal changed copy target")
        copied.step_targets = chosen
        return copied
    if not policy or original.target_object is None:
        return copied
    chosen = policy(seat, original)
    if chosen == original.target_object:
        return copied
    if rule.mode == "counterspell":
        target = table.spell_stack.get(chosen)
        allowed = counter_types[original.source]
        if (not target or target.kind != "spell"
                or not (target.action.card_type in allowed
                        or ("noncreature" in allowed
                            and target.action.card_type != "creature"))):
            raise ValueError("Illegal copied counterspell target")
        return replace(copied, target_object=chosen, target=target.controller)
    if rule.mode == "copy_spell":
        if not table.copy_target_legal(chosen):
            raise ValueError("Illegal copied Reiterate target")
        return replace(copied, target_object=chosen)
    if chosen not in table.rules.objects:
        raise ValueError("Invalid copy target")
    trial = replace(copied, target_object=chosen,
                    target=table.rules.get(chosen).controller)
    if not table.targets_legal(trial):
        raise ValueError("Illegal copy target")
    return trial


def commit_reviewed_spell_copy(table, copied, seat, Event, counter_types, *,
                               reuse_event=False):
    """Register one virtual spell, exactly one logical copy event and triggers.

    No hand card, mana source, recast, or new physical spell object is created.
    Reuse_event preserves v35 event identity; v33 historically uses a distinct
    equivalent event for trigger generation.
    """
    table.copy_actions.add(id(copied))
    if copied.effect == "counter":
        table.copy_counter_types[id(copied)] = counter_types[copied.source]
    table.spell_stack.spell(copied, None)
    event = Event("spell_copied", seat,
                  spell_types=frozenset({copied.card_type}))
    table.rules.events.append(event)
    trigger_event = (event if reuse_event else
                     Event("spell_copied", seat,
                           spell_types=frozenset({copied.card_type})))
    table._apply_pending(table.rules.triggers(trigger_event))
    table.note(f"    COPY P{seat}: {copied.source} copied onto stack (not cast).")
