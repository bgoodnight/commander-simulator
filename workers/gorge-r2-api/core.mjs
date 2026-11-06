// Pure eligibility and aggregation helpers shared by Worker and offline tests.
// No R2 credentials or source recordings ever leave the Worker.
export const IDENTITY_FIELDS = [
  "engine_commit", "rules_patch_sha256", "card_corpus_sha256",
  "player_deck_sha256", "pilot_version", "opponent_panel_sha256",
  "oracle_bulk_sha256", "simulation_protocol_sha256"
];
// PyArrow typically writes integer game fields as Parquet INT64, and
// hyparquet correctly decodes them as BigInt. Narrow only safe counters.
export function normalizeRow(row) {
  const out={...row};
  for(const key of ["hero_seat","winner_seat","turns","seed","event_start_row","native_event_count"]) {
    if(typeof out[key]==="bigint") {
      if(out[key]>BigInt(Number.MAX_SAFE_INTEGER) ||
         out[key]<BigInt(Number.MIN_SAFE_INTEGER))
        throw Error("Unsafe Parquet INT64 in "+key);
      out[key]=Number(out[key]);
    }
  }
  return out;
}
export const isDecisive = row => (
  row && row.finished === true && row.replay_verified === true &&
  !row.error && row.draw === false &&
  Number.isInteger(row.hero_seat) && row.hero_seat >= 0 && row.hero_seat < 4 &&
  Number.isInteger(row.winner_seat) && row.winner_seat >= 0 && row.winner_seat < 4
);
export function stableJson(obj) {
  const normalize = v => Array.isArray(v) ? v.map(normalize) :
    v && typeof v === "object" ?
      Object.fromEntries(Object.keys(v).sort().map(k => [k, normalize(v[k])])) : v;
  return JSON.stringify(normalize(obj));
}
export async function sha256(text) {
  const bytes = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(hash)].map(x => x.toString(16).padStart(2,"0")).join("");
}
export async function isApproved(row, registry, fingerprintCache=new Map()) {
  if (!isDecisive(row) || typeof row.source_sha256 !== "string" ||
      !/^[a-f0-9]{64}$/i.test(row.source_sha256)) return false;
  const cohort = registry.cohorts?.find(c => c.cohort_id === row.cohort_id);
  if (!cohort || cohort.status !== "current" || cohort.approved !== true ||
      !cohort.approval_ref) return false;
  if (IDENTITY_FIELDS.some(k => !cohort[k] || row[k] !== cohort[k])) return false;
  let fingerprint = fingerprintCache.get(cohort.cohort_id);
  if(!fingerprint) {
    fingerprint = await sha256(stableJson({
      cohort_id: cohort.cohort_id,
      ...Object.fromEntries(IDENTITY_FIELDS.map(k => [k,cohort[k]]))
    }));
    fingerprintCache.set(cohort.cohort_id,fingerprint);
  }
  return row.cohort_manifest_sha256 === fingerprint;
}
export function aggregate(rows, deck) {
  const seen = new Set();
  const selected = rows.filter(row => {
    if (row.deck !== deck || !isDecisive(row)) return false;
    if (typeof row.game_id !== "string" || !row.game_id || seen.has(row.game_id))
      throw Error("Duplicate or invalid approved game ID");
    seen.add(row.game_id);
    return true;
  });
  const group = new Map();
  let wins = 0, losses = 0;
  const turns = [];
  for (const row of selected) {
    const won = row.winner_seat === row.hero_seat;
    if (won) wins++; else losses++;
    if (typeof row.turns === "number" && row.turns >= 0) turns.push(row.turns);
    const decks = JSON.parse(row.decks_json);
    if (!Array.isArray(decks) || decks.length !== 4 ||
        decks[row.hero_seat] !== deck || new Set(decks).size !== 4)
      throw Error("Invalid four-player source pod");
    for (let seat=0; seat<4; seat++) {
      if (seat === row.hero_seat) continue;
      const opponent=decks[seat];
      const v=group.get(opponent)||{name:opponent,n:0,wins:0,losses:0};
      v.n++;
      if (won) v.wins++; else v.losses++;
      group.set(opponent,v);
    }
  }
  turns.sort((a,b)=>a-b);
  const histogram=new Map();
  for(const turn of turns)histogram.set(turn,(histogram.get(turn)||0)+1);
  const median = turns.length ? (turns[(turns.length-1)>>1]+turns[turns.length>>1])/2 : null;
  return {
    schema:"gorge-r2-live-summary-v1",
    source:"r2-direct-parquet",
    population:"approved_current_decisive_only",
    deck,
    n:selected.length,
    wins,losses,
    win_rate:selected.length?wins/selected.length:null,
    baseline:0.25,
    median_game_turns:median,
    game_turn_histogram:[...histogram].map(([turn,games])=>({turn,games})),
    groups:{opponents:[...group.values()].map(g=>({...g,win_rate:g.wins/g.n}))
      .sort((a,b)=>b.n-a.n||a.name.localeCompare(b.name))},
    regressions:{status:"not_precomputed"},
    disclaimer:"Only completed, verified decisive games from explicitly approved current cohorts."
  };
}
/**
 * Stable, presentation-oriented projection: original Results overview metrics
 * with exact denominators and explicit unavailable detail coverage. No native
 * event payloads, hidden identities, seeds, or experimental statistics.
 *
 * Individual game/turn UI data needs its own safe native-source projection;
 * this overview never pretends that event-family counts are a card replay.
 */
export function uiOverview(summary) {
  if(!summary || summary.schema!=="gorge-r2-live-summary-v1" ||
     !["ready","awaiting_cohort_approval","no_warehouse_shards"].includes(summary.status))
    throw Error("invalid_ui_overview_source");
  const ready=summary.status==="ready";
  const groups=ready?summary.groups?.opponents||[]:[];
  const count=ready?summary.n:0;
  if(!Number.isSafeInteger(count)||count<0 ||
     (ready && (summary.wins+summary.losses!==count ||
       !Number.isFinite(summary.win_rate))))throw Error("invalid_ui_outcomes");
  const histogram=ready?summary.game_turn_histogram||[]:[];
  if(ready && histogram.reduce((sum,x)=>sum+x.games,0)!==count)
    throw Error("incomplete_turn_histogram");
  return {
    schema:"gorge-r2-ui-overview-v1",
    deck:summary.deck,
    status:summary.status,
    population:"approved_current_decisive_only",
    source:"r2-direct-parquet",
    outcomes:{n:count,wins:ready?summary.wins:0,
      losses:ready?summary.losses:0,
      win_rate:ready?summary.win_rate:null,baseline:.25},
    game_turn_histogram:histogram,
    median_game_turns:ready?summary.median_game_turns:null,
    groups:{opponents:groups},
    coverage:{
      outcome_games:count,
      turn_histogram_games:ready?histogram.reduce((sum,x)=>sum+x.games,0):0,
      card_insights:"not_exported_from_warehouse",
      named_turn_actions:"requires_source_backed_ui_projection",
      turn_entry_boards:"requires_source_backed_ui_projection",
      hand_durations:"requires_source_backed_ui_projection"
    },
    disclaimer:"Approved, replay-verified decisive games only. Unavailable detail fields are not inferred."
  };
}

/**
 * Convert independently precomputed, public-only per-game projections into
 * the EXACT batch envelope used by the original DeckGameOutcomes renderer.
 * This never attempts to reconstruct missing native turn snapshots from
 * Parquet, and never accepts a projection for an unapproved source row.
 *
 * Projection payload is produced off-request from a verified native recording.
 * UI-facing fields must be source-backed; hidden hands/objects are forbidden.
 */
export function originalUiBatch(rows, projection, deck) {
  if(!Array.isArray(rows)||!rows.length ||
     !projection||projection.schema!=="gorge-r2-original-ui-projection-v1" ||
     projection.deck!==deck||!Array.isArray(projection.games))
    throw Error("invalid_original_ui_projection");
  const indexed=new Map();
  const revisions=new Set();
  for(const row of rows) {
    if(!isDecisive(row)||row.deck!==deck||
       typeof row.game_id!=="string"||indexed.has(row.game_id)||
       typeof row.player_deck_sha256!=="string"||!row.player_deck_sha256)
      throw Error("invalid_original_ui_source");
    indexed.set(row.game_id,row);
    revisions.add(row.player_deck_sha256);
  }
  if(revisions.size!==1)throw Error("mixed_original_ui_deck_revisions");
  if(projection.games.length!==indexed.size)throw Error("incomplete_original_ui_projection");
  const runs=[];
  const matched=new Set();
  for(const item of projection.games) {
    if(!item||typeof item.game_id!=="string"||matched.has(item.game_id))
      throw Error("duplicate_original_ui_game");
    const row=indexed.get(item.game_id);
    if(!row||item.chain!==row.chain)throw Error("original_ui_source_mismatch");
    matched.add(item.game_id);
    if(item.source_sha256!==row.source_sha256)
      throw Error("original_ui_source_digest_mismatch");
    const run=item.run;
    const allowedRunFields=new Set(["seed","completed_rounds","opening_board_states",
      "opening_hand","opening_hands_by_seat","opening_hand_count","mulligan",
      "ui_observations","life_history","opponent_decks","gorge_source","outcome"]);
    if(!run||Object.keys(run).some(key=>!allowedRunFields.has(key)))
      throw Error("unexpected_original_ui_run_field");
    if(!Number.isInteger(run.seed)||run.seed!==row.seed||
       !Number.isInteger(run.completed_rounds)||run.completed_rounds<1||
       run.completed_rounds>60||
       !Array.isArray(run.life_history)||
       run.life_history.length!==run.completed_rounds+1||
       !Array.isArray(run.ui_observations)||
       run.ui_observations.length!==run.completed_rounds||
       run.gorge_source?.chain!==row.chain||
       run.gorge_source?.visibility!=="public_events_only"||
       run.gorge_source?.synthetic_simulation_only!==false||
       run.outcome?.complete!==true||
       run.outcome?.status!==(row.hero_seat===row.winner_seat?"win":"loss")||
       run.outcome?.winner_seat!==(row.winner_seat-row.hero_seat+4)%4)
      throw Error("invalid_original_ui_game");
    // Public dashboard never receives private object identity crosswalks,
    // hand card identities, native logs, bot intents or unfiltered events.
    const forbidden=new Set(["event_json","intents","log","objects","object_identity",
      "secret","native_events","source_object_id","library","hidden_cards"]);
    const visit=(value)=>{
      if(Array.isArray(value)) {for(const part of value)visit(part);return;}
      if(!value||typeof value!=="object")return;
      for(const [key,v] of Object.entries(value)) {
        if(forbidden.has(key))throw Error("private_original_ui_field");
        if(["hand","opening_hand","opponent_hands","opening_hands_by_seat"].includes(key)&&v!==null)
          throw Error("private_original_ui_hand");
        visit(v);
      }
    };
    visit(run);
    runs.push(run);
  }
  const requestedRounds=Math.max(...runs.map(run=>run.completed_rounds));
  // Reconcile the cohort-wide batch horizon without inventing turns or
  // rewriting recorded game observations.
  const normalizedRuns=runs.map(run=>({
    ...run,outcome:{...run.outcome,requested_rounds:requestedRounds}
  }));
  return {
    format:"commander-gorge-outcomes-v1",schema_version:1,engine:"gorge",
    deck_key:deck,deck_sha256:[...revisions][0],
    scenario:"four_real_commander_decks",pilot_style:"gorge_bot",
    provisional_mode:"not_applicable",
    opponent_fidelity:"gorge_native_full_100_card_decks",
    outcomes_are_competitive_win_rates:false,
    requested_rounds:requestedRounds,runs:normalizedRuns,
    source_note:"Approved source-backed public Gorge UI projections; no private native logs or hidden hands.",
    example_replays:[]
  };
}

export function validateDeck(deck) {
  if (!/^[a-z][a-z0-9_-]{1,75}$/.test(deck||"")) throw Error("Invalid deck");
  return deck;
}

/**
 * Public-safe game index: use only after isApproved verifies the source cohort.
 * This is deliberately NOT a native replay or an events.parquet export.
 */
export function approvedGameIndex(rows, deck, limit=20) {
  if(!Number.isInteger(limit) || limit<1 || limit>25)throw Error("invalid_game_limit");
  const ids=new Set();
  const parsed=rows.map(row=>{
    if(!isDecisive(row) || row.deck!==deck)throw Error("unapproved_game_index_source");
    if(typeof row.game_id!=="string" || !row.game_id || ids.has(row.game_id))
      throw Error("duplicate_or_invalid_game_id");
    ids.add(row.game_id);
    const pod=JSON.parse(row.decks_json);
    if(!Array.isArray(pod) || pod.length!==4 || pod[row.hero_seat]!==deck ||
      pod.some(v=>typeof v!=="string" || !/^[a-z][a-z0-9_-]{1,75}$/.test(v)) ||
      new Set(pod).size!==4)throw Error("invalid_game_pod");
    return {
      game_id:row.game_id,
      turns:Number.isInteger(row.turns)&&row.turns>=0?row.turns:null,
      result:row.hero_seat===row.winner_seat?"win":"loss",
      opponent_decks:pod.filter((_,seat)=>seat!==row.hero_seat),
      // No source trace, seed, hidden hand, event payload, or object keys.
    };
  }).sort((a,b)=>a.game_id.localeCompare(b.game_id));
  return {schema:"gorge-r2-approved-game-index-v1",deck,
    population:"approved_current_decisive_only",
    total:parsed.length,limit,has_more:parsed.length>limit,games:parsed.slice(0,limit)};
}

/** Safe detail for one already-verified, approved game; never exposes the native recording. */
export function approvedGameDetail(rows,deck,gameId) {
  const matches=rows.filter(row=>row.game_id===gameId);
  if(matches.length>1)throw Error("duplicate_approved_game_id");
  if(!matches.length)return null;
  const item=approvedGameIndex(matches,deck,1).games[0];
  return {schema:"gorge-r2-approved-game-detail-v1",
    population:"approved_current_decisive_only",deck,...item,
    replay_status:"not_available",
    disclaimer:"Native event replay is not exposed by this endpoint."};
}

export const EVENT_KINDS = [
  "game_start","shuffle","move_zone","draw","life_change","damage","tap",
  "untap","step_change","turn_change","priority","put_on_stack","resolve",
  "mana_add","mana_clear","counter_change","declare_attackers",
  "declare_blockers","player_lost","game_over"
];

/** Counts only, never the private native event payload or game object identities. */
export function approvedEventSegments(events,gameId) {
  const selected=events.filter(e=>e.game_id===gameId).sort((a,b)=>a.seq-b.seq);
  if(selected.length>100000)throw Error("event_count_limit");
  const segments=[];
  let segment=null,last=-1,total=0;
  for(const e of selected) {
    if(!Number.isSafeInteger(e.seq)||e.seq<=last ||
       !Number.isSafeInteger(e.kind_id)||e.kind_id<0 ||
       typeof e.secret!=="boolean")throw Error("invalid_event_projection");
    last=e.seq;
    // Secret native events are deliberately not counted by family or exposed
    // with their per-event location; their contribution is withheld entirely.
    if(e.kind_id===9 || segment===null) {
      segment={segment:segments.length,start_seq:e.seq,end_seq:e.seq,
        public_events:0,withheld_events:0,kinds:{}};
      segments.push(segment);
    }
    segment.end_seq=e.seq;
    if(e.secret)segment.withheld_events++;
    else {
      const family=EVENT_KINDS[e.kind_id]??"unknown";
      segment.kinds[family]=(segment.kinds[family]??0)+1;
      segment.public_events++;
    }
    total++;
  }
  return {schema:"gorge-r2-event-segments-v1",game_id:gameId,
    segmentation:"native_turn_change_boundaries_not_complete_player_rounds",
    event_count:total,segments,
    raw_events_exposed:false};
}

/** Authoritative physical Parquet row window; rejects legacy unindexed shards.
 * Never derive offsets from client input or game_id/seed.
 */
export function approvedEventWindow(game, totalRows, maxGameEvents=30000) {
  const start=game?.event_start_row,count=game?.native_event_count;
  if(!Number.isSafeInteger(totalRows)||totalRows<0||
     !Number.isSafeInteger(start)||start<0||
     !Number.isSafeInteger(count)||count<1||count>maxGameEvents||
     start>totalRows||count>totalRows-start)
    throw Error("unindexed_or_oversized_game_events");
  return {rowStart:start,rowEnd:start+count,count};
}

/** Strict opt-in for short-lived, hex-only Worker diagnostic credentials. */
export function isDiagnosticAuthorized(authHeader,token) {
  return typeof token==="string" && /^[a-f0-9]{64}$/.test(token) &&
    typeof authHeader==="string" && authHeader==="Bearer "+token;
}
