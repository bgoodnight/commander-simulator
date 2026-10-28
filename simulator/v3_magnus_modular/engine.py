"""Data-driven, bounded MTG *partial* simulator. Not a rules engine.

The card catalog declares card name, types, mana cost, triggered abilities, and tags.
Unsupported effects remain explicit; no guessing that a card does something.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from pathlib import Path
import json,random
ROOT=Path(__file__).parent

@dataclass(frozen=True)
class Source:
    key:str
    kind:str
    modes:tuple[tuple[int,int,int,int,int], ...] # U,R,C,spell-U,spell-R

class Catalog:
    def __init__(self,path=ROOT/'cards.json',deck_path=ROOT/'deck_v16.json'):
        data=json.loads(Path(path).read_text());self.cards=data['cards']
        deck=json.loads(Path(deck_path).read_text());self.deck_name=deck['name']
        self.commander=deck['commander'];self.deck_counts=deck['cards'];self.library=[]
        assert self.commander in self.cards and self.cards[self.commander]['type']=='commander'
        for name,count in self.deck_counts.items():
            assert name in self.cards, f'Missing card behavior/metadata for {name}'
            assert isinstance(count,int) and count>=0
            self.library.extend([name]*count)
        assert len(self.library)==99, f'library has {len(self.library)} cards'
        assert self.commander not in self.library
    def get(self,n):return self.cards[n]
    def type(self,n):return self.get(n)['type']
    def tags(self,n):return set(self.get(n).get('tags',[]))
    def effects(self,n,event):return [e for e in self.get(n).get('effects',[]) if e['event']==event]
    def cost(self,n):return self.get(n).get('cost')
    def supported(self,n):return self.get(n)['status']

@dataclass
class Token:
    ident:int
    kind:str
    birth:int
    haste:bool=False
    expires:bool=False

class Game:
    def __init__(self,catalog:Catalog,seed:int,policy='delay_one',scenario='none',trace=False):
        self.cat=catalog;self.seed=seed;self.rng=random.Random(seed);self.policy=policy;self.scenario=scenario
        self.deck=catalog.library.copy();self.rng.shuffle(self.deck)
        self.hand=[];self.mulligans=0
        # One free London mulligan: redraw seven without bottoming. Further mulligans not modeled.
        self.hand=[self.deck.pop(0) for _ in range(7)]
        if not 2<=sum(self.cat.type(c)=='land' for c in self.hand)<=4:
            self.mulligans=1;self.deck=catalog.library.copy();self.rng.shuffle(self.deck)
            self.hand=[self.deck.pop(0) for _ in range(7)]
        self.turn=0;self.board={};self.lands=[];self.tokens=[];self.token_serial=0
        self.tapped=set();self.treasures=0;self.grave=[];self.exile=[]
        self.floating=(0,0,0,0,0);self.magnus_casts=0;self.magnus_deferred_turn=None;self.first_magnus=None
        self.class_levels={};self.selection_cast=0;self.instant_sorcery_cast=0;self.actions=0;self.ramp_cast=0
        self.total_spent=0;self.generic_saved=0;self.disruption_stopped=False;self.disruption_target=None
        self.first_combo=None;self.combo_events=[];self.unmodeled_seen=set();self.turn_stats={}
        self.log=[];self.trace=trace
    def note(self,msg):
        if self.trace:self.log.append(msg)
    def has(self,n):return n in self.board
    def has_magnus(self):return self.has('Magnus the Red')
    def level(self,n):return self.class_levels.get(n,0)
    def token_count(self):return len(self.tokens)
    def wizard(self,n):
        if self.has('Maskwood Nexus') or self.has('Arcane Adaptation'):return self.cat.type(n) in ('creature','commander')
        return 'Wizard' in self.cat.get(n).get('subtypes',[])
    def wizards(self):
        return sum(self.wizard(c) for c in self.board if self.cat.type(c) in ('creature','commander'))+sum(t.kind in ('Wizard','Stormsplitter') or self.has('Maskwood Nexus') or self.has('Arcane Adaptation') for t in self.tokens)
    def engine_count(self):
        return sum(bool(self.cat.tags(c)&{'early_engine','token_engine','mana_engine','discount_engine','draw_engine','control_engine','copy_engine'}) for c in self.board if c!='Magnus the Red')
    def token_engine_count(self):return sum('token_engine' in self.cat.tags(c) for c in self.board)
    def discount(self):
        base=0
        for c in self.board:
            for e in self.cat.effects(c,'static'):
                if e['op']=='discount_spells':base+=e['value']
                elif e['op']=='discount_per_token':base+=len(self.tokens)*e['value']
        return base
    def add_tokens(self,kind,amount=1):
        for _ in range(amount):
            self.token_serial+=1
            self.tokens.append(Token(self.token_serial,kind,self.turn,kind=='Stormsplitter',kind=='Stormsplitter'))
        if amount:self.note(f'    Trigger: create {amount} {kind} token(s); total tokens {self.token_count()}.')
    def draw(self,n=1):
        out=[]
        for _ in range(n):
            if self.deck:
                c=self.deck.pop(0);out.append(c);self.hand.append(c)
            else:self.note('    Library empty: further draw cannot resolve normally (not modeled as a loss).')
        if out:
            self.note('    Draw: '+', '.join(out))
            for c in out:
                if self.cat.supported(c) in ('partial','unmodeled'):self.unmodeled_seen.add(c)
        return out
    def value(self,c):
        t=self.cat.type(c);land_count=len(self.lands)
        if t=='land':return 28 if land_count<min(5,self.turn+1) else 18 if land_count<6 else 4
        tags=self.cat.tags(c)
        if 'ramp' in tags:return 25 if self.turn<=4 else 12
        if 'selection' in tags:return 21 if land_count<4 else 11
        if 'early_engine' in tags:return 19
        if tags&{'discount_engine','token_engine','mana_engine','control_engine'}:return 16
        if tags&{'counter'}:return 17 if self.turn>=4 else 11
        if tags&{'finisher'}:return 6
        return 9
    def bottom(self,items):self.deck.extend(items)
    def select(self,method):
        if method=='preordain':
            top=self.deck[:2];self.deck=self.deck[2:];keep=sorted(top,key=self.value,reverse=True)
            chosen=[c for c in keep if self.value(c)>=13]
            self.deck=chosen+self.deck;self.bottom([c for c in keep if c not in chosen]);self.note(f'    Preordain scry: top {chosen}, bottom {[c for c in keep if c not in chosen]}.');self.draw()
        elif method=='ponder':
            top=self.deck[:3];self.deck=self.deck[3:];sorted_top=sorted(top,key=self.value,reverse=True)
            if sorted_top and self.value(sorted_top[0])<=6:
                self.deck=top+self.deck;self.rng.shuffle(self.deck);self.note('    Ponder shuffled the library.')
            else:
                self.deck=sorted_top+self.deck;self.note('    Ponder ordered: '+str(sorted_top))
            self.draw()
        elif method=='brainstorm':
            self.draw(3);low=sorted(self.hand,key=self.value)[:2]
            for c in low:self.hand.remove(c)
            self.deck=low+self.deck;self.note('    Brainstorm put back: '+str(low))
        elif method=='telling_time':
            peek=self.deck[:3];self.deck=self.deck[3:];peek.sort(key=self.value,reverse=True)
            if peek:self.hand.append(peek[0])
            if len(peek)>1:self.deck=[peek[1]]+self.deck
            self.bottom(peek[2:]);self.note('    Telling Time: hand '+str(peek[:1])+', top '+str(peek[1:2])+', bottom '+str(peek[2:]))
        elif method=='impulse':
            peek=self.deck[:4];self.deck=self.deck[4:];peek.sort(key=self.value,reverse=True)
            if peek:self.hand.append(peek[0]);self.note('    Impulse: took '+peek[0])
            self.bottom(peek[1:])
        elif method=='frantic_search':
            self.draw(2)
            low=sorted(self.hand,key=self.value)[:2]
            for c in low:self.hand.remove(c);self.grave.append(c)
            tapped_lands=[f'L{i}' for i in range(len(self.lands)) if f'L{i}' in self.tapped]
            for i in tapped_lands[:3]:self.tapped.remove(i)
            self.note(f'    Frantic Search: discarded {low}, untapped {len(tapped_lands[:3])} lands.')
        elif method=='scry3':
            peek=self.deck[:3];self.deck=self.deck[3:];good=sorted([c for c in peek if self.value(c)>=13],key=self.value,reverse=True)
            bad=[c for c in peek if c not in good];self.deck=good+self.deck;self.bottom(bad)
            self.note(f'    Scry 3: kept {good}, bottomed {bad}.')
        else:raise ValueError('Unimplemented selection method: '+method)
    def event(self,event,spell='',zone='hand',is_copy=False):
        # Snapshot trigger sources: each Stormsplitter copy is itself a permanent with its ability.
        providers=([spell] if event=='enter' else list(self.board.keys())+['Stormsplitter']*sum(t.kind=='Stormsplitter' for t in self.tokens))
        for provider in providers:
            for e in self.cat.effects(provider,event):
                count=1
                if self.has('Harmonic Prodigy') and (self.wizard(provider) or 'Shaman' in self.cat.get(provider).get('subtypes',[])):
                    count+=1
                if event in ('cast_instant_sorcery','cast_noncreature','cast_or_copy_instant_sorcery') and self.has('Veyran, Voice of Duality'):
                    count+=1
                if e['op']=='create_token':self.add_tokens(e['token'],e.get('amount',1)*count)
                elif e['op']=='treasure':self.treasures+=e['amount']*count;self.note(f'    Trigger: {provider} creates {e["amount"]*count} Treasure(s); total {self.treasures}.')
                elif e['op']=='draw':self.draw(e['amount']*count)
                elif e['op']=='selection':self.select(e['method']) # only called on resolve directly below
                elif e['op']=='draw_discard':
                    self.draw(e['draw']*count);low=sorted(self.hand,key=self.value)[:e['discard']*count]
                    for c in low:self.hand.remove(c);self.grave.append(c)
                    self.note('    Draw/discard: '+str(low))
                elif e['op']=='tutor':
                    for _ in range(count):self.tutor(e['filter'])
                elif e['op']=='utility':pass
                else:raise ValueError('Unknown effect: '+str(e))
    def tutor(self,filter_name):
        if filter_name=='spell_mv_lte_2':
            opts=[c for c in self.deck if self.cat.type(c)=='spell' and self.cat.cost(c) and sum(self.cat.cost(c))<=2]
            # X is zero outside stack: Mathemagics qualifies, and other X costs in catalog qualify.
            opts.sort(key=lambda c: (c=='Mathemagics' and self.turn>=6,self.value(c)),reverse=True)
            if opts:
                c=opts[0];self.deck.remove(c);self.hand.append(c);self.rng.shuffle(self.deck);self.note('    Spellseeker tutored: '+c)
    def resolve_cost(self,name,buyback=False,x=0):
        cost=self.cat.cost(name)
        if cost is None:return None
        g,u,r=cost
        if name=='Magnus the Red':g+=2*self.magnus_casts
        if buyback:g+=self.cat.get(name).get('buyback_generic',0)
        if name in ('Mathemagics',):g+=2*x
        if name in ('Comet Storm',):g+=x
        # Permanent discounts are only for instant/sorcery, not artifacts, Wizards or activated abilities.
        if self.cat.type(name)=='spell':g=max(0,g-self.discount())
        return (g,u,r)
    def mana_sources(self,spell=False):
        src=[];lute=self.has('Resonating Lute')
        for i,(n,kind) in enumerate(self.lands):
            key=f'L{i}'
            if key in self.tapped:continue
            modes={'U':[(1,0,0,0,0)],'R':[(0,1,0,0,0)],'C':[(0,0,1,0,0)],'D':[(1,0,0,0,0),(0,1,0,0,0)]}[kind]
            if spell and lute:modes=modes+[(0,0,0,2,0),(0,0,0,0,2)]
            src.append(Source(key,'land',tuple(modes)))
        for n in self.board:
            if not self.cat.get(n).get('mana_rock') or 'A:'+n in self.tapped:continue
            profiles={'U':(1,0,0,0,0),'R':(0,1,0,0,0),'C':(0,0,1,0,0),'UR':(1,1,0,0,0),'CC':(0,0,2,0,0)}
            card_mana=self.cat.get(n).get('mana_production',{})
            modes=[profiles[k] for k in card_mana['modes']]
            src.append(Source('A:'+n,'signet' if card_mana.get('activation_generic') else 'rock',tuple(modes)))
        for i in range(self.treasures):src.append(Source('X'+str(i),'treasure',((1,0,0,0,0),(0,1,0,0,0),(0,0,1,0,0))))
        if spell and self.level('Sorcerer Class')>=2:
            for n,birth in self.board.items():
                if self.cat.type(n) not in ('creature','commander') or birth>=self.turn or 'C:'+n in self.tapped:continue
                src.append(Source('C:'+n,'class',((0,0,0,1,0),(0,0,0,0,1))))
            for t in self.tokens:
                if (t.birth<self.turn or t.haste) and 'T'+str(t.ident) not in self.tapped:
                    src.append(Source('T'+str(t.ident),'class',((0,0,0,1,0),(0,0,0,0,1))))
        if self.has('Phyrexian Altar'):
            for t in self.tokens:src.append(Source('T'+str(t.ident),'altar',((1,0,0,0,0),(0,1,0,0,0),(0,0,1,0,0))))
        return src
    def _remaining(self,pool,cost,spell,signet=False):
        # Signet activation can spend any one *ordinary* mana. Try each color
        # rather than greedily spending red required by the underlying spell.
        activation_choices=[None] if not signet else [i for i in (2,0,1) if pool[i]>0]
        for activation in activation_choices:
            p=list(pool);g,u,r=cost
            if activation is not None:p[activation]-=1
            if spell:
                use=min(u,p[3]);u-=use;p[3]-=use
                use=min(r,p[4]);r-=use;p[4]-=use
            if p[0]<u or p[1]<r:continue
            p[0]-=u;p[1]-=r
            for i in ((2,3,4,0,1) if spell else (2,0,1)):
                used=min(g,p[i]);g-=used;p[i]-=used
            if g==0:return tuple(p)
        return None
    def payment(self,name,buyback=False,x=0,spell_override=None,cost_override=None):
        cost=cost_override if cost_override is not None else self.resolve_cost(name,buyback,x)
        if cost is None:return None
        spell=self.cat.type(name)=='spell' if spell_override is None else spell_override
        sources=self.mana_sources(spell)
        # Cap only after explicitly warning. All modeled early-turn games normally fit the cap.
        if len(sources)>14:
            sources=sorted(sources,key=lambda s:({'land':0,'rock':1,'signet':2,'class':3,'treasure':4,'altar':5}[s.kind],s.key))[:14]
            self.unmodeled_seen.add('mana-source-cap')
        # DFS branch & bound. Scores penalize sacrificing tokens and Treasures.
        best=None;calls=0
        def rec(idx,pool,used,keys,signet):
            nonlocal best,calls
            calls+=1
            if calls>45000:return
            remaining=self._remaining(pool,cost,spell,signet)
            if remaining is not None:
                penalty=sum({'altar':100,'treasure':40,'class':7,'signet':2,'land':1,'rock':1}[s.kind] for s,m in used)
                rank=(penalty,len(used),-sum(remaining))
                if best is None or rank<best[0]:best=(rank,list(used),remaining)
                return
            if idx>=len(sources):return
            if best is not None and sum({'altar':100,'treasure':40,'class':7,'signet':2,'land':1,'rock':1}[s.kind] for s,m in used)>=best[0][0]:return
            s=sources[idx]
            if s.key not in keys:
                for mode in s.modes:
                    new=tuple(pool[j]+mode[j] for j in range(5))
                    rec(idx+1,new,used+[(s,mode)],keys|{s.key},signet or s.kind=='signet')
            rec(idx+1,pool,used,keys,signet)
        rec(0,self.floating,[],set(),False)
        if best is None:return None
        _,used,remaining=best
        return used,remaining,cost
    def pay(self,name,buyback=False,x=0,spell_override=None,cost_override=None):
        plan=self.payment(name,buyback,x,spell_override,cost_override)
        if not plan:return False
        used,remaining,cost=plan
        self.floating=remaining
        for s,m in used:
            if s.kind in ('treasure','altar'):continue
            self.tapped.add(s.key)
        self.treasures-=sum(s.kind=='treasure' for s,m in used)
        victims={int(s.key[1:]) for s,m in used if s.kind=='altar'}
        if victims:
            self.tokens=[t for t in self.tokens if t.ident not in victims]
            self.note(f'    Altar sacrificed {len(victims)} token(s) for mana; {len(self.tokens)} remain.')
        self.total_spent+=sum(cost)
        printed=self.cat.cost(name)
        if cost_override is None and printed and self.cat.type(name)=='spell':
            gross=printed[0]+self.cat.get(name).get('buyback_generic',0)*(buyback)+(2*x if name=='Mathemagics' else x if name=='Comet Storm' else 0)
            self.generic_saved+=max(0,gross-cost[0])
        detail=', '.join(s.key+':'+str(sum(m)) for s,m in used)
        self.note(f'    Pay {name}: {cost[0]} generic + {cost[1]}U + {cost[2]}R; sources [{detail}]; float {self.floating}.')
        return True
    def can_pay(self,name,buyback=False,x=0):return self.payment(name,buyback,x) is not None
    def can_pay_activated(self,cost):return self.payment('Sorcerer Class',spell_override=False,cost_override=tuple(cost)) is not None
    def pay_activated(self,cost):return self.pay('Sorcerer Class',spell_override=False,cost_override=tuple(cost))
    def cast(self,name,buyback=False,from_grave=False,x=0):
        if name not in (self.grave if from_grave else self.hand):return False
        typ=self.cat.type(name)
        if typ=='land' or typ=='commander':return False
        if self.cat.cost(name) is None:return False
        if from_grave:
            if not self.has('Underworld Breach') or len(self.grave)-self.grave.count(name)<3:return False
        if not self.pay(name,buyback,x):return False
        if from_grave:
            self.grave.remove(name)
            expend=[c for c in self.grave if c not in ('Mathemagics','Searing Touch','Mystic Speculation')][:3]
            if len(expend)<3:expend=self.grave[:3]
            for c in expend:self.grave.remove(c);self.exile.append(c)
            self.note('    Escape exiled from graveyard: '+', '.join(expend))
        else:self.hand.remove(name)
        self.actions+=1
        if typ=='spell':
            self.instant_sorcery_cast+=1
            self.note(f'  Cast {name}'+(' with buyback' if buyback else '')+(' via escape' if from_grave else '')+'.')
            self.event('cast_instant_sorcery',name,zone='grave' if from_grave else 'hand')
            self.event('cast_noncreature',name)
            self.event('cast_or_copy_instant_sorcery',name)
            if from_grave:self.event('cast_from_outside_hand',name)
            for eff in self.cat.effects(name,'resolve'):
                if eff['op']=='selection':self.select(eff['method']);self.selection_cast+=1
                elif eff['op']=='utility':self.note('    Utility target/effect not fully adjudicated ('+eff['method']+').')
            if buyback:self.hand.append(name)
            else:self.grave.append(name)
        else:
            if from_grave:self.event('cast_from_outside_hand',name,zone='grave')
            self.board[name]=self.turn
            if typ=='permanent' and self.has('Third Path Iconoclast') and name!='Third Path Iconoclast':
                self.event('cast_noncreature',name)
            self.note('  Cast '+name+ (' [partial behavior]' if self.cat.supported(name)=='partial' else '')+'.')
            self.event('enter',name)
            if name=='Sorcerer Class':self.class_levels[name]=1
            if name=='Underworld Breach':self.note('    Breach available until this end step.')
            if name=='Magnus the Red':raise AssertionError('Use cast_commander')
            if 'ramp' in self.cat.tags(name):self.ramp_cast+=1
        return True
    def cast_commander(self):
        if self.has_magnus() or not self.can_pay('Magnus the Red'):return False
        if not self.pay('Magnus the Red'):return False
        self.board['Magnus the Red']=self.turn;self.magnus_casts+=1
        self.actions+=1
        if self.first_magnus is None:self.first_magnus=self.turn
        self.note('  Cast MAGNUS THE RED from command zone.')
        self.event('cast_from_outside_hand','Magnus the Red',zone='command')
        return True
    def play_land(self):
        choices=[n for n in self.hand if self.cat.type(n)=='land']
        if not choices:return False
        u=sum(k in ('U','D') for n,k in self.lands);r=sum(k in ('R','D') for n,k in self.lands)
        def kind(n):
            profile=self.cat.get(n).get('land_profile','D')
            if profile=='pathway':return 'U' if u<2 else 'R'
            if profile=='fetch':return 'U' if u<2 else 'R'
            return profile
        def tapped(n):
            if n=='Stormcarved Coast':return len(self.lands)<2
            if n=='Sulfur Falls':return not any(c in ('Island','Mountain','Steam Vents') for c,k in self.lands)
            if n=='Spirebluff Canal':return len(self.lands)>=3
            if n=='Mystic Sanctuary':return sum(c in ('Island','Steam Vents') for c,k in self.lands)<3
            return False
        choices.sort(key=lambda n:(not tapped(n),kind(n)=='D',kind(n)=='U' and u<2,kind(n)=='R' and r<1),reverse=True)
        n=choices[0];self.hand.remove(n)
        if n=='Fabled Passage':
            basic='Island' if u<2 else 'Mountain'
            if basic in self.deck:self.deck.remove(basic);self.rng.shuffle(self.deck)
            n=basic;tap=True # Fabled Passage enters its fetched land tapped unless four lands already controlled (simplified)
            if len(self.lands)>=3:tap=False
        else:tap=tapped(n)
        i=len(self.lands);self.lands.append((n,kind(n)))
        if tap:self.tapped.add('L'+str(i))
        self.note(f'  Land: {n}'+(' (tapped)' if tap else '')+'.')
        return True
    def new_turn(self,turn):
        self.turn=turn;self.tapped=set();self.floating=(0,0,0,0,0)
        self.note(f'\nTURN {turn} [opening hand={len(self.hand)} cards]' if turn==1 else f'\nTURN {turn}')
        self.draw()
        self.play_land()
    def end_turn(self):
        self.tokens=[t for t in self.tokens if not t.expires]
        if self.has('Underworld Breach'):
            del self.board['Underworld Breach'];self.grave.append('Underworld Breach');self.note('  End step: sacrifice Underworld Breach.')
        self.floating=(0,0,0,0,0)
        self.turn_stats[self.turn]={
            'magnus':self.has_magnus(),'engines':self.engine_count(),'tokens':self.token_count(),'wizards':self.wizards(),
            'rocks':sum('ramp' in self.cat.tags(c) for c in self.board),'hand':len(self.hand),
            'selection_cast':self.selection_cast,'spell_cast':self.instant_sorcery_cast,
            'mana_spent':self.total_spent,'generic_saved':self.generic_saved,'treasures':self.treasures,
            'available_defense':self.defense_ready()
        }
        self.note('  End: lands '+str(len(self.lands))+', rocks '+str(self.turn_stats[self.turn]['rocks'])+', engines '+str(self.engine_count())+', tokens '+str(self.token_count())+', hand '+str(len(self.hand))+', grave '+str(len(self.grave))+'.')
    def activate(self,name,ability_id):
        if name not in self.board:return False
        abil=next((a for a in self.cat.get(name).get('activated_abilities',[]) if a['id']==ability_id),None)
        if not abil:return False
        if abil.get('mana_cost') and not self.pay_activated(abil['mana_cost']):return False
        if abil.get('cost',{}).get('tap_self'):
            if self.board[name]>=self.turn or 'C:'+name in self.tapped:return False
            self.tapped.add('C:'+name)
        if abil['effect']=='class_level':
            if self.level(name)!=abil['level']-1:return False
            self.class_levels[name]=abil['level'];self.note(f'  Activate {name} -> level {abil["level"]}.');return True
        if abil['effect']=='draw_discard':
            self.note(f'  Activate {name}: draw {abil["draw"]}, discard {abil["discard"]}.')
            self.draw(abil['draw'])
            for _ in range(abil['discard']):
                if not self.hand:break
                low=min(self.hand,key=self.value);self.hand.remove(low);self.grave.append(low);self.note('    Discard: '+low)
            return True
        # Counter abilities require an opponent's spell; handled by dedicated reaction logic.
        return False
    def untapped_wizard_keys(self):
        result=[]
        for c in self.board:
            if self.cat.type(c) in ('creature','commander') and self.wizard(c) and 'C:'+c not in self.tapped:result.append('C:'+c)
        for t in self.tokens:
            if (t.kind in ('Wizard','Stormsplitter') or self.has('Arcane Adaptation') or self.has('Maskwood Nexus')) and 'T'+str(t.ident) not in self.tapped:
                result.append('T'+str(t.ident))
        return result
    def defense_ready(self):
        for n in ('Swan Song',"An Offer You Can't Refuse",'Counterspell','Arcane Denial'):
            if n in self.hand and self.can_pay(n):return True
        if self.has('Voidmage Prodigy') and self.untapped_wizard_keys() and self.can_pay_activated([0,2,0]):return True
        if self.has('Patron Wizard') and len(self.untapped_wizard_keys())>=3:return True
        return False
    def opponent_removal(self):
        target='Magnus the Red' if self.has_magnus() else next((c for c in self.board if 'early_engine' in self.cat.tags(c) or 'token_engine' in self.cat.tags(c)),None)
        if target is None:return
        self.disruption_target=target;self.note('  OPPONENT: casts targeted creature removal at '+target+'.')
        for c in ('Swan Song',"An Offer You Can't Refuse",'Counterspell','Arcane Denial'):
            if c in self.hand and self.can_pay(c):
                self.cast(c);self.disruption_stopped=True;self.note('  RESPONSE: countered removal with '+c+'.');return
        if self.has('Voidmage Prodigy') and self.untapped_wizard_keys() and self.can_pay_activated([0,2,0]):
            # Sacrifice Wizard as cost, tapping not required. Use expendable Wizard token first.
            choices=self.untapped_wizard_keys()
            if self.pay_activated([0,2,0]):
                token=next((k for k in choices if k.startswith('T')),None)
                if token:
                    ident=int(token[1:]);self.tokens=[t for t in self.tokens if t.ident!=ident]
                    self.note('  RESPONSE: Voidmage sacrifices Wizard token to counter removal.')
                else:
                    creature=next(k for k in choices if k.startswith('C:'))[2:]
                    del self.board[creature]
                    self.note('  RESPONSE: Voidmage sacrifices '+creature+' to counter removal.')
                self.disruption_stopped=True;return
        if self.has('Patron Wizard') and len(self.untapped_wizard_keys())>=3:
            # Assumed opponent has 2 available generic mana.
            keys=self.untapped_wizard_keys()[:3];self.tapped.update(keys)
            self.disruption_stopped=True;self.note('  RESPONSE: Patron Wizard taps three Wizards, tax 3 vs opponent 2 mana.');return
        del self.board[target]
        self.note('  RESULT: '+target+' removed.')
    def summary(self):
        return {'seed':self.seed,'policy':self.policy,'scenario':self.scenario,'first_magnus':self.first_magnus,'turns':self.turn_stats,'selection_cast':self.selection_cast,'spells_cast':self.instant_sorcery_cast,'total_mana_paid':self.total_spent,'generic_saved':self.generic_saved,'first_combo':self.first_combo,'combo_events':self.combo_events,'mulligans':self.mulligans,'disruption_target':self.disruption_target,'disruption_stopped':self.disruption_stopped,'unmodeled_seen':sorted(self.unmodeled_seen),'trace':self.log if self.trace else []}
