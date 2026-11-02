"""Source-pinned reusable replacement effects for physical life changes.

Registration replaces proposed changes before the authoritative life ledger
commits them. A replacement is not a trigger and does not create a second
life change or a fake life-gained event.
"""
from dataclasses import dataclass,replace


@dataclass(frozen=True)
class LifeReplacementRule:
    oracle_id: str
    excerpt: str
    condition: str
    effect: str
    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt
                or self.condition!="opponent_would_gain_life"
                or self.effect!="lose_that_much_instead"):
            raise ValueError("Unsupported life replacement configuration")


RULES={
    "Plague Drone":LifeReplacementRule(
        "9e859925-6a08-4ec2-8dd5-d461ea333dae",
        "If an opponent would gain life, that player loses that much life instead.",
        "opponent_would_gain_life","lose_that_much_instead"),
}


class ReviewedLifeReplacements:
    """Applies only matching, currently-present physical source effects."""

    def __init__(self,kernel,catalog):
        if not isinstance(catalog,dict):
            raise TypeError("Pinned catalog required")
        self.kernel=kernel
        self.catalog=catalog

    def transform(self,change):
        if change.kind!="gain" or change.amount==0:
            return change
        from .kernel_life import LifeChange
        for source in sorted(self.kernel.on_battlefield(),
                             key=lambda o:o.object_id):
            raw=self.catalog.get(source.card.name)
            rule=RULES.get(source.card.name)
            if (rule is None or source.controller==change.seat
                    or not isinstance(raw,dict)
                    or raw.get("oracle_id")!=source.card.card_id
                    or raw.get("oracle_id")!=rule.oracle_id
                    or rule.excerpt not in raw.get("oracle_text","")):
                continue
            # Preserve the origin of attempted gain for auditing; annotate
            # the actual life ledger as loss rather than triggering gain.
            return LifeChange(change.seat,change.amount,"loss",
                              change.source_id)
        return change
