"""Read-only M3 reporting adapter over the one authoritative live kernel.

Use only at an actual turn boundary chosen by the game driver. This module
does not advance time, create cards, infer plays, or implement tutor rules.
"""
from collections import Counter


def project_kernel_turn(zones, seat, turn, catalog, *,
                        verified_tutor_access=(), engine_verified_combos=()):
    """Snapshot real zone IDs into a validated single-seat JSON-friendly view.

    Battlefields are selected by *controller*, so stolen permanents count for
    their current controller. Hidden hand/graveyard are selected by owner via
    the kernel's zone index. Unknown non-token names fail closed. Unknown
    tokens are reported separately; they are not assigned guessed keywords.
    """
    if type(seat) is not int or not 0 <= seat < zones.seats:
        raise ValueError("Invalid seat")
    if type(turn) is not int or turn < 1:
        raise ValueError("Invalid turn number")
    if not isinstance(catalog, dict):
        raise ValueError("Expected pinned name catalog")
    kernel = zones.kernel
    if not hasattr(kernel, "objects") or not hasattr(zones, "ids"):
        raise ValueError("Not an authoritative indexed kernel")
    zone_ids = {
        "battlefield": sorted(
            obj.object_id for obj in kernel.objects.values()
            if obj.zone == "battlefield" and obj.controller == seat
        ),
        "hand": list(zones.ids(seat, "hand")),
        "graveyard": list(zones.ids(seat, "graveyard")),
    }
    result = {}
    objects = {}
    skipped_tokens = []
    for zone, ids in zone_ids.items():
        names = []
        records = []
        for oid in ids:
            obj = kernel.get(oid)
            if obj.zone != zone:
                raise AssertionError("Kernel index zone mismatch")
            if zone != "battlefield" and obj.owner != seat:
                raise AssertionError("Private zone owner mismatch")
            if zone == "battlefield" and obj.controller != seat:
                raise AssertionError("Battlefield controller mismatch")
            name = obj.card.name
            if name not in catalog:
                if obj.token and zone == "battlefield":
                    skipped_tokens.append({"object_id": oid, "name": name})
                    continue
                raise ValueError("Unverified object in kernel projection: " + name)
            names.append(name)
            records.append({"object_id": oid, "name": name, "owner": obj.owner,
                            "controller": obj.controller, "token": bool(obj.token),
                            "tapped": bool(obj.tapped)})
        result[zone] = names
        objects[zone] = records

    # External annotations come only from independently checked game logic.
    # Never construct tutor access from a printed card, role, or generic label.
    access = list(verified_tutor_access)
    if any(not isinstance(row, dict) or row.get("verified") is not True
           or row.get("tutor") not in catalog or row.get("target") not in catalog
           or row.get("destination") not in {"hand", "battlefield"}
           for row in access):
        raise ValueError("Only verified tutor evidence can enter a snapshot")
    combos = list(engine_verified_combos)
    if any(not isinstance(x, str) or not x for x in combos):
        raise ValueError("Invalid operational combo identifier")

    return {
        "source": "authoritative_game",
        "turn": turn,
        "seat": seat,
        "battlefield": result["battlefield"],
        "hand": result["hand"],
        "graveyard": result["graveyard"],
        "object_views": objects,
        "untracked_tokens": skipped_tokens,
        "verified_tutor_access": access,
        "engine_verified_combos": combos,
        "reporting_limits": (
            "Only the selected seat's controlled battlefield and owned private "
            "zones are projected. Uncatalogued tokens have no inferred printed "
            "features. Tutor and combo evidence must be rules-engine verified."
        ),
    }
