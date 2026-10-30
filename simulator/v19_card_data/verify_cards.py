"""Validate deck identities against a supplied Scryfall Oracle bulk snapshot.

This tool does not download data; pass a locally supplied JSON or JSONL snapshot.
It preserves exact names and fails closed on missing or ambiguous records.
"""
import argparse, gzip, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v18_budget_deck'))
from budget_table import load_deck

ALLOWED=frozenset('UR')
def verify(deck, records):
    needed={name for (_,name) in deck}; found={name:[] for name in needed}; faces={name:[] for name in needed}
    for card in records:
        exact=card.get('name')
        if exact in found: found[exact].append(card)
        # Exact Oracle names win over incidental matches to another card's face.
        face_names={face.get('name') for face in card.get('card_faces', []) if isinstance(face, dict)}
        for name in (face_names & needed)-{exact}: faces[name].append(card)
    rows=[]
    for name in sorted(needed):
        matches=found[name] or faces[name]
        if len(matches)!=1:
            rows.append({'name':name,'status':'missing' if not matches else 'ambiguous','count':len(matches)});continue
        card=matches[0]; identity=card.get('color_identity'); typ=card.get('type_line'); oid=card.get('oracle_id')
        if (not isinstance(identity,list) or any(c not in {'W','U','B','R','G'} for c in identity)
                or not isinstance(typ,str) or not typ.strip() or not isinstance(oid,str) or not oid):
            rows.append({'name':name,'status':'invalid_metadata'});continue
        status='valid' if set(identity)<=ALLOWED else 'outside_commander_identity'
        rows.append({'name':name,'status':status,'oracle_id':oid,'type_line':typ,
                     'color_identity':identity,'mana_cost':card.get('mana_cost'),
                     'layout':card.get('layout'),'commander_legality':card.get('legalities',{}).get('commander'),
                     'oracle_name':card.get('name'),'scryfall_uri':card.get('scryfall_uri')})
    return {'deck_card_count':sum(deck.values()),'distinct_names':len(needed),
            'all_metadata_verified':all(r['status']=='valid' for r in rows),
            'commander_legality_verified':all(r.get('commander_legality')=='legal' for r in rows),
            'cards':rows}

def read_snapshot(path):
    p=Path(path)
    opener=gzip.open if p.suffix=='.gz' else open
    with opener(p,'rt',encoding='utf-8') as f:
        if p.name.endswith(('.jsonl','.jsonl.gz')):
            yield from (json.loads(line) for line in f if line.strip())
        else:
            data=json.load(f)
            if not isinstance(data,list):raise ValueError('Snapshot must be a JSON array or JSONL records')
            yield from data

def main():
    parser=argparse.ArgumentParser();parser.add_argument('snapshot');parser.add_argument('--output',required=True)
    args=parser.parse_args();report=verify(load_deck(),read_snapshot(args.snapshot));report['source_snapshot']=Path(args.snapshot).name
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='cards'}))
    if not report['all_metadata_verified'] or not report['commander_legality_verified']:sys.exit(1)
if __name__=='__main__':main()
