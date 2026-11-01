"""Unit contracts for the two source-reviewed live trigger bindings."""
import unittest
from types import SimpleNamespace as NS

from commander_sim.live_trigger_bridge import (
    BARAL_LOOT, MAGECRAFT_DRAW, PYROMANCER_TOKEN, KILN_TREASURE,
    TriggerToken, LiveTriggerBridge, TRIGGER_CARDS,
)


def make_object(oid, card_id, name, operations, zone="battlefield"):
    return NS(object_id=oid, zone=zone,
              card=NS(card_id=card_id,name=name,
                      abilities=tuple(NS(kind="triggered",op=op,event=event)
                         for op,event in operations)))


class LiveTriggerBridgeTests(unittest.TestCase):
    def setUp(self):
        self.baral=make_object(11,"named:Baral, Chief of Compliance",
            "Baral, Chief of Compliance",
            (("optional_loot","spell_countered_by"),))
        self.mage=make_object(22,"named:Archmage Emeritus","Archmage Emeritus",
            (("draw","spell_cast"),("draw","spell_copied")))
        self.pyro=make_object(31,"named:Young Pyromancer","Young Pyromancer",
            (("create_token","spell_cast"),))
        self.kiln=make_object(41,"named:Storm-Kiln Artist","Storm-Kiln Artist",
            (("create_token","spell_cast"),("create_token","spell_copied")))
        for obj,token in ((self.pyro,"elemental_1_1"),(self.kiln,"treasure")):
            obj.card.abilities=tuple(NS(kind=a.kind,op=a.op,event=a.event,
                args=(("token_id",token),)) for a in obj.card.abilities)
        self.kernel=NS(objects={11:self.baral,22:self.mage,31:self.pyro,41:self.kiln})
        self.bridge=LiveTriggerBridge(self.kernel)

    def test_reviewed_sources_have_pinned_ids_and_operations(self):
        self.assertEqual(BARAL_LOOT.oracle_id,
                         "baf80db7-2ca8-4bfc-b5b6-25ed51878dd7")
        self.assertEqual(MAGECRAFT_DRAW.oracle_id,
                         "8305d576-21d8-4ce7-8eda-a7cd9793aca5")
        self.assertEqual(set(TRIGGER_CARDS),
            {"named:Baral, Chief of Compliance","named:Archmage Emeritus",
             "named:Young Pyromancer","named:Storm-Kiln Artist"})

    def test_registration_is_idempotent_for_same_object_and_event(self):
        self.assertTrue(self.bridge.register(self.baral))
        self.assertTrue(self.bridge.register(self.baral))
        self.assertEqual(len(self.bridge.subscriptions._live),1)
        self.assertTrue(self.bridge.subscriptions.contains(
            11,BARAL_LOOT.slots[0],"spell_countered_by"))

    def test_multiple_hooks_register_for_one_magecraft_ability(self):
        self.assertTrue(self.bridge.register(self.mage))
        self.assertEqual(len(self.bridge.subscriptions._live),2)
        self.assertTrue(self.bridge.subscriptions.contains(
            22,MAGECRAFT_DRAW.slots[0],"spell_cast"))
        self.assertTrue(self.bridge.subscriptions.contains(
            22,MAGECRAFT_DRAW.slots[0],"spell_copied"))

    def test_stack_event_is_dispatched_only_after_queue_registration(self):
        item=NS(source_id=11,op="optional_loot")
        self.assertTrue(self.bridge.queued(item))
        calls=[]
        self.assertTrue(self.bridge.execute(item,
            lambda spec:calls.append((spec.draw,spec.discard))))
        self.assertEqual(calls,[(1,1)])
        self.assertEqual(len(self.bridge.invocations),1)
        self.assertEqual(self.bridge.invocations[0].fidelity,"exact")
        self.assertEqual(self.bridge.invocations[0].source_object_id,11)

    def test_doubled_trigger_frames_execute_twice_not_once(self):
        item=NS(source_id=11,op="optional_loot")
        self.bridge.queued(item)
        calls=[]
        for _ in range(2):
            self.assertTrue(self.bridge.execute(item,lambda op:calls.append(op)))
        self.assertEqual(len(calls),2)
        self.assertEqual(len(self.bridge.invocations),2)
        self.assertEqual(len(self.bridge.subscriptions._live),1)

    def test_source_departure_retains_pending_trigger_then_prunes(self):
        item=NS(source_id=11,op="optional_loot")
        self.bridge.queued(item)
        self.baral.zone="graveyard"
        self.assertEqual(self.bridge.reconcile((11,)),())
        self.assertTrue(self.bridge.execute(item,lambda _:None))
        self.assertEqual(self.bridge.reconcile(()),(11,))
        self.assertEqual(len(self.bridge.subscriptions._live),0)
        self.assertFalse(self.bridge.execute(item,lambda _:None))

    def test_failed_callback_writes_no_false_provenance(self):
        item=NS(source_id=11,op="optional_loot")
        self.bridge.queued(item)
        def rejected(_):
            raise ValueError("Illegal discard")
        with self.assertRaises(ValueError):
            self.bridge.execute(item,rejected)
        self.assertEqual(self.bridge.invocations,[])

    def test_pinned_token_slots_and_two_kiln_hooks(self):
        self.assertEqual(PYROMANCER_TOKEN.slots[0].declaration.token_id,"elemental_1_1")
        self.assertEqual(KILN_TREASURE.slots[0].declaration.token_id,"treasure")
        self.assertTrue(self.bridge.register(self.pyro))
        self.assertTrue(self.bridge.register(self.kiln))
        self.assertEqual(len([s for s in self.bridge.subscriptions._live if s[0]==31]),1)
        self.assertEqual(len([s for s in self.bridge.subscriptions._live if s[0]==41]),2)

    def test_token_trigger_rejects_mismatched_token_or_quantity(self):
        self.bridge.register(self.pyro)
        wrong=NS(source_id=31,op="create_token",
                 args=(("token_id","treasure"),),quantity=1)
        with self.assertRaises(ValueError):
            self.bridge.execute(wrong,lambda _:None)
        doubled=NS(source_id=31,op="create_token",
                   args=(("token_id","elemental_1_1"),),quantity=2)
        with self.assertRaises(ValueError):
            self.bridge.execute(doubled,lambda _:None)
        self.assertEqual(self.bridge.invocations,[])

    def test_token_triggers_commit_each_stack_frame_and_provenance_once(self):
        self.bridge.register(self.kiln)
        item=NS(source_id=41,op="create_token",
                args=(("token_id","treasure"),),quantity=1)
        seen=[]
        for _ in range(2):
            self.assertTrue(self.bridge.execute(item,lambda x:seen.append(x.token_id)))
        self.assertEqual(seen,["treasure","treasure"])
        self.assertEqual(len(self.bridge.invocations),2)
        self.assertEqual(len(self.bridge.subscriptions._live),2)

    def test_unreviewed_token_source_cannot_claim_existing_registration(self):
        fake=make_object(50,"named:Young Pyromancer","Young Pyromancer",
            (("create_token","spell_cast"),))
        fake.card.abilities=(NS(kind="triggered",op="create_token",
                               event="spell_cast",args=(("token_id","treasure"),)),)
        self.kernel.objects[50]=fake
        self.assertFalse(self.bridge.register(fake))
        self.assertFalse(self.bridge.queued(NS(source_id=50,op="create_token")))
        self.assertEqual(self.bridge.invocations,[])

    def test_unknown_or_wrong_card_identity_never_registers(self):
        fake=make_object(33,"named:Baral, Chief of Compliance",
                         "Unreviewed Card",(("optional_loot","spell_countered_by"),))
        self.kernel.objects[33]=fake
        self.assertFalse(self.bridge.register(fake))
        self.assertFalse(self.bridge.queued(NS(source_id=33,op="optional_loot")))
        self.assertFalse(self.bridge.execute(NS(source_id=33,op="optional_loot"),
                                             lambda _:None))


if __name__=="__main__":
    unittest.main()
