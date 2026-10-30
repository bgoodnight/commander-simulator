"""Channel activation cost calculation."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v7_rules'))
from rules import Cost

BASE_COSTS = {
    'Otawara, Soaring City': Cost(generic=3, blue=1),
    'Sokenzan, Crucible of Defiance': Cost(generic=3, red=1),
}

def channel_cost(name, controlled_permanents):
    """Reduce generic mana once for each controlled legendary creature."""
    base = BASE_COSTS[name]
    count = sum('creature' in obj.types and 'legendary' in obj.card.supertypes
                for obj in controlled_permanents)
    return Cost(generic=max(0, base.generic - count), blue=base.blue, red=base.red)
