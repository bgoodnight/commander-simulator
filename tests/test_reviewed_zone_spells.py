"""Reused zone effects: opponent graveyard theft and delayed on-death return."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_death_effects import (
    ReviewedDeathEngine,capture_battlefield)
from commander_sim.reviewed_zone_spells import (
    ZoneSpellEngine,reviewed_zone_spell)

class ZoneSpellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES if f.key=="mortarion_physical_final")
        cls.catalog={row["deck_name"]:row["card"] for row in
                     json.loads(f.snapshot_path.read_text())["cards"]}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=12)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.mana=TemplateManaService(
            self.kernel,self.catalog,frozenset({"B"}),zones=self.zones)
        self.death=ReviewedDeathEngine(self.zones,self.life,self.catalog)
        self.spells=ZoneSpellEngine(
            self.zones,self.life,self.catalog,self.mana,self.death)
        self.death.zone_spells=self.spells

    def add(self,name,seat=0,zone="battlefield",types=("creature",),
            power=2,toughness=2):
        raw=self.catalog.get(name,{})
        return self.zones.add(self.C(
            raw.get("oracle_id","test:"+name),name,frozenset(types),
            base_power=power,base_toughness=toughness,coverage="approx"),
            seat,zone)

    def land(self,n):
        for i in range(n):
            self.add("Swamp",types=("land",))

    def test_conscripting_real_opponent_graveyard_creature_exiles_rest(self):
        self.land(5)
        source=self.add("Nurgle's Conscription",zone="hand",types=("instant",))
        creature=self.add("Enemy One",seat=2,zone="graveyard",power=4,toughness=4)
        other=self.add("Enemy Two",seat=2,zone="graveyard")
        out=self.spells.cast(0,source,creature,turn=5)
        self.assertEqual(out.operation,"opponent_graveyard_theft")
        new=self.kernel.get(out.moved_ids[0])
        self.assertEqual(new.owner,2)
        self.assertEqual(new.controller,0)
        self.assertTrue(new.tapped)
        self.assertEqual(self.zones.names(2,"graveyard"),())
        self.assertEqual(len(self.zones.ids(2,"exile")),1)
        self.assertTrue(self.zones.assert_consistent())

    def test_undying_return_tracks_actual_death_and_counter(self):
        self.land(1)
        source=self.add("Undying Malice",zone="hand",types=("instant",))
        body=self.add("Own Body",power=3,toughness=3)
        activated=self.spells.cast(0,source,body,turn=3,expires_at_seat=2)
        self.assertIsNotNone(activated)
        before=capture_battlefield(self.kernel)
        ix=len(self.kernel.moves)
        self.zones.move(body,"graveyard","destroy")
        self.death.resolve_deaths(before,move_index=ix,turn=3)
        own=[o for o in self.kernel.on_battlefield() if o.card.name=="Own Body"]
        self.assertEqual(len(own),1)
        self.assertTrue(own[0].tapped)
        self.assertEqual(own[0].counters["+1/+1"],1)
        self.assertEqual(self.spells.pending_returns,{})
        self.assertTrue(self.zones.assert_consistent())

    def test_delayed_return_skips_card_already_moved_out_of_graveyard(self):
        self.land(1)
        instant=self.add("Undying Malice",zone="hand",types=("instant",))
        body=self.add("Target Body",power=2,toughness=3)
        self.assertIsNotNone(self.spells.cast(0,instant,body,turn=3))
        before=capture_battlefield(self.kernel)
        move_ix=len(self.kernel.moves)
        graveyard_id=self.zones.move(body,"graveyard","destroy")
        death_move=self.kernel.moves[move_ix]
        self.zones.move(graveyard_id,"exile","exile")
        returned=self.spells.observe_deaths(before,(death_move,),turn=3)
        self.assertEqual(returned,())
        self.assertEqual(self.spells.pending_returns,{})
        self.assertFalse(any(o.card.name=="Target Body" for o in
                             self.kernel.on_battlefield()))
        self.assertTrue(self.zones.assert_consistent())

    def test_temporary_permission_expires_at_active_turn_end(self):
        self.land(1)
        instant=self.add("Undying Malice",zone="hand",types=("instant",))
        creature=self.add("Body",power=2,toughness=2)
        self.spells.cast(0,instant,creature,turn=4,expires_at_seat=3)
        self.assertEqual(self.spells.expire(4,active_seat=1),())
        self.assertEqual(self.spells.expire(4,active_seat=3),(creature,))
        ix=len(self.kernel.moves)
        before=capture_battlefield(self.kernel)
        self.zones.move(creature,"graveyard","destroy")
        self.death.resolve_deaths(before,move_index=ix,turn=4)
        self.assertFalse(any(o.card.name=="Body" for o in
                         self.kernel.on_battlefield()))

    def test_wrong_pinned_spell_identity_fails_closed(self):
        bad=dict(self.catalog["Nurgle's Conscription"],oracle_id="fake")
        self.assertIsNone(reviewed_zone_spell("Nurgle's Conscription",bad))


if __name__=="__main__":
    unittest.main()
