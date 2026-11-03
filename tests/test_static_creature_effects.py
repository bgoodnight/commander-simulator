"""Continuous creature-characteristic queries and lethal toughness regressions."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel, run_bounded_early_game
from commander_sim.reviewed_static_modifiers import (
    reviewed_static_rule, static_abilities, choose_creature_subtype,
    resolve_static_entry)


class StaticCreatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture=next(f for f in FIXTURES if f.key=="wretched_ranks")
        cls.catalog={row["deck_name"]:row["card"] for row in
                     json.loads(fixture.snapshot_path.read_text())["cards"]}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=21)
        self.C=C

    def creature(self,seat=0,name="Zombie",subtypes=("Zombie",),colors=("B",),
                 toughness=1,keywords=()):
        return self.zones.add(self.C(
            "test:"+name+str(seat),name,frozenset({"creature"}),
            subtypes=frozenset(subtypes),colors=frozenset(colors),
            base_power=1,base_toughness=toughness,
            keywords=frozenset(keywords),coverage="approx"),seat,"battlefield")

    def source(self,name,seat=0,zone="battlefield"):
        raw=self.catalog[name]
        return self.zones.add(self.C(
            raw["oracle_id"],name,frozenset({raw["type_line"].lower()}),
            abilities=static_abilities(name,raw),coverage="approx"),seat,zone)

    def test_global_color_and_controller_scopes_and_source_removal(self):
        a=self.creature(seat=0,name="Own black")
        b=self.creature(seat=1,name="Enemy black")
        c=self.creature(seat=1,name="Enemy green",colors=("G",))
        moon=self.source("Bad Moon")
        self.assertEqual([self.kernel.get(i).toughness for i in (a,b,c)],[2,2,1])
        self.assertEqual(self.kernel.get(a).power,2)
        moved=self.zones.move(moon,"graveyard","destroy")
        self.assertIn(moved,self.zones.ids(0,"graveyard"))
        self.assertEqual([self.kernel.get(i).toughness for i in (a,b,c)],[1,1,1])
        self.assertTrue(self.zones.assert_consistent())

    def test_zombie_anthem_stacks_and_entry_tokens_and_leaves(self):
        a=self.creature()
        b=self.creature(seat=1)
        mastery=self.source("Liliana's Mastery",zone="hand")
        entered=self.zones.move(mastery,"battlefield")
        # A controlled-subtype bonus never buffs an opponent.
        self.assertEqual(self.kernel.get(a).toughness,2)
        self.assertEqual(self.kernel.get(b).toughness,1)
        tokens=resolve_static_entry(self.zones,entered,self.catalog)
        self.assertEqual(len(tokens),2)
        self.assertEqual([self.kernel.get(i).toughness for i in tokens],[3,3])
        moon=self.source("Bad Moon")
        self.assertEqual(self.kernel.get(a).toughness,3)
        self.assertEqual([self.kernel.get(i).toughness for i in tokens],[4,4])
        self.zones.move(entered,"graveyard","destroy")
        self.assertEqual(self.kernel.get(a).toughness,2)
        self.assertEqual([self.kernel.get(i).toughness for i in tokens],[3,3])
        self.assertTrue(self.zones.assert_consistent())

    def test_chosen_subtype_is_explicit_and_follows_source_zone(self):
        z=self.creature(name="Zombie")
        h=self.creature(name="Human",subtypes=("Human",))
        banner=self.source("Patchwork Banner")
        self.assertEqual(self.kernel.get(z).toughness,1)
        choose_creature_subtype(self.kernel,banner,"Zombie")
        self.assertEqual(self.kernel.get(z).toughness,2)
        self.assertEqual(self.kernel.get(h).toughness,1)
        self.zones.move(banner,"graveyard","destroy")
        self.assertEqual(self.kernel.get(z).toughness,1)
        self.assertNotIn(banner,getattr(self.kernel,"static_choices",{}))

    def test_zero_toughness_ignores_indestructible_hexproof_and_shield(self):
        from rules import Ability
        target=self.creature(seat=1,name="Protected",colors=("G",),
                keywords=("indestructible","hexproof","shield"))
        defender=self.creature(seat=1,name="Larger",colors=("G",),toughness=4)
        minus=Ability(kind="static",op="creature_stat_modifier",args=(
            ("scope","all"),("power",-2),("toughness",-2)))
        rule=self.C("test:debuff","Continuous minus two",
                    frozenset({"enchantment"}),abilities=(minus,),
                    coverage="approx")
        src=self.zones.add(rule,0,"hand")
        entered=self.zones.move(src,"battlefield")
        self.assertNotIn(target,self.kernel.objects)
        self.assertIn(defender,self.kernel.objects)
        self.assertEqual(self.kernel.get(defender).toughness,2)
        moves=[m for m in self.kernel.moves if m.object_id==target]
        self.assertEqual(moves[-1].reason,"state_based")
        self.assertEqual(moves[-1].new_zone,"graveyard")
        self.assertTrue(self.zones.assert_consistent())

    def test_zero_toughness_cascade_when_anthem_source_dies(self):
        from rules import Ability
        friend=self.creature(name="Ally",toughness=1)
        bonus=Ability(kind="static",op="creature_stat_modifier",
                      args=(("scope","controller"),("power",1),("toughness",1)))
        anthem=self.zones.add(self.C("test:creatureanthem","Anthem Body",
             frozenset({"creature"}),base_power=1,base_toughness=1,
             abilities=(bonus,),coverage="approx"),0,"battlefield")
        penalty=Ability(kind="static",op="creature_stat_modifier",
                        args=(("scope","all"),("power",-1),("toughness",-1)))
        debuff=self.zones.add(self.C("test:penalty","Penalty",
            frozenset({"enchantment"}),abilities=(penalty,),
            coverage="approx"),1,"battlefield")
        self.assertEqual(self.kernel.get(friend).toughness,1)
        self.kernel.get(anthem).damage_marked=1
        self.kernel.check_state_based()
        self.assertNotIn(anthem,self.kernel.objects)
        self.assertNotIn(friend,self.kernel.objects)
        self.assertIn(debuff,self.kernel.objects)
        self.assertTrue(self.zones.assert_consistent())

    def test_oracle_mismatch_fails_closed(self):
        raw=self.catalog["Bad Moon"]
        self.assertIsNone(reviewed_static_rule("Bad Moon",
            dict(raw,oracle_text="Black creatures get +2/+2.")))
        self.assertEqual(static_abilities("Bad Moon",
            dict(raw,oracle_id="mismatch")),())


if __name__=="__main__":
    unittest.main()
