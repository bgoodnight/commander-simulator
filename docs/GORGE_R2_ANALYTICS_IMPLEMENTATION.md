# R2 Gorge analytics workflow — extraction v0.2

## Purpose
This analysis-only branch reads a **specific private batch** from the existing
Cloudflare R2 bucket and computes auditable time-indexed features. The pipeline
does not trigger simulations, change rules/pilots, grant cohort approval, write
to R2, or publish to Pages.

## Components
- `tools/gorge_r2_native_ingest.py`: bounded `warehouse/v1/<batch>/[<hero>]`
  acquisition with original shard `manifest.json` SHA-256 and byte-size
  verification; optional matching `native/v1` tar.gz archives, extracted
  with path and tar-member safety checks. AWS credentials stay in runner
  environment.
- `tools/gorge_hero_ebm_prototype.py`: one game row per hero with decisive
  outcome status and basic first-decision hand features. Never use status,
  seed, number of events, or game duration as model predictors.
- `tools/gorge_landmark_features.py`: source-backed snapshots **at exact
  global turns 4/8/12**, including hero life, hand, battlefield, graveyard,
  number of basic lands on battlefield, and token count. Null when the exact
  snapshot does not exist. Source event seq and snapshot index accompany
  every observed row.
- `tools/gorge_assemble_model_table.py`: joins those rows for exploratory
  feature inspection, explicitly marking all landmark model rows as
  **not approved** until terminal-time risk set and cohort certification exist.
- `tools/gorge_model_readiness.py`: sample/outcome/feature coverage audit.
- `.github/workflows/gorge-hero-ebm-prototype.yml`: on-branch repeatable
  regression run against stored real experimental recordings; outputs
  `hero_features.jsonl`, `landmark_features.jsonl`,
  `experimental_model_table.jsonl`, `model-readiness.json`, and EBM
  software smoke output.
- `.github/workflows/gorge-r2-native-feature-extraction.yml`: manually
  entered exact batch + hero, read-only source acquisition, feature artifact.
  **GitHub only exposes workflow_dispatch for a workflow present on the
  default branch.** The workflow is preparation on this isolated branch;
  it must be made dispatchable deliberately after coordination, or be run
  in an authenticated trusted checkout.

## R2 invocation (trusted checkout, credentials already configured)
```bash
export AWS_ACCESS_KEY_ID="... runner-injected secret ..."
export AWS_SECRET_ACCESS_KEY="... runner-injected secret ..."
export AWS_DEFAULT_REGION=auto
python tools/gorge_r2_native_ingest.py --batch-id 123456-1 \
  --hero mortarion_current --account-id "$GORGE_R2_ACCOUNT_ID" \
  --destination local-private-r2
python tools/gorge_landmark_features.py \
  --native-root local-private-r2/native_shards \
  --hero mortarion_current --output private-report/landmarks.jsonl
```
The batch ID is illustrative; choose an actual R2 warehouse run-attempt.
The acquisition requires the historical native archive naming convention
`...-<batch-id>.tar.gz` and a matching complete manifest. If newer runs
use a different archive naming layout, inventory and adapt the key matching
rather than infer a correspondence from dates or seeds. Never expose credentials
or native omniscient traces in public CI artifacts.

## Specific integrity and modeling gaps
1. Native `log.events` event kinds and seat-zero omitempty semantics require
   audited actor/target interpretation **before** emitting cast/mana/damage
   features. Do not count unrecognized events as zero.
2. Basic-land counts are exact for six named basic land faces only, not
   total lands or mana available; nonbasic card types must be joined to an
   Oracle/Forge card-type registry.
3. Terminal states require event-sequenced elimination/game-over timestamps
   to define risk sets for landmark prediction. A snapshot by itself is not
   evidence that a player was still at risk at an arbitrary cutoff.
4. A first pending decision is not guaranteed to be a kept pregame hand.
5. Versioned game IDs must include cohort/run/hero/shard/seed when ingesting
   multiple batches. Current one-batch JSONL prototype keys on seed.
6. Extracted private tables contain hidden hand/library information and should
   remain restricted to trusted offline analytics, not the public Worker API
   or GitHub Pages.
7. Archive completeness depends on `-native-limit` and retry handling in
   the generating workflow; verify expected vs available attempts.
8. Historical or experimental source access does not grant production analytic
   eligibility, even with a valid hash or Gorge replay chain.

## Next implementation sequence
- Inventory the first new R2 batch manifest and native archives.
- Run event contract audits for actor, land played, cast, mana, sacrifice,
  token creation, damage and terminal outcome. Add fixture cases for each.
- Add deck/card Oracle metadata and source-backed event counts to the feature
  dictionary with explicit unknown/zero distinction.
- Build terminal-time landmark eligibility and grouped-seed CV, then compare
  opponent-only baseline, elastic net and EBM on sufficiently large
  **approved** cohorts.
