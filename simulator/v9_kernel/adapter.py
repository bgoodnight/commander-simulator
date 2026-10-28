"""V9 incremental table adapter: move the existing real-deck seat without duplicating combat/stack rules.

This is still the v8 game with v6 hand/land/mana adapters. More than one detailed
player is intentionally rejected until those adapters are genuinely multi-seat.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'v8_central'))
from table import CentralTable

@dataclass(frozen=True)
class DeckProvider:
    """An explicit four-seat provider descriptor, separate from the pilot.

    'magnus' currently selects the fully modeled-but-partial v6 Magnus pilot;
    the other names select historical synthetic archetype pilots.
    """
    kind:str
    pilot:str='default'

    def __post_init__(self):
        from simulation import ARCHETYPES
        if self.kind not in (*ARCHETYPES,'magnus'):
            raise ValueError('Unsupported provider '+self.kind)
        if self.pilot!='default':
            raise NotImplementedError('Custom pilot policies have not been wired into the v8 legacy adapter')

class V9Table(CentralTable):
    """One existing CentralTable kernel and driver; arbitrary *single* detailed seat.

    The legacy pilot still uses separate hands/library and mana approximations.
    Do NOT claim this class can run two detailed seats or kernel-owned card zones.
    """
    def __init__(self,providers=None,seed=1,trace=False,opening=None):
        from simulation import ARCHETYPES
        if providers is None:
            providers=(DeckProvider('magnus'),DeckProvider('aggro'),DeckProvider('control'),DeckProvider('combo'))
        providers=tuple(p if isinstance(p,DeckProvider) else DeckProvider(p) for p in providers)
        if len(providers)!=4:raise ValueError('Exactly four providers required')
        details=[i for i,p in enumerate(providers) if p.kind=='magnus']
        if len(details)!=1:
            raise NotImplementedError('This incremental live adapter requires exactly one detailed Magnus seat; multiple are NOT supported')
        detail_seat=details[0]
        opponents=[p.kind for p in providers if p.kind!='magnus']
        super().__init__(opponents,seed=seed,trace=trace,opening=opening)
        original=[self.details,*self.players[1:]]
        ordered=iter(original[1:])
        self.players=[original[0] if i==detail_seat else next(ordered) for i in range(4)]
        for i,p in enumerate(self.players):p.seat=i
        self.providers=providers
        self.detailed_seat=detail_seat
        self._upkeep_actor=None
        # Historical detailed player created at seat zero. v8 battlefield starts empty,
        # so no object/controller IDs need remapping; all new IDs use current seat.
        assert not self.rules.objects

    def emit(self,name,action=None,**payload):
        # Correct v6's hardcoded controller=0 detailed-land event without editing history.
        if name=='land_played' and self._upkeep_actor is self.details:
            payload['controller']=self.details.seat
        return super().emit(name,action,**payload)

    def note(self,s):
        # Correct detailed upkeep's literal P0 labels at the reporting boundary.
        if getattr(self,'_upkeep_actor',None) is getattr(self,'details',None) and self.detailed_seat!=0:
            s=s.replace('P0 ',f'P{self.detailed_seat} ')
        return super().note(s)

    def upkeep(self,p,t):
        self._upkeep_actor=p
        try:return super().upkeep(p,t)
        finally:self._upkeep_actor=None

    def diagnostics(self):
        d=super().diagnostics()
        d['v9']={
            'providers':[p.kind for p in self.providers],
            'detailed_seat':self.detailed_seat,
            'kernel_view_consistent':self.world.consistent(),
            'migration_status':'single detailed seat portable; legacy hands/libraries/resources and counter-only priority remain active',
            'multi_detailed_games_supported':False,
            'authoritative_card_zones_in_live_game':False,
        }
        return d
