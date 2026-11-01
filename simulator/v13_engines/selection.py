"""Ordered look/scry/hand choices over the authoritative ID-only library index.

Library storage is bottom-to-top; all policy orders are top-first. Policies see
only the cards relevant to the choice and never receive an opportunity to act.
"""
from dataclasses import dataclass
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from commander_sim.legacy_common_ops import DrawDiscard,apply_draw_discard


@dataclass(frozen=True)
class CardOption:
    object_id:int
    name:str
    kind:str
    effect:str


@dataclass(frozen=True)
class SelectionRequest:
    kind:str
    controller:int
    cards:tuple[CardOption,...]
    count:int=0


class Selection:
    def __init__(self,table):self.t=table;self.history=[]

    def request(self,kind,seat,ids,count=0):
        specs=self.t.zones.specs
        cards=tuple(CardOption(oid,self.t.rules.get(oid).card.name,
                              specs[self.t.rules.get(oid).card.card_id].kind,
                              specs[self.t.rules.get(oid).card.card_id].effect) for oid in ids)
        return SelectionRequest(kind,seat,cards,count)

    def score(self,seat,card):
        return (0 if card.effect=='unsupported' else 90 if card.kind=='land' and self.t.players[seat].lands<4
                else 20 if card.kind=='land' else 70)

    def ask(self,request,default):
        policy=getattr(self.t,'selection_policy',None)
        return policy(request) if policy else default

    def choose(self,kind,seat,ids,count):
        ids=tuple(ids);request=self.request(kind,seat,ids,count)
        preferred=sorted(request.cards,key=lambda c:-self.score(seat,c))
        default=tuple(c.object_id for c in preferred[:count])
        chosen=tuple(self.ask(request,default))
        if len(chosen)!=count or len(set(chosen))!=len(chosen) or any(x not in ids for x in chosen):
            raise ValueError('Selection must contain the required number of distinct legal IDs')
        self.record(kind,seat,chosen)
        return chosen

    def record(self,kind,seat,ids=(),**data):
        self.history.append(dict(kind=kind,controller=seat,ids=list(ids),**data))
        names=[self.t.rules.get(x).card.name for x in ids if x in self.t.rules.objects]
        self.t.note(f'    CHOICE {kind} P{seat}: {names}; {data}.')

    def look(self,seat,n):return tuple(reversed(self.t.zones.ids(seat,'library')[-n:])) if n else ()

    def rearrange(self,seat,seen,top,bottom):
        seen,top,bottom=tuple(seen),tuple(top),tuple(bottom)
        selected=top+bottom
        if len(selected)!=len(seen) or len(set(selected))!=len(selected) or set(selected)!=set(seen):
            raise ValueError('Top/bottom must partition the looked-at cards exactly')
        ids=self.t.zones.order[seat,'library']
        if any(oid not in ids for oid in seen):raise ValueError('Looked-at object left the library')
        ids[:]=list(reversed(bottom))+[oid for oid in ids if oid not in set(seen)]+list(reversed(top))
        self.t.zones.operations.append(('reorder',seat,top,bottom))
        self.t.rules._dirty()

    def put_back(self,seat,n):
        hand=self.t.zones.ids(seat,'hand')
        # Default puts the least useful cards back; policy order is next-draw first.
        request=self.request('brainstorm_put_back',seat,hand,min(n,len(hand)))
        preferred=sorted(request.cards,key=lambda c:self.score(seat,c))
        chosen=tuple(self.ask(request,tuple(c.object_id for c in preferred[:request.count])))
        if len(chosen)!=request.count or len(set(chosen))!=len(chosen) or any(x not in hand for x in chosen):
            raise ValueError('Invalid Brainstorm put-back choice')
        self.record(request.kind,seat,chosen)
        for oid in reversed(chosen):self.t.zones.move(oid,'library')

    def discard(self,seat,n=1,kind='discard'):
        hand=self.t.zones.ids(seat,'hand');count=min(n,len(hand))
        request=self.request(kind,seat,hand,count)
        preferred=sorted(request.cards,key=lambda c:self.score(seat,c))
        chosen=tuple(self.ask(request,tuple(c.object_id for c in preferred[:count])))
        if len(chosen)!=count or len(set(chosen))!=count or any(x not in hand for x in chosen):
            raise ValueError('Invalid discard choice')
        self.record(kind,seat,chosen)
        for oid in chosen:self.t.zones.discard(seat,oid)

    def scry(self,seat,n):
        seen=self.look(seat,n);request=self.request('scry',seat,seen)
        top=tuple(c.object_id for c in sorted(request.cards,key=lambda c:-self.score(seat,c)) if self.score(seat,c)>20)
        bottom=tuple(c.object_id for c in request.cards if c.object_id not in top)
        choice=self.ask(request,{'top':top,'bottom':bottom})
        if not isinstance(choice,dict) or set(choice)!={'top','bottom'}:raise ValueError('Scry requires top and bottom')
        self.rearrange(seat,seen,choice['top'],choice['bottom'])
        self.record('scry',seat,seen,top=list(choice['top']),bottom=list(choice['bottom']))

    def resolve(self,name,seat):
        player=self.t.players[seat]
        if name=='Brainstorm':
            apply_draw_discard(self.t,seat,DrawDiscard(3));self.put_back(seat,2)
        elif name=='Ponder':
            seen=self.look(seat,3);top=self.choose('ponder_order',seat,seen,len(seen))
            self.rearrange(seat,seen,top,())
            request=self.request('ponder_shuffle',seat,seen)
            shuffle=self.ask(request,bool(request.cards) and all(self.score(seat,c)<=20 for c in request.cards))
            if type(shuffle) is not bool:raise ValueError('Ponder shuffle must be a boolean choice')
            if shuffle:self.t.zones.shuffle(seat)
            self.record('ponder_shuffle',seat,shuffle=shuffle);player.draw()
        elif name=='Preordain':self.scry(seat,2);player.draw()
        elif name in ('Telling Time','Impulse'):
            seen=self.look(seat,3 if name=='Telling Time' else 4)
            chosen=self.choose('look_to_hand',seat,seen,min(1,len(seen)))
            remaining=tuple(x for x in seen if x not in chosen)
            if name=='Telling Time':
                top=self.choose('telling_top',seat,remaining,min(1,len(remaining)))
                bottom=tuple(x for x in remaining if x not in top)
            else:top=();bottom=self.choose('impulse_bottom',seat,remaining,len(remaining))
            # Validate all choices before moving the chosen card out of the looked-at set.
            self.rearrange(seat,remaining,top,bottom)
            for oid in chosen:self.t.zones.move(oid,'hand')
        elif name=='Frantic Search':
            player.draw(2);self.discard(seat,2,'frantic_discard')
            lands=tuple(o.object_id for o in self.t.rules.on_battlefield() if 'land' in o.types)
            policy=getattr(self.t,'frantic_untap_policy',None)
            chosen=tuple(policy(seat,lands)) if policy else tuple(oid for oid in lands if self.t.rules.get(oid).controller==seat and self.t.rules.get(oid).tapped)[:3]
            if len(chosen)>3 or len(set(chosen))!=len(chosen) or any(x not in lands for x in chosen):
                raise ValueError('Frantic Search needs up to three distinct lands')
            for oid in chosen:self.t.rules.get(oid).tapped=False
            self.t.rules._dirty();self.record('frantic_untap',seat,chosen)
        else:raise NotImplementedError('Unknown selection spell')
