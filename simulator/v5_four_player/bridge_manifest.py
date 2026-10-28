"""Audit readiness of v3 detailed card catalog for shared v5 model.
Does not silently translate unknown printed card abilities into fake effects.
"""
import json
from pathlib import Path
from collections import Counter
from simulation import ROOT

def make_manifest():
    older=ROOT/'v3_source'
    if not older.exists():older=ROOT.parent/'magnus_modular_v3'
    catalog=json.loads((older/'cards.json').read_text())['cards']
    deck=json.loads((older/'deck_v16.json').read_text())
    bystatus=Counter();bytype=Counter();special=[]
    cards={}
    for name,count in deck['cards'].items():
        d=catalog[name];bystatus[d['status']]+=count;bytype[d['type']]+=count
        cards[name]={'count':count,'v3_status':d['status'],'card_type':d['type'],
                     'v3_cost_URC':d.get('cost'),'tagged_effects':d.get('effects',[]),
                     'reaction':d.get('reaction'),
                     'v5_bridge_status':'needs adapter; not yet executable'}
        if d['status']!='modeled':special.append(name)
    return {'deck':deck['name'],'commander':deck['commander'],'library_count':sum(deck['cards'].values()),
            'legacy_status_counts':dict(bystatus),'legacy_type_counts':dict(bytype),
            'conversion_status':'schema validated; actual colored-cost, combat, spell trigger, and card-specific adapters pending',
            'cards_needing_validation':special,'cards':cards}
if __name__=='__main__':
    data=make_manifest();(ROOT/'v3_bridge_manifest.json').write_text(json.dumps(data,indent=2))
    print(data['library_count'],data['legacy_status_counts'])
