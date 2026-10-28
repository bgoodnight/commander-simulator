"""One bounded spell/counter resolver used by every seat, not deck-specific windows.

Deliberate limited-scope priority: only counterspell reactions, with nested
counterspells supported. Cast triggers are emitted on casting even if countered.
Triggered abilities currently settle before response windows; full priority to
respond to triggers is a future milestone, explicitly not claimed here.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v5_four_player'))
import simulation as base

@dataclass
class SpellFrame:
    action:base.Action
    counter_target:int|None=None
    countered:bool=False

class SharedStack:
    def __init__(self,table):
        self.table=table
        self.frames:list[SpellFrame]=[]
        self.max_depth_seen=0
        self.counters_resolved=0
        self.responses_attempted=0
        self.spells_resolved=0
        self.spells_countered=0
        self.passes=0

    @staticmethod
    def allowed(counter,spell):
        from responses import descriptor
        allowed=descriptor(counter).legal_spell_types
        return spell.card_type in allowed or ('noncreature' in allowed and spell.card_type!='creature')

    def _candidates(self,top):
        t=self.table
        result=[]
        for p in t.alive():
            if p.seat==top.action.actor:continue
            for card in p.hand:
                if card.effect!='counter' or not self.allowed(card,top.action):continue
                a=t.action_for_card(p,card)
                if not t.can_pay(p,a):continue
                direct=top.action.target==p.seat or top.action.effect in ('wipe','finisher')
                importance=top.action.effect in ('wipe','finisher','counter')
                chance=(.44 if direct else .13)+(.34 if importance else 0)+(.17 if top.action.effect=='remove' and direct else 0)
                chance+=base.CONF['counter_response_bonus'].get(p.archetype,0)
                if top.action.effect=='counter':chance+=0.21 if p.seat==self.frames[0].action.actor else 0
                result.append((min(.98,chance),p,card,a))
        return result

    def resolve(self,action):
        t=self.table
        self.frames=[SpellFrame(action)]
        self.max_depth_seen=max(self.max_depth_seen,1)
        # Try one counter per new stack top; the counter can itself be countered.
        while t.interactive:
            t.safe_runner.check(stack_depth=len(self.frames))
            opts=self._candidates(self.frames[-1])
            if not opts:break
            policy=getattr(t,'response_policy',None)
            if policy is not None:
                selected=policy(self.frames[-1],tuple(opts))
                if selected is None:
                    self.passes+=1;break
                if selected not in opts:raise ValueError('Response policy chose an illegal option')
                probability,p,card,a=selected
            else:
                selected=max(opts,key=lambda z:z[0]+t.rng.random()*.12)
                probability,p,card,a=selected
                if t.rng.random()>probability:
                    self.passes+=1;break
            self.responses_attempted+=1
            t.pay_spell(p,card,a,response=True)
            self.frames.append(SpellFrame(a,len(self.frames)-1))
            self.max_depth_seen=max(self.max_depth_seen,len(self.frames))
            t.note(f'    STACK: P{p.seat} casts {card.name} targeting {self.frames[-2].action.source}.')
            t.emit('spell_cast',a)
            t.safe_runner.check(stack_depth=len(self.frames))
        # Resolve LIFO. Each uncountered counterspell counters its immediate target.
        for i in range(len(self.frames)-1,-1,-1):
            f=self.frames[i]
            if f.countered:
                self.spells_countered+=1
                if f.action.effect!='counter':t.counts['spells_countered']+=1
                t.emit('spell_countered',f.action)
                t.note(f'    STACK: {f.action.source} is countered.')
                continue
            if f.counter_target is not None:
                self.frames[f.counter_target].countered=True
                self.counters_resolved+=1;t.counts['counters_cast']+=1
                t.players[f.action.actor].counters_used+=1
                if self.frames[f.counter_target].action.effect=='counter':t.counts['counter_counters']+=1
                t.note(f'    STACK: {f.action.source} counters {self.frames[f.counter_target].action.source}.')
                # Card-specific response riders live in declarative adapter metadata.
                t.resolve_counter_rider(f.action,self.frames[f.counter_target].action)
                self.spells_resolved+=1;t.emit('spell_resolved',f.action)
            else:
                t.apply(f.action)
                self.spells_resolved+=1;t.emit('spell_resolved',f.action)
        result=not self.frames[0].countered
        self.frames=[]
        return result
