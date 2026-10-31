"""Frostboil Snarl's optional reveal entry and U/R mana."""
from dataclasses import replace
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v20_verified_types'))
from verified_table import VerifiedTable
from resources import fixed, U, R
from budget_table import BudgetPlayer, load_deck, card_spec
from collections import Counter
import random
import integrated as v6
import simulation as base

class EarlyManaPlayer(BudgetPlayer):
    def __init__(self,seat,seed,zones):
        base.Player.__init__(self,seat,'magnus',seed,[],v6.MagnusPilot())
        self.zones=zones;self.payment_policy=v6.ColoredPayment()
        self.ready_sources=[];self.floating=(0,0,0);self.commander_casts=0
        self.payments=[];self.treasures=0;self.coverage=Counter();self.unsupported_seen=Counter()
        self.block_policy='never';library=[]
        for (section,name),qty in load_deck().items():
            if section=='Library':
                spec=card_spec(name)
                if name=='Frostboil Snarl':spec=replace(spec,kind='land',card_type='land',effect='none')
                library.extend([spec]*qty)
        random.Random(seed+601).shuffle(library)
        for spec in library:zones.add_spec(spec,seat,detailed=True)
        zones.add_spec(v6.named_spec('Magnus the Red'),seat,'command',detailed=True)
        for name in ('Abrade','Arcane Adaptation'):
            if 'named:'+name not in zones.specs:zones.register(v6.named_spec(name),detailed=True)
        self.draw(7)
        if not 2 <= sum(c.kind=='land' for c in self.hand) <= 5:self.mulligan()

class EarlyManaTable(VerifiedTable):
    detailed_player_class=EarlyManaPlayer
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.snarl_events=[]

    def entry_choices(self,player,oid,force_tapped=False):
        obj=self.rules.get(oid)
        if obj.card.name!='Frostboil Snarl':return super().entry_choices(player,oid,force_tapped)
        eligible=tuple(o for o in self.zones.ids(player.seat,'hand') if o!=oid
                       and self.rules.get(o).types & {'land'} and self.rules.subtypes(o) & {'Island','Mountain'})
        policy=getattr(self,'snarl_reveal_policy',None)
        chosen=policy(player.seat,eligible) if policy else (eligible[0] if eligible else None)
        if chosen is not None and chosen not in eligible:raise ValueError('Snarl requires an Island or Mountain card in hand')
        self.snarl_events.append(('reveal',player.seat,chosen))
        self.note(f'    FROSTBOIL: revealed {self.rules.get(chosen).card.name if chosen else None}.')
        return bool(force_tapped or chosen is None),0,None
