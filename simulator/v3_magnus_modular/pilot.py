"""Priority-based pilot. Card-specific priority is metadata-driven; combos have their own priority.

The pilot does NOT search the entire game tree. It tries affordable plays,
and records abilities it cannot responsibly model.
"""
from engine import Game,Catalog
from combos import Combos

class Pilot:
    def __init__(self,catalog=None,combos=None,simulate_combos=False):
        self.cat=catalog or Catalog();self.combos=combos or Combos();self.simulate_combos=simulate_combos
    def score(self,g,c):
        tags=self.cat.tags(c);typ=self.cat.type(c);cost=self.cat.cost(c)
        if cost is None:return -999
        if 'ramp' in tags:return 102 if g.turn<=3 else 75 if g.turn<=5 else 22
        if 'selection' in tags:
            return (103 if g.turn==1 and cost[0]+cost[1]+cost[2]<=1 else
                    95 if len(g.lands)<min(g.turn,5) else
                    78 if g.turn<=4 else 46)
        if 'early_engine' in tags:return 88 if g.turn<=4 else 57
        if 'token_engine' in tags:return 68 if g.turn>=3 else 54
        if 'discount_engine' in tags:return 79
        if 'mana_engine' in tags:return 62 if g.turn>=3 else 53
        if 'control_engine' in tags:return 63 if g.turn>=3 else 50
        if 'copy_engine' in tags:return 58
        if 'draw_engine' in tags:return 60
        if 'tutor_engine' in tags:return 53
        if 'type_engine' in tags:return 35
        if 'grave_engine' in tags:return 38 if len(g.grave)>=5 and g.turn>=5 else -20
        if 'buyback_engine' in tags:
            if c=='Mystic Speculation':return 32 if g.turn>=4 else 20
            if c=='Searing Touch':return 29 if g.engine_count()>0 and g.turn>=4 else -40
            return -40 # Capsize needs a meaningful permanent target; not represented in goldfish
        if typ=='creature':return 18 if g.turn>=5 else -15
        return -50
    def activate_looter(self,g):
        for c in g.board:
            if 'looter' in self.cat.tags(c) and g.board[c]<g.turn and 'C:'+c not in g.tapped:
                g.activate(c,'loot')
    def check_combos(self,g):
        available=self.combos.evaluate(g)
        for combo in available:
            if not any(x['id']==combo['id'] for x in g.combo_events):
                g.combo_events.append({'turn':g.turn,**combo})
                if g.first_combo is None:g.first_combo=g.turn
                g.note('  COMBO READY: '+combo['name']+' — '+combo['reason'])
                if self.simulate_combos:
                    proof=self.combos.execute_bounded(g,combo['id'],cycles=3)
                    g.note('  COMBO BOUNDED TEST: '+str(proof))
                    g.combo_events[-1]['bounded_test']=proof
        return available
    def run(self,seed=20261028,policy='delay_one',scenario='none',turns=8,trace=False):
        g=Game(self.cat,seed,policy,scenario,trace)
        for turn in range(1,turns+1):
            g.new_turn(turn)
            self.activate_looter(g)
            can_magnus_now=g.can_pay('Magnus the Red') and not g.has_magnus()
            if can_magnus_now and g.magnus_deferred_turn is None and policy=='delay_one':
                g.magnus_deferred_turn=turn
                g.note('  POLICY: could cast Magnus, deliberately develop cabal this turn instead.')
            # Each player has same per-turn action selection. Only commander availability differs.
            for action_index in range(12):
                actions=[]
                for c in dict.fromkeys(g.hand):
                    if self.cat.type(c) in ('land','commander') or self.cat.cost(c) is None:continue
                    if 'counter' in self.cat.tags(c):continue # opponent turn only
                    if self.cat.type(c)=='spell' and not ('selection' in self.cat.tags(c) or 'buyback_engine' in self.cat.tags(c)):continue
                    if self.cat.type(c)=='spell' and c=='Mystic Speculation' and g.turn<4:continue
                    if not g.can_pay(c):continue
                    val=self.score(g,c)
                    if val>0:actions.append((val,c))
                # Commander can be cast immediately or only after the skipped turn.
                commander_allowed=(policy=='rush' or (policy=='delay_one' and g.magnus_deferred_turn is not None and g.turn>g.magnus_deferred_turn) or (policy=='conditional' and (g.engine_count()>=1 or g.turn>=7)))
                if not g.has_magnus() and g.can_pay('Magnus the Red') and commander_allowed:
                    actions.append((99 if g.turn<=5 else 85,'Magnus the Red'))
                if not actions:break
                # No same-card buyback spam in basic priority pilot; combo handled separately.
                actions.sort(key=lambda x:(x[0],-sum(self.cat.cost(x[1])) if self.cat.cost(x[1]) else 0,x[1]),reverse=True)
                score,chosen=actions[0]
                if chosen=='Magnus the Red':success=g.cast_commander()
                else:success=g.cast(chosen)
                if not success:break
                # Keep combo detection separate from priority play actions.
                self.check_combos(g)
                # Avoid spending a held counter as a proactive spell; unspent mana is intentional.
            if g.has('Sorcerer Class') and g.level('Sorcerer Class')==1 and g.turn>=5 and g.token_count()>=2 and g.can_pay_activated([3,1,0]):
                g.activate('Sorcerer Class','level_2')
            # End-of-turn combat: in goldfish, Magnus connects after untap (not guaranteed vs opponents).
            if g.has_magnus() and g.board['Magnus the Red']<turn:
                g.note('  COMBAT assumption: Magnus connects unblocked, creates Spawn.')
                g.event('combat_damage','Magnus the Red')
            if scenario=='one_removal_t5' and turn==5:g.opponent_removal()
            g.end_turn()
        return g
