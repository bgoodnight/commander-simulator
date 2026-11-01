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
from .reviewed_cost_reduction import REDUCERS
from .reviewed_graveyard_creatures import GRAVEYARD_CREATURES
from .reviewed_nonhand_cast_triggers import NONHAND_CAST_TRIGGERS
from .reviewed_escape import BREACH_REVIEWS
from .reviewed_buyback import BUYBACK
from .reviewed_spell_copy import REVIEWED_COPY_SPELLS


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
        ("cost_reduction",REDUCERS),
        ("graveyard_creature_cast",GRAVEYARD_CREATURES),
        ("nonhand_cast_trigger",NONHAND_CAST_TRIGGERS),
        ("escape_grant",BREACH_REVIEWS),
        ("buyback",BUYBACK),
        ("spell_copy",REVIEWED_COPY_SPELLS),
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
    return {
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
