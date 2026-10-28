"""Paired draw and mana-only simulations for the exact Magnus v1.4 -> v1.5 lists.
No opponent interaction, no tutoring/cantrip draws/looting/casting Wizards in ramp mode;
no claims of wins or full-game gameplay. Reproducible randomized shuffle study.
"""
from pathlib import Path
from collections import Counter
from functools import lru_cache
import json
import numpy as np
ROOT=Path('/mnt/data')

def read_deck(ver):
    fn=ROOT/f'magnus_thousand_sons_v1_{ver}.txt'
    sec=None; rows=[]
    for line in fn.read_text().splitlines():
        line=line.strip()
        if line.startswith('Commander ('): sec='Commander'
        elif line.startswith('Creatures ('): sec='Creatures'
        elif line.startswith('Artifacts and Enchantments ('): sec='Artifacts'
        elif line.startswith('Instants and Sorceries ('): sec='Spells'
        elif line.startswith('Lands ('): sec='Lands'
        elif line and line.split(' ',1)[0].isdigit() and sec:
            qty,name=line.split(' ',1)
            rows.extend([(name,sec)]*int(qty))
    assert len(rows)==100, (ver,len(rows))
    return rows
rows14=read_deck('4'); rows15=read_deck('5')
deck14=[n for n,s in rows14 if s!='Commander']
deck15=[n for n,s in rows15 if s!='Commander']
replacements={"Kitsa, Otterball Elite":"Jace, Vryn's Prodigy","Stormcatch Mentor":"Goblin Electromancer", "Whispers of the Muse":"Sigil Tracer", "Scroll Rack":"Cryptic Gateway"}
assert Counter([replacements.get(n,n) for n in deck14])==Counter(deck15)
new_names=[replacements.get(n,n) for n in deck14]
LANDS={n for n,s in rows14 if s=='Lands'}
ROCKS={'Sol Ring','Arcane Signet','Izzet Signet','Talisman of Creativity','Fellwar Stone','Mind Stone'}
CHEAP_WIZARDS={'Harmonic Prodigy','Baral, Chief of Compliance','Voidmage Prodigy','Veyran, Voice of Duality','Spellseeker','Patron Wizard','Dualcaster Mage','Kitsa, Otterball Elite','Stormcatch Mentor',"Jace, Vryn's Prodigy",'Goblin Electromancer','Sigil Tracer'}
# cheap spells/selection includes any true <$2 mana cantrips, independent of other permanents
CHEAP_CANTRIP={'Brainstorm','Ponder','Whispers of the Muse'}
COUNTERS={'Counterspell','Arcane Denial','Swan Song',"An Offer You Can't Refuse",'Flusterstorm','Muddle the Mixture'}
INSTANT_PROTECTION={'Counterspell','Arcane Denial','Swan Song',"An Offer You Can't Refuse",'Flusterstorm','Muddle the Mixture','March of Swirling Mist'}
WIZARD_CONTROL={'Patron Wizard','Voidmage Prodigy'}
ENGINE={'Young Pyromancer','Third Path Iconoclast','Stormsplitter','Storm-Kiln Artist','Docent of Perfection','Guttersnipe'}
WIN_SPELLS={'Mathemagics','Comet Storm','Searing Touch'}
COPIERS={'Twincast','Reiterate','Tzaangor Shaman','Dualcaster Mage','Sigil Tracer'}
LOOP_BUYBACK={'Searing Touch','Mystic Speculation','Capsize','Whispers of the Muse'}
RAMP = ROCKS
CONVERTERS={'Arcane Adaptation','Maskwood Nexus'}
EXPENSIVE={'Lord of Change','Mutalith Vortex Beast','Heralds of Tzeentch'}
CHEAP_DRAW={'Brainstorm','Ponder','Whispers of the Muse','Frantic Search'}
DRAW_FILTER_PERMANENTS={"Jace, Vryn's Prodigy",'Kitsa, Otterball Elite','Scroll Rack','Sorcerer Class'}
SPELL_TUTORS={'Mystical Tutor','Muddle the Mixture','Spellseeker','Step Through'}
COMBO_A={'Storm-Kiln Artist','Searing Touch'}
COMBO_B={'Young Pyromancer','Phyrexian Altar','Mystic Speculation'}
COMBO_C={'Stormsplitter','Sorcerer Class','Mystic Speculation'}

N=120000
rng=np.random.default_rng(2026102722)
metrics={v:{t:Counter() for t in [3,4,5,6,8,10]} for v in ['v1.4','v1.5']}
opening={v:Counter() for v in metrics}
for i in range(N):
    # Paired shuffles share the same slots, with the four edited cards substituted.
    perm=rng.permutation(99)
    for ver,dd in [('v1.4',deck14),('v1.5',new_names)]:
        seen=[dd[k] for k in perm]
        op=seen[:7]
        lc=sum(x in LANDS for x in op)
        opening[ver]['2_to_4_lands']+=2<=lc<=4
        opening[ver]['0_to_1_lands']+=lc<=1
        opening[ver]['5_plus_lands']+=lc>=5
        for t in [3,4,5,6,8,10]:
            s=set(seen[:7+t]); m=metrics[ver][t]
            m['rock_seen']+=bool(s&ROCKS)
            m['two_or_more_rocks_seen']+=len(s&ROCKS)>=2
            m['cheap_wizard_seen']+=bool(s&CHEAP_WIZARDS)
            m['cheap_wizard_and_rock_seen']+=bool(s&CHEAP_WIZARDS) and bool(s&ROCKS)
            m['cheap_cantrip_seen']+=bool(s&CHEAP_CANTRIP)
            m['any_draw_filter_or_tutor_seen']+=bool(s & (CHEAP_DRAW|DRAW_FILTER_PERMANENTS|SPELL_TUTORS))
            m['two_draw_filter_or_tutors_seen']+=len(s & (CHEAP_DRAW|DRAW_FILTER_PERMANENTS|SPELL_TUTORS))>=2
            m['early_engine_seen']+=bool(s & ENGINE)
            m['counter_seen']+=bool(s & COUNTERS)
            m['engine_and_counter_seen']+=bool(s & ENGINE) and bool(s & COUNTERS)
            m['converter_seen']+=bool(s & CONVERTERS)
            m['buyback_seen']+=bool(s & LOOP_BUYBACK)
            m['buyback_with_mana_source_seen']+=bool(s & LOOP_BUYBACK) and bool(s & {'Storm-Kiln Artist','Phyrexian Altar','Sorcerer Class'})
            m['full_simple_combo_A_seen']+=COMBO_A<=s
            m['full_simple_combo_B_seen']+=COMBO_B<=s
            m['full_simple_combo_C_seen']+=COMBO_C<=s
            m['x_and_copy_seen']+= 'Mathemagics' in s and bool(s & COPIERS)
            m['x_and_2copiers_seen']+= 'Mathemagics' in s and len(s&COPIERS)>=2
            m['wizard_control_seen']+=bool(s & WIZARD_CONTROL)
            m['wizard_control_plus_real_wizard_seen']+=bool(s & WIZARD_CONTROL) and bool(s & CHEAP_WIZARDS)
            m['cryptic_gateway_seen']+='Cryptic Gateway' in s
            m['gateway_plus_expensive_seen']+= ('Cryptic Gateway' in s and bool(s & EXPENSIVE))
            m['gateway_plus_converter_and_expensive_seen']+= ('Cryptic Gateway' in s and bool(s & EXPENSIVE) and bool(s & CONVERTERS))
            m['sigil_plus_wizard_and_x_seen']+= ('Sigil Tracer' in s and 'Mathemagics' in s and len(s & CHEAP_WIZARDS)>=2)

# Ramp-only early turns, using a conservative one rock per turn sequencing.
DUAL={'Command Tower','Steam Vents','Training Center','Stormcarved Coast','Sulfur Falls','Shivan Reef','Spirebluff Canal','Riverglide Pathway','Fiery Islet','Cascade Bluffs','Exotic Orchard'}
BL={'Island','Otawara, Soaring City','Mystic Sanctuary'}
RD={'Mountain','Sokenzan, Crucible of Defiance'}
BASIC_TYPES_ISLAND={'Island','Steam Vents'}
BASIC_TYPES_MOUNTAIN={'Mountain','Steam Vents'}
@lru_cache(maxsize=200000)
def pools(key):
    sources=sorted(key)
    if 'Izzet Signet' in sources:
        sources.remove('Izzet Signet'); signet=True
    else: signet=False
    poss={(0,0,0)}
    for src in sources:
        if src in BL: choices=[(1,0,0)]
        elif src in RD: choices=[(0,1,0)]
        elif src in DUAL or src in ['Arcane Signet','Fellwar Stone','Talisman of Creativity']:
            choices=[(1,0,0),(0,1,0)]
            if src=='Talisman of Creativity': choices+=[(0,0,1)]
        elif src=='Sol Ring': choices=[(0,0,2)]
        else: choices=[(0,0,1)]
        poss={(u+a,r+b,c+d) for u,r,c in poss for a,b,d in choices}
    if signet:
        after=set()
        for u,r,c in poss:
            if u+r+c>=1:
                if u>0:after.add((u,r+1,c))
                if r>0:after.add((u+1,r,c))
                if c>0:after.add((u+1,r+1,c-1))
        poss|=after
    return tuple(poss)
def can_pay(source_names,gen=0,blue=0,red=0):
    return any(u>=blue and r>=red and u+r+c>=gen+blue+red for u,r,c in pools(tuple(sorted(source_names))))

def untapped_land(new, existing):
    if new=='Mystic Sanctuary':return sum(x in BASIC_TYPES_ISLAND for x in existing)>=3
    if new=='Stormcarved Coast':return len(existing)>=2
    if new=='Sulfur Falls':return any(x in BASIC_TYPES_ISLAND or x in BASIC_TYPES_MOUNTAIN for x in existing)
    if new=='Spirebluff Canal':return len(existing)<3
    if new=='Fabled Passage':return len(existing)>=3 # resolves into untapped basic at 4 lands
    return True

def choice_land(hand,existing):
    cand=[x for x in hand if x in LANDS]
    if not cand:return None
    def score(x):
        now=untapped_land(x,existing)
        # prefer early untapped, then color coverage; avoid Fabled early if not needed
        owned=''.join('U' if n in BL else 'R' if n in RD else 'UR' if n in DUAL or n=='Fabled Passage' else '' for n in existing)
        cols='UR' if x in DUAL or x=='Fabled Passage' else 'U' if x in BL else 'R' if x in RD else ''
        return ((3 if now else 0), (2 if ('U' not in owned and 'U' in cols) or ('R' not in owned and 'R' in cols) else 0), (1 if x in DUAL else 0), (1 if x!='Fabled Passage' else 0))
    return max(cand,key=score)

def land_source(x,existing):
    # Fabled Passage searches for a basic as a replacement land
    if x!='Fabled Passage':return x
    owned=''.join('U' if n in BL else 'R' if n in RD else 'UR' if n in DUAL else '' for n in existing)
    return 'Mountain' if 'R' not in owned and 'U' in owned else 'Island'

M=18000
mana={t:Counter() for t in [3,4,5,6,7]}
for i in range(M):
    arr=[deck14[j] for j in rng.permutation(99)]
    hand=arr[:7]; idx=7
    landson=[]; rocks=[]; tap_new=False
    for t in range(1,8):
        hand.append(arr[idx]);idx+=1
        new=choice_land(hand,landson)
        if new:
            hand.remove(new)
            tap_new=not untapped_land(new,landson)
            landson.append(land_source(new,landson))
        else:tap_new=False
        sources=list(landson)+list(rocks)
        if tap_new and new:sources.remove(landson[-1])
        if t in mana:
            mana[t]['five_mana_UR']+=can_pay(sources,3,1,1)
            mana[t]['five_mana_UR_plus_one_U']+=can_pay(sources,3,2,1)
            relevant_seen=set(arr[:7+t])
            mana[t]['ready_with_one_U_counter_seen'] += (can_pay(sources,3,2,1) and bool(relevant_seen & {'Swan Song',"An Offer You Can't Refuse",'Flusterstorm'}))
            mana[t]['ready_with_any_counter_seen'] += (can_pay(sources,3,2,1) and bool(relevant_seen & COUNTERS))
            mana[t]['ready_plus_cheap_wizard_seen'] += (can_pay(sources,3,1,1) and bool(relevant_seen & CHEAP_WIZARDS))
            mana[t]['ready_plus_rock_played'] += (can_pay(sources,3,1,1) and bool(rocks))
            mana[t]['five_mana_UR_plus_two_U']+=can_pay(sources,3,3,1)
            mana[t]['three_mana_UR']+=can_pay(sources,1,1,1)
            mana[t]['at_least_three_lands']+=len(landson)>=3
            mana[t]['at_least_four_lands']+=len(landson)>=4
        # Prioritize up to one conventional rock, no other spells or cantrips.
        for rock in ['Sol Ring','Arcane Signet','Talisman of Creativity','Izzet Signet','Fellwar Stone','Mind Stone']:
            if rock in hand and can_pay(sources,1 if rock=='Sol Ring' else 2):
                hand.remove(rock);rocks.append(rock);break

results={
 'method': 'paired 120k shuffled Commander draws with one card drawn each turn and no mulligan; separate 18k no-opponent ramp-only play sequences with one ramp artifact per turn; exact decklists and deterministic seed',
 'versions':{
  'v1.4':{'opening':{k:round(v/N*100,2) for k,v in opening['v1.4'].items()},'draw_access':{str(t):{k:round(v/N*100,2) for k,v in metrics['v1.4'][t].items()} for t in metrics['v1.4']}},
  'v1.5':{'opening':{k:round(v/N*100,2) for k,v in opening['v1.5'].items()},'draw_access':{str(t):{k:round(v/N*100,2) for k,v in metrics['v1.5'][t].items()} for t in metrics['v1.5']}}
 },
 'ramp_only_same_both_versions':{str(t):{k:round(v/M*100,2) for k,v in mana[t].items()} for t in mana},
 'caveats':['Draw counts do not imply castability or win rates.','The two decks have exactly the same lands and six rocks; hence ramp-only outcomes are identical by construction.','Ramp-only sequences ignore playing creatures, interaction, cantrips, additional mana from Storm-Kiln Artist/Sorcerer Class, artifact tutoring, and opponents; one ramp artifact cast per turn.','Multi-land color selection assumes available opponent colors for Exotic Orchard and Fellwar Stone, and simplified modal-land/signet handling.','Raw access assumes no mulligans or additional card draw; Jace, Kitsa, Scroll Rack, Whispers, and gateway effects are not resolved.','Cryptic Gateway coaccess needs hand creatures and two compatible untapped creatures; listed rates are a weak upper bound.']
}
out=ROOT/'magnus_v14_v15_comparison.json'
out.write_text(json.dumps(results,indent=2))
print('mana',results['ramp_only_same_both_versions'])
for t in [4,5,6,8,10]:
 print('TURN',t)
 for k in ['cheap_wizard_seen','cheap_wizard_and_rock_seen','cheap_cantrip_seen','any_draw_filter_or_tutor_seen','two_draw_filter_or_tutors_seen','early_engine_seen','counter_seen','engine_and_counter_seen','buyback_seen','buyback_with_mana_source_seen','x_and_copy_seen','x_and_2copiers_seen','gateway_plus_expensive_seen','gateway_plus_converter_and_expensive_seen','sigil_plus_wizard_and_x_seen']:
  print(k,results['versions']['v1.4']['draw_access'][str(t)].get(k,0),results['versions']['v1.5']['draw_access'][str(t)].get(k,0))
print('CREATED',out)
