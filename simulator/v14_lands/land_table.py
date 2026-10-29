"""Land entry and stack-based basic fetch on the v13 live engine.

No additional caches; historic engines remain standalone comparison baselines.
"""
from pathlib import Path
from dataclasses import dataclass
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v13_engines'))
from engine_table import EngineTable
from kernel import WorldEntry
from rules import Event
from land_cards import RULES,EntryRule,FETCH,install


@dataclass(frozen=True)
class EntryChoice:
    controller:int
    name:str
    other_lands:int
    other_islands:int
    opponents:int
    life:int


@dataclass(frozen=True)
class BasicOption:
    object_id:int
    name:str
    subtypes:frozenset[str]


@dataclass(frozen=True)
class FetchChoice:
    controller:int
    source_id:int
    basics:tuple[BasicOption,...]


class LandTable(EngineTable):
    def __init__(self,*args,**kwargs):
        self.land_events=[]
        super().__init__(*args,**kwargs)
        install(self)

    def entry_choices(self,player,oid,force_tapped=False):
        obj=self.rules.get(oid);rule=RULES.get(obj.card.name,EntryRule())
        lands=self.rules.controlled(player.seat,{'land'})
        request=EntryChoice(player.seat,obj.card.name,len(lands),sum('Island' in o.subtypes for o in lands),
                            sum(p is not player and p.eliminated_round is None for p in self.players),player.life)
        life=0;face=None
        if rule.modal:
            policy=getattr(self,'pathway_policy',None)
            u=sum('Island' in o.subtypes for o in lands);r=sum('Mountain' in o.subtypes for o in lands)
            face=policy(request) if policy else 'U' if u<=r else 'R'
            if face not in ('U','R'):raise ValueError('Choose a supported Pathway face U or R')
        if rule.condition=='pay_life':
            policy=getattr(self,'shock_land_policy',None)
            pay=policy(request) if policy else player.life>rule.life and not force_tapped
            if type(pay) is not bool:raise ValueError('Shock-land choice must be boolean')
            if pay and player.life<rule.life:raise ValueError('Cannot pay the shock-land life cost')
            life=rule.life if pay else 0;tapped=not pay
        elif rule.condition=='opponents':tapped=request.opponents<rule.threshold
        elif rule.condition=='other_lands_min':tapped=request.other_lands<rule.threshold
        elif rule.condition=='other_lands_max':tapped=request.other_lands>rule.threshold
        elif rule.condition=='other_islands':tapped=request.other_islands<rule.threshold
        elif rule.condition=='island_or_mountain':tapped=not any(o.subtypes&{'Island','Mountain'} for o in lands)
        elif rule.condition=='always_untapped':tapped=False
        else:raise NotImplementedError('Unknown land entry predicate')
        return bool(force_tapped or tapped),life,face

    def enter_land(self,player,oid,*,force_tapped=False,cause='effect',choices=None):
        obj=self.rules.get(oid)
        if 'land' not in obj.types or obj.zone=='battlefield':raise ValueError('Expected a land entering from another zone')
        tapped,life,face=choices if choices is not None else self.entry_choices(player,oid,force_tapped)
        if life:
            player.life-=life
            self.rules.events.append(Event('life_paid',player.seat,oid,amount=life))
        new=self.zones.move(oid,'battlefield');obj=self.rules.get(new)
        obj.controller=player.seat;obj.tapped=tapped
        self.world.views[new]=WorldEntry(player,None,'resource')
        self.rules.resource_names[new]=obj.card.name+(f' [{face}]' if face else '')
        self.rules._dirty()
        self.land_events.append(dict(kind='entry',controller=player.seat,name=obj.card.name,object_id=new,
                                     tapped=tapped,life_paid=life,cause=cause,face=face))
        self.emit('land_entered',controller=player.seat,object_id=new,tapped=tapped,cause=cause)
        self.note(f'    LAND ENTERS P{player.seat}: {self.rules.resource_names[new]} #{new}; tapped={tapped}; life_paid={life}; cause={cause}.')
        return new

    def play_land(self,player,card,turn):
        s=self.spell_stack
        if (not player.alive or player.eliminated_round is not None or player.seat!=self.active_seat or self.phase!='main' or s.frames or s.pending
                or s.resolving or s.running and s.holder!=player.seat):
            raise ValueError('Land play requires own main phase, priority and an empty stack')
        if card not in player.hand or card.kind!='land':raise ValueError('Land not available in hand')
        if getattr(player,'_land_turn',None)==self.safe_runner.turn:raise ValueError('Land already played this turn')
        choices=self.entry_choices(player,card.object_id)
        oid=self.enter_land(player,card.object_id,cause='land_play',choices=choices)
        player._land_turn=self.safe_runner.turn
        self.emit('land_played',controller=player.seat,round=turn,object_id=oid)
        return card.name if self.rules.get(oid).tapped else None

    def resolve_activation(self,frame):
        if frame.ability.operation!='search_basic_land':return super().resolve_activation(frame)
        player=self.players[frame.controller]
        basics=tuple(BasicOption(oid,self.rules.get(oid).card.name,self.rules.get(oid).subtypes)
                     for oid in self.zones.ids(frame.controller,'library')
                     if 'land' in self.rules.get(oid).types and 'basic' in self.rules.get(oid).card.supertypes)
        request=FetchChoice(frame.controller,frame.source_id,basics)
        policy=getattr(self,'fetch_policy',None)
        lands=self.rules.controlled(frame.controller,{'land'})
        u=sum('Island' in o.subtypes for o in lands);r=sum('Mountain' in o.subtypes for o in lands)
        desired='Island' if u<=r else 'Mountain'
        default=next((b.object_id for b in basics if desired in b.subtypes),basics[0].object_id if basics else None)
        chosen=policy(request) if policy else default
        if chosen is not None and chosen not in {b.object_id for b in basics}:raise ValueError('Fetch must choose a basic land in the controller library, or fail to find')
        new=self.enter_land(player,chosen,force_tapped=True,cause='basic_fetch') if chosen is not None else None
        self.zones.shuffle(frame.controller)
        enough=player.lands>=4
        if new is not None and enough:self.rules.get(new).tapped=False;self.rules._dirty()
        self.land_events.append(dict(kind='fetch_resolved',controller=frame.controller,source_id=frame.source_id,
                                     fetched_id=new,lands_at_resolution=player.lands,untapped=bool(new is not None and enough)))
        self.rules.events.append(Event('ability_resolved',frame.controller,frame.source_id))
        self.emit('ability_resolved',controller=frame.controller,source_id=frame.source_id,ability=frame.ability.key)
        self.note(f'    BASIC FETCH P{frame.controller}: source #{frame.source_id}; fetched #{new}; lands={player.lands}; untapped={bool(new is not None and enough)}; shuffled.')
        return True

    def choose_priority(self,seat,choices):
        # A distinct development choice, rather than the old automatic fetch.
        if not self.spell_stack.frames and self.players[seat].alive:
            choice=next((c for c in choices if c.kind=='activate' and c.ability==FETCH),None)
            if choice:return choice
        return super().choose_priority(seat,choices)

    def diagnostics(self):
        d=super().diagnostics()
        d['v14']=dict(entry_conditions=True,basic_land_types=True,fabled_passage_stack_ability=True,
                       land_events=len(self.land_events),new_caching=False,
                       limits=['Mystic Sanctuary graveyard trigger deferred','utility/channel abilities deferred',
                               'Pathway mana-face subset','no simultaneous multi-land-entry system'])
        return d
