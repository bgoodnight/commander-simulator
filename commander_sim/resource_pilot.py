"""Reusable bounded resource sequencing policy; never grants card abilities.

The reviewed sacrifice engine and physical mana planner remain authoritative.
This layer only decides when trading an expendable token for mana is likely
to unlock an independently reviewed spell in the current main phase.
"""
from .mana_costs import parse_fixed_mana_cost, UnsupportedManaCost
from .reviewed_sacrifice_actions import SACRIFICE_MODES
from .resource_development import assess_resources

_MANA_OPERATIONS = frozenset({"colorless_mana", "any_color_mana"})


def choose_token_mana_sacrifice(zones, seat, catalog, mana_service,
                                *, supported_spell, max_sacrifices=4):
    """Return (source_id, token_id) or None, with bounded lookahead.

    Requires a real token creature and a registered mana-producing sacrifice
    outlet. The only decision heuristic is a currently unpayable *reviewed*
    spell plausibly reachable using up to max_sacrifices token sacrifices.
    It never assumes extra token creation, untaps, or repeated triggers.
    """
    if mana_service.kernel is not zones.kernel or not callable(supported_spell):
        raise ValueError("Resource policy requires the authoritative host")
    if type(max_sacrifices) is not int or max_sacrifices < 1:
        raise ValueError("Expected positive sacrifice bound")
    objects = list(zones.kernel.on_battlefield())
    sources = sorted((o for o in objects if o.controller == seat
                      and o.card.name in SACRIFICE_MODES
                      and SACRIFICE_MODES[o.card.name].action in _MANA_OPERATIONS
                      and not o.tapped),
                     key=lambda o:o.object_id)
    tokens = sorted((o for o in objects if o.controller == seat
                     and o.token and "creature" in o.types
                     and "commander" not in o.card.supertypes),
                    key=lambda o:(o.power, o.object_id))
    if not sources or not tokens:
        return None
    resource = assess_resources(zones.kernel, mana_service, seat)
    current = resource.available_fixed_mana
    per_token = max(2 if SACRIFICE_MODES[source.card.name].action == "colorless_mana"
                    else 1 for source in sources)
    capacity = current + per_token * min(len(tokens), max_sacrifices)
    has_payoff = False
    for oid in zones.ids(seat, "hand"):
        card = zones.kernel.get(oid)
        if not supported_spell(card):
            continue
        raw = catalog.get(card.card.name)
        if not raw:
            continue
        try:
            cost = parse_fixed_mana_cost(raw.get("mana_cost"))
            payable = mana_service.plan_spell(seat, raw["mana_cost"], card)
        except (UnsupportedManaCost, ValueError):
            continue
        total = cost.generic + len(cost.colored)
        if payable is None and current < total <= capacity:
            has_payoff = True
            break
    if not has_payoff:
        return None
    for source in sources:
        mode = SACRIFICE_MODES[source.card.name]
        for victim in tokens:
            if mode.sacrifice_other and source.object_id == victim.object_id:
                continue
            return source.object_id, victim.object_id
    return None


def plan_common_spell(zones, seat, source, recipe, catalog, mana_service, life):
    """Reusable conservative choices for a reviewed shared-spell recipe.

    No guessed targets or invented mana. Returns (fixed_paid_cost, x,
    sacrifice_ids) or None. The same policy handles any registered spell
    using the recipe's typed cost and output parameters.
    """
    from .reviewed_common_spells import spell_payment_cost
    if source.object_id not in zones.ids(seat, "hand"):
        return None
    # Low life is a constraint on *life-consuming* effects, not a blanket
    # prohibition on spells that can gain life (for example, an X drain).
    # Per-step life loss is validated below before the cast is admitted.
    if life.total(seat) <= 0:
        return None
    eligible = sorted(
        (o for o in zones.kernel.on_battlefield()
         if o.controller==seat and "commander" not in o.card.supertypes
         and (bool(o.types & {"artifact","creature"})
              if recipe.sacrifice_cost=="artifact_or_creature"
              else "creature" in o.types)),
        key=lambda o: (not o.token,
                        # Nontoken creatures are eligible only if a reviewed
                        # "self dies" trigger can recover some of their value.
                        o.power if "creature" in o.types else 0,
                        o.object_id))
    victims=()
    if recipe.sacrifice_cost=="artifact_or_creature":
        approved=[o for o in eligible if o.token]
        if not approved:
            from .reviewed_death_effects import DEATH_RULES
            approved=[o for o in eligible
                      if any(rule.action.scope=="self_creature"
                             for rule in DEATH_RULES.get(o.card.name,()))]
        if not approved:
            return None
        victims=(approved[0].object_id,)
    elif recipe.sacrifice_cost=="optional_creatures":
        victims=tuple(o.object_id for o in eligible if o.token)[:3]
    multiplier=1+len(victims) if recipe.sacrifice_cost=="optional_creatures" else 1
    draws=multiplier*sum(step.quantity for step in recipe.steps if step.kind=="draw")
    if draws>len(zones.ids(seat,"library")):
        return None
    loss=multiplier*sum(step.quantity for step in recipe.steps if step.kind=="lose_life")
    if loss and loss>=life.total(seat)-4:
        return None
    if recipe.variable_x:
        max_x=min(16,assess_resources(zones.kernel,mana_service,seat).available_fixed_mana)
        # Small but positive X is a legal, sometimes game-saving play.
        # The shared mana planner, not a total-mana estimate, determines
        # whether the actual colored and generic payment is possible.
        for x in range(max_x,0,-1):
            cost=spell_payment_cost(recipe,x)
            try:
                preview=mana_service.plan_spell(
                    seat,cost,source,excluded_source_ids=victims)
            except ValueError as error:
                if str(error)!="Bounded mana search exhausted; no action committed":
                    raise
                # Never guess that X was payable. Conservatively decline
                # the entire spell when source planning is inconclusive.
                return None
            if preview is not None:
                return cost,x,victims
        return None
    cost=spell_payment_cost(recipe)
    try:
        preview=mana_service.plan_spell(
            seat,cost,source,excluded_source_ids=victims)
    except ValueError as error:
        if str(error)!="Bounded mana search exhausted; no action committed":
            raise
        return None
    if preview is None:
        return None
    return cost,0,victims


def ritual_enables_spell(zones,seat,source,catalog,mana_service):
    """Avoid burning Dark Ritual unless its mana can unlock a legal spell.

    This is bounded decision support, not a second mana solver. A currently
    unpayable verified spell must become plausibly affordable with +2 net
    available mana; mere speculative future draws do not justify spending it.
    """
    from .reviewed_early_cards import REVIEWED_BY_DECK
    current=assess_resources(zones.kernel,mana_service,seat).available_fixed_mana
    for oid in zones.ids(seat,"hand"):
        other=zones.kernel.get(oid)
        if oid==source.object_id:
            continue
        raw=catalog.get(other.card.name,{})
        if raw.get("oracle_id")!=other.card.card_id:
            continue
        cost=raw.get("mana_cost","")
        try:
            fixed=parse_fixed_mana_cost(cost.replace("{B/P}","{B}"))
        except (UnsupportedManaCost,ValueError):
            continue
        total=fixed.generic+len(fixed.colored)
        if current < total <= current+2 and "B" in fixed.colored:
            return True
    return False


def choose_composed_activation(zones, seat, life, mana_service, catalog, *,
                               activations_this_turn=0):
    """Choose an optional reviewed global damage action by physical net value.

    A fixed damage-all activation should not wipe friendly bodies for a
    speculative token engine. Conversely, a positive enemy sweep is useful
    even without a commander present. A safe one-life self-trigger is
    allowed only when a reviewed end-step life-loss engine is present and
    enough mana remains to pay for its token output.
    """
    from .composed_abilities import ABILITIES
    if activations_this_turn>=1 or life.total(seat)<=12:
        return None
    available=assess_resources(zones.kernel,mana_service,seat).available_fixed_mana
    if available<1:
        return None
    board=list(zones.kernel.on_battlefield())
    own=[o for o in board if o.controller==seat and "creature" in o.types]
    enemies=[o for o in board if o.controller!=seat and
             "creature" in o.types and life.total(o.controller)>0]
    commander_engines=[]
    for source in board:
        if source.controller!=seat:
            continue
        rules=ABILITIES.get(source.card.name,())
        raw=catalog.get(source.card.name,{})
        if raw.get("oracle_id")!=source.card.card_id:
            continue
        if any(r.event=="end_step" and r.payment.x_generic
               and r.oracle_id==source.card.card_id
               and r.oracle_excerpt in raw.get("oracle_text","")
               for r in rules):
            commander_engines.append(source)
    candidates=[]
    for source in board:
        raw=catalog.get(source.card.name,{})
        if source.controller!=seat or raw.get("oracle_id")!=source.card.card_id:
            continue
        for rule in ABILITIES.get(source.card.name,()):
            if (rule.event!="activate" or rule.payment.x_generic
                    or rule.payment.x_black_only
                    or rule.oracle_excerpt not in raw.get("oracle_text","")
                    or not any(step.operation=="damage_all" for step in rule.steps)):
                continue
            try:
                if mana_service.plan(seat,rule.payment.mana) is None:
                    continue
            except ValueError as err:
                if str(err)!="Bounded mana search exhausted; no action committed":
                    raise
                continue
            damage=1  # Reviewed fixed damage_all step in this bounded kernel.
            def killed(obj):
                return (obj.toughness-obj.damage_marked<=damage and
                        "indestructible" not in obj.keywords)
            enemy_kills=sum(killed(o) for o in enemies)
            own_kills=sum(killed(o) for o in own)
            has_positive_sweep=(enemy_kills>=2 and enemy_kills>own_kills)
            has_safe_life_engine=(bool(commander_engines)
                and available>=3 and life.total(seat)>=22
                and own_kills==0 and len(own)<3)
            if not (has_positive_sweep or has_safe_life_engine):
                continue
            # Prefer the best immediate board trade, then a safe engine setup.
            score=4*(enemy_kills-own_kills)+int(has_safe_life_engine)
            candidates.append((-score,source.object_id))
    return min(candidates)[1] if candidates else None


def choose_composed_x_activation(zones,seat,life,mana_service,catalog):
    """General bounded policy for black-only X area-damage activations.

    Declines any X that trades too many own creatures or threatens lethal
    self-damage. The engine, not this pilot, validates black-only payment and
    source identity. Works for future X-black damage cards using the same
    declarative ability parameters.
    """
    from .composed_abilities import ABILITIES
    kernel=zones.kernel
    if life.total(seat)<=8:
        return None
    enemies=[o for o in kernel.on_battlefield()
             if o.controller!=seat and "creature" in o.types]
    own=[o for o in kernel.on_battlefield()
         if o.controller==seat and "creature" in o.types]
    if len(enemies)<2:
        return None
    candidates=[]
    for source in sorted(own,key=lambda o:o.object_id):
        raw=catalog.get(source.card.name,{})
        if raw.get("oracle_id")!=source.card.card_id:
            continue
        for rule in ABILITIES.get(source.card.name,()):
            if not (rule.event=="activate" and rule.payment.x_black_only
                    and rule.oracle_excerpt in raw.get("oracle_text","")
                    and any(step.operation=="damage_all"
                            and step.quantity=="x" for step in rule.steps)):
                continue
            for x in range(1,min(5,life.total(seat)-8)+1):
                try:
                    payment=mana_service.plan(seat,"{B}"*x)
                except ValueError as err:
                    if str(err)!="Bounded mana search exhausted; no action committed":
                        raise
                    break
                if payment is None:
                    continue
                enemy_kills=sum(o.toughness-o.damage_marked<=x
                     and "indestructible" not in o.keywords for o in enemies)
                self_kills=sum(o.toughness-o.damage_marked<=x
                     and "indestructible" not in o.keywords for o in own)
                if enemy_kills>=2 and enemy_kills>self_kills:
                    # Avoid paying more life/mana than necessary for an
                    # equivalent sweep. Prefer a stronger net board swing.
                    candidates.append((enemy_kills-self_kills,-x,
                                       -source.object_id,source.object_id,x))
    if not candidates:
        return None
    best=max(candidates)
    return best[3],best[4]


def choose_variable_end_step_payments(zones, seat, life, mana_service,
                                      catalog, life_start_index):
    """Supply explicit mana-backed X choices, never inventing triggered mana."""
    from .composed_abilities import ABILITIES
    lost=sum(event.amount for event in life.kernel.life_changes[life_start_index:]
             if event.seat==seat and event.kind in {"loss","damage"})
    if lost<=0:
        return {}
    choices={}
    for source in zones.kernel.on_battlefield():
        raw=catalog.get(source.card.name,{})
        if source.controller!=seat or raw.get("oracle_id")!=source.card.card_id:
            continue
        for rule in ABILITIES.get(source.card.name,()):
            if not (rule.event=="end_step" and rule.payment.x_generic
                    and rule.oracle_excerpt in raw.get("oracle_text","")):
                continue
            for x in range(min(lost,8),0,-1):
                if mana_service.plan(seat,"{"+str(x)+"}") is not None:
                    choices[source.object_id]=x
                    break
    return choices


def choose_utility_activation(zones,seat,life,mana_service,catalog,
                              *,hand_cast_reviewed,tap_ready=None):
    """Select at most one value-positive utility activation at this boundary.

    This is an explicit policy over registered UtilityRule parameters, not
    hard-coded behavior attached to names. Repeated activations are legal in
    the shared executor; a bounded pilot may choose fewer.
    """
    from .reviewed_utility_activations import reviewed_utility
    from .reviewed_sacrifice_actions import SACRIFICE_MODES
    from .graveyard_recipes import GraveyardRecipe,eligible_graveyard_cards
    hand_size=len(zones.ids(seat,"hand"))
    land_count=sum("land" in o.types and o.controller==seat
                   for o in zones.kernel.on_battlefield())
    sources=[]
    for source in zones.kernel.objects.values():
        if source.controller!=seat:
            continue
        raw=catalog.get(source.card.name)
        rule=reviewed_utility(source.card.name,raw)
        if (rule is None or source.card.card_id!=rule.oracle_id
                or source.zone!=rule.source_zone
                or rule.tap and source.tapped
                or rule.tap_creature and (
                    tap_ready is None or not tap_ready(source))):
            continue
        if life.total(seat)<12 and (rule.life or rule.life_by_commander_colors):
            continue
        if rule.life_loss_after and life.total(seat)<=rule.life_loss_after+4:
            continue
        tap_cost_ids=()
        if rule.tap_count:
            cost_options=sorted((o for o in zones.kernel.on_battlefield()
                if o.controller==seat and not o.tapped
                and "creature" in o.types and rule.tapped_subtype in o.subtypes),
                key=lambda o:(not o.token,o.power,o.object_id))
            if len(cost_options)<rule.tap_count:
                continue
            tap_cost_ids=tuple(o.object_id for o in cost_options[:rule.tap_count])
        excluded=tuple(((source.object_id,) if rule.tap else ()) + tap_cost_ids)
        if (rule.mana and
            mana_service.plan(seat,rule.mana,excluded_source_ids=excluded) is None):
            continue
        target=None
        if rule.operation=="creature_to_hand":
            if hand_size>=4:
                continue
            target_choices=[oid for oid in zones.ids(seat,"graveyard")
                if "creature" in zones.kernel.get(oid).types
                and rule.target_subtypes<=zones.kernel.get(oid).subtypes
                and rule.target_supertypes<=zones.kernel.get(oid).card.supertypes
                and hand_cast_reviewed(zones.kernel.get(oid))]
            if not target_choices:
                continue
            target=max(target_choices,key=lambda oid: (
                catalog.get(zones.kernel.get(oid).card.name,{}).get("cmc",0),-oid))
        elif rule.operation=="exile_graveyard_token":
            candidates=eligible_graveyard_cards(
                zones,seat,GraveyardRecipe("exile","any",
                                          frozenset({"creature"})))
            if not candidates:
                continue
            # Prefer disrupting an opposing graveyard before exiling our own
            # future reanimation piece. No commander or card-name tables.
            target=max(candidates,key=lambda oid: (
                zones.kernel.get(oid).owner!=seat,
                catalog.get(zones.kernel.get(oid).card.name,{}).get("cmc",0),
                -oid))
        elif rule.operation=="all_legendary_creatures_to_hand":
            if not any("creature" in zones.kernel.get(oid).types
                  and rule.target_supertypes <= zones.kernel.get(oid).card.supertypes
                  for oid in zones.ids(seat,"graveyard")):
                continue
        elif rule.operation=="self_to_battlefield_tapped":
            has_outlet=any(o.controller==seat and o.zone=="battlefield"
                           and o.card.name in SACRIFICE_MODES
                           for o in zones.kernel.objects.values())
            if not has_outlet:
                continue
        elif rule.operation=="draw":
            if len(zones.ids(seat,"library"))<rule.draw_count:
                continue
            if rule.tap_count and hand_size>=5:
                continue
            if rule.discard:
                if land_count<4:
                    continue
            elif rule.sacrifice:
                if hand_size>0 or land_count<5:
                    continue
            elif hand_size>=4:
                continue
        elif rule.operation=="drain_opponents":
            black=sum("B" in (o.card.colors or ())
                      for o in zones.kernel.on_battlefield()
                      if o.controller==seat)
            if black<2:
                continue
        priority={"creature_to_hand":0,"all_legendary_creatures_to_hand":0,
                  "exile_graveyard_token":1,"self_to_battlefield_tapped":1,
                  "draw":2,"drain_opponents":3}[rule.operation]
        sources.append((priority,source.object_id,target))
    if not sources:
        return None
    _,source_id,target=min(sources)
    return source_id,target


def choose_end_step_token_mana(zones,seat,life,mana_service,catalog,
                               *,life_start_index,max_sacrifices=3):
    """Spend a disposable token for a larger reviewed end-step X payoff.

    A source must be a live, source-reviewed creature-sacrifice mana outlet.
    The potential increase in X must exceed the token being sacrificed;
    this forbids speculative or net-zero sacrifices to fund Mortarion.
    No token is invented by the choice operation; its caller must invoke the
    existing physical reviewed sacrifice activation and re-evaluate.
    """
    from .composed_abilities import ABILITIES
    from .reviewed_sacrifice_actions import SACRIFICE_MODES
    if type(life_start_index) is not int:
        raise ValueError("Expected physical turn life ledger index")
    if type(max_sacrifices) is not int or max_sacrifices < 1:
        raise ValueError("Expected positive sacrifice bound")
    changes=life.kernel.life_changes
    if not 0<=life_start_index<=len(changes):
        raise ValueError("Invalid life ledger index")
    lost=sum(change.amount for change in changes[life_start_index:]
             if change.seat==seat and change.kind in {"loss","damage"})
    if lost<2:
        return None
    objective=False
    for obj in zones.kernel.on_battlefield():
        if obj.controller!=seat:
            continue
        raw=catalog.get(obj.card.name,{})
        if raw.get("oracle_id")!=obj.card.card_id:
            continue
        if any(rule.event=="end_step" and rule.payment.x_generic
               and rule.oracle_id==obj.card.card_id
               and rule.oracle_excerpt in raw.get("oracle_text","")
               for rule in ABILITIES.get(obj.card.name,())):
            objective=True
            break
    if not objective:
        return None
    tokens=sorted(
        (obj for obj in zones.kernel.on_battlefield()
         if obj.controller==seat and obj.token
         and "creature" in obj.types
         and "commander" not in obj.card.supertypes),
        key=lambda obj:(obj.power,obj.object_id))
    if not tokens:
        return None
    # Actual colored/general spendability, not simply nominal source count.
    baseline=max(
        (x for x in range(min(lost,20),-1,-1)
         if mana_service.plan(seat,"{"+str(x)+"}") is not None),
        default=0)
    for source in sorted(zones.kernel.on_battlefield(),key=lambda o:o.object_id):
        if source.controller!=seat or source.tapped:
            continue
        rule=SACRIFICE_MODES.get(source.card.name)
        raw=catalog.get(source.card.name,{})
        if (rule is None or rule.action not in {"colorless_mana","any_color_mana"}
                or raw.get("oracle_id")!=source.card.card_id
                or rule.oracle_id!=source.card.card_id
                or rule.excerpt not in raw.get("oracle_text","")):
            continue
        yield_mana=2 if rule.action=="colorless_mana" else 1
        if min(lost,baseline+yield_mana)-baseline < 2:
            continue
        victim=next((t for t in tokens
                     if t.object_id!=source.object_id),None)
        if victim is not None:
            return source.object_id,victim.object_id
    return None


def choose_reviewed_removal(zones, seat, life, rule, *, turn=1):
    """Choose a worthwhile existing battlefield target for a reviewed removal.

    No imagined enemy permanents. The same threat/conservation heuristic is
    shared by all physical destroy and debuff spells; it deliberately declines
    marginal one-for-ones and unfavorable sweepers.
    Returns (target_id, x) or None. None never authorizes a cast.
    """
    from .reviewed_removal_spells import valid_removal_target, reviewed_amount
    kernel=zones.kernel
    own=[o for o in kernel.on_battlefield()
         if o.controller==seat and "creature" in o.types]
    opponents=[o for o in kernel.on_battlefield()
               if o.controller!=seat and "creature" in o.types]
    if (not opponents and rule.target not in {
            "creature_or_enchantment","opponent_creature_or_enchantment"}):
        return None
    danger=life.total(seat)<=18
    if rule.operation=="debuff_all":
        if rule.x_life_cost:
            if life.total(seat)<=4:
                return None
            magnitudes=range(min(5,life.total(seat)-5),0,-1)
        else:
            magnitudes=(reviewed_amount(kernel,seat,rule),)
        for magnitude in magnitudes:
            if magnitude<=0:
                continue
            foe=sum(o.toughness<=magnitude for o in opponents)
            friendly=sum(o.toughness<=magnitude for o in own)
            if foe>=2 and foe>=friendly+1 and (danger or foe>=3):
                return None,magnitude if rule.x_life_cost else 0
        return None
    if rule.operation=="destroy_below_power":
        options=[]
        for source in own:
            if not valid_removal_target(zones,seat,rule,source.object_id):
                continue
            foe=sum(o.power<source.power for o in opponents)
            friends=sum(o.object_id!=source.object_id
                        and o.power<source.power for o in own)
            if foe>=2 and foe>friends:
                options.append((foe-friends,source.power,source.object_id))
        if not options:
            return None
        return max(options)[2],0
    valid=[o for o in kernel.on_battlefield()
           if valid_removal_target(zones,seat,rule,o.object_id)
           and o.controller!=seat]
    if not valid:
        return None
    if rule.operation=="destroy_and_debuff":
        foe=sum(o.toughness<=rule.amount for o in opponents)
        friends=sum(o.toughness<=rule.amount for o in own)
        if foe < friends+2:
            return None
    scored=[]
    for obj in valid:
        creature="creature" in obj.types
        power=obj.power if creature else 0
        toughness=obj.toughness if creature else 0
        # Noncreature enchantments are real engine permanents even without
        # power/toughness. Do not ignore legal removal solely because the
        # threat heuristic was originally combat-only.
        threat=(7 if "enchantment" in obj.types and not creature
                else power+min(3,toughness))
        if rule.operation=="debuff_same_name":
            group=sum(o.card.name==obj.card.name and
                      o.toughness<=rule.amount for o in opponents)
            if not group:
                continue
            threat+=2*(group-1)
        if rule.operation=="damage_gain" and (not creature or reviewed_amount(kernel,seat,rule)<=0):
            continue
        if rule.operation=="destroy" and not danger and threat<6:
            continue
        if rule.operation=="debuff_same_name" and threat<4 and not danger:
            continue
        if rule.operation=="destroy" and rule.life_cost=="target_mana_value":
            # Only a real pinned target or a token has known mana value.
            if not obj.token:
                continue
        scored.append((threat,-obj.object_id,obj.object_id))
    return (max(scored)[2],0) if scored else None


def choose_attachment_use(zones,seat,attachments,mana_service,catalog):
    """Select one source-paid attachment action from reviewed parameters.

    Scores legal targets by survival, protection of valuable engines and
    draw-on-death opportunities; does not know particular card-to-card combos.
    An existing useful attachment is not needlessly moved each turn.
    """
    kernel=zones.kernel
    options=[]
    own=[o for o in kernel.on_battlefield()
         if o.controller==seat and "creature" in o.types]
    for source in sorted(tuple(kernel.on_battlefield()),
                         key=lambda o:o.object_id):
        rule=attachments._rule(source)
        if source.controller!=seat or rule is None or not rule.equip_cost:
            continue
        try:
            if mana_service.plan(seat,rule.equip_cost) is None:
                continue
        except ValueError as e:
            if str(e)!="Bounded mana search exhausted; no action committed":
                raise
            continue
        if source.object_id in attachments.attached:
            live=kernel.objects.get(attachments.attached[source.object_id])
            if live is not None and live.zone=="battlefield":
                continue
        for target in own:
            if not attachments._legal_target(source,target,rule):
                continue
            if rule.death_draw:
                if len(zones.ids(seat,"library"))<rule.death_draw:
                    continue
                # A fragile token becomes card draw. Otherwise the pilot
                # will not throw away a valuable engine for two cards.
                score=(16 if target.token and target.toughness+rule.toughness<=0
                       else 3 if target.token else -8)
            elif "hexproof" in rule.keywords:
                score=(14 if "commander" in target.card.supertypes
                       else 6 if not target.token else 1)
            elif "deathtouch" in rule.keywords:
                score=(9 if target.power>=2 and "deathtouch" not in target.keywords
                       else 1)
            else:
                score=2
            if score>0:
                options.append((score,-target.object_id,
                                source.object_id,target.object_id))
    if not options:
        return None
    choice=max(options)
    return choice[2],choice[3]


def choose_temporary_reanimation(zones,seat,attachments,mana_service,catalog):
    """Conservatively activate reviewed tap-and-reanimate effects.

    Prefer creatures with verified ETB utility or valuable death triggers.
    No graveyard action is created when the physical target is unavailable.
    """
    kernel=zones.kernel
    available=[]
    for source in kernel.on_battlefield():
        rule=attachments._rule(source)
        if (source.controller!=seat or source.tapped or rule is None
                or not rule.recursion_cost):
            continue
        try:
            if mana_service.plan(seat,rule.recursion_cost) is None:
                continue
        except ValueError as error:
            if str(error)!="Bounded mana search exhausted; no action committed":
                raise
            continue
        for oid in zones.ids(seat,"graveyard"):
            target=kernel.get(oid)
            if "creature" not in target.types:
                continue
            raw=catalog.get(target.card.name,{})
            if raw.get("oracle_id")!=target.card.card_id:
                continue
            # This bounded reanimation path gives haste and temporary board
            # presence, but does NOT currently resolve ordinary ETB triggers.
            # Score only the supported combat/body properties; do not award
            # hypothetical value to names or unexecuted printed text.
            if target.power<=0:
                continue
            score=(2*max(0,target.power)+max(0,target.toughness)//2
                   +5*int("lifelink" in target.keywords)
                   +4*int("flying" in target.keywords)
                   +3*int("menace" in target.keywords)
                   +3*int("trample" in target.keywords)
                   +2*int("deathtouch" in target.keywords))
            available.append((score,-oid,source.object_id,oid))
    if not available:
        return None
    best=max(available)
    return best[2],best[3]
