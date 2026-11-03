"""Declarative as-enters choices stored on the existing physical kernel.

Choice registrations authorize only the choice, not the rest of a card's
abilities. The caller supplies the player decision before dependent events.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class EntryChoice:
    oracle_id: str
    excerpt: str
    operation: str
    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt
                or self.operation!="choose_player"):
            raise ValueError("Unregistered as-enters choice")


CHOICES={
    "Stuffy Doll":EntryChoice(
        "499dceab-1890-49c8-b35d-b059a1dc950f",
        "As this creature enters, choose a player.",
        "choose_player")
}


def reviewed_entry_choice(name,raw):
    rule=CHOICES.get(name)
    return rule if (isinstance(raw,dict)
                    and rule is not None
                    and raw.get("oracle_id")==rule.oracle_id
                    and rule.excerpt in raw.get("oracle_text","")) else None


def set_reviewed_entry_choice(zones,source_id,catalog,*,player):
    """Record chosen player on an existing battlefield object.

    Supports any number of distinct choice-using permanents, without adding
    a second battlefield model. Choices do not follow new object IDs across
    zone changes. This bounded host has no pre-entry replacement window.
    """
    kernel=zones.kernel
    source=kernel.objects.get(source_id)
    if source is None or source.zone!="battlefield":
        raise ValueError("Entry choice source must be on the battlefield")
    rule=reviewed_entry_choice(source.card.name,catalog.get(source.card.name))
    if rule is None or rule.oracle_id!=source.card.card_id:
        raise ValueError("Unreviewed entry choice source")
    if (type(player) is not int or player not in kernel.life_totals
            or kernel.life_totals[player]<=0):
        raise ValueError("Chosen player must still be in the game")
    if not hasattr(kernel,"reviewed_player_choices"):
        kernel.reviewed_player_choices={}
    if source_id in kernel.reviewed_player_choices:
        raise ValueError("Entry choice already made for this permanent")
    kernel.reviewed_player_choices[source_id]=player
    return player
