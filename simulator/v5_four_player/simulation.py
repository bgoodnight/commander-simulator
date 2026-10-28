"""Commander table simulation v5: FOUR active seats, abstract synthetic decks.

Shared engine resolves typed actions. No actual printed MTG cards are simulated here.
The detailed-deck port is a *contract*, not a claim that v3 Magnus is integrated.
Standard library only, deterministic seeds. Rules intentionally approximated.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
from pathlib import Path
from typing import Protocol, Callable, Any
import copy, json, random, math

ROOT=Path(__file__).parent
CONF=json.loads((ROOT/'archetypes.json').read_text())
TEM=json.loads((ROOT/'templates.json').read_text())['templates']
ARCHETYPES=tuple(CONF['archetypes'])

# Typed object model: external detailed-deck adapters should produce these types.
@dataclass(frozen=True)
class CardSpec:
    name:str
    kind:str                   # synthetic category or named card ID
    mana_value:int
    card_type:str              # creature / instant / sorcery / artifact / enchantment / land
    effect:str                 # reusable effect ID in shared resolver
    parameters:dict=field(default_factory=dict)
    # A detailed adapter will eventually attach colored mana requirements;
    # the abstract engine currently assumes all mana fungible.
    colored_cost:dict=field(default_factory=dict)

@dataclass
class Creature:
    id:int; controller:int; power:int; toughness:int; entered_round:int; name:str
    tapped:bool=False; token:bool=False; engine:bool=False; keywords:tuple=()

@dataclass
class Permanent:
    id:int; controller:int; kind:str; value:int; entered_round:int; name:str
    is_creature:bool=False; linked_creature:int|None=None

@dataclass
class Action:
    actor:int; source:str; card_type:str; effect:str; cost:int
    target:int|None=None; target_object:int|None=None; parameters:dict=field(default_factory=dict)
    tags:tuple=()                # generic response and targeting tags

class Pilot(Protocol):
    def select_action(self,table:'Table', player:'Player')->Action|None: ...

@dataclass
class Player:
    seat:int; archetype:str; rng_seed:int; library:list[CardSpec]; pilot:Pilot
    life:int=40; hand:list[CardSpec]=field(default_factory=list)
    lands:int=0; mana:int=0; permanents:list[Permanent]=field(default_factory=list)
    creatures:list[Creature]=field(default_factory=list)
    cards_cast:int=0; mana_spent:int=0; counters_used:int=0; removal_used:int=0
    damage_dealt:int=0; damage_taken:int=0; land_misses:int=0
    eliminated_round:int|None=None; mulligans:int=0; finisher_attempts:int=0
    rng:random.Random=field(init=False,repr=False)
    # External detailed-deck agent may override generic mana payment.
    payment_policy:Any=field(default=None,repr=False)
    block_policy:str='trade'  # detailed decks may request 'never'
    def __post_init__(self):self.rng=random.Random(self.rng_seed)
    @property
    def alive(self):return self.life>0
    def draw(self,n=1):
        for _ in range(n):
            if self.library:self.hand.append(self.library.pop())
            else:self.life=0 # simplified lose on draw from empty library
    def ramp(self):return sum(x.value for x in self.permanents if x.kind=='ramp')
    def available_sources(self):return self.lands+self.ramp()
    def engines(self):return sum(x.kind=='engine' for x in self.permanents)
    def combo(self):return sum(x.kind=='combo_piece' for x in self.permanents)
    def clocks(self):return sum(x.kind=='clock' for x in self.permanents)
    def power(self):return sum(c.power for c in self.creatures)
    def public_strength(self):
        # Visible only: hand size known, hand composition unknown.
        return (0.75*self.power()+0.55*len(self.creatures)+2.8*self.engines()+
                2.0*self.combo()+3.0*self.clocks()+0.7*self.available_sources()+
                0.30*len(self.hand)+0.07*self.life)
    def win_proximity(self):
        # Objective diagnostic; never used by target selection.
        finishers=sum(c.kind=='finisher' for c in self.hand)
        return round((self.public_strength()+self.combo()*3.5+
                     (10 if finishers and self.combo()>=3 else 0)+
                     2.5*sum(c.kind=='counter' for c in self.hand)),2)
    def snapshot(self,round_num):
        return dict(round=round_num,life=self.life,lands=self.lands,sources=self.available_sources(),
                    creatures=len(self.creatures),power=self.power(),engines=self.engines(),
                    combo=self.combo(),clocks=self.clocks(),hand=len(self.hand),
                    public_threat=round(self.public_strength(),1),objective_proximity=self.win_proximity(),
                    cards_cast=self.cards_cast,alive=self.alive)

# Consistent generic metadata; card effects are declared in a deck provider,
# not keyed off the controller's name in the shared resolution engine.
KINDS={
 'land':('land','none'), 'ramp':('artifact','ramp'),
 'small':('creature','creature'), 'medium':('creature','creature'),
 'large':('creature','creature'),'tokens':('sorcery','tokens'),
 'engine':('enchantment','engine'), 'draw':('sorcery','draw'),
 'removal':('instant','remove'), 'counter':('instant','counter'),
 'wipe':('sorcery','wipe'), 'combo_piece':('artifact','combo_piece'),
 'finisher':('sorcery','finisher'), 'buff':('sorcery','buff'),
 'burn':('instant','burn')}

def synthetic_library(archetype:str,seed:int)->list[CardSpec]:
    """Real shuffled 99-card category bag with fixed action costs / sizes."""
    if archetype not in ARCHETYPES:raise ValueError(archetype)
    rng=random.Random(seed*1879+19)
    cards=[]
    for kind,count in CONF['archetypes'][archetype].items():
        ctype,effect=KINDS[kind]
        for i in range(count):
            cost=rng.randint(*TEM[kind]['cost'])
            args={}
            for prop in ('power','toughness','count','cards','power_boost','damage'):
                if prop in TEM[kind]:args[prop]=rng.randint(*TEM[kind][prop])
            if kind=='ramp':args['mana_gain']=2 if rng.random()<CONF['ramp_double_chance'].get(archetype,.08) else 1
            if kind=='engine':args['is_creature']=rng.random()<0.35
            if kind=='removal':args['universal']=rng.random()<TEM['removal']['universal_chance']
            if kind=='finisher':
                args['mode']=CONF['finisher_modes'].get(archetype,'damage')
                if args['mode']=='combo_win':args['required_pieces']=CONF['combo_required_pieces']
            cards.append(CardSpec(f'{archetype}:{kind}:{i}',kind,cost,ctype,effect,args))
    assert len(cards)==99
    rng.shuffle(cards)
    return cards

class PriorityPilot:
    """Same pilot interface for every seat. Priorities are archetype configuration."""
    def select_action(self,table,player):
        prefs=CONF['priority'][player.archetype]; viable=[]
        for ix,card in enumerate(player.hand):
            if card.kind in ('land','counter') or card.mana_value>player.mana:continue
            if card.effect=='buff' and not player.creatures:continue
            if card.effect=='remove' and not table.removal_targets(player,card):continue
            if card.effect=='wipe' and not table.wipe_worth(player):continue
            if card.effect=='finisher':
                mode=card.parameters.get('mode')
                if mode=='combo_win' and (player.combo()<card.parameters.get('required_pieces',3) or
                                           player.available_sources()<CONF['combo_min_sources']):continue
                if mode=='spell_burst' and player.engines()<1:continue
                if mode=='overrun' and player.power()<8:continue
                if mode=='inevitability' and player.engines()<1:continue
            score=100-(prefs.index(card.kind)*5 if card.kind in prefs else 95)
            if card.kind=='ramp' and table.round_num>=9:score-=45
            if card.kind=='draw' and len(player.hand)<=3:score+=15
            if card.kind=='small' and table.round_num>=7:score-=14
            if card.kind=='large' and table.round_num<=3:score-=15
            if card.kind=='burn':
                if not table.find_burn_target(player,card):continue
                score+=4 if table.min_enemy_life(player)<14 else -20
            if card.kind in ('removal','wipe'):score+=table.interaction_urgency(player,card)
            # Control and combo retain counters for plausible opponents unless
            # playing an important resource piece; no artificial 'defense token'.
            reserve=CONF['reserve_counter_mana'][player.archetype]
            if player.hand and any(c.kind=='counter' for c in player.hand) and player.mana-card.mana_value<reserve and card.kind not in ('ramp','draw','engine'):
                score-=19
            viable.append((score,-card.mana_value,-ix,card))
        if not viable:return None
        _,_,_,chosen=max(viable,key=lambda x:x[:3]);return table.build_action(player,chosen)

class Table:
    def __init__(self,archetypes:list[str],seed:int=1,interactive:bool=True,
                 trace:bool=False,players:list[Player]|None=None):
        if len(archetypes)!=4:raise ValueError('Four active seats required')
        self.seed=seed;self.rng=random.Random(seed*17317+17)
        self.round_num=0;self.interactive=interactive;self.trace=trace
        self.events:list[str]=[];self.counts=Counter();self.eliminations=[]
        self.target_stats=Counter();self.exposures=Counter();self.turns=[]
        self.winner:int|None=None;self.win_reason='';self.end_round:int|None=None
        if players is not None:
            if len(players)!=4 or sorted(p.seat for p in players)!=list(range(4)):
                raise ValueError('Injected players must occupy four unique seats 0-3')
            self.players=players
        else:
            self.players=[self.new_player(i,a) for i,a in enumerate(archetypes)]
        self.pilot_override=None
        self.effect_handlers:dict[str,Callable]= {}
        self.event_listeners:list[Callable]=[]
        self.response_hooks:list[Callable]=[]
    @classmethod
    def with_players(cls,players:list[Player],seed:int=1,interactive:bool=True,trace:bool=False):
        """Inject any four agents (including detailed real-deck agents)."""
        return cls([p.archetype for p in players],seed,interactive,trace,players=players)
    def new_player(self,seat,archetype):
        player=Player(seat,archetype,self.seed*109+seat*431+3,
                      synthetic_library(archetype,self.seed*67+seat*17+23),PriorityPilot())
        player.draw(7)
        if sum(c.kind=='land' for c in player.hand)<2 or sum(c.kind=='land' for c in player.hand)>5:
            player.library=synthetic_library(archetype,self.seed*67+seat*17+23)
            player.hand=[];player.draw(7);player.mulligans=1
        return player
    def note(self,s):
        if self.trace:self.events.append(s)
    def register_effect(self,name:str,handler:Callable):
        """Extend resolution without editing the base game engine."""
        self.effect_handlers[name]=handler
    def add_response_hook(self,hook:Callable):
        """Hook(table, action) -> True (countered), False (not countered), None (defer)."""
        self.response_hooks.append(hook)
    def on_event(self,listener:Callable):
        """Listener receives (table,event_name,action,payload)."""
        self.event_listeners.append(listener)
    def emit(self,name,action=None,**payload):
        for listener in tuple(self.event_listeners):listener(self,name,action,payload)
    def alive(self):return [p for p in self.players if p.alive]
    def rivals(self,p):return [q for q in self.players if q.alive and q.seat!=p.seat]
    def min_enemy_life(self,p):return min((q.life for q in self.rivals(p)),default=40)
    def rankings(self):
        ranked=sorted(self.alive(),key=lambda x:(x.public_strength(),-x.seat),reverse=True)
        return {p.seat:i+1 for i,p in enumerate(ranked)}
    def choose_target(self,actor,kind='attack'):
        rivals=self.rivals(actor)
        if not rivals:return None
        ranks=self.rankings();weights=[]
        for q in rivals:
            rank=ranks[q.seat];self.exposures[(kind,rank)]+=1
            blockers=sum(not c.tapped for c in q.creatures)
            lead=(len(self.alive())-rank)
            vulnerability=0.65 if blockers==0 else -0.10*min(6,blockers)
            lowlife=max(-0.5,min(1.4,(20-q.life)/15))
            if kind=='attack':utility=0.56*lead+0.70*vulnerability+0.5*lowlife
            else:utility=0.78*lead+0.27*lowlife
            weights.append(math.exp((utility+self.rng.uniform(-0.1,0.1))/1.45))
        chosen=self.rng.choices(rivals,weights=weights,k=1)[0]
        self.target_stats[(kind,ranks[chosen.seat])]+=1
        return chosen
    def next_id(self):
        self._id=getattr(self,'_id',0)+1;return self._id
    def add_creature(self,p,power,toughness,name,token=False,engine=False,keywords=()):
        c=Creature(self.next_id(),p.seat,max(0,power),max(1,toughness),self.round_num,
                   name,False,token,engine,tuple(keywords))
        p.creatures.append(c)
        self.emit('creature_entered',None,controller=p.seat,creature_id=c.id,source=name,token=token)
        return c
    def add_permanent(self,p,kind,value,name,is_creature=False):
        perm=Permanent(self.next_id(),p.seat,kind,value,self.round_num,name,is_creature)
        p.permanents.append(perm)
        if is_creature:
            creature=self.add_creature(p,2,3,name,engine=(kind=='engine'))
            perm.linked_creature=creature.id
        return perm
    def kill_creature(self,p,creature):
        if creature not in p.creatures:return
        p.creatures.remove(creature);self.counts['creature_deaths']+=1
        self.emit('creature_died',None,controller=p.seat,creature_id=creature.id,source=creature.name)
        p.permanents=[x for x in p.permanents if x.linked_creature!=creature.id]
    def remove_permanent(self,p,perm):
        if perm not in p.permanents:return
        p.permanents.remove(perm)
        for c in list(p.creatures):
            if c.id==perm.linked_creature:self.kill_creature(p,c)
    def damage(self,p,n,source=None,cause='damage'):
        if not p.alive:return
        amount=max(0,n)
        p.life-=amount;p.damage_taken+=amount
        if source:source.damage_dealt+=amount
        self.emit('damage',None,source=(source.seat if source else None),target=p.seat,amount=amount,cause=cause)
        if p.life<=0:self.eliminate(p,cause)
    def eliminate(self,p,cause):
        if p.eliminated_round is not None:return
        p.eliminated_round=self.round_num;self.eliminations.append({'round':self.round_num,'seat':p.seat,'archetype':p.archetype,'cause':cause})
        p.creatures=[];p.permanents=[];p.hand=[];p.mana=0
        self.emit('elimination',None,seat=p.seat,cause=cause)
        self.counts['eliminated']+=1
        self.note(f'    ELIMINATED P{p.seat} ({p.archetype}) round {self.round_num}: {cause}.')
    def remove_players_together(self,targets:list[Player],cause,actor=None):
        # All affected players lose simultaneously, before follow-up priority.
        for q in targets:
            if q.alive:q.life=0
        for q in targets:
            if q.eliminated_round is None:self.eliminate(q,cause)
        if len(targets)>=2:self.counts['multi_elimination_events']+=1
    def removal_targets(self,p,card):
        out=[];universal=card.parameters.get('universal',False)
        for q in self.rivals(p):
            out += [(q,c) for c in q.creatures]
            if universal:out += [(q,x) for x in q.permanents]
        return out
    def select_removal(self,p,card):
        targets=self.removal_targets(p,card)
        if not targets:return None
        ranks=self.rankings();weights=[]
        for q,per in targets:
            val=(per.power+0.35*per.toughness+3*per.engine if isinstance(per,Creature)
                 else per.value*2+3*(per.kind in ('combo_piece','clock','engine')))
            weights.append(math.exp(min(11,val+0.5*(len(self.alive())-ranks[q.seat]))/3))
        return self.rng.choices(targets,weights=weights,k=1)[0]
    def wipe_worth(self,p):
        enemies=self.rivals(p)
        return sum(len(q.creatures) for q in enemies)>=4 and sum(q.power() for q in enemies)>=max(15,1.65*p.power()+4)
    def interaction_urgency(self,p,card):
        if card.kind=='wipe':return 18 if self.wipe_worth(p) else -100
        candidates=self.removal_targets(p,card)
        if not candidates:return -100
        return 15 if any((c.power>=6 or c.engine) if isinstance(c,Creature) else c.kind=='clock' for _,c in candidates) else -11
    def find_burn_target(self,p,card):
        rivals=self.rivals(p)
        if not rivals:return None
        # Target low-health opponent when elimination feasible, otherwise table leader.
        lethal=[q for q in rivals if q.life<=card.parameters.get('damage',4)]
        if lethal:return min(lethal,key=lambda q:q.life)
        return self.choose_target(p,'burn')
    def build_action(self,p,card:CardSpec)->Action:
        action=Action(p.seat,card.name,card.card_type,card.effect,card.mana_value,parameters=dict(card.parameters))
        if card.effect=='remove':
            target=self.select_removal(p,card)
            if target:action.target=target[0].seat;action.target_object=target[1].id
        elif card.effect=='burn':
            target=self.find_burn_target(p,card)
            if target:action.target=target.seat
        elif card.effect=='finisher':
            mode=card.parameters.get('mode','damage')
            if mode=='damage':
                target=self.choose_target(p,'burn')
                if target:action.target=target.seat
        return action
    def respond(self,action:Action)->bool:
        """Small shared spell window: one counter, optional counter-counter by caster.

        Not a full MTG stack. Applicable to creature/permanent/noncreature spells.
        Counterspell cards are consumed and cost paid by the responder.
        """
        if not self.interactive:return False
        for hook in self.response_hooks:
            outcome=hook(self,action)
            if outcome is not None:return bool(outcome)
        actor=self.players[action.actor]
        if action.effect=='counter':return False
        options=[]
        for q in self.alive():
            if q.seat==actor.seat or q.mana<2:continue
            counter=next((c for c in q.hand if c.effect=='counter' and c.mana_value<=q.mana and
                          action.card_type in c.parameters.get('can_counter_types',('creature','instant','sorcery','artifact','enchantment','planeswalker'))),None)
            if counter is None:continue
            directly=q.seat==action.target
            severity={'finisher':9,'wipe':8,'combo_piece':5,'engine':4,'remove':4,'creature':3,'tokens':4,'buff':3}.get(action.effect,2)
            if action.effect=='wipe':directly=bool(q.creatures)
            if action.effect=='finisher':directly=True
            rank=self.rankings().get(actor.seat,4)
            desire=(0.24+(0.37 if directly else 0.0)+(0.17 if severity>=8 else 0.0)+
                    (0.08 if rank==1 else 0.0)+CONF['counter_response_bonus'].get(q.archetype,0.0))
            options.append((desire+self.rng.random()*0.25,q,counter))
        if not options:return False
        desire,q,counter=max(options,key=lambda z:z[0])
        if self.rng.random()>min(.94,desire):return False
        q.hand.remove(counter);q.mana-=counter.mana_value;q.mana_spent+=counter.mana_value
        q.cards_cast+=1;q.counters_used+=1;self.counts['counters_cast']+=1
        self.note(f'    P{q.seat} counters {action.source} (cost {counter.mana_value}).')
        # One counter-counter at most; actor's counter responds to the defensive counter.
        return_counter=next((c for c in actor.hand if c.effect=='counter' and c.mana_value<=actor.mana and
                             'instant' in c.parameters.get('can_counter_types',('creature','instant','sorcery','artifact','enchantment','planeswalker'))),None)
        if return_counter and (action.effect=='finisher' or actor.rng.random()<0.38):
            actor.hand.remove(return_counter);actor.mana-=return_counter.mana_value
            actor.mana_spent+=return_counter.mana_value;actor.cards_cast+=1;actor.counters_used+=1
            self.counts['counter_counters']+=1
            self.note(f'    P{actor.seat} counter-counters; original spell resolves.')
            return False
        self.counts['spells_countered']+=1
        return True
    def apply(self,action:Action):
        """Typed effect resolver. Detailed decks can dispatch additional effect handlers here."""
        p=self.players[action.actor];a=action.parameters;eff=action.effect
        self.counts['resolved_'+eff]+=1
        if eff in self.effect_handlers:
            self.effect_handlers[eff](self,action)
            return
        if eff=='ramp':self.add_permanent(p,'ramp',a.get('mana_gain',1),action.source)
        elif eff=='creature':self.add_creature(p,a.get('power',2),a.get('toughness',2),action.source)
        elif eff=='tokens':
            for _ in range(a.get('count',2)):self.add_creature(p,a.get('power',1),a.get('power',1),'Token',token=True)
        elif eff=='engine':self.add_permanent(p,'engine',3,action.source,a.get('is_creature',False))
        elif eff=='draw':
            p.draw(a.get('cards',2))
            if not p.alive:self.eliminate(p,'empty_library')
        elif eff=='combo_piece':self.add_permanent(p,'combo_piece',4,action.source)
        elif eff=='remove':
            if action.target is not None and action.target_object is not None:
                q=self.players[action.target]
                if q.alive:
                    c=next((c for c in q.creatures if c.id==action.target_object),None)
                    per=next((x for x in q.permanents if x.id==action.target_object),None)
                    if c:self.kill_creature(q,c)
                    elif per:self.remove_permanent(q,per)
                    if c or per:p.removal_used+=1;self.counts['removals_resolved']+=1
        elif eff=='wipe':
            n=sum(len(q.creatures) for q in self.alive())
            for q in self.alive():
                for c in list(q.creatures):self.kill_creature(q,c)
            self.counts['wipes_resolved']+=1
            self.note(f'    Board wipe removes {n} creatures.')
        elif eff=='buff':
            bonus=a.get('power_boost',1)
            for c in p.creatures:c.power+=bonus
        elif eff=='burn':
            if action.target is not None:
                q=self.players[action.target];self.damage(q,a.get('damage',4),p,'burn')
        elif eff=='finisher':self.finish(p,a,action)
        elif eff=='counter':pass
        else:raise ValueError(f'Unknown effect {eff!r} from {action.source}')
    def finish(self,p,a,action):
        mode=a.get('mode','damage');p.finisher_attempts+=1;self.counts['finishers_resolved']+=1
        if mode=='combo_win' and p.combo()>=a.get('required_pieces',3):
            opponents=self.rivals(p)
            self.note(f'    P{p.seat} executes abstract COMBO FINISHER: eliminates {len(opponents)} opponents.')
            self.remove_players_together(opponents,'resolved_combo',p)
        elif mode=='spell_burst':
            # Damage from one spell resolves simultaneously; cap engine scaling.
            amount=a.get('damage',8)+min(14,3*p.engines()+p.combo()*2)
            opponents=self.rivals(p);self.note(f'    P{p.seat} spell burst: {amount} to EACH opponent.')
            # One mass-damage resolution: determine all deaths before removing any player.
            hit=[]
            for q in opponents:
                q.life-=amount;q.damage_taken+=amount;p.damage_dealt+=amount
                if q.life<=0:hit.append(q)
            if hit:self.remove_players_together(hit,'spell_burst',p)
            self.counts['spell_bursts']+=1
        elif mode=='inevitability':
            self.add_permanent(p,'clock',5,action.source)
            self.note(f'    P{p.seat} establishes persistent 5-damage/turn finisher.')
        elif mode=='overrun':
            bonus=2+min(3,p.engines())
            for c in p.creatures:c.power+=bonus
            self.note(f'    P{p.seat} overrun grants +{bonus} power permanently (simplified).')
        elif mode=='damage':
            target=self.players[action.target] if action.target is not None else self.choose_target(p,'burn')
            if target:self.damage(target,a.get('damage',10),p,'finisher_damage')
        else:raise ValueError(f'Unknown finisher mode {mode}')
    def cast(self,action:Action):
        p=self.players[action.actor]
        if not p.alive or p.mana<action.cost:return False
        if p.payment_policy and not p.payment_policy.can_pay(p,action):return False
        card=next((c for c in p.hand if c.name==action.source),None)
        if not card:return False
        p.hand.remove(card)
        if p.payment_policy:p.payment_policy.pay(p,action)
        else:p.mana-=action.cost
        p.mana_spent+=action.cost;p.cards_cast+=1
        self.counts['casts']+=1
        self.note(f'  P{p.seat} ({p.archetype}) casts {card.kind} {card.card_type} [{action.effect}] cost {action.cost}, mana left {p.mana}.')
        self.emit('spell_cast',action)
        if self.respond(action):
            self.emit('spell_countered',action)
            return True
        self.apply(action)
        self.emit('spell_resolved',action)
        if not p.alive:self.eliminate(p,'empty_library')
        return True
    def upkeep(self,p,t):
        self.emit('turn_start',None,controller=p.seat,round=t)
        p.mana=p.available_sources()
        for c in p.creatures:c.tapped=False
        p.draw(1)
        if not p.alive:self.eliminate(p,'empty_library');return
        for perm in list(p.permanents):
            if perm.kind=='engine' and perm.entered_round<t:
                if p.rng.random()<TEM['engine']['extra_draw_chance']:
                    p.draw(1);self.counts['bonus_draws']+=1
                if p.rng.random()<TEM['engine']['token_chance']:
                    self.add_creature(p,1,1,'engine token',token=True)
        if not p.alive:self.eliminate(p,'empty_library');return
        for perm in list(p.permanents):
            if perm.kind=='clock' and perm.entered_round<t and self.rivals(p):
                target=self.choose_target(p,'clock');self.damage(target,perm.value,p,'persistent_finisher')
        if not p.alive:return
        land=next((c for c in p.hand if c.kind=='land'),None)
        if land:
            p.hand.remove(land);p.lands+=1
            self.emit('land_played',None,controller=p.seat,round=t)
            self.note(f'  P{p.seat} land -> {p.lands} lands.')
        else:p.land_misses+=1
        p.mana=p.available_sources()
    def main(self,p):
        for _ in range(12):
            if not p.alive or len(self.alive())<=1:return
            action=p.pilot.select_action(self,p)
            if action is None:break
            if not self.cast(action):break
        # Cleanup excess cards, ditch lower-priority synthetic cards.
        if len(p.hand)>7:
            priority=CONF['priority'].get(p.archetype,[])
            ordered=sorted(p.hand,key=lambda c:(c.kind=='land' and p.lands<5, -(priority.index(c.kind) if c.kind in priority else 99)),reverse=True)
            p.hand=ordered[:7]
    def block(self,defender,attacker_creature,used:set[int]):
        if defender.block_policy=='never':return None
        legal=[c for c in defender.creatures if c.id not in used and not c.tapped]
        choices=[]
        for c in legal:
            kill=c.power>=attacker_creature.toughness
            survive=c.toughness>attacker_creature.power
            urgency=(defender.life<=attacker_creature.power+5)
            if kill and (survive or urgency or c.power<=attacker_creature.power+1):
                choices.append((4*survive+2*kill-0.1*c.power,c))
            elif urgency and c.toughness>attacker_creature.power:
                choices.append((1.4-0.1*c.power,c))
        return max(choices,key=lambda t:t[0])[1] if choices else None
    def combat(self,p):
        if not self.interactive:return
        eligible=[c for c in list(p.creatures) if c.entered_round<self.round_num and not c.tapped]
        used_blockers={q.seat:set() for q in self.alive()}
        for creature in eligible:
            if creature not in p.creatures or not p.alive or len(self.alive())<=1:continue
            if p.rng.random()>=CONF['attack_rate'].get(p.archetype,0.65):continue
            target=self.choose_target(p,'attack')
            if target is None:continue
            self.emit('combat_attack',None,attacker=p.seat,defender=target.seat,creature_id=creature.id)
            creature.tapped=True
            blocker=self.block(target,creature,used_blockers[target.seat])
            if blocker:
                self.note(f'    COMBAT: P{p.seat} {creature.power}/{creature.toughness} attacks P{target.seat}; P{target.seat} blocks with {blocker.power}/{blocker.toughness}.')
                used_blockers[target.seat].add(blocker.id)
                dies_a=blocker.power>=creature.toughness
                dies_b=creature.power>=blocker.toughness
                if dies_a:self.kill_creature(p,creature)
                if dies_b:self.kill_creature(target,blocker)
                self.counts['blocks']+=1
            else:
                self.note(f'    COMBAT: P{p.seat} attacks P{target.seat} unblocked for {creature.power}; before={target.life} life.')
                self.damage(target,creature.power,p,'combat')
            self.counts['attackers']+=1
    def end_check(self):
        alive=self.alive()
        if len(alive)<=1:
            if alive:self.winner=alive[0].seat
            self.end_round=self.round_num
            self.win_reason=self.eliminations[-1]['cause'] if self.eliminations else 'unknown'
            return True
        return False
    def run(self,max_rounds=30):
        # Randomized seat order makes symmetric mirrors a useful fairness test.
        order=list(range(4));self.rng.shuffle(order);self.turn_order=order
        for turn in range(1,max_rounds+1):
            self.round_num=turn
            self.note(f'\n========== ROUND {turn} ==========')
            for seat in order:
                p=self.players[seat]
                if not p.alive:continue
                self.upkeep(p,turn)
                if p.alive:
                    self.main(p)
                    self.combat(p)
                if self.end_check():break
            self.turns.append({'round':turn,'players':[p.snapshot(turn) for p in self.players],
                               'rankings':self.rankings()})
            if self.trace:
                top=sorted(self.alive(),key=lambda x:x.public_strength(),reverse=True)
                self.note('  End round: '+', '.join(f'P{q.seat} {q.archetype} life={q.life} power={q.power()} mana={q.available_sources()} threat={q.public_strength():.1f}' for q in top))
            if self.end_round is not None:break
        if self.end_round is None:self.win_reason='turn_limit'
        return self
    def summary(self):
        return {'seed':self.seed,'archetypes':[p.archetype for p in self.players],
                'winner':self.winner,'winner_archetype':(self.players[self.winner].archetype if self.winner is not None else None),
                'ending_round':self.end_round,'outcome':self.win_reason,'rounds_played':self.round_num,
                'eliminations':self.eliminations,'metrics':dict(self.counts),
                'players':[{'seat':p.seat,'type':p.archetype,'life':p.life,'mulligans':p.mulligans,
                            'casts':p.cards_cast,'sources':p.available_sources(),
                            'damage_dealt':p.damage_dealt,'removal':p.removal_used,'counters':p.counters_used,
                            'finisher_attempts':p.finisher_attempts} for p in self.players]}

def sample_matchup(seed:int):
    rng=random.Random(seed*4049+101)
    return [rng.choice(ARCHETYPES) for _ in range(4)]
