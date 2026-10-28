"""Reproducible v1.5 vs v1.6 early-game goldfish/visibility comparison.
Two independent views: paired natural-draw access (exact), and an intentionally
simplified resource-aware sequencing model that casts lands, rocks, cantrips,
cheap Wizards, and Magnus. NO opponent actions, mulligans, tutors, or combo wins.
Spend model approximates color choice and treats Izzet Signet as a net +1 mana
when another source exists; does not model exact mana-tap sequencing.
"""
from pathlib import Path
from collections import Counter
import numpy as np, json, random, math
ROOT=Path('/mnt/data')
SECTIONS=['Commander','Creatures','Artifacts','Spells','Lands']

def parse(ver):
    text=(ROOT/f'magnus_thousand_sons_v1_{ver}.txt').read_text()
    sec=None; rows=[]
    for line in text.splitlines():
        if line.startswith('Commander ('):sec='Commander'
        elif line.startswith('Creatures ('):sec='Creatures'
        elif line.startswith('Artifacts and Enchantments ('):sec='Artifacts'
        elif line.startswith('Instants and Sorceries ('):sec='Spells'
        elif line.startswith('Lands ('):sec='Lands'
        elif line[:1].isdigit() and sec:
            try:
                q,name=line.split(' ',1)
                rows.extend([(name,sec)]*int(q))
            except Exception:pass
    assert len(rows)==100,(ver,len(rows))
    assert Counter(n for n,s in rows if s!='Commander').total()==99
    return rows
rows15=parse('5');rows16=parse('6')
assert Counter([n for n,s in rows15 if s!='Commander'])-Counter([n for n,s in rows16 if s!='Commander'])==Counter({'Guttersnipe':1,'Past in Flames':1,'Cryptic Gateway':1})
assert Counter([n for n,s in rows16 if s!='Commander'])-Counter([n for n,s in rows15 if s!='Commander'])==Counter({'Preordain':1,'Telling Time':1,'Impulse':1})
D15=[n for n,s in rows15 if s!='Commander'];D16=[n for n,s in rows16 if s!='Commander']
LANDS={n for n,s in rows15 if s=='Lands'}
ROCKS={'Sol Ring','Arcane Signet','Izzet Signet','Talisman of Creativity','Fellwar Stone','Mind Stone'}
CANTRIPS={'Brainstorm','Ponder','Preordain','Telling Time','Impulse'}
SELECTION=CANTRIPS|{'Frantic Search','Mystic Speculation'}
COUNTERS={'Counterspell','Arcane Denial','Swan Song','An Offer You Can\'t Refuse','Flusterstorm','Muddle the Mixture'}
ONE_U_COUNTER={'Swan Song',"An Offer You Can't Refuse",'Flusterstorm'}
CHEAP_CREATURE={'Harmonic Prodigy','Young Pyromancer','Third Path Iconoclast',"Jace, Vryn's Prodigy",'Goblin Electromancer','Baral, Chief of Compliance','Voidmage Prodigy','Sigil Tracer','Veyran, Voice of Duality','Spellseeker','Stormsplitter','Dualcaster Mage'}
CHEAP_WIZARD=CHEAP_CREATURE-{'Young Pyromancer','Third Path Iconoclast'}
ACTIONABLE_ENGINE={'Young Pyromancer','Third Path Iconoclast','Goblin Electromancer','Baral, Chief of Compliance',"Jace, Vryn's Prodigy",'Harmonic Prodigy','Voidmage Prodigy','Sigil Tracer','Stormsplitter'}
MANA_WIZARD={'Goblin Electromancer','Baral, Chief of Compliance'}
BASIC_ISLAND={'Island','Steam Vents'};BASIC_MOUNTAIN={'Mountain','Steam Vents'}
BLUE={'Island','Otawara, Soaring City','Mystic Sanctuary'}
RED={'Mountain','Sokenzan, Crucible of Defiance'}
DUALS={'Command Tower','Steam Vents','Training Center','Stormcarved Coast','Sulfur Falls','Shivan Reef','Spirebluff Canal','Riverglide Pathway','Fiery Islet','Cascade Bluffs','Exotic Orchard'}

# Exact paired draw-access simulation: same shuffled index positions in each version.
def raw_access(N=150000, seed=152608):
    rng=np.random.default_rng(seed)
    tally={'v1.5':{t:Counter() for t in (3,4,5,6,8)},'v1.6':{t:Counter() for t in (3,4,5,6,8)}}
    for _ in range(N):
        perm=rng.permutation(99)
        for v,deck in [('v1.5',D15),('v1.6',D16)]:
            for t in (3,4,5,6,8):
                seen=set(deck[k] for k in perm[:7+t])
                m=tally[v][t]
                m['any_cheap_selection']+=bool(seen & CANTRIPS)
                m['two_cheap_selection']+=len(seen & CANTRIPS)>=2
                m['one_mana_cantrip']+=bool(seen & {'Brainstorm','Ponder','Preordain'})
                m['mana_rock']+=bool(seen & ROCKS)
                m['mana_rock_and_selection']+=bool(seen & ROCKS) and bool(seen & CANTRIPS)
                m['early_cabal_creature']+=bool(seen & ACTIONABLE_ENGINE)
                m['early_cabal_plus_selection']+=bool(seen & ACTIONABLE_ENGINE) and bool(seen & CANTRIPS)
                m['counterspell']+=bool(seen & COUNTERS)
                m['cabal_plus_counter']+=bool(seen & ACTIONABLE_ENGINE) and bool(seen & COUNTERS)
                m['buyback']+=bool(seen & {'Searing Touch','Mystic Speculation','Capsize'})
                m['big_x']+=bool(seen & {'Mathemagics','Comet Storm'})
                m['ramp_and_early_cabal']+=bool(seen & ROCKS) and bool(seen & ACTIONABLE_ENGINE)
    return {v:{str(t):{key:round(count/N*100,2) for key,count in tally[v][t].items()} for t in tally[v]} for v in tally}

def untapped_land(x, existing):
    if x=='Mystic Sanctuary':return sum(c in BASIC_ISLAND for c in existing)>=3
    if x=='Stormcarved Coast':return len(existing)>=2
    if x=='Sulfur Falls':return any(c in BASIC_ISLAND or c in BASIC_MOUNTAIN for c in existing)
    if x=='Spirebluff Canal':return len(existing)<3
    if x=='Fabled Passage':return len(existing)>=3
    return True

def land_choice(cards, lands):
    choices=[n for n in cards if n in LANDS]
    if not choices:return None
    num_blue=sum(n in BLUE or n in DUALS for n in lands)
    num_red=sum(n in RED or n in DUALS for n in lands)
    def score(n):
        cols=('UR' if n in DUALS or n=='Fabled Passage' else 'U' if n in BLUE else 'R' if n in RED else '')
        fixes=(int('U' in cols and num_blue<2) +int('R' in cols and num_red<1))
        return (int(untapped_land(n,lands))*4+ fixes*3 + int(n in DUALS) + int(n in BASIC_ISLAND))
    return max(choices,key=score)

def mana_quality(lands,rocks,land_tapped=False):
    l=list(lands)
    if land_tapped and l:l=l[:-1]
    sources=l+list(rocks)
    total=sum(2 if n=='Sol Ring' else 1 for n in sources)
    if 'Izzet Signet' in sources and len(sources)==1:total-=1
    u=sum(n in BLUE or n in DUALS or n in {'Arcane Signet','Talisman of Creativity','Fellwar Stone','Izzet Signet'} for n in sources)
    r=sum(n in RED or n in DUALS or n in {'Arcane Signet','Talisman of Creativity','Fellwar Stone','Izzet Signet'} for n in sources)
    # Ambiguous dual source is not two simultaneous mana; always check total too.
    return (total,u,r)

def playable(budget,u,r,cost):
    g,cu,cr=cost
    return budget>=g+cu+cr and u>=cu and r>=cr

def spend(budget,u,r,cost):
    g,cu,cr=cost
    return (budget-g-cu-cr,max(0,u-cu),max(0,r-cr))

COSTS={
 'Sol Ring':(1,0,0),'Arcane Signet':(2,0,0),'Izzet Signet':(2,0,0),
 'Talisman of Creativity':(2,0,0),'Fellwar Stone':(2,0,0),'Mind Stone':(2,0,0),
 'Harmonic Prodigy':(1,0,1),'Young Pyromancer':(1,0,1),'Third Path Iconoclast':(0,1,1),
 "Jace, Vryn's Prodigy":(1,1,0),'Goblin Electromancer':(0,1,1),'Baral, Chief of Compliance':(1,1,0),
 'Voidmage Prodigy':(0,2,0),'Veyran, Voice of Duality':(1,1,1),'Sigil Tracer':(1,2,0),
 'Spellseeker':(2,1,0),'Stormsplitter':(3,0,1),'Dualcaster Mage':(1,0,2),
 'Brainstorm':(0,1,0),'Ponder':(0,1,0),'Preordain':(0,1,0),'Telling Time':(1,1,0),'Impulse':(1,1,0),
 'Mystic Speculation':(0,1,0)
}
# This model does not model tempo from cost reduction of other noncommander wizards, or fancier permanent mana engines.
# Picks cantrip cards based on game state; a creature can be cast only if sufficient mana remains after ramp and smoothing.

def score_card(card,turn,lands,rocks,hand,field):
    missing_land=len(lands)<min(5,turn+1)
    if card in LANDS:
        return (12 if missing_land else (8 if len(lands)<5 else 0))
    if card in ROCKS:
        return 10 if turn<=3 and len(rocks)<3 else 3
    if card in {'Preordain','Ponder','Impulse','Telling Time'}:
        return 8 if turn<=4 and len(hand)<6 else 5
    if card in {'Young Pyromancer','Third Path Iconoclast','Goblin Electromancer','Baral, Chief of Compliance',"Jace, Vryn's Prodigy"}:
        return 8 if turn<=4 and card not in field else 3
    if card in COUNTERS: return 6 if turn>=3 else 3
    if card in {'Sigil Tracer','Harmonic Prodigy','Storm-Kiln Artist','Sorcerer Class','Phyrexian Altar'}:return 6
    if card in {'Mathemagics','Comet Storm','Underworld Breach'}:return 2 if turn<=4 else 5
    return 2

def cast_cantrip(card,hand,deck,turn,lands,rocks,field,rng):
    # deck as a list top at deck[0], with a mutable bottom; game effects implemented at their useful tactical level
    if card=='Preordain':
        k=deck[:2];del deck[:len(k)]
        best=sorted(k,key=lambda c:score_card(c,turn,lands,rocks,hand,field), reverse=True)
        keep=[c for c in best if score_card(c,turn,lands,rocks,hand,field)>=5]
        other=[c for c in best if c not in keep]
        deck[:0]=keep
        deck.extend(other)
        if deck:hand.append(deck.pop(0))
    elif card=='Ponder':
        k=deck[:3];del deck[:len(k)]
        ordered=sorted(k,key=lambda c:score_card(c,turn,lands,rocks,hand,field), reverse=True)
        if ordered and score_card(ordered[0],turn,lands,rocks,hand,field)<4:
            deck[:0]=ordered; rng.shuffle(deck)
        else:
            deck[:0]=ordered
        if deck:hand.append(deck.pop(0))
    elif card=='Telling Time':
        k=deck[:3];del deck[:len(k)]
        k.sort(key=lambda c:score_card(c,turn,lands,rocks,hand,field), reverse=True)
        if k:hand.append(k[0])
        if len(k)>=2:deck.insert(0,k[1])
        if len(k)>=3:deck.append(k[2])
    elif card=='Impulse':
        k=deck[:4];del deck[:len(k)]
        k.sort(key=lambda c:score_card(c,turn,lands,rocks,hand,field), reverse=True)
        if k:hand.append(k[0]);deck.extend(k[1:])
    elif card=='Brainstorm':
        for i in range(min(3,len(deck))):hand.append(deck.pop(0))
        to_put=sorted(hand, key=lambda c:score_card(c,turn,lands,rocks,hand,field))[:2]
        for c in to_put:hand.remove(c)
        deck[:0]=to_put # downside: without shuffling, bad cards are redraws
    elif card=='Mystic Speculation':
        k=deck[:3];del deck[:len(k)]
        k.sort(key=lambda c:score_card(c,turn,lands,rocks,hand,field), reverse=True)
        keep=[c for c in k if score_card(c,turn,lands,rocks,hand,field)>=5]
        others=[c for c in k if c not in keep]
        deck[:0]=keep;deck.extend(others)

def run_game(cards, seed, max_t=8):
    rng=random.Random(seed)
    deck=cards.copy();rng.shuffle(deck)
    hand=deck[:7];del deck[:7]
    lands=[];rocks=[];field=[];tokens=0; magnus=False
    protection_after=False; arrival=None; arrival_engine=False; t6_engine=False
    t5_rock=False; sel_cast=0; t3_sel=0; t5_sel=0; t5_lands=0
    laid=0; t4_magnus=False; t5_magnus=False; t6_magnus=False
    had_interaction_at_magnus=False; t6_live_protection=False; t7_live_protection=False
    for turn in range(1,max_t+1):
        if deck:hand.append(deck.pop(0))
        if turn>=2 and "Jace, Vryn's Prodigy" in field and deck:
            hand.append(deck.pop(0))
            discard=min(hand,key=lambda c:score_card(c,turn,lands,rocks,hand,field))
            hand.remove(discard)
        land=land_choice(hand,lands)
        tap_new=False
        if land:
            hand.remove(land)
            tap_new=not untapped_land(land,lands)
            if land=='Fabled Passage':
                land='Mountain' if not any(n in RED or n in DUALS for n in lands) else 'Island'
            lands.append(land); laid+=1
        budget,u,r=mana_quality(lands,rocks,tap_new)
        # play early rocks, then use cantrips that dig for missing land/rock/engine, then Wizards, then Magnus if possible
        for _ in range(2):
            opts=[c for c in rocks_of(hand) if playable(budget,u,r,COSTS[c])]
            if not opts:break
            rock=sorted(opts,key=lambda c:(c!='Sol Ring',c not in {'Arcane Signet','Talisman of Creativity','Fellwar Stone','Izzet Signet'}))[0]
            hand.remove(rock)
            budget,u,r=spend(budget,u,r,COSTS[rock])
            rocks.append(rock)
            # new rocks are untapped and can be tapped during the current turn
            budget += 2 if rock=='Sol Ring' else 1
            if rock in {'Arcane Signet','Fellwar Stone','Izzet Signet','Talisman of Creativity'}:u+=1;r+=1
        # One or two draw/selection spells if they can pay and need help, allow t1 and t2
        max_select=2 if turn>=3 else 1
        for _ in range(max_select):
            candidates=[c for c in hand if c in CANTRIPS and playable(budget,u,r,COSTS[c])]
            if not candidates:break
            # short on lands or little to do -> selection; don't use last mana if it prevents casting Magnus this turn
            if turn>=4 and playable(budget,u,r,(3,1,1)) and not magnus:break
            if turn>=3 and len(lands)>=turn and budget<=2 and any(c in ACTIONABLE_ENGINE for c in hand):break
            c=sorted(candidates,key=lambda c:({'Preordain':0,'Ponder':1,'Impulse':2,'Telling Time':3,'Brainstorm':4}[c],COSTS[c][0]))[0]
            hand.remove(c);budget,u,r=spend(budget,u,r,COSTS[c]);cast_cantrip(c,hand,deck,turn,lands,rocks,field,rng)
            sel_cast+=1
            if turn<=3:t3_sel+=1
            if turn<=5:t5_sel+=1
            if ('Young Pyromancer' in field or 'Third Path Iconoclast' in field):
                tokens+=int('Young Pyromancer' in field)+int('Third Path Iconoclast' in field)
        # If not yet cast, Magnus in command zone; prefer casting as soon as feasible.
        if not magnus and playable(budget,u,r,(3,1,1)):
            before=(budget,u,r)
            budget,u,r=spend(budget,u,r,(3,1,1))
            magnus=True;arrival=turn;arrival_engine=bool(set(field)&ACTIONABLE_ENGINE) or tokens>=1
            had_interaction_at_magnus=bool(set(hand)&COUNTERS)
            protection_after=(budget>=1 and u>=1 and bool(set(hand)&ONE_U_COUNTER)) or (budget>=2 and u>=2 and bool(set(hand)&{'Counterspell','Muddle the Mixture'}))
        # Cast cheap relevant creatures with remaining resources.
        creatures=sorted([x for x in hand if x in CHEAP_CREATURE],key=lambda c:(0 if c in {'Young Pyromancer','Third Path Iconoclast','Goblin Electromancer','Baral, Chief of Compliance',"Jace, Vryn's Prodigy"} else 1,sum(COSTS[c])))
        for c in creatures:
            if playable(budget,u,r,COSTS[c]):
                hand.remove(c);budget,u,r=spend(budget,u,r,COSTS[c]);field.append(c)
        if turn==5:
            t5_rock=len(rocks)>0;t5_lands=len(lands)
        if turn==4:t4_magnus=magnus
        if turn==5:t5_magnus=magnus
        if turn==6:
            t6_magnus=magnus; t6_engine=bool(set(field)&ACTIONABLE_ENGINE) or tokens>=1
            t6_live_protection=bool(magnus and ((budget>=1 and u>=1 and bool(set(hand)&ONE_U_COUNTER)) or (budget>=2 and u>=2 and bool(set(hand)&{'Counterspell','Muddle the Mixture'}))))
        if turn==7:
            t7_live_protection=bool(magnus and ((budget>=1 and u>=1 and bool(set(hand)&ONE_U_COUNTER)) or (budget>=2 and u>=2 and bool(set(hand)&{'Counterspell','Muddle the Mixture'}))))
    return {'t4_magnus':t4_magnus,'t5_magnus':t5_magnus,'t6_magnus':t6_magnus,
        'cast_magnus_by_t6_with_engine': bool(arrival is not None and arrival<=6 and arrival_engine),
        'cast_magnus_by_t6_with_counter_in_hand':bool(arrival is not None and arrival<=6 and had_interaction_at_magnus),
        'cast_magnus_by_t6_with_one_U_counter_held':bool(arrival is not None and arrival<=6 and protection_after),
        'early_selection_cast_t3': t3_sel>=1,'selection_cast_t5':t5_sel>=1,
        'at_least_2_selection_cast_t5':t5_sel>=2,
        'rock_by_t5':t5_rock,'four_land_by_t5':t5_lands>=4,
        'cast_magnus_by_t6_and_engine_by_t6':bool(t6_magnus and t6_engine),
        'cast_magnus_by_t6_and_counter_seen':bool(t6_magnus and (set(hand)&COUNTERS)),
        't6_magnus_and_protection_mana_post_main':t6_live_protection,
        't7_magnus_and_protection_mana_post_main':t7_live_protection,
        'arrival_turn':arrival or 9,'spells_selected':sel_cast,'tokens_by_t8':tokens}

def rocks_of(h):return [x for x in h if x in ROCKS]

def pilot_compare(N=18000,seed=515161):
    tally={'v1.5':Counter(),'v1.6':Counter()}; arrivals={'v1.5':Counter(),'v1.6':Counter()}
    for i in range(N):
        # paired seed for the same pseudo-random run; identical common cards initially indexed differently
        for v,dd in [('v1.5',D15),('v1.6',D16)]:
            x=run_game(dd, seed+i)
            for k,val in x.items():
                if isinstance(val,bool):tally[v][k]+=int(val)
            arrivals[v][x['arrival_turn']]+=1
    return {v:{'metrics_pct':{k:round(q/N*100,2) for k,q in tally[v].items()},
               'first_arrival_distribution_pct':{str(k):round(q/N*100,2) for k,q in sorted(arrivals[v].items())}}
            for v in tally}
if __name__=='__main__':
    raw=raw_access()
    print('Raw drawn')
    for t in ['3','5','6','8']:
        for k in ['any_cheap_selection','two_cheap_selection','one_mana_cantrip','mana_rock','early_cabal_creature','early_cabal_plus_selection','counterspell','ramp_and_early_cabal','buyback']:
            print(t,k,raw['v1.5'][t][k],raw['v1.6'][t][k])
    pilot=pilot_compare()
    print('Pilot comparison')
    for k in pilot['v1.5']['metrics_pct']:
        print(k,pilot['v1.5']['metrics_pct'][k],pilot['v1.6']['metrics_pct'][k])
    results={'draw_trials':150000,'sequenced_trials_per_deck':18000,'raw_access_pct':raw,'pilot':pilot,
      'method':'Exact paired shuffled natural card access without mulligans; separate early-game heuristic play model with land/rock/cantrip/Wizard/Magnus choices. No opponents, tutors, combat, removal, player decision tree or win simulation; mana-color spending approximated; Jace draws/discards after the turn it enters, spells trigger Pyromancer/Iconoclast; cantrips actually manipulate and draw cards, Brainstorm puts two back. All numbers are illustrative, not win rates.'}
    out=ROOT/'magnus_v15_v16_results.json';out.write_text(json.dumps(results,indent=2))
    print('WROTE',out)
