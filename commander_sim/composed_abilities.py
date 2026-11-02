"""Reviewed compositional ability execution on the existing physical kernel.

Profiles are declarative: event + predicate + typed payment + effect sequence.
No profile may manufacture a permanent or a mana ability by matching prose.
This bounded implementation has no opponent priority/prevention, APNAP stack,
or combat. The caller explicitly supplies legal phase windows and choices.
"""
from dataclasses import dataclass, replace
from .ability_composition import (
    AbilitySlot, AbilityHandler, ComposedCard, AbilityDispatcher)
from .kernel_life import KernelLife
from .reviewed_death_effects import capture_battlefield
from .reviewed_token_spells import TokenBlueprint, create_reviewed_token_batches


_ASTARTES = TokenBlueprint(
    "Astartes Warrior", frozenset({"creature"}),
    frozenset({"Astartes", "Warrior"}), frozenset({"B"}), 2, 2,
    keywords=frozenset({"menace"}))


@dataclass(frozen=True)
class Predicate:
    kind: str
    def __post_init__(self):
        if self.kind not in {"always", "no_creatures", "life_lost_this_turn"}:
            raise ValueError("Unregistered composed predicate")


@dataclass(frozen=True)
class Payment:
    mana: str = ""
    x_generic: bool = False
    x_black_only: bool = False
    def __post_init__(self):
        if sum((bool(self.mana),self.x_generic,self.x_black_only))>1:
            raise ValueError("Only one explicit mana payment mode is supported")


@dataclass(frozen=True)
class Step:
    operation: str
    token: TokenBlueprint | None = None
    quantity: str = "one"
    def __post_init__(self):
        if self.operation not in {"create_tokens", "damage_all",
                                  "sacrifice_source", "lose_life", "amass"}:
            raise ValueError("Unregistered composed operation")
        if self.quantity not in {"one", "x"}:
            raise ValueError("Unregistered quantity variable")
        if (self.operation == "create_tokens") != (self.token is not None):
            raise ValueError("Token effects require exactly one token blueprint")


@dataclass(frozen=True)
class Ability:
    oracle_id: str
    oracle_excerpt: str
    event: str
    condition: Predicate
    payment: Payment
    steps: tuple[Step, ...]
    def __post_init__(self):
        if (not self.oracle_id or not self.oracle_excerpt
                or self.event not in {"end_step", "upkeep", "activate"}
                or not self.steps or not all(isinstance(s, Step) for s in self.steps)):
            raise ValueError("Incomplete reviewed composed ability")


# All differences between these cards are data. No card-name case statements
# appear in the executor.
ABILITIES = {
    "Mortarion, Daemon Primarch": (
        Ability("588eecbf-dcfc-4b97-b81c-8b9f3d39e08f",
                "At the beginning of your end step, you may pay {X}. If you do, create X 2/2 black Astartes Warrior creature tokens with menace. X can't be greater than the amount of life you lost this turn.",
                "end_step", Predicate("life_lost_this_turn"),
                Payment(x_generic=True),
                (Step("create_tokens", _ASTARTES, "x"),)),
    ),
    "Dreadhorde Invasion": (
        Ability("01deabbb-af6a-4998-99a7-35b7cfa9ef77",
                "At the beginning of your upkeep, you lose 1 life and amass Zombies 1.",
                "upkeep", Predicate("always"), Payment(),
                (Step("lose_life"), Step("amass"))),
    ),
    "Crypt Rats": (
        Ability("104095ed-55e3-408e-bf70-4fe06bb16d2f",
                "{X}: This creature deals X damage to each creature and each player. Spend only black mana on X.",
                "activate", Predicate("always"), Payment(x_black_only=True),
                (Step("damage_all",quantity="x"),)),
    ),
    "Plague Spitter": (
        Ability("5feedfb0-30e6-400d-9e28-d541ea1aa14e",
                "At the beginning of your upkeep, this creature deals 1 damage to each creature and each player.",
                "upkeep", Predicate("always"), Payment(),
                (Step("damage_all"),)),
    ),
    "Pestilence": (
        Ability("dafe63ef-f3d6-45e7-877a-573da92ba85e",
                "{B}: This enchantment deals 1 damage to each creature and each player.",
                "activate", Predicate("always"), Payment("{B}"),
                (Step("damage_all"),)),
        Ability("dafe63ef-f3d6-45e7-877a-573da92ba85e",
                "At the beginning of the end step, if no creatures are on the battlefield, sacrifice this enchantment.",
                "end_step", Predicate("no_creatures"), Payment(),
                (Step("sacrifice_source"),)),
    ),
    "Pestilence Demon": (
        Ability("2572add6-c0b1-44bd-8713-1e94e3fe69d6",
                "{B}: This creature deals 1 damage to each creature and each player.",
                "activate", Predicate("always"), Payment("{B}"),
                (Step("damage_all"),)),
    ),
    "Thrashing Wumpus": (
        Ability("ef220824-fab4-4d8e-9ba4-65ff5ba1db66",
                "{B}: This creature deals 1 damage to each creature and each player.",
                "activate", Predicate("always"), Payment("{B}"),
                (Step("damage_all"),)),
    ),
}


def reviewed_composed_permanent(name, raw):
    """Authorize an ordinary enchantment body with reviewed later abilities.

    All mandatory entry effects must be absent; actual activated/triggered
    slots are independently admitted by ComposedAbilityEngine.
    """
    if not isinstance(raw,dict) or raw.get("layout")!="normal":
        return False
    if raw.get("type_line","").split(" — ",1)[0]!="Enchantment":
        return False
    profiles=ABILITIES.get(name,())
    return bool(profiles and all(
        rule.oracle_id==raw.get("oracle_id") and
        rule.oracle_excerpt in raw.get("oracle_text","")
        for rule in profiles))


@dataclass(frozen=True)
class Execution:
    source_id: int
    operation: str
    created_ids: tuple[int, ...] = ()
    life_lost: int = 0
    deaths: int = 0


class ComposedAbilityEngine:
    """Connects reviewed profiles to authoritative kernel/life/death hosts."""

    def __init__(self, zones, life: KernelLife, catalog, mana_service,
                 death_engine=None):
        if (zones.kernel is not life.kernel or
                mana_service.kernel is not zones.kernel):
            raise ValueError("Composed abilities require a shared physical kernel")
        self.zones = zones
        self.life = life
        self.catalog = catalog
        self.mana_service = mana_service
        self.death_engine = death_engine
        self._handled = set()

    def _abilities(self, source, event):
        raw = self.catalog.get(source.card.name)
        if (source.zone != "battlefield" or not isinstance(raw, dict)
                or raw.get("oracle_id") != source.card.card_id):
            return ()
        text = raw.get("oracle_text", "")
        return tuple(rule for rule in ABILITIES.get(source.card.name, ())
                     if rule.event == event
                     and rule.oracle_id == source.card.card_id
                     and rule.oracle_excerpt in text)

    def _condition(self, rule, controller, start_life_index):
        if rule.condition.kind == "no_creatures":
            return not any("creature" in obj.types
                           for obj in self.zones.kernel.on_battlefield())
        if rule.condition.kind == "life_lost_this_turn":
            return self.life_lost_since(controller, start_life_index) > 0
        return True

    def life_lost_since(self, seat, first_change):
        changes = self.life.kernel.life_changes
        if type(first_change) is not int or not 0 <= first_change <= len(changes):
            raise ValueError("Invalid authoritative life-event boundary")
        return sum(change.amount for change in changes[first_change:]
                   if change.seat == seat and change.kind in {"loss", "damage"})

    def _execute(self, source, rule, *, x=0):
        before = capture_battlefield(self.zones.kernel)
        first_move = len(self.zones.kernel.moves)
        created = ()
        loss = 0
        for step in rule.steps:
            n = x if step.quantity == "x" else 1
            if step.operation == "create_tokens":
                if n:
                    created += tuple(create_reviewed_token_batches(
                        self.zones, source.controller,
                        (replace(step.token, count=n),)))
            elif step.operation == "lose_life":
                self.life.lose(source.controller,n,source.object_id)
                loss += n
            elif step.operation == "amass":
                # Shared amass primitive: an existing Army receives counters
                # and gains Zombie subtype, otherwise create a 0/0 Zombie Army
                # and add the counters before checking state-based actions.
                army=next((o for o in sorted(
                    self.zones.kernel.on_battlefield(),
                    key=lambda object_:object_.object_id)
                    if o.controller==source.controller and
                    "creature" in o.types and "Army" in o.subtypes),None)
                if army is None:
                    army_blueprint=TokenBlueprint(
                        "Zombie Army",frozenset({"creature"}),
                        frozenset({"Zombie","Army"}),frozenset({"B"}),0,0)
                    token_ids=create_reviewed_token_batches(
                        self.zones,source.controller,(army_blueprint,))
                    created+=tuple(token_ids)
                    army=self.zones.kernel.get(token_ids[0])
                elif "Zombie" not in army.subtypes:
                    army.card=replace(army.card,
                                      subtypes=army.subtypes | frozenset({"Zombie"}))
                    self.zones.kernel._dirty()
                self.zones.kernel.add_counter(army.object_id,"+1/+1",n)
            elif step.operation == "damage_all":
                # Bounded no-prevention damage: all creature damage is marked
                # simultaneously, then the existing kernel runs state-based
                # actions. Player damage is separately marked as damage, not
                # as an invented life-payment cost.
                creatures = tuple(o.object_id
                                  for o in self.zones.kernel.on_battlefield()
                                  if "creature" in o.types)
                for seat in sorted(self.life.kernel.life_totals):
                    self.life.damage(seat, n, source.object_id)
                    loss += n
                if creatures:
                    self.zones.kernel.damage_creatures_together(
                        {oid:n for oid in creatures})
            elif step.operation == "sacrifice_source":
                self.zones.move(source.object_id, "graveyard", "sacrifice")
        resolved = ()
        if self.death_engine is not None:
            resolved = self.death_engine.resolve_deaths(
                before, move_index=first_move, turn=self._turn)
        return Execution(source.object_id, "+".join(s.operation for s in rule.steps),
                         created, loss, len(resolved))

    def _dispatch_reviewed(self, source, rule, *, x=0):
        """Use the project's existing ability-level fidelity dispatcher.

        The composed profile is a declaration; its already-reviewed atom
        sequence is executed by the same callback mechanism as other
        reviewed creature, search, phase and sacrifice abilities.
        """
        slot_id = "composed:" + rule.event + ":" + str(
            ABILITIES[source.card.name].index(rule))
        slot = AbilitySlot(
            rule.oracle_id, "front", slot_id,
            "triggered" if rule.event == "end_step" else "activated",
            rule, rule.oracle_excerpt, "pinned-composed-v1",
            frozenset({"physical_zones", "composed_effects"}))
        card = ComposedCard(
            rule.oracle_id, self.catalog[source.card.name]["oracle_text"],
            (slot,),
            (AbilityHandler(slot.key, "simplified", rule,
                            slot.source_revision, slot.prereqs,
                            ("No opponent priority, damage prevention, or APNAP stack",)),))
        dispatcher = AbilityDispatcher(
            card, "hybrid", frozenset({"physical_zones", "composed_effects"}))
        return dispatcher.invoke(
            slot.slot_id, source.object_id,
            lambda operation: self._execute(source, operation, x=x))

    def activate(self, source_id, *, turn, legal_window=True, x=0):
        """Perform one legal reviewed activation; repeat calls are permitted.

        Caller owns priority and activation strategy. This deliberately
        doesn't choose how often to activate an ability.
        """
        if type(turn) is not int or turn < 1 or legal_window is not True:
            raise ValueError("Activation requires an explicitly legal window")
        source = self.zones.kernel.get(source_id)
        rules = self._abilities(source, "activate")
        if not rules:
            raise ValueError("Unreviewed activated ability")
        rule = rules[0]
        if not self._condition(rule, source.controller, 0):
            return None
        if type(x) is not int or x<0:
            raise ValueError("X must be nonnegative")
        if rule.payment.x_black_only:
            # Each pip of an X-only-black payment is a real {B} requirement,
            # not an unrestricted {X} generic source.
            if x==0:
                return None
            cost="{B}"*x
        else:
            if x:
                raise ValueError("An X choice was supplied to a fixed ability")
            cost=rule.payment.mana
        if self.mana_service.plan(source.controller,cost) is None:
            return None
        paid=self.mana_service.pay(source.controller,cost)
        if paid is None:
            return None
        self._turn=turn
        return self._dispatch_reviewed(source,rule,x=x)

    def upkeep(self, *, active_seat, turn):
        """Resolve source-reviewed own-upkeep profiles on authoritative zones."""
        if (type(turn) is not int or turn<1 or
                type(active_seat) is not int or
                active_seat not in self.life.kernel.life_totals):
            raise ValueError("Invalid composed upkeep")
        self._turn=turn
        outcomes=[]
        for source in sorted(tuple(self.zones.kernel.on_battlefield()),
                             key=lambda obj:obj.object_id):
            if source.controller!=active_seat:
                continue
            for slot,rule in enumerate(self._abilities(source,"upkeep")):
                key=(turn,active_seat,"upkeep",source.object_id,slot)
                if key in self._handled:
                    continue
                self._handled.add(key)
                if self._condition(rule,active_seat,len(self.life.kernel.life_changes)):
                    outcomes.append(self._dispatch_reviewed(source,rule))
        return tuple(outcomes)

    def end_step(self, *, active_seat, turn, life_start_index, x_choices=None):
        """Execute reviewed end-step triggers with host-provided X choices.

        Requires the first life-change index captured at the start of the
        current turn. Zero X declines Mortarion's optional payment. The
        current bounded host resolves in source-ID order, without priority.
        """
        if type(turn) is not int or turn < 1:
            raise ValueError("Invalid turn")
        if type(active_seat) is not int or active_seat not in self.life.kernel.life_totals:
            raise ValueError("Invalid active seat")
        self.life_lost_since(active_seat, life_start_index)
        choices = {} if x_choices is None else x_choices
        if not isinstance(choices, dict):
            raise TypeError("X choices must map physical source IDs to integers")
        self._turn = turn
        # All end-step conditions are checked at the triggering boundary,
        # before Mortarion can create tokens or another trigger changes life.
        # Triggers then resolve in bounded source order (not APNAP/priority).
        pending = []
        for source in sorted(tuple(self.zones.kernel.on_battlefield()),
                             key=lambda o:o.object_id):
            for slot, rule in enumerate(self._abilities(source, "end_step")):
                if source.controller != active_seat and rule.condition.kind != "no_creatures":
                    continue
                key = (turn, active_seat, source.object_id, slot, rule.oracle_excerpt)
                if key in self._handled:
                    continue
                if self._condition(rule, source.controller, life_start_index):
                    pending.append((key, source, rule))
                else:
                    # At the beginning of the step the condition was false.
                    self._handled.add(key)
        # Validate all externally supplied decisions before mutating state.
        for key, source, rule in pending:
            x = choices.get(source.object_id, 0)
            if type(x) is not int or x < 0:
                raise ValueError("X must be a nonnegative integer")
            if rule.payment.x_generic and x > self.life_lost_since(
                    source.controller, life_start_index):
                raise ValueError("X exceeds actual life lost this turn")
        results = []
        for key, source, rule in pending:
            # An intervening-if trigger is tested both when it triggers and
            # when it resolves. This matters for Pestilence if a creature
            # enters after the end step began but before the trigger resolves.
            if rule.condition.kind == "no_creatures" and not self._condition(
                    rule, source.controller, life_start_index):
                self._handled.add(key)
                continue
            x = choices.get(source.object_id, 0)
            if rule.payment.x_generic:
                if not x:
                    self._handled.add(key)
                    continue
                paid = self.mana_service.pay(source.controller, "{" + str(x) + "}")
                if paid is None:
                    self._handled.add(key)
                    continue
            results.append(self._dispatch_reviewed(source, rule, x=x))
            self._handled.add(key)
        return tuple(results)
