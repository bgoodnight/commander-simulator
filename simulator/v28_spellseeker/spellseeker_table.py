"""Spellseeker's optional enter-the-battlefield search."""
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
import re,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v27_wizard_tutors'))
from wizard_tutor_table import WizardTutorTable, IDENTITIES
from utility_table import UtilityStack
from rules import Cost,Ability,Event
from simulation import Action
from commander_sim.legacy_tutor_ops import resolve_historical_search

NAME='Spellseeker'
MANA_COSTS={r['name']:r['mana_cost'] for r in IDENTITIES['cards']}

def library_mana_value(name):
    if name not in MANA_COSTS or MANA_COSTS[name] is None:raise NotImplementedError('Unknown mana value for '+name)
    symbols=re.findall(r'\{([^}]+)\}',MANA_COSTS[name]);total=0
    for sym in symbols:
        if sym.isdigit():total+=int(sym)
        elif sym=='X':continue
        elif sym in ('U','R','U/P'):total+=1
        else:raise NotImplementedError('Unsupported mana symbol '+sym)
    return total

class SeekerStack(UtilityStack):
    trigger_operations=UtilityStack.trigger_operations|{'spellseeker_search'}

class SpellseekerTable(WizardTutorTable):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.spell_stack=SeekerStack(self)
        key='named:'+NAME
        self.zones.specs[key]=replace(self.zones.specs[key],kind=NAME,card_type='creature',effect='named_spellseeker',
            mana_value=3,colored_cost=MappingProxyType({'U':1,'R':0}),parameters=MappingProxyType({'coverage':'verified_subset'}))
        for obj in self.rules.objects.values():
            if obj.card.card_id==key:
                obj.card=replace(obj.card,types=frozenset({'creature'}),subtypes=frozenset({'Human','Wizard'}),
                    cost=Cost(generic=2,blue=1),base_power=1,base_toughness=1,coverage='verified_subset',
                    abilities=(Ability('triggered',event='creature_entered',op='spellseeker_search',condition='self_enters'),))
        self.rules._dirty();self.register_effect('named_spellseeker',self.resolve_spellseeker)
        self.on_event(self.spellseeker_entered)

    def action_for(self,player,card):
        if card.name!=NAME:return super().action_for(player,card)
        cost=self.rules.modified_cost(player.seat,frozenset({'creature'}),Cost(generic=2,blue=1))
        action=Action(player.seat,NAME,'creature',card.effect,cost.total,parameters={**card.parameters,'U':1,'R':0})
        return self.adjust_named_action_cost(action)

    def resolve_spellseeker(self,table,action):
        self.add_creature(self.players[action.actor],1,1,NAME)

    def spellseeker_entered(self,table,event,action,payload):
        if event!='creature_entered':return
        oid=payload['creature_id'];obj=self.rules.objects.get(oid)
        if not obj or obj.card.name!=NAME:return
        self._apply_pending(self.rules.triggers(Event('creature_entered',obj.controller,oid)))

    def resolve_trigger(self,item):
        if item.op!='spellseeker_search':return super().resolve_trigger(item)
        policy=getattr(self,'spellseeker_search_policy',None)
        take=policy(item.controller,item.source_id) if policy else True
        if type(take) is not bool:raise ValueError('Spellseeker search choice must be boolean')
        if not take:
            self.tutor_events.append(('spellseeker_declined',item.controller,None,None));return
        seat=item.controller
        resolve_historical_search(self,seat,'spellseeker',mana_value=library_mana_value)
