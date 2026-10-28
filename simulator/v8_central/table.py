"""V8 shared multiplayer transition table.

Mixed and fully abstract tables use the same authoritative battlefield kernel,
combat/damage transition operations, cast/payment pipeline and bounded stack.
Existing pilots are adapters; unsupported named cards remain inert.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'v5_four_player'))
sys.path.insert(0,str(ROOT.parent/'v6_real_deck'))
sys.path.insert(0,str(ROOT.parent/'v7_rules'))
import simulation as base
import integrated as v6
import bridge as v7
from rules import Event,Modifier,Cost,SafetyStop
from kernel import Battlefield
from stack import SharedStack
from responses import descriptor
from turns import TurnDriver

class CentralTable(v7.ModularTable):
    def __init__(self,opponents=('aggro','control','combo'),seed=1,trace=True,opening=None):
        super().__init__(opponents,seed,trace=trace,opening=opening)
        self.world=Battlefield(self)
        self.rules=self.world.kernel
        self.safe_runner=self.rules.guard
        self.spell_stack=SharedStack(self)
        self._world_actions=0
        self.safety_stop=None
        self.pending_triggers=[]
    def _view(self):
        # Persistent references, never reconstruct the entire battlefield for a cost query.
        ex={};internal={}
        for p in self.players:
            for c in p.creatures:
                if c.id in self.rules.objects:
                    ex[c.id]=(p,c);internal[(p.seat,c.id)]=c.id
        return self.rules,ex,internal
    def add_creature(self,p,power,toughness,name,token=False,engine=False,keywords=()):
        # Same synthetic keyword assignment as v6, but it is encoded as data.
        if p is not self.details and not keywords and not token:
            if p.rng.random()<(0.17 if power>=4 else 0.06 if power>=2 else 0.0):keywords=('flying',)
        return self.world.create_creature(p,power,toughness,name,token,engine,keywords)
    def add_permanent(self,p,kind,value,name,is_creature=False):
        return self.world.create_permanent(p,kind,value,name,is_creature)
    def kill_creature(self,p,c):
        if c.id not in self.rules.objects:return False
        return self.world.destroy(c.id)
    def remove_permanent(self,p,perm):
        if perm.id not in self.rules.objects:return False
        return self.world.destroy(perm.id)
    def block(self,defender,attacker,used):
        if defender.block_policy=='never':return None
        k,ex,_=self._view()
        if attacker.id not in k.objects:return None
        candidates=[ex[o.object_id][1] for o in k.legal_blockers(attacker.id,defender.seat,frozenset(used)) if o.object_id in ex]
        options=[]
        for c in candidates:
            kill=c.power>=attacker.toughness;survive=c.toughness>attacker.power
            urgency=defender.life<=attacker.power+5
            if kill and (survive or urgency or c.power<=attacker.power+1):options.append((4*survive+2*kill-0.1*c.power,c))
            elif urgency and survive:options.append((1.4-0.1*c.power,c))
        return max(options,key=lambda x:x[0])[1] if options else None
    def damage(self,p,n,source=None,cause='damage'):
        if not p.alive:return
        amount=max(0,n)
        before={q.seat:q.life for q in self.players}
        self.rules.damage_players(before,{p.seat:amount},source.seat if source else None)
        p.life=before[p.seat];p.damage_taken+=amount
        if source:source.damage_dealt+=amount
        self.emit('damage',None,source=(source.seat if source else None),target=p.seat,amount=amount,cause=cause)
        if p.life<=0:self.eliminate(p,cause)
        if cause=='combat' and source is not None and amount:
            attacker=getattr(self,'current_attacker_id',None)
            if attacker in self.rules.objects:
                self._apply_pending(self.rules.triggers(Event('combat_damage_player',source.seat,attacker,amount=amount)))
    def damage_many(self,damage:dict[int,int],source=None,cause='damage'):
        lives={q.seat:q.life for q in self.players}
        result=self.rules.damage_players(lives,damage,source.seat if source else None)
        for seat,amount in damage.items():
            p=self.players[seat]
            if p.life<=0:continue
            p.life=lives[seat];p.damage_taken+=amount
            if source:source.damage_dealt+=amount
            self.emit('damage',None,source=source.seat if source else None,target=seat,amount=amount,cause=cause)
        for seat in result.eliminated:self.eliminate(self.players[seat],cause)
        if len(result.eliminated)>1:self.counts['multi_elimination_events']+=1
    def eliminate(self,p,cause):
        if p.eliminated_round is not None:return
        self.world.leave_game(p.seat)
        return base.Table.eliminate(self,p,cause)
    def remove_players_together(self,targets,cause,actor=None):
        # Non-damage loss (e.g. abstract combo winner) must remain non-damage.
        for q in targets:
            if q.alive:q.life=0
        for q in targets:
            if q.eliminated_round is None:self.eliminate(q,cause)
        if len(targets)>1:self.counts['multi_elimination_events']+=1
    def _cleanup_expiring(self):
        for p in self.alive():
            for c in list(p.creatures):
                if c.token and 'expires' in c.keywords:
                    if self.world.move(c.id,'exile','token_cease'):
                        self.counts['token_exiled']+=1
                        self.note('    Expires: '+c.name+' copy ceases to exist.')
        self.world.cleanup()
    def named_triggers(self,table,event,action,payload):
        # This listener is registered by the v6 constructor, but now all *named*
        # triggers are evaluated from the persistent shared object registry.
        if event!='spell_cast' or action is None:return
        pending=self.rules.triggers(Event(event,controller=action.actor,spell_types=frozenset({action.card_type})))
        self._apply_pending(pending)
    def _apply_pending(self,pending):
        # Every trigger's operation and object creation pass through one dispatcher.
        from catalog import DEFINITIONS
        for item in pending:
            p=self.players[item.controller]
            self.shared_triggers+=item.quantity
            if item.op=='draw':
                p.draw(item.quantity)
                if not p.alive:self.eliminate(p,'empty_library')
            elif item.op=='create_token':
                definition=DEFINITIONS[dict(item.args)['token_id']]
                for _ in range(item.quantity):
                    if definition.card_id=='treasure':self.world.create_treasure(p)
                    else:
                        tags=tuple(definition.keywords)
                        if definition.card_id=='stormsplitter':tags+=('expires',)
                        self.add_creature(p,definition.base_power,definition.base_toughness,definition.name,token=True,keywords=tags)
            else:raise NotImplementedError('Unimplemented trigger operation '+item.op)
    def action_for_card(self,p,card):
        return self.action_for(p,card) if getattr(p,'payment_policy',None) else self.build_action(p,card)
    def can_pay(self,p,action):
        policy=getattr(p,'payment_policy',None)
        return policy.can_pay(p,action) if policy else p.mana>=action.cost
    def resolve_counter_rider(self,response,original):
        rider=descriptor(v6.named_spec(response.source) if response.source in v6.COUNTERS else
                         base.CardSpec(response.source,'counter',response.cost,'instant','counter')).after_resolution
        beneficiary=self.players[original.actor]
        if rider=='none':return
        if rider=='bird_token':
            self.add_creature(beneficiary,2,2,'Bird (Swan Song)',token=True,keywords=('flying',))
        elif rider=='two_treasures':
            for _ in range(2):self.world.create_treasure(beneficiary)
        else:raise NotImplementedError('Unregistered response rider '+rider)
    def pay_spell(self,p,card,action,response=False):
        if not self.can_pay(p,action):raise ValueError('Illegal mana payment')
        if card not in p.hand:raise ValueError('Spell not available')
        p.hand.remove(card)
        policy=getattr(p,'payment_policy',None)
        if policy:
            old_treasure=getattr(p,'treasures',0)
            policy.pay(p,action)
            consumed=old_treasure-getattr(p,'treasures',0)
            if consumed:self.world.consume_treasures(p,consumed)
        else:p.mana-=action.cost
        p.cards_cast+=1;p.mana_spent+=action.cost;self.counts['casts']+=1
        if p is self.details:
            p.coverage['approx' if card.name in v6.APPROX else 'supported']+=1
            if card.name!='Magnus the Red' and card.card_type in ('instant','sorcery'):p.graveyard.append(card.name)
        self.note(f'  P{p.seat} ({p.archetype}) casts {card.name} [{action.card_type}] for {action.cost}; mana={p.mana}.')
        return True
    def cast(self,action):
        p=self.players[action.actor]
        if not p.alive:return False
        if action.effect=='unsupported':raise ValueError('Unsupported effect cannot resolve')
        zone_cast=p is self.details and action.source=='Magnus the Red' and p.commander_in_zone
        card=v6.named_spec('Magnus the Red') if zone_cast else next((c for c in p.hand if c.name==action.source),None)
        if card is None:return False
        if not self.can_pay(p,action):return False
        self.safe_runner.check((p.seat,action.source,p.mana,tuple((c.name for c in p.hand)),len(p.creatures)),stack_depth=1)
        if zone_cast:p.hand.append(card)
        self.pay_spell(p,card,action)
        if zone_cast:
            p.commander_casts+=1
            p.commander_in_zone=False
        self.emit('spell_cast',action)
        success=self.spell_stack.resolve(action)
        if zone_cast:
            p.commander_in_zone=not any(c.name=='Magnus the Red' for c in p.creatures)
            if not success:self.note('    Countered commander returns to command zone.')
        if not p.alive:self.eliminate(p,'empty_library')
        self._world_actions+=1
        return True
    def respond(self,action):
        raise RuntimeError('All spell responses use the shared stack; separate respond() disabled')
    def apply(self,action):
        if action.effect in ('remove','named_pongify'):
            # Target legality is shared by synthetic removal and printed-card
            # implementations; hexproof/shroud stop target-based destruction.
            oid=action.target_object
            if oid is None or oid not in self.rules.objects or not self.rules.legal_target(action.actor,oid,{'creature','artifact','enchantment','planeswalker'}):
                self.counts['illegal_target_on_resolution']+=1
                self.note('    Spell has no legal target on resolution.')
                return
        if action.effect=='buff':
            self.counts['resolved_buff']+=1
            for c in list(self.players[action.actor].creatures):
                self.world.modifier(c,power=action.parameters.get('power_boost',1))
            return
        return base.Table.apply(self,action)
    def finish(self,p,a,action):
        mode=a.get('mode','damage')
        if mode=='spell_burst':
            p.finisher_attempts+=1;self.counts['finishers_resolved']+=1
            n=a.get('damage',8)+min(14,3*p.engines()+p.combo()*2)
            self.damage_many({q.seat:n for q in self.rivals(p)},p,'spell_burst')
            self.counts['spell_bursts']+=1
            return
        if mode=='overrun':
            p.finisher_attempts+=1;self.counts['finishers_resolved']+=1
            bonus=2+min(3,p.engines())
            for c in list(p.creatures):self.world.modifier(c,power=bonus)
            return
        return base.Table.finish(self,p,a,action)
    def combat(self,p):
        # Shared combat rules for all seats, including flying and simultaneous damage.
        if not self.interactive:return
        candidates=list(p.creatures);used={q.seat:set() for q in self.alive()}
        for c in candidates:
            if c not in p.creatures or not p.alive or len(self.alive())<=1:continue
            if c.entered_round>=self.round_num and 'haste' not in c.keywords:continue
            if c.tapped:continue
            rate=base.CONF['attack_rate'].get(p.archetype,.65)
            if p is self.details and c.name=='Magnus the Red':rate=.78
            if p is self.details and c.name in v6.ENGINE_BODIES:continue
            if p.rng.random()>=rate:continue
            target=self.choose_target(p,'attack')
            if target is None:continue
            if p is self.details and c.power<=3:
                predicted=self.block(target,c,set())
                if predicted is not None and predicted.power>=c.toughness and predicted.toughness>c.power:continue
            self.emit('combat_attack',None,attacker=p.seat,defender=target.seat,creature_id=c.id)
            self.world.tap(c)
            blocker=self.block(target,c,used[target.seat])
            if blocker:
                used[target.seat].add(blocker.id)
                self.note(f'    COMBAT P{p.seat} {c.name} {c.power}/{c.toughness} into P{target.seat} {blocker.name} {blocker.power}/{blocker.toughness}.')
                self.world.damage_pair(c,blocker)
                self.counts['blocks']+=1
            else:
                self.note(f'    COMBAT P{p.seat} {c.name} hits P{target.seat} for {c.power}.')
                self.current_attacker_id=c.id
                self.damage(target,c.power,p,'combat')
                self.current_attacker_id=None
            self.counts['attackers']+=1
    def upkeep(self,p,t):
        # Retain specialized mana/land sequencing; the shared table handles
        # battlefield creation and combat, and kernel object tapping is synchronized.
        v7.ModularTable.upkeep(self,p,t)
        for c in p.creatures:self.world.tap(c,False)
    def run(self,max_rounds=8):
        result=TurnDriver(self).run(max_rounds)
        if not self.world.consistent():raise AssertionError('Kernel and pilot battlefield views diverged')
        return result
    def diagnostics(self):
        d=super().diagnostics()
        d['v8']={
            'kernel_permanent_creatures':len(list(self.rules.on_battlefield())),
            'kernel_view_consistent':self.world.consistent(),
            'creatures_entered':self.world.creatures_entered,
            'permanents_entered':self.world.permanents_entered,
            'zone_transitions':self.world.transitions,
            'combat_damage_batches':self.world.damage_batches,
            'shared_stack_max_depth':self.spell_stack.max_depth_seen,
            'shared_stack_resolved':self.spell_stack.spells_resolved,
            'shared_stack_countered':self.spell_stack.spells_countered,
            'guard_stop':self.safety_stop,
            'limits':['shared battlefield/keyword/combat/damage/spell stack','some land/mana, hand/library, and legacy synthetic finishers remain adapters',
                     'counter-only response priority; triggered abilities resolve before responses']}
        return d
