"""Targeted land triggers and activations on the v14 shared priority stack."""
from pathlib import Path
from dataclasses import dataclass,replace
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v14_lands'))
from land_table import LandTable
from engine_table import EngineStack
from priority import Choice
from rules import Event,TriggerResult
from utility_cards import ISLET,RIPTIDE,install
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from commander_sim.legacy_common_ops import (DrawDiscard,apply_draw_discard,
    ZoneTransfer,transfer_physical_object)

@dataclass(frozen=True)
class SanctuaryChoice:
    controller:int
    source_id:int
    eligible:tuple[int,...]

class UtilityStack(EngineStack):
    trigger_operations=EngineStack.trigger_operations|{'sanctuary_return'}

    def resolve_top(self):
        frame=self.frames[-1]
        if frame.kind=='triggered' and frame.trigger.op=='sanctuary_return':
            target=dict(frame.trigger.args)['target']
            if not self.table.sanctuary_target_legal(frame.controller,target):
                self.frames.pop();self.fizzled+=1
                self.history.append(('fizzle',frame.frame_id,frame.kind,frame.controller))
                self.table.note(f'    FIZZLE: Sanctuary target #{target} is no longer legal.')
                self.holder=self.table.active_seat;self.checkpoint();return
        return super().resolve_top()

class UtilityTable(LandTable):
    def __init__(self,*args,**kwargs):
        self.utility_events=[]
        super().__init__(*args,**kwargs)
        self.spell_stack=UtilityStack(self)
        install(self)

    def enter_land(self,player,oid,**kwargs):
        new=super().enter_land(player,oid,**kwargs)
        obj=self.rules.get(new)
        if obj.card.name=='Mystic Sanctuary' and not obj.tapped:
            self.spell_stack.trigger(TriggerResult(new,player.seat,'sanctuary_return'))
            self.note(f'    SANCTUARY #{new}: untapped entry triggered; target chosen at stack placement.')
        return new

    def sanctuary_target_legal(self,seat,oid):
        obj=self.rules.objects.get(oid)
        return bool(obj and obj.owner==seat and obj.zone=='graveyard' and obj.types&{'instant','sorcery'})

    def prepare_trigger(self,frame):
        if frame.trigger.op!='sanctuary_return':return frame
        eligible=tuple(oid for oid in self.zones.ids(frame.controller,'graveyard')
                       if self.sanctuary_target_legal(frame.controller,oid))
        if not eligible:
            self.utility_events.append(('sanctuary_no_target',frame.source_id))
            self.note('    SANCTUARY: no legal graveyard target; ability cannot be put on the stack.')
            return None
        request=SanctuaryChoice(frame.controller,frame.source_id,eligible)
        policy=getattr(self,'sanctuary_target_policy',None)
        chosen=policy(request) if policy else eligible[-1]
        if chosen not in eligible:raise ValueError('Sanctuary requires one legal graveyard target')
        trigger=replace(frame.trigger,args=(('target',chosen),))
        self.utility_events.append(('sanctuary_target',frame.source_id,chosen))
        return replace(frame,trigger=trigger)

    def resolve_trigger(self,item):
        if item.op!='sanctuary_return':return super().resolve_trigger(item)
        target=dict(item.args)['target']
        if not self.sanctuary_target_legal(item.controller,target):return
        policy=getattr(self,'sanctuary_return_policy',None)
        take=policy(item.controller,item.source_id,target) if policy else True
        if type(take) is not bool:raise ValueError('Sanctuary return choice must be boolean')
        if take:transfer_physical_object(self,item.controller,target,
            ZoneTransfer('graveyard','library',allowed_types_any=frozenset({'instant','sorcery'}),require_owner=True))
        self.utility_events.append(('sanctuary_resolved',item.source_id,target,take))
        self.note(f'    SANCTUARY: target #{target}; return to library top={take}.')

    def wizard_target_legal(self,seat,oid):
        obj=self.rules.objects.get(oid)
        return bool(obj and obj.controller==seat and self.rules.legal_target(seat,oid,{'creature','artifact','enchantment','land','planeswalker','battle'})
                    and 'Wizard' in self.rules.subtypes(oid))

    def activation_available(self,seat,oid,specification,target_frame=None):
        if specification==RIPTIDE:
            if not self.wizard_target_legal(seat,target_frame):return False
            obj=self.rules.objects.get(oid)
            if not obj or obj.zone!='battlefield' or obj.controller!=seat or obj.tapped:return False
            if specification not in self.activation_catalog.get(obj.card.card_id,()):return False
            return self.resources.plan(seat,specification.cost,excluded=(oid,)) is not None
        return super().activation_available(seat,oid,specification,target_frame)

    def priority_choices(self,seat):
        choices=list(super().priority_choices(seat))
        for source in self.rules.controlled(seat,{'land'}):
            if RIPTIDE not in self.activation_catalog.get(source.card.card_id,()):continue
            for target in self.rules.controlled(seat):
                if self.activation_available(seat,source.object_id,RIPTIDE,target.object_id):
                    choices.append(Choice('activate',source_id=source.object_id,ability=RIPTIDE,target_frame=target.object_id))
        return tuple(choices)

    def resolve_activation(self,frame):
        spec=frame.ability
        if spec not in (ISLET,RIPTIDE):return super().resolve_activation(frame)
        if spec==RIPTIDE:
            if not self.wizard_target_legal(frame.controller,frame.target_frame):
                self.utility_events.append(('riptide_fizzle',frame.source_id,frame.target_frame))
                return False
            transfer_physical_object(self,frame.controller,frame.target_frame,
                ZoneTransfer('battlefield','hand',require_controller=True,reason='bounce'))
            self.utility_events.append(('riptide_return',frame.source_id,frame.target_frame))
        else:
            apply_draw_discard(self,frame.controller,DrawDiscard(1))
            self.utility_events.append(('islet_draw',frame.source_id))
        self.rules.events.append(Event('ability_resolved',frame.controller,frame.source_id))
        self.emit('ability_resolved',controller=frame.controller,source_id=frame.source_id,ability=spec.key)
        return True

    def diagnostics(self):
        d=super().diagnostics()
        d['v14']['limits']=['Sanctuary/Islet/Riptide superseded by v15',
                            'channel abilities deferred','Pathway mana-face subset',
                            'no simultaneous multi-land-entry system']
        d['v15']=dict(utility_lands=['Mystic Sanctuary','Fiery Islet','Riptide Laboratory'],
                       utility_events=len(self.utility_events),new_caching=False,
                       limits=['no general graveyard protection or replacement layers',
                               'only one detailed Magnus deck','channel abilities deferred'])
        return d
