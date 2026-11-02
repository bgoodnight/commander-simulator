"""Reproducible bounded opponent pressure over the authoritative physical kernel.

This is *not* a second rules engine or a claim to run three real Commander
decks. Three opponents have varied seeded development/removal/damage policies.
Their abstract creature tokens occupy the same battlefield, so reviewed
Pestilence, sweepers and death triggers interact with real physical objects.
Opponent combat uses physical attackers/blockers with explicit simplified legality;\nopponent spell effects remain abstract.
"""
from dataclasses import dataclass
from random import Random

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


class BoundedOpponentPressure:
    """Simulate between-turn pressure, not an unsupported multiplayer priority stack."""

    def __init__(self, zones, life, catalog, death_engine, phase_engine,
                 card_definition, *, seed=0, scenario="balanced"):
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
        self.rng = Random(seed * 1009 + 617)
        roles = list(SCENARIOS[scenario])
        self.rng.shuffle(roles)
        self.roles = dict(zip(range(1,4), roles))
        self.events = []
        self._defeated = False
        self._born = {}
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
        size = 2 if role in {"aggro","value"} else 1
        name = "Abstract " + role + " opponent creature"
        definition = self.definition(
            "stress:" + role, name, frozenset({"creature"}),
            base_power=size, base_toughness=size, coverage="approx")
        oid = self.zones.add(definition, seat, "battlefield", token=True)
        self._born[oid]=turn
        self.events.append(OpponentEvent(turn,seat,role,"abstract_creature",oid,size))

    def _exile_one(self, seat, turn, role):
        # Model a reviewed-like targeted exile pressure event, NOT an actual
        # spell cast from an opponent's hand. No invented mana or card.
        kernel = self.zones.kernel
        candidates = [
            o for o in kernel.on_battlefield()
            if o.controller == 0
            and bool(o.types & {"creature","enchantment","artifact"})
            and kernel.legal_target(seat,o.object_id,
                                    frozenset({"creature","enchantment","artifact"}))]
        if not candidates:
            return False
        # Target a consequential engine or commander over an expendable token.
        def score(o):
            raw=self.catalog.get(o.card.name,{})
            return (int("commander" in o.card.supertypes)*10
                    + (4 if o.card.name in {
                        "Pestilence","Ashnod's Altar","Pitiless Plunderer",
                        "Bastion of Remembrance"} else 0)
                    + min(5,int(raw.get("cmc") or 0)) - (4 if o.token else 0))
        target=max(candidates,key=lambda o:(score(o),-o.object_id))
        from .reviewed_death_effects import capture_battlefield
        before=capture_battlefield(kernel)
        moves=len(kernel.moves)
        self.zones.move(target.object_id,"exile","exile",commander_choice=True)
        if self.death_engine is not None:
            self.death_engine.resolve_deaths(before,move_index=moves,turn=turn)
        self.events.append(OpponentEvent(turn,seat,role,"abstract_exile",
                                         target.object_id))
        return True

    def _combat(self,seat,role,turn):
        """Resolve bounded combat using real blocker legality and damage/SBA.

        No first strike, trample assignment, prevention, double strike, or
        combat-trigger stack. Declines unsafe attacker/blocker assumptions.
        """
        kernel=self.zones.kernel
        used=set()
        attackers=[o for o in self._board(seat)
                   if not o.tapped and o.power>0
                   and self._born.get(o.object_id,0)<turn]
        if role=="control":
            attackers=attackers[:1]
        if role=="value":
            attackers=attackers[:2]
        for attacker in attackers:
            if self.life.total(0)<=0:
                break
            # Re-check live state: earlier combat could destroy an attacker.
            if attacker.object_id not in kernel.objects:
                continue
            blockers=kernel.legal_blockers(attacker.object_id,0,frozenset(used))
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
                    self.life.total(0)<=16):
                chosen=None
            attacker.tapped=True
            kernel._dirty()
            if chosen is None:
                self.life.damage(0,attacker.power,attacker.object_id)
                self.events.append(OpponentEvent(
                    turn,seat,role,"abstract_unblocked_damage",
                    attacker.object_id,attacker.power))
                continue
            used.add(chosen.object_id)
            from .reviewed_death_effects import capture_battlefield
            before=capture_battlefield(kernel)
            first_move=len(kernel.moves)
            # Simultaneous marked creature damage on existing physical objects.
            kernel.damage_creatures_together({
                attacker.object_id:chosen.power,
                chosen.object_id:attacker.power})
            # Lifelink is based on actual damage dealt; prevention and combat
            # damage triggers remain outside this bounded simulation.
            if "lifelink" in chosen.keywords and chosen.power>0:
                self.life.gain(0,chosen.power,chosen.object_id)
            # Deathtouch is a reusable combat lethal condition. It does not
            # ignore indestructible, and it applies after damage is marked.
            for source,target in ((attacker,chosen),(chosen,attacker)):
                if (source.power>0 and "deathtouch" in source.keywords
                        and target.object_id in kernel.objects
                        and "indestructible" not in kernel.get(target.object_id).keywords):
                    self.zones.move(target.object_id,"graveyard","state_based",
                                    commander_choice=True)
            if self.death_engine is not None:
                self.death_engine.resolve_deaths(
                    before,move_index=first_move,turn=turn)
            self.events.append(OpponentEvent(
                turn,seat,role,"abstract_blocked_combat",
                attacker.object_id,attacker.power))

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
            if role=="combo" and turn>=7 and self.life.total(0)>0:
                amount=3+turn//3+self.rng.choice((-1,0,0,1))
                self.life.lose(0,amount)
                self.events.append(OpponentEvent(
                    turn,seat,role,"abstract_combo_loss",None,amount))
            # Each opponent has its own end-of-turn damage cleanup and
            # duration expiration before the next player's turn begins.
            kernel=self.zones.kernel
            kernel.cleanup()
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
