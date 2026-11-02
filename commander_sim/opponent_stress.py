"""Reproducible bounded opponent pressure over the authoritative physical kernel.

This is *not* a second rules engine or a claim to run three real Commander
decks. Three opponents have varied seeded development/removal/damage policies.
Their abstract creature tokens occupy the same battlefield, so reviewed
Pestilence, sweepers and death triggers interact with real physical objects.
Opponent combat uses physical attackers/blockers with explicit simplified legality;\nopponent spell effects remain abstract.
"""
from dataclasses import dataclass
from random import Random
from .reviewed_death_effects import capture_battlefield

SCENARIOS = {
    "balanced": ("aggro", "control", "value"),
    "aggressive": ("aggro", "aggro", "value"),
    "control": ("control", "control", "value"),
    "combo": ("value", "control", "combo"),
    "mixed": ("aggro", "control", "combo"),
}


@dataclass(frozen=True)
class OpponentEvent:
    turn: int
    seat: int
    role: str
    operation: str
    object_id: int | None = None
    amount: int = 0
    target_seat: int | None = None


class BoundedOpponentPressure:
    """Simulate between-turn pressure, not an unsupported multiplayer priority stack."""

    def __init__(self, zones, life, catalog, death_engine, phase_engine,
                 card_definition, *, seed=0, scenario="balanced",
                 attachment_engine=None):
        if scenario not in SCENARIOS:
            raise ValueError("Unknown opponent stress scenario")
        if zones.kernel is not life.kernel:
            raise ValueError("Opponent stress must share authoritative physical kernel")
        self.zones = zones
        self.life = life
        self.catalog = catalog
        self.death_engine = death_engine
        self.phase_engine = phase_engine
        self.definition = card_definition
        self.scenario = scenario
        self.attachments = attachment_engine
        self.before_removal = None
        self.zone_spells = None
        self.rng = Random(seed * 1009 + 617)
        roles = list(SCENARIOS[scenario])
        self.rng.shuffle(roles)
        self.roles = dict(zip(range(1,4), roles))
        self.events = []
        self._defeated = False
        self._born = {}
        # Finite, explicitly abstract opponent library objects make graveyard
        # and mill interactions testable without pretending to supply real
        # opposing decklists. Physical cards retain zone provenance.
        for seat,role in self.roles.items():
            for i in range(16):
                profile=i%5
                p,t=((2,2),(3,2),(2,3),(1,4),(4,3))[profile]
                keywords=(frozenset({"flying"}) if profile==4
                          else frozenset({"deathtouch"}) if profile==3
                          else frozenset())
                definition=self.definition(
                    "stress:"+role+":"+str(seat)+":"+str(i),
                    "Abstract "+role+" creature "+str(i),
                    frozenset({"creature"}),
                    base_power=p,base_toughness=t,
                    keywords=keywords,coverage="approx")
                self.zones.add(definition,seat,"library")
        # Opponent exile events consume a finite abstract interaction budget,
        # rather than pretending an unlimited stream of free removal spells.
        self._removal_budget = {
            seat: (2 if role=="control" else 1 if role=="value" else 0)
            for seat,role in self.roles.items()}

    def _board(self, seat):
        return sorted(
            (o for o in self.zones.kernel.on_battlefield()
             if o.controller == seat and "creature" in o.types),
            key=lambda o:o.object_id)

    def _spawn(self, seat, turn, role):
        # A role may develop a genuine physical (but still abstract) creature
        # card or an expendable token. Cards enter from the seat's finite
        # abstract library and create real graveyard objects when they die.
        as_card=bool(self.zones.ids(seat,"library")) and self.rng.random()<0.66
        if as_card:
            old=self.zones.ids(seat,"library")[-1]
            oid=self.zones.move(old,"battlefield","resolve")
            size=self.zones.kernel.get(oid).power
        else:
            size=2 if role in {"aggro","value"} else 1
            name="Abstract "+role+" token"
            definition=self.definition(
                "stress:token:"+role,name,frozenset({"creature"}),
                base_power=size,base_toughness=size,coverage="approx")
            oid=self.zones.add(definition,seat,"battlefield",token=True)
        self._born[oid]=turn
        self.events.append(OpponentEvent(turn,seat,role,"abstract_creature",
                                          oid,size,seat))

    def _threat(self,seat):
        """Seat-neutral board/life pressure, never a hard-coded human bonus."""
        board=tuple(self._board(seat))
        noncreatures=sum(
            "artifact" in o.types or "enchantment" in o.types
            for o in self.zones.kernel.on_battlefield()
            if o.controller==seat)
        force=sum(max(0,o.power) for o in board)
        commanders=sum("commander" in o.card.supertypes for o in board)
        return 1.0 + 0.45*force + 1.1*len(board) + 1.3*noncreatures + 4.0*commanders + 0.07*max(0,self.life.total(seat))

    def _target_seat(self,actor,role,*,combat=False,eligible=None):
        """Weighted stochastic threat selection among *all* other live seats.

        Aggro biases toward poorly defended opponents, control toward
        developed boards, value mixes both. Never target the source seat.
        Each candidate receives a positive floor; ties are not broken by
        seating order or by assuming seat zero is the human player.
        """
        choices=[seat for seat in self.life.kernel.life_totals
                 if seat!=actor and self.life.total(seat)>0
                 and (eligible is None or seat in eligible)]
        if not choices:
            return None
        weights=[]
        for seat in choices:
            board=self._board(seat)
            blocker_power=sum(max(0,o.power) for o in board if not o.tapped)
            threat=self._threat(seat)
            if combat:
                weight=(2.0+0.35*threat)/(1+0.22*blocker_power)
                if role=="aggro":
                    weight*=1.3
            elif role=="control":
                weight=2.0+threat
            else:
                weight=2.0+0.55*threat
            weights.append(max(0.25,weight))
        return self.rng.choices(choices,weights=weights,k=1)[0]

    def _exile_one(self, seat, turn, role):
        # Model a reviewed-like targeted exile pressure event, NOT an actual
        # spell cast from an opponent's hand. No invented mana or card.
        kernel = self.zones.kernel
        removal_kind=("destroy" if self.rng.random()<
                      (0.58 if role=="control" else 0.73)
                      else "exile")
        valid=[
            o for o in kernel.on_battlefield()
            if o.controller!=seat
            and bool(o.types & {"creature","enchantment","artifact"})
            and (removal_kind=="exile" or "indestructible" not in o.keywords)
            and kernel.legal_target(seat,o.object_id,
                                    frozenset({"creature","enchantment","artifact"}))]
        target_seat=self._target_seat(seat,role,eligible={
            obj.controller for obj in valid})
        if target_seat is None:
            return False
        candidates=[o for o in valid if o.controller==target_seat]
        # Target a consequential engine or commander over an expendable token.
        def score(o):
            # Generic permanent threat: commander / board influence /
            # printed size. No favored named cards or lowest-ID tie bias.
            from .reviewed_death_effects import DEATH_RULES
            from .composed_abilities import ABILITIES
            from .reviewed_attachments import reviewed_attachment
            raw=self.catalog.get(o.card.name,{})
            engine_effect=(
                bool(DEATH_RULES.get(o.card.name))
                or bool(ABILITIES.get(o.card.name))
                or reviewed_attachment(o.card.name,raw) is not None)
            return (3.5*int("commander" in o.card.supertypes)
                    + 2.5*int(engine_effect)
                    + 0.5*max(0,o.power)
                    + 0.35*max(0,o.toughness)
                    + min(3,max(0,float(raw.get("cmc") or 0)))*0.5
                    - 1.5*int(o.token))
        weights=[max(0.25,1+max(-0.5,score(obj)))**1.8
                 for obj in candidates]
        target=self.rng.choices(candidates,weights=weights,k=1)[0]
        # One bounded instant response window before a creature destroy;
        # only the defending player can cast their own reviewed response.
        if removal_kind=="destroy" and callable(self.before_removal):
            self.before_removal(target.object_id,seat,turn,removal_kind)
        if (removal_kind=="destroy" and target.object_id in kernel.objects
                and "indestructible" in kernel.get(target.object_id).keywords):
            self.events.append(OpponentEvent(
                turn,seat,role,"abstract_destroy_prevented",
                target.object_id,0,target_seat))
            return True
        before=capture_battlefield(kernel)
        moves=len(kernel.moves)
        self.zones.move(target.object_id,
                        "graveyard" if removal_kind=="destroy" else "exile",
                        removal_kind,commander_choice=True)
        if self.death_engine is not None:
            self.death_engine.resolve_deaths(before,move_index=moves,turn=turn)
        if self.attachments is not None:
            self.attachments.sync(turn=turn)
        self.events.append(OpponentEvent(
            turn,seat,role,"abstract_"+removal_kind,
            target.object_id,0,target_seat))
        return True

    def _combat(self,seat,role,turn,defender=None,attacker_ids=None):
        """Resolve bounded combat using real blocker legality and damage/SBA.

        No first strike, trample assignment, prevention, double strike, or
        combat-trigger stack. Declines unsafe attacker/blocker assumptions.
        """
        kernel=self.zones.kernel
        if defender is None:
            defender=self._target_seat(seat,role,combat=True)
        if defender is None or defender==seat:
            return
        used=set()
        attackers=[o for o in self._board(seat)
                   if not o.tapped and o.power>0
                   and self._born.get(o.object_id,0)<turn
                   and (attacker_ids is None or o.object_id in attacker_ids)]
        if attacker_ids is None and role=="control":
            attackers=attackers[:1]
        if attacker_ids is None and role=="value":
            attackers=attackers[:2]
        for attacker in attackers:
            if self.life.total(defender)<=0:
                break
            # Re-check live state: earlier combat could destroy an attacker.
            if attacker.object_id not in kernel.objects:
                continue
            blockers=kernel.legal_blockers(attacker.object_id,defender,frozenset(used))
            # Keep priority engine creatures unless a trade is productive or
            # survival demands blocking. Tokens are the preferred expendables.
            def worth_blocking(o):
                good_trade=(o.power>=attacker.toughness or
                            (o.power>0 and "deathtouch" in o.keywords
                             and "indestructible" not in attacker.keywords))
                survives=o.toughness>attacker.power
                return (survives, good_trade, o.token,
                        -int("commander" in o.card.supertypes),
                        -o.object_id)
            blockers.sort(key=worth_blocking,reverse=True)
            chosen=blockers[0] if blockers else None
            if chosen is not None and not (
                    chosen.toughness>attacker.power or
                    chosen.power>=attacker.toughness or
                    (chosen.power>0 and "deathtouch" in chosen.keywords and
                     "indestructible" not in attacker.keywords) or
                    self.life.total(defender)<=16):
                chosen=None
            selected=[chosen] if chosen is not None else []
            if "menace" in attacker.keywords:
                if len(blockers)<2 or chosen is None:
                    selected=[]
                else:
                    second=next((b for b in blockers
                                 if b.object_id!=chosen.object_id),None)
                    selected=[chosen,second] if second is not None else []
            if "vigilance" not in attacker.keywords:
                attacker.tapped=True
                kernel._dirty()
            if not selected:
                self.life.damage(defender,attacker.power,attacker.object_id)
                if "lifelink" in attacker.keywords:
                    self.life.gain(seat,attacker.power,attacker.object_id)
                self.events.append(OpponentEvent(
                    turn,seat,role,"abstract_unblocked_damage",
                    attacker.object_id,attacker.power,defender))
                if ("decayed" in attacker.keywords
                        and attacker.object_id in kernel.objects):
                    snap=capture_battlefield(kernel)
                    mid=len(kernel.moves)
                    self.zones.move(attacker.object_id,"graveyard","sacrifice",
                                    commander_choice=True)
                    if self.death_engine:
                        self.death_engine.resolve_deaths(
                            snap,move_index=mid,turn=turn)
                continue
            for block in selected:
                used.add(block.object_id)
            before=capture_battlefield(kernel)
            first_move=len(kernel.moves)
            # Simultaneous marked creature damage on existing physical objects.
            assignments={attacker.object_id:sum(x.power for x in selected)}
            remaining=attacker.power
            for block in selected:
                assigned=min(remaining,max(1,block.toughness))
                assignments[block.object_id]=assigned
                remaining-=assigned
            kernel.damage_creatures_together(assignments)
            # Lifelink is based on actual marked damage; replacement,
            # prevention, first strike and trample remain outside this slice.
            if "lifelink" in attacker.keywords:
                self.life.gain(seat,attacker.power,attacker.object_id)
            for block in selected:
                if "lifelink" in block.keywords and block.power>0:
                    self.life.gain(defender,block.power,block.object_id)
            # Deathtouch is a generic lethal criterion after physical damage.
            for source,target in (
                    (attacker,block) for block in selected):
                if (source.power>0 and "deathtouch" in source.keywords
                        and assignments.get(target.object_id,0)>0
                        and target.object_id in kernel.objects
                        and "indestructible" not in kernel.get(target.object_id).keywords):
                    self.zones.move(target.object_id,"graveyard","state_based",
                                    commander_choice=True)
            for source in selected:
                target=attacker
                if (source.power>0 and "deathtouch" in source.keywords
                        and target.object_id in kernel.objects
                        and "indestructible" not in kernel.get(target.object_id).keywords):
                    self.zones.move(target.object_id,"graveyard","state_based",
                                    commander_choice=True)
            if self.death_engine is not None:
                self.death_engine.resolve_deaths(
                    before,move_index=first_move,turn=turn)
            if self.attachments is not None:
                self.attachments.sync(turn=turn)
            self.events.append(OpponentEvent(
                turn,seat,role,"abstract_blocked_combat",
                attacker.object_id,attacker.power,defender))
            if ("decayed" in attacker.keywords
                    and attacker.object_id in kernel.objects):
                snap=capture_battlefield(kernel)
                mid=len(kernel.moves)
                self.zones.move(attacker.object_id,"graveyard","sacrifice",
                                commander_choice=True)
                if self.death_engine:
                    self.death_engine.resolve_deaths(snap,move_index=mid,turn=turn)

    def player_combat(self,turn,*,beginning_creature_ids=()):
        """A bounded, board-aware offensive turn for the physical pilot.

        Opponent seats are chosen by the same seat-neutral threat model.
        No phantom enemy blocking or player-zero targeting preference.
        """
        kernel=self.zones.kernel
        start=len(self.events)
        beginning=set(beginning_creature_ids)
        attackers=[]
        all_live=[o for o in self._board(0) if o.power>0 and not o.tapped]
        for o in all_live:
            if o.object_id not in beginning and "haste" not in o.keywords:
                self._born[o.object_id]=turn
            else:
                self._born[o.object_id]=0
            if self._born[o.object_id]<turn:
                attackers.append(o)
        if not attackers:
            return ()
        # Reserve defensive bodies when facing dangerous developed boards.
        opponents=sum(len(self._board(seat)) for seat in (1,2,3))
        reserve=2 if self.life.total(0)<=18 and opponents>=5 else (
            1 if opponents>=5 else 0)
        attackers.sort(key=lambda o:(
            int("lifelink" in o.keywords),
            int("flying" in o.keywords),
            int("menace" in o.keywords),
            o.power,
            int(o.token),-o.object_id),reverse=True)
        keep=set(o.object_id for o in sorted(
            attackers,key=lambda o:(
                int("deathtouch" in o.keywords),
                o.toughness,
                int("indestructible" in o.keywords),
                -o.object_id),reverse=True)[:reserve])
        chosen=[o.object_id for o in attackers
                if o.object_id not in keep][:3]
        if not chosen:
            return ()
        opponent=self._target_seat(0,"value",combat=True)
        if opponent is None:
            return ()
        self._combat(0,"physical_pilot",turn,defender=opponent,
                     attacker_ids=set(chosen))
        return tuple(self.events[start:])

    def advance(self, turn):
        """Three opponents take their bounded abstract turns after seat 0.

        Their upkeep boundaries are real phase events; they can trigger
        Ophiomancer correctly. Other actions are abstract pressure with
        independently seeded variance and no unsupported rule claims.
        """
        if type(turn) is not int or turn < 1:
            raise ValueError("Positive turn required")
        current=len(self.events)
        for seat in (1,2,3):
            role=self.roles[seat]
            # Each player untaps their own permanents before their upkeep.
            # Previous stress batches incorrectly left attackers tapped for
            # the rest of the game, understating repeat combat pressure.
            for permanent in self.zones.kernel.on_battlefield():
                if permanent.controller==seat and permanent.tapped:
                    permanent.tapped=False
                    self.zones.kernel._dirty()
            if self.attachments is not None:
                self.attachments.sync(turn=turn)
            # Unlike goldfish mode, 'each upkeep' triggers have all four
            # upkeeps. These are resolved with existing reviewed phase logic.
            if self.phase_engine:
                for res in self.phase_engine.resolve(
                        phase="upkeep", active_seat=seat, round_id=turn):
                    self.events.append(OpponentEvent(
                        turn,seat,role,"reviewed_opponent_upkeep",res.source_id,
                        len(res.created_token_ids)))
            on_board=self._board(seat)
            spawn = (
                role=="aggro" and (turn <= 5 or turn % 3 == 0) or
                role=="control" and turn % 4 == 0 or
                role=="value" and turn % 2 == 0 or
                role=="combo" and turn % 3 == 0)
            if spawn and len(on_board)<5:
                self._spawn(seat,turn,role)
            # Seeded physical hand turnover permits realistic discard triggers.
            if turn>=3 and self.rng.random()<(0.25 if role=="value" else 0.12):
                if self.zones.ids(seat,"library"):
                    hand_ids,complete=self.zones.draw(seat,1)
                    if not complete:
                        raise AssertionError("Reviewed opponent draw preview invalidated")
                    discarded=self.zones.discard(seat,hand_ids[0])
                    self.events.append(OpponentEvent(
                        turn,seat,role,"abstract_discard",discarded,1,seat))
            should_exile=(
                role=="control" and turn in {4,7,9}
                and self.rng.random()<0.74 or
                role=="value" and turn in {6,9}
                and self.rng.random()<0.28)
            if should_exile and self._removal_budget[seat]>0:
                if self._exile_one(seat,turn,role):
                    self._removal_budget[seat]-=1
            # Attack with actual non-summoning-sick abstract opponent
            # creatures. Legal defender blockers, creature damage, and LKI
            # death triggers run on the existing authoritative battlefield.
            self._combat(seat,role,turn)
            # Combo role adds an explicitly abstract noncombat clock.
            if role=="combo" and turn>=7:
                victim=self._target_seat(seat,role)
                if victim is not None:
                    amount=3+turn//3+self.rng.choice((-1,0,0,1))
                    self.life.lose(victim,amount)
                    self.events.append(OpponentEvent(
                        turn,seat,role,"abstract_combo_loss",None,amount,victim))
            # Each opponent has its own end-of-turn damage cleanup and
            # duration expiration before the next player's turn begins.
            kernel=self.zones.kernel
            kernel.cleanup()
            if self.zone_spells is not None:
                self.zone_spells.expire(turn,active_seat=seat)
            if self.attachments is not None:
                self.attachments.sync(turn=turn)
            if self.life.total(0)<=0 and not self._defeated:
                self._defeated=True
                self.events.append(OpponentEvent(turn,seat,role,"life_zero"))
                break
        if not self.zones.assert_consistent():
            raise AssertionError("Opponent pressure corrupted authoritative zones")
        return tuple(self.events[current:])

    @property
    def defeated(self):
        return self._defeated
