"""Typed, Oracle-pinned token-producing sorceries over one physical kernel.

One reusable token creation operation handles distinct token batches, counts,
tapped entry and printed color/type/size. No card-specific handler. Hand-cast
authorization and printed flashback/activated-token permissions are separate.
"""
from dataclasses import dataclass

from .generic_cast import ReviewedCreatureCast, cast_reviewed_spell
from .legacy_common_ops import spawn_repeated_tokens


@dataclass(frozen=True)
class TokenBlueprint:
    token_name: str
    types: frozenset[str]
    subtypes: frozenset[str]
    colors: frozenset[str]
    power: int
    toughness: int
    count: int = 1
    tapped: bool = False
    limitations: tuple[str,...] = ()
    keywords: frozenset[str] = frozenset()

    def __post_init__(self):
        if (not self.token_name or not self.types
                or not isinstance(self.types,frozenset)
                or not isinstance(self.subtypes,frozenset)
                or not isinstance(self.colors,frozenset)
                or not self.colors <= frozenset("WUBRG")
                or type(self.power) is not int or type(self.toughness) is not int
                or type(self.count) is not int or self.count<1
                or type(self.tapped) is not bool
                or not isinstance(self.limitations,tuple)
                or not isinstance(self.keywords,frozenset)
                or any(not isinstance(k,str) or not k for k in self.keywords)):
            raise ValueError("Invalid reviewed token blueprint")


@dataclass(frozen=True)
class TokenSpellReview:
    oracle_id: str
    oracle_text: str
    mana_cost: str
    batches: tuple[TokenBlueprint,...]
    unmodeled_permissions: tuple[str,...] = ()

    def __post_init__(self):
        if (not self.oracle_id or not self.oracle_text or not self.mana_cost
                or not self.batches or not all(isinstance(b,TokenBlueprint)
                                              for b in self.batches)):
            raise ValueError("Incomplete reviewed token-producing spell")


def _creature(name,subtype,colors,power,toughness,count,*,tapped=False):
    return TokenBlueprint(name,frozenset({"creature"}),frozenset({subtype}),
                          frozenset(colors),power,toughness,count,tapped)


TOKEN_SPELLS={
    "Ral's Reinforcements":TokenSpellReview(
        "e7fa2fc2-8542-4069-b75f-5520dd30f74d",
        "Create two 1/1 blue and red Elemental creature tokens.","{1}{R}",
        (_creature("Elemental","Elemental","UR",1,1,2),)),
    "Hard Evidence":TokenSpellReview(
        "0728b195-2dfe-4d73-91ae-e658a97b0b9a",
        'Create a 0/3 blue Crab creature token.\nInvestigate. (Create a Clue token. It\'s an artifact with "{2}, Sacrifice this token: Draw a card.")',
        "{U}",(
            _creature("Crab","Crab","U",0,3,1),
            TokenBlueprint("Clue",frozenset({"artifact"}),frozenset({"Clue"}),
                           frozenset(),0,0,1,False,
                           ("Clue sacrifice-and-draw activation not available",)),
        ),
        ("Clue activated ability unavailable in bounded runner",)),
    "Strike It Rich":TokenSpellReview(
        "c34c17c7-3827-49a2-be25-67f44fdfe150",
        'Create a Treasure token. (It\'s an artifact with "{T}, Sacrifice this token: Add one mana of any color.")\nFlashback {2}{R} (You may cast this card from your graveyard for its flashback cost. Then exile it.)',
        "{R}",(
            TokenBlueprint("Treasure",frozenset({"artifact"}),frozenset({"Treasure"}),
                           frozenset(),0,0,1,False,
                           ("Treasure tap/sacrifice mana activation unavailable",)),
        ),
        ("Flashback casting unavailable","Treasure activation unavailable")),
    "Moan of the Unhallowed":TokenSpellReview(
        "ce87e5ed-2562-4563-9a5b-bd53c04ec4a5",
        "Create two 2/2 black Zombie creature tokens.\nFlashback {5}{B}{B} (You may cast this card from your graveyard for its flashback cost. Then exile it.)",
        "{2}{B}{B}",(_creature("Zombie","Zombie","B",2,2,2),),
        ("Flashback casting unavailable",)),
    "Army of the Damned":TokenSpellReview(
        "75d667ec-86f4-4850-a3b6-e7a9fc7053b0",
        "Create thirteen tapped 2/2 black Zombie creature tokens.\nFlashback {7}{B}{B}{B} (You may cast this card from your graveyard for its flashback cost. Then exile it.)",
        "{5}{B}{B}{B}",
        (_creature("Zombie","Zombie","B",2,2,13,tapped=True),),
        ("Flashback casting unavailable",)),
}


def reviewed_token_spell(name, card):
    row=TOKEN_SPELLS.get(name)
    if (row is None or card.get("layout")!="normal"
            or card.get("oracle_id")!=row.oracle_id
            or card.get("oracle_text")!=row.oracle_text
            or card.get("mana_cost")!=row.mana_cost
            or card.get("type_line","").split(" — ",1)[0]!="Sorcery"):
        return None
    return row


def create_reviewed_token_batches(zones, seat, batches):
    """Shared reviewed token emitter for sorceries and triggered permanents.

    All token characteristics are parameters; no card-name-specific code.
    The existing kernel owns the resulting permanent IDs and zones.
    """
    if type(seat) is not int or not 0<=seat<zones.seats:
        raise ValueError("Invalid seat")
    if (not isinstance(batches,tuple) or
            not all(isinstance(batch,TokenBlueprint) for batch in batches)):
        raise TypeError("Expected immutable reviewed token batches")
    from .early_game_runner import _load_live_kernel
    _,_,CardDefinition=_load_live_kernel()
    tokens=[]
    for batch in batches:
        definition=CardDefinition(
            "reviewed-token:"+batch.token_name,batch.token_name,batch.types,
            subtypes=batch.subtypes,base_power=batch.power,
            base_toughness=batch.toughness,colors=batch.colors,
            keywords=batch.keywords,
            coverage="unimplemented" if batch.limitations else "approx")
        def add():
            oid=zones.add(definition,seat,"battlefield",token=True)
            # Physical token creation is an observable event, irrespective
            # of which reviewed card produced the token. Consumers own their
            # cursors; there is no permanent/global event queue.
            if not hasattr(zones.kernel, "reviewed_token_events"):
                zones.kernel.reviewed_token_events=[]
            zones.kernel.reviewed_token_events.append((seat,oid))
            if batch.tapped:
                zones.kernel.get(oid).tapped=True
                zones.kernel._dirty()
            return oid
        tokens.extend(spawn_repeated_tokens(add,batch.count))
    return tuple(tokens)


def create_reviewed_tokens(zones, seat, review):
    """Resolve registered spell token batches via the generic emitter."""
    if not isinstance(review,TokenSpellReview):
        raise TypeError("Expected pinned reviewed token spell")
    return create_reviewed_token_batches(zones,seat,review.batches)

@dataclass(frozen=True)
class TokenSpellOutcome:
    source_name: str
    source_stack_id: int
    source_graveyard_id: int
    token_ids: tuple[int,...]
    paid_source_ids: tuple[int,...]
    limitations: tuple[str,...]


def cast_and_resolve_reviewed_token_spell(zones, seat, source_id, catalog,
                                          commander_colors, mana_service, *,
                                          on_cast=None):
    """Hand-cast a reviewed token sorcery and resolve verified token batches.

    The outer turn driver owns timing; not a permission to cast from graveyard.
    """
    if source_id not in zones.ids(seat,"hand"):
        raise ValueError("Sorcery must be in actor hand")
    obj=zones.kernel.get(source_id)
    card=catalog.get(obj.card.name)
    if card is None or card.get("oracle_id")!=obj.card.card_id:
        raise ValueError("Unreviewed printed source")
    review=reviewed_token_spell(obj.card.name,card)
    if review is None or obj.card.types!=frozenset({"sorcery"}):
        raise ValueError("Token sorcery identity or text not reviewed")
    if mana_service is None or mana_service.kernel is not zones.kernel:
        raise ValueError("Physical mana service is required")
    if on_cast is not None and not callable(on_cast):
        raise TypeError("Reviewed cast-event hook must be callable")
    permitted=ReviewedCreatureCast(review.oracle_id,review.mana_cost,True,
                                   review.unmodeled_permissions)
    committed=cast_reviewed_spell(
        zones,seat,source_id,permitted,commander_colors,
        mana_service=mana_service,spell_type="sorcery")
    if committed is None:
        return None
    if on_cast is not None:
        on_cast(committed.ticket)
    created=[]
    def resolve(kernel,ticket):
        created.extend(create_reviewed_tokens(zones,seat,review))
    moved=zones.resolve(committed.ticket,effect=resolve)
    return TokenSpellOutcome(obj.card.name,committed.ticket.object_id,
                             moved,tuple(created),committed.paid_source_ids,
                             review.unmodeled_permissions)
