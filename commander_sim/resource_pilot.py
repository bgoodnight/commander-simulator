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
    if life.total(seat) <= 4:
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
    if loss>=life.total(seat)-4:
        return None
    if recipe.variable_x:
        max_x=min(16,assess_resources(zones.kernel,mana_service,seat).available_fixed_mana)
        for x in range(max_x,2,-1):
            cost=spell_payment_cost(recipe,x)
            if mana_service.plan_spell(seat,cost,source) is not None:
                return cost,x,victims
        return None
    cost=spell_payment_cost(recipe)
    if mana_service.plan_spell(seat,cost,source) is None:
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
    """Conservative pre-combat action choice using only composed rule metadata.

    No opponent battlefield is fabricated. Prefer one affordable, beneficial
    area-damage activation when it can feed a reviewed life-loss-based token
    trigger, without exhausting the mana needed for that later X payment.
    """
    from .composed_abilities import ABILITIES
    if activations_this_turn >= 1 or life.total(seat)<=12:
        return None
    available=assess_resources(zones.kernel,mana_service,seat).available_fixed_mana
    if available<2:
        return None
    commander_engines=[]
    for source in zones.kernel.on_battlefield():
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
    if not commander_engines:
        return None
    for source in sorted(zones.kernel.on_battlefield(),key=lambda o:o.object_id):
        raw=catalog.get(source.card.name,{})
        if source.controller!=seat or raw.get("oracle_id")!=source.card.card_id:
            continue
        for rule in ABILITIES.get(source.card.name,()):
            if (rule.event=="activate" and not rule.payment.x_generic
                    and rule.oracle_excerpt in raw.get("oracle_text","")
                    and any(step.operation=="damage_all" for step in rule.steps)
                    and mana_service.plan(seat,rule.payment.mana) is not None):
                return source.object_id
    return None


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
                              *,hand_cast_reviewed):
    """Select at most one value-positive utility activation at this boundary.

    This is an explicit policy over registered UtilityRule parameters, not
    hard-coded behavior attached to names. Repeated activations are legal in
    the shared executor; a bounded pilot may choose fewer.
    """
    from .reviewed_utility_activations import reviewed_utility
    from .reviewed_sacrifice_actions import SACRIFICE_MODES
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
                or rule.tap and source.tapped):
            continue
        if life.total(seat)<12 and (rule.life or rule.life_by_commander_colors):
            continue
        excluded=(source.object_id,) if rule.tap else ()
        if mana_service.plan(seat,rule.mana,excluded_source_ids=excluded) is None:
            continue
        target=None
        if rule.operation=="creature_to_hand":
            if hand_size>=4:
                continue
            target_choices=[oid for oid in zones.ids(seat,"graveyard")
                if "creature" in zones.kernel.get(oid).types
                and hand_cast_reviewed(zones.kernel.get(oid))]
            if not target_choices:
                continue
            target=max(target_choices,key=lambda oid: (
                catalog.get(zones.kernel.get(oid).card.name,{}).get("cmc",0),-oid))
        elif rule.operation=="self_to_battlefield_tapped":
            has_outlet=any(o.controller==seat and o.zone=="battlefield"
                           and o.card.name in SACRIFICE_MODES
                           for o in zones.kernel.objects.values())
            if not has_outlet:
                continue
        elif rule.operation=="draw":
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
        priority={"creature_to_hand":0,"self_to_battlefield_tapped":1,
                  "draw":2,"drain_opponents":3}[rule.operation]
        sources.append((priority,source.object_id,target))
    if not sources:
        return None
    _,source_id,target=min(sources)
    return source_id,target
