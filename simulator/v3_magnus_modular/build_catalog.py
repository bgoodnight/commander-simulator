"""One-time initial catalog import; edit cards.json directly for subsequent changes."""
import json,re
from pathlib import Path
root=Path(__file__).parent
lines=(root/'deck_v16.txt').read_text().splitlines()
section=None; cards={}
for l in lines:
    if l.startswith('Commander ('):section='commander'
    elif l.startswith('Creatures ('):section='creature'
    elif l.startswith('Artifacts and Enchantments ('):section='permanent'
    elif l.startswith('Instants and Sorceries ('):section='spell'
    elif l.startswith('Lands ('):section='land'
    m=re.match(r'^(\d+) (.+)$',l)
    if m and section:cards[m.group(2)]={'type':section, 'count':int(m.group(1)),'cost':None,'effects':[],'status':'unmodeled'}
# Cost format [generic, blue, red]. Costs and tags below must be independently checked for each new card.
costs={
'Magnus the Red':(3,1,1),'Sol Ring':(1,0,0),'Arcane Signet':(2,0,0),'Izzet Signet':(2,0,0),'Talisman of Creativity':(2,0,0),'Fellwar Stone':(2,0,0),'Mind Stone':(2,0,0),
'Young Pyromancer':(1,0,1),'Third Path Iconoclast':(0,1,1),'Goblin Electromancer':(0,1,1),'Baral, Chief of Compliance':(1,1,0),"Jace, Vryn's Prodigy":(1,1,0), 'Harmonic Prodigy':(1,0,1), 'Voidmage Prodigy':(0,2,0),'Sigil Tracer':(1,2,0),'Patron Wizard':(0,3,0),'Spellseeker':(2,1,0),'Stormsplitter':(3,0,1),'Storm-Kiln Artist':(3,0,1),'Veyran, Voice of Duality':(1,1,1),'Archmage Emeritus':(2,2,0),'Docent of Perfection':(3,2,0),
'Sorcerer Class':(0,1,1),'Phyrexian Altar':(3,0,0),'The Lost and the Damned':(1,1,1),'Arcane Adaptation':(2,1,0),'Maskwood Nexus':(4,0,0),'Resonating Lute':(2,1,1),'Underworld Breach':(1,0,1),
'Brainstorm':(0,1,0),'Ponder':(0,1,0),'Preordain':(0,1,0),'Telling Time':(1,1,0),'Impulse':(1,1,0),'Frantic Search':(2,1,0),'Mystic Speculation':(0,1,0),'Searing Touch':(0,0,1),'Capsize':(1,2,0),'Counterspell':(0,2,0),'Arcane Denial':(1,1,0),'Flusterstorm':(0,1,0),'Swan Song':(0,1,0),"An Offer You Can't Refuse":(0,1,0),
'Pongify':(0,1,0),'Abrade':(1,0,1),'Chaos Warp':(2,0,1),'Chaos Mutation':(3,1,1),'Mystical Tutor':(0,1,0),'Muddle the Mixture':(0,2,0),'Step Through':(3,2,0),'Twincast':(0,2,0),'Reiterate':(1,0,2),'Mathemagics':(0,2,0),'Comet Storm':(0,0,2),'March of Swirling Mist':(0,1,0),'Jeska\'s Will':(2,0,1),'Mana Geyser':(3,0,2),'Cyclonic Rift':(1,1,0),
'Pink Horror':(3,0,1),'Lord of Change':(5,2,0),'Tzaangor Shaman':(2,1,1),'Exalted Flamer of Tzeentch':(2,0,1), 'Heralds of Tzeentch':(4,1,0),'Mutalith Vortex Beast':(4,1,1), 'Dualcaster Mage':(1,0,2),
}
for name,v in cards.items():
    if name in costs:v['cost']=costs[name]
    if v['type']=='land':v['status']='modeled'
# Model hooks are declarative. Registry handlers understand these common operations.
types={
'Magnus the Red':['Demon','Primarch'],'Young Pyromancer':['Human','Shaman'],'Third Path Iconoclast':['Human','Monk'],'Harmonic Prodigy':['Human','Wizard'],'Storm-Kiln Artist':['Dwarf','Shaman'], 'Docent of Perfection':['Insect','Horror'],'Archmage Emeritus':['Human','Wizard'],'Patron Wizard':['Human','Wizard'],'Voidmage Prodigy':['Human','Wizard'],'Spellseeker':['Human','Wizard'],'Veyran, Voice of Duality':['Efreet','Wizard'],'Baral, Chief of Compliance':['Human','Wizard'],'Dualcaster Mage':['Human','Wizard'],'Stormsplitter':['Otter','Wizard'],"Jace, Vryn's Prodigy":['Human','Wizard'],'Goblin Electromancer':['Goblin','Wizard'],'Sigil Tracer':['Merfolk','Wizard'],'Tzaangor Shaman':['Shaman'],'Pink Horror':['Demon','Horror'],'Lord of Change':['Demon'],'Exalted Flamer of Tzeentch':['Demon'],'Heralds of Tzeentch':['Demon'],'Mutalith Vortex Beast':['Mutant','Beast']}
for n,t in types.items():cards[n]['subtypes']=t

def add(n,event,op,**kw):
    cards[n]['effects'].append({'event':event,'op':op,**kw});cards[n]['status']='modeled' if cards[n]['status']!='partial' else 'partial'
for n in ['Sol Ring','Arcane Signet','Izzet Signet','Talisman of Creativity','Fellwar Stone','Mind Stone']:
    cards[n]['mana_rock']=True;cards[n]['status']='modeled'
for n in ['Baral, Chief of Compliance','Goblin Electromancer']:
    add(n,'static','discount_spells',value=1)
add('Magnus the Red','static','discount_per_token',value=1)
add('Magnus the Red','combat_damage','create_token',token='Spawn',amount=1)
add('Harmonic Prodigy','static','double_wizard_shaman_triggers')
add('Veyran, Voice of Duality','static','additional_spell_triggers')
for n,token,amt in [('Young Pyromancer','Elemental',1),('Third Path Iconoclast','Soldier',1),('Docent of Perfection','Wizard',1),('Stormsplitter','Stormsplitter',1)]:
    add(n,'cast_instant_sorcery' if n!='Third Path Iconoclast' else 'cast_noncreature','create_token',token=token,amount=amt)
add('Storm-Kiln Artist','cast_or_copy_instant_sorcery','treasure',amount=1)
add('Archmage Emeritus','cast_or_copy_instant_sorcery','draw',amount=1)
add('The Lost and the Damned','cast_from_outside_hand','create_token',token='Spawn',amount=1)
add('Spellseeker','enter','tutor',filter='spell_mv_lte_2',destination='hand')
add('Sorcerer Class','enter','draw_discard',draw=2,discard=2)
add('Sorcerer Class','level_2','grant_spell_mana_to_creatures')
add('Phyrexian Altar','activated','sacrifice_for_mana')
add('Resonating Lute','static','lands_spell_mana_ability')
add('Arcane Adaptation','static','choose_type',chosen='Wizard')
add('Maskwood Nexus','static','all_creature_types')
add('Underworld Breach','static','escape_nonland_spells')
for n,ability in {'Brainstorm':'brainstorm','Ponder':'ponder','Preordain':'preordain','Telling Time':'telling_time','Impulse':'impulse','Frantic Search':'frantic_search','Mystic Speculation':'scry3'}.items():
    add(n,'resolve','selection',method=ability)
for n,val in {'Mystic Speculation':2,'Searing Touch':4,'Capsize':3}.items():
    cards[n]['buyback_generic']=val
    if n!='Mystic Speculation':add(n,'resolve','utility',method=n.lower().replace(' ','_'))
for n in ['Counterspell','Arcane Denial','Swan Song',"An Offer You Can't Refuse",'Flusterstorm']:
    cards[n]['reaction']='counter';cards[n]['status']='partial' # only scripted threat checks
for n in ['Pongify','Abrade','Chaos Warp','Cyclonic Rift','March of Swirling Mist']:
    cards[n]['reaction']='removal_or_protection';cards[n]['status']='partial'
for n in ['Mystical Tutor','Muddle the Mixture','Step Through','Twincast','Reiterate','Mathemagics','Comet Storm','Jeska\'s Will','Mana Geyser','Chaos Mutation','Tzaangor Shaman','Pink Horror','Lord of Change','Exalted Flamer of Tzeentch','Heralds of Tzeentch','Mutalith Vortex Beast','Dualcaster Mage','Patron Wizard','Voidmage Prodigy','Sigil Tracer','Stormsplitter',"Jace, Vryn's Prodigy",'Docent of Perfection','Sorcerer Class','Phyrexian Altar','Underworld Breach']:
    if cards[n]['status']=='modeled':cards[n]['status']='partial' # key effects deliberately not all implemented
for n in ['Searing Touch','Capsize']:cards[n]['status']='partial'
for n,v in cards.items():
    if v['type']=='spell' and v['effects'] and v['status']=='unmodeled':v['status']='partial'
# engine uses catalog hooks, not card name checks for triggers. Pilot only consults tags.
tags={
 'Sol Ring':['ramp'],'Arcane Signet':['ramp'],'Izzet Signet':['ramp'],'Talisman of Creativity':['ramp'],'Fellwar Stone':['ramp'],'Mind Stone':['ramp'],
 'Young Pyromancer':['early_engine','token_engine'],'Third Path Iconoclast':['early_engine','token_engine'],'Goblin Electromancer':['early_engine','discount_engine'],'Baral, Chief of Compliance':['early_engine','discount_engine'],"Jace, Vryn's Prodigy":['early_engine','looter'], 'Harmonic Prodigy':['early_engine','trigger_booster'],
 'Storm-Kiln Artist':['mana_engine'],'Stormsplitter':['token_engine','combo_piece'],'Archmage Emeritus':['draw_engine'],'Docent of Perfection':['token_engine'],'Voidmage Prodigy':['control_engine'],'Patron Wizard':['control_engine'],'Sigil Tracer':['copy_engine'],'Spellseeker':['tutor_engine'],
 'Sorcerer Class':['mana_engine','draw_engine'],'Phyrexian Altar':['mana_engine'],'Resonating Lute':['mana_engine'], 'Arcane Adaptation':['type_engine'],'Maskwood Nexus':['type_engine'],'The Lost and the Damned':['token_engine'],'Underworld Breach':['grave_engine'],
 'Brainstorm':['selection'],'Ponder':['selection'],'Preordain':['selection'],'Telling Time':['selection'],'Impulse':['selection'],'Frantic Search':['selection'],'Mystic Speculation':['selection','buyback_engine'],
 'Searing Touch':['buyback_engine','damage'],'Capsize':['buyback_engine','bounce'],'Mathemagics':['finisher'],'Comet Storm':['finisher'],
 'Counterspell':['counter'],'Arcane Denial':['counter'],'Swan Song':['counter'],"An Offer You Can't Refuse":['counter'],'Flusterstorm':['counter']}
for n,t in tags.items():cards[n]['tags']=t
(root/'cards.json').write_text(json.dumps({'version':1,'notes':'Card effects declared by card name; status=partial means not every printed behavior is simulated. Null cost means intentionally unsupported.','cards':cards},indent=2))
print('created',len(cards),'named entries',sum(x['count'] for x in cards.values()),'cards')
