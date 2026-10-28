"""Incremental bridge: v7 shared trait/trigger/cost services under the v6 pilot.

V5's abstract player engine and v6's existing player/stack approximations remain.
This is evidence for migration, not a claim that all table rules are centralized.
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import replace
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'v6_real_deck'))
sys.path.insert(0,str(ROOT.parent/'v5_four_player'))
import integrated as v6
import simulation as v5
from rules import GameKernel,Event,Cost,ExecutionGuard,SafetyStop
from loops import LoopResolver
from catalog import BY_NAME,DEFINITIONS,MAGNUS,SPAWN,ELEMENTAL,SOLDIER,TREASURE

class ModularTable(v6.MixedTable):
    """Works with the existing real Magnus deck and three synthetic players.

    No duplicates of named Pyromancer/Magnus/discount trigger rules: all those
    resolve via indexed definition-driven reusable abilities in the v7 kernel.
    Other preexisting v6 behavior remains explicitly a known approximation.
    """
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.rules=GameKernel();self.safe_runner=self.rules.guard
        self.combo_planner=LoopResolver(self.safe_runner)
        self.safety_stop=None
        self.shared_triggers=0
        self.shared_cost_queries=0
    def _view(self):
        # Cached per observable board revision; no repeated object creation
        # when the pilot asks about the same unchanged position.
        signature=(tuple((p.seat,tuple((c.id,c.name,c.power,c.toughness,c.token,c.tapped,c.keywords)
                                  for c in p.creatures)) for p in self.players),self.details.treasures)
        if getattr(self,'_view_cache_key',None)==signature:return self._view_cache_value
        k=GameKernel(self.safe_runner);to_external={};to_internal={}
        for p in self.players:
            for c in p.creatures:
                defn=BY_NAME.get(c.name)
                if defn is None:
                    from rules import CardDefinition
                    defn=CardDefinition('synthetic_'+str(c.id),c.name,frozenset({'creature'}),
                                         base_power=c.power,base_toughness=c.toughness,
                                         keywords=frozenset(x for x in c.keywords if x!='expires'))
                o=k.add(defn,p.seat,token=c.token)
                # Dynamic modifiers granted by other effects can be expressed on
                # the original object with `keywords` even if base card doesn't have it.
                if c.keywords:
                    from rules import Modifier
                    added=frozenset(c.keywords)-defn.keywords-{'expires'}
                    if added:k.add_modifier(o.object_id,Modifier(keywords=added))
                to_external[o.object_id]=(p,c)
                to_internal[(p.seat,c.id)]=o.object_id
        for _ in range(self.details.treasures):k.add(TREASURE,0,token=True)
        self._view_cache_key=signature
        self._view_cache_value=(k,to_external,to_internal)
        return self._view_cache_value
    def action_for(self,p,c):
        if p is not self.details:return super().action_for(p,c)
        action=super().action_for(p,c)
        if c.card_type in ('instant','sorcery'):
            k,_,_=self._view()
            base_cost=v6.CAT[c.name].get('cost')
            if base_cost:
                generic,blue,red=base_cost
                total=k.modified_cost(p.seat,frozenset({c.card_type}),Cost(generic,blue,red))
                action.cost=total.total
                action.parameters.update(U=blue,R=red)
                self.shared_cost_queries+=1
        return action
    def named_triggers(self,table,event,action,payload):
        if event!='spell_cast' or action is None:return
        k,_,_=self._view()
        pending=k.triggers(Event(event,controller=action.actor,spell_types=frozenset({action.card_type})))
        self._apply_pending(pending)
    def _apply_pending(self,pending):
        for triggered in pending:
            controller=self.players[triggered.controller]
            args=dict(triggered.args)
            self.shared_triggers+=triggered.quantity
            if triggered.op=='create_token':
                definition=DEFINITIONS[args['token_id']]
                for _ in range(triggered.quantity):
                    if definition is TREASURE and controller is self.details:
                        controller.treasures+=1;controller.ready_sources.append('Treasure');controller.mana+=1
                    elif definition is TREASURE:
                        self.add_permanent(controller,'ramp',1,'Treasure')
                    else:
                        kw=tuple(definition.keywords)
                        if definition.card_id=='stormsplitter':kw+=('expires',)
                        self.add_creature(controller,definition.base_power,definition.base_toughness,definition.name,token=True,keywords=kw)
            elif triggered.op=='draw':
                controller.draw(triggered.quantity)
                if not controller.alive:self.eliminate(controller,'empty_library')
            else:raise ValueError('No adapter for '+triggered.op)
    def damage(self,p,n,source=None,cause='damage'):
        # Shared damage-to-player implementation is still the v5 table; v7's
        # indexed trigger evaluator replaces the name-dependent Magnus trigger.
        v5.Table.damage(self,p,n,source,cause)
        if cause=='combat' and source is not None and n>0:
            attacker=getattr(self,'current_attacker',None)
            if attacker:
                k,_,to_internal=self._view()
                c=next((c for c in source.creatures if c.name==attacker),None)
                if c:
                    key=(source.seat,c.id)
                    pending=k.triggers(Event('combat_damage_player',source.seat,to_internal[key],amount=n))
                    self._apply_pending(pending)
    def block(self,defender,attacker_creature,used):
        if defender.block_policy=='never':return None
        k,external,internal=self._view()
        attacker_seat=attacker_creature.controller
        aid=internal[(attacker_seat,attacker_creature.id)]
        legal=k.legal_blockers(aid,defender.seat,used=frozenset(internal[(defender.seat,x)] for x in used if (defender.seat,x) in internal))
        candidates=[external[o.object_id][1] for o in legal]
        choices=[]
        for c in candidates:
            kill=c.power>=attacker_creature.toughness
            survive=c.toughness>attacker_creature.power
            urgency=defender.life<=attacker_creature.power+5
            if kill and (survive or urgency or c.power<=attacker_creature.power+1):choices.append((4*survive+2*kill-.1*c.power,c))
            elif urgency and c.toughness>attacker_creature.power:choices.append((1.4-.1*c.power,c))
        return max(choices,key=lambda x:x[0])[1] if choices else None
    def kill_creature(self,p,c):
        # Engine-wide destroy calls will be moved to zone API in later milestone.
        if 'indestructible' in c.keywords:return
        super().kill_creature(p,c)
    def _cleanup_expiring(self):
        # End-step exile of temporary copies, not 'dies' / destruction.
        for p in self.alive():
            for c in list(p.creatures):
                if c.token and 'expires' in c.keywords:
                    p.creatures.remove(c)
                    self.note(f'    {c.name} temporary copy exiled at end step.')
                    self.counts['token_exiled']+=1
    def upkeep(self,p,t):
        self.safe_runner.new_turn(t*4+p.seat)
        return super().upkeep(p,t)
    def cast(self,action):
        actor=self.players[action.actor]
        private=(tuple(x.name for x in actor.hand),tuple(x.name for x in actor.library[-6:]),
                 actor.life,actor.mana,tuple((c.id,c.power,c.toughness) for c in actor.creatures),
                 tuple(sorted((q.seat,q.life,len(q.creatures)) for q in self.players)),action.source)
        self.safe_runner.check(private)
        return super().cast(action)
    def run(self,max_rounds=8):
        try:return super().run(max_rounds)
        except SafetyStop as exc:
            self.safety_stop=exc.reason
            self.win_reason='unresolved_safety_guard';self.winner=None;self.end_round=None
            self.note('  SAFETY HALT, unresolved: '+exc.reason)
            return self
    def diagnostics(self):
        d=super().diagnostics()
        d['v7']={'shared_trigger_instances':self.shared_triggers,
                 'shared_cost_queries':self.shared_cost_queries,
                 'safety_stop':self.safety_stop,
                 'modular_scope':'typed costs/triggers/block legality; full stack and zones pending'}
        return d
