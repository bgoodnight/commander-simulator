"""Exact named-operation inventory across all six pinned Commander lists.

A registration is evidence of a reviewed *suboperation*, not of full-card
support. The report distinguishes named registrations from unreviewed cards
without granting any Oracle-text heuristics executable permission.
"""
import argparse
from collections import defaultdict
import json

from .deck_fixtures import FIXTURES
from .shared_effect_registry import named_registrations, EFFECT_FAMILIES, effect_registrations


REGISTRATIONS=named_registrations()


def named_effect_coverage(fixtures=FIXTURES):
    """Separate actual pinned source registry coverage from heuristic signals."""
    requested=defaultdict(set)
    by_deck={}
    all_oracles={}
    oracle_types={}
    for fixture in fixtures:
        data=json.loads(fixture.snapshot_path.read_text(encoding="utf-8"))
        if data.get("problems") or not isinstance(data.get("cards"),list):
            raise ValueError("Incomplete snapshot cannot produce named coverage")
        deck={}
        for entry in data["cards"]:
            name=entry["deck_name"]
            row=entry["card"]
            oracle=row.get("oracle_id")
            if not oracle:
                raise ValueError("Missing Oracle ID")
            all_oracles.setdefault(oracle,name)
            # Printed type classification only; no inferred rules support.
            type_line=row.get("type_line","")
            if not type_line and row.get("card_faces"):
                type_line=row["card_faces"][0].get("type_line","")
            type_words=set(type_line.split(" — ",1)[0].lower().split())
            category=next((kind for kind in (
                "creature","instant","sorcery","artifact","enchantment","land")
                if kind in type_words),"other")
            oracle_types.setdefault(oracle,category)
            registered=tuple(sorted({kind for kind,source_id
                in REGISTRATIONS.get(name,()) if source_id==oracle}))
            requested[oracle].update(registered)
            deck[name]={"oracle_id":oracle,
                        "reviewed_suboperations":registered,
                        "status":"partial" if registered else "not_registered"}
        by_deck[fixture.key]={
            "named_cards":len(deck),
            "with_reviewed_suboperations":sum(bool(entry["reviewed_suboperations"])
                                              for entry in deck.values()),
            "without_registered_suboperations":sum(
                not entry["reviewed_suboperations"] for entry in deck.values()),
            "full_card_coverage_confirmed":0,
            "cards":deck,
        }
    remaining={all_oracles[oracle]:oracle for oracle,operations in requested.items()
               if not operations}
    unregistered_by_card_type={}
    for oracle,operations in requested.items():
        if not operations:
            category=oracle_types[oracle]
            unregistered_by_card_type.setdefault(category,[]).append(all_oracles[oracle])
    unregistered_by_card_type={
        kind:{"count":len(names),"names":sorted(names)}
        for kind,names in sorted(unregistered_by_card_type.items())}
    by_operation={}
    for oracle,kinds in requested.items():
        for kind in kinds:
            by_operation[kind]=by_operation.get(kind,0)+1
    # The catalog is shared: describe actual cross-deck registrations, not
    # invented card coverage or inferred text-only capabilities.
    shared_families={}
    for family in EFFECT_FAMILIES:
        oracle_ids={record.oracle_id for record in effect_registrations()
                    if record.family==family}
        in_decks=tuple(sorted(key for key,deck in by_deck.items()
            if any(entry["oracle_id"] in oracle_ids
                   for entry in deck["cards"].values())))
        shared_families[family]={
            "registered_oracle_cards":len(oracle_ids),
            "deck_variants":in_decks,
            "deck_variant_count":len(in_decks),
        }
    return {
        "shared_effect_families":shared_families,
        "shared_effect_family_count":len(shared_families),
        "shared_effect_operation_count":len({
            record.operation for record in effect_registrations()}),
        "deck_count":len(by_deck),
        "deck_card_entries":sum(row["named_cards"] for row in by_deck.values()),
        "distinct_oracle_cards":len(all_oracles),
        "with_reviewed_suboperations":sum(bool(ops) for ops in requested.values()),
        "without_registered_suboperations":len(remaining),
        "full_card_coverage_confirmed":0,
        "reviewed_unique_cards_by_operation":dict(sorted(by_operation.items())),
        "unregistered_names":sorted(remaining),
        "unregistered_by_card_type":unregistered_by_card_type,
        "decks":by_deck,
        "disclaimer":(
            "A registered effect family only proves an explicitly reviewed "
            "suboperation. These manifests do not prove every printed ability, "
            "timing, replacement, priority or multiplayer interaction."),
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary",action="store_true")
    args=parser.parse_args(argv)
    result=named_effect_coverage()
    if args.summary:
        result.pop("decks")
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
