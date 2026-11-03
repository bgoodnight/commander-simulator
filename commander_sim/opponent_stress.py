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
from .pilot_policy import choose_combat_posture

# Registry of assignable abstract opponent types. Add a pressure behavior
# for any new role and register it here; seat selection itself never changes.
OPPONENT_TYPES = ("aggro", "control", "value", "combo")

SCENARIOS = {
    "random": None,  # independently sample each seat with replacement
    "balanced": ("aggro", "control", "value"),
    "aggressive": ("aggro", "aggro", "value"),
    "control": ("control", "control", "value"),
    "combo": ("value", "control", "combo"),
    "mixed": ("aggro", "control", "combo"),
}


def assign_opponent_roles(scenario, rng):
    """Assign three seeded seat policies independently or use a test preset.

    Random pods draw with replacement, allowing repeated types. Presets
    retain their fixed composition but randomize seat order.
    """
    if scenario not in SCENARIOS:
        raise ValueError("Unknown opponent stress scenario")
    preset = SCENARIOS[scenario]
    if preset is None:
        picks = [rng.choice(OPPONENT_TYPES) for _ in range(3)]
    else:
        picks = list(preset)
        rng.shuffle(picks)
    return dict(zip((1, 2, 3), picks))


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
                 card_definition, *, seed=0, scenario="random",
                 attachment_engine=None, mana_service=None):
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
        self.mana_service = mana_service
        self.before_removal = None
        self.zone_spells = None
        self.rng = Random(seed * 1009 + 617)
        self.roles = assign_opponent_roles(scenario, self.rng)
        self.events = []
        self._defeated = False
        self._eliminated_seats = set()
        self._born = {}
        self.last_player_combat_decision = None
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
        if self.life.total(seat)<=0:
            return []
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
        if self.life.total(seat)<=0:
            return False
        # Model a reviewed-like targeted exile pressure event, NOT an actual
        # spell cast from an opponent's hand. No invented mana or card.
        kernel = self.zones.kernel
        removal_kind=("destroy" if self.rng.random()<
                      (0.58 if role=="control" else 0.73)
                      else "exile")
        valid=[
            o for o in kernel.on_battlefield()
            if o.controller!=seat
            and self.life.total(o.controller)>0
            and bool(o.types & {"creature","enchantment","artifact"})
            and (removal_kind=="exile" or "indestructible" not in o.keywords)
            and kernel.legal_target(seat,o.object_id,
                                    frozenset({"creature","enchantment","artifact"}))]
        if not valid:
            return False
        # Target a consequential engine or commander over an expendable token.
        # Score *all* legal opposing objects together. Choosing a seat first
        # made the value of a single high-priority threat depend on how many
        # low-impact permanents another seat controlled, and could distort
        # decisions when only the physical pilot had reviewed engines.
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
        # A finite stochastic choice retains interaction variance while
        # permitting any seat's high-threat permanent to draw attention.
        # Seat number, player identity and object insertion order never enter
        # the scoring formula. Within a score tier, shuffle before sampling.
        candidates=sorted(valid,key=lambda o:(o.controller,o.object_id))
        weights=[max(0.25,1+max(-0.5,score(obj)))**1.8
                 for obj in candidates]
        target=self.rng.choices(candidates,weights=weights,k=1)[0]
        target_seat=target.controller
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
        if self.life.total(seat)<=0:
            return
        if defender is None:
            defender=self._target_seat(seat,role,combat=True)
        if (defender is None or defender==seat
                or self.life.total(defender)<=0):
            return
        used=set()
        attackers=[o for o in self._board(seat)
                   if not o.tapped and o.power>0
                   and self._born.get(o.object_id,0)<turn
                   and (attacker_ids is None or o.object_id in attacker_ids)]
        if attacker_ids is None and role in {"control","value"}:
            # These roles commit fewer attackers. Pick the strongest legal
            # candidates, rather than whichever entered the board first.
            attackers.sort(key=lambda o:(
                int("flying" in o.keywords),
                int("menace" in o.keywords),
                int("lifelink" in o.keywords),
                o.power, -o.object_id), reverse=True)
            attackers=attackers[:1 if role=="control" else 2]
        for attacker in attackers:
            if self.life.total(defender)<=0:
                break
            # Re-check live state: earlier combat could destroy an attacker.
            if attacker.object_id not in kernel.objects:
                continue
            if attacker.controller==0:
                from .reviewed_attack_triggers import resolve_attack_grants
                for source_id,attacker_id,keyword in resolve_attack_grants(
                        kernel,self.catalog,attacker.object_id):
                    self.events.append(OpponentEvent(
                        turn,seat,role,"reviewed_attack_keyword_grant",
                        attacker_id,0,defender))
            if attacker.controller==0:
                # One source-verified attack trigger resolution per declared
                # attacker. Resulting tokens enter the physical battlefield;
                # they are not retroactively added to this attack.
                from .reviewed_attack_tokens import resolve_attack_tokens
                created=resolve_attack_tokens(
                    self.zones,self.catalog,attacker.object_id)
                if created:
                    self.events.append(OpponentEvent(
                        turn,seat,role,"reviewed_attack_tokens",
                        attacker.object_id,len(created),defender))
            if attacker.controller==0:
                from .reviewed_attack_mill import resolve_attack_mill
                milled=resolve_attack_mill(
                    self.zones,self.catalog,attacker.object_id)
                if milled is not None:
                    self.events.append(OpponentEvent(
                        turn,seat,role,"reviewed_attack_mill",
                        attacker.object_id,len(milled.milled_ids),defender))
                    if milled.token_ids:
                        self.events.append(OpponentEvent(
                            turn,seat,role,"reviewed_attack_tokens",
                            attacker.object_id,len(milled.token_ids),defender))
                    if milled.returned_id is not None:
                        self.events.append(OpponentEvent(
                            turn,seat,role,"reviewed_attack_retrieve",
                            milled.returned_id,1,defender))
            if attacker.controller==0:
                from .reviewed_attack_zones import resolve_attack_zone
                outcome=resolve_attack_zone(
                    self.zones,self.life,self.catalog,attacker.object_id,
                    mana_service=self.mana_service,
                    death_engine=self.death_engine,turn=turn)
                if outcome is not None:
                    if outcome.returned_id is not None:
                        self.events.append(OpponentEvent(
                            turn,seat,role,"reviewed_attack_recursion",
                            outcome.returned_id,1,defender))
                    if outcome.sacrificed_old_ids:
                        self.events.append(OpponentEvent(
                            turn,seat,role,"reviewed_attack_sacrifice",
                            attacker.object_id,len(outcome.sacrificed_old_ids),defender))
            blockers=kernel.legal_blockers(attacker.object_id,defender,frozenset(used))
            # Magic creatures with negative power assign/deal zero combat
            # damage. Their signed power still matters for other effects.
            attacker_damage=max(0,attacker.power)
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
                if attacker_damage:
                    self.life.damage(defender,attacker_damage,attacker.object_id)
                    # This is the one unblocked creature-to-player damage
                    # boundary. Do not fire on blocked creature combat.
                    from .reviewed_combat_damage import resolve_combat_damage_player
                    triggered=resolve_combat_damage_player(
                        self.zones,self.catalog,attacker.object_id,
                        defender,attacker_damage)
                    if triggered is not None:
                        if triggered.token_ids:
                            self.events.append(OpponentEvent(
                                turn,seat,role,"reviewed_combat_damage_tokens",
                                attacker.object_id,len(triggered.token_ids),defender))
                        if triggered.discarded_ids:
                            self.events.append(OpponentEvent(
                                turn,seat,role,"reviewed_combat_damage_discard",
                                attacker.object_id,len(triggered.discarded_ids),defender))
                    if "lifelink" in attacker.keywords:
                        self.life.gain(seat,attacker_damage,attacker.object_id)
                self.events.append(OpponentEvent(
                    turn,seat,role,"abstract_unblocked_damage",
                    attacker.object_id,attacker_damage,defender))
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
            assignments={
                attacker.object_id:sum(max(0,block.power) for block in selected)}
            remaining=attacker_damage
            for block in selected:
                assigned=min(remaining,max(1,block.toughness))
                assignments[block.object_id]=assigned
                remaining-=assigned
            kernel.damage_creatures_together(assignments)
            # Lifelink is based on actual marked damage; replacement,
            # prevention, first strike and trample remain outside this slice.
            if "lifelink" in attacker.keywords and attacker_damage:
                self.life.gain(seat,attacker_damage,attacker.object_id)
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

    def player_combat(self,turn,*,beginning_creature_ids=(),
                      style="adaptive",signals=None):
        """A bounded, board-aware offensive turn for the physical pilot.

        The legal battlefield and defender selection are unchanged. Attack
        caps and defensive reserves follow the same deck-derived personality
        as main-phase action ranking; no commander-specific exceptions.
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
        opponents=sum(len(self._board(seat)) for seat in (1,2,3))
        posture=choose_combat_posture(
            life=self.life.total(0),opposing_creatures=opponents,
            style=style,signals=signals)
        self.last_player_combat_decision={
            "style":style,**posture.as_dict(),
            "candidate_attackers":len(attackers),
            "selected_attackers":0,"target_seat":None}
        if not attackers:
            return ()
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
                -o.object_id),reverse=True)[:posture.reserve])
        chosen=[o.object_id for o in attackers
                if o.object_id not in keep][:posture.attack_limit]
        if not chosen:
            return ()
        opponent=self._target_seat(0,"value",combat=True)
        if opponent is None:
            return ()
        self.last_player_combat_decision.update({
            "selected_attackers":len(chosen),"target_seat":opponent})
        self._combat(0,"physical_pilot",turn,defender=opponent,
                     attacker_ids=set(chosen))
        return tuple(self.events[start:])

    def _record_zero_life_eliminations(self,turn):
        """Stop defeated seats contributing pressure, remove their owned cards.

        The kernel's leave_game path removes actual owned objects rather than
        converting them into graveyard deaths, which would create false death
        triggers. Seat zero's 100-card conservation is retained until the
        enclosing runner stops. This is life-zero only, not general SBA.
        """
        new=[]
        for seat in range(4):
            if (self.life.total(seat)>0
                    or seat in self._eliminated_seats):
                continue
            self._eliminated_seats.add(seat)
            if seat!=0:
                self.zones.leave_game(seat)
            else:
                self._defeated=True
            event=OpponentEvent(
                turn,seat,self.roles.get(seat,"physical_pilot"),
                "life_zero",None,0,seat)
            self.events.append(event)
            new.append(event)
        return tuple(new)

    def advance(self, turn):
        """Three opponents take their bounded abstract turns after seat 0.

        Their upkeep boundaries are real phase events; they can trigger
        Ophiomancer correctly. Other actions are abstract pressure with
        independently seeded variance and no unsupported rule claims.
        """
        if type(turn) is not int or turn < 1:
            raise ValueError("Positive turn required")
        current=len(self.events)
        self._record_zero_life_eliminations(turn)
        for seat in (1,2,3):
            if self._defeated:
                break
            if self.life.total(seat)<=0:
                continue
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
            self._record_zero_life_eliminations(turn)
            if self._defeated:
                break
        if not self.zones.assert_consistent():
            raise AssertionError("Opponent pressure corrupted authoritative zones")
        return tuple(self.events[current:])

    @property
    def defeated(self):
        return self._defeated
