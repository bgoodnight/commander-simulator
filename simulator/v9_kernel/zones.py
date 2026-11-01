"""Reusable authoritative nonbattlefield card-zone service for the *next* live migration.

Uses the exact central GameKernel object registry and zone moves, never a copied
card-state dictionary. Ordered zone indices contain object IDs only, not card data.
Does not pretend that the v6 legacy pilot has been migrated; V9Table has not
installed this service into the old list-mutating draw/mulligan/cast methods.
"""
from __future__ import annotations
from collections import defaultdict,Counter
from dataclasses import dataclass
from random import Random
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v8_central'))
from kernel import CentralKernel
from rules import CardDefinition,Event

CARD_ZONES=frozenset({'library','hand','graveyard','exile','command','stack','battlefield'})

@dataclass(frozen=True)
class CastTicket:
    object_id:int
    seat:int
    spell_types:frozenset[str]
    card_name:str

class KernelZones:
    """Physical-card identities and ordered zones, for any seat (no seat-zero logic).

    'battlefield' transitions are supported in this service but callers must
    supply a compatible battlefield projection when using the legacy v8 table.
    Hence the integration remains gated until full zone-backed players exist.
    """
    def __init__(self,kernel:CentralKernel|None=None,seats=4,seed=1):
        if seats!=4:raise ValueError('Commander prototype requires four seats')
        self.kernel=kernel or CentralKernel()
        self.seats=seats;self.rng=Random(seed)
        self.order=defaultdict(list) # (owner,zone)->list of authoritative kernel IDs
        self.operations=[]
        self._pending:dict[int,CastTicket]={}
    def _checkseat(self,seat):
        if not 0<=seat<self.seats:raise ValueError('Invalid seat')
    def add(self,definition:CardDefinition,owner:int,zone='library',token=False):
        self._checkseat(owner)
        if zone not in CARD_ZONES:raise ValueError(zone)
        if token and zone!='battlefield':raise ValueError('Token cannot originate off battlefield')
        obj=self.kernel.add(definition,owner,zone=zone,token=token)
        self.order[owner,zone].append(obj.object_id)
        self.operations.append(('add',owner,obj.object_id,zone))
        return obj.object_id
    def ids(self,seat:int,zone:str):
        self._checkseat(seat)
        return tuple(self.order[seat,zone])
    def names(self,seat:int,zone:str):
        return tuple(self.kernel.get(oid).card.name for oid in self.ids(seat,zone))
    def move(self,oid:int,to_zone:str,reason='resolve',commander_choice=False):
        if to_zone not in CARD_ZONES:raise ValueError(to_zone)
        obj=self.kernel.get(oid);owner=obj.owner;old=obj.zone
        if oid not in self.order[owner,old]:raise AssertionError('Unknown zone index entry')
        transition=self.kernel.move(oid,to_zone,reason,commander_choice)
        if transition is None:return oid
        self.order[owner,old].remove(oid)
        if transition.new_object_id is not None:
            self.order[owner,transition.new_zone].append(transition.new_object_id)
        self.operations.append((reason,owner,oid,transition.new_object_id,old,transition.new_zone))
        return transition.new_object_id
    def draw(self,seat:int,n=1):
        if n<0:raise ValueError('Negative draw')
        draws=[]
        for _ in range(n):
            if not self.ids(seat,'library'):
                # Empty-library draw is a LOSS to process in the caller's
                # shared state-based-action window, not a synthetic card.
                self.operations.append(('draw_from_empty',seat))
                return tuple(draws),False
            draws.append(self.move(self.ids(seat,'library')[-1],'hand'))
        return tuple(draws),True
    def discard(self,seat:int,oid:int):
        if oid not in self.ids(seat,'hand'):raise ValueError('Card not in hand')
        return self.move(oid,'graveyard','discard')
    def mill(self,seat:int,n=1):
        if n<0:raise ValueError('Negative mill')
        return tuple(self.move(oid,'graveyard','mill') for oid in list(reversed(self.ids(seat,'library')[-n:])) if n)
    def search_to_hand(self,seat:int,predicate):
        matches=[x for x in self.ids(seat,'library') if predicate(self.kernel.get(x).card)]
        if not matches:return None
        oid=self.move(matches[0],'hand')
        self.shuffle(seat)
        return oid
    def shuffle(self,seat:int):
        ids=self.order[seat,'library']
        self.rng.shuffle(ids)
        self.operations.append(('shuffle',seat,len(ids)))
    def cast(self,seat:int,oid:int,*,reviewed_origin=None,
             exile_on_stack_exit=False):
        # Physical zone kernel is not the permission engine. Only callers that
        # have independently reviewed an ability may request a graveyard cast;
        # the default remains legal hand/command only.
        if reviewed_origin is None:
            allowed=oid in self.ids(seat,'hand') or oid in self.ids(seat,'command')
        elif reviewed_origin=='graveyard':
            allowed=oid in self.ids(seat,'graveyard')
        else:
            raise ValueError('Unknown reviewed casting origin')
        if not allowed:
            raise ValueError('Card not available to cast')
        card=self.kernel.get(oid).card
        if type(exile_on_stack_exit) is not bool:
            raise ValueError('Exile replacement permission must be Boolean')
        if exile_on_stack_exit and (reviewed_origin!='graveyard'
                or not hasattr(self.kernel,'flashback_pending')
                or not card.types.intersection({'instant','sorcery'})):
            raise ValueError('Reviewed graveyard flashback stack required')
        if 'land' in card.types:raise ValueError('Land is played, not cast')
        if card.coverage=='unimplemented':raise NotImplementedError('Unsupported card '+card.name)
        new=self.move(oid,'stack')
        ticket=CastTicket(new,seat,card.types,card.name)
        self._pending[new]=ticket
        if exile_on_stack_exit:
            self.kernel.flashback_pending.add(new)
        # Cast event is separate from both subsequent countering and resolving.
        metadata=(('origin','graveyard'),) if reviewed_origin=='graveyard' else ()
        self.kernel.events.append(Event('spell_cast',seat,new,spell_types=card.types,
                                        metadata=metadata))
        return ticket
    def counter(self,ticket:CastTicket,commander_to_command=True):
        self._require_ticket(ticket)
        obj=self.kernel.get(ticket.object_id)
        new=self.move(ticket.object_id,'graveyard',commander_choice=commander_to_command)
        self._pending.pop(ticket.object_id)
        self.kernel.events.append(Event('spell_countered',ticket.seat,ticket.object_id,spell_types=obj.types))
        return new
    def resolve(self,ticket:CastTicket,effect=None,*,spell_destination=None):
        self._require_ticket(ticket)
        obj=self.kernel.get(ticket.object_id)
        permanent=bool(obj.types.intersection({'creature','artifact','enchantment','planeswalker','battle'}))
        if spell_destination is not None and (
                permanent or spell_destination not in {'graveyard','exile','hand'}):
            raise ValueError('Invalid reviewed spell resolution destination')
        if not permanent and effect is None:
            # We cannot invent printed spell behavior. Keep the ticket and object
            # on stack until a registered/verified handler is available.
            raise NotImplementedError('Missing resolution effect for '+obj.card.name)
        if effect is not None:
            effect(self.kernel,ticket)
        # A reviewed additional buyback cost may direct a resolving spell to
        # its owner's hand. The spell remains a physical card; it is not
        # duplicated, and flashback exile replacement still wins on exit.
        new=self.move(ticket.object_id,
                      'battlefield' if permanent else spell_destination or 'graveyard')
        self._pending.pop(ticket.object_id)
        self.kernel.events.append(Event('spell_resolved',ticket.seat,ticket.object_id,spell_types=obj.types))
        return new
    def play_land(self,seat:int,oid:int):
        if oid not in self.ids(seat,'hand') or 'land' not in self.kernel.get(oid).types:
            raise ValueError('Not a land card in hand')
        # Once-per-turn legal action determination belongs to the table.
        return self.move(oid,'battlefield')
    def _require_ticket(self,ticket):
        if self._pending.get(ticket.object_id)!=ticket or self.kernel.get(ticket.object_id).zone!='stack':
            raise ValueError('No such active spell')
    def leave_game(self,seat:int):
        """Remove owned objects, with no artificial death triggers or exile."""
        self._checkseat(seat)
        for zone in CARD_ZONES:
            for oid in list(self.ids(seat,zone)):
                self.order[seat,zone].remove(oid)
                self.kernel.objects.pop(oid,None)
                self._pending.pop(oid,None)
        self.kernel._dirty()
        self.operations.append(('leave_game',seat))
    def assert_consistent(self):
        all_ids=[]
        for (owner,zone),ids in self.order.items():
            for oid in ids:
                if oid not in self.kernel.objects:raise AssertionError('Missing kernel card '+str(oid))
                o=self.kernel.get(oid)
                if (o.owner,o.zone)!=(owner,zone):raise AssertionError('Zone index differs from object')
                all_ids.append(oid)
        if len(all_ids)!=len(set(all_ids)):raise AssertionError('Duplicate card object')
        if set(all_ids)!=set(self.kernel.objects):raise AssertionError('Kernel contains unindexed cards')
        if any(oid not in self.order[t.seat,'stack'] for oid,t in self._pending.items()):
            raise AssertionError('Pending spell not on stack')
        return True
