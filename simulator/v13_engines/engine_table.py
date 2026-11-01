"""Exact selection and a focused engine-text batch on the v12 live engine."""
from pathlib import Path
import sys
from dataclasses import replace,dataclass
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v12_combat'))
from expanded import CombatTable
from stepped import StepStack
from rules import Event,Modifier,TriggerResult
from selection import Selection
from engine_turns import EngineDriver
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from commander_sim.legacy_common_ops import DrawDiscard,apply_draw_discard
import engine_cards as engine_provider


class EngineStack(StepStack):
    trigger_operations=StepStack.trigger_operations|{'pump_self','optional_loot','copy_source_until_end','exile_object'}

    def checkpoint(self):
        super().checkpoint()
        # Refresh the legacy pilot projection of descriptor-derived power.
        for obj in self.table.rules.on_battlefield():
            if any(a.op=='power_per_controlled_type' for a in obj.card.abilities):
                self.table.world.refresh(obj.object_id)


@dataclass(frozen=True)
class DelayedExile:
    controller:int
    object_id:int
    due_end:int


class EngineTable(CombatTable):
    def __init__(self,*args,**kwargs):
        self.end_step_serial=0;self.delayed_exiles=[];self.engine_events=[]
        super().__init__(*args,**kwargs)
        engine_provider.install(self)
        self.spell_stack=EngineStack(self);self.selection=Selection(self)

    def run(self,max_rounds=8):return EngineDriver(self).run(max_rounds)

    def add_creature(self,player,*args,**kwargs):
        creature=super().add_creature(player,*args,**kwargs)
        if creature and hasattr(self,'upgraded_definitions') and creature.name in self.upgraded_definitions:
            obj=self.rules.get(creature.id)
            obj.card=replace(self.upgraded_definitions[creature.name],card_id=obj.card.card_id)
            self.rules._dirty()
        return creature

    def _apply_pending(self,pending):
        for item in pending:
            if item.op=='copy_source_until_end':
                obj=self.rules.objects.get(item.source_id)
                if obj:item=replace(item,args=item.args+(('copiable',obj.card),))
            self.spell_stack.trigger(item)

    def named_triggers(self,table,event,action,payload):
        if event=='spell_countered_by':
            self._apply_pending(self.rules.triggers(Event(event,controller=payload['controller'])))
        else:super().named_triggers(table,event,action,payload)

    def resolve_selection(self,table,action):
        if action.source not in engine_provider.SELECTION:return super().resolve_selection(table,action)
        self.selection.resolve(action.source,action.actor)

    def pay_spell(self,player,card,action,response=False):
        result=super().pay_spell(player,card,action,response)
        if player is self.details and card.name in set(engine_provider.SELECTION)-{'Frantic Search'}:
            player.coverage['approx']-=1;player.coverage['supported']+=1
        return result

    def resolve_trigger(self,item):
        args=dict(item.args);player=self.players[item.controller]
        if item.op=='pump_self':
            obj=self.rules.objects.get(item.source_id)
            if obj and obj.zone=='battlefield':
                self.rules.add_modifier(obj.object_id,Modifier(args['power'],args['toughness'],expires_at=args['duration']))
                self.world.refresh(obj.object_id)
                self.engine_events.append(('prowess',obj.object_id,obj.power,obj.toughness))
                self.note(f'    PROWESS #{obj.object_id}: now {obj.power}/{obj.toughness} until cleanup.')
        elif item.op=='optional_loot':
            policy=getattr(self,'loot_policy',None)
            take=policy(item.controller,item.source_id) if policy else True
            if type(take) is not bool:raise ValueError('Loot choice must be boolean')
            if take:
                apply_draw_discard(self,item.controller,DrawDiscard(1,1,'baral_discard'),selection=self.selection)
            self.engine_events.append(('loot',item.controller,take))
            self.note(f'    BARAL LOOT P{item.controller}: accepted={take}.')
        elif item.op=='copy_source_until_end':
            obj=self.rules.objects.get(item.source_id)
            definition=obj.card if obj and obj.zone=='battlefield' else args.get('copiable')
            if definition is None:raise ValueError('Missing last-known copiable values')
            creature=self.add_creature(player,definition.base_power,definition.base_toughness,definition.name,
                                       token=True,keywords=tuple(definition.keywords))
            copy=self.rules.get(creature.id);copy.card=definition
            self.rules._dirty()
            self.delayed_exiles.append(DelayedExile(item.controller,copy.object_id,self.end_step_serial+1))
            self.engine_events.append(('copy_created',item.source_id,copy.object_id,self.end_step_serial+1))
            self.note(f'    COPY #{copy.object_id}: next end-step #{self.end_step_serial+1}; copiable base only.')
        elif item.op=='exile_object':
            oid=args['object_id'];obj=self.rules.objects.get(oid)
            if obj and obj.zone=='battlefield':self.world.move(oid,'exile','exile')
            self.engine_events.append(('delayed_exile',oid))
            self.note(f'    DELAYED EXILE #{oid}: completed (departed objects are ignored).')
        else:return super().resolve_trigger(item)

    def begin_end_step(self):
        self.end_step_serial+=1;due=[d for d in self.delayed_exiles if d.due_end<=self.end_step_serial]
        self.delayed_exiles[:]=[d for d in self.delayed_exiles if d.due_end>self.end_step_serial]
        for d in due:
            if self.players[d.controller].alive:
                self.spell_stack.trigger(TriggerResult(d.object_id,d.controller,'exile_object',args=(('object_id',d.object_id),)))
        self.note(f'    END-STEP #{self.end_step_serial}: {len(due)} delayed exile abilities due.')

    def diagnostics(self):
        d=super().diagnostics()
        d['approx_definitions']=[n for n in d['approx_definitions'] if n not in engine_provider.SELECTION]
        d['known_rules_gaps']=[x for x in d['known_rules_gaps'] if 'temporary-token expiry' not in x]
        d['v13']=dict(exact_selection=list(engine_provider.SELECTION),engine_text=list(engine_provider.UPGRADED),
                       delayed_pending=len(self.delayed_exiles),selection_choices=len(self.selection.history),
                       limits=['no live spell copies or replacement/draw triggers','limited copiable-value model',
                               'deterministic default pilot; explicit policies supported','special lands remain partial'])
        return d
