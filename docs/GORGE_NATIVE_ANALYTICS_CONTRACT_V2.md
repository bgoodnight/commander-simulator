# Gorge full-native analytics contract — exploratory v0.1 (2026-11-05)

Status: design and source-schema audit. Not a claim that private R2 was read. No gameplay modifications, UI changes or production cohort approval.

## Authoritative source inspection
- `tools/gorge_commander_probe.go` defines `Result`, per-turn `snapshot`, `objectCrosswalk`, and native capture.
- `tools/gorge_warehouse_export.py` validates finished/replay-verified source records and writes zstd Parquet `games.parquet` and `events.parquet`.
- `docs/gorge-warehouse-v1.md` defines native archive `native/v1` and analytical `warehouse/v1` prefixes.
- `docs/GORGE_PRELIMINARY_DATA_FEASIBILITY_20261105.md` records 3 inspected public UI replays, NOT full private R2.
- Cohort isolation / approval lives in pending integration changes; never imply verification means current approval.

## Exact native facts and critical limitations
1. `runs.jsonl`: seed, four decks, hero seat, finish/draw/winner, stall, errors, turns, intents/events, pilot strings, replay verification and chain. A failed/unfinished game still needs preservation in the attempted-game registry.
2. `gorge-seed-{seed}.json` native JSON: `log` of events and intents, per-turn snapshots, terminal object crosswalk. `log.events` has monotonically increasing integer seq/kind, with additional kind-specific fields.
3. Snapshot boundary is **first pending decision of each global turn**, not end-of-turn, not hero-turn, and not necessarily a full decision-time state. Each seat snapshot has life, lost, six-color mana pool and object IDs in hand/battlefield/library/graveyard/exile/command.
4. `objects[]` identifies one-game-scoped object ID, printed/effective name, owner, controller **at end**, token/copy flags, types **at end**. End-state controller/types do not automatically establish controller/type at event time.
5. `-native-limit` defaults to **2** and is constrained 0..100; traces are captured only for those initial eligible attempts (or verified games with `-retry-unverified`). `-retry-unverified` skips rejected attempts from stdout and skips native output for unverified attempts. The code must be changed/configured deliberately to preserve **every attempted game**, including capped/error attempts, for a large full-fidelity population. Setting `-native-limit 100` is sufficient only when the relevant shard has <=100 attempts and failures are not skipped.
6. The existing v1 Parquet exporter **requires finished and replay_verified** and only extracts native `log.events`; it does not extract `log.intents`, object crosswalk, or snapshots into queryable normalized tables. Native tarball is therefore essential.
7. A zero-valued seat or other Go `omitempty` field can be missing in serialized events. Treat omitted actor as **unknown until event-kind contract proves its meaning**, never globally coerce to seat 0.
8. Exact raw event JSON is preserved. Decoding event kinds, cost sources, actions or ability semantics requires per-kind audited definitions and source-event examples.
9. The public UI replay is a reduced derivative and **not an authoritative substitute** for full native event/intent history.

## Proposed private R2 logical warehouse v2
Partition immutable source by `cohort_id / run_id / attempt / hero_deck / shard`; use version/manifest fingerprints, not storage path alone, for approval. Preserve old `native/v1` and `warehouse/v1` unchanged.

**Source tables** (Parquet with zstd; nullable values never silently imputed):
- `attempts` (one row **per attempted game**, even failed): `attempt_id`, `game_id` nullable, cohort ID, run ID, seed, attempt index, hero deck, four deck IDs/hashes, seats, pilots, version fingerprints, requested turn cap, turns, terminal status {decisive_win,decisive_loss,draw,turn_cap,error,replay_mismatch,unknown}, winner seat, finished, verified, error/stall, source object key and source SHA.
- `events`: `game_id,seq,kind_id,event_json,actor_seat_nullable,object_id_nullable,secret_flag` (one native event per row), unique `game_id,seq`.
- `intents`: `game_id,intent_index,intent_json` preserving **raw** decision response and metadata. A recorded intent is not necessarily the full legal option set.
- `objects`: `game_id,object_id,printed_name,effective_name,owner_seat,controller_at_end,is_token,is_copy,types_at_end`.
- `snapshots`: `game_id,global_turn,active_seat,step,after_event_seq,boundary,snapshot_index`.
- `snapshot_players`: `game_id,snapshot_index,seat,life,lost,mana_pool_json`.
- `snapshot_zones`: `game_id,snapshot_index,seat,zone,ordinal,object_id`. Preserve ordered library/hand, including privileged hidden information.
- `decks`: pinned deck key, decklist hash, commander, color identity, Oracle data hash and reviewed archetype annotations.
- `cohorts`: exact engine/rules/corpus/Oracle/pilot/deck/panel/protocol fingerprints, immutable manifest hash, approval status and reference.
**Derived analytics tables** (separate materialization, recomputable):
- `feature_dictionary`: feature ID, display label, family, type, definition, observation cutoff, availability/fidelity, minimum evidence and extractor version.
- `game_features`: one row/game/hero/landmark/extractor version for outcome and pre-landmark aggregates; alternatively sparse long form `game_feature_values(game_id,seat,landmark,feature_id,value,observed,evidence_count)`.
- `card_exposures`: game/hero/object/card, accessible_at, drawn_at, cast_at, leaves_hand_at, hand exposure duration, confidence and evidence sequence.
- `event_evidence`: derived feature key to exact native `game_id,seq` or `snapshot_index` supporting replay/audit.
- `model_runs`: input cohort hashes, eligibility policy version, data/extractor version, feature schema SHA, algorithm/config, grouped split seeds, metrics and coefficients.

Stable joining: `attempt_id` unique by run/attempt; `game_id` unique by immutable cohort/run/hero/shard/seed, not bare seed; `object_id` scoped to game. Never join across cohorts on seed alone.

## Feature inventory and availability
Legend **E** = source-backed exact when indicated events are checked; **C** = requires reconstruction and validation; **U** = not guaranteed from currently logged sources.

| Family | Proposed variables | Availability and validation |
|---|---|---|
| Outcome/eligibility | win, loss, draw, terminal status, winner, finish turn, seat | E from runs, verified source and approval registry; track all attempts |
| Opponent context | identities, color combinations, reviewed strategy labels, seat order | E identities; C externally enriched metadata |
| Opening hand | card indicators, land count, mana curve | E from earliest valid snapshot if before first draw/action; C confirm temporal boundary and mulligans |
| Card casting | first cast/number of casts, cast from hand/command, commander timing | C event kind + actor/object crosswalk + global vs hero turns; event ID support |
| Card access | drawn, in hand at global landmark, held duration | E for sampled zone states; C for exact intervals via moves; do not infer unseen intervals |
| Mana | land drops, mana added, rocks present, cost reducers deployed | C with event kind/ownership/zone; exact payment/unused potential U until audited |
| Combat | attack declarations, blocks, player damage, removal and tokens | C events and object crosswalk; causal damage attribution U if native cause absent |
| Board | battlefield, graveyard and zone composition at turn entry | E by IDs and snapshots; C card types at historical time |
| Pilot decisions | selected action, recorded intent and response | E raw intent; available options/opportunity/regret U unless explicitly captured |
| Mechanic effects | sacrifice, death triggers, treasure production, Astartes, tokens, spell discount | C per-event mechanics registry; U for silent/unsupported effects |
| Opponent pressure | early life changes, elimination, opposing board and actions | C; no future-event leakage |

A missing/unsupported signal is **NULL/UNOBSERVED**, not zero. `0` means we can prove no event/opportunity/quantity in a complete, validated window.

## Temporal and statistical policies
- Keep **pregame** models distinct from **T3/T5/T7 or hero-turn** landmark models; define explicitly whether T means global turn or player turn. Recommended: hero completed turn count, as long as boundaries can be established, with precise global-event cutoff.
- Only information at or before landmark is usable; exclude games terminal at/before landmark from survivor-risk model. Terminal state, final object types and final outcome may be used for QA only, not predictive features prior to landmark.
- Primary response: decisive win vs decisive loss from **approved** cohorts only. Draws, stalls and failures go to a separately reported attempts/competing-outcomes diagnostic; do not code them as losses.
- Match grouped splits on shared seeds/protocol/opponent pods; separate any repeated seed or reused opening hand. Do not mix rules/pilot/deck hashes.
- Avoid duplicative predictor encodings like `opponent_present` and `opponent_count` for a design where both are identical.
- Fit logistic elastic net only with sufficient independent seed groups and outcome balance; tune inside grouped CV, evaluate out-of-sample Brier/log loss/calibration vs opponent-only composition baseline. Stability selection and strong-heredity interaction filtering, no post-hoc p-values.
- Bootstrap by independent simulation group; no causal interpretation of card coefficients. For controlled card-swap claims run matched-seed experiments.

## Extraction stages and validation gates
0. **Inventory (no writes)**: list R2 source manifests, native archives, parquet shards, counts and compressed sizes by batch/version; ensure auth in trusted runner only.
1. **Attempt completeness**: reconcile requested, run, stdout, source-native, exported Parquet counts; identify native-limit, retries, skipped attempts; explicitly distinguish `no native available`.
2. **Raw normalization**: parse JSON, verify hashes, replay chain, object IDs/zone references, increasing event seq, snapshot time alignment, valid actor/seat, no duplicated records.
3. **Event registry audit**: sample each `kind_id`, document semantics, zero-seat omission, actor vs owner vs controller, and lifecycle events; reject unproven mappings.
4. **Feature prototype**: start game eligibility, opener, observed first cast, per-landmark life/zone sizes, hand card indicators, cast counts and opponent composition; retain source reference per feature.
5. **Quality report**: by cohort/deck/pilot show features observed, missing, ambiguous and unavailable; quantify event/intent/snapshot coverage and competing-outcome counts.
6. **Model feasibility**: check sample, outcome balance, feature support, seed dependencies, CV folds; only then fit offline elastic net. Never publish exploratory results to UI.
7. **Optional v2 materialization**: partition generated Parquet and JSON dictionary to private R2 with immutable versioned prefixes and completion-manifest-last, subject to separate review.

## Immediate high-priority simulator capture checks for the other chat
1. Verify large-batch workflow uses a sufficiently small shard size and `-native-limit` covers **every attempt**, with no skipped failed attempts; current code may not.
2. Record attempted seeds and terminal status even on retries, turns caps, errors and replay mismatch.
3. Ensure `objects`, snapshots and raw intents are retained in every archived source tarball, not just `events.parquet`.
4. Pin exact original and patched Gorge source, card-corpus, Oracle, hero/opponent deck/pilot and protocol fingerprints at source time.
5. Record explicit distinctions for missing event actor/player=0 so ownership and card attribution can be audited.
6. Compare checksum/outcome for fixed seed with vs without capture, to ensure observation hooks do not alter play.
