"""Synthetic four-seat MTG threat model (v4 prototype, not a rules engine).

All enemy decks are 99-card archetype-weighted category bags. There are no
actual opposing card rules or hidden stat bonuses for a 'good' opening. Luck
comes from the shuffle, a simple free mulligan, and drawn/played card categories.

This module deliberately does not modify the v3 Magnus card engine. Its
state/action/response adapter is documented in README.md for a future join.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter
import json, random, math

ROOT=Path(__file__).parent
PROFILES=json.loads((ROOT/'profiles.json').read_text())
TEMPLATES=json.loads((ROOT/'templates.json').read_text())['templates']
ARCHETYPES=tuple(PROFILES['archetypes'])

@dataclass(frozen=True)
class AbstractCard:
    kind:str
    cost:int

@dataclass
class Creature:
    id:int
    power:int
    toughness:int
    born:int
    name:str
    tapped:bool=False
    is_token:bool=False
    linked_permanent:int|None=None

@dataclass
class Permanent:
    id:int
    kind:str  # engine, combo_piece, buff
    value:float
    is_creature:bool=False
    born:int=0

@dataclass
class Player:
    seat:int
    arch:str
    seed:int
    passive:bool=False
    life:int=40
    lands:int=0
    ramp:int=0
    hand:list[AbstractCard]=field(default_factory=list)
    deck:list[AbstractCard]=field(default_factory=list)
    creatures:list[Creature]=field(default_factory=list)
    permanents:list[Permanent]=field(default_factory=list)
    mana:int=0
    total_spent:int=0
    threats_answered:int=0
    cards_cast:int=0
    creatures_lost:int=0
    removal_cast:int=0
    counters_cast:int=0
    attack_damage_dealt:int=0
    damage_taken:int=0
    first_win_attempt:int|None=None
    spells_caught:int=0
    mana_misses:int=0
    log:list[str]=field(default_factory=list)
    stats:list[dict]=field(default_factory=list)
    rng:random.Random=field(init=False,repr=False)
    next_id:int=0
    def __post_init__(self):
        self.rng=random.Random(self.seed*104729+1009)
        if self.passive:return
        self.deck=[AbstractCard(k,self.rng.randint(*TEMPLATES[k]['cost'])) for k,n in PROFILES['archetypes'][self.arch].items() for _ in range(n)]
        assert len(self.deck)==99
        self.rng.shuffle(self.deck)
        self.draw(7)
        land_ct=sum(c.kind=='land' for c in self.hand)
        if land_ct<2 or land_ct>5:
            self.deck=[AbstractCard(k,self.rng.randint(*TEMPLATES[k]['cost'])) for k,n in PROFILES['archetypes'][self.arch].items() for _ in range(n)]
            self.rng.shuffle(self.deck)
            self.hand=[];self.draw(7)  # deliberately simple free redraw
    def draw(self,n:int):
        for _ in range(n):
            if self.deck:self.hand.append(self.deck.pop())
    def new_id(self):self.next_id+=1;return self.next_id
    def has_kind(self,kind):return any(c.kind==kind for c in self.hand)
    def pop_kind(self,kind):
        for i,c in enumerate(self.hand):
            if c.kind==kind:return self.hand.pop(i)
        return None
    @property
    def alive(self):return self.life>0
    def active_mana(self):return self.lands+self.ramp
    def engine_n(self):return sum(x.kind=='engine' for x in self.permanents)
    def combo_n(self):return sum(x.kind=='combo_piece' for x in self.permanents)
    def buff_n(self):return sum(x.kind=='buff' for x in self.permanents)
    def power(self):return sum(c.power for c in self.creatures)
    def board_strength(self):return self.power()*0.85+len(self.creatures)*0.5+sum(x.value for x in self.permanents)
    def threat(self):
        # Absolute, intentionally interpretable proxy. Target decisions USE ordinal rank.
        return round(self.board_strength()+0.85*self.active_mana()+0.26*len(self.hand)+0.06*self.life+2.0*self.combo_n(),2)
    def snapshot(self,turn:int):
        return {'turn':turn,'life':self.life,'lands':self.lands,'mana_sources':self.active_mana(),
                'hand':len(self.hand),'creatures':len(self.creatures),'board_power':self.power(),
                'engine_count':self.engine_n(),'combo_pieces':self.combo_n(),
                'board_strength':round(self.board_strength(),2),'threat':self.threat(),
                'total_cast':self.cards_cast,'total_spent':self.total_spent,'mana_misses':self.mana_misses}

class Table:
    def __init__(self,archetypes:list[str],seed:int=1,interaction:bool=True,passive_magnus:bool=True,trace:bool=False):
        if len(archetypes)!=3 and passive_magnus:raise ValueError('Expected exactly three opponents')
        if any(a not in ARCHETYPES for a in archetypes):raise ValueError('Invalid archetype')
        self.seed=seed;self.rng=random.Random(seed*17011+53)
        self.interaction=interaction;self.trace=trace;self.events=[];self.turn=0
        self.players=[]
        if passive_magnus:self.players.append(Player(0,'magnus_passive',seed+1,passive=True))
        for i,a in enumerate(archetypes):self.players.append(Player(i+int(passive_magnus),a,seed*17+i*67+10))
        self.counts=Counter();self.target_counts=Counter();self.rank_target_counts=Counter();self.rank_exposures=Counter();self.rank_events=[]
    def say(self,s):
        if self.trace:self.events.append(s)
    def other_players(self,p):return [q for q in self.players if q.seat!=p.seat and q.alive]
    def random_param(self,category,key,p):
        a,b=TEMPLATES[category][key];return p.rng.randint(a,b)
    def ranks(self):
        active=[p for p in self.players if p.alive]
        sorted_players=sorted(active,key=lambda p:(p.threat(),p.seat),reverse=True)
        return {p.seat:i+1 for i,p in enumerate(sorted_players)}
    def choose_target(self,p,kind='attack'):
        targets=self.other_players(p)
        if not targets:return None
        rank=self.ranks();weights=[]
        for q in targets:
            self.rank_exposures[(kind,rank[q.seat])]+=1
            blockers=sum(1 for c in q.creatures if not c.tapped)
            # 1 is the highest public threat rank. Vulnerability influences attacks
            # but threat ranking dominates. A low-life player is an elimination opportunity.
            lead=4-rank[q.seat]
            openness=1 if blockers==0 else 0 if blockers<3 else -0.35
            ease=max(-1.0,min(1.1,(25-q.life)/20))
            if kind=='attack':utility=0.8*lead+0.6*openness+0.45*ease
            else:utility=1.0*lead+0.12*ease
            utility+=self.rng.uniform(-0.2,0.2)
            weights.append(math.exp(utility/1.45))
        selected=self.rng.choices(targets,weights=weights,k=1)[0]
        self.rank_target_counts[(kind,rank[selected.seat])]+=1
        return selected
    def available_responses(self,target:Player|None,attacker:Player,severity:float,category:str)->list[Player]:
        if not self.interaction:return []
        interested=[p for p in self.players if p.alive and not p.passive and p.seat!=attacker.seat and p.mana>=2 and p.has_kind('counter')]
        if target is not None:
            interested.sort(key=lambda p:(p.seat!=target.seat,-p.threat()))
        else:interested.sort(key=lambda p:-p.threat())
        return interested
    def counter_attempt(self,actor:Player,target:Player|None,category:str,severity:float)->bool:
        if not self.interaction:return False
        for defender in self.available_responses(target,actor,severity,category):
            directly=target is not None and target.seat==defender.seat
            if category=='wipe':directly=bool(defender.creatures)
            lead=self.ranks().get(actor.seat,4)
            chance=(0.80 if directly and severity>3 else 0.48 if directly else 0.11)
            if category in ('finisher','wipe'):chance+=0.20
            if lead==1:chance+=0.15
            if defender.arch=='control':chance+=0.08
            if defender.rng.random()<min(chance,0.96):
                defender.pop_kind('counter');defender.mana-=2;defender.cards_cast+=1;defender.counters_cast+=1
                defender.total_spent+=2;defender.threats_answered+=1
                self.counts['counters_used']+=1
                self.say(f'    RESPONSE: P{defender.seat} ({defender.arch}) counters P{actor.seat}\'s {category} ({category} threat severity {severity:.1f}); 2 mana spent.')
                return True
        return False
    def begin(self,p:Player,t:int):
        if not p.alive or p.passive:return
        # Abstract land cards must actually be drawn; missed land drops compound.
        p.draw(1)
        for _ in range(min(2,p.engine_n())):
            if p.rng.random()<TEMPLATES['engine']['extra_draw_chance']:
                p.draw(1);self.counts['engine_extra_draws']+=1
        if p.has_kind('land'):
            p.pop_kind('land');p.lands+=1;self.say(f'  P{p.seat} ({p.arch}) land drop; lands={p.lands}.')
        else:
            p.mana_misses+=1;self.counts['land_misses']+=1
            self.say(f'  P{p.seat} ({p.arch}) MISSED land drop; lands={p.lands}.')
        for c in p.creatures:c.tapped=False
        p.mana=p.active_mana()
        # Token/engine snowball: established engines make additional output
        # after turns have passed, never on the exact turn they enter.
        for perm in list(p.permanents):
            if perm.kind=='engine' and perm.born<t and p.rng.random()<TEMPLATES['engine']['token_chance']:
                self.create_creature(p,t,1,1,'engine token',is_token=True)
                self.say(f'  P{p.seat} engine generated 1/1 token.')
    def create_creature(self,p,t,power,toughness,name,is_token=False,linked_permanent=None):
        p.creatures.append(Creature(p.new_id(),power,toughness,t,name,is_token=is_token,linked_permanent=linked_permanent))
    def destroy_creature(self,p,c):
        if c not in p.creatures:return
        p.creatures.remove(c);p.creatures_lost+=1
        if c.linked_permanent is not None:
            p.permanents=[x for x in p.permanents if x.id!=c.linked_permanent]
    def set_cost(self,kind,p):return self.random_param(kind,'cost',p)
    def candidate(self,p:Player,t:int):
        # Priorities in one config file; opportunistic choices from actually drawn hand.
        priorities=PROFILES['priority'][p.arch]
        ranked=[]
        for i,card in enumerate(p.hand):
            kind=card.kind
            if kind in ('land','counter'):continue
            cost=card.cost
            if cost>p.mana:continue
            if kind=='finisher' and p.arch=='combo' and p.combo_n()<2:continue
            if kind=='buff' and not p.creatures:continue
            if kind in ('removal','wipe') and not self.interaction:continue
            if kind=='removal' and not self.removal_targets(p):continue
            if kind=='wipe' and not self.wipe_worth_it(p):continue
            # Play drawn spells even with counters in hand when meaningful.
            pri=priorities.index(kind) if kind in priorities else 99
            if kind=='large' and t<=3:pri+=6
            if kind=='small' and t>=7:pri+=3
            if kind=='draw' and len(p.hand)<=2:pri=max(0,pri-3)
            if kind=='ramp' and t>=8:pri+=5
            # Reserve mana for known counterspell if likely opponent threat.
            if kind not in ('ramp','engine','draw') and p.has_kind('counter') and p.arch in ('control','combo','spellslinger'):
                reserve=PROFILES['reserve_counter_mana'][p.arch]
                if t>=3 and p.mana-cost<reserve:pri+=4
            ranked.append((pri,cost,i,card))
        return min(ranked) if ranked else None
    def removal_targets(self,p):
        return [q for q in self.other_players(p) if q.creatures or q.permanents]
    def wipe_worth_it(self,p):
        foes=self.other_players(p)
        opponent_power=sum(x.power() for x in foes)
        return opponent_power>=max(12,p.power()*1.5+3) and sum(len(q.creatures) for q in foes)>=4
    def choose_removal(self,p,universal:bool):
        victims=[]
        ranks=self.ranks()
        for q in self.other_players(p):
            for c in q.creatures:
                value=c.power+0.45*c.toughness+1*(c.name=='large')
                victims.append((value+0.8*(4-ranks[q.seat]),q,'creature',c))
            if universal:
                for permanent in q.permanents:
                    value=permanent.value+2.0*(permanent.kind=='combo_piece')
                    victims.append((value+0.8*(4-ranks[q.seat]),q,'permanent',permanent))
        if not victims:return None
        weights=[math.exp(min(9,v[0])/2.5) for v in victims]
        return p.rng.choices(victims,weights=weights,k=1)[0]
    def cast(self,p:Player,kind:str,cost:int,t:int):
        # Important: actor mana is paid when attempting to cast, even if countered.
        p.mana-=cost;p.total_spent+=cost;p.cards_cast+=1
        severity={'small':1,'medium':2,'large':4,'tokens':3,'engine':4,'ramp':2,'draw':2,'combo_piece':5,'finisher':8,'wipe':7,'removal':3,'buff':3,'burn':3}[kind]
        target=None;removal=None
        if kind=='removal':
            removal=self.choose_removal(p,p.rng.random()<TEMPLATES['removal']['universal_chance'])
            target=removal[1] if removal else None
        if (kind=='burn' or kind=='finisher') and self.interaction:target=self.choose_target(p,'removal')
        if kind=='wipe':target=None
        if self.counter_attempt(p,target,kind,severity):
            self.counts['spell_countered']+=1;return
        self.counts['cast_'+kind]+=1
        self.say(f'  P{p.seat} ({p.arch}) CAST {kind} for {cost} mana; {p.mana} left.')
        if kind=='ramp':
            gain=2 if p.rng.random()<(0.18 if p.arch=='ramp_stompy' else 0.08) else 1
            p.ramp+=gain
            self.say(f'    Permanent ramp +{gain} mana/turn; next-turn capacity {p.active_mana()}.')
        elif kind in ('small','medium','large'):
            pow=self.random_param(kind,'power',p);tgh=self.random_param(kind,'toughness',p)
            self.create_creature(p,t,pow,tgh,kind)
            self.say(f'    Adds a {pow}/{tgh} {kind} creature (next turn attacks).')
        elif kind=='tokens':
            n=self.random_param(kind,'count',p);power=self.random_param(kind,'power',p)
            for _ in range(n):self.create_creature(p,t,power,power,'token',True)
            self.say(f'    Generates {n} {power}/{power} creatures.')
        elif kind=='engine':
            perm=Permanent(p.new_id(),'engine',3.0,p.rng.random()<0.4,t)
            p.permanents.append(perm)
            if perm.is_creature:self.create_creature(p,t,2,3,'engine creature',linked_permanent=perm.id)
            self.say('    Persistent draw/token engine enters'+(' as 2/3 creature.' if perm.is_creature else ' as noncreature permanent.'))
        elif kind=='draw':
            n=self.random_param(kind,'cards',p);p.draw(n)
            self.say(f'    Draws {n} extra abstract cards.')
        elif kind=='buff':
            n=self.random_param(kind,'power_boost',p)
            for c in p.creatures:c.power+=n
            self.say(f'    Board buff: +{n} power counters to current creatures (simplified lasting effect).')
        elif kind=='combo_piece':
            p.permanents.append(Permanent(p.new_id(),'combo_piece',5.0,False,t))
            self.say(f'    Combo setup pieces now {p.combo_n()}.')
        elif kind in ('finisher','burn'):
            if p.arch=='combo' and kind=='finisher' and p.combo_n()>=2:
                p.first_win_attempt=p.first_win_attempt or t
                self.counts['combo_win_attempts']+=1
                self.say(f'    ABSTRACT COMBO WIN ATTEMPT by P{p.seat}; record only (not resolved as win).')
            elif target:
                amount=self.random_param('finisher' if kind=='finisher' else 'burn','damage',p)
                target.life=max(0,target.life-amount)
                target.damage_taken+=amount
                self.say(f'    P{target.seat} takes {amount} direct damage; life={target.life}.')
        elif kind=='removal' and removal:
            _,victim,z,obj=removal
            if z=='creature':
                if obj in victim.creatures:self.destroy_creature(victim,obj)
            else:
                if obj in victim.permanents:
                    victim.permanents.remove(obj)
                    victim.creatures=[c for c in victim.creatures if c.linked_permanent!=obj.id]
            p.removal_cast+=1;p.threats_answered+=1
            self.target_counts[(p.seat,victim.seat,'removal')]+=1
            self.say(f'    REMOVES P{victim.seat}\'s {obj.name if z=="creature" else obj.kind}; remaining power={victim.power()}.')
        elif kind=='wipe':
            removed=sum(len(q.creatures) for q in self.players)
            for q in self.players:
                for c in list(q.creatures):self.destroy_creature(q,c)
            self.counts['board_wipes_resolved']+=1
            self.say(f'    WIPE: {removed} creatures across all players destroyed.')
    def main(self,p,t):
        if not p.alive or p.passive:return
        for _ in range(7):
            action=self.candidate(p,t)
            if action is None:break
            _,cost,i,card=action
            p.hand.pop(i)
            self.cast(p,card.kind,cost,t)
        if len(p.hand)>7:
            # Simplified discard to seven at EOT; not a real Magic discard optimizer.
            priorities=PROFILES['priority'][p.arch]
            p.hand.sort(key=lambda c: (c.kind!='land', c.kind in priorities and 99-priorities.index(c.kind)))
            n=len(p.hand)-7; p.hand=p.hand[n:]
    def fight(self,attacker:Player,defender:Player,creature:Creature):
        legal=[c for c in defender.creatures if not c.tapped]
        # Block favorable trades, block much more aggressively at low life.
        candidates=[]
        for c in legal:
            kill=c.power>=creature.toughness
            survive=c.toughness>creature.power
            urgency=(defender.life<=creature.power+5)
            if kill and (survive or urgency or c.power<=creature.power+1):
                candidates.append((3*survive+2*kill-0.13*c.power,c))
            elif urgency and c.toughness>=creature.power:
                candidates.append((1.5-0.12*c.power,c))
        blocked=bool(candidates)
        if blocked:
            _,blocker=max(candidates,key=lambda z:z[0]);blocker.tapped=True
            attacker_dies=blocker.power>=creature.toughness
            blocker_dies=creature.power>=blocker.toughness
            if attacker_dies and creature in attacker.creatures:
                self.destroy_creature(attacker,creature);self.counts['combat_deaths']+=1
            if blocker_dies and blocker in defender.creatures:
                self.destroy_creature(defender,blocker);self.counts['combat_deaths']+=1
            self.say(f'    BLOCK P{defender.seat} {blocker.power}/{blocker.toughness} vs P{attacker.seat} {creature.power}/{creature.toughness} -> attacker_dead={attacker_dies}, blocker_dead={blocker_dies}.')
        else:
            damage=creature.power;defender.life=max(0,defender.life-damage)
            attacker.attack_damage_dealt+=damage;defender.damage_taken+=damage
            self.say(f'    ATTACK P{attacker.seat} -> P{defender.seat}: {damage} unblocked; life={defender.life}.')
        self.target_counts[(attacker.seat,defender.seat,'attack')]+=1
    def combat(self,p:Player,t:int):
        if not self.interaction or p.passive or not p.alive:return
        eligible=[c for c in p.creatures if c.born<t and not c.tapped]
        for c in list(eligible):
            if not p.alive:break
            if c not in p.creatures:continue
            if p.rng.random()>=PROFILES['attack_rate'][p.arch]:continue
            target=self.choose_target(p,'attack')
            if target is None:break
            c.tapped=True
            self.fight(p,target,c)
    def round(self,t):
        self.turn=t
        if self.trace:self.say(f'\n===== ROUND {t} =====')
        for p in self.players:
            if p.passive or not p.alive:continue
            self.say(f'\nP{p.seat} ({p.arch}) starts life={p.life}, cards={len(p.hand)}, sources={p.active_mana()}, power={p.power()}')
            self.begin(p,t)
            self.main(p,t)
            self.combat(p,t)
        for p in self.players:p.stats.append(p.snapshot(t))
        ranks=self.ranks();self.rank_events.append({'turn':t,'ranks':ranks})
        if self.trace:
            ranks_desc=' > '.join(f'P{p.seat}:{p.arch} ({p.threat():.1f}, {p.life} life)' for p in sorted([x for x in self.players if x.alive],key=lambda x:ranks[x.seat]))
            self.say('END ROUND ranks (high to low): '+ranks_desc)
    def run(self,turns=10):
        for t in range(1,turns+1):self.round(t)
        return self
    def report(self):
        return {'seed':self.seed,'interaction':self.interaction,
                'players':[{'seat':p.seat,'archetype':p.arch,'passive':p.passive,'life':p.life,'mana_sources':p.active_mana(),
                            'casts':p.cards_cast,'creatures_lost':p.creatures_lost,'removals':p.removal_cast,
                            'counters':p.counters_cast,'attack_damage':p.attack_damage_dealt,
                            'win_attempt':p.first_win_attempt,'stats':p.stats} for p in self.players],
                'events':dict(self.counts),'rank_target_counts':[{'kind':k,'rank':r,'count':n} for (k,r),n in sorted(self.rank_target_counts.items())],'rank_exposures':[{'kind':k,'rank':r,'count':n} for (k,r),n in sorted(self.rank_exposures.items())],'targets':[{'from':a,'to':b,'kind':k,'count':v} for (a,b,k),v in sorted(self.target_counts.items())]}

def sample_archetypes(seed:int):
    rng=random.Random(seed*9967+11)
    return [rng.choice(ARCHETYPES) for _ in range(3)]
