"""Actual spell-cast event drives reusable permanent counter triggers."""
import json
import unittest
from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.reviewed_cast_reactions import resolve_cast_reactions


class CastReactionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=next(f for f in EXPERIMENTAL_FIXTURES
               if f.key=="mortarion_physical_final")
        cls.catalog={e["deck_name"]:e["card"] for e in
                     json.loads(f.snapshot_path.read_text())["cards"]}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=7)
        self.C=C

    def add(self,name,*,zone,types,colors):
        raw=self.catalog.get(name,{})
        return self.zones.add(self.C(
            raw.get("oracle_id","test:"+name),name,frozenset(types),
            colors=frozenset(colors),coverage="approx"),0,zone)

    def test_krrik_gains_counter_for_verified_black_spell_cast(self):
        k=self.add("K'rrik, Son of Yawgmoth",zone="battlefield",
                   types=("creature",),colors=("B",))
        spell=self.add("Sign in Blood",zone="hand",types=("sorcery",),
                       colors=("B",))
        ticket=self.zones.cast(0,spell)
        result=resolve_cast_reactions(
            self.zones,0,self.catalog,source_spell=self.kernel.get(ticket.object_id))
        self.assertEqual(len(result),1)
        self.assertEqual(self.kernel.get(k).counters["+1/+1"],1)

    def test_colorless_spell_cannot_trigger_black_cast_reaction(self):
        k=self.add("K'rrik, Son of Yawgmoth",zone="battlefield",
                   types=("creature",),colors=("B",))
        spell=self.add("Sol Ring",zone="hand",types=("artifact",),colors=())
        ticket=self.zones.cast(0,spell)
        result=resolve_cast_reactions(
            self.zones,0,self.catalog,source_spell=self.kernel.get(ticket.object_id))
        self.assertEqual(result,())
        self.assertEqual(self.kernel.get(k).counters["+1/+1"],0)

    def test_nonmatching_source_uuid_cannot_get_reaction(self):
        k=self.add("K'rrik, Son of Yawgmoth",zone="battlefield",
                   types=("creature",),colors=("B",))
        impostor=self.kernel.get(k)
        impostor.card=self.C("fake","K'rrik, Son of Yawgmoth",
                             frozenset({"creature"}),coverage="approx")
        spell=self.add("Sign in Blood",zone="hand",types=("sorcery",),colors=("B",))
        ticket=self.zones.cast(0,spell)
        self.assertEqual(resolve_cast_reactions(
            self.zones,0,self.catalog,source_spell=self.kernel.get(ticket.object_id)),())


if __name__=="__main__":
    unittest.main()
