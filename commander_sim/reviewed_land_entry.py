"""Physical land entry effects composed from shared zone/life operations.

All source admission uses exact pinned Oracle IDs and excerpts. The host
chooses target players/cards; no new zones, cards, or graveyard content are
invented. Mandatory ETB actions execute even when they affect empty zones.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class LandEntry:
    oracle_id: str
    excerpt: str
    operation: str
    optional: bool = False
    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt or
                self.operation not in {"exile_target_graveyard",
                                       "graveyard_creature_to_library_top",
                                       "gain_one_life"}):
            raise ValueError("Unregistered land entry operation")

RULES={
    "Bojuka Bog":LandEntry(
        "04b7362d-0490-4cb0-b5d7-2a7732f659ce",
        "When this land enters, exile target player's graveyard.",
        "exile_target_graveyard"),
    "Mortuary Mire":LandEntry(
        "1b3fb20a-e090-4286-9c03-6b71c27c45be",
        "When this land enters, you may put target creature card from your graveyard on top of your library.",
        "graveyard_creature_to_library_top",True),
    "Swiftwater Cliffs":LandEntry(
        "2f4ad084-2062-44c0-9975-15f100204531",
        "When this land enters, you gain 1 life.",
        "gain_one_life"),
}


def reviewed_land_entry(name,raw):
    rule=RULES.get(name)
    if (rule is None or not isinstance(raw,dict)
            or raw.get("oracle_id")!=rule.oracle_id
            or rule.excerpt not in raw.get("oracle_text","")):
        return None
    return rule


@dataclass(frozen=True)
class LandEntryResult:
    source_id: int
    operation: str
    moved_ids: tuple[int,...] = ()
    target_seat: int | None = None


def resolve_land_entry(zones, life, source_id, catalog, *,
                       target_seat=None, target_creature_id=None):
    kernel=zones.kernel
    if life.kernel is not kernel:
        raise ValueError("Land entry requires matching physical life/kernel")
    obj=kernel.get(source_id)
    raw=catalog.get(obj.card.name)
    rule=reviewed_land_entry(obj.card.name,raw)
    if (rule is None or obj.card.card_id!=rule.oracle_id
            or obj.zone!="battlefield" or "land" not in obj.types):
        raise ValueError("Unreviewed land entry source")
    seat=obj.controller
    moved=[]
    if rule.operation=="exile_target_graveyard":
        if target_seat is None:
            target_seat=next(s for s in sorted(life.kernel.life_totals) if s!=seat)
        if target_seat not in life.kernel.life_totals:
            raise ValueError("Target player is not in the game")
        for oid in tuple(zones.ids(target_seat,"graveyard")):
            moved.append(zones.move(oid,"exile","exile"))
    elif rule.operation=="graveyard_creature_to_library_top":
        if target_creature_id is not None:
            if target_creature_id not in zones.ids(seat,"graveyard"):
                raise ValueError("Target not in controller graveyard")
            card=kernel.get(target_creature_id)
            if "creature" not in card.types:
                raise ValueError("Mortuary Mire requires creature card")
            moved.append(zones.move(target_creature_id,"library","resolve"))
    elif rule.operation=="gain_one_life":
        life.gain(seat,1,source_id)
    return LandEntryResult(source_id,rule.operation,tuple(moved),target_seat)
