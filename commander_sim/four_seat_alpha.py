"""Experimental four-seat *abstract category* game on the current physical kernel.

All 4 seats share IndexedKernel / LiveZones / KernelLife / TemplateManaService;
the old v5 99-card archetype recipes supply synthetic cards and preferences.
This is NOT printed-card-accurate Commander. Exact-card action dispatch, stack,
priority, replacements and Commander effects are not claimed. The calibrated
abstract finisher is an explicitly named approximation.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from random import Random
from statistics import median
import json

from .early_game_runner import _load_live_kernel
from .kernel_life import KernelLife
from .template_resources import TemplateManaService
from .effect_templates import ManaMode

ROOT=Path(__file__).resolve().parents[1]
CONF=json.loads((ROOT/"simulator/v5_four_player/archetypes.json").read_text())
TEMPLATES=json.loads((ROOT/"simulator/v5_four_player/templates.json").read_text())["templates"]
KINDS={
    "land":"land", "ramp":"artifact", "small":"creature", "medium":"creature",
    "large":"creature", "tokens":"sorcery", "engine":"enchantment",
    "draw":"sorcery", "removal":"instant", "counter":"instant",
    "wipe":"sorcery", "combo_piece":"artifact", "finisher":"sorcery",
    "buff":"sorcery", "burn":"instant"
}
PLAYABLE=frozenset({"ramp","small","medium","large","draw","engine",
                    "combo_piece","removal","tokens","burn","wipe","finisher"})
ARCHETYPES=tuple(CONF["archetypes"])


@dataclass(frozen=True)
class AbstractProfileCard:
    kind: str
    cost: int
    size: int=0
    quantity: int=0


class AbstractSourceMana(TemplateManaService):
    """The *existing* source-ID payment algorithm; only modes are synthetic."""
    def modes(self,obj):
        if obj.zone!="battlefield" or not obj.card.card_id.startswith("calibration:"):
            return ()
        parts=obj.card.card_id.split(":")
        kind=parts[2]
        if kind=="land":
            return (ManaMode(("C",)),)
        if kind=="ramp":
            amount=2 if "double" in parts else 1
            return (ManaMode(("C",)*amount),)
        return ()


class SharedFourSeatTable:
    """Four active seats with symmetric legal-zone and mana payment primitives."""
    def __init__(self,archetypes,*,seed=0,round_limit=30):
        if len(archetypes)!=4 or any(a not in ARCHETYPES for a in archetypes):
            raise ValueError("Exactly four known archetypes required")
        if type(seed)!=int or type(round_limit)!=int or not 1<=round_limit<=30:
            raise ValueError("Invalid bounded tournament settings")
        K,Z,C=_load_live_kernel()
        self.kernel=K();self.zones=Z(self.kernel,seed=seed)
        self.life=KernelLife(self.kernel)
        self.CardDefinition=C
        self.rng=Random(seed*109+51)
        self.roles=tuple(archetypes)
        self.seed=seed;self.limit=round_limit
        self.mana=AbstractSourceMana(
            self.kernel,{},frozenset("WUBRG"),zones=self.zones,max_states=30000)
        self.events=[];self.history=[];self.eliminated=set()
        self.entered={}
        self.first_threat={};self.first_damage={}
        self.outcome=None
        self._load_decks()

    def _load_decks(self):
        for seat,role in enumerate(self.roles):
            rng=Random(self.seed*4049+seat*659+917)
            cards=[]
            for kind,n in CONF["archetypes"][role].items():
                for i in range(n):
                    profile=TEMPLATES[kind]
                    cost=rng.randint(*profile["cost"])
                    strength=rng.randint(*profile.get("power",(2,2)))
                    toughness=rng.randint(*profile.get("toughness",(2,2)))
                    double=kind=="ramp" and rng.random()<CONF["ramp_double_chance"].get(role,.08)
                    cid=f"calibration:{seat}:{kind}:{i}:"+("double" if double else "ordinary")
                    name=f"Generic {role} {kind} {i}"
                    types=frozenset({KINDS[kind]})
                    definition=self.CardDefinition(
                        cid,name,types,base_power=strength if kind in ("small","medium","large") else 0,
                        base_toughness=toughness if kind in ("small","medium","large") else 0,
                        coverage="approx")
                    cards.append((definition,AbstractProfileCard(kind,cost,strength,toughness)))
            if len(cards)!=99:
                raise AssertionError("Profile must supply precisely 99 cards")
            rng.shuffle(cards)
            for d,profile in cards:
                oid=self.zones.add(d,seat,"library")
                self.profiles[d.card_id]=profile

    @property
    def profiles(self):
        if not hasattr(self,"_profiles"):
            self._profiles={}
        return self._profiles

    def _role_objects(self,seat):
        return [o for o in self.kernel.on_battlefield() if o.controller==seat]

    def _creatures(self,seat):
        return [o for o in self._role_objects(seat) if "creature" in o.types]

    def _sources(self,seat):
        return sum(len(self.mana.modes(o)[0].output) for o in self._role_objects(seat)
                   if self.mana.modes(o))

    def _log(self,turn,seat,action,**extra):
        self.events.append({"round":turn,"seat":seat,"archetype":self.roles[seat],
                            "action":action,**extra})

    def _eliminate(self,seat,turn,reason):
        if seat in self.eliminated:
            return
        self.eliminated.add(seat)
        self._log(turn,seat,"eliminated",reason=reason)
        self.zones.leave_game(seat)

    def _check_life(self,turn):
        for seat in range(4):
            if seat not in self.eliminated and self.life.total(seat)<=0:
                self._eliminate(seat,turn,"life_zero")

    def _draw(self,seat,n,turn):
        drawn,complete=self.zones.draw(seat,n)
        for oid in drawn:
            self._log(turn,seat,"draw",card_id=self.kernel.get(oid).card.card_id)
        if not complete:
            self._eliminate(seat,turn,"empty_library")
        return complete

    def _pick(self,seat,turn):
        priorities=CONF["priority"][self.roles[seat]]
        ranked=[]
        for oid in self.zones.ids(seat,"hand"):
            obj=self.kernel.get(oid)
            profile=self.profiles[obj.card.card_id]
            if profile.kind not in PLAYABLE:
                continue
            if profile.kind=="draw" and len(self.zones.ids(seat,"library"))<3:
                continue
            if profile.kind in {"removal","wipe"} and not any(
                    self._creatures(other) for other in range(4) if other!=seat
                    and other not in self.eliminated):
                continue
            if profile.kind=="finisher" and self._sources(seat)<7:
                continue
            if profile.kind=="finisher" and self.roles[seat]=="combo" and sum(
                    o.card.card_id.split(":")[2]=="combo_piece" for o in self._role_objects(seat))<3:
                continue
            cost=f"{{{profile.cost}}}"
            payment=self.mana.plan(seat,cost)
            if payment is None:
                continue
            score=100-5*(priorities.index(profile.kind) if profile.kind in priorities else 18)
            if profile.kind=="ramp" and turn>=9:
                score-=35
            if profile.kind=="draw" and len(self.zones.ids(seat,"hand"))<=3:
                score+=15
            ranked.append((-score,profile.cost,obj.card.card_id,oid))
        if not ranked:return None
        ranked.sort()
        return ranked[0][-1]

    def _cast(self,seat,oid,turn):
        obj=self.kernel.get(oid)
        p=self.profiles[obj.card.card_id]
        paid=self.mana.pay(seat,f"{{{p.cost}}}")
        if paid is None:raise AssertionError("Previously feasible generic payment failed")
        old_id=obj.card.card_id
        ticket=self.zones.cast(seat,oid)
        target=None
        if p.kind in {"removal","wipe"}:
            candidates=[o for other in range(4) if other!=seat and other not in self.eliminated
                        for o in self._creatures(other)
                        if self.kernel.legal_target(seat,o.object_id,frozenset({"creature"}))]
            if candidates:
                target=max(candidates,key=lambda o:(o.power,o.toughness,o.object_id))
        if p.kind=="removal" and target is not None:
            self.zones.move(target.object_id,"graveyard","destroy")
        if p.kind=="wipe":
            for other in range(4):
                if other==seat or other in self.eliminated:continue
                for c in list(self._creatures(other)):
                    if c.object_id in self.kernel.objects and "indestructible" not in c.keywords:
                        self.zones.move(c.object_id,"graveyard","destroy")
        if p.kind=="draw":
            self._draw(seat,2,turn)
        if p.kind=="burn":
            other=self._target(seat)
            if other is not None:self.life.damage(other,3)
        if p.kind=="finisher":
            # Bounded archetype *approximation*, not a printed-card win rule.
            amount=12 if self.roles[seat] in ("combo","spellslinger") else 6
            for other in range(4):
                if other!=seat and other not in self.eliminated:
                    self.life.damage(other,amount)
        # Lands, ramp, creatures, engines, combo pieces remain physical.
        permanent=p.kind in {"ramp","small","medium","large","engine","combo_piece"}
        if permanent:
            fresh=self.zones.resolve(ticket)
            self.entered[fresh]=turn
        else:
            self.zones.resolve(ticket,effect=lambda kernel,t:None)
        self._log(turn,seat,"abstract_cast",card_id=old_id,kind=p.kind,
                  source_ids=list(paid.source_ids),target_seat=target.controller if target else None)
        self._check_life(turn)

    def _target(self,seat):
        others=[s for s in range(4) if s!=seat and s not in self.eliminated]
        if not others:return None
        return self.rng.choice(others)

    def _combat(self,seat,turn):
        role=self.roles[seat]
        for creature in sorted(self._creatures(seat),key=lambda o:o.object_id):
            if creature.object_id not in self.kernel.objects or creature.tapped:
                continue
            if self.entered.get(creature.object_id,0)>=turn:
                continue
            if self.rng.random()>CONF["attack_rate"][role]:
                continue
            defender=self._target(seat)
            if defender is None:return
            blockers=self.kernel.legal_blockers(creature.object_id,defender)
            # Primitive, symmetric one-blocker combat; no stack/combat steps.
            blocker=max(blockers,key=lambda o:(o.power>=creature.toughness,
                                                o.toughness>creature.power,o.power),
                        default=None)
            creature.tapped=True
            if blocker is None:
                amount=max(0,creature.power)
                self.life.damage(defender,amount,creature.object_id)
                self._log(turn,seat,"combat_damage",target_seat=defender,amount=amount)
            else:
                self.kernel.damage_creatures_together({
                    creature.object_id:max(0,blocker.power),
                    blocker.object_id:max(0,creature.power)})
                self._log(turn,seat,"combat_blocked",target_seat=defender)
            self._check_life(turn)
            if seat in self.eliminated:return

    def run(self):
        self.order=list(range(4));self.rng.shuffle(self.order)
        for seat in range(4):
            self.zones.shuffle(seat)
            self._draw(seat,7,0)
        for turn in range(1,self.limit+1):
            for seat in self.order:
                if seat in self.eliminated:continue
                self.mana.clear()
                for obj in self._role_objects(seat):
                    obj.tapped=False
                if not self._draw(seat,1,turn):continue
                lands=[oid for oid in self.zones.ids(seat,"hand")
                       if self.profiles[self.kernel.get(oid).card.card_id].kind=="land"]
                if lands:
                    oid=self.zones.play_land(seat,lands[0])
                    self.entered[oid]=turn
                    self._log(turn,seat,"land_play")
                for _ in range(7):
                    chosen=self._pick(seat,turn)
                    if chosen is None or seat in self.eliminated:break
                    self._cast(seat,chosen,turn)
                if seat not in self.eliminated:
                    self._combat(seat,turn)
                self.mana.clear()
                self.kernel.cleanup()
                self._check_life(turn)
                if len(self.eliminated)>=3:break
            self.history.append({
                "round":turn,
                "seats":{str(s):{
                    "role":self.roles[s],"life":self.life.total(s),
                    "hand":len(self.zones.ids(s,"hand")),
                    "library":len(self.zones.ids(s,"library")),
                    "sources":self._sources(s),"creatures":len(self._creatures(s)),
                    "alive":s not in self.eliminated}
                    for s in range(4)}})
            if not self.zones.assert_consistent():
                raise AssertionError("Shared kernel and zone indices diverged")
            if len(self.eliminated)>=3:break
        alive=[s for s in range(4) if s not in self.eliminated]
        self.outcome={"winner":alive[0] if len(alive)==1 else None,
                      "rounds":len(self.history),
                      "status":"win" if len(alive)==1 else "unresolved",
                      "reason":"last_survivor" if len(alive)==1 else "round_limit"}
        return self

    def summary(self):
        if self.outcome is None:raise ValueError("Run before summarizing")
        return {"format":"shared-kernel-abstract-four-seat-alpha-v1",
                "seed":self.seed,"archetypes":list(self.roles),"turn_order":self.order,
                "outcome":self.outcome,"events":self.events,"history":self.history,
                "fidelity":"abstract_actions_physical_zones_and_generic_source_payment",
                "printed_card_accuracy":False,
                "four_real_decks":False}
