"""Deterministic pre-optimization reference, excluding runtime/cache statistics."""
from dataclasses import is_dataclass,fields
from collections.abc import Mapping
import hashlib,json


def canonical(value):
    if is_dataclass(value):
        # Preserve v14 reference format for the later optional unknown-color field.
        return {f.name:canonical(getattr(value,f.name)) for f in fields(value)
                if not (f.name=='colors' and type(value).__name__=='CardDefinition' and getattr(value,f.name) is None)}
    if isinstance(value,Mapping):return {str(k):canonical(v) for k,v in value.items()}
    if isinstance(value,(set,frozenset)):return sorted(canonical(x) for x in value)
    if isinstance(value,(tuple,list)):return [canonical(x) for x in value]
    return value


def reference_payload(t):
    objects=[]
    for oid,o in sorted(t.rules.objects.items()):
        objects.append(dict(id=oid,card=o.card,owner=o.owner,controller=o.controller,zone=o.zone,
                            token=o.token,tapped=o.tapped,damage=o.damage_marked,power=o.power,
                            toughness=o.toughness,counters=dict(o.counters),modifiers=o.modifiers))
    return canonical(dict(objects=objects,zone_order=[(seat,zone,ids) for (seat,zone),ids in sorted(t.zones.order.items()) if ids],
                          players=[p.snapshot(t.round_num) for p in t.players],turns=t.turns,
                          land_turns=[getattr(p,'_land_turn',None) for p in t.players],
                          active=t.active_seat,turn_order=getattr(t,'turn_order',(0,1,2,3)),turn_serial=t.turn_serial,phase=t.phase,step=t.step,
                          attack_ready=t.attack_ready,frames=t.spell_stack.frames,pending=t.spell_stack.pending,
                          spell_tickets=t.zones._pending,
                          rng=t.rng.getstate(),player_rng=[p.rng.getstate() for p in t.players],zone_rng=t.zones.rng.getstate(),
                          winner=t.winner,reason=t.win_reason,safety=t.safety_stop,
                          moves=t.rules.moves,rule_events=t.rules.events,zone_operations=t.zones.operations,
                          mana_pools=t.rules.mana_pools,payments=t.resources.payments,activations=t.resources.activations,
                          priority=t.spell_stack.history,steps=t.step_history,combat=t.combat_batches,
                          selection=t.selection.history,engines=t.engine_events,lands=t.land_events,
                          delayed=t.delayed_exiles,end_serial=t.end_step_serial))


def fingerprint(t):
    raw=json.dumps(reference_payload(t),sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()
