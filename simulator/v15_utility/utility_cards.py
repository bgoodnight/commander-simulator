"""Utility-land ability descriptors; no effect is inferred from generic land types."""
from dataclasses import dataclass
from rules import Cost

@dataclass(frozen=True)
class UtilitySpec:
    key:str
    cost:Cost
    tap:bool=True
    sacrifice:bool=False
    operation:str='draw'
    amount:int=1
    target_kinds:frozenset[str]=frozenset()

ISLET=UtilitySpec('fiery_islet_draw',Cost(generic=1),sacrifice=True)
RIPTIDE=UtilitySpec('riptide_wizard_bounce',Cost(generic=1,blue=1),operation='bounce_wizard')


def install(table):
    table.register_activation('named:Fiery Islet',ISLET)
    table.register_activation('named:Riptide Laboratory',RIPTIDE)
