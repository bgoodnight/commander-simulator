"""Read-only, source-pinned cross-deck effect-gap inventory.

Candidate families come from printed Oracle text and are NOT executable rules.
A named registration proves only that some reviewed suboperation exists.
A provisional profile proves only that a small, explicitly partial import is
available. Neither certifies a whole card or legal game outcomes.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from commander_sim.deck_fixtures import FIXTURES, EXPERIMENTAL_FIXTURES
from commander_sim.named_effect_coverage import named_effect_coverage
from commander_sim.provisional_import import provisional_profile

FORMAT = "commander-effect-gap-audit-v1"
FAMILY_PATTERNS = {
    "graveyard_recursion": re.compile(
        r"graveyard|unearth|flashback|escape|reanimate", re.I),
    "sacrifice_death": re.compile(
        r"sacrific(?:e|es|ed|ing)|\bdies\b|whenever.*\bdie\b", re.I | re.S),
    "entry_trigger": re.compile(
        r"(?:when|whenever)[^\n.]*\benter(?:s|ed|ing)?\b|fabricate", re.I),
    "token_generation": re.compile(r"\bcreate\b[^\n.]*\btoken", re.I),
    "card_selection": re.compile(
        r"\bdraw\b|\bmill\b|\bscry\b|\bsurveil\b|\bdiscard\b", re.I),
    "removal_interaction": re.compile(
        r"\bdestroy\b|\bexile target\b|\breturn target\b|\bcounter target\b", re.I),
    "mana_cost_alternatives": re.compile(
        r"\bconvoke\b|\baffinity\b|\bdelve\b|\bcosts? \{[0-9X]\} less\b|"
        r"\brather than pay\b|\bwithout paying its mana cost\b", re.I),
    "continuous_modifiers": re.compile(
        r"\bindestructible\b|\bhexproof\b|\bward\b|"
        r"\bget(?:s)? [+-][0-9X]|\bcounters?\b", re.I),
    "combat_attack": re.compile(
        r"\battack(?:s|ing|ed)?\b|\bblocks?\b|\bcombat damage\b", re.I),
    "spell_copy": re.compile(r"\bcopy\b[^\n.]*\bspell|\bcopy target\b", re.I),
}


def candidate_families(oracle_text):
    if not isinstance(oracle_text, str):
        return ()
    return tuple(kind for kind, pattern in FAMILY_PATTERNS.items()
                 if pattern.search(oracle_text))


def audit_effect_gaps(fixtures=None):
    """Inventory all pinned card variants with a strict uncertainty boundary."""
    if fixtures is None:
        fixtures = (*FIXTURES, *EXPERIMENTAL_FIXTURES)
    fixtures = tuple(fixtures)
    named = named_effect_coverage(fixtures=fixtures)
    by_deck = {}
    cross = defaultdict(set)
    aggregate_family = Counter()
    for fixture in fixtures:
        stored = json.loads(fixture.snapshot_path.read_text(encoding="utf-8"))
        reviewed_deck = named["decks"][fixture.key]["cards"]
        counts = Counter()
        families = defaultdict(list)
        for entry in stored["cards"]:
            name = entry["deck_name"]
            raw = entry["card"]
            registrations = reviewed_deck[name]["reviewed_suboperations"]
            provisional = provisional_profile(raw)
            status = ("reviewed_partial" if registrations
                      else "provisional_only" if provisional is not None
                      else "no_registered_recipe")
            counts[status] += 1
            if status != "reviewed_partial":
                cross[(name,raw["oracle_id"],status)].add(fixture.key)
            for kind in candidate_families(raw.get("oracle_text","")):
                if status == "no_registered_recipe":
                    families[kind].append(name)
                    aggregate_family[kind] += 1
        by_deck[fixture.key] = {
            "status_counts": dict(sorted(counts.items())),
            "candidate_families_with_no_registered_recipe": {
                kind: {"card_count":len(names),"card_names":sorted(set(names))}
                for kind,names in sorted(families.items())
            },
        }
    recurring = [
        {"name":name,"oracle_id":oracle_id,"status":status,
         "deck_variants":sorted(deck_keys),"variant_count":len(deck_keys)}
        for (name,oracle_id,status),deck_keys in cross.items()
        if len(deck_keys) >= 2
    ]
    recurring.sort(key=lambda x:(-x["variant_count"],x["name"],x["oracle_id"]))
    return {
        "format": FORMAT,
        "deck_variants":len(fixtures),
        "unique_pinned_oracle_cards":named["distinct_oracle_cards"],
        "by_deck":by_deck,
        "no_recipe_candidate_family_occurrences":
            dict(sorted(aggregate_family.items())),
        "recurring_gaps_across_variants":recurring,
        "disclaimer": (
            "Printed-text matches are candidate families, not permissions or "
            "executable rules. A registered or provisional suboperation is "
            "partial evidence, not whole-card support. Named registrations "
            "may omit generic kernel support, and unregistered cards are not "
            "necessarily unplayable. Opponent policy and priority are incomplete."),
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-only",action="store_true")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args(argv)
    data=audit_effect_gaps(FIXTURES if args.canonical_only else None)
    rendered=json.dumps(data,sort_keys=True,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered,encoding="utf-8")
        print("Wrote",data["deck_variants"],"pinned deck audits to",args.output)
    else:
        print(rendered)


if __name__ == "__main__":
    main()
