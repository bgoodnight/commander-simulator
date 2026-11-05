"""Fail-closed, version-pinned eligibility for *current* Gorge statistics.

Archive is an immutable input classification, not a destructive R2 operation.
Default: unknown and legacy game rows are historical/ineligible. Verification
of game mechanics remains a separate certification process.
"""
from __future__ import annotations

import hashlib
import json

SCHEMA = "gorge-analytics-cohort-registry-v1"
IDENTITY_FIELDS = (
    "engine_commit", "rules_patch_sha256", "card_corpus_sha256",
    "player_deck_sha256", "pilot_version", "opponent_panel_sha256",
    "oracle_bulk_sha256", "simulation_protocol_sha256",
)
ALLOWED_STATUSES = frozenset(("current", "experimental", "archived"))


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def validate_registry(registry):
    if not isinstance(registry, dict) or registry.get("schema") != SCHEMA:
        raise ValueError("Unrecognized cohort registry")
    cohorts = registry.get("cohorts")
    if not isinstance(cohorts, list):
        raise ValueError("Missing cohort registry")
    names = set()
    for cohort in cohorts:
        if not isinstance(cohort, dict):
            raise ValueError("Malformed cohort")
        cid = cohort.get("cohort_id")
        if not isinstance(cid, str) or not cid or cid in names:
            raise ValueError("Duplicate or invalid cohort identifier")
        names.add(cid)
        if cohort.get("status") not in ALLOWED_STATUSES:
            raise ValueError("Invalid cohort status")
        if cohort["status"] == "current" and cohort.get("approved") is not True:
            raise ValueError("Current cohort must be explicitly approved")
        if cohort.get("approved") is True and cohort["status"] != "current":
            raise ValueError("Only current cohorts can be approved")
        if cohort["status"] == "current":
            if any(not isinstance(cohort.get(k), str) or not cohort[k] for k in IDENTITY_FIELDS):
                raise ValueError("Current cohort lacks version fingerprint")
            if not isinstance(cohort.get("approval_ref"), str) or not cohort["approval_ref"]:
                raise ValueError("Missing approval audit reference")
    return {c["cohort_id"]: c for c in cohorts}


def inspect(row, registry):
    """Returns (eligible, reason); never infers provenance from seed or date."""
    by_id = validate_registry(registry)
    if not isinstance(row, dict):
        return False, "malformed_record"
    cid = row.get("cohort_id")
    if not isinstance(cid, str) or cid not in by_id:
        return False, "unknown_or_legacy_cohort"
    cohort = by_id[cid]
    if cohort["status"] != "current" or cohort.get("approved") is not True:
        return False, cohort["status"]
    if any(row.get(k) != cohort[k] for k in IDENTITY_FIELDS):
        return False, "version_mismatch"
    if row.get("cohort_manifest_sha256") != _digest({
        "cohort_id": cid,
        **{k: cohort[k] for k in IDENTITY_FIELDS},
    }):
        return False, "cohort_fingerprint_mismatch"
    if row.get("finished") is not True or row.get("replay_verified") is not True or row.get("error"):
        return False, "unverified_game"
    if not isinstance(row.get("source_sha256"), str) or len(row["source_sha256"]) != 64:
        return False, "missing_source_digest"
    return True, "approved"


def eligible_partition(rows, registry):
    """No unapproved games can reach statistical denominators."""
    validate_registry(registry)
    if not isinstance(rows, list):
        raise ValueError("Expected game records")
    current, excluded = [], []
    seen = set()
    for row in rows:
        approved, reason = inspect(row, registry)
        if approved:
            gid = row.get("game_id")
            if not isinstance(gid, str) or not gid or gid in seen:
                raise ValueError("Approved game IDs must be distinct and nonempty")
            seen.add(gid)
            current.append(row)
        else:
            excluded.append({"game_id": row.get("game_id") if isinstance(row, dict) else None,
                             "cohort_id": row.get("cohort_id") if isinstance(row, dict) else None,
                             "reason": reason})
    return current, excluded


def fingerprint(cohort):
    return _digest({"cohort_id": cohort["cohort_id"],
                    **{k: cohort[k] for k in IDENTITY_FIELDS}})
