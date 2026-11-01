"""The committed v1.14 premium deck on the current v30 rules engine.

Historical tables keep their original decks. The five added card names are
recorded explicitly; unsupported spell effects remain uncastable.
"""
from collections import Counter
from dataclasses import replace
from pathlib import Path
import random,re,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v30_phyrexian_altar'))
from altar_table import AltarTable
from budget_table import BudgetPlayer,card_spec,load_deck as load_budget
from verified_table import read_types
from spellseeker_table import library_mana_value
from medallion_table import COLORS
from commander_sim.legacy_tutor_ops import resolve_historical_search
from rules import Cost
from resources import fixed,R
import integrated as v6
import simulation as base

DECK_PATH=Path(__file__).resolve().parents[2]/'decklists'/'magnus_thousand_sons_v1_14_premium.txt'
EXTRA_TYPES={'Cyclonic Rift':frozenset({'instant'}),'Reiterate':frozenset({'instant'}),
             'Training Center':frozenset({'land'}),'Otawara, Soaring City':frozenset({'land'}),
             'Lindblum, Industrial Regency':frozenset({'land'})}
EXTRA_VALUES={'Cyclonic Rift':2,'Reiterate':3}
EXTRA_COLORS={'Cyclonic Rift':('U',),'Reiterate':('R',)}

def load_premium():
    section=None;cards=Counter()
    for raw in DECK_PATH.read_text().splitlines():
        line=raw.strip()
        if not line:continue
        if line in ('Commander','Library'):section=line;continue
        m=re.fullmatch(r'(\d+) (.+)',line)
        if not m or section is None or int(m[1])<1:raise ValueError('Invalid deck entry: '+line)
        cards[(section,m[2])]+=int(m[1])
    if cards.get(('Commander','Magnus the Red'))!=1 or sum(v for (s,_),v in cards.items() if s=='Commander')!=1:raise ValueError('Expected Magnus commander')
    if sum(cards.values())!=100:raise ValueError('Expected 100 cards')
    if any(qty>1 and name not in {'Island','Mountain'} for (_,name),qty in cards.items()):raise ValueError('Duplicate nonbasic')
    return cards

def premium_spec(name):
    spec=card_spec(name)
    if name in EXTRA_VALUES:spec=replace(spec,card_type='instant')
    if name=='Lindblum, Industrial Regency':spec=base.CardSpec(name,'land',0,'land','none',{}, {})
    return spec

class PremiumPlayer(BudgetPlayer):
    def __init__(self,seat,seed,zones,deck=None):
        base.Player.__init__(self,seat,'magnus',seed,[],v6.MagnusPilot())
        self.zones=zones;self.payment_policy=v6.ColoredPayment()
        self.ready_sources=[];self.floating=(0,0,0);self.commander_casts=0
        self.payments=[];self.treasures=0;self.coverage=Counter();self.unsupported_seen=Counter()
        self.block_policy='never';library=[]
        cards=load_premium() if deck is None else {(section,name):qty for section,name,qty in deck.cards}
        for (section,name),qty in cards.items():
            if section!='Library':continue
            spec=premium_spec(name)
            library.extend([spec]*qty)
        random.Random(seed+601).shuffle(library)
        for spec in library:zones.add_spec(spec,seat,detailed=True)
        zones.add_spec(v6.named_spec('Magnus the Red'),seat,'command',detailed=True)
        # Existing rule installers assume their definitions exist even when a
        # particular deck does not contain those cards. Register definitions
        # only; this creates no physical objects and consumes no randomness.
        names={name for _,name in load_premium()} | {name for _,name in load_budget()}
        names.update(('Abrade','Arcane Adaptation'))
        for name in sorted(names):
            if 'named:'+name not in zones.specs:zones.register(premium_spec(name),detailed=True)
        self.draw(7)
        if not 2<=sum(c.kind=='land' for c in self.hand)<=5:self.mulligan()

class PremiumTable(AltarTable):
    detailed_player_class=PremiumPlayer
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for obj in self.rules.objects.values():
            if obj.card.name=='Lindblum, Industrial Regency':
                obj.card=replace(obj.card,subtypes=frozenset({'Town'}))
        self.rules._dirty()
        previous=self.resources.abilities
        def abilities(obj,visiting=frozenset()):
            if obj.card.name=='Lindblum, Industrial Regency' and obj.zone=='battlefield' and obj.object_id not in visiting:
                return fixed(R)
            return previous(obj,visiting)
        self.resources.abilities=abilities
    def entry_choices(self,player,oid,force_tapped=False):
        if self.rules.get(oid).card.name=='Lindblum, Industrial Regency':return True,0,None
        return super().entry_choices(player,oid,force_tapped)
    def deck_types(self):
        types=read_types();types.update(EXTRA_TYPES)
        if any(name not in types for _,name in load_premium()):raise ValueError('Missing premium type metadata')
        return types
    def resolve_search(self,table,action):
        if action.source!='Merchant Scroll':return super().resolve_search(table,action)
        colors={**COLORS,**EXTRA_COLORS}
        return resolve_historical_search(self,action.actor,'merchant_scroll',printed_colors=colors)
    def resolve_trigger(self,item):
        if item.op!='spellseeker_search':return super().resolve_trigger(item)
        policy=getattr(self,'spellseeker_search_policy',None)
        take=policy(item.controller,item.source_id) if policy else True
        if type(take) is not bool:raise ValueError('Spellseeker search choice must be boolean')
        if not take:
            self.tutor_events.append(('spellseeker_declined',item.controller,None,None));return
        def value(name):return EXTRA_VALUES[name] if name in EXTRA_VALUES else library_mana_value(name)
        return resolve_historical_search(self,item.controller,'spellseeker',mana_value=value)
