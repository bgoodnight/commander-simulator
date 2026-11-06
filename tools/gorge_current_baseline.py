"""Promote an audited corrected Gorge source batch to a versioned current baseline.

Never mutate native recordings. Fingerprints are constructed entirely from
pinned source manifest fields and explicitly labelled derived policy digests.
Approval of a cohort is a user decision, not a claim of rules perfection.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from tools.gorge_cohort_eligibility import IDENTITY_FIELDS, fingerprint
from tools.gorge_cohort_provenance import stamp
from tools.gorge_warehouse_export import export

BATCH="42143344243-1"
DECKS=("mortarion_current","magnus_premium")
APPROVAL_REF="github:bgoodnight/commander-simulator/actions/runs/42154033809; user-authorized best-available-current baseline 2026-11-05"

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,
       separators=(",",":"),ensure_ascii=False).encode("utf-8")).hexdigest()

def cohort_for(manifest,deck):
    if (manifest.get("schema")!="gorge-fresh-corrected-pilot-source-v1"
        or manifest.get("hero_deck")!=deck or deck not in DECKS
        or str(manifest.get("source_run_id"))+"-"+str(manifest.get("run_attempt"))!=BATCH
        or manifest.get("approval") is not False):
        raise ValueError("Source is not the exact audited experimental batch")
    for k in ("engine_commit","pilot_patch_sha256","probe_sha256",
              "ward_blight_patch_sha256","card_corpus_sha256",
              "hero_deck_sha256","oracle_bulk_sha256","trial_panel_sha256",
              "opponents_sha256","pilot"):
        if not isinstance(manifest.get(k),str) or not manifest[k]:
            raise ValueError("Missing original recorded provenance: "+k)
    rules=digest({"contract":"derived-composite-corrected-rules-v1",
       "pilot_patch_sha256":manifest["pilot_patch_sha256"],
       "ward_blight_patch_sha256":manifest["ward_blight_patch_sha256"]})
    protocol=digest({"contract":"corrected-probe-opponent-protocol-v1",
       "probe_sha256":manifest["probe_sha256"],
       "opponents_sha256":manifest["opponents_sha256"],
       "trial_panel_sha256":manifest["trial_panel_sha256"]})
    return {
      "cohort_id":"corrected-pilot-current-20261105-"+deck,
      "status":"current","approved":True,
      "approval_ref":APPROVAL_REF,
      "approval_level":"best_available_current_baseline",
      "limitations":"Small source-verified sample, gameplay/pilot fidelity not exhaustively certified; descriptive and exploratory use, no calibrated inference.",
      "source_batch":BATCH,"deck":deck,
      "engine_commit":manifest["engine_commit"],
      "rules_patch_sha256":rules,
      "card_corpus_sha256":manifest["card_corpus_sha256"],
      "player_deck_sha256":manifest["hero_deck_sha256"],
      "pilot_version":manifest["pilot"],
      "opponent_panel_sha256":manifest["trial_panel_sha256"],
      "oracle_bulk_sha256":manifest["oracle_bulk_sha256"],
      "simulation_protocol_sha256":protocol,
      "source_manifest_fingerprint":digest(manifest),
      "rules_digest_definition":"composite: pilot_patch_sha256 + ward_blight_patch_sha256",
      "protocol_digest_definition":"composite: probe_sha256 + opponents_sha256 + trial_panel_sha256",
    }

def registry_match(cohort,registry_path):
    registry=json.loads(Path(registry_path).read_text())
    matches=[x for x in registry.get("cohorts",[]) if x.get("cohort_id")==cohort["cohort_id"]]
    if len(matches)!=1:raise ValueError("Current cohort not uniquely approved in registry")
    actual=matches[0]
    for field in (*IDENTITY_FIELDS,"status","approved","approval_ref",
                  "source_manifest_fingerprint","source_batch","deck"):
        if actual.get(field)!=cohort[field]:
            raise ValueError("Registry/source fingerprint mismatch: "+field)
    return actual

def promote(source,out,deck,registry_path,projection_path):
    source=Path(source)
    manifest=json.loads((source/"source-manifest.json").read_text())
    cohort=cohort_for(manifest,deck)
    registry_match(cohort,registry_path)
    projection=json.loads(Path(projection_path).read_text())
    runs=[json.loads(line) for line in (source/"runs.jsonl").read_text().splitlines() if line.strip()]
    projected=projection.get("games",[])
    if (projection.get("schema")!="gorge-r2-original-ui-projection-v1" or
        projection.get("source_batch")!=BATCH or projection.get("deck")!=deck or
        len(runs)!=12 or len(projected)!=12):
        raise ValueError("Source/UI game population mismatch")
    identities={x["game_id"]:x for x in projected}
    if len(identities)!=len(runs):raise ValueError("Duplicate projection ID")
    for row in runs:
        seed=row["seed"]
        key=f"{BATCH}/{deck}/0/{seed}"
        item=identities.get(key)
        raw=(source/"native"/f"gorge-seed-{seed}.json").read_bytes()
        if not item or item["source_sha256"]!=hashlib.sha256(raw).hexdigest() or item["chain"]!=row["replay_chain"]:
            raise ValueError("Native projection provenance mismatch: "+str(seed))
    stamped=stamp(runs,source/"native",cohort)
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    stamped_file=source/"runs-stamped.jsonl"
    if stamped_file.exists():raise ValueError("Refuse to replace source stamped file")
    # No alteration to existing source directory: mirror native logs and write
    # new stamped records to a separate working tree.
    staging=out/"source"
    (staging/"native").mkdir(parents=True,exist_ok=True)
    import shutil
    for row in runs:
        src=source/"native"/f"gorge-seed-{row['seed']}.json"
        shutil.copyfile(src,staging/"native"/src.name)
    with (staging/"runs-stamped.jsonl").open("w") as f:
        for row in stamped:f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
    folder=out/"warehouse"
    record=export(staging,folder,BATCH,deck,0,"runs-stamped.jsonl")
    # Version-pinned compatible original UI projection is copied unchanged.
    shutil.copyfile(projection_path,folder/"ui-original.v1.json")
    gamecount=record["games"]
    if gamecount!=12:raise ValueError("Incomplete promoted cohort")
    return {"schema":"gorge-current-baseline-promotion-v1",
            "deck":deck,"source_batch":BATCH,"cohort_id":cohort["cohort_id"],
            "cohort_manifest_sha256":fingerprint(cohort),
            "source_manifest_fingerprint":cohort["source_manifest_fingerprint"],
            "games":gamecount,"ui_projection_sha256":hashlib.sha256(
               (folder/"ui-original.v1.json").read_bytes()).hexdigest(),
            "parquet_sha256":record["files"]["games.parquet"]["sha256"],
            "approval_level":"best_available_current_baseline",
            "publication":"not_yet_uploaded"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("fingerprints","promote"))
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--deck",required=True,choices=DECKS)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--registry",type=Path)
    p.add_argument("--projection",type=Path)
    a=p.parse_args()
    cohort=cohort_for(json.loads((a.source/"source-manifest.json").read_text()),a.deck)
    if a.action=="fingerprints":
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(cohort,sort_keys=True,indent=2)+"\n")
        return
    if not a.registry or not a.projection:
        p.error("promote needs --registry and --projection")
    result=promote(a.source,a.out,a.deck,a.registry,a.projection)
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
