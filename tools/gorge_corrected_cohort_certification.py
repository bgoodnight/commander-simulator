"""Read-only certification gate audit for corrected Gorge experimental batches.

Audits exact original native recordings and exact private R2 UI projection.
Passing integrity checks does NOT approve a cohort or certify Magic gameplay.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from tools.gorge_cohort_eligibility import IDENTITY_FIELDS, validate_registry
from tools.gorge_ui_export import convert

def _sha(data: bytes)->str:
    return hashlib.sha256(data).hexdigest()

def audit(results:Path, projection_file:Path, archive_audit_file:Path,
          registry_file:Path, *, batch:str, deck:str)->dict:
    results=Path(results)
    manifest=json.loads((results/"source-manifest.json").read_text())
    qualification=json.loads((results/"qualification-summary.json").read_text())
    rows=[json.loads(line) for line in (results/"runs.jsonl").read_text().splitlines()
          if line.strip()]
    raw_projection=Path(projection_file).read_bytes()
    projection=json.loads(raw_projection)
    archive_audit=json.loads(Path(archive_audit_file).read_text())
    registry=json.loads(Path(registry_file).read_text())
    validate_registry(registry)
    if (manifest.get("schema")!="gorge-fresh-corrected-pilot-source-v1"
        or manifest.get("source_run_id")+"-"+str(manifest.get("run_attempt"))!=batch
        or manifest.get("hero_deck")!=deck or manifest.get("approval") is not False
        or len(rows)!=manifest.get("attempts_expected")):
        raise ValueError("Native population/manifest mismatch")
    if (projection.get("schema")!="gorge-r2-original-ui-projection-v1"
        or projection.get("source_batch")!=batch
        or projection.get("deck")!=deck
        or projection.get("shard")!=0
        or len(projection.get("games",[]))!=len(rows)):
        raise ValueError("UI projection population mismatch")
    if (archive_audit.get("schema")!="gorge-r2-private-experimental-ui-archive-v1"
        or archive_audit.get("approval") is not False
        or archive_audit.get("production_eligible") is not False
        or archive_audit.get("source_batch")!=batch
        or archive_audit.get("hero")!=deck
        or archive_audit.get("game_count")!=len(rows)
        or archive_audit.get("ui_projection_sha256")!=_sha(raw_projection)
        or archive_audit.get("source_manifest_sha256")!=_sha(
            (results/"source-manifest.json").read_bytes())):
        raise ValueError("R2 archived UI projection digest/audit mismatch")
    indexed={x["game_id"]:x for x in projection["games"]}
    if len(indexed)!=len(rows):
        raise ValueError("Duplicate projected game IDs")
    seeds=set()
    wins=0
    action_count=0
    for row in rows:
        seed=row.get("seed")
        seat=row.get("hero_seat")
        if (type(seed) is not int or seed in seeds
            or type(seat) is not int or seat not in range(4)
            or row.get("finished") is not True
            or row.get("replay_verified") is not True
            or row.get("draw") is True or row.get("error")
            or type(row.get("winner_seat")) is not int
            or row["winner_seat"] not in range(4)
            or row.get("decks",[None]*4)[seat]!=deck):
            raise ValueError(f"Nondecisive/unverified/invalid pilot game: {seed}")
        seeds.add(seed)
        path=results/"native"/f"gorge-seed-{seed}.json"
        raw=path.read_bytes()
        source=json.loads(raw)
        if (source.get("schema")!="gorge-native-trace-v1"
            or source.get("seed")!=seed
            or source.get("chain")!=row.get("replay_chain")
            or source.get("decks")!=row.get("decks")
            or source.get("hero_seat")!=seat):
            raise ValueError(f"Native source mismatch: {seed}")
        item=indexed.get(f"{batch}/{deck}/0/{seed}")
        if (not item or item.get("chain")!=row["replay_chain"]
            or item.get("source_sha256")!=_sha(raw)
            or item.get("run",{}).get("seed")!=seed):
            raise ValueError(f"Projection-native source mismatch: {seed}")
        run=item["run"]
        winner=(row["winner_seat"]-seat+4)%4
        if (run.get("outcome",{}).get("winner_seat")!=winner
            or run["outcome"].get("status")!=("win" if row["winner_seat"]==seat else "loss")
            or len(run.get("ui_observations",[]))!=run.get("completed_rounds")
            or len(run.get("life_history",[]))!=run.get("completed_rounds",0)+1):
            raise ValueError(f"Projected outcome/turn mismatch: {seed}")
        safe=convert(source,include_hidden=False)
        if safe.get("visibility")!="public_events_only":
            raise ValueError("Public-only conversion failed")
        wins+=int(row["winner_seat"]==seat)
        action_count+=sum(1 for turn in run["ui_observations"]
                          for action in turn.get("actions",[]) if action.get("card"))
    source_fields={k:manifest.get(k) for k in IDENTITY_FIELDS}
    missing=[k for k,v in source_fields.items() if not isinstance(v,str) or not v]
    current=[c for c in registry["cohorts"] if c["status"]=="current" and c["approved"] is True]
    blockers=[
        "Source manifest explicitly designates an unapproved experimental candidate",
        "Private experimental R2 projection is not an approved warehouse shard",
        "No documented gameplay rules/pilot/opponent fidelity certification audit for this run",
    ]
    if missing:
        blockers.append("Missing pinned cohort identity fields: "+", ".join(missing))
    if not current:
        blockers.append("No approved current cohort in registry")
    if any(row.get("cohort_id") is None for row in rows):
        blockers.append("Source runs lack current-cohort fingerprint and signed-off approval provenance")
    return {
        "schema":"gorge-corrected-cohort-certification-audit-v1",
        "batch":batch,"deck":deck,
        "native_recordings_checked":len(rows),
        "projected_games_checked":len(indexed),
        "verified_decisive_games":len(rows),
        "wins":wins,"losses":len(rows)-wins,
        "source_matched_named_actions":action_count,
        "projection_sha256":_sha(raw_projection),
        "source_integrity":"passed",
        "ui_projection_compatibility":"source_checked",
        "cohort_approved":False,
        "certification_status":"blocked",
        "publication_eligible":False,
        "blockers":blockers,
    }
