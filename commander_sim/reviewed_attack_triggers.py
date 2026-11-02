"""Source-reviewed declarative on-attack keyword grants.

The generic combat host calls this only after a legal creature is declared
attacking; it does not manufacture attacks or infer abilities from names.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class AttackGrant:
    oracle_id:str
    excerpt:str
    subtype:str
    min_power:int
    token_only:bool
    keyword:str
    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt or
                self.min_power<0 or not self.subtype or not self.keyword):
            raise ValueError("Invalid reviewed attack condition")


RULES={
    "Dreadhorde Invasion":AttackGrant(
        "01deabbb-af6a-4998-99a7-35b7cfa9ef77",
        "Whenever a Zombie token you control with power 6 or greater attacks, it gains lifelink until end of turn.",
        "Zombie",6,True,"lifelink")
}


def resolve_attack_grants(kernel,catalog,attacker_id):
    """Apply end-turn buffs to this physical attacking object once per source."""
    from simulator.v7_rules.rules import Modifier
    attacker=kernel.objects.get(attacker_id)
    if (attacker is None or attacker.zone!="battlefield" or
            "creature" not in attacker.types):
        return ()
    results=[]
    for source in tuple(kernel.on_battlefield()):
        raw=catalog.get(source.card.name)
        rule=RULES.get(source.card.name)
        if (source.controller!=attacker.controller or rule is None
                or source.card.card_id!=rule.oracle_id
                or not isinstance(raw,dict)
                or raw.get("oracle_id")!=rule.oracle_id
                or rule.excerpt not in raw.get("oracle_text","")
                or (rule.token_only and not attacker.token)
                or rule.subtype not in attacker.subtypes
                or attacker.power<rule.min_power):
            continue
        kernel.add_modifier(attacker_id,Modifier(
            keywords=frozenset({rule.keyword}),expires_at="end_turn"))
        results.append((source.object_id,attacker_id,rule.keyword))
    return tuple(results)
