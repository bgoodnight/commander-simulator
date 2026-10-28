"""v6: conservative real Magnus seat in the unchanged v5 abstract four-player engine.

This is a vertical integration test, NOT a complete MTG rules implementation.
Unimplemented card text is reported and cannot silently resolve as a generic effect.
"""
from __future__ import annotations
import json, random, sys
from collections import Counter
from dataclasses import replace
from pathlib import Path
from itertools import product
ROOT=Path(__file__).resolve().parent
V5=ROOT.parent/'v5_four_player'
V3=ROOT.parent/'v3_magnus_modular'
sys.path.insert(0,str(V5))
import simulation as base

CAT=json.loads((V3/'cards.json').read_text())['cards']
DECK=json.loads((V3/'deck_v16.json').read_text())

# Reviewed subset, actual costs from v3 catalog. Named creatures have verified
# core bodies / triggers; spells tagged partial when selection is simplified.
CREATURES={
    'Magnus the Red':(4,5,('flying',)),
    'Young Pyromancer':(2,1,()),
    'Harmonic Prodigy':(1,3,()),
    'Third Path Iconoclast':(1,1,()),
    'Storm-Kiln Artist':(2,2,()),
    'Goblin Electromancer':(2,2,()),
    'Baral, Chief of Compliance':(1,3,()),
    'Stormsplitter':(1,4,('haste',)),
    'Archmage Emeritus':(2,2,()),
}
ROCKS={'Sol Ring','Arcane Signet','Izzet Signet','Talisman of Creativity','Mind Stone','Fellwar Stone'}
SELECTION={'Brainstorm':3,'Ponder':1,'Preordain':1,'Telling Time':1,'Impulse':1,'Frantic Search':2}
COUNTERS={'Counterspell':('creature','instant','sorcery','artifact','enchantment','planeswalker'),
          'Arcane Denial':('creature','instant','sorcery','artifact','enchantment','planeswalker'),
          'Swan Song':('instant','sorcery','enchantment'),
          "An Offer You Can't Refuse":('noncreature',),
          'Flusterstorm':('instant','sorcery')}
REMOVAL={'Pongify'}
ENGINE_BODIES={'Young Pyromancer','Third Path Iconoclast','Goblin Electromancer','Baral, Chief of Compliance','Harmonic Prodigy','Storm-Kiln Artist','Archmage Emeritus','Stormsplitter'}
SUPPORTED=set(CREATURES)|ROCKS|set(SELECTION)|set(COUNTERS)|REMOVAL|{n for n,d in CAT.items() if d['type']=='land'}
APPROX={'Brainstorm','Ponder','Preordain','Telling Time','Impulse','Frantic Search','Flusterstorm',
        'Arcane Denial',"An Offer You Can't Refuse"}

LANDS={n for n,d in CAT.items() if d['type']=='land'}

def named_spec(name):
    d=CAT[name];c=d.get('cost');mv=sum(c) if c else 0
    typ=d['type']
    typ={'commander':'creature','spell':'instant' if name in COUNTERS or name in REMOVAL or name in {'Brainstorm','Telling Time','Impulse','Frantic Search'} else 'sorcery',
         'permanent':'artifact'}.get(typ,typ)
    if name in LANDS: return base.CardSpec(name,'land',0,'land','none')
    if name in CREATURES: eff='named_creature'
    elif name in ROCKS:eff='named_rock'
    elif name in SELECTION:eff='named_selection'
    elif name in COUNTERS:eff='counter'
    elif name in REMOVAL:eff='named_pongify'
    else:eff='unsupported'
    return base.CardSpec(name,name,mv,typ,eff,{'coverage':'approx' if name in APPROX else 'supported' if eff!='unsupported' else 'unsupported'},
                         {'U':c[1],'R':c[2]} if c else {})

def shuffled_library(seed):
    a=[]
    for n,count in DECK['cards'].items():a.extend([named_spec(n)]*count)
    assert len(a)==99
    random.Random(seed).shuffle(a)
    return a

class ColoredPayment:
    """Spend floating mana plus ready land/rock sources, never generic for colored pips.

    The small branch-bound search minimizes tapped sources and avoids double-spending.
    Izzet Signet produces U+R but requires one additional mana, so cannot activate alone.
    """
    @staticmethod
    def modes(n):
        if n=='Riverglide Pathway [U]':return [(1,0,0)]
        if n=='Riverglide Pathway [R]':return [(0,1,0)]
        if n=='Sol Ring':return [(0,0,2)]
        if n=='Izzet Signet':return [(1,1,0)]
        if n=='Mind Stone':return [(0,0,1)]
        if n=='Treasure':return [(1,0,0),(0,1,0),(0,0,1)]
        if n in {'Arcane Signet','Talisman of Creativity','Fellwar Stone'}:return [(1,0,0),(0,1,0)]
        d=CAT.get(n,{})
        profile=d.get('land_profile','C')
        if profile=='U':return [(1,0,0)]
        if profile=='R':return [(0,1,0)]
        if profile=='D' or profile=='pathway' or profile=='fetch':return [(1,0,0),(0,1,0)]
        return [(0,0,1)]
    def _best(self,p,action):
        cost=action.cost
        u=action.parameters.get('U',0);r=action.parameters.get('R',0)
        generic=max(0,cost-u-r)
        sources=list(getattr(p,'ready_sources',[]))
        floating=getattr(p,'floating',(0,0,0))
        states={(floating[0],floating[1],floating[2],False):()}
        # Dynamic states. Dominated source subsets pruned by bounded totals.
        cap=cost+3
        for i,n in enumerate(sources):
            nexts=dict(states)
            for (a,b,c,signet),plan in states.items():
                for mode in self.modes(n):
                    key=(min(cap,a+mode[0]),min(cap,b+mode[1]),min(cap,c+mode[2]), signet or n=='Izzet Signet')
                    new=plan+((i,mode),)
                    if key not in nexts or len(new)<len(nexts[key]):nexts[key]=new
            states=nexts
        choices=[]
        for (a,b,c,signet),plan in states.items():
            # Signet requires tapping a separate source for its activation cost.
            extra=int(signet)
            if a>=u and b>=r and a+b+c-u-r>=generic+extra:
                choices.append((len(plan),sum(mode[0]+mode[1]+mode[2] for _,mode in plan),plan,(a,b,c),extra))
        if not choices:return None
        _,_,plan,tot,extra=min(choices,key=lambda z:(z[0],z[1]))
        # Pay colored first, then generic + activation, drawing from C, U, R.
        left=[tot[0]-u,tot[1]-r,tot[2]]
        remaining=generic+extra
        for i in (2,0,1):
            used=min(left[i],remaining);left[i]-=used;remaining-=used
        assert remaining==0
        return plan,tuple(left)
    def can_pay(self,p,a):return self._best(p,a) is not None
    def pay(self,p,a):
        result=self._best(p,a)
        if result is None:raise ValueError('Illegal colored mana payment')
        plan,left=result
        used={i for i,_ in plan}
        spent_treasure=sum(p.ready_sources[i]=='Treasure' for i in used)
        p.treasures-=spent_treasure
        p.ready_sources=[n for i,n in enumerate(p.ready_sources) if i not in used]
        p.floating=left
        p.mana=sum(sum(m) for n in p.ready_sources for m in [max(self.modes(n),key=lambda x:sum(x))])+sum(left)
        p.payments.append({'source':a.source,'cost':a.cost,'U':a.parameters.get('U',0),'R':a.parameters.get('R',0),'sources_tapped':[n for i,n in enumerate(getattr(p,'_pre_pay_sources',[]))] if False else len(plan)})

class MagnusPilot:
    """Conservative, reproducible priority pilot. No perfect-information decisions."""
    def select_action(self,table,p):
        options=[]
        cards=list(p.hand)
        if p.commander_in_zone:cards.append(named_spec('Magnus the Red'))
        for ix,c in enumerate(cards):
            if c.effect in ('unsupported','none','counter'):continue
            if c.effect=='named_pongify' and not table.removal_targets(p,c):continue
            a=table.action_for(p,c)
            if not p.payment_policy.can_pay(p,a):continue
            if c.name in ROCKS:score=95+(5 if table.round_num<=3 else -15)
            elif c.name in {'Young Pyromancer','Third Path Iconoclast','Goblin Electromancer','Baral, Chief of Compliance'}:score=85
            elif c.name=='Magnus the Red':score=88 if p.token_count()>=1 else 65
            elif c.name in {'Storm-Kiln Artist','Harmonic Prodigy','Archmage Emeritus','Stormsplitter'}:score=75
            elif c.name in SELECTION:score=67 if len(p.hand)<=4 else 43
            elif c.name=='Pongify':score=45+table.interaction_urgency(p,c)
            else:score=10
            if c.name=='Magnus the Red' and table.round_num<=4:score-=5
            if c.name in SELECTION and p.token_count()>=3:score+=10
            # Do not spend counter mana on speculative late development when an enemy win looms.
            if c.name not in ROCKS and any(q.combo()>=2 for q in table.rivals(p)) and p.has_response():
                if p.mana-a.cost<2:score-=30
            options.append((score,-a.cost,-ix,a))
        return max(options,key=lambda x:x[:3])[-1] if options else None

class DetailedPlayer(base.Player):
    def __init__(self,seat,seed):
        super().__init__(seat,'magnus',seed,shuffled_library(seed+601),MagnusPilot())
        self.payment_policy=ColoredPayment()
        self.ready_sources=[];self.floating=(0,0,0);self.land_names=[];self.rock_names=[]
        self.commander_in_zone=True;self.commander_casts=0;self.graveyard=[];self.payments=[];self.treasures=0
        self.coverage=Counter();self.unsupported_seen=Counter();self.land_misses=0
        self.block_policy='never'
        self.draw(7)
        if not 2<=sum(x.kind=='land' for x in self.hand)<=5:
            self.library=shuffled_library(seed+602);self.hand=[];self.draw(7);self.mulligans=1
    def token_count(self):return sum(c.token for c in self.creatures)
    def has_response(self):return any(c.name in COUNTERS for c in self.hand)
    def available_sources(self):
        return len(self.land_names)+sum(2 if n=='Sol Ring' else 1 for n in self.rock_names)+self.treasures
    def snapshot(self,round_num):
        d=super().snapshot(round_num)
        d.update(tokens=self.token_count(),colored_ready={'U':sum('U' in str(ColoredPayment.modes(n)) for n in self.ready_sources),
                                                         'R':sum('1, 0)' in str(ColoredPayment.modes(n)) for n in self.ready_sources)},
                 named_hand=[x.name for x in self.hand],commander_zone=self.commander_in_zone,
                 commander_casts=self.commander_casts,unsupported_in_hand=sum(x.effect=='unsupported' for x in self.hand))
        return d

class MixedTable(base.Table):
    def __init__(self,opponents=('aggro','control','combo'),seed=1,trace=True,opening=None):
        alltypes=['magnus',*opponents]
        if len(opponents)!=3:raise ValueError('Exactly three abstract opponents')
        # Equivalent to Table.with_players without a fake abstract Magnus deck.
        players=[DetailedPlayer(0,seed*109+3)]+[base.Player(i,a,seed*109+i*431+3,
                     base.synthetic_library(a,seed*67+i*17+23),base.PriorityPilot()) for i,a in enumerate(opponents,1)]
        for p in players[1:]:
            p.draw(7)
            if not 2<=sum(x.kind=='land' for x in p.hand)<=5:
                p.library=base.synthetic_library(p.archetype,seed*67+p.seat*17+23);p.hand=[];p.draw(7);p.mulligans=1
        super().__init__(alltypes,seed,True,trace,players=players)
        self.details=self.players[0];self.coverage_log=[];self.seeded_opening=bool(opening)
        if opening:self._set_opening(opening)
        self.register_effect('named_creature',self.resolve_creature)
        self.register_effect('named_rock',self.resolve_rock)
        self.register_effect('named_selection',self.resolve_selection)
        self.register_effect('named_pongify',self.resolve_pongify)
        self.on_event(self.named_triggers)
    def _set_opening(self,names):
        """Diagnostic-only fixed opening: move named cards from same 99-card library.
        Do not use for unbiased deck performance claims.
        """
        p=self.details
        for name in names:
            found=next((c for c in p.hand+p.library if c.name==name),None)
            if found is None:raise ValueError('Card not in deck '+name)
            if found in p.hand:p.hand.remove(found)
            else:p.library.remove(found)
            p.hand.insert(0,found)
        while len(p.hand)>7:p.library.insert(0,p.hand.pop())
        while len(p.hand)<7:p.draw()
    def action_for(self,p,c):
        red=c.colored_cost.get('R',0);blue=c.colored_cost.get('U',0)
        disc=0
        if c.card_type in ('instant','sorcery'):
            if any(x.name=='Magnus the Red' for x in p.creatures):disc+=p.token_count()
            disc+=sum(x.name in {'Goblin Electromancer','Baral, Chief of Compliance'} for x in p.creatures)
        cost=max(red+blue,c.mana_value-disc)+(2*p.commander_casts if c.name=='Magnus the Red' else 0)
        a=base.Action(p.seat,c.name,c.card_type,c.effect,cost,
                      parameters={**c.parameters,'U':blue,'R':red})
        if c.name=='Pongify':
            targets=self.removal_targets(p,c)
            if targets:
                q,creature=max(((q,x) for q,x in targets if isinstance(x,base.Creature)),key=lambda qc:qc[1].power,default=(None,None))
                if q is not None:a.target=q.seat;a.target_object=creature.id
        return a
    def upkeep(self,p,t):
        if p is not self.details:return super().upkeep(p,t)
        self.emit('turn_start',None,controller=p.seat,round=t)
        for c in p.creatures:c.tapped=False
        # Land play is the main-phase approximation retained from v5.
        p.draw(1)
        if not p.alive:self.eliminate(p,'empty_library');return
        land=next((c for c in p.hand if c.kind=='land'),None)
        newly_tapped=None
        if land:
            p.hand.remove(land)
            landname=land.name
            if landname=='Fabled Passage':
                # Sacrifice and search for basic, thinning the library.
                basics=[c for c in p.library if c.name in ('Island','Mountain')]
                if basics:
                    u=sum(n=='Island' or ' [U]' in n for n in p.land_names)
                    r=sum(n=='Mountain' or ' [R]' in n for n in p.land_names)
                    desired='Island' if u<=r else 'Mountain'
                    basic=next((c for c in basics if c.name==desired),basics[0])
                    p.library.remove(basic);landname=basic.name
                    if t<4:newly_tapped=landname
                    self.note(f'  P0 uses Fabled Passage, fetches {landname} ({"tapped" if t<4 else "untapped"}).')
                else:
                    landname='Fabled Passage'
            elif landname=='Riverglide Pathway':
                u=sum(n=='Island' or n.endswith('[U]') for n in p.land_names)
                r=sum(n=='Mountain' or n.endswith('[R]') for n in p.land_names)
                landname='Riverglide Pathway [U]' if u<=r else 'Riverglide Pathway [R]'
            old=len(p.land_names)
            if landname=='Mystic Sanctuary' or (landname=='Stormcarved Coast' and old<2) or (landname=='Spirebluff Canal' and old>=3):
                newly_tapped=landname
            if landname=='Sulfur Falls' and not any(n in ('Island','Mountain','Steam Vents') for n in p.land_names):
                newly_tapped=landname
            if landname=='Steam Vents':
                # Choosing to pay 2 life avoids a temporary mana delay.
                p.life-=2;p.damage_taken+=2
                self.note('  Steam Vents enters untapped; P0 pays 2 life.')
                if p.life<=0:self.eliminate(p,'shock_land');return
            p.land_names.append(landname);p.lands=len(p.land_names)
            self.note(f'  P0 plays {land.name} ({p.lands} lands){" tapped" if newly_tapped else ""}.')
            self.emit('land_played',None,controller=0,round=t)
        else:p.land_misses+=1;self.note('  P0 misses land drop.')
        p.ready_sources=p.land_names.copy()+p.rock_names.copy()+['Treasure']*p.treasures;p.floating=(0,0,0)
        if newly_tapped and newly_tapped in p.ready_sources:p.ready_sources.remove(newly_tapped)
        p.mana=sum(max(sum(mode) for mode in ColoredPayment.modes(n)) for n in p.ready_sources)
        self.coverage_log.append({'round':t,'hand_unsupported':[c.name for c in p.hand if c.effect=='unsupported']})
        for c in p.hand:
            if c.effect=='unsupported':p.unsupported_seen[c.name]+=1
    def main(self,p):
        if p is not self.details:return super().main(p)
        for _ in range(12):
            if not p.alive or len(self.alive())<=1:break
            action=p.pilot.select_action(self,p)
            if action is None:break
            if not self.cast(action):raise AssertionError('Pilot offered illegal action '+str(action))
        # Do not discard down to 7 here before end step? v5 approximates cleanup.
        if len(p.hand)>7:
            p.hand=p.hand[:7]
    def cast(self,a):
        p=self.players[a.actor]
        if p is not self.details:return super().cast(a)
        if a.source=='Magnus the Red' and p.commander_in_zone:
            p.hand.append(named_spec('Magnus the Red'))
            zone_cast=True
        else:zone_cast=False
        if a.effect=='unsupported':raise ValueError('Unsupported card may not be cast: '+a.source)
        if not p.payment_policy.can_pay(p,a):
            if zone_cast:p.hand.pop()
            return False
        # superclass's counter window is delegated to overridden respond().
        success=super().cast(a)
        if success:
            p.coverage['approx' if a.source in APPROX else 'supported']+=1
            if zone_cast:
                p.commander_casts+=1
                p.commander_in_zone=not any(c.name=='Magnus the Red' for c in p.creatures)
            elif a.source not in CREATURES and a.source not in ROCKS:
                p.graveyard.append(a.source)
        return success
    def respond(self,action):
        """Single defensive-counter window; actual colored payment for Magnus.
        Counterspell is still a simplified priority exchange: no arbitrary stack nesting.
        """
        if not self.interactive or action.effect=='counter':return False
        actor=self.players[action.actor]
        choices=[]
        for q in self.alive():
            if q.seat==actor.seat:continue
            for c in q.hand:
                if c.effect!='counter':continue
                if q is self.details:
                    allowed=COUNTERS.get(c.name,())
                    legal=action.card_type in allowed or ('noncreature' in allowed and action.card_type!='creature')
                    response=self.action_for(q,c)
                    payable=q.payment_policy.can_pay(q,response)
                else:
                    allowed=c.parameters.get('can_counter_types',('creature','instant','sorcery','artifact','enchantment','planeswalker'))
                    legal=action.card_type in allowed
                    payable=q.mana>=c.mana_value
                if not legal or not payable:continue
                directly=(action.target==q.seat or action.effect in ('wipe','finisher'))
                importance=action.effect in ('finisher','wipe')
                # Reserve interaction for high-impact spells, threat to own board, or directly targeted removal.
                chance=(0.45 if directly else 0.12)+(0.38 if importance else 0)+(0.2 if action.effect=='remove' and directly else 0)
                chance+=base.CONF['counter_response_bonus'].get(q.archetype,0)
                if q is self.details and action.effect=='named_creature' and not directly:chance-=0.07
                choices.append((chance,q,c))
        if not choices:return False
        chance,q,c=max(choices,key=lambda v:v[0]+self.rng.random()*.12)
        if self.rng.random()>min(.96,chance):return False
        if q is self.details:
            r=self.action_for(q,c)
            q.hand.remove(c);q.payment_policy.pay(q,r);q.cards_cast+=1;q.mana_spent+=r.cost
            q.coverage['approx' if c.name in APPROX else 'supported']+=1;q.graveyard.append(c.name)
            self.emit('spell_cast',r)
        else:
            q.hand.remove(c);q.mana-=c.mana_value;q.cards_cast+=1;q.mana_spent+=c.mana_value
            r=base.Action(q.seat,c.name,'instant','counter',c.mana_value)
            self.emit('spell_cast',r)
        q.counters_used+=1;self.counts['counters_cast']+=1
        self.note(f'    P{q.seat} counters {action.source} with {c.name}.')
        # Not yet modeling counter-counter response; diagnostic records this limitation.
        self.counts['spells_countered']+=1
        if c.name=='Swan Song':self.add_creature(actor,2,2,'Bird (Swan Song)',token=True,keywords=('flying',))
        if c.name=="An Offer You Can't Refuse":
            if actor is self.details:
                actor.treasures+=2;actor.ready_sources.extend(['Treasure','Treasure']);actor.mana+=2
            else:self.add_permanent(actor,'ramp',2,'Treasures (Offer)')
        return True
    def add_creature(self,p,power,toughness,name,token=False,engine=False,keywords=()):
        # Synthetic flyers are assigned at creation, not based on the Magnus seat's
        # actual draws. This lets opponents sometimes block or pressure in the air.
        if p is not self.details and not keywords and not token:
            if p.rng.random()<(0.17 if power>=4 else 0.06 if power>=2 else 0.0):
                keywords=('flying',)
        return super().add_creature(p,power,toughness,name,token,engine,keywords)
    def resolve_creature(self,table,action):
        p=self.players[action.actor];name=action.source
        power,tough,keywords=CREATURES[name]
        # Creature is a permanent that can be targeted/removed via common v5 board.
        c=self.add_creature(p,power,tough,name,keywords=keywords)
        self.note(f'    {name} enters battlefield ({power}/{tough}).')
    def resolve_rock(self,table,action):
        p=self.players[action.actor];name=action.source
        p.rock_names.append(name)
        self.add_permanent(p,'ramp',2 if name=='Sol Ring' else 1,name)
        self.note(f'    {name} increases available mana next turn.')
    def resolve_selection(self,table,action):
        p=self.players[action.actor];name=action.source
        # Explicitly partial selection; no scry optimization, choose among top cards only.
        n=SELECTION[name]
        p.draw(n)
        if name=='Brainstorm':
            # Draw three, return two from hand to top, keeping our best development.
            priority=lambda c: 1 if c.kind=='land' and p.lands<5 else 0 if c.effect=='unsupported' else 2
            for c in sorted(p.hand,key=priority)[:2]:
                p.hand.remove(c);p.library.append(c)
        if name=='Frantic Search':
            for c in sorted(p.hand,key=lambda c:c.effect!='unsupported')[:2]:
                p.hand.remove(c);p.graveyard.append(c.name)
            # Untapping lands is not implemented; diagnostic flags retained.
        self.note(f'    {name}: partial card selection ({n} cards drawn; exact look/scry not modeled).')
    def resolve_pongify(self,table,action):
        if action.target is None or action.target_object is None:return
        q=self.players[action.target]
        c=next((c for c in q.creatures if c.id==action.target_object),None)
        if c:
            self.kill_creature(q,c)
            self.add_creature(q,3,3,'Ape (Pongify)',token=True)
            self.details.removal_used+=1
            self.note(f'    Pongify destroys {c.name}; P{q.seat} gets a 3/3 Ape.')
    def named_triggers(self,table,event,action,payload):
        p=self.details
        if event=='creature_died' and payload.get('controller')==p.seat:
            if payload.get('source')=='Magnus the Red':
                p.commander_in_zone=True
                self.note('    Magnus returns to the command zone (commander tax on next cast).')
        if event!='spell_cast' or action is None or action.actor!=p.seat:return
        if action.card_type not in ('instant','sorcery'):return
        # Cast triggers happen after mana cost was fixed and paid; even a countered spell triggers.
        h=any(c.name=='Harmonic Prodigy' for c in p.creatures)
        snapshot=list(p.creatures)
        total=0
        for creature in snapshot:
            if creature.name=='Young Pyromancer':
                for _ in range(2 if h else 1):self.add_creature(p,1,1,'Elemental',token=True);total+=1
            if creature.name=='Third Path Iconoclast':
                self.add_creature(p,1,1,'Soldier',token=True);total+=1
            if creature.name=='Stormsplitter':
                for _ in range(2 if h else 1):
                    copy=self.add_creature(p,1,4,'Stormsplitter',token=True,keywords=('haste','expires'))
                    # Stormsplitter token will also have a triggered ability on future casts.
                    total+=1
            if creature.name=='Storm-Kiln Artist':
                for _ in range(2 if h else 1):
                    p.treasures+=1;p.ready_sources.append('Treasure');p.mana+=1;total+=1
            if creature.name=='Archmage Emeritus':
                for _ in range(2 if h else 1):p.draw();total+=1
        if total:self.note(f'    Cast triggers: {total} tokens/treasures/draw effects; token count={p.token_count()}.')
    def kill_creature(self,p,c):
        super().kill_creature(p,c)
        if p is self.details and c.name=='Magnus the Red' and c not in p.creatures:
            p.commander_in_zone=True
    def damage(self,p,n,source=None,cause='damage'):
        super().damage(p,n,source,cause)
        # Combat damage from Magnus creates 3/3 Spawn (flying can be blocked only by flyers/reach).
        if cause=='combat' and source is self.details and getattr(self,'current_attacker',None)=='Magnus the Red' and n>0:
            self.add_creature(source,3,3,'Spawn',token=True)
            self.note('    Blade of Magnus creates a 3/3 Spawn token.')
    def block(self,defender,attacker_creature,used):
        if 'flying' in attacker_creature.keywords:
            legal=[c for c in defender.creatures if c.id not in used and not c.tapped and ('flying' in c.keywords or 'reach' in c.keywords)]
            if not legal:return None
            # Restrict legal blockers without changing shared block heuristic.
            illegal=[c for c in defender.creatures if c not in legal]
            defender.creatures=[c for c in defender.creatures if c in legal]
            try:return super().block(defender,attacker_creature,used)
            finally:defender.creatures=legal+illegal
        return super().block(defender,attacker_creature,used)
    def combat(self,p):
        # Retain v5 multiplayer targeting, damage and blocks; fix flying and haste only.
        if not self.interactive:return
        eligible=[c for c in list(p.creatures) if (c.entered_round<self.round_num or 'haste' in c.keywords) and not c.tapped]
        used_blockers={q.seat:set() for q in self.alive()}
        for c in eligible:
            if c not in p.creatures or not p.alive or len(self.alive())<=1:continue
            rate=base.CONF['attack_rate'].get(p.archetype,0.65)
            if p is self.details and c.name=='Magnus the Red':rate=0.78
            if p is self.details and c.name in ENGINE_BODIES:
                # Pilot protects continuous engines instead of recklessly attacking 2/1s.
                continue
            if p.rng.random()>=rate:continue
            q=self.choose_target(p,'attack')
            if not q:continue
            if p is self.details and c.power<=3:
                predicted=self.block(q,c,set())
                if predicted is not None and predicted.power>=c.toughness and predicted.toughness>c.power:
                    continue
            self.emit('combat_attack',None,attacker=p.seat,defender=q.seat,creature_id=c.id)
            c.tapped=True
            block=self.block(q,c,used_blockers[q.seat])
            if block:
                used_blockers[q.seat].add(block.id)
                da=block.power>=c.toughness;db=c.power>=block.toughness
                self.note(f'    COMBAT P{p.seat} {c.name} {c.power}/{c.toughness} into P{q.seat} {block.name} {block.power}/{block.toughness}.')
                if da:self.kill_creature(p,c)
                if db:self.kill_creature(q,block)
                self.counts['blocks']+=1
            else:
                self.note(f'    COMBAT P{p.seat} {c.name} attacks P{q.seat} unblocked for {c.power}.')
                self.current_attacker=c.name if p is self.details else None
                self.damage(q,c.power,p,'combat')
                self.current_attacker=None
            self.counts['attackers']+=1
    def _cleanup_expiring(self):
        for q in self.alive():
            for c in list(q.creatures):
                if c.token and 'expires' in c.keywords:self.kill_creature(q,c)
    def run(self,max_rounds=8):
        order=list(range(4));self.rng.shuffle(order);self.turn_order=order
        for turn in range(1,max_rounds+1):
            self.round_num=turn;self.note(f'\n========== ROUND {turn} ==========')
            for seat in order:
                p=self.players[seat]
                if not p.alive:continue
                self.upkeep(p,turn)
                if p.alive:self.main(p);self.combat(p)
                self._cleanup_expiring()
                if self.end_check():break
            self.turns.append({'round':turn,'players':[p.snapshot(turn) for p in self.players], 'rankings':self.rankings()})
            if self.trace:self.note('  End round: '+', '.join(f'P{q.seat} {q.archetype} life={q.life} board={q.power()} sources={q.available_sources()}' for q in self.alive()))
            if self.end_round is not None:break
        if self.end_round is None:self.win_reason='turn_limit'
        return self
    def diagnostics(self):
        p=self.details
        return {'seed':self.seed,'opening_forced':self.seeded_opening,
                'name':DECK['name'],'library_total':sum(DECK['cards'].values()),
                'supported_definitions':sum(n in SUPPORTED for n in DECK['cards']),
                'unsupported_definitions':[n for n in DECK['cards'] if n not in SUPPORTED],
                'approx_definitions':sorted(APPROX),
                'coverage_casts':dict(p.coverage),'unsupported_held':dict(p.unsupported_seen),
                'commander_casts':p.commander_casts,'commander_in_zone':p.commander_in_zone,
                'mana_payments':p.payments,'land_misses':p.land_misses,
                'known_rules_gaps':['limited named-card subset; many cards inert',
                    'selection and scry approximated','priority/stack only one defensive counter layer',
                    'abstract cards use fungible mana','permanent and token zones simplified',
                    'no commander damage tracking','no multi-block or detailed evasion except flying',
                    'select land ETB conditions approximated; land utility and painful mana abilities not modeled',
                    'Izzet Signet activation simplified to pooled source costs',
                    'no sorcery speed priority protection on counter windows',
                    'combat damage assignment simplified','no buyback/tutors/actual Magnus combo recipes']}


def game(seed=1,opponents=('aggro','control','combo'),opening=None,rounds=8):
    return MixedTable(opponents,seed,True,opening=opening).run(rounds)
