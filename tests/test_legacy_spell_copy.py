"""Shared v33/v35 copy action construction, retarget restrictions and events."""
import unittest
from dataclasses import dataclass
from types import SimpleNamespace as NS

from commander_sim.legacy_spell_copy import (
    CopyTargetRule, COPY_TARGET_RULES, prepare_reviewed_spell_copy,
    commit_reviewed_spell_copy,
)


@dataclass
class Action:
    source: str
    effect: str
    actor: int = 0
    card_type: str = "instant"
    target_object: int | None = None
    target: int | None = None
    step_targets: tuple[int, ...] = ()


@dataclass(frozen=True)
class Event:
    name: str
    controller: int
    spell_types: frozenset[str] = frozenset()


class DummyStack:
    def __init__(self):
        self.frames = {}
        self.spells = []
    def get(self, oid):
        return self.frames.get(oid)
    def spell(self, action, ticket):
        self.spells.append((action, ticket))


class DummyTable:
    def __init__(self):
        self.spell_stack = DummyStack()
        self.copy_actions = set()
        self.copy_counter_types = {}
        self.notes = []
        self.pending = []
        self.trigger_events = []
        self.rules = NS(objects={
            8: NS(controller=1), 9: NS(controller=2)
        }, get=lambda oid: NS(controller=1 if oid == 8 else 2),
                        events=[], triggers=self._triggers)
        self.note = self.notes.append
        self._apply_pending = self.pending.extend
        self.targets_legal = lambda action: action.target_object in (8, 9)
        self.legal_step_targets = lambda seat: (8,9)
        self.copy_target_legal = lambda oid: oid == 20

    def _triggers(self, event):
        self.trigger_events.append(event)
        return (event.name,)


class CommonCopyTests(unittest.TestCase):
    def setUp(self):
        self.t = DummyTable()
        self.counter_types = {"Negate": frozenset({"noncreature"})}

    def test_untargeted_spell_copy_keeps_existing_action_mode(self):
        original = Action("Consider", "named_consider", actor=1)
        copied = prepare_reviewed_spell_copy(self.t,original,0,
            allowed_effects=frozenset(),counter_types=self.counter_types)
        self.assertIsNot(copied,original)
        self.assertEqual(copied.actor,0)
        self.assertEqual(original.actor,1)

    def test_single_permanent_retarget_updates_only_copy(self):
        original = Action("Rift","named_cyclonic_rift",target_object=8,target=1)
        self.t.copy_target_policy = lambda seat,action: 9
        copied=prepare_reviewed_spell_copy(self.t,original,0,
            allowed_effects=frozenset({"named_cyclonic_rift"}),
            counter_types=self.counter_types)
        self.assertEqual((copied.target_object,copied.target),(9,2))
        self.assertEqual(original.target_object,8)

    def test_illegal_target_rejected_without_commit(self):
        original=Action("Rift","named_cyclonic_rift",target_object=8)
        self.t.copy_target_policy=lambda seat,action:99
        with self.assertRaises(ValueError):
            prepare_reviewed_spell_copy(self.t,original,0,
               allowed_effects=frozenset({"named_cyclonic_rift"}),
               counter_types=self.counter_types)
        self.assertEqual(self.t.spell_stack.spells,[])

    def test_two_target_copy_preserves_original_and_checks_changes(self):
        original=Action("Step Through","named_step_through",card_type="sorcery",
                        step_targets=(8,9))
        self.t.copy_target_policy=lambda seat,action:(9,8)
        copied=prepare_reviewed_spell_copy(self.t,original,0,
            allowed_effects=frozenset({"named_step_through"}),
            counter_types=self.counter_types)
        self.assertEqual(copied.step_targets,(9,8))
        self.assertEqual(original.step_targets,(8,9))
        self.t.copy_target_policy=lambda seat,action:(9,99)
        with self.assertRaises(ValueError):
            prepare_reviewed_spell_copy(self.t,original,0,
                allowed_effects=frozenset({"named_step_through"}),
                counter_types=self.counter_types)

    def test_counterspell_retarget_honors_counter_type(self):
        original=Action("Negate","counter",target_object=10)
        self.t.spell_stack.frames[11] = NS(kind="spell",
            action=NS(card_type="creature"),controller=1)
        self.t.copy_target_policy=lambda seat,action:11
        with self.assertRaises(ValueError):
            prepare_reviewed_spell_copy(self.t,original,0,
                allowed_effects=frozenset({"counter"}),
                counter_types=self.counter_types)
        self.t.spell_stack.frames[12] = NS(kind="spell",
            action=NS(card_type="instant"),controller=2)
        self.t.copy_target_policy=lambda seat,action:12
        copied=prepare_reviewed_spell_copy(self.t,original,0,
            allowed_effects=frozenset({"counter"}),
            counter_types=self.counter_types)
        self.assertEqual((copied.target_object,copied.target),(12,2))

    def test_reiterate_target_must_be_copyable(self):
        original=Action("Reiterate","named_reiterate",target_object=20)
        self.t.copy_target_policy=lambda seat,action:99
        with self.assertRaises(ValueError):
            prepare_reviewed_spell_copy(self.t,original,0,
                allowed_effects=frozenset({"named_reiterate"}),
                counter_types=self.counter_types)

    def test_virtual_copy_commits_single_event_without_new_card(self):
        copied=Action("Consider","named_consider")
        commit_reviewed_spell_copy(self.t,copied,0,Event,self.counter_types)
        self.assertIn(id(copied),self.t.copy_actions)
        self.assertEqual(len(self.t.spell_stack.spells),1)
        self.assertIs(self.t.spell_stack.spells[0][0],copied)
        self.assertEqual([x.name for x in self.t.rules.events],["spell_copied"])
        self.assertEqual(self.t.pending,["spell_copied"])
        self.assertNotIn("spell_cast",[x.name for x in self.t.rules.events])

    def test_copy_counter_mode_registers_restrictions(self):
        copied=Action("Negate","counter")
        commit_reviewed_spell_copy(self.t,copied,0,Event,self.counter_types)
        self.assertEqual(self.t.copy_counter_types[id(copied)],
                         frozenset({"noncreature"}))

    def test_shared_event_identity_is_configurable_for_old_engine_parity(self):
        copied=Action("Consider","named_consider")
        commit_reviewed_spell_copy(self.t,copied,0,Event,self.counter_types,
                                    reuse_event=True)
        self.assertIs(self.t.trigger_events[0],self.t.rules.events[0])

    def test_unsupported_retarget_category_fails_closed(self):
        with self.assertRaises(ValueError):
            CopyTargetRule("unrestricted")
        self.assertEqual(COPY_TARGET_RULES["named_step_through"].mode,
                         "two_creatures")


if __name__ == "__main__":
    unittest.main()
