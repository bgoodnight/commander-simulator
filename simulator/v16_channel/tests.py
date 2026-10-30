"""Focused tests for the in-progress channel cost calculation."""
import unittest
from types import SimpleNamespace
from channel_costs import channel_cost

def permanent(types, supertypes=()):
    return SimpleNamespace(types=set(types), card=SimpleNamespace(supertypes=set(supertypes)))

class ChannelCostTests(unittest.TestCase):
    def test_legendary_creatures_reduce_only_generic(self):
        creatures = [permanent(['creature'], ['legendary']) for _ in range(5)]
        self.assertEqual((channel_cost('Otawara, Soaring City', creatures).generic,
                          channel_cost('Otawara, Soaring City', creatures).blue), (0, 1))
        self.assertEqual(channel_cost('Sokenzan, Crucible of Defiance', creatures).red, 1)

    def test_only_legendary_creatures_count(self):
        cards = [permanent(['land'], ['legendary']), permanent(['creature']),
                 permanent(['creature', 'artifact'], ['legendary'])]
        self.assertEqual(channel_cost('Sokenzan, Crucible of Defiance', cards).generic, 2)

    def test_no_reduction(self):
        self.assertEqual(channel_cost('Otawara, Soaring City', []).generic, 3)

from channel_table import ChannelTable, OTAWARA, SOKENZAN

class ChannelIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.t = ChannelTable(seed=211)
        self.t.priority_policy = lambda *args: None
        self.t.active_seat = 0
        self.t.phase = 'main'
        self.t.spell_stack.holder = 0
        self.t.rules.mana_pools[0] = (10, 10, 10)
        self.p = self.t.details

    def give(self, name):
        card = next(c for c in self.p.hand + self.p.library if c.name == name)
        return card.object_id if card in self.p.hand else self.t.zones.move(card.object_id, 'hand')

    def choice(self, source, target=None):
        return next(c for c in self.t.priority_choices(0) if c.kind == 'channel'
                    and c.source_id == source and c.target_frame == target)

    def test_sokenzan_discards_before_resolution_and_creates_hasty_spirits(self):
        oid = self.give(SOKENZAN.name)
        self.t.commit_choice(0, self.choice(oid))
        self.assertNotIn(oid, self.t.rules.objects)
        self.assertIn(SOKENZAN.name, [c.name for c in self.t.zones.views(0, 'graveyard')])
        self.assertEqual(self.t.spell_stack.frames[-1].kind, 'activated')
        self.t.spell_stack.resolve()
        spirits = [o for o in self.t.rules.controlled(0) if o.card.name == 'Spirit']
        self.assertEqual(len(spirits), 2)
        self.assertTrue(all(o.token and 'Spirit' in o.subtypes and 'haste' in o.keywords for o in spirits))

    def test_otawara_returns_target(self):
        oid = self.give(OTAWARA.name)
        target = self.t.add_creature(self.t.players[1], 2, 2, 'target', token=True)
        self.t.commit_choice(0, self.choice(oid, target.id))
        self.t.spell_stack.resolve()
        self.assertNotIn(target.id, self.t.rules.objects)
        self.assertEqual(self.t.spell_stack.abilities_resolved, 1)

    def test_otawara_fizzles_if_target_leaves(self):
        oid = self.give(OTAWARA.name)
        target = self.t.add_creature(self.t.players[1], 2, 2, 'target', token=True)
        self.t.commit_choice(0, self.choice(oid, target.id))
        self.t.world.move(target.id, 'graveyard', 'destroy')
        self.t.spell_stack.resolve()
        self.assertEqual(self.t.spell_stack.fizzled, 1)

    def test_no_colored_mana_means_no_channel_choice(self):
        oid = self.give(SOKENZAN.name)
        self.t.rules.mana_pools[0] = (0, 0, 0)
        self.assertFalse(any(c.kind == 'channel' and c.source_id == oid for c in self.t.priority_choices(0)))

    def test_countered_ability_does_not_refund_discard(self):
        oid = self.give(SOKENZAN.name)
        self.t.commit_choice(0, self.choice(oid))
        frame = self.t.spell_stack.frames[-1]
        self.assertIsNotNone(self.t.spell_stack.counter(frame.frame_id, {'activated'}, 1))
        self.t.spell_stack.resolve()
        self.assertIn(SOKENZAN.name, [c.name for c in self.t.zones.views(0, 'graveyard')])
        self.assertFalse(any(o.card.name == 'Spirit' for o in self.t.rules.controlled(0)))

    def test_discarded_card_leaving_graveyard_does_not_stop_ability(self):
        oid = self.give(SOKENZAN.name)
        self.t.commit_choice(0, self.choice(oid))
        discarded = next(oid for oid in self.t.zones.ids(0, 'graveyard') if self.t.rules.get(oid).card.name == SOKENZAN.name)
        self.t.zones.move(discarded, 'exile', 'exile')
        self.t.spell_stack.resolve()
        self.assertEqual(sum(o.card.name == 'Spirit' for o in self.t.rules.controlled(0)), 2)

    def test_channel_is_not_a_spell(self):
        oid = self.give(SOKENZAN.name)
        before = self.t.spell_stack.spells_resolved
        self.t.commit_choice(0, self.choice(oid))
        self.t.spell_stack.resolve()
        self.assertEqual(self.t.spell_stack.spells_resolved, before)

    def test_shroud_target_is_illegal(self):
        oid = self.give(OTAWARA.name)
        target = self.t.add_creature(self.t.players[1], 2, 2, 'target', token=True, keywords=('shroud',))
        self.assertFalse(self.t.channel_available(0, oid, OTAWARA, target.id))

    def test_invalid_or_wrong_player_source(self):
        oid = self.give(SOKENZAN.name)
        self.assertFalse(self.t.channel_available(1, oid, SOKENZAN))
        self.assertFalse(self.t.channel_available(0, oid, OTAWARA))

    def test_brainstorm_resolves_in_response_to_channel(self):
        oid = self.give(SOKENZAN.name)
        self.give('Brainstorm')
        self.t.commit_choice(0, self.choice(oid))
        used = []
        def policy(seat, frames, choices):
            choice = next((c for c in choices if seat == 0 and frames and c.kind == 'spell'
                           and c.action.source == 'Brainstorm'), None)
            if choice and not used:
                used.append(True)
                return choice
            return None
        self.t.priority_policy = policy
        self.t.spell_stack.resolve()
        self.assertEqual(len(used), 1)
        resolved = [x for x in self.t.spell_stack.history if x[0] == 'resolve']
        self.assertEqual([x[2] for x in resolved[-2:]], ['spell', 'activated'])
        self.t.assert_consistent()

    def test_real_baral_has_legendary_metadata(self):
        self.assertIn('legendary', self.t.upgraded_definitions['Baral, Chief of Compliance'].supertypes)
        oid = self.give('Baral, Chief of Compliance')
        self.assertIn('legendary', self.t.rules.get(oid).card.supertypes)

if __name__ == '__main__':
    unittest.main()
