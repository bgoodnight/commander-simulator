"""Focused named metadata upgrades; rules and stack operate on descriptors."""
from dataclasses import replace
from rules import Ability
from catalog import BY_NAME

UPGRADED=('Harmonic Prodigy','Storm-Kiln Artist','Baral, Chief of Compliance','Stormsplitter','Archmage Emeritus')
SELECTION=('Brainstorm','Ponder','Preordain','Telling Time','Impulse','Frantic Search')


def definition(original):
    name=original.name;abilities=original.abilities
    if name=='Harmonic Prodigy':
        abilities=tuple(replace(a,args=a.args+(('exclude_self_wizard',True),)) if a.op=='double_wizard_shaman_triggers' else a for a in abilities)
        abilities+=(Ability('triggered',event='spell_cast',op='pump_self',condition='controller_cast_noncreature',
                            args=(('power',1),('toughness',1),('duration','end_turn'))),)
    elif name=='Storm-Kiln Artist':
        abilities+=(Ability('static',op='power_per_controlled_type',args=(('type','artifact'),('per',1))),)
    elif name=='Baral, Chief of Compliance':
        abilities+=(Ability('triggered',event='spell_countered_by',op='optional_loot',condition='controller_countered_spell'),)
    elif name=='Archmage Emeritus':
        abilities+=tuple(replace(a,event='spell_copied') for a in abilities if a.event=='spell_cast' and a.op=='draw')
    elif name=='Stormsplitter':
        abilities=tuple(replace(a,op='copy_source_until_end',args=()) if a.op=='create_token' else a for a in abilities)
        return replace(original,subtypes=frozenset({'Otter','Wizard'}),abilities=abilities)
    return replace(original,abilities=abilities)


def install(table):
    table.upgraded_definitions={}
    for name in UPGRADED:
        upgraded=definition(BY_NAME[name]);table.upgraded_definitions[name]=upgraded
        for obj in table.rules.objects.values():
            if obj.card.name==name:obj.card=replace(upgraded,card_id=obj.card.card_id)
    table.rules._dirty()
