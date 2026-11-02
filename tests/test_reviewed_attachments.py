"""Equipment, Auras and global continuous effects use one physical kernel."""
import json
import unittest

from commander_sim.deck_fixtures import EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.kernel_life import KernelLife
from commander_sim.template_resources import TemplateManaService
from commander_sim.reviewed_death_effects import ReviewedDeathEngine,capture_battlefield
from commander_sim.reviewed_attachments import AttachmentEngine,reviewed_attachment
from commander_sim.reviewed_unearth import expire_reviewed_unearth


class PhysicalAttachmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture=next(f for f in EXPERIMENTAL_FIXTURES
                     if f.key=="mortarion_physical_final")
        cls.catalog={item["deck_name"]:item["card"] for item in
                     json.loads(fixture.snapshot_path.read_text())["cards"]}

    def setUp(self):
        K,Z,C=_load_live_kernel()
        self.kernel=K()
        self.zones=Z(self.kernel,seed=28)
        self.C=C
        self.life=KernelLife(self.kernel)
        self.mana=TemplateManaService(
            self.kernel,self.catalog,frozenset({"B"}),zones=self.zones)
        self.death=ReviewedDeathEngine(self.zones,self.life,self.catalog)
        self.attach=AttachmentEngine(self.zones,self.life,self.catalog,
                                     self.mana,self.death)
        self.death.attachments=self.attach

    def add(self,name,types=("creature",),seat=0,zone="battlefield",
            power=2,toughness=2,token=False):
        raw=self.catalog.get(name,{})
        return self.zones.add(self.C(
            raw.get("oracle_id","test:"+name),name,
            frozenset(types),base_power=power,base_toughness=toughness,
            coverage="approx"),seat,zone,token=token)

    def lands(self,n):
        for _ in range(n):
            self.add("Swamp",types=("land",))

    def test_collar_keywords_follow_only_live_equipped_creature(self):
        self.lands(2)
        collar=self.add("Basilisk Collar",types=("artifact",))
        a=self.add("First",power=3)
        b=self.add("Second")
        self.assertIsNotNone(self.attach.bind(collar,a))
        self.assertTrue({"deathtouch","lifelink"}<=self.kernel.get(a).keywords)
        self.assertNotIn("lifelink",self.kernel.get(b).keywords)
        self.zones.move(collar,"graveyard","destroy")
        self.attach.sync()
        self.assertNotIn("lifelink",self.kernel.get(a).keywords)
        self.assertTrue(self.zones.assert_consistent())

    def test_boots_grant_hexproof_and_haste_only_while_attached(self):
        self.lands(1)
        boots=self.add("Swiftfoot Boots",types=("artifact",))
        creature=self.add("Commander Body",power=5,toughness=5)
        self.assertIsNotNone(self.attach.bind(boots,creature))
        self.assertTrue({"hexproof","haste"}<=self.kernel.get(creature).keywords)
        self.assertFalse(self.kernel.legal_target(1,creature,frozenset({"creature"})))
        self.assertTrue(self.kernel.legal_target(0,creature,frozenset({"creature"})))
        self.assertTrue(self.zones.assert_consistent())

    def test_skullclamp_kills_one_toughness_token_and_draws_two(self):
        self.lands(1)
        self.add("Draw one",types=("instant",),zone="library")
        self.add("Draw two",types=("instant",),zone="library")
        clamp=self.add("Skullclamp",types=("artifact",))
        token=self.add("Soldier",token=True,power=1,toughness=1)
        outcome=self.attach.bind(clamp,token)
        self.assertIsNotNone(outcome)
        self.assertNotIn(token,self.kernel.objects)
        self.assertEqual(len(self.zones.ids(0,"hand")),2)
        self.assertTrue(self.zones.assert_consistent())

    def test_monument_buff_and_upkeep_sacrifice_use_shared_death(self):
        monument=self.add("Eldrazi Monument",types=("artifact",))
        token=self.add("Soldier",token=True,power=1,toughness=1)
        body=self.add("Body",power=2,toughness=2)
        self.attach.sync()
        self.assertEqual(self.kernel.get(body).power,3)
        self.assertTrue({"flying","indestructible"}<=self.kernel.get(body).keywords)
        out=self.attach.upkeep(0,turn=2)
        self.assertEqual(out[0].operation,"upkeep_sacrifice_creature")
        self.assertNotIn(token,self.kernel.objects)
        self.assertIn(monument,self.kernel.objects)
        self.assertTrue(self.zones.assert_consistent())

    def test_monument_sacrificed_when_no_creatures(self):
        monument=self.add("Eldrazi Monument",types=("artifact",))
        out=self.attach.upkeep(0,turn=2)
        self.assertEqual(out[0].operation,"upkeep_sacrifice_source")
        self.assertNotIn(monument,self.kernel.objects)
        self.assertTrue(self.zones.assert_consistent())

    def test_whip_lifelink_and_temporary_reanimation_exiles(self):
        self.lands(4)
        whip=self.add("Whip of Erebos",types=("artifact",))
        live=self.add("Body",power=3)
        dead=self.add("Dead Body",zone="graveyard",power=4,toughness=3)
        self.attach.sync()
        self.assertIn("lifelink",self.kernel.get(live).keywords)
        result=self.attach.resurrect(whip,dead,turn=3)
        self.assertIsNotNone(result)
        raised=self.kernel.get(result.target_id)
        self.assertIn("haste",raised.keywords)
        self.assertIn("lifelink",raised.keywords)
        self.assertTrue(self.kernel.get(whip).tapped)
        expired=expire_reviewed_unearth(self.zones)
        self.assertTrue(expired)
        self.assertNotIn(result.target_id,self.kernel.objects)
        self.assertTrue(self.zones.assert_consistent())

    def test_nurgle_rot_attaches_to_enemy_and_returns_when_enemy_dies(self):
        source=self.add("Nurgle's Rot",types=("enchantment",))
        enemy=self.add("Enemy",seat=2)
        self.assertIsNotNone(self.attach.bind(
            source,enemy,already_paid=True))
        before=capture_battlefield(self.kernel)
        index=len(self.kernel.moves)
        self.zones.move(enemy,"graveyard","destroy")
        self.death.resolve_deaths(before,move_index=index,turn=2)
        self.assertEqual(self.zones.names(0,"hand"),("Nurgle's Rot",))
        demons=[o for o in self.kernel.on_battlefield()
                if o.card.name=="Plaguebearer of Nurgle"]
        self.assertEqual(len(demons),1)
        self.assertTrue(self.zones.assert_consistent())

    def test_aura_cannot_attach_own_creature(self):
        source=self.add("Nurgle's Rot",types=("enchantment",))
        own=self.add("Own")
        self.assertIsNone(self.attach.bind(source,own,already_paid=True))
        self.assertTrue(self.zones.assert_consistent())

    def test_identity_guard_does_not_infer_attachments(self):
        r=reviewed_attachment("Basilisk Collar",self.catalog["Basilisk Collar"])
        self.assertIsNotNone(r)
        fake=dict(self.catalog["Basilisk Collar"],oracle_id="wrong")
        self.assertIsNone(reviewed_attachment("Basilisk Collar",fake))


if __name__=="__main__":
    unittest.main()
