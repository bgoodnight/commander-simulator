"""Magnus v1.6 illustrative Monte Carlo pilot comparison.
Three same-deck casting policies; includes colored resources and common small spells.
NOT a Magic rules engine or win-rate estimator.
"""
from __future__ import annotations
import random, json, math
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path('/mnt/data')
rows=[];section=None
for line in (ROOT/'magnus_thousand_sons_v1_6.txt').read_text().splitlines():
    if line.startswith('Commander ('):section='commander'
    elif line.startswith('Creatures ('):section='creatures'
    elif line.startswith('Artifacts and Enchantments ('):section='artifacts'
    elif line.startswith('Instants and Sorceries ('):section='spells'
    elif line.startswith('Lands ('):section='lands'
    elif line[:1].isdigit() and section:
        try:
            q,n=line.split(' ',1);rows.extend([(n,section)]*int(q))
        except:pass
assert len(rows)==100
library=[n for n,t in rows if t!='commander']
LANDS={n for n,t in rows if t=='lands'}
ROCKS={'Sol Ring','Arcane Signet','Izzet Signet','Talisman of Creativity','Fellwar Stone','Mind Stone'}
CANTRIPS={'Preordain','Ponder','Brainstorm','Telling Time','Impulse','Frantic Search'}
CHEAP_COUNTERS={'Swan Song','An Offer You Can\'t Refuse','Flusterstorm','Counterspell','Arcane Denial'}
WIZARDS={'Goblin Electromancer','Baral, Chief of Compliance','Voidmage Prodigy',"Jace, Vryn's Prodigy",'Harmonic Prodigy','Sigil Tracer','Spellseeker','Patron Wizard','Archmage Emeritus','Veyran, Voice of Duality','Stormsplitter','Dualcaster Mage'}
TOKEN_ENGINES={'Young Pyromancer','Third Path Iconoclast','Docent of Perfection','Stormsplitter'}
RESOURCE_ENGINES={'Goblin Electromancer','Baral, Chief of Compliance','Storm-Kiln Artist','Sorcerer Class','Phyrexian Altar','Archmage Emeritus',"Jace, Vryn's Prodigy"}
DEF_ENGINES={'Patron Wizard','Voidmage Prodigy','Sigil Tracer'}
EARLY_ENGINES={'Young Pyromancer','Third Path Iconoclast','Goblin Electromancer','Baral, Chief of Compliance',"Jace, Vryn's Prodigy",'Sorcerer Class','Harmonic Prodigy','Voidmage Prodigy'}
# Generic, U, R. Costs after one-time installation / base spell mana.
COST={
 'Sol Ring':(1,0,0),'Arcane Signet':(2,0,0),'Izzet Signet':(2,0,0),
 'Talisman of Creativity':(2,0,0),'Fellwar Stone':(2,0,0),'Mind Stone':(2,0,0),
 'Young Pyromancer':(1,0,1),'Third Path Iconoclast':(0,1,1),
 'Goblin Electromancer':(0,1,1),'Baral, Chief of Compliance':(1,1,0),
 "Jace, Vryn's Prodigy":(1,1,0),'Harmonic Prodigy':(1,0,1),
 'Voidmage Prodigy':(0,2,0),'Sigil Tracer':(1,2,0),'Patron Wizard':(0,3,0),
 'Spellseeker':(2,1,0),'Stormsplitter':(3,0,1),'Storm-Kiln Artist':(3,0,1),
 'Veyran, Voice of Duality':(1,1,1),'Archmage Emeritus':(2,2,0),
 'Docent of Perfection':(3,2,0),'Sorcerer Class':(0,1,1),
 'Phyrexian Altar':(3,0,0),'The Lost and the Damned':(1,1,1),
 'Arcane Adaptation':(2,1,0),'Maskwood Nexus':(4,0,0),
 'Brainstorm':(0,1,0),'Ponder':(0,1,0),'Preordain':(0,1,0),
 'Telling Time':(1,1,0),'Impulse':(1,1,0),'Frantic Search':(2,1,0),
 'Mystic Speculation':(0,1,0), 'Magnus the Red':(3,1,1),
}
PRIOR={'Sol Ring':20,'Arcane Signet':17,'Izzet Signet':16,'Talisman of Creativity':17,
       'Fellwar Stone':16,'Mind Stone':15,'Young Pyromancer':13,'Third Path Iconoclast':13,
       'Baral, Chief of Compliance':12,'Goblin Electromancer':12,"Jace, Vryn's Prodigy":11,
       'Sorcerer Class':10,'Voidmage Prodigy':9,'Storm-Kiln Artist':11,'Harmonic Prodigy':8,
       'Sigil Tracer':9,'Patron Wizard':8,'Stormsplitter':9,'Phyrexian Altar':8,
       'Docent of Perfection':7,'Archmage Emeritus':8,'Spellseeker':7,
       'The Lost and the Damned':7}
ALL_PLAYABLE=set(COST)-{'Magnus the Red'}-CANTRIPS
COMBAT_CHANCE=.50

def land_kind(name,prev,turn):
    if name in {'Island','Otawara, Soaring City','Mystic Sanctuary'}: return 'U'
    if name in {'Mountain','Sokenzan, Crucible of Defiance'}:return 'R'
    if name=='Fabled Passage':return 'D'
    if name in {'Command Tower','Steam Vents','Training Center','Stormcarved Coast','Sulfur Falls','Shivan Reef','Spirebluff Canal','Riverglide Pathway','Fiery Islet','Cascade Bluffs','Exotic Orchard'}:return 'D'
    if name=='Riptide Laboratory':return 'C'
    return 'C'

def enters_tapped(n,prior):
    if n=='Mystic Sanctuary':return sum(c in {'Island','Steam Vents'} for c in prior)<3
    if n=='Stormcarved Coast':return len(prior)<2
    if n=='Sulfur Falls':return not any(x in {'Island','Mountain','Steam Vents'} for x in prior)
    if n=='Spirebluff Canal':return len(prior)>=3
    return False

def max_lands_good(hand,landlist,turn):
    opts=[n for n in hand if n in LANDS]
    if not opts:return None
    types=[land_kind(n,landlist,turn) for n in landlist]
    u=types.count('U')+types.count('D');r=types.count('R')+types.count('D')
    return max(opts,key=lambda n: (not enters_tapped(n,landlist), (3 if (u==0 and land_kind(n,landlist,turn) in ['U','D']) else 0)+(3 if (r==0 and land_kind(n,landlist,turn) in ['R','D']) else 0), land_kind(n,landlist,turn)=='D',n=='Island'))

def card_value(name,turn,lands,hand,board):
    if name in LANDS:return 15 if len(lands)<4 else (9 if len(lands)<6 else 2)
    if name in ROCKS:return 14 if turn<4 else (10 if turn<7 else 5)
    if name in EARLY_ENGINES:return 11 if turn<=4 else 8
    if name in CHEAP_COUNTERS:return 7 if turn<=4 else 10
    if name in {'Sigil Tracer','Patron Wizard','Storm-Kiln Artist','Stormsplitter','Archmage Emeritus','Spellseeker'}:return 9
    if name in CANTRIPS:return 8 if turn<=5 else 6
    if name in {'Phyrexian Altar','Mystic Speculation','Mathemagics','Searing Touch'}:return 7 if turn>=5 else 3
    return 3

def select_spell(n,hand,deck,turn,lands,board,rng):
    if n=='Preordain':
        cards=deck[:2];del deck[:2]
        cards.sort(key=lambda c: card_value(c,turn,lands,hand,board),reverse=True)
        if cards and card_value(cards[0],turn,lands,hand,board)>=7:
            deck[:0]=cards[:1];deck.extend(cards[1:])
        else:deck.extend(cards)
        if deck:hand.append(deck.pop(0))
    elif n=='Ponder':
        peek=deck[:3];del deck[:3]
        peek.sort(key=lambda c:card_value(c,turn,lands,hand,board),reverse=True)
        if peek and card_value(peek[0],turn,lands,hand,board)<7:
            deck[:0]=peek;rng.shuffle(deck)
        else:deck[:0]=peek
        if deck:hand.append(deck.pop(0))
    elif n=='Brainstorm':
        hand.extend(deck[:3]);del deck[:3]
        bottom=sorted(hand,key=lambda c:card_value(c,turn,lands,hand,board))[:2]
        for card in bottom:hand.remove(card)
        deck[:0]=bottom
    elif n=='Telling Time':
        peek=deck[:3];del deck[:3]
        peek.sort(key=lambda c:card_value(c,turn,lands,hand,board),reverse=True)
        if peek:hand.append(peek[0])
        if len(peek)>1:deck.insert(0,peek[1]);deck.extend(peek[2:])
    elif n=='Impulse':
        peek=deck[:4];del deck[:4]
        peek.sort(key=lambda c:card_value(c,turn,lands,hand,board),reverse=True)
        if peek:hand.append(peek[0]);deck.extend(peek[1:])
    elif n=='Frantic Search':
        hand.extend(deck[:2]);del deck[:2]
        for card in sorted(hand,key=lambda c:card_value(c,turn,lands,hand,board))[:2]:hand.remove(card)

def take(pool,cost):
    """One-use mana unit pool: each physical dual picks one color. Return consumed indices or None."""
    g,u,r=cost;need=g+u+r
    if len(pool)<need:return None
    blues=[i for i,(c,src) in enumerate(pool) if c in ('U','D')]
    reds=[i for i,(c,src) in enumerate(pool) if c in ('R','D')]
    if len(blues)<u or len(reds)<r:return None
    import itertools
    options=[]
    for bs in itertools.combinations(blues,u):
        bset=set(bs)
        for rs in itertools.combinations([i for i in reds if i not in bset],r):
            chosen=set(bs)|set(rs)
            possible=sorted([i for i in range(len(pool)) if i not in chosen], key=lambda i:({'C':0,'R':1,'U':1,'D':3}[pool[i][0]],pool[i][1]=='treasure'))
            chosen.update(possible[:g])
            if len(chosen)<need:continue
            # prefer to leave flexible sources in pool for later, burn C first
            sc=sum((2 if pool[i][0]=='D' else 0)+(3 if pool[i][1]=='treasure' else 0) for i in chosen)
            options.append((sc,chosen))
    if not options:return None
    return min(options,key=lambda x:x[0])[1]

class Game:
    def __init__(self,deck,policy,seed,disrupt=False):
        self.rng=random.Random(seed);self.deck=deck.copy();self.rng.shuffle(self.deck)
        self.policy=policy;self.disrupt=disrupt
        self.hand=self.deck[:7];del self.deck[:7]
        self.mulligans=0
        # One free London mulligan, keep if two-to-four lands, at least one useful cheap mana or selection.
        for _ in range(2):
            nlands=sum(n in LANDS for n in self.hand)
            if 2<=nlands<=4 and (any(n in ROCKS|CANTRIPS|EARLY_ENGINES for n in self.hand) or nlands==3):break
            self.deck.extend(self.hand);self.rng.shuffle(self.deck);self.hand=self.deck[:7];del self.deck[:7];self.mulligans+=1
        self.lands=[];self.rocks=[];self.board={};self.tokens=0;self.wizard_tokens=0;self.treasures=0
        self.class_level=0;self.magnus=False;self.first_legal=None;self.magnus_turn=None
        self.pool=[];self.selection=0;self.spell_casts=0;self.protected_on_arrival=False;self.hard_protection_at_arrival=False;self.first_magnus_turn=None;self.commander_casts=0;self.token_ready=0
        self.counter_hand_at_arrival=False;self.engine_on_arrival=False;self.tokens_on_arrival=0;self.token_engine_arrival=False;self.cost_reducer_arrival=False;self.engine_and_hard_defense=False
        self.defense_on_arrival=False;self.engine_turn=None;self.engine_online_at={};self.magnus_alive_at={}
        self.disrupted_target=None;self.disruption_stopped=False;self.removal_turn=6
        self.tokens_t4=0;self.rocks_t4=0;self.mana_t5=0;self.has_draw_seen_t5=False;self.first_legal_t=None
        self.card_copies=0;self.cantrips_t3=0
    def mana_units(self,turn):
        p=[]
        for c,placed in self.lands:
            if placed==turn and enters_tapped(c,[n for n,t in self.lands if t<turn]):continue
            if c=='Fabled Passage':
                # Fetch basic (tapped until four lands on its ETB), correct choice according to color balance.
                continue
            p.append((land_kind(c,self.lands,turn),'land'))
        for r in self.rocks:
            if r=='Sol Ring':p.extend([('C','rock'),('C','rock')])
            elif r=='Mind Stone':p.append(('C','rock'))
            elif r=='Izzet Signet':pass
            else:p.append(('D','rock'))
        p.extend([('D','treasure')]*self.treasures)
        # Izzet Signet: tap one other mana to add UR; net +1 mana, exact colors.
        if 'Izzet Signet' in self.rocks and p:
            i=next((i for i,(v,s) in enumerate(p) if v=='C'),0)
            p.pop(i);p.extend([('U','signet'),('R','signet')])
        # Level-two Sorcerer Class mana added later, as spell-restricted units.
        return p
    def pay(self,card,kind='permanent',tokens=False,reserve=False,extra=0):
        c=COST[card];g,u,r=c
        if kind=='spell':
            cut=int('Baral, Chief of Compliance' in self.board)+int('Goblin Electromancer' in self.board)
            if self.magnus:cut+=self.tokens
            g=max(0,g+extra-cut)
        else:g+=extra
        if card=='Magnus the Red':g+=2*self.commander_casts
        target=(g,u,r)
        permitted=[(i,c) for i,c in enumerate(self.pool) if kind=='spell' or c[1]!='class-spell-only']
        which2=take([c for i,c in permitted],target)
        which={permitted[i][0] for i in which2} if which2 is not None else None
        if which is None:return False
        if reserve and any(n in CHEAP_COUNTERS for n in self.hand):
            kept=[x for i,x in enumerate(self.pool) if i not in which]
            if not self.has_active_protection(kept):return False
        used=[x for i,x in enumerate(self.pool) if i in which]
        self.treasures-=sum(s=='treasure' for c,s in used)
        self.pool=[x for i,x in enumerate(self.pool) if i not in which]
        return True
    def has_active_protection(self,pool=None,include_patron=True):
        pp=self.pool if pool is None else pool
        for c in CHEAP_COUNTERS & set(self.hand):
            cost=(0,1,0) if c in {'Swan Song',"An Offer You Can't Refuse",'Flusterstorm'} else (0,2,0) if c=='Counterspell' else (max(0,1-int(self.magnus)*self.tokens-int('Goblin Electromancer' in self.board)-int('Baral, Chief of Compliance' in self.board)),1,0)
            if take(pp,cost) is not None:return True
        if include_patron and 'Patron Wizard' in self.board and self.wizard_count(available_only=True)>=2:return True # tax proxy only
        if 'Voidmage Prodigy' in self.board and self.wizard_count()>1 and take(pp,(0,2,0)) is not None:return True
        return False
    def wizard_count(self,available_only=False):
        count=sum(1 for x in self.board if x in WIZARDS and (not available_only or self.board[x]<self.turn))
        count+=self.wizard_tokens
        if 'Arcane Adaptation' in self.board or 'Maskwood Nexus' in self.board:
            count=max(count,len([x for x in self.board if x not in ROCKS])+self.tokens)
        return count
    def cast_noncreature(self,n):
        self.spell_casts+=1
        if 'Young Pyromancer' in self.board:self.tokens+=2 if 'Harmonic Prodigy' in self.board else 1
        if 'Third Path Iconoclast' in self.board:self.tokens+=1
        if 'Docent of Perfection' in self.board:self.tokens+=1;self.wizard_tokens+=1
        if 'Stormsplitter' in self.board:
            num=2 if 'Harmonic Prodigy' in self.board else 1
            self.tokens+=num;self.wizard_tokens+=num
        if 'Storm-Kiln Artist' in self.board:
            self.treasures+=2 if 'Harmonic Prodigy' in self.board else 1
            self.pool.extend([('D','treasure')]*(2 if 'Harmonic Prodigy' in self.board else 1))
        if 'Archmage Emeritus' in self.board:
            num=2 if 'Harmonic Prodigy' in self.board else 1
            for _ in range(num):
                if self.deck:self.hand.append(self.deck.pop(0))
    def play_card(self,c):
        if c not in self.hand:return False
        if c in CANTRIPS:
            if not self.pay(c,'spell'):return False
            self.hand.remove(c);self.cast_noncreature(c)
            select_spell(c,self.hand,self.deck,self.turn,[c for c,_ in self.lands],self.board,self.rng)
            self.selection+=1
            if self.turn<=3:self.cantrips_t3+=1
            if c=='Frantic Search':
                # Untap up to 3 already tapped lands: approximate by restoring their actual color units.
                # Do not give extra land units if those lands are still untapped in pool.
                rem=sum(src=='land' for _,src in self.pool)
                taps=[(land_kind(n,[],self.turn),'land') for n,t in self.lands if n!='Fabled Passage' and not (t==self.turn and enters_tapped(n,[]))]
                self.pool.extend(taps[:max(0,min(3,len(taps)-rem))])
            return True
        if c not in COST:return False
        if not self.pay(c,'permanent'):return False
        self.hand.remove(c);self.board[c]=self.turn
        if c in ROCKS:
            self.rocks.append(c);del self.board[c]
            # rocks can tap immediately (non-creature); signet requires another mana to filter
            if c=='Sol Ring':self.pool.extend([('C','rock'),('C','rock')])
            elif c=='Mind Stone':self.pool.append(('C','rock'))
            elif c=='Izzet Signet':
                if self.pool:
                    idx=next((i for i,(v,_) in enumerate(self.pool) if v=='C'),0)
                    typ,src=self.pool.pop(idx)
                    if src=='treasure':self.treasures-=1
                    self.pool.extend([('U','signet'),('R','signet')])
            else:self.pool.append(('D','rock'))
        if c=='Sorcerer Class':
            # draw 2, discard 2 (loot, not net card advantage)
            self.hand.extend(self.deck[:2]);del self.deck[:2]
            for x in sorted(self.hand,key=lambda c:card_value(c,self.turn,[n for n,t in self.lands],self.hand,self.board))[:2]:self.hand.remove(x)
            self.class_level=1
        return True
    def use_jace(self):
        if "Jace, Vryn's Prodigy" in self.board and self.board["Jace, Vryn's Prodigy"]<self.turn:
            if self.deck:
                self.hand.append(self.deck.pop(0))
                c=min(self.hand,key=lambda c:card_value(c,self.turn,[n for n,t in self.lands],self.hand,self.board));self.hand.remove(c)
    def cast_magnus(self):
        if self.magnus:return False
        if not self.pay('Magnus the Red'):return False
        self.magnus=True;self.magnus_turn=self.turn;self.commander_casts+=1
        if self.first_magnus_turn is None:self.first_magnus_turn=self.turn
        self.engine_on_arrival=self.engine_count()>=1
        self.token_engine_arrival=bool(set(self.board)&TOKEN_ENGINES)
        self.cost_reducer_arrival=bool(set(self.board)&{'Goblin Electromancer','Baral, Chief of Compliance'})
        self.tokens_on_arrival=self.tokens
        self.counter_hand_at_arrival=bool(set(self.hand)&CHEAP_COUNTERS)
        self.protected_on_arrival=self.has_active_protection()
        self.hard_protection_at_arrival=self.has_active_protection(include_patron=False)
        self.engine_and_hard_defense=self.engine_on_arrival and self.hard_protection_at_arrival
        self.defense_on_arrival=self.protected_on_arrival or self.wizard_count()>=2 and ('Patron Wizard' in self.board or 'Voidmage Prodigy' in self.board)
        if 'The Lost and the Damned' in self.board:self.tokens+=1 # cast from command zone
        return True
    def engine_count(self):
        return len(set(self.board)&(TOKEN_ENGINES|RESOURCE_ENGINES|DEF_ENGINES))
    def at_least_usable_engine(self):
        return self.engine_count()>=1 and (self.tokens>=1 or any(c in self.board for c in RESOURCE_ENGINES|{'Sigil Tracer','Patron Wizard','Voidmage Prodigy'}))
    def play_early_engines(self,prioritize=False):
        # Early creatures / permanent mana engines; avoid high-cost Tzeentch creatures.
        options=sorted((c for c in self.hand if c in ALL_PLAYABLE and c not in ROCKS and c not in {'Arcane Adaptation','Maskwood Nexus'}),key=lambda c:(-PRIOR.get(c,0),sum(COST[c])))
        played=0
        for c in options:
            if played>= (3 if prioritize else 2):break
            if self.turn<=3 and sum(COST[c])>3:continue
            if self.turn<=4 and sum(COST[c])>4:continue
            if not prioritize and self.magnus and self.turn==self.magnus_turn:
                # avoid spending the last counter mana after commander
                if self.has_active_protection() and not self.pay_preview_with_protection(c):continue
            if self.play_card(c):played+=1
        return played
    def pay_preview_with_protection(self,c):
        ch=take(self.pool,COST[c]);
        if ch is None:return False
        remaining=[x for i,x in enumerate(self.pool) if i not in ch]
        return self.has_active_protection(remaining)
    def make_selection(self,limit=2):
        played=0
        for _ in range(limit):
            opts=[n for n in self.hand if n in CANTRIPS]
            opts.sort(key=lambda c: (0 if c in ['Preordain','Ponder'] else 1 if c in ['Impulse','Telling Time'] else 2,sum(COST[c])))
            if not opts:break
            short_lands=len(self.lands)<min(self.turn,5)
            if not short_lands and self.turn>=4 and self.magnus and self.protected_on_arrival and self.has_active_protection() and len(self.pool)<=2:break
            can=False
            for c in opts:
                if self.play_card(c):played+=1;can=True;break
            if not can:break
        return played
    def refresh_land(self):
        c=max_lands_good(self.hand,[n for n,t in self.lands],self.turn)
        if c:
            self.hand.remove(c);self.lands.append((c,self.turn))
            if c=='Fabled Passage':
                # Fetch chosen basic; enters tapped except on fourth or later land.
                n='Island' if sum(x in ('Island','Steam Vents','Shivan Reef') for x,_ in self.lands)<2 else 'Mountain'
                self.lands[-1]=(n,self.turn)
                if len(self.lands)>=4:self.pool.append((land_kind(n,[],self.turn),'land'))
            elif not enters_tapped(c,[n for n,t in self.lands[:-1]]):self.pool.append((land_kind(c,[],self.turn),'land'))
    def build_rock(self):
        for _ in range(3):
            opts=[n for n in self.hand if n in ROCKS]
            opts.sort(key=lambda c:-PRIOR[c]);played=False
            for c in opts:
                if self.play_card(c):played=True;break
            if not played:break
    def level_class(self):
        if self.class_level==1 and self.turn>=4 and self.engine_count()>1:
            if take(self.pool,(0,1,1)) is not None:
                i=take(self.pool,(0,1,1))
                for c,s in [self.pool[j] for j in i]:
                    if s=='treasure':self.treasures-=1
                self.pool=[n for j,n in enumerate(self.pool) if j not in i]
                self.class_level=2
        if self.class_level==2:
            # Tap established creatures for instant/sorcery and level costs only, not for Magnus or other permanents.
            n=sum(v<self.turn for k,v in self.board.items() if k not in ROCKS)+self.token_ready
            if 'Patron Wizard' in self.board or 'Sigil Tracer' in self.board:n=max(0,n-2)
            self.pool.extend([('D','class-spell-only')]*min(12,n))
    def defend_threat(self):
        # One opponent instant removal directed at Magnus if in play, else highest-weight creature engine.
        target='Magnus the Red' if self.magnus else next((c for c in sorted(self.board,key=lambda c:-PRIOR.get(c,0)) if c not in ROCKS and c!='Sorcerer Class'),None)
        if not target:return
        self.disrupted_target=target
        can_counter=False
        for c in sorted(self.hand & CHEAP_COUNTERS if isinstance(self.hand,set) else set(self.hand)&CHEAP_COUNTERS):
            cost=(0,1,0) if c in {'Swan Song',"An Offer You Can't Refuse",'Flusterstorm'} else (0,2,0) if c=='Counterspell' else (max(0,1-int(self.magnus)*self.tokens-int('Goblin Electromancer' in self.board)-int('Baral, Chief of Compliance' in self.board)),1,0)
            indices=take(self.pool,cost)
            if indices is not None:
                self.hand.remove(c)
                self.pool=[v for j,v in enumerate(self.pool) if j not in indices]
                can_counter=True
                break
        if not can_counter and 'Voidmage Prodigy' in self.board and self.wizard_count()>1:
            ii=take(self.pool,(0,2,0))
            if ii is not None:
                self.pool=[v for j,v in enumerate(self.pool) if j not in ii]
                can_counter=True
                if self.wizard_tokens>0:self.wizard_tokens-=1;self.tokens=max(0,self.tokens-1)
        if not can_counter and 'Patron Wizard' in self.board and self.wizard_count(available_only=True)>=3:
            # tax counter succeeds if enemy cannot afford to pay. Assume 50% independent.
            can_counter=self.rng.random()<.50
        if can_counter:self.disruption_stopped=True
        else:
            if target=='Magnus the Red':self.magnus=False
            elif target in self.board:del self.board[target]
    def run(self,turns=8):
        for turn in range(1,turns+1):
            self.turn=turn
            self.pool=self.mana_units(turn)
            self.token_ready=self.tokens
            # In normal 3+ player Commander everyone draws on turn one.
            if self.deck:self.hand.append(self.deck.pop(0))
            self.use_jace()
            if self.magnus and self.magnus_turn is not None and turn>self.magnus_turn:
                if self.rng.random()<COMBAT_CHANCE:self.tokens+=1
            self.refresh_land()
            self.build_rock()
            # draw before summoning if missing lands or lacking actionable engine
            if turn<=3:self.make_selection(2)
            # A first-deployment opportunity is defined after playing land and ramp, before spending on other engines.
            eligible=(not self.magnus and take(self.pool,COST['Magnus the Red']) is not None)
            if eligible and self.first_legal is None:self.first_legal=turn
            if self.policy=='rush':
                if eligible:self.cast_magnus()
                self.play_early_engines(prioritize=False)
                if turn>3:self.make_selection(2)
            elif self.policy=='delay_one':
                if eligible and turn>self.first_legal:self.cast_magnus()
                if not self.magnus:self.play_early_engines(prioritize=True)
                else:self.play_early_engines(prioritize=False)
                if turn>3:self.make_selection(2)
                # If a currently missing Magnus is affordable following development on same turn, deploy no earlier than next turn.
                if not self.magnus and self.first_legal and turn>self.first_legal and self.magnus_turn is None and take(self.pool,COST['Magnus the Red']) is not None:self.cast_magnus()
            elif self.policy=='prepared':
                # Wait at least one full turn, then require engine and defense, or force turn 8 to avoid indefinite passivity
                ready=self.at_least_usable_engine() and (self.has_active_protection() or ('Voidmage Prodigy' in self.board and self.wizard_count()>1))
                if eligible and self.first_legal and turn>self.first_legal and (ready or turn>=7):self.cast_magnus()
                if not self.magnus:self.play_early_engines(prioritize=True)
                else:self.play_early_engines(prioritize=False)
                if turn>3:self.make_selection(2)
                if not self.magnus and self.first_legal and turn>self.first_legal and take(self.pool,COST['Magnus the Red']) is not None:
                    ready=self.at_least_usable_engine() and self.has_active_protection()
                    if ready or turn>=7:self.cast_magnus()
            # After main development, level Sorcerer Class if affordable (costs mana in setup turn)
            if turn>=4 and self.class_level>=1 and (self.class_level==2 or self.magnus or len(self.lands)>=5):self.level_class()
            if turn==4:self.tokens_t4=self.tokens;self.rocks_t4=len(self.rocks)
            if turn==5:self.has_draw_seen_t5=self.selection>0
            self.magnus_alive_at[turn]=self.magnus
            self.engine_online_at[turn]=(self.magnus and self.at_least_usable_engine())
            if self.disrupt and turn==5:self.defend_threat()
        return {
           'first_legal':self.first_legal or 99,'magnus_turn':self.first_magnus_turn or 99,
           'delay_from_legal':(self.first_magnus_turn-self.first_legal) if self.first_legal is not None and self.first_magnus_turn is not None else 99,
           'magnus_t4':self.first_magnus_turn is not None and self.first_magnus_turn<=4,
           'magnus_t5':self.first_magnus_turn is not None and self.first_magnus_turn<=5,
           'magnus_t6':self.first_magnus_turn is not None and self.first_magnus_turn<=6,
           'magnus_t7':self.first_magnus_turn is not None and self.first_magnus_turn<=7,
           'magnus_t8':self.first_magnus_turn is not None and self.first_magnus_turn<=8,
           'magnus_with_engine':self.engine_on_arrival,'magnus_with_token':self.tokens_on_arrival>0,
           'magnus_with_2tokens':self.tokens_on_arrival>=2,'magnus_with_live_protection':self.protected_on_arrival,
           'magnus_with_counter_hand':self.counter_hand_at_arrival,'magnus_hard_protection':self.hard_protection_at_arrival,
           'token_engine_arrival':self.token_engine_arrival,'cost_reducer_arrival':self.cost_reducer_arrival,
           'engine_and_hard_defense':self.engine_and_hard_defense,
           'online_t6':self.engine_online_at.get(6,False),'online_t7':self.engine_online_at.get(7,False),
           'online_t8':self.engine_online_at.get(8,False),
           'magnus_alive_t6':self.magnus_alive_at.get(6,False),'magnus_alive_t7':self.magnus_alive_at.get(7,False),
           'selection_early':self.cantrips_t3>0, 'any_selection':self.selection>0,
           'class_level_2':self.class_level>=2,'ramp_t4_2plus':self.rocks_t4>=2,
           'disrupted':self.disrupted_target is not None,'disruption_stopped':self.disruption_stopped,
           'tokens_t8':self.tokens,'engine_count_t8':self.engine_count(),
           'mulligans':self.mulligans,'tokens_ge2_t8':self.tokens>=2,'tokens_ge4_t8':self.tokens>=4,
        }

def run_samples(n=10000,seed=164400,disrupt=False):
    outcomes={}
    for mode in ['rush','delay_one','prepared']:
        tall=Counter();nums=defaultdict(float);dists=Counter()
        for i in range(n):
            result=Game(library,mode,seed+i,disrupt).run()
            for k,v in result.items():
                if isinstance(v,bool):tall[k]+=int(v)
                elif k in {'tokens_t8','engine_count_t8','mulligans'}:nums[k]+=v
                elif k in {'first_legal','magnus_turn','delay_from_legal'}:
                    dists[(k,v)]+=1
        outcomes[mode]={'rates_pct':{k:round(v/n*100,2) for k,v in tall.items()},
                        'means':{k:round(v/n,3) for k,v in nums.items()},
                        'distributions':{k:{str(t):round(cnt/n*100,2) for (name,t),cnt in dists.items() if name==k} for k in ['first_legal','magnus_turn','delay_from_legal']}}
    return outcomes

if __name__=='__main__':
    import sys
    n=int(sys.argv[1]) if len(sys.argv)>1 else 10000
    bas=run_samples(n)
    dis=run_samples(n,disrupt=True)
    results={'N_per_policy_per_scenario':n,'no_disruption':bas,'single_removal_after_turn5':dis,
             'description':'Illustrative heuristic policy goldfish with one free London mulligan, multiplayer Commander turn-one draw, land and six rock choices, exact colored mana unit spending (Izzet Signet modeled as input one / output UR), cheap cantrip resolution, early Wizard/engine casting, cost reducers on instant/sorceries, some spell-token and Treasure triggers. Magnus combat hit assumed 50%/turn after arrival. Does not model opponents strategic play, most spells or win loops, full tutors, real combat, the restricted Sorcerer Class mana (level 2 tracked only), or detailed Phyrexian Altar choices. Disruption: one targeted instant removal after turn5 development, may be countered with available counter/board defenses (Patron Wizard success assumed 50%). Rates are not actual game or win probabilities.'}
    dest=ROOT/'magnus_v16_patient_results.json';dest.write_text(json.dumps(results,indent=2))
    for label,d in [('baseline',bas),('one removal',dis)]:
        print('\n',label)
        keys=['magnus_t5','magnus_t6','magnus_t7','magnus_t8','magnus_with_engine','magnus_with_token','magnus_with_live_protection','magnus_hard_protection','online_t6','online_t7','online_t8','magnus_alive_t6','disrupted','disruption_stopped']
        print('METRIC'.ljust(32), *[x.ljust(13) for x in d])
        for k in keys:print(k.ljust(32),*[str(d[x]['rates_pct'].get(k,0)).ljust(13) for x in d])
    print('saved',dest)
