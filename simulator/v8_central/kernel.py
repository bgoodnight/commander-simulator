"""V8 authoritative shared battlefield and operation kernel.

All seat adapters use the same object registry. Legacy Creature/Permanent objects
are read-side views for existing pilots, not independent rules engines.
"""
from __future__ import annotations
from dataclasses import dataclass,replace
from typing import Any
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v7_rules'))
from rules import GameKernel,GameObject,CardDefinition,Modifier,Event,Cost,SafetyStop
from catalog import BY_NAME,DEFINITIONS

class CentralKernel(GameKernel):
    def damage_creatures_together(self,damage:dict[int,int]):
        """Simultaneous damage before a single state-based action check."""
        for oid,amount in damage.items():
            if amount<0:raise ValueError('negative damage')
            obj=self.get(oid)
            if obj.zone!='battlefield' or 'creature' not in obj.types:raise ValueError('invalid damage recipient')
        for oid,amount in damage.items():
            self.get(oid).damage_marked+=amount
            self.events.append(Event('damage_creature',target_id=oid,amount=amount))
        self._dirty();self.check_state_based()

    def attempt_destroy_many(self,ids:list[int],commander_ids=frozenset()):
        """All creatures chosen from the same snapshot, respecting indestructible."""
        effects=[]
        for oid in ids:
            if oid not in self.objects:continue
            moved=self.destroy(oid,commander_choice=oid in commander_ids)
            if moved:effects.append(moved)
        return effects

@dataclass
class WorldEntry:
    player:Any
    view:Any
    kind:str

class Battlefield:
    """Persistent game-object IDs are identical to exposed view IDs.

    Projections are changed only after a successful kernel operation. Dynamic
    card characteristics are declared; synthetic opponent bodies get generated
    definitions with typed characteristics rather than hidden card-name rules.
    """
    def __init__(self,table):
        self.table=table
        self.kernel=CentralKernel()
        self.views:dict[int,WorldEntry]={}
        self.transitions=0
        self.creatures_entered=0
        self.permanents_entered=0
        self.damage_batches=0
    def _definition(self,name,power,toughness,keywords,kind='creature',engine=False):
        if kind=='creature' and name in BY_NAME:
            d=BY_NAME[name]
            if d.base_power==power and d.base_toughness==toughness:
                return d if not set(keywords)-set(d.keywords) else replace(d,keywords=d.keywords|frozenset(keywords))
        types={'creature'} if kind=='creature' else {'artifact' if kind in {'ramp','combo_piece'} else 'enchantment'}
        return CardDefinition('synthetic:'+name+':'+str(power)+':'+str(toughness)+':'+','.join(sorted(keywords)),name,
                              frozenset(types),base_power=power,base_toughness=toughness,keywords=frozenset(keywords),coverage='approx')
    def create_treasure(self,p):
        from catalog import TREASURE
        from simulation import Permanent
        obj=self.kernel.add(TREASURE,p.seat,token=True)
        if hasattr(p,'treasures'):
            p.treasures+=1;p.ready_sources.append('Treasure');p.mana+=1
            self.views[obj.object_id]=WorldEntry(p,None,'resource')
        else:
            # Abstract seats use a persistent approximation of treasure mana.
            per=Permanent(obj.object_id,p.seat,'ramp',1,self.table.round_num,'Treasure')
            p.permanents.append(per)
            self.views[obj.object_id]=WorldEntry(p,per,'permanent')
        self.permanents_entered+=1
        return obj
    def consume_treasures(self,p,n):
        resources=[oid for oid,entry in self.views.items() if entry.player is p and entry.kind=='resource' and
                   oid in self.kernel.objects and self.kernel.get(oid).card.name=='Treasure']
        if len(resources)<n:raise AssertionError('Treasure accounting mismatch')
        for oid in resources[:n]:
            self.kernel.move(oid,'graveyard','sacrifice')
            self.views.pop(oid)
            self.transitions+=1
    def create_creature(self,p,power,toughness,name,token=False,engine=False,keywords=()):
        from simulation import Creature
        d=self._definition(name,max(0,power),max(1,toughness),keywords)
        obj=self.kernel.add(d,p.seat,token=token)
        c=Creature(obj.object_id,p.seat,max(0,power),max(1,toughness),self.table.round_num,name,False,token,engine,tuple(keywords))
        p.creatures.append(c)
        self.views[c.id]=WorldEntry(p,c,'creature')
        self.creatures_entered+=1
        self.table.emit('creature_entered',None,controller=p.seat,creature_id=c.id,source=name,token=token)
        return c
    def create_permanent(self,p,kind,value,name,is_creature=False):
        from simulation import Permanent
        d=self._definition(name,2,3,(),kind='creature' if is_creature else kind)
        obj=self.kernel.add(d,p.seat)
        per=Permanent(obj.object_id,p.seat,kind,value,self.table.round_num,name,is_creature)
        p.permanents.append(per);self.views[per.id]=WorldEntry(p,per,'permanent')
        self.permanents_entered+=1
        if is_creature:
            # A permanent that is also a creature has the SAME physical identity.
            from simulation import Creature
            c=Creature(obj.object_id,p.seat,2,3,self.table.round_num,name,False,False,kind=='engine',())
            p.creatures.append(c);per.linked_creature=c.id
            self.table.emit('creature_entered',None,controller=p.seat,creature_id=c.id,source=name,token=False)
        return per
    def id_for(self,seat,legacy_id):
        entry=self.views.get(legacy_id)
        if not entry or entry.player.seat!=seat:return None
        return legacy_id
    def _after_movement(self,ids,prior_names):
        # Reconcile from the authoritative live-ID set; no card-name destruction policy.
        removed=[]
        for oid in ids:
            if oid in self.kernel.objects:continue
            entry=self.views.pop(oid,None)
            if entry is None:continue
            p,v,kind=entry.player,entry.view,entry.kind
            c=next((x for x in p.creatures if x.id==oid),None)
            perm=next((x for x in p.permanents if x.id==oid),None)
            if c:
                p.creatures.remove(c)
                self.table.counts['creature_deaths']+=int(any(m.object_id==oid and m.new_zone=='graveyard' for m in self.kernel.moves))
                if any(m.object_id==oid and m.new_zone=='graveyard' for m in self.kernel.moves):
                    self.table.emit('creature_died',None,controller=p.seat,creature_id=oid,source=c.name)
            if perm:
                p.permanents.remove(perm)
                if not getattr(self.table,'source_backed_mana',False) and p is getattr(self.table,'details',None) and perm.name in p.rock_names:
                    p.rock_names.remove(perm.name)
                    if perm.name in p.ready_sources:p.ready_sources.remove(perm.name)
                    p.mana=min(p.mana,sum(max(map(sum,__import__('integrated').ColoredPayment.modes(n))) for n in p.ready_sources)+sum(p.floating))
            # A commander moved to command zone without losing its death trigger.
            removed.append((oid,p.seat,prior_names.get(oid)))
            self.transitions+=1
        return removed
    def destroy(self,oid):
        if oid not in self.kernel.objects:return False
        before={oid:self.kernel.get(oid).card.name}
        obj=self.kernel.get(oid)
        is_commander='commander' in obj.card.supertypes
        owner=self.views[oid].player if oid in self.views else None
        moved=self.kernel.destroy(oid,commander_choice=is_commander)
        if moved:
            self._after_movement([oid],before)
            if is_commander and owner is not None and hasattr(owner,'commander_in_zone'):
                owner.commander_in_zone=bool(moved.commander_replacement)
        return moved is not None
    def move(self,oid,zone,reason='exile'):
        if oid not in self.kernel.objects:return False
        prior={oid:self.kernel.get(oid).card.name}
        obj=self.kernel.get(oid)
        is_commander='commander' in obj.card.supertypes
        owner=self.views[oid].player if oid in self.views else None
        moved=self.kernel.move(oid,zone,reason,commander_choice=is_commander)
        if moved:
            self._after_movement([oid],prior)
            if is_commander and owner is not None and hasattr(owner,'commander_in_zone'):
                owner.commander_in_zone=bool(moved.commander_replacement or zone=='command')
        return bool(moved)
    def damage_pair(self,first,second):
        prior={oid:self.kernel.get(oid).card.name for oid in (first.id,second.id)}
        self.kernel.damage_creatures_together({first.id:second.power,second.id:first.power})
        self.damage_batches+=1
        return self._after_movement([first.id,second.id],prior)
    def modifier(self,creature,power=0,toughness=0,keywords=(),duration='never'):
        self.kernel.add_modifier(creature.id,Modifier(power,toughness,frozenset(keywords),duration))
        self.refresh(creature.id)
    def refresh(self,oid):
        if oid not in self.kernel.objects or oid not in self.views:return
        o=self.kernel.get(oid);view=self.views[oid].view
        if hasattr(view,'power'):
            view.power=o.power;view.toughness=o.toughness;view.keywords=tuple(o.keywords)
            view.tapped=o.tapped
    def tap(self,c,yes=True):
        if c.id in self.kernel.objects:
            self.kernel.get(c.id).tapped=yes;self.kernel._dirty()
        c.tapped=yes
    def cleanup(self):
        self.kernel.cleanup()
        for oid in list(self.views):self.refresh(oid)
    def leave_game(self,seat):
        """Objects owned by a leaving player cease to exist in this game.

        This is not destruction or exile, and must not fire dies triggers.
        The legacy player may clear its read-side lists after this call.
        """
        for oid,obj in list(self.kernel.objects.items()):
            if obj.controller==seat or obj.owner==seat:
                del self.kernel.objects[oid]
                self.views.pop(oid,None)
                self.transitions+=1
        self.kernel._dirty()

    def consistent(self):
        views=set(self.views)
        for entry in self.views.values():
            if entry.kind=='resource':
                if entry.view is not None:return False
                continue
            if not any(x.id in views and x is entry.view for x in entry.player.creatures+entry.player.permanents):return False
        return views=={o.object_id for o in self.kernel.on_battlefield()}

