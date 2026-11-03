"""Four equal-seat physical kernel / abstract archetype integration checks."""
import unittest

from commander_sim.four_seat_alpha import SharedFourSeatTable


class FourSeatAlphaTests(unittest.TestCase):
    def test_every_seat_has_independent_ninety_nine_card_library(self):
        t=SharedFourSeatTable(("aggro","control","combo","midrange"),seed=7)
        self.assertEqual(len(t.kernel.objects),396)
        self.assertEqual([len(t.zones.ids(seat,"library")) for seat in range(4)],
                         [99]*4)
        self.assertEqual(set(o.owner for o in t.kernel.objects.values()),set(range(4)))
        self.assertIs(t.zones.kernel,t.life.kernel)
        self.assertIs(t.zones.kernel,t.mana.kernel)
        self.assertTrue(t.zones.assert_consistent())

    def test_all_archetypes_have_creatures_and_generic_spell_types(self):
        t=SharedFourSeatTable(("aggro","control","combo","midrange"),seed=7)
        for seat in range(4):
            types=[o.types for o in t.kernel.objects.values() if o.owner==seat]
            self.assertTrue(any("creature" in ty for ty in types))
            self.assertTrue(any("artifact" in ty for ty in types))
            self.assertTrue(any("sorcery" in ty for ty in types))
            self.assertTrue(any("instant" in ty for ty in types))

    def test_generic_mana_can_only_use_own_physical_sources(self):
        t=SharedFourSeatTable(("aggro","control","combo","midrange"),seed=7)
        card=t.CardDefinition("calibration:0:land:0:ordinary","Test generic land",
                              frozenset({"land"}),coverage="approx")
        a=t.zones.add(card,0,"battlefield")
        b=t.zones.add(card,1,"battlefield")
        self.assertEqual(t.mana.plan(0,"{1}").source_ids,(a,))
        self.assertEqual(t.mana.plan(1,"{1}").source_ids,(b,))
        self.assertIsNone(t.mana.plan(2,"{1}"))
        paid=t.mana.pay(0,"{1}")
        self.assertEqual(paid.source_ids,(a,))
        self.assertTrue(t.kernel.get(a).tapped)
        self.assertFalse(t.kernel.get(b).tapped)

    def test_shared_host_runs_four_active_seats_without_zone_corruption(self):
        t=SharedFourSeatTable(("aggro","control","combo","midrange"),
                              seed=9,round_limit=5).run()
        self.assertTrue(t.zones.assert_consistent())
        self.assertTrue(t.history)
        self.assertEqual(len(t.order),4)
        self.assertEqual(set(t.order),set(range(4)))
        self.assertTrue(all(set(row["seats"])=={"0","1","2","3"} for row in t.history))
        self.assertTrue(any(e["action"]=="land_play" for e in t.events))
        self.assertTrue(any(e["action"]=="abstract_cast" for e in t.events))
        self.assertEqual(t.summary()["four_real_decks"],False)

    def test_mirror_is_seed_reproducible(self):
        x=SharedFourSeatTable(("aggro",)*4,seed=17,round_limit=4).run().summary()
        y=SharedFourSeatTable(("aggro",)*4,seed=17,round_limit=4).run().summary()
        self.assertEqual(x,y)


if __name__=="__main__":
    unittest.main()
