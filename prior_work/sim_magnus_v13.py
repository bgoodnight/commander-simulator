"""Reproducible approximate solitaire analysis of Magnus v1.3.
Rules-aware for deck composition/draw probabilities; coarse early mana simulation,
NOT a full MTG game simulator (no opponents, detailed colored mana, or optimal tutors).
"""
from pathlib import Path
from collections import Counter
import numpy as np, json

ROOT=Path('/mnt/data')
path=ROOT/'magnus_thousand_sons_v1_3.txt'
rows=[]; section=None
for ln in path.read_text().splitlines():
    st=ln.strip()
    if st.startswith('Commander') or st.startswith('Creatures (') or st.startswith('Artifacts and Enchantments (') or st.startswith('Instants and Sorceries (') or st.startswith('Lands ('):
        section=st.split(' (')[0]; continue
    if st and st[0].isdigit() and ' ' in st and section:
        n,name=st.split(' ',1)
        if n.isdigit(): rows.extend([(name,section)]*int(n))
assert len(rows)==100 and sum(s=='Commander' for _,s in rows)==1,Counter(s for _,s in rows)
deck=[name for name,sec in rows if sec != 'Commander']
assert len(deck)==99

LANDS={n for n,s in rows if s=='Lands'}
ROCKS={'Sol Ring','Arcane Signet','Talisman of Creativity','Izzet Signet'}
EARLY_TOKEN={'Young Pyromancer','Third Path Iconoclast'}
TOKEN_MAKERS=EARLY_TOKEN|{'Stormsplitter','Docent of Perfection','Deekah, Fractal Theorist','Pink Horror','The Lost and the Damned'}
CHEAP_DRAW={'Brainstorm','Ponder'}
COUNTERS={'Counterspell','Arcane Denial','Swan Song','An Offer You Can\'t Refuse','Flusterstorm','Muddle the Mixture'}
REMOVAL={'Pongify','Abrade','Chaos Warp','Chaos Mutation','Cyclonic Rift','March of Swirling Mist','Capsize'}
MANA_ENGINES={'Storm-Kiln Artist','Phyrexian Altar','Sorcerer Class','Resonating Lute'}
BUYBACK={'Searing Touch','Mystic Speculation','Haze of Rage','Whispers of the Muse','Capsize'}
RAMP_BASE=ROCKS

# Bigger sample for card access (the exact hypergeometric rates are easy to check).
SEED=20261027
rng=np.random.default_rng(SEED)
N=18_000
stats=Counter()
land_at_7=Counter()
byturn= {t:Counter() for t in (3,4,5,6,8,10)}
combo_by8=Counter()
for k in range(N):
    cards=rng.permutation(deck)
    op=list(cards[:7]); s=set(op); lc=sum(x in LANDS for x in op)
    land_at_7[lc]+=1
    stats['two_four_land_open']+=2<=lc<=4
    stats['zero_one_land_open']+=lc<=1
    stats['five_plus_land_open']+=lc>=5
    stats['two_four_land_earlytoken_open']+=(2<=lc<=4 and bool(s&EARLY_TOKEN))
    stats['two_four_land_rock_open']+=(2<=lc<=4 and bool(s&ROCKS))
    for t in byturn:
        seen=list(cards[:7+t])  # Commander draw on turn 1
        a=set(seen)
        v=byturn[t]
        v['lands_at_least_turn']+=sum(x in LANDS for x in seen)>=t
        v['at_least_3_lands']+=sum(x in LANDS for x in seen)>=3
        v['at_least_5_lands']+=sum(x in LANDS for x in seen)>=5
        v['any_rock']+=bool(a&ROCKS)
        v['any_early_token']+=bool(a&EARLY_TOKEN)
        v['any_token_maker']+=bool(a&TOKEN_MAKERS)
        v['any_counter']+=bool(a&COUNTERS)
        v['any_removal']+=bool(a&REMOVAL)
        v['any_mana_engine']+=bool(a&MANA_ENGINES)
        v['any_buyback']+=bool(a&BUYBACK)
        v['any_mana_engine_and_buyback']+=bool(a&MANA_ENGINES) and bool(a&BUYBACK)
    b=set(cards[:15]) # through turn eight
    combo_by8['searing_touch_kiln'] += {'Storm-Kiln Artist','Searing Touch'}<=b
    combo_by8['speculation_pyro_altar'] += {'Young Pyromancer','Phyrexian Altar','Mystic Speculation'}<=b
    combo_by8['speculation_storm_class'] += {'Stormsplitter','Sorcerer Class','Mystic Speculation'}<=b
    combo_by8['speculation_storm_altar'] += {'Stormsplitter','Phyrexian Altar','Mystic Speculation'}<=b
    combo_by8['any_buyback_and_any_engine'] += bool(b&BUYBACK) and bool(b&MANA_ENGINES)
    combo_by8['all_engine_spells'] += {'Sorcerer Class','Phyrexian Altar','Storm-Kiln Artist'}<=b
    combo_by8['mathemagics_and_copy'] += 'Mathemagics' in b and bool(b&{'Twincast','Reverberate','Reiterate','Tzaangor Shaman','Dualcaster Mage'})
    combo_by8['mathemagics_and_two_copy_spells'] += 'Mathemagics' in b and len(b&{'Twincast','Reverberate','Reiterate'})>=2

# Monte Carlo 1 London mulligan: keep raw 7 with 2-4 lands, otherwise redraw 7, bottom one appropriate card.
# Does not count 1-land Sol Ring exception or context-dependent keeps.
M=10_000
mull=Counter()
for k in range(M):
    p=list(rng.permutation(deck)[:7]); n=sum(x in LANDS for x in p)
    if n<2 or n>4:
        p=list(rng.permutation(deck)[:7]); n=sum(x in LANDS for x in p)
        mull['mulligan_taken']+=1
        bottom = next((c for c in p if (c not in LANDS if n<=4 else c in LANDS)),p[0])
        p.remove(bottom)
    nl=sum(x in LANDS for x in p)
    mull['two_four_lands']+=2<=nl<=4
    mull['zero_one_lands']+=nl<=1
    mull['five_plus_lands']+=nl>=5

# Coarse turns 1-6: lands and rocks ONLY, goldfish lines with no opponents, no other spells;
# mana color simulated only as broad U and R access for a commander cast, assumes untapped basics/most duallands.
# This is a *best-case sequencing potential* rather than an actual complete playthrough.
MULTI={'Command Tower','Steam Vents','Training Center','Stormcarved Coast','Sulfur Falls','Shivan Reef','Spirebluff Canal','Riverglide Pathway','Fiery Islet','Cascade Bluffs','Exotic Orchard','Fabled Passage'}
BLUE={'Island','Otawara, Soaring City','Mystic Sanctuary'}
RED={'Mountain','Sokenzan, Crucible of Defiance'}
OTHER={'Riptide Laboratory'}

def mana_land_color(x):
    if x in MULTI:return 'UR'
    if x in BLUE:return 'U'
    if x in RED:return 'R'
    return 'C'

def tapped_land(x,numlands,have_lands):
    if x=='Mystic Sanctuary':return sum(n=='Island' for n in have_lands)<3
    if x=='Fabled Passage':return numlands<4
    if x=='Stormcarved Coast':return numlands<=2
    if x=='Sulfur Falls':return not any(n in MULTI or n in BLUE or n in RED for n in have_lands)
    if x=='Spirebluff Canal':return numlands>3
    return False

def best_land(hand, battlefield, want_blue=True):
    landcards=[x for x in hand if x in LANDS]
    if not landcards:return None
    numlands=len(battlefield)+1
    cols=[mana_land_color(x) for x in battlefield]
    needU='U' not in ''.join(cols)
    needR='R' not in ''.join(cols)
    # prefer untapped, then color fixing, then mono over scarce dual when not needed
    def key(x):
        return (not tapped_land(x,numlands,battlefield),
                (2 if mana_land_color(x)=='UR' else 1 if ((needU and mana_land_color(x)=='U') or (needR and mana_land_color(x)=='R')) else 0),
                1 if x in BLUE else 0)
    return max(landcards,key=key)

G=7_000
gold={t:Counter() for t in range(1,7)}
for it in range(G):
    d=list(rng.permutation(deck)); hand=list(d[:7]); d=d[7:]
    lands=[]; active_rocks=[]; played_rocks=[]
    for turn in range(1,7):
        hand.append(d.pop(0))
        chosen=best_land(hand,lands)
        if chosen:
            hand.remove(chosen); was_tapped=tapped_land(chosen,len(lands)+1,lands); lands.append(chosen)
        else: was_tapped=False
        avail=len(lands)-int(was_tapped)+2*('Sol Ring' in active_rocks)+sum(z!='Sol Ring' for z in active_rocks)
        # mana available before this turn's rock casting (mana only, no other spells)
        cols=''.join(mana_land_color(z) for z in lands)
        if any(z in active_rocks for z in ('Arcane Signet','Talisman of Creativity','Izzet Signet')):cols+='UR'
        gold[turn]['castable_5_mana']+=avail>=5 and 'U' in cols and 'R' in cols
        gold[turn]['have_5_raw_mana']+=avail>=5
        gold[turn]['have_4_raw_mana']+=avail>=4
        gold[turn]['land_count_3_plus']+=len(lands)>=3
        gold[turn]['land_count_4_plus']+=len(lands)>=4
        # spend turn on rock development. Simplified generic mana; Izzet Signet's initial need for activation ignored.
        pool=avail
        # cast ring first; it can tap immediately and add 2
        if 'Sol Ring' in hand and pool>=1:
            hand.remove('Sol Ring');active_rocks.append('Sol Ring');pool+=1
        for z in ('Arcane Signet','Talisman of Creativity','Izzet Signet'):
            if z in hand and pool>=2:
                hand.remove(z); active_rocks.append(z);pool-=1 if z!='Izzet Signet' and pool>2 else 2
                # note: for signet remaining >=1 would give 1 net, otherwise 0; above is simplified

res={
    'seed':SEED, 'deck_file':str(path), 'N_open':N, 'N_mull':M, 'N_mana':G,
    'count':dict(Counter(s for n,s in rows)),
    'opening': {k:round(v/N*100,2) for k,v in stats.items()},
    'opening_land_distribution':{str(k):round(v/N*100,2) for k,v in sorted(land_at_7.items())},
    'mulligan':{k:round(v/M*100,2) for k,v in mull.items()},
    'raw_access':{str(t):{k:round(v/N*100,2) for k,v in d.items()} for t,d in byturn.items()},
    'combo_by_turn8_unassisted_access':{k:round(v/N*100,3) for k,v in combo_by8.items()},
    'mana_only_optimistic':{str(t):{k:round(v/G*100,2) for k,v in d.items()} for t,d in gold.items()},
    'caveat':'Openings and raw access are exact-shuffle empirical probabilities; combo assembly is card-seen only, not mana/board readiness. Mana curve ignores spending on nonrock cards, mulligans, tutors, full color and ETB constraints, and opponent interaction.'
}
(ROOT/'magnus_v13_sim_results.json').write_text(json.dumps(res,indent=2))
print(json.dumps(res,indent=2))
