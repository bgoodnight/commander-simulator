"""Authoritative kernel-attached life totals for bounded multi-seat effect slices.

Life belongs to the *existing kernel*, not a parallel simulation. This module
does not provide priority, damage prevention, replacement effects, multiplayer
turn sequencing, commander damage or player elimination. It exposes distinct
life-loss, life-gain, and damage interfaces so callers cannot silently equate
damage with life loss; damage needs a reviewed host for prevention/triggers.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class LifeChange:
    seat: int
    amount: int
    kind: str
    source_id: int | None = None

    def __post_init__(self):
        if (type(self.seat) is not int or self.seat < 0
                or type(self.amount) is not int or self.amount < 0
                or self.kind not in {"gain","loss","damage"}):
            raise ValueError("Invalid kernel life change")


class KernelLife:
    def __init__(self, kernel, seats=4, starting_life=40):
        if (type(seats) is not int or not 1<=seats<=4
                or type(starting_life) is not int or starting_life<=0):
            raise ValueError("Invalid starting life state")
        self.kernel=kernel
        if not hasattr(kernel,"life_totals"):
            kernel.life_totals={seat:starting_life for seat in range(seats)}
        if (set(kernel.life_totals)!=set(range(seats))
                or any(type(value) is not int for value in kernel.life_totals.values())):
            raise ValueError("Kernel already holds incompatible life totals")
        if not hasattr(kernel,"life_changes"):
            kernel.life_changes=[]

    def total(self,seat):
        if type(seat) is not int or seat not in self.kernel.life_totals:
            raise ValueError("Unknown life seat")
        return self.kernel.life_totals[seat]

    def apply(self,change: LifeChange):
        if not isinstance(change,LifeChange):
            raise TypeError("Expected typed reviewed life change")
        before=self.total(change.seat)
        self.kernel.life_totals[change.seat]=(
            before+change.amount if change.kind=="gain" else before-change.amount)
        self.kernel.life_changes.append(change)
        self.kernel._dirty()
        return self.kernel.life_totals[change.seat]

    def gain(self,seat,amount,source_id=None):
        return self.apply(LifeChange(seat,amount,"gain",source_id))

    def lose(self,seat,amount,source_id=None):
        return self.apply(LifeChange(seat,amount,"loss",source_id))

    def damage(self,seat,amount,source_id=None):
        """Record unprevented player damage as damage, distinct from costs.

        This bounded operation requires an external host to establish that
        prevention, replacement, protection and player elimination do not
        change the result. It is not a full damage prevention engine.
        """
        return self.apply(LifeChange(seat,amount,"damage",source_id))

    def each_opponent_loses(self,controller,amount,source_id=None):
        self.total(controller)
        if type(amount) is not int or amount<0:
            raise ValueError("Invalid reviewed opponent loss")
        return tuple((seat,self.lose(seat,amount,source_id))
                     for seat in sorted(self.kernel.life_totals)
                     if seat!=controller)
