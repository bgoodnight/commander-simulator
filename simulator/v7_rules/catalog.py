"""Proof-of-reuse card descriptions; not Oracle coverage for all 100 cards."""
from rules import Ability,CardDefinition,Cost

SPAWN=CardDefinition('spawn_3_3','Spawn',frozenset({'creature'}),base_power=3,base_toughness=3)
ELEMENTAL=CardDefinition('elemental_1_1','Elemental',frozenset({'creature'}),frozenset({'Elemental'}),base_power=1,base_toughness=1)
SOLDIER=CardDefinition('soldier_1_1','Soldier',frozenset({'artifact','creature'}),frozenset({'Soldier'}),base_power=1,base_toughness=1)
TREASURE=CardDefinition('treasure','Treasure',frozenset({'artifact'}),frozenset({'Treasure'}))

MAGNUS=CardDefinition('magnus_the_red','Magnus the Red',frozenset({'creature'}),
    frozenset({'Demon','Primarch'}),frozenset({'legendary','commander'}),Cost(3,1,1),4,5,
    frozenset({'flying'}),(
    Ability('static',op='reduce_generic_cost',condition='cast_instant_or_sorcery',amount='own_creature_tokens'),
    Ability('triggered',event='combat_damage_player',op='create_token',condition='self_combat_damage_player',args=(('token_id','spawn_3_3'),)),
    ))
PYROMANCER=CardDefinition('young_pyromancer','Young Pyromancer',frozenset({'creature'}),frozenset({'Human','Shaman'}),cost=Cost(1,red=1),base_power=2,base_toughness=1,abilities=(
    Ability('triggered',event='spell_cast',op='create_token',condition='controller_cast_instant_sorcery',args=(('token_id','elemental_1_1'),)),))
ICONOCLAST=CardDefinition('third_path_iconoclast','Third Path Iconoclast',frozenset({'creature'}),frozenset({'Human','Monk'}),cost=Cost(0,1,1),base_power=1,base_toughness=1,abilities=(
    Ability('triggered',event='spell_cast',op='create_token',condition='controller_cast_noncreature',args=(('token_id','soldier_1_1'),)),))
HARMONIC=CardDefinition('harmonic_prodigy','Harmonic Prodigy',frozenset({'creature'}),frozenset({'Human','Wizard'}),cost=Cost(1,red=1),base_power=1,base_toughness=3,abilities=(Ability('static',op='double_wizard_shaman_triggers'),))
STORM_KILN=CardDefinition('storm_kiln_artist','Storm-Kiln Artist',frozenset({'creature'}),frozenset({'Dwarf','Shaman'}),cost=Cost(3,red=1),base_power=2,base_toughness=2,abilities=(
    Ability('triggered',event='spell_cast',op='create_token',condition='controller_cast_instant_sorcery',args=(('token_id','treasure'),)),
    Ability('triggered',event='spell_copied',op='create_token',condition='controller_cast_instant_sorcery',args=(('token_id','treasure'),)),))
GENERIC_DISCOUNT=CardDefinition('generic_discount','Generic Discount Creature',frozenset({'creature'}),
    cost=Cost(1),base_power=1,base_toughness=1,abilities=(Ability('static',op='reduce_generic_cost',condition='cast_instant_or_sorcery',amount='constant',args=(('value',1),)),))

DEFINITIONS={c.card_id:c for c in (SPAWN,ELEMENTAL,SOLDIER,TREASURE,MAGNUS,PYROMANCER,ICONOCLAST,HARMONIC,STORM_KILN,GENERIC_DISCOUNT)}
ARCHMAGE=CardDefinition('archmage_emeritus','Archmage Emeritus',frozenset({'creature'}),frozenset({'Human','Wizard'}),cost=Cost(2,blue=2),base_power=2,base_toughness=2,abilities=(Ability('triggered',event='spell_cast',op='draw',condition='controller_cast_instant_sorcery'),))
STORMSPLITTER=CardDefinition('stormsplitter','Stormsplitter',frozenset({'creature'}),frozenset({'Elemental','Wizard'}),cost=Cost(3,red=1),base_power=1,base_toughness=4,keywords=frozenset({'haste'}),abilities=(Ability('triggered',event='spell_cast',op='create_token',condition='controller_cast_instant_sorcery',args=(('token_id','stormsplitter'),)),))
GOBLIN=CardDefinition('goblin_electromancer','Goblin Electromancer',frozenset({'creature'}),frozenset({'Goblin','Wizard'}),cost=Cost(0,blue=1,red=1),base_power=2,base_toughness=2,abilities=(Ability('static',op='reduce_generic_cost',condition='cast_instant_or_sorcery',amount='constant',args=(('value',1),)),))
BARAL=CardDefinition('baral','Baral, Chief of Compliance',frozenset({'creature'}),frozenset({'Human','Wizard'}),cost=Cost(1,blue=1),base_power=1,base_toughness=3,abilities=(Ability('static',op='reduce_generic_cost',condition='cast_instant_or_sorcery',amount='constant',args=(('value',1),)),))
DEFINITIONS.update({c.card_id:c for c in (ARCHMAGE,STORMSPLITTER,GOBLIN,BARAL)})
BY_NAME={c.name:c for c in DEFINITIONS.values()}
