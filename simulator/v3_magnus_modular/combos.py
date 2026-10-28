"""Independent combo recipes, with explicit evaluators; never auto-claim wins."""
import json
from pathlib import Path
ROOT=Path(__file__).parent

class Combos:
    def __init__(self,path=ROOT/'combos.json'):
        data=json.loads(Path(path).read_text());self.recipes=sorted(data['combos'],key=lambda x:-x['priority'])
        self.evaluators={'searing_treasure':self.searing,'speculation_altar':self.speculation_altar,'speculation_class':self.speculation_class}
        assert all(x['evaluator'] in self.evaluators for x in self.recipes)
    def evaluate(self,g):
        matches=[]
        for c in self.recipes:
            if not all(g.has(n) for n in c['requires_battlefield']):continue
            if not all(n in g.hand for n in c['requires_hand']):continue
            if any(g.level(n)<l for n,l in c.get('requires_level',{}).items()):continue
            ok,reason=self.evaluators[c['evaluator']](g)
            if ok:matches.append({'id':c['id'],'name':c['name'],'result':c['result'],'reason':reason})
        return matches
    def searing(self,g):
        # One Treasure produced by Storm-Kiln Artist per spell cast; as long as
        # the repeat casting costs one red, Treasure recoups that mana.
        return (g.discount()>=4 and g.can_pay('Searing Touch',buyback=True),
                'Buyback is entirely generic-discounted; each cast pays R and produces >=1 Treasure.')
    def speculation_altar(self,g):
        return (g.discount()>=2 and g.can_pay('Mystic Speculation',buyback=True),
                'Each U casting makes >=1 Pyromancer token; sacrifice that token to Altar for U.')
    def speculation_class(self,g):
        return (g.discount()>=2 and g.can_pay('Mystic Speculation',buyback=True),
                'Each U casting makes >=1 hasty Stormsplitter copy; tap new copy for spell-only U.')
    def execute_bounded(self,g,combo_id,cycles=3):
        """Replay at most cycles iterations through the ordinary cast/payment engine.

        Reports observed repeatability; deliberately does not declare infinity or a win.
        """
        recipe=next(c for c in self.recipes if c['id']==combo_id)
        ready={x['id'] for x in self.evaluate(g)}
        if combo_id not in ready:return {'iterations':0,'sustainable':False}
        spell=recipe['cycle']['cast']
        completed=0
        for _ in range(cycles):
            if not g.cast(spell,buyback=True):break
            completed+=1
        # Test whether state could sustain at least one more real iteration.
        after={x['id'] for x in self.evaluate(g)}
        return {'iterations':completed,'sustainable':completed==cycles and combo_id in after,
                'note':'Simulated bounded repetitions; not a full proof of an infinite loop.'}
