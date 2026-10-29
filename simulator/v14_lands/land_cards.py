"""Named land metadata; entry predicates and search mechanics contain no names."""
from dataclasses import dataclass,replace
from resources import Cost


@dataclass(frozen=True)
class EntryRule:
    condition:str='always_untapped'
    threshold:int=0
    subtypes:frozenset[str]=frozenset()
    basic:bool=False
    life:int=0
    modal:bool=False


RULES={
    'Island':EntryRule(subtypes=frozenset({'Island'}),basic=True),
    'Mountain':EntryRule(subtypes=frozenset({'Mountain'}),basic=True),
    'Steam Vents':EntryRule('pay_life',subtypes=frozenset({'Island','Mountain'}),life=2),
    'Training Center':EntryRule('opponents',2),
    'Stormcarved Coast':EntryRule('other_lands_min',2),
    'Sulfur Falls':EntryRule('island_or_mountain',1),
    'Spirebluff Canal':EntryRule('other_lands_max',2),
    'Mystic Sanctuary':EntryRule('other_islands',3,subtypes=frozenset({'Island'})),
    'Fabled Passage':EntryRule(),
    'Riverglide Pathway':EntryRule(modal=True),
}


@dataclass(frozen=True)
class FetchSpec:
    key:str='fabled_passage_fetch'
    cost:Cost=Cost()
    tap:bool=True
    sacrifice:bool=True
    operation:str='search_basic_land'
    amount:int=1
    target_kinds:frozenset[str]=frozenset()


FETCH=FetchSpec()


def install(table):
    for obj in table.rules.objects.values():
        if obj.card.card_id.startswith('named:') and obj.card.name in RULES:
            rule=RULES[obj.card.name]
            supertypes=obj.card.supertypes|({'basic'} if rule.basic else set())
            obj.card=replace(obj.card,subtypes=rule.subtypes,supertypes=frozenset(supertypes))
    table.register_activation('named:Fabled Passage',FETCH)
    table.rules._dirty()
