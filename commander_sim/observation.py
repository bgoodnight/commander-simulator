"""Conservative six-turn projections from a hash-matched identity snapshot.

This is not the live game engine. Only basic lands and reviewed Command Tower
production are modeled. No spells, other land abilities, combat, triggers or responses are
resolved. Candidate spells are a mana-value screen, not legal-action checks.
"""
from collections import Counter
import json
from pathlib import Path
import random
from .snapshots import validate_snapshot
from .identities import CardRegistry
from .mana_costs import (
    parse_fixed_mana_cost, plan_source_payment, UnsupportedManaCost
)

_BASIC=frozenset({'Plains','Island','Swamp','Mountain','Forest','Wastes',
                  'Snow-Covered Plains','Snow-Covered Island','Snow-Covered Swamp',
                  'Snow-Covered Mountain','Snow-Covered Forest'})
_BASIC_COLORS={'Plains':'W','Island':'U','Swamp':'B','Mountain':'R','Forest':'G','Wastes':'C'}

def _source_colors(name, commander_colors):
    if name == 'Command Tower':return tuple(sorted(commander_colors))
    basic=name.removeprefix('Snow-Covered ')
    return (_BASIC_COLORS[basic],) if basic in _BASIC_COLORS else ()

def _mulligan_decision(known_lands, unknown_faces):
    """Take the first free mulligan only when all possible counts are poor."""
    if known_lands > 5 or known_lands + unknown_faces < 2:
        return 'mulligan'
    if known_lands >= 2 and known_lands + unknown_faces <= 5:
        return 'keep'
    return 'uncertain_keep'

def observe(deck_path, snapshot_path, *, seed=0, turns=6, reserve=0, threats=(), commander='Magnus the Red', mulligan='keep'):
    if type(seed) is not int or type(turns) is not int or turns < 1 or turns > 100:
        raise ValueError('Expected integer seed and 1 to 100 turns')
    if type(reserve) is not int or reserve < 0:
        raise ValueError('Reserve must be a nonnegative integer')
    if mulligan not in ('keep','one-free'):
        raise ValueError('Mulligan policy must be keep or one-free')
    if not isinstance(threats, (tuple, list)) or any(not isinstance(item, dict) or type(item.get('turn')) is not int or item['turn'] < 1 for item in threats):
        raise ValueError('Threats must be objects with a positive integer turn')
    snapshot = validate_snapshot(deck_path, snapshot_path, commander=commander)
    registry = CardRegistry(snapshot)
    commander_colors=registry.get(commander).color_identity
    library = [name for section,name,quantity in snapshot.deck.cards if section == 'Library' for _ in range(quantity)]
    rng=random.Random(seed);rng.shuffle(library)
    hand=library[:7]; del library[:7]
    initial_hand=list(hand)
    known_lands=unknown_faces=0
    for name in hand:
        try:face=registry.get(name).primary_face()
        except NotImplementedError:
            unknown_faces+=1;continue
        if 'land' in face.types:known_lands+=1
    decision=_mulligan_decision(known_lands,unknown_faces) if mulligan=='one-free' else 'keep'
    if decision=='mulligan':
        # Commander multiplayer grants the first mulligan for free: shuffle
        # the hand into the library and draw seven, with no card bottomed.
        library.extend(hand);rng.shuffle(library);hand=library[:7];del library[:7]
    opening_hand=list(hand)
    lands=[]; trace=[]
    for turn in range(1,turns+1):
        drawn=library.pop(0) if library else None
        if drawn:hand.append(drawn)
        # A reproducible, deliberately narrow policy; it does not use hidden library knowledge.
        land=next((name for name in hand if (name in _BASIC or name == 'Command Tower') and _source_colors(name,commander_colors)),None)
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
        # Source-backed *payment preview* for the existing observation trace.
        # Each hypothetical card uses a fresh independent assignment of
        # currently modeled basic/Command Tower sources. No spell is cast, no
        # source taps, no mana floats, and unmodeled mana costs fail closed.
        source_modes = tuple(_source_colors(source, commander_colors)
                             for source in lands)
        paid_previews = []
        for name in hand:
            identity = registry.get(name)
            try:
                face = identity.primary_face()
            except NotImplementedError:
                continue
            if 'land' in face.types or identity.layout != 'normal':
                continue
            try:
                cost = parse_fixed_mana_cost(face.mana_cost)
            except UnsupportedManaCost:
                continue
            plan = plan_source_payment(cost, source_modes)
            if plan is not None:
                paid_previews.append({
                    'card': name, 'mana_cost': face.mana_cost,
                    'source_indices': list(plan),
                    'source_names': [lands[i] for i in plan],
                    'status': 'source_paid_mana_preview',
                    'limitations': ('Mana symbols can be matched by modeled sources; '
                                    'this is NOT a legal spell cast. No extra costs, '
                                    'timing, targets, abilities or resolution checked')
                })
        current_threats=[dict(item) for item in threats if item.get('turn')==turn]
        if len(library)+len(hand)+len(lands)+1 != 100:
            raise AssertionError('Physical card conservation failed')
        trace.append({'turn':turn,'drawn':drawn,'land_played':land,'modeled_basic_sources':dict(Counter(name for name in lands if name in _BASIC)),
                      'modeled_sources':[{'card':name,'colors':list(_source_colors(name,commander_colors))} for name in lands],
                      'reserved_mana':reserved,'in_hand':list(hand),'playable_now':[],
                      'candidate_if_supported':candidates,
                      'source_paid_mana_preview':paid_previews,
                      'scripted_threats':current_threats,
                      'library_count':len(library),'hand_count':len(hand),'battlefield_count':len(lands)})
    return {'mode':'observation','commander':commander,'deck_sha256':snapshot.deck_sha256,'snapshot_sha256':snapshot.snapshot_sha256,
            'seed':seed,'turns':turns,'opening_hand_policy':('keep seven' if mulligan=='keep' else 'one free mulligan if all possible land counts are outside 2–5; otherwise keep'),
            'mulligan':{'policy':mulligan,'decision':decision,'initial_hand':initial_hand,
                        'known_lands':known_lands,'unknown_faces':unknown_faces,
                        'limitations':'at most one free multiplayer mulligan; no color, curve or spell quality assessment'},
            'opening_hand':opening_hand,
            'seat_assumption':'not the starting player; draw on turn one',
            'land_policy':'play first basic land or Command Tower in hand; other nonbasic lands are not modeled',
            'reserve_policy':f'reserve up to {reserve} modeled sources as a hypothetical planning choice',
            'first_unmodeled_choice':'turn 1: other nonbasic land and spell decisions are not modeled',
            'not_modeled':['spell casting or resolution','non-mana legal cast restrictions',
                           'alternative and additional costs','other nonbasic land abilities',
                           'triggers','opponent actions except supplied threat descriptions','combat','win rates'],
            'mana_preview_scope': ('Fixed printed W/U/B/R/G/C plus generic costs only, '
                                   'using currently modeled basics and Command Tower. '
                                   'No taps, casts, special costs, effects or priority.'),
            'trace':trace}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('deck');parser.add_argument('snapshot');parser.add_argument('--seed',type=int,default=0)
    parser.add_argument('--commander',default='Magnus the Red')
    parser.add_argument('--turns',type=int,default=6);parser.add_argument('--reserve',type=int,default=0)
    parser.add_argument('--mulligan',choices=('keep','one-free'),default='keep')
    parser.add_argument('--threats',type=Path,help='JSON array of explicitly scripted threat descriptions')
    args=parser.parse_args()
    try:
        threats=json.loads(args.threats.read_text()) if args.threats else []
        if not isinstance(threats,list) or any(not isinstance(x,dict) or not isinstance(x.get('turn'),int) for x in threats):
            raise ValueError('Threats must be a JSON array of objects with integer turn')
        print(json.dumps(observe(args.deck,args.snapshot,seed=args.seed,turns=args.turns,reserve=args.reserve,threats=threats,commander=args.commander,mulligan=args.mulligan),indent=2))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        parser.error(str(exc))
