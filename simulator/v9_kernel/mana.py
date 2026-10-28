"""Reusable source-specific U/R/generic payment planner for the shared rules kernel.

Production integration into legacy upkeep/payment is deferred: v8 still has
v6's ColoredPayment and synthetic fungible mana adapters. This module is an
independent, fail-closed resource service ready to replace those adapters.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v8_central'))
from rules import CardDefinition,Cost,SafetyStop
from kernel import CentralKernel

@dataclass(frozen=True)
class ManaMode:
    colorless:int=0
    blue:int=0
    red:int=0
    def __post_init__(self):
        if min(self.colorless,self.blue,self.red)<0:
            raise ValueError('Invalid mana output')

@dataclass(frozen=True)
class PaymentPlan:
    activations:tuple[tuple[int,ManaMode],...]
    cost:Cost
    unused:ManaMode

class TypedMana:
    """Store physical source identity/tap flags on one GameKernel, not a mana counter.

    Source modes are explicit data; only fixed mana outputs are represented.
    No costs to activate, floating mana, treasure sacrifice, or hybrid/phyrexian
    symbols are claimed in this milestone.
    """
    def __init__(self,kernel:CentralKernel|None=None,max_states=10000):
        self.kernel=kernel or CentralKernel()
        self.modes={}
        self.max_states=max_states
    def add_source(self,seat,name,modes,kind='land'):
        modes=tuple(modes)
        if not modes or not all(isinstance(m,ManaMode) and sum((m.colorless,m.blue,m.red))>0 for m in modes):raise ValueError('Missing mana modes')
        if kind not in ('land','artifact'):raise ValueError('Unsupported source type')
        d=CardDefinition('resource:'+name,name,frozenset({kind}),coverage='verified_subset')
        o=self.kernel.add(d,seat)
        self.modes[o.object_id]=modes
        return o.object_id
    def plan(self,seat,cost:Cost):
        if not isinstance(cost,Cost):raise TypeError('Only U/R/generic costs supported')
        eligible=sorted((oid,modes) for oid,modes in self.modes.items() if oid in self.kernel.objects and
                        self.kernel.get(oid).zone=='battlefield' and self.kernel.get(oid).controller==seat and
                        not self.kernel.get(oid).tapped)
        if cost.total==0:return PaymentPlan((),cost,ManaMode(0,0,0))
        best=None;visited=0
        # Branch and bound on source count, then lexicographic source ID; never
        # spend a colored mode needlessly if a cheaper source count suffices.
        def search(i,selected,c,u,r):
            nonlocal best,visited
            visited+=1
            if visited>self.max_states:raise SafetyStop('mana_search_budget')
            if best is not None and len(selected)>len(best[0]):return
            if u>=cost.blue and r>=cost.red and c+u+r>=cost.total:
                excess=(c,u-cost.blue,r-cost.red)
                candidate=(tuple(selected),excess)
                if best is None or (len(candidate[0]),tuple(x[0] for x in candidate[0]),sum(excess))< \
                        (len(best[0]),tuple(x[0] for x in best[0]),sum(best[1])):
                    best=candidate
                return
            if i==len(eligible):return
            oid,modes=eligible[i]
            search(i+1,selected,c,u,r)
            for m in modes:search(i+1,selected+[(oid,m)],c+m.colorless,u+m.blue,r+m.red)
        search(0,[],0,0,0)
        if best is None:return None
        selected,(c,u,r)=best
        # Generic cost may consume any surplus colored production. Express the
        # exact unspent pool deterministically with generic paid from colorless first.
        generic_remaining=cost.generic
        used_c=min(c,generic_remaining);generic_remaining-=used_c
        used_u=min(u,generic_remaining);generic_remaining-=used_u
        used_r=min(r,generic_remaining);generic_remaining-=used_r
        if generic_remaining:raise AssertionError('Payment planner violated requirement')
        return PaymentPlan(tuple(selected),cost,ManaMode(c-used_c,u-used_u,r-used_r) if c-used_c+u-used_u+r-used_r>0 else ManaMode(0,0,0))
    def pay(self,seat,cost:Cost):
        plan=self.plan(seat,cost)
        if plan is None:raise ValueError('Cannot pay mana cost')
        for oid,_ in plan.activations:
            obj=self.kernel.get(oid)
            if obj.controller!=seat or obj.tapped:raise AssertionError('Illegal activation')
            obj.tapped=True
        self.kernel._dirty()
        return plan
    def untap(self,seat):
        for oid in list(self.modes):
            if oid in self.kernel.objects and self.kernel.get(oid).controller==seat:
                self.kernel.get(oid).tapped=False
        self.kernel._dirty()
