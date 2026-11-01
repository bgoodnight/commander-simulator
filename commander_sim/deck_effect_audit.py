"""Offline, conservative inventory of repeated effects across pinned Commander decks.

Oracle text is evidence for a *candidate mechanic*, NOT executable source
code. The output records reviewed template/operation status separately from
true full-card runtime fidelity, which is unknown until replay tested.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse
import json
import re

from .deck_fixtures import FIXTURES
from .reviewed_tutors import TUTORS
from .reviewed_rocks import ROCKS
from .live_trigger_bridge import TRIGGER_CARDS


# Broad, intentionally heuristic *discovery* categories, not legality.
# Narrow reviewed registrations establish actual supported suboperations.
MECHANIC_PATTERNS = {
    "mana": r"add \{[WUBRGC]\}|add one mana|add two mana|mana of any color",
    "draw": r"\bdraw (?:a|one|two|three|x|\d+) cards?\b|\bdraw cards\b",
    "tokens": r"\bcreate\b[^\n]{0,130}\btokens?\b",
    "graveyard": r"\bgraveyard\b|\bmill\b|\breanimate\b",
    "sacrifice": r"\bsacrifice\b",
    "cost_reduction": r"costs? \{\d+\} less|costs? less|reduce the cost",
    "copy": r"\bcopy\b",
    "search": r"\bsearch your library\b",
    "damage": r"deals? (?:\d+|x) damage|deal (?:\d+|x) damage",
    "counters": r"\bcounter target\b|\bput (?:a|\d+) [^\n]{0,60} counters?\b",
    "death": r"\bwhenever\b[^\n]{0,95}\b(?:dies|die)\b",
    "exile": r"\bexile\b",
}
_PATTERNS = {name: re.compile(pattern, re.IGNORECASE)
             for name, pattern in MECHANIC_PATTERNS.items()}


@dataclass(frozen=True)
class CardAudit:
    deck: str
    name: str
    oracle_id: str
    candidates: tuple[str, ...]
    verified_operations: tuple[str, ...]
    full_card_status: str = "not_established"


def verified_suboperations(name):
    """Only explicitly reviewed, versioned registration may make this claim.

    Mana rock templates are reviewed, but their mana effects can still be
    simplified or unavailable in a particular runner. Historical search
    resolution is exact only for its supported search suboperation.
    Trigger registrations apply only to the historical Magnus stack.
    """
    out = []
    if name in ROCKS:
        out.append("reviewed_mana_template")
    if name in TUTORS:
        out.append("reviewed_search_template")
    if any(key == "named:" + name for key in TRIGGER_CARDS):
        out.append("historical_live_trigger_slot")
    return tuple(out)


def audit_snapshot(fixture):
    """Return pinned snapshot rows, rejecting incomplete identities."""
    with fixture.snapshot_path.open(encoding="utf-8") as stream:
        snapshot=json.load(stream)
    if snapshot.get("problems") or not isinstance(snapshot.get("cards"), list):
        raise ValueError("Incomplete or malformed pinned deck snapshot")
    seen=set()
    rows=[]
    for item in snapshot["cards"]:
        card=item.get("card") or {}
        name=item.get("deck_name")
        oracle_id=card.get("oracle_id")
        # Scryfall stores Adventure and modal-DFC Oracle text per face.
        # Treat the union of printed face text as a discovery signal only;
        # executable face-specific permissions require separate review.
        oracle_text=card.get("oracle_text")
        if oracle_text is None and isinstance(card.get("card_faces"),list):
            face_texts=[face.get("oracle_text") for face in card["card_faces"]]
            oracle_text="\n".join(face_texts) if face_texts and all(
                isinstance(text,str) for text in face_texts) else None
        if (not isinstance(name,str) or not name
                or not isinstance(oracle_id,str) or not oracle_id
                or not isinstance(oracle_text,str)
                or name in seen):
            raise ValueError("Card lacks reviewed identity, text or unique deck name")
        seen.add(name)
        rows.append(CardAudit(
            fixture.key,name,oracle_id,
            tuple(key for key,pattern in _PATTERNS.items()
                  if pattern.search(oracle_text)),
            verified_suboperations(name)))
    return tuple(rows)


def audit_all(fixtures=FIXTURES):
    """Inventory separate deck occurrences; report overlaps transparently."""
    by_deck={}
    distinct=set()
    mechanics=defaultdict(set)
    signals=Counter()
    registrations=Counter()
    cards_by_deck={}
    for fixture in fixtures:
        rows=audit_snapshot(fixture)
        cards_by_deck[fixture.key]=rows
        by_deck[fixture.key]={
            "unique_printed_cards":len(rows),
            "mechanic_candidates":dict(sorted(Counter(
                key for row in rows for key in row.candidates).items())),
            "reviewed_suboperation_cards":sum(bool(row.verified_operations)
                                              for row in rows),
            "full_card_execution_verified":0,
        }
        for row in rows:
            distinct.add(row.oracle_id)
            for kind in row.candidates:
                mechanics[kind].add(row.oracle_id)
                signals[kind]+=1
            for op in row.verified_operations:
                registrations[op]+=1
    return {
        "disclaimer":("Oracle-pattern hits are audit candidates, not "
                      "implemented behaviors. Full-card execution has not "
                      "been established by this inventory."),
        "deck_count":len(by_deck),
        "deck_card_entries":sum(x["unique_printed_cards"] for x in by_deck.values()),
        "distinct_oracle_ids":len(distinct),
        "candidate_mechanics_by_card_entry":dict(sorted(signals.items())),
        "distinct_cards_by_mechanic":{key:len(value)
                                     for key,value in sorted(mechanics.items())},
        "reviewed_suboperation_registrations_by_deck_entry":dict(
            sorted(registrations.items())),
        "decks":by_deck,
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--details",action="store_true",
                        help="Include each pinned card's candidates/registrations")
    args=parser.parse_args(argv)
    data=audit_all()
    if args.details:
        data["cards"]={fixture.key:[
            dict(name=row.name,oracle_id=row.oracle_id,
                 candidate_mechanics=row.candidates,
                 verified_suboperations=row.verified_operations,
                 full_card_status=row.full_card_status)
            for row in audit_snapshot(fixture)] for fixture in FIXTURES}
    print(json.dumps(data,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
