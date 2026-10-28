#!/usr/bin/env python3
"""Magnus v1.6: transparent, rules-aware *partial* early-game simulator.

One uniform greedy pilot; only Magnus deployment policy changes. Not an MTG rules
engine or a win-rate model. See accompanying report / --help.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations
import argparse, json, random, statistics

ROOT=Path(__file__).parent
DECK=ROOT/'magnus_thousand_sons_v1_6.txt'

def read_deck(path=DECK):
    library=[]; section=''
    for line in path.read_text().splitlines():
        if line.startswith('Commander ('): section='cmd'
        elif line.startswith('Creatures ('): section='creature'
        elif line.startswith('Artifacts and Enchantments ('): section='permanent'
        elif line.startswith('Instants and Sorceries ('): section='spell'
        elif line.startswith('Lands ('): section='land'
        elif line[:1].isdigit() and section:
            parts=line.split(' ',1)
            if len(parts)==2 and parts[0].isdigit():
                library.extend([(parts[1],section)]*int(parts[0]))
    assert len(library)==100 and library.count(('Magnus the Red','cmd'))==1
    return [n for n,t in library if t!='cmd'],{n:t for n,t in library}
LIB, TYPE=read_deck()
LAND={n for n,t in TYPE.items() if t=='land'}
ROCK={'Sol Ring','Arcane Signet','Izzet Signet','Talisman of Creativity','Fellwar Stone','Mind Stone'}
CANTRIP={'Brainstorm','Ponder','Preordain','Telling Time','Impulse','Frantic Search','Mystic Speculation'}
COUNTER={"An Offer You Can't Refuse",'Swan Song','Flusterstorm','Counterspell','Arcane Denial'}
SELECTION={'Brainstorm','Ponder','Preordain','Telling Time','Impulse','Frantic Search'}
CREATURES={n for n,t in TYPE.items() if t=='creature'}
WIZARDS={'Harmonic Prodigy','Archmage Emeritus','Patron Wizard','Voidmage Prodigy','Spellseeker','Veyran, Voice of Duality','Baral, Chief of Compliance','Dualcaster Mage','Stormsplitter',"Jace, Vryn's Prodigy",'Goblin Electromancer','Sigil Tracer','Docent of Perfection'}
SHAMANS={'Young Pyromancer','Storm-Kiln Artist','Tzaangor Shaman'}
TOKEN_ENGINES={'Young Pyromancer','Third Path Iconoclast','Docent of Perfection','Stormsplitter','The Lost and the Damned'}
UTILITY_ENGINES={'Goblin Electromancer','Baral, Chief of Compliance',"Jace, Vryn's Prodigy",'Harmonic Prodigy','Storm-Kiln Artist','Patron Wizard','Voidmage Prodigy','Sorcerer Class','Phyrexian Altar','Sigil Tracer','Archmage Emeritus','Spellseeker'}
# (generic, blue, red); cards outside this subset are tracked in hand as inert.
COST={
 'Sol Ring':(1,0,0),'Arcane Signet':(2,0,0),'Izzet Signet':(2,0,0),
 'Talisman of Creativity':(2,0,0),'Fellwar Stone':(2,0,0),'Mind Stone':(2,0,0),
 'Magnus the Red':(3,1,1),'Young Pyromancer':(1,0,1),
 'Third Path Iconoclast':(0,1,1),'Goblin Electromancer':(0,1,1),
 'Baral, Chief of Compliance':(1,1,0),"Jace, Vryn's Prodigy":(1,1,0),
 'Harmonic Prodigy':(1,0,1),'Voidmage Prodigy':(0,2,0),
 'Sigil Tracer':(1,2,0),'Patron Wizard':(0,3,0),'Spellseeker':(2,1,0),
 'Stormsplitter':(3,0,1),'Storm-Kiln Artist':(3,0,1),
 'Veyran, Voice of Duality':(1,1,1),'Archmage Emeritus':(2,2,0),
 'Docent of Perfection':(3,2,0),'Sorcerer Class':(0,1,1),
 'Phyrexian Altar':(3,0,0),'The Lost and the Damned':(1,1,1),
 'Arcane Adaptation':(2,1,0),'Maskwood Nexus':(4,0,0),
 'Resonating Lute':(2,1,1),
 'Brainstorm':(0,1,0),'Ponder':(0,1,0),'Preordain':(0,1,0),
 'Telling Time':(1,1,0),'Impulse':(1,1,0),'Frantic Search':(2,1,0),
 'Mystic Speculation':(0,1,0),
 'Searing Touch':(0,0,1),'Capsize':(1,2,0),
 'Counterspell':(0,2,0),'Arcane Denial':(1,1,0),
 'Flusterstorm':(0,1,0),'Swan Song':(0,1,0),
 "An Offer You Can't Refuse":(0,1,0)
}
# Model includes 6 rocks, repeatable creature/spell engines, common selection,
# selected graveyard/late-game payoffs only as *cards* (not fully resolved).

@dataclass(frozen=True)
class Source:
    sid:str
    modes:tuple[tuple[int,int,int], ...] # U,R,C output
    restricted:bool=False
    sacrifice:bool=False
    kind:str='land'

def land_kind(name,lands):
    if name in {'Island','Otawara, Soaring City','Mystic Sanctuary'}:return 'U'
    if name in {'Mountain','Sokenzan, Crucible of Defiance'}:return 'R'
    if name=='Riptide Laboratory':return 'C'
    if name=='Fabled Passage':return 'fetch'
    if name=='Cascade Bluffs':return 'dual_approx' # filter requires input: simplifying
    if name=='Riverglide Pathway':return 'pathway'
    return 'D'

def enters_tapped(name,existing):
    if name=='Mystic Sanctuary':return sum(x in {'Island','Steam Vents'} for x in existing)<3
    if name=='Stormcarved Coast':return len(existing)<2
    if name=='Sulfur Falls':return not any(x in {'Island','Mountain','Steam Vents'} for x in existing)
    if name=='Spirebluff Canal':return len(existing)>=3
    return False

def score_card(card,turn,game):
    lands=len(game.lands)
    if card in LAND: return 22 if lands<min(5,turn) else 11 if lands<6 else 3
    if card in ROCK:return 18 if turn<=4 else 11 if turn<=6 else 5
    if card in {'Young Pyromancer','Third Path Iconoclast'}:return 14
    if card in {'Goblin Electromancer','Baral, Chief of Compliance',"Jace, Vryn's Prodigy"}:return 13
    if card in COUNTER:return 13 if turn>=4 else 8
    if card in {'Harmonic Prodigy','Storm-Kiln Artist','Patron Wizard','Voidmage Prodigy','Sigil Tracer'}:return 11
    if card in {'Sorcerer Class','Phyrexian Altar'}:return 10
    if card in {'Spellseeker','Archmage Emeritus','Stormsplitter'}:return 9
    if card in SELECTION:return 11 if len(game.lands)<4 else 9
    if card=='Mathemagics':return 9
    if card in {'Capsize','Searing Touch','Mystic Speculation'}:return 7
    return 5

class Game:
    def __init__(self,policy,seed,removal=False):
        self.policy=policy;self.rng=random.Random(seed); self.deck=LIB.copy();self.rng.shuffle(self.deck)
        self.hand=[];self.mull=0
        for attempt in range(2):
            self.hand=self.deck[:7];self.deck=self.deck[7:]
            land_count=sum(x in LAND for x in self.hand)
            if (land_count in (0,1,5,6,7)) and attempt==0:
                self.mull+=1;self.deck=LIB.copy();self.rng.shuffle(self.deck);continue
            break
        self.turn=0;self.lands=[];self.board={};self.rocks={};self.tapped=set()
        self.tokens=[] # (kind, birth turn, haste, expiry turn or None)
        self.treasures=0;self.grave=[];self.scry_buffer=[]
        self.level=0;self.magnus=False;self.magnus_birth=None;self.commander_casts=0
        self.first_opportunity=None;self.first_cast=None
        self.magnus_arrival_engine=False;self.magnus_arrival_tokens=0
        self.magnus_arrival_protected=False;self.magnus_arrival_engine_protected=False
        self.removal=removal;self.removal_target=None;self.removal_stopped=False
        self.tmetrics={};self.spells=0;self.spells_after_magnus=0;self.selection_used=0
        self.sources_spent=0;self.total_sources=0;self.post_magnus_token_growth=0
        self.float={'U':0,'R':0,'C':0,'SU':0,'SR':0}
        self.turn_mana_actions=Counter();self.did_magnus_this_turn=False
        self.mana_paid=Counter();self.discount_saved=0;self.treasures_made=0
        self.missed_engine_cards=0
    def draw(self,n=1):
        for _ in range(n):
            if self.deck:self.hand.append(self.deck.pop(0))
    def available_wizards(self):
        transform='Arcane Adaptation' in self.board or 'Maskwood Nexus' in self.board
        wiz=[n for n in self.board if n in CREATURES and (n in WIZARDS or transform)]
        types=[t for t in self.tokens if t[0]=='wizard' or transform]
        return len(wiz)+len(types)
    def live_tokens(self):return len(self.tokens)
    def has_engine(self):return bool(set(self.board)&(TOKEN_ENGINES|UTILITY_ENGINES))
    def token_engine(self):return bool(set(self.board)&TOKEN_ENGINES)
    def discount(self):return int('Baral, Chief of Compliance' in self.board)+int('Goblin Electromancer' in self.board)+(self.live_tokens() if self.magnus else 0)
    def resolved_cost(self,card,spell=False,buyback=False):
        g,u,r=COST[card]
        if card=='Magnus the Red':g+=2*self.commander_casts
        if buyback:g+= {'Mystic Speculation':2,'Searing Touch':4,'Capsize':3}.get(card,0)
        if spell:g=max(0,g-self.discount())
        return (g,u,r)
    def add_land(self):
        opts=[x for x in self.hand if x in LAND]
        if not opts:return
        existing=[x[0] for x in self.lands]
        have_u=sum(1 for n,m,t in self.lands if m in ('U','D'))
        have_r=sum(1 for n,m,t in self.lands if m in ('R','D'))
        def value(n):
            color=land_kind(n,existing)
            return (0 if enters_tapped(n,existing) else 20)+(5 if color=='D' else 4 if (color=='U' and have_u<2 or color=='R' and have_r<1) else 1)
        x=max(opts,key=value);self.hand.remove(x)
        kind=land_kind(x,existing)
        tapped=enters_tapped(x,existing)
        if kind=='fetch':
            kind='U' if have_u<2 else 'R'
            self.deck.remove('Island' if kind=='U' else 'Mountain') if ('Island' if kind=='U' else 'Mountain') in self.deck else None
            x='Island' if kind=='U' else 'Mountain'
            tapped=len(self.lands)<3
            self.rng.shuffle(self.deck)
        if kind=='pathway':kind='U' if have_u<2 else 'R'
        if kind=='dual_approx':kind='D'
        self.lands.append((x,kind,tapped))
        if tapped:self.tapped.add(f'L{len(self.lands)-1}')
    def sources(self,spell=False):
        S=[];lute='Resonating Lute' in self.board
        for i,(name,kind,_) in enumerate(self.lands):
            sid=f'L{i}'
            if sid in self.tapped:continue
            mods={'U':((1,0,0),),'R':((0,1,0),),'C':((0,0,1),),'D':((1,0,0),(0,1,0))}[kind]
            S.append(Source(sid,mods,False,False,'land'))
            # Lute adds a separate tap ability to lands. Can't use it for creatures or activated abilities.
            if lute and spell:S[-1]=Source(sid,mods+((2,0,0),(0,2,0)),False,False,'land')
        for n in self.rocks:
            if n in self.tapped:continue
            if n=='Sol Ring':m=((0,0,2),)
            elif n=='Mind Stone':m=((0,0,1),)
            elif n=='Izzet Signet':continue # modeled separately as UR output at cost of one conventional mana
            else:m=((1,0,0),(0,1,0)) # Fellwar Stone assumes access to U/R; opponent dependent
            S.append(Source('A:'+n,m,False,False,'rock'))
        for i in range(self.treasures):S.append(Source(f'T{i}',((1,0,0),(0,1,0),(0,0,1)),False,True,'treasure'))
        if spell and self.level>=2:
            for c,birth in self.board.items():
                if c in CREATURES and birth<self.turn and 'C:'+c not in self.tapped:
                    S.append(Source('C:'+c,((1,0,0),(0,1,0)),True,False,'creature'))
            for idx,t in enumerate(self.tokens):
                if (t[1]<self.turn or t[2]) and f'K{idx}' not in self.tapped:
                    S.append(Source(f'K{idx}',((1,0,0),(0,1,0)),True,False,'token'))
        if 'Phyrexian Altar' in self.board:
            for idx,t in enumerate(self.tokens):
                S.append(Source(f'K{idx}',((1,0,0),(0,1,0),(0,0,1)),False,True,'altar'))
        return S
    def try_pay(self,card,spell=False,buyback=False,execute=False,protect=False):
        g,u,r=self.resolved_cost(card,spell,buyback)
        if g+u+r==0:return True
        src=self.sources(spell)
        # State-space search: tap sources with chosen modes. Distinct sources may share a token ID
        # (Sorcerer Class tap versus Altar sacrifice); can use only one mode per token.
        # Signet modeled by separately considering one activator source consumed for its UR output.
        signet='Izzet Signet' in self.rocks and 'A:Izzet Signet' not in self.tapped
        candidates=[]
        sources0=src
        if signet:
            for act in src:
                if act.restricted or act.kind=='altar':continue
                for mode in act.modes:
                    if sum(mode)>=1 and not (act.kind=='land' and 'Resonating Lute' in self.board and sum(mode)>1):
                        # Consume one mana to activate, retaining remainder; prefer generic for payment.
                        v=list(mode)
                        for col in (2,0,1):
                            if v[col]>0:
                                v[col]-=1;break
                        candidates.append((Source('A:Izzet Signet',((v[0]+1,v[1]+1,v[2]),),False,False,'signet'),act.sid))
        # DFS includes skip: search modest number of early/midgame mana sources; cap at 13.
        def feasible(U,R,C,SU,SR):
            # Does available mana pay colored requirements and remaining generic?
            if spell:
                if U+SU<u or R+SR<r:return False
                return U+R+C+SU+SR >=u+r+g
            return U>=u and R>=r and U+R+C >=u+r+g
        def consume(U,R,C,SU,SR):
            # First spend spell-restricted mana to avoid silently accelerating creatures.
            cu=min(SU,u) if spell else 0;SU-=cu;remu=u-cu;U-=remu
            cr=min(SR,r) if spell else 0;SR-=cr;remr=r-cr;R-=remr
            generic=g
            for k in ('C','SU','SR','U','R'):
                if k in ('SU','SR') and not spell:continue
                v={'C':C,'SU':SU,'SR':SR,'U':U,'R':R}[k]
                amt=min(v,generic);generic-=amt
                if k=='C':C-=amt
                elif k=='SU':SU-=amt
                elif k=='SR':SR-=amt
                elif k=='U':U-=amt
                elif k=='R':R-=amt
            assert generic==0 and min(U,R,C,SU,SR)>=0
            return {'U':U,'R':R,'C':C,'SU':SU,'SR':SR}
        def solve(sequence,consumed=frozenset()):
            best=None;calls=0
            order=sorted(sequence,key=lambda s:(s.kind in ('altar','treasure'),s.kind in ('creature','token'),len(s.modes)>1,-max(sum(x) for x in s.modes)))
            # Branch and bound: once a mana payment is found, minimize source taps.
            def rec(i,U,R,C,SU,SR,used,seen):
                nonlocal best,calls
                calls+=1
                if calls>18000:return
                if feasible(U,R,C,SU,SR):
                    score=(len(used),sum(s.kind in ('altar','treasure') for s,m in used),sum(s.kind in ('creature','token') for s,m in used),-sum(sum(m) for s,m in used))
                    if best is None or score<best[0]:best=(score,list(used),(U,R,C,SU,SR))
                    return
                if i>=len(order) or (best and len(used)>=best[0][0]):return
                # Bound on available future total mana; prevents hopeless skip branches.
                maximum=sum(max(sum(m) for m in source.modes) for source in order[i:])
                if U+R+C+SU+SR+maximum<g+u+r:return
                s=order[i]
                if s.sid in seen or s.sid in consumed:
                    rec(i+1,U,R,C,SU,SR,used,seen);return
                # Try actual taps ahead of skipping for rapid feasible-plan discovery.
                for m in s.modes:
                    locked=s.restricted or (s.kind=='land' and 'Resonating Lute' in self.board and sum(m)==2)
                    if locked:
                        rec(i+1,U,R,C,SU+m[0],SR+m[1],used+[(s,m)],seen|{s.sid})
                    else:
                        rec(i+1,U+m[0],R+m[1],C+m[2],SU,SR,used+[(s,m)],seen|{s.sid})
                rec(i+1,U,R,C,SU,SR,used,seen)
            # Mana already floating from previous taps remains available this phase.
            f=self.float
            rec(0,f['U'],f['R'],f['C'],f['SU'] if spell else 0,f['SR'] if spell else 0,[],frozenset())
            return best
        # Targeted source cap avoids exponential blowups in very wide token boards.
        if len(sources0)>13:
            sources0=sorted(sources0,key=lambda s:(s.kind=='altar',s.kind=='creature',s.kind=='treasure'))[:13]
        results=[]
        found=solve(sources0)
        if found:results.append(found)
        if signet:
            for virtual,activator in candidates[:12]:
                others=[s for s in sources0 if s.sid!=activator and s.sid!='A:Izzet Signet']
                x=solve(others+[virtual],frozenset({activator}))
                if x:results.append((x[0],x[1]+[(Source(activator,(),False,False,'signet_activator'),(0,0,0))],x[2]))
        if not results:return False
        score,plan,available=min(results,key=lambda x:x[0])
        if protect and not self._protection_after_plan(plan):return False
        if not execute:return True
        used={s.sid for s,m in plan}
        self.tapped.update(sid for sid in used if not sid.startswith('T') and not (sid.startswith('K') and any(s.kind=='altar' and s.sid==sid for s,m in plan)))
        remaining=consume(*available)
        if not spell:
            remaining['SU']=self.float['SU'];remaining['SR']=self.float['SR']
        self.float=remaining
        self.mana_paid[self.turn]+=g+u+r
        if spell:self.discount_saved+=max(0,COST[card][0]+(3 if buyback and card=='Capsize' else 4 if buyback and card=='Searing Touch' else 2 if buyback and card=='Mystic Speculation' else 0)-g)
        self.treasures-=sum(s.kind=='treasure' for s,m in plan)
        self.sources_spent+=len(used)
        sacrifice=[int(s.sid[1:]) for s,m in plan if s.kind=='altar']
        for i in sorted(set(sacrifice),reverse=True):
            if i<len(self.tokens):del self.tokens[i]
        return True
    def _protection_after_plan(self,plan):
        # For policy comparison, any held inexpensive counter with an unused blue source suffices.
        used={s.sid for s,m in plan}
        return any(c in self.hand for c in COUNTER) and any(s.sid not in used and any(x[0] for x in s.modes) for s in self.sources(True))
    def protect_available(self):
        for c in self.hand:
            if c in COUNTER and self.try_pay(c,spell=True):return True
        # Voidmage: sacrifice a Wizard (itself qualifies) and pay UU.
        if 'Voidmage Prodigy' in self.board and self.available_wizards()>=1:
            # Candidate evaluation through a virtual spell with UU (no cost discount).
            if self.mana_for_UU():return True
        if 'Patron Wizard' in self.board and self.available_wizards()>=3:return True
        return False
    def mana_for_UU(self):
        return any(self.try_pay(c,spell=False) for c in ('Counterspell',) if c in COST)
    def smart_select(self,n):
        def val(c):return score_card(c,self.turn,self)
        if n=='Ponder':
            peek=self.deck[:3];del self.deck[:3]
            peek.sort(key=val,reverse=True)
            if peek and val(peek[0])<7:
                self.deck=peek+self.deck;self.rng.shuffle(self.deck)
            else:self.deck=peek+self.deck
            self.draw()
        elif n=='Preordain':
            peek=self.deck[:2];del self.deck[:2]
            good=[c for c in peek if val(c)>=8]; bad=[c for c in peek if c not in good]
            self.deck=sorted(good,key=val,reverse=True)+self.deck+bad;self.draw()
        elif n=='Brainstorm':
            self.draw(3)
            low=sorted(self.hand,key=val)[:2]
            for c in low:self.hand.remove(c)
            self.deck=low+self.deck
        elif n=='Telling Time':
            peek=self.deck[:3];del self.deck[:3]
            peek.sort(key=val,reverse=True)
            if peek:self.hand.append(peek[0])
            if len(peek)>1:self.deck=peek[1:2]+self.deck+peek[2:]
        elif n=='Impulse':
            peek=self.deck[:4];del self.deck[:4]
            peek.sort(key=val,reverse=True)
            if peek:self.hand.append(peek[0]);self.deck+=peek[1:]
        elif n=='Frantic Search':
            self.draw(2)
            for c in sorted(self.hand,key=val)[:2]:self.hand.remove(c);self.grave.append(c)
            # untap up to three lands, only those already tapped
            land_ids=[f'L{i}' for i in range(len(self.lands)) if f'L{i}' in self.tapped]
            for k in land_ids[:3]:self.tapped.remove(k)
        elif n=='Mystic Speculation':
            peek=self.deck[:3];del self.deck[:3]
            good=[c for c in peek if val(c)>=8];bad=[c for c in peek if c not in good]
            self.deck=sorted(good,key=val,reverse=True)+self.deck+bad
    def add_token(self,kind='other',count=1,haste=False,expiry=None):
        for _ in range(count):self.tokens.append((kind,self.turn,haste,expiry))
    def noncreature_trigger(self,card,from_grave=False):
        self.spells+=1
        if self.magnus:self.spells_after_magnus+=1
        harmonic='Harmonic Prodigy' in self.board
        if 'Young Pyromancer' in self.board:self.add_token(count=2 if harmonic else 1)
        if 'Third Path Iconoclast' in self.board:self.add_token()
        if 'Docent of Perfection' in self.board:self.add_token(kind='wizard')
        if 'Stormsplitter' in self.board:self.add_token('wizard',2 if harmonic else 1,haste=True,expiry=self.turn)
        if 'Storm-Kiln Artist' in self.board:
            amount=2 if harmonic else 1
            self.treasures+=amount;self.treasures_made+=amount
        if 'Archmage Emeritus' in self.board:self.draw(2 if harmonic else 1)
        if from_grave and 'The Lost and the Damned' in self.board:self.add_token()
    def cast_card(self,n,kind='permanent',buyback=False):
        if n not in self.hand or n not in COST:return False
        typ=TYPE.get(n)
        spell=typ=='spell'
        if not self.try_pay(n,spell=spell,buyback=buyback,execute=True):return False
        self.hand.remove(n)
        if spell:
            self.noncreature_trigger(n)
            self.smart_select(n)
            if not buyback:self.grave.append(n)
            else:self.hand.append(n)
            if n in SELECTION:self.selection_used+=1
        else:
            if 'Third Path Iconoclast' in self.board and TYPE.get(n)=='permanent':self.add_token()
            if n in ROCK:self.rocks[n]=self.turn
            else:self.board[n]=self.turn
            if n=='Sorcerer Class':
                self.level=1;self.draw(2)
                for c in sorted(self.hand,key=lambda c:score_card(c,self.turn,self))[:2]:
                    self.hand.remove(c);self.grave.append(c)
            if n=='Spellseeker':
                # Tutor instant/sorcery mana value <=2, including Mathemagics (X=0 in library).
                eligible=[c for c in self.deck if c in {'Preordain','Brainstorm','Mystic Speculation','Searing Touch','Mathemagics','Counterspell','Swan Song'}]
                if eligible:
                    desired='Mathemagics' if self.turn>=6 and 'Mathemagics' not in self.hand else 'Preordain' if 'Preordain' in eligible else eligible[0]
                    if desired not in eligible:desired=eligible[0]
                    self.deck.remove(desired);self.hand.append(desired);self.rng.shuffle(self.deck)
        self.turn_mana_actions[self.turn]+=1
        return True
    def try_jace(self):
        n="Jace, Vryn's Prodigy"
        if n in self.board and self.board[n]<self.turn and 'C:'+n not in self.tapped:
            self.tapped.add('C:'+n);self.draw(1)
            if self.hand:
                c=min(self.hand,key=lambda x:score_card(x,self.turn,self));self.hand.remove(c);self.grave.append(c)
            # No flip modeled: Jace transform at five in graveyard would be important later.
    def play_magnus(self):
        if self.magnus:return False
        if not self.try_pay('Magnus the Red',execute=True):return False
        self.magnus=True;self.magnus_birth=self.turn;self.commander_casts+=1
        if self.first_cast is None:self.first_cast=self.turn
        self.magnus_arrival_engine=self.has_engine()
        self.magnus_arrival_tokens=self.live_tokens()
        self.magnus_arrival_protected=self.protect_available()
        self.magnus_arrival_engine_protected=self.has_engine() and self.magnus_arrival_protected
        if 'The Lost and the Damned' in self.board:self.add_token()
        self.turn_mana_actions[self.turn]+=1
        return True
    def play_rocks(self):
        # Shared across policies. Prefer Sol Ring and rocks providing colored mana.
        preferred=['Sol Ring','Arcane Signet','Talisman of Creativity','Fellwar Stone','Izzet Signet','Mind Stone']
        for c in preferred:
            if c in self.hand:self.cast_card(c)
    def play_selection(self,early=False):
        order=['Preordain','Ponder','Brainstorm','Telling Time','Impulse','Frantic Search']
        count=0
        for c in order:
            if c not in self.hand:continue
            mana_short=len(self.lands)<min(self.turn,5)
            # Spend spare early mana on selection, not just when already short on lands.
            if self.magnus and self.turn==self.magnus_birth and self.protect_available():
                # Don't lose ready defense simply to draw one card.
                if self._spend_protection_if_cast(c):continue
            if self.cast_card(c):count+=1
            if count>=2:break
    def _spend_protection_if_cast(self,card):
        # Conservative heuristic: don't cast selection when we have just 1-2 untapped mana sources
        return len(self.sources(True))<=2
    def play_engines(self):
        priority=['Young Pyromancer','Third Path Iconoclast','Goblin Electromancer','Baral, Chief of Compliance',
            "Jace, Vryn's Prodigy",'Harmonic Prodigy','Sorcerer Class','Voidmage Prodigy',
            'Storm-Kiln Artist','Sigil Tracer','Patron Wizard','Phyrexian Altar',
            'Spellseeker','Stormsplitter','Archmage Emeritus','Docent of Perfection',
            'Resonating Lute','Arcane Adaptation','The Lost and the Damned','Maskwood Nexus']
        for c in priority:
            if c not in self.hand:continue
            if self.turn<=3 and sum(COST[c])>3:continue
            if self.turn<=4 and sum(COST[c])>4:continue
            if self.magnus and self.turn==self.magnus_birth and self.protect_available() and len(self.sources())<=2:continue
            self.cast_card(c)
    def spell_engine(self):
        # Utility casts when not needed for card selection: modeled once per turn; no infinite loops.
        if self.turn<=3:return
        if 'Mystic Speculation' in self.hand and (self.token_engine() or self.magnus):
            self.cast_card('Mystic Speculation',buyback=self.magnus and self.discount()>=2)
        if 'Searing Touch' in self.hand and (self.token_engine() or 'Storm-Kiln Artist' in self.board):
            self.cast_card('Searing Touch',buyback=self.magnus and self.discount()>=4)
    def class_upgrade(self):
        if self.level==1 and self.turn>=4 and self.available_wizards()+self.live_tokens()>=2:
            # Level 2 costs 3U and is a sorcery-speed activated ability; no Magnus discount.
            if self.pay_custom((3,1,0)):
                self.level=2;return True
        return False
    def pay_custom(self,cost):
        # Reuse cost planner without permanent modification of COST at call-site.
        COST['__custom__']=cost
        try:return self.try_pay('__custom__',execute=True)
        finally:del COST['__custom__']
    def defend(self):
        # Opponent casts instant removal on its turn 5. Opponent has 2 mana to pay soft taxes.
        target='Magnus the Red' if self.magnus else next((c for c in ['Storm-Kiln Artist','Young Pyromancer','Goblin Electromancer','Baral, Chief of Compliance','Patron Wizard','Sigil Tracer','Third Path Iconoclast'] if c in self.board),None)
        if target is None:return
        self.removal_target=target
        for c in ['Swan Song',"An Offer You Can't Refuse",'Counterspell','Arcane Denial']:
            if c in self.hand and self.try_pay(c,spell=True,execute=True):
                self.hand.remove(c);self.grave.append(c);self.noncreature_trigger(c)
                self.removal_stopped=True;return
        # Flusterstorm alone creates only one tax, opponent is modeled with 2 spare mana.
        if 'Voidmage Prodigy' in self.board and self.available_wizards()>0 and self.pay_custom((0,2,0)):
            # choose disposable Wizard token first; otherwise sacrifice Voidmage itself.
            converted='Arcane Adaptation' in self.board or 'Maskwood Nexus' in self.board
            ids=[i for i,t in enumerate(self.tokens) if t[0]=='wizard' or converted]
            if ids:del self.tokens[ids[-1]]
            else:self.board.pop('Voidmage Prodigy',None)
            self.removal_stopped=True;return
        if 'Patron Wizard' in self.board and self.available_wizards()>=3:
            # Needs >=3 tax activations to exceed scripted opponent's 2 floating mana.
            self.removal_stopped=True;return
        if target=='Magnus the Red':self.magnus=False;self.magnus_birth=None
        else:self.board.pop(target,None)
    def mana_capacity(self):
        # Snapshot gross natural mana, not net after spending; spell-only mana excluded.
        total=0
        for s in self.sources(False):
            if s.kind=='altar':continue
            total+=max(sum(m) for m in s.modes)
        return total
    def operate_turn(self,turn):
        self.turn=turn;self.tapped=set();self.did_magnus_this_turn=False
        self.float={'U':0,'R':0,'C':0,'SU':0,'SR':0}
        self.tokens=[t for t in self.tokens if t[3] is None or t[3]>=turn]
        self.draw()
        self.add_land()
        self.try_jace()
        before=self.spells; t_before=self.live_tokens()
        # Shared decisions: selection if missing land, mana rocks, then Magnus policy, then engines/spells.
        if len(self.lands)<min(turn,5):self.play_selection(early=True)
        self.play_rocks()
        eligible=not self.magnus and self.try_pay('Magnus the Red')
        if eligible and self.first_opportunity is None:self.first_opportunity=turn
        must_wait=self.first_opportunity is None or turn<=self.first_opportunity
        if self.policy=='rush':deploy=eligible
        elif self.policy=='delay_one':deploy=eligible and not must_wait
        elif self.policy=='conditional':
            # Delay at least a turn; afterward require useful setup or force by turn 7.
            deploy=eligible and not must_wait and (turn>=7 or (self.has_engine() and (self.live_tokens()>=1 or self.protect_available())))
        else:raise ValueError(self.policy)
        if deploy:self.play_magnus()
        self.play_engines()
        self.play_selection(early=False)
        # An extra opportunity after spending setup mana applies equally to all three strategies.
        self.spell_engine()
        if self.level==1 and turn>=5:self.class_upgrade()
        # Magnus creates a Spawn only after combat damage; 50% hit assumption on turns after arrival.
        if self.magnus and self.magnus_birth<turn and self.rng.random()<.5:self.add_token()
        # Temporary Stormsplitter tokens are exiled at the beginning of this end step.
        self.tokens=[t for t in self.tokens if t[3] is None or t[3]>turn]
        if self.removal and turn==5:self.defend()
        self.tmetrics[turn]={
            'magnus':self.magnus,'cast':self.first_cast is not None and self.first_cast<=turn,
            'engine':self.has_engine(),'magnus_engine':self.magnus and self.has_engine(),
            'magnus_token':self.magnus and self.live_tokens()>0,
            'tokens':self.live_tokens(),'mana_rocks':len(self.rocks),
            'selection_used':self.selection_used,'spells_cast':self.spells,
            'spells_this_turn':self.spells-before,
            'token_growth':self.live_tokens()-t_before,
            'protect':self.protect_available(),'magnus_protected':self.magnus and self.protect_available(),
            'available_hand':len(self.hand), 'engine_count':len(set(self.board)&(TOKEN_ENGINES|UTILITY_ENGINES)),
            'magnus_engine_protected':self.magnus and self.has_engine() and self.protect_available(),
            'mana_paid_cumulative':sum(self.mana_paid.values()),
            'early_actions_cumulative':sum(v for t,v in self.turn_mana_actions.items() if t<=4),
            'discount_saved':self.discount_saved,'treasures_made':self.treasures_made
        }
    def run(self,turns=8):
        for t in range(1,turns+1):self.operate_turn(t)
        return {
            'first_opportunity':self.first_opportunity or 99,'first_magnus':self.first_cast or 99,
            'magnus_engine_at_arrival':self.magnus_arrival_engine,
            'tokens_at_arrival':self.magnus_arrival_tokens,
            'protected_at_arrival':self.magnus_arrival_protected,
            'engine_and_protection_at_arrival':self.magnus_arrival_engine_protected,
            'removed':self.removal_target is not None,'removal_stopped':self.removal_stopped,
            'selection_used':self.selection_used,'spell_casts':self.spells,
            'spell_casts_after_magnus':self.spells_after_magnus,
            'tmetrics':self.tmetrics,
        }

def run_experiment(n=600,seed=20261028):
    data={}
    for scenario in (False,True):
        group={}
        for policy in ('rush','delay_one','conditional'):
            rows=[Game(policy,seed+i,scenario).run() for i in range(n)]
            overall={}
            for turn in (4,5,6,7,8):
                m=[x['tmetrics'][turn] for x in rows]
                for key in ('magnus','magnus_engine','magnus_token','magnus_protected','magnus_engine_protected','protect'):
                    overall[f'{key}_t{turn}']=round(sum(x[key] for x in m)/n*100,1)
                for key in ('tokens','spells_cast','spells_this_turn','selection_used','mana_rocks','engine_count','available_hand','mana_paid_cumulative','early_actions_cumulative','discount_saved','treasures_made'):
                    overall[f'{key}_t{turn}_mean']=round(sum(x[key] for x in m)/n,2)
            for key in ('magnus_engine_at_arrival','protected_at_arrival','engine_and_protection_at_arrival','removed','removal_stopped'):
                overall[key]=round(sum(x[key] for x in rows)/n*100,1)
            overall['early_selection_by_t3']=round(sum(x['tmetrics'][3]['selection_used']>0 for x in rows)/n*100,1)
            overall['setup_two_plus_actions_by_t4']=round(sum(x['tmetrics'][4]['early_actions_cumulative']>=2 for x in rows)/n*100,1)
            overall['tokens_at_arrival_mean_all_trials']=round(sum(x['tokens_at_arrival'] for x in rows)/n,2)
            overall['magnus_with_2_tokens_at_arrival']=round(sum(x['first_magnus']!=99 and x['tokens_at_arrival']>=2 for x in rows)/n*100,1)
            overall['first_magnus_mean_by_t8']=round(sum(min(9,x['first_magnus']) for x in rows)/n,2)
            overall['first_magnus_t5']=round(sum(x['first_magnus']<=5 for x in rows)/n*100,1)
            overall['first_magnus_t6']=round(sum(x['first_magnus']<=6 for x in rows)/n*100,1)
            group[policy]=overall
        data['one_removal_t5' if scenario else 'no_removal']=group
    return {'deck':'v1.6','trials_per_policy_scenario':n,'seed':seed,'findings':data,
        'disclaimer':'Illustrative greedy goldfish, finite supported card subset. Not a complete MTG rules engine; no win rates.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trials',type=int,default=600)
    p.add_argument('--seed',type=int,default=20261028)
    p.add_argument('--out',type=Path,default=ROOT/'magnus_v16_sim_v2_results.json')
    args=p.parse_args()
    report=run_experiment(args.trials,args.seed)
    args.out.write_text(json.dumps(report,indent=2))
    print(json.dumps(report['findings'],indent=2))
