"""V7a/b reusable rules primitives; intentionally NOT a complete MTG rules engine.

No card-name branches in rules. Cards declare characteristics and ability descriptors.
Each GameKernel is independent: no global mutable game state or singleton trigger lists.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from typing import Callable, Iterable
import time

PERMANENT_TYPES=frozenset({'creature','artifact','enchantment','planeswalker','battle','land'})
SPELL_TYPES=frozenset({'instant','sorcery'})
ZONES=frozenset({'library','hand','battlefield','graveyard','exile','command','stack'})
REASONS=frozenset({'destroy','sacrifice','exile','bounce','discard','mill','resolve','state_based','commander_choice','token_cease','blink'})

@dataclass(frozen=True)
class Cost:
    generic:int=0; blue:int=0; red:int=0
    def __post_init__(self):
        if min(self.generic,self.blue,self.red)<0:raise ValueError('Negative mana requirement')
    @property
    def total(self):return self.generic+self.blue+self.red

@dataclass(frozen=True)
class Effect:
    op:str
    args:tuple[tuple[str,object],...]=()
    @staticmethod
    def make(op,**args):return Effect(op,tuple(sorted(args.items())))
    def get(self,key,default=None):return dict(self.args).get(key,default)

@dataclass(frozen=True)
class Ability:
    kind:str             # static / triggered / activated / replacement
    event:str=''         # exact typed event name (for triggered abilities)
    op:str=''            # reusable effect id
    condition:str=''     # registered predicate e.g. controller_cast_instant_sorcery
    amount:str=''        # registered amount provider, e.g. own_creature_tokens
    args:tuple[tuple[str,object],...]=()
    def arg(self,key,default=None):return dict(self.args).get(key,default)

@dataclass(frozen=True)
class CardDefinition:
    card_id:str
    name:str
    types:frozenset[str]
    subtypes:frozenset[str]=frozenset()
    supertypes:frozenset[str]=frozenset()
    cost:Cost=Cost()
    base_power:int=0
    base_toughness:int=0
    keywords:frozenset[str]=frozenset()
    abilities:tuple[Ability,...]=()
    coverage:str='verified_subset'
    def __post_init__(self):
        if not self.card_id or not self.types:raise ValueError('Card needs ID and types')
        if self.coverage not in {'verified_subset','approx','unimplemented'}:raise ValueError('Unknown coverage')

@dataclass
class Modifier:
    power:int=0
    toughness:int=0
    keywords:frozenset[str]=frozenset()
    expires_at:str='never'  # never or end_turn

@dataclass
class GameObject:
    object_id:int
    card:CardDefinition
    owner:int
    controller:int
    zone:str='battlefield'
    token:bool=False
    tapped:bool=False
    damage_marked:int=0
    counters:Counter=field(default_factory=Counter)
    modifiers:list[Modifier]=field(default_factory=list)
    @property
    def types(self):return self.card.types
    @property
    def subtypes(self):return self.card.subtypes
    @property
    def keywords(self):return self.card.keywords.union(*(m.keywords for m in self.modifiers))
    @property
    def power(self):return self.card.base_power+self.counters['+1/+1']-self.counters['-1/-1']+sum(m.power for m in self.modifiers)
    @property
    def toughness(self):return self.card.base_toughness+self.counters['+1/+1']-self.counters['-1/-1']+sum(m.toughness for m in self.modifiers)
    @property
    def is_creature_token(self):return self.token and self.zone=='battlefield' and 'creature' in self.types

@dataclass(frozen=True)
class Event:
    name:str
    controller:int|None=None
    source_id:int|None=None
    target_id:int|None=None
    spell_types:frozenset[str]=frozenset()
    amount:int=0
    metadata:tuple[tuple[str,object],...]=()

@dataclass(frozen=True)
class Move:
    object_id:int              # source zone instance
    old_zone:str
    new_zone:str
    reason:str
    commander_replacement:bool=False
    new_object_id:int|None=None # destination is always a new game object

@dataclass(frozen=True)
class TriggerResult:
    source_id:int
    controller:int
    op:str
    quantity:int=1
    args:tuple[tuple[str,object],...]=()

class SafetyStop(Exception):
    """Fail closed: the game is unresolved, never silently scored as a loss."""
    def __init__(self,reason):super().__init__(reason);self.reason=reason

@dataclass(frozen=True)
class SafetyLimits:
    max_actions_per_turn:int=128
    max_triggers_per_event:int=256
    max_stack_depth:int=64
    max_repeated_states:int=3
    max_total_actions:int=10000
    max_seconds:float=4.0
    max_objects:int=1000

class ExecutionGuard:
    def __init__(self,limits:SafetyLimits|None=None):
        self.limits=limits or SafetyLimits();self.start=time.monotonic()
        self.turn_actions=0;self.total_actions=0;self.repeated=Counter();self.turn=0;self.stop_reason=None
    def new_turn(self,turn:int):
        self.turn=turn;self.turn_actions=0;self.repeated.clear()
    def check(self,signature:tuple|None=None,stack_depth=0):
        self.turn_actions+=1;self.total_actions+=1
        if self.turn_actions>self.limits.max_actions_per_turn:self._stop('action_budget_per_turn')
        if self.total_actions>self.limits.max_total_actions:self._stop('action_budget_per_game')
        if stack_depth>self.limits.max_stack_depth:self._stop('stack_depth_budget')
        if time.monotonic()-self.start>self.limits.max_seconds:self._stop('wall_clock_budget')
        if signature is not None:
            self.repeated[signature]+=1
            if self.repeated[signature]>self.limits.max_repeated_states:self._stop('repeated_game_state')
    def guard_trigger_count(self,n):
        if n>self.limits.max_triggers_per_event:self._stop('trigger_budget')
    def guard_objects(self,n):
        if n>self.limits.max_objects:self._stop('object_budget')
    def _stop(self,why):
        self.stop_reason=why
        raise SafetyStop(why)

class GameKernel:
    """Shared typed object, keyword, cost and event/zone rule implementations.

    Does not use pilot preferences, player names, or special commander identities.
    TriggerResult objects are queued and interpreted by a higher-level table; this
    kernel does not pretend to implement a complete stack/priority system.
    """
    def __init__(self,guard:ExecutionGuard|None=None):
        self.objects:dict[int,GameObject]={}
        self.next_object_id=1
        self.events:list[Event]=[]
        self.moves:list[Move]=[]
        self.guard=guard or ExecutionGuard()
        self.revision=0
        self._cached:dict[tuple,object]={}
        self._special_effects:dict[str,Callable]={}
    def _dirty(self):self.revision+=1;self._cached.clear()
    def add(self,card:CardDefinition,owner:int,controller:int|None=None,zone='battlefield',token=False):
        if zone not in ZONES:raise ValueError('Unknown zone')
        self.guard.guard_objects(len(self.objects)+1)
        obj=GameObject(self.next_object_id,card,owner,owner if controller is None else controller,zone,token)
        self.next_object_id+=1;self.objects[obj.object_id]=obj;self._dirty()
        return obj
    def get(self,oid):return self.objects[oid]
    def on_battlefield(self):return (o for o in self.objects.values() if o.zone=='battlefield')
    def controlled(self,seat,types=frozenset()):
        return [o for o in self.on_battlefield() if o.controller==seat and (not types or o.types & types)]
    def subtypes(self,oid):
        """Derived creature types from declared additive static effects, all zones.

        Printed definitions stay unchanged. Unsupported layer/type-changing
        operations are not inferred from names.
        """
        obj=self.get(oid)
        result=obj.card.subtypes
        if 'creature' not in obj.types:return result
        seat=obj.controller if obj.zone in {'battlefield','stack'} else obj.owner
        for source in self.controlled(seat):
            for ability in source.card.abilities:
                if ability.kind=='static' and ability.op=='add_creature_subtype':
                    result=result|frozenset({ability.arg('subtype')})
        return result
    def tokens(self,seat,creatures_only=False):
        return sum(o.token and (not creatures_only or 'creature' in o.types) for o in self.controlled(seat))
    def add_counter(self,oid,kind,quantity=1):
        if quantity<=0:raise ValueError('Counter increase must be positive')
        self.objects[oid].counters[kind]+=quantity;self._dirty()
    def add_modifier(self,oid,modifier:Modifier):self.objects[oid].modifiers.append(modifier);self._dirty()
    def cleanup(self):
        for o in self.on_battlefield():
            o.damage_marked=0;o.modifiers[:]=[m for m in o.modifiers if m.expires_at!='end_turn']
        self._dirty();self.check_state_based()
    def eligible_target(self,source_controller:int,target_id:int,types:frozenset[str],op:str):
        o=self.objects[target_id]
        if o.zone!='battlefield' or not o.types.intersection(types):return False
        if source_controller!=o.controller and 'hexproof' in o.keywords:return False
        if 'shroud' in o.keywords:return False
        return True
    def legal_target(self,source_controller:int,target_id:int,types:frozenset[str]):
        o=self.objects[target_id]
        return o.zone=='battlefield' and bool(o.types.intersection(types)) and (o.controller==source_controller or 'hexproof' not in o.keywords) and 'shroud' not in o.keywords
    def legal_blockers(self,attacker_id:int,defender:int,used=frozenset()):
        attacker=self.objects[attacker_id]
        def can_block(o):
            if o.tapped or o.object_id in used or 'creature' not in o.types:return False
            if 'flying' in attacker.keywords and not o.keywords.intersection({'flying','reach'}):return False
            if 'unblockable' in attacker.keywords:return False
            return True
        return [o for o in self.controlled(defender,{'creature'}) if can_block(o)]
    def move(self,oid,to_zone:str,reason:str,commander_choice=False):
        if to_zone not in ZONES or reason not in REASONS:raise ValueError('Invalid zone movement')
        obj=self.objects[oid];from_zone=obj.zone
        if from_zone==to_zone:return None
        redirect_commander=bool(commander_choice and 'commander' in obj.card.supertypes and
                                to_zone in {'graveyard','exile'})
        # A zone change creates a new MTG game object. In particular, the old
        # target_id must not follow a bounced/blinked permanent into a new zone.
        del self.objects[oid]
        new_id=None
        if not obj.token:
            target=self.add(obj.card,obj.owner,obj.owner if to_zone!='battlefield' else obj.controller,to_zone)
            new_id=target.object_id
        moved=Move(oid,from_zone,to_zone,reason,False,new_id)
        self.moves.append(moved)
        self.events.append(Event('zone_changed',obj.controller,oid,metadata=(('from',from_zone),('to',to_zone),('reason',reason),('new_id',new_id))))
        if from_zone=='battlefield' and to_zone=='graveyard' and reason in {'destroy','sacrifice','state_based'}:
            self.events.append(Event('dies',obj.controller,oid))
        if obj.token and to_zone!='battlefield':
            self.events.append(Event('token_ceased',obj.controller,oid))
        if redirect_commander:
            # Commander moving through graveyard can still trigger 'dies'.
            redirected=self.move(new_id,'command','commander_choice')
            moved=Move(oid,from_zone,'command',reason,True,redirected.new_object_id)
        self._dirty()
        return moved
    def destroy(self,oid,commander_choice=False):
        obj=self.objects[oid]
        if obj.zone!='battlefield':return None
        if 'indestructible' in obj.keywords:return None
        return self.move(oid,'graveyard','destroy',commander_choice)
    def sacrifice(self,oid,commander_choice=False):return self.move(oid,'graveyard','sacrifice',commander_choice)
    def exile(self,oid,commander_choice=False):return self.move(oid,'exile','exile',commander_choice)
    def bounce(self,oid):return self.move(oid,'hand','bounce')
    def mark_damage(self,oid,amount):
        o=self.objects[oid]
        if o.zone=='battlefield' and amount>0:
            o.damage_marked+=amount;self._dirty()
            self.events.append(Event('damage_creature',target_id=oid,amount=amount))
            self.check_state_based()
    def check_state_based(self):
        for o in list(self.on_battlefield()):
            if 'creature' not in o.types:continue
            if o.toughness<=0:self.move(o.object_id,'graveyard','state_based')
            elif o.damage_marked>=o.toughness and 'indestructible' not in o.keywords:self.move(o.object_id,'graveyard','state_based')
    def modified_cost(self,seat:int,spell_types:frozenset[str],base_cost:Cost,commander_tax=0):
        """Only generic cost reduction: colored requirements always remain."""
        k=(self.revision,seat,tuple(sorted(spell_types)),base_cost,commander_tax)
        if k in self._cached:return self._cached[k]
        reduction=0
        for o in self.controlled(seat):
            for a in o.card.abilities:
                if a.kind!='static' or a.op!='reduce_generic_cost':continue
                if a.condition=='cast_instant_or_sorcery' and not spell_types & SPELL_TYPES:continue
                if a.condition=='cast_noncreature' and 'creature' in spell_types:continue
                if a.amount=='own_creature_tokens':reduction+=self.tokens(seat,True)
                elif a.amount=='constant':reduction+=a.arg('value',0)
                else:raise ValueError('Unknown cost amount rule '+a.amount)
        result=Cost(max(0,base_cost.generic+commander_tax-reduction),base_cost.blue,base_cost.red)
        self._cached[k]=result
        return result
    def triggers(self,event:Event):
        """Return pending abilities; callers queue and resolve them in event order."""
        resolved=[]
        snapshot=list(self.on_battlefield())
        cache_key=('trigger_index',self.revision,event.name)
        if cache_key not in self._cached:
            self._cached[cache_key]=[(o,a) for o in snapshot for a in o.card.abilities
                                     if a.kind=='triggered' and a.event==event.name]
        for o,a in self._cached[cache_key]:
                if not self._matches(o,a,event):continue
                times=1
                if self.subtypes(o.object_id) & {'Wizard','Shaman'}:
                    times+=sum(1 for m in snapshot if m.controller==o.controller for ma in m.card.abilities
                               if ma.kind=='static' and ma.op=='double_wizard_shaman_triggers')
                resolved.append(TriggerResult(o.object_id,o.controller,a.op,times,a.args))
        self.guard.guard_trigger_count(sum(t.quantity for t in resolved))
        return resolved
    @staticmethod
    def _matches(o,a,event):
        if a.condition=='controller_cast_instant_sorcery':return event.controller==o.controller and bool(event.spell_types & SPELL_TYPES)
        if a.condition=='controller_cast_noncreature':return event.controller==o.controller and 'creature' not in event.spell_types
        if a.condition=='controller_cast_or_copy_instant_sorcery':return event.controller==o.controller and bool(event.spell_types & SPELL_TYPES)
        if a.condition=='self_combat_damage_player':return event.source_id==o.object_id and event.amount>0
        if a.condition=='always':return True
        raise ValueError('Unknown trigger predicate '+a.condition)

    def resolve_trigger_results(self,pending:Iterable[TriggerResult],token_catalog:dict[str,CardDefinition],emit_callbacks=()):
        """Simple noninteractive diagnostic resolver, NOT the MTG priority stack.

        No recursive trigger resolution; output is bounded and available to an
        adapter as events instead. Future stack module will own queued triggers.
        """
        result=[]
        for item in pending:
            self.guard.guard_trigger_count(item.quantity)
            args=dict(item.args)
            if item.op=='create_token':
                definition=token_catalog[args['token_id']]
                for _ in range(item.quantity):
                    obj=self.add(definition,item.controller,token=True)
                    result.append(obj)
            else:raise ValueError('Unimplemented reusable effect '+item.op)
        return result

    def register_effect(self,op:str,handler:Callable):
        if not op or op in self._special_effects:raise ValueError('Invalid or duplicate custom effect')
        self._special_effects[op]=handler

    def execute(self,effect:Effect,actor:int,target_id:int|None=None):
        """One typed primitive operation per effect; caller handles priority/stack.

        Unknown effects FAIL rather than becoming a pretend generic spell.
        """
        op=effect.op
        if op in self._special_effects:return self._special_effects[op](self,actor,target_id,effect)
        if op not in {'destroy','exile','bounce','sacrifice','add_counter','grant_keyword','damage_creature'}:
            raise NotImplementedError('Unregistered effect '+op)
        if target_id is None:raise ValueError('Target required')
        obj=self.objects[target_id]
        if op=='sacrifice':
            if obj.controller!=actor:raise ValueError('Cannot sacrifice an opponent permanent')
            return self.sacrifice(target_id)
        if not self.legal_target(actor,target_id,PERMANENT_TYPES):raise ValueError('Illegal target')
        if op=='destroy':return self.destroy(target_id)
        if op=='exile':return self.exile(target_id)
        if op=='bounce':return self.bounce(target_id)
        if op=='add_counter':
            self.add_counter(target_id,effect.get('counter','+1/+1'),effect.get('quantity',1));return obj
        if op=='grant_keyword':
            self.add_modifier(target_id,Modifier(keywords=frozenset({effect.get('keyword')}),expires_at=effect.get('duration','end_turn')));return obj
        if op=='damage_creature':
            self.mark_damage(target_id,effect.get('amount',0));return obj if target_id in self.objects else None

    def damage_players(self,life:dict[int,int],amounts:dict[int,int],source:int|None=None):
        """Apply one simultaneous damage event, report ALL deaths together."""
        snapshot=dict(life)
        for seat,amount in amounts.items():
            if amount<0:raise ValueError('Negative damage')
            if seat not in life:raise ValueError('Unknown player')
            if snapshot[seat]>0:life[seat]-=amount
        eliminated=tuple(sorted(seat for seat in amounts if snapshot[seat]>0 and life[seat]<=0))
        for seat,amount in sorted(amounts.items()):
            if snapshot[seat]>0:self.events.append(Event('damage_player',controller=source,amount=amount,metadata=(('seat',seat),)))
        for seat in eliminated:self.events.append(Event('player_eliminated',controller=seat))
        self._dirty()
        return PlayerDamageResult(tuple(sorted(amounts.items())),eliminated)



@dataclass(frozen=True)
class PlayerDamageResult:
    amounts:tuple[tuple[int,int],...]
    eliminated:tuple[int,...]

# Registry is deliberately per-kernel; adding a special handler to one game does
# not change any other game, or turn common card text into global name tests.

