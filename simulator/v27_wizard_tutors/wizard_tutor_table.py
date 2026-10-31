"""Fabricate plus Step Through's wizardcycling ability."""
from dataclasses import dataclass,replace
from pathlib import Path
from types import MappingProxyType
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from commander_sim.queries import Query,Match
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v26_search'))
from search_table import SearchTable
from priority import Choice
from rules import Cost,Event
from simulation import Action

FABRICATE='Fabricate';STEP='Step Through'
ARTIFACT_QUERY=Query(types_all=frozenset({'artifact'}))
WIZARD_QUERY=Query(subtypes_all=frozenset({'Wizard'}))
IDENTITIES=json.loads((Path(__file__).resolve().parents[1]/'v20_verified_types'/'CARD_IDENTITIES.json').read_text())

@dataclass(frozen=True)
class Wizardcycling:
    key:str='step_through_wizardcycling'
    operation:str='wizardcycling'

WIZARDCYCLING=Wizardcycling()

class WizardTutorTable(SearchTable):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        # Install printed subtypes for canonical cards in all zones; additional
        # supported type-changing effects are derived by the existing kernel.
        subtype_map={}
        for row in IDENTITIES['cards']:
            front=row['type_line'].split(' // ',1)[0]
            subtype_map[row['name']]=frozenset(front.split(' — ',1)[1].split()) if ' — ' in front else frozenset()
        for obj in self.rules.objects.values():
            if obj.owner==self.detailed_seat and not obj.token and obj.card.name in subtype_map:
                obj.card=replace(obj.card,subtypes=subtype_map[obj.card.name])
        key='named:'+FABRICATE
        self.zones.specs[key]=replace(self.zones.specs[key],kind=FABRICATE,card_type='sorcery',effect='named_fabricate',
             mana_value=3,colored_cost=MappingProxyType({'U':1,'R':0}),parameters=MappingProxyType({'coverage':'verified_subset'}))
        for obj in self.rules.objects.values():
            if obj.card.card_id==key:obj.card=replace(obj.card,types=frozenset({'sorcery'}),cost=Cost(generic=2,blue=1),coverage='verified_subset')
        self.register_effect('named_fabricate',self.resolve_fabricate)
        self.rules._dirty()

    def action_for(self,player,card):
        if card.name!=FABRICATE:return super().action_for(player,card)
        cost=self.rules.modified_cost(player.seat,frozenset({'sorcery'}),Cost(generic=2,blue=1))
        action=Action(player.seat,FABRICATE,'sorcery',card.effect,cost.total,parameters={**card.parameters,'U':1,'R':0})
        return self.adjust_named_action_cost(action)

    def search_to_hand(self,seat,eligible,kind):
        request=self.selection.request(kind,seat,eligible)
        ranked=sorted(request.cards,key=lambda c:-self.selection.score(seat,c))
        default=ranked[0].object_id if ranked else None
        policy=getattr(self,'tutor_policy',None);chosen=policy(request) if policy else default
        if chosen is not None and chosen not in eligible:raise ValueError('Search must choose an eligible card or fail to find')
        name=self.rules.get(chosen).card.name if chosen is not None else None
        new=self.zones.move(chosen,'hand') if chosen is not None else None
        self.zones.shuffle(seat);self.tutor_events.append((kind,seat,new,name))
        self.note(f'    {kind.upper()} P{seat}: revealed {name}, put into hand, then shuffled.')

    def resolve_fabricate(self,table,action):
        seat=action.actor
        self.search_to_hand(seat,tuple(oid for oid in self.zones.ids(seat,'library') if ARTIFACT_QUERY.matches_kernel(self.rules,oid) is Match.YES),'fabricate')

    def wizardcycling_available(self,seat,oid):
        obj=self.rules.objects.get(oid)
        return bool(obj and obj.owner==seat and obj.zone=='hand' and obj.card.name==STEP
                    and self.resources.plan(seat,Cost(generic=2)) is not None)

    def priority_choices(self,seat):
        choices=list(super().priority_choices(seat))
        for oid in self.zones.ids(seat,'hand'):
            if self.wizardcycling_available(seat,oid):choices.append(Choice('wizardcycle',source_id=oid,ability=WIZARDCYCLING))
        return tuple(choices)

    def choose_priority(self,seat,choices):
        chosen=super().choose_priority(seat,choices)
        if chosen:return chosen
        if seat==self.active_seat and self.phase=='main' and not self.spell_stack.frames:
            return next((c for c in choices if c.kind=='wizardcycle'),None)
        return None

    def commit_choice(self,seat,choice):
        if choice.kind!='wizardcycle':return super().commit_choice(seat,choice)
        if self.spell_stack.resolving or self.spell_stack.holder!=seat:raise ValueError('No priority')
        if choice.ability!=WIZARDCYCLING or not self.wizardcycling_available(seat,choice.source_id):raise ValueError('Illegal wizardcycling')
        self.resources.pay(seat,Cost(generic=2));self.zones.move(choice.source_id,'graveyard','discard')
        self.spell_stack.activated(seat,choice.source_id,WIZARDCYCLING,label='Step Through: wizardcycling')
        self.rules.events.append(Event('ability_activated',seat,choice.source_id))
        self.rules.events.append(Event('cycled',seat,choice.source_id))
        self.emit('ability_activated',controller=seat,source_id=choice.source_id,ability=WIZARDCYCLING.key)
        self.emit('cycled',controller=seat,source_id=choice.source_id)

    def resolve_activation(self,frame):
        if frame.ability!=WIZARDCYCLING:return super().resolve_activation(frame)
        seat=frame.controller
        eligible=tuple(oid for oid in self.zones.ids(seat,'library') if WIZARD_QUERY.matches_kernel(self.rules,oid) is Match.YES)
        self.search_to_hand(seat,eligible,'wizardcycling')
        self.rules.events.append(Event('ability_resolved',seat,frame.source_id))
        self.emit('ability_resolved',controller=seat,source_id=frame.source_id,ability=WIZARDCYCLING.key)
        return True
