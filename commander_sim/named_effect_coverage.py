"""Exact named-operation inventory across all six pinned Commander lists.

A registration is evidence of a reviewed *suboperation*, not of full-card
support. The report distinguishes named registrations from unreviewed cards
without granting any Oracle-text heuristics executable permission.
"""
import argparse
from collections import defaultdict
import json

from .deck_fixtures import FIXTURES
from .reviewed_rocks import ROCKS
from .reviewed_tutors import TUTORS
from .reviewed_token_spells import TOKEN_SPELLS
from .bounded_trigger_effects import REVIEWED_CAST_TRIGGERS
from .reviewed_death_effects import DEATH_RULES
from .reviewed_sacrifice_actions import SACRIFICE_MODES
from .reviewed_phase_effects import PHASE_RULES
from .reviewed_unearth import UNEARTH
from .reviewed_flashback import FLASHBACK
from .reviewed_enter_effects import ENTER_RULES


def _named_sources():
    catalog=defaultdict(list)
    for kind,source in (
        ("mana",ROCKS),
        ("search",TUTORS),
        ("fixed_token_spell",TOKEN_SPELLS),
        ("cast_trigger",REVIEWED_CAST_TRIGGERS),
        ("death_trigger",DEATH_RULES),
        ("sacrifice_activation",SACRIFICE_MODES),
        ("phase_trigger",PHASE_RULES),
        ("unearth",UNEARTH),
        ("flashback",FLASHBACK),
        ("enter_trigger",ENTER_RULES),
    ):
        for name,row in source.items():
            if kind in {"mana","search"}:
                oracle_id=row["review"].oracle_id
            elif kind=="cast_trigger":
                for spec in row:
                    catalog[name].append((kind,spec.card.oracle_id))
                continue
            elif isinstance(row,tuple):
                for item in row:
                    catalog[name].append((kind,item.oracle_id))
                continue
            else:
                oracle_id=row.oracle_id
            catalog[name].append((kind,oracle_id))
    return {key:tuple(values) for key,values in catalog.items()}


REGISTRATIONS=_named_sources()


def named_effect_coverage(fixtures=FIXTURES):
    """Separate actual pinned source registry coverage from heuristic signals."""
    requested=defaultdict(set)
    by_deck={}
    all_oracles={}
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
    by_operation={}
    for oracle,kinds in requested.items():
        for kind in kinds:
            by_operation[kind]=by_operation.get(kind,0)+1
    return {
        "deck_count":len(by_deck),
        "deck_card_entries":sum(row["named_cards"] for row in by_deck.values()),
        "distinct_oracle_cards":len(all_oracles),
        "with_reviewed_suboperations":sum(bool(ops) for ops in requested.values()),
        "without_registered_suboperations":len(remaining),
        "full_card_coverage_confirmed":0,
        "reviewed_unique_cards_by_operation":dict(sorted(by_operation.items())),
        "unregistered_names":sorted(remaining),
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
