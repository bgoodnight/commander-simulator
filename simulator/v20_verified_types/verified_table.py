"""Use verified card types for v1.13 while leaving unsupported effects inert."""
import json, sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v18_budget_deck'))
from budget_table import BudgetTable, load_deck

DATA=Path(__file__).with_name('CARD_IDENTITIES.json')
TYPES=frozenset({'land','creature','artifact','enchantment','planeswalker','instant','sorcery','battle','kindred'})

def read_types():
    report=json.loads(DATA.read_text())
    if not report['all_metadata_verified'] or not report['commander_legality_verified']:
        raise ValueError('Deck identity verification incomplete')
    records={r['name']:r for r in report['cards']}
    if set(records)!={name for _,name in load_deck()}:raise ValueError('Identity report does not match deck')
    result={}
    for name,row in records.items():
        front=row['type_line'].split(' // ',1)[0].split(' — ',1)[0].lower()
        result[name]=frozenset(front.split()) & TYPES
        if not result[name]:raise ValueError('Unsupported type line for '+name)
    return result

class VerifiedTable(BudgetTable):
    def deck_types(self):
        return read_types()

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        types=self.deck_types()
        for obj in self.rules.objects.values():
            if obj.owner==self.detailed_seat and not obj.token:
                obj.card=replace(obj.card,types=types[obj.card.name])
        self.rules._dirty()
