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
  for(const key of ["hero_seat","winner_seat","turns","seed"]) {
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
    groups:{opponents:[...group.values()].map(g=>({...g,win_rate:g.wins/g.n}))
      .sort((a,b)=>b.n-a.n||a.name.localeCompare(b.name))},
    regressions:{status:"not_precomputed"},
    disclaimer:"Only completed, verified decisive games from explicitly approved current cohorts."
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
