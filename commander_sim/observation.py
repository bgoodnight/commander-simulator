"""Conservative six-turn projections from a hash-matched identity snapshot.

This is not the live game engine. Only basic Island/Mountain land drops are
modeled. No spells, nonbasic land abilities, combat, triggers or responses are
resolved. Candidate spells are a mana-value screen, not legal-action checks.
"""
from collections import Counter
import json
from pathlib import Path
import random
from .snapshots import validate_snapshot
from .identities import CardRegistry


def observe(deck_path, snapshot_path, *, seed=0, turns=6, reserve=0, threats=()):
    if type(seed) is not int or type(turns) is not int or turns < 1 or turns > 100:
        raise ValueError('Expected integer seed and 1 to 100 turns')
    if type(reserve) is not int or reserve < 0:
        raise ValueError('Reserve must be a nonnegative integer')
    if not isinstance(threats, (tuple, list)) or any(not isinstance(item, dict) or type(item.get('turn')) is not int or item['turn'] < 1 for item in threats):
        raise ValueError('Threats must be objects with a positive integer turn')
    snapshot = validate_snapshot(deck_path, snapshot_path)
    registry = CardRegistry(snapshot)
    library = [name for section,name,quantity in snapshot.deck.cards if section == 'Library' for _ in range(quantity)]
    random.Random(seed).shuffle(library)
    hand=library[:7]; del library[:7]
    opening_hand=list(hand)
    lands=[]; trace=[]
    for turn in range(1,turns+1):
        drawn=library.pop(0) if library else None
        if drawn:hand.append(drawn)
        # A reproducible, deliberately narrow policy; it does not use hidden library knowledge.
        land=next((name for name in hand if name in ('Island','Mountain')),None)
        if land:
            hand.remove(land);lands.append(land)
        capacity=len(lands);reserved=min(reserve,capacity)
        candidates=[]
        for name in hand:
            card=registry.get(name)
            try:primary=card.primary_face()
            except NotImplementedError:continue
            if 'land' in primary.types:
                continue
            # Scryfall's aggregate CMC can describe another face; avoid claiming
            # a candidate for multiface cards until face-specific values exist.
            if card.layout != 'normal':
                continue
            value=primary.mana_value
            if isinstance(value,(int,float)) and value <= capacity-reserved:
                candidates.append({'card':name,'mana_value':value,'mana_cost':primary.mana_cost,
                                   'status':'candidate_if_supported',
                                   'limitations':'total-mana screen only; colors, timing, targets and effects not checked'})
        current_threats=[dict(item) for item in threats if item.get('turn')==turn]
        if len(library)+len(hand)+len(lands)+1 != 100:
            raise AssertionError('Physical card conservation failed')
        trace.append({'turn':turn,'drawn':drawn,'land_played':land,'modeled_basic_sources':dict(Counter(lands)),
                      'reserved_mana':reserved,'in_hand':list(hand),'playable_now':[],
                      'candidate_if_supported':candidates,'scripted_threats':current_threats,
                      'library_count':len(library),'hand_count':len(hand),'battlefield_count':len(lands)})
    return {'mode':'observation','deck_sha256':snapshot.deck_sha256,'snapshot_sha256':snapshot.snapshot_sha256,
            'seed':seed,'turns':turns,'opening_hand_policy':'keep seven; no mulligan model',
            'opening_hand':opening_hand,
            'seat_assumption':'not the starting player; draw on turn one',
            'land_policy':'play first Island or Mountain in hand; nonbasic lands are not modeled',
            'reserve_policy':f'reserve up to {reserve} basic sources as a hypothetical planning choice',
            'first_unmodeled_choice':'turn 1: nonbasic land and spell decisions are not modeled',
            'not_modeled':['spell casting or resolution','color requirements','nonbasic land abilities',
                           'triggers','opponent actions except supplied threat descriptions','combat','win rates'],
            'trace':trace}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('deck');parser.add_argument('snapshot');parser.add_argument('--seed',type=int,default=0)
    parser.add_argument('--turns',type=int,default=6);parser.add_argument('--reserve',type=int,default=0)
    parser.add_argument('--threats',type=Path,help='JSON array of explicitly scripted threat descriptions')
    args=parser.parse_args()
    try:
        threats=json.loads(args.threats.read_text()) if args.threats else []
        if not isinstance(threats,list) or any(not isinstance(x,dict) or not isinstance(x.get('turn'),int) for x in threats):
            raise ValueError('Threats must be a JSON array of objects with integer turn')
        print(json.dumps(observe(args.deck,args.snapshot,seed=args.seed,turns=args.turns,reserve=args.reserve,threats=threats),indent=2))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        parser.error(str(exc))
