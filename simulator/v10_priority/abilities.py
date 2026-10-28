"""Explicit nonmana activation descriptors; unknown operations fail closed."""
from dataclasses import dataclass
from resources import Cost

@dataclass(frozen=True)
class ActivatedSpec:
    key: str
    cost: Cost = Cost()
    tap: bool = False
    sacrifice: bool = False
    operation: str = 'draw'
    amount: int = 1
    target_kinds: frozenset[str] = frozenset()

    def __post_init__(self):
        if self.operation not in ('draw', 'counter_stack'):
            raise NotImplementedError('Unregistered activated operation ' + self.operation)
        if self.amount < 1: raise ValueError('Ability amount must be positive')
        if self.operation == 'counter_stack' and not self.target_kinds:
            raise ValueError('Stack counter ability needs explicit target kinds')
        if self.target_kinds - {'spell', 'triggered', 'activated'}:
            raise ValueError('Unsupported stack target kind')

MIND_STONE_DRAW = ActivatedSpec('mind_stone_draw', Cost(generic=1), tap=True, sacrifice=True)
NAMED_ACTIVATIONS = {'named:Mind Stone': (MIND_STONE_DRAW,)}
