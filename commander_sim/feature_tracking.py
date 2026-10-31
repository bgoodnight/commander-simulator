"""Deck Intelligence: metadata-derived features and curated strategy milestones.

Never infer effects, tutors or combos from Oracle text. This is a read-only
reporting layer: actual board states, tutor legality and operational combos
must be supplied by the authoritative engine. A keyword/type match describes
a card, not a synergistic or executable ability.
"""
from collections import Counter


def _check_catalog(catalog):
    if not isinstance(catalog, dict):
        raise ValueError("Expected pinned metadata indexed by exact card name")
    for name, card in catalog.items():
        if not isinstance(name, str) or not isinstance(card, dict):
            raise ValueError("Invalid pinned card metadata")
        if not isinstance(card.get("type_line"), str) or not isinstance(card.get("keywords"), list):
            raise ValueError("Missing verified type or keyword metadata: " + name)


def _profile(profile, catalog):
    if not isinstance(profile, dict) or any(k not in {"key_cards", "groups", "combos"} for k in profile):
        raise ValueError("Invalid strategy profile")
    keys = profile.get("key_cards", [])
    groups = profile.get("groups", [])
    combos = profile.get("combos", [])
    if not all(isinstance(x, list) for x in (keys, groups, combos)):
        raise ValueError("Profile entries must be lists")
    ids = set()
    for entry, kind in [(x, "key") for x in keys] + [(x, "group") for x in groups] + [(x, "combo") for x in combos]:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not entry["id"]:
            raise ValueError("Each strategy definition needs a stable id")
        if entry["id"] in ids:
            raise ValueError("Duplicate strategy id")
        ids.add(entry["id"])
        names = ([entry.get("card")] if kind == "key" else entry.get("cards" if kind == "group" else "pieces"))
        if not isinstance(names, list) or not names or any(not isinstance(n, str) or n not in catalog for n in names):
            raise ValueError("Strategy uses missing or unverified cards")
        if len(set(names)) != len(names):
            raise ValueError("Repeated card in strategy definition")
        if kind == "key" and not isinstance(entry.get("role", ""), str):
            raise ValueError("Invalid strategic role")
    return keys, groups, combos


def printed_features(catalog, quantities, profile=None):
    """List printed keyword/type/subtype counts; curated groups are separate.

    Counts include the entire selected deck, not simulated permanents. Multiple
    printed keyword occurrences do not establish an actual synergy.
    """
    _check_catalog(catalog)
    keys, groups, combos = _profile(profile or {}, catalog)
    counts = {"type": Counter(), "subtype": Counter(), "keyword": Counter()}
    for name, quantity in quantities.items():
        if name not in catalog or type(quantity) is not int or quantity < 0:
            raise ValueError("Invalid exact card identity or quantity")
        card = catalog[name]
        before, sep, after = card["type_line"].partition(" — ")
        # These are labels parsed from verified characteristics, not a rules parser.
        for token in before.replace(" // ", " ").split():
            if token.lower() in {"creature", "artifact", "enchantment", "instant", "sorcery",
                                 "land", "planeswalker", "battle", "kindred", "tribal"}:
                counts["type"][token.lower()] += quantity
        if sep:
            for subtype in after.split():
                counts["subtype"][subtype] += quantity
        for keyword in set(card["keywords"]):
            if not isinstance(keyword, str):
                raise ValueError("Unverified keyword")
            counts["keyword"][keyword] += quantity
    return {
        "source": "verified_printed_metadata",
        "counts": {k: dict(sorted(v.items())) for k, v in counts.items()},
        "curated_groups": {g["id"]: sum(quantities.get(name, 0) for name in g["cards"]) for g in groups},
        "key_cards": [{"id": k["id"], "card": k["card"], "role": k.get("role", "")} for k in keys],
        "combo_definitions": [{"id": c["id"], "pieces": list(c["pieces"])} for c in combos],
        "limitations": "Printed attributes and curated membership only, not playable abilities or synergy effectiveness",
    }


def analyze_game_turns(catalog, profile, states):
    """Read-only analysis of engine-supplied end-of-turn authoritative snapshots.

    Expected state: source='authoritative_game', turn, battlefield, hand,
    graveyard, and optional engine-verified tutor_access/operational_combos.
    State card names are projections of real engine objects, not generated here.
    Operational combo labels require separate explicit rules-engine evidence.
    """
    _check_catalog(catalog)
    keys, groups, combos = _profile(profile, catalog)
    if not isinstance(states, list) or not states:
        raise ValueError("Expected authoritative turn snapshots")
    previous_turn = 0
    output = []
    for state in states:
        if not isinstance(state, dict) or state.get("source") != "authoritative_game":
            raise ValueError("Board analysis requires authoritative game snapshots")
        turn = state.get("turn")
        if type(turn) is not int or turn <= previous_turn:
            raise ValueError("Turns must be strictly increasing")
        previous_turn = turn
        zones = {}
        for zone in ("battlefield", "hand", "graveyard"):
            cards = state.get(zone)
            if not isinstance(cards, list) or any(not isinstance(n, str) or n not in catalog for n in cards):
                raise ValueError("Missing or unverified " + zone + " projection")
            zones[zone] = Counter(cards)
        tutor_access = state.get("verified_tutor_access", [])
        if not isinstance(tutor_access, list) or any(
            not isinstance(x, dict) or x.get("verified") is not True
            or x.get("target") not in catalog or x.get("tutor") not in catalog
            or x.get("destination") not in ("hand", "battlefield")
            for x in tutor_access
        ):
            raise ValueError("Unverified tutor access cannot count as available")
        reachable = {x["target"] for x in tutor_access}
        operational = state.get("engine_verified_combos", [])
        if not isinstance(operational, list) or any(
            not isinstance(x, str) or x not in {c["id"] for c in combos}
            for x in operational
        ):
            raise ValueError("Unrecognized combo verification")
        in_play = zones["battlefield"]
        tracked_keys = []
        for k in keys:
            name = k["card"]
            tracked_keys.append({
                "id": k["id"],
                "card": name,
                "battlefield": in_play[name],
                "hand": zones["hand"][name],
                "graveyard": zones["graveyard"][name],
                "engine_verified_tutor_access": name in reachable,
            })
        combo_results = []
        for combo in combos:
            pieces = combo["pieces"]
            present = [name for name in pieces if in_play[name] > 0]
            accessible = [name for name in pieces if in_play[name] > 0 or zones["hand"][name] > 0 or name in reachable]
            verified = combo["id"] in operational
            combo_results.append({
                "id": combo["id"],
                "pieces_on_battlefield": len(present),
                "pieces_accessible": len(accessible),
                "pieces_required": len(pieces),
                "status": ("engine_verified_operational" if verified else
                           "all_pieces_present_unverified" if len(present) == len(pieces) else
                           "all_pieces_accessible_unverified" if len(accessible) == len(pieces) else
                           "incomplete"),
            })
        output.append({
            "turn": turn,
            "battlefield_count": sum(in_play.values()),
            "groups_on_battlefield": {
                g["id"]: sum(in_play[n] for n in g["cards"]) for g in groups
            },
            "key_cards": tracked_keys,
            "combos": combo_results,
        })
    return {
        "source": "authoritative_game_snapshots",
        "turns": output,
        "limitations": ("Printed features and curated memberships are descriptive only. "
                        "Tutor reachability must come from verified engine actions; "
                        "combo presence is not proof of legal execution or a win."),
    }
