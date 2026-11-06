"use strict";
/* Convert sanitized source-backed Gorge replays to the ORIGINAL Results runs.
 * Offline exporter only. Never put raw Gorge logs, object identity maps,
 * hidden hands, or source event object IDs in the public R2 projection.
 */
const fs=require("node:fs");
const adapter=require("../web/pages/gorge_legacy_adapter.js");
const renderer=require("../web/pages/game_outcomes.js");
const MAX_GAMES=200;
function requireText(v,label){if(typeof v!=="string"||!v.trim())throw Error("Missing "+label);return v;}
function removeObjectIds(v){
  if(Array.isArray(v))return v.map(removeObjectIds);
  if(!v || typeof v!=="object")return v;
  return Object.fromEntries(Object.entries(v)
    .filter(([k])=>k!=="source_object_id")
    .map(([k,val])=>[k,removeObjectIds(val)]));
}
function generate(input){
  if(input?.schema!=="gorge-original-ui-projection-input-v1")
    throw Error("Invalid projection input schema");
  const deck=requireText(input.deck,"deck");
  const batch=requireText(input.source_batch,"batch");
  const sha=requireText(input.deck_sha256,"deck hash");
  if(!/^[a-f0-9]{64}$/i.test(sha))throw Error("Invalid deck SHA");
  if(!Number.isInteger(input.shard)||input.shard<0)throw Error("Invalid shard");
  if(!Array.isArray(input.games)||input.games.length<1||input.games.length>MAX_GAMES)
    throw Error("Invalid game count");
  const verified=[],seeds=new Set(),ids=new Set();
  for(const entry of input.games){
    if(!Number.isInteger(entry.seed)||seeds.has(entry.seed)||
       typeof entry.game_id!=="string"||ids.has(entry.game_id))
      throw Error("Duplicate/malformed source game");
    seeds.add(entry.seed);ids.add(entry.game_id);
    if(!/^[a-f0-9]{64}$/i.test(entry.source_sha256||""))
      throw Error("Missing native digest");
    const expected=batch+"/"+deck+"/"+input.shard+"/"+entry.seed;
    if(entry.game_id!==expected)throw Error("Game ID differs from warehouse identity");
    const replay=entry.replay;
    if(!adapter.validateReplay(replay)||replay.visibility!=="public_events_only"||
       replay.synthetic_simulation_only!==false||
       replay.seed!==entry.seed||replay.chain!==entry.chain||
       replay.decks[entry.hero_seat]!==deck)
      throw Error("Invalid or nonpublic native-derived replay");
    if(!Number.isInteger(entry.hero_seat)||entry.hero_seat<0||entry.hero_seat>3||
       !Number.isInteger(entry.winner_seat)||entry.winner_seat<0||entry.winner_seat>3||
       adapter.realWinner(replay)!==entry.winner_seat)
      throw Error("Native winner/hero seat provenance mismatch");
    const own=replay.turns.filter(t=>Number.isInteger(t.turn)&&
      t.turn>0&&t.seat===entry.hero_seat);
    if(!own.length||own.length>60)throw Error("Invalid native round count");
    const hashes={[deck]:sha};
    let run=adapter.projectRun(replay,entry.hero_seat,own.length,hashes);
    if(!run.outcome.complete || !["win","loss"].includes(run.outcome.status))
      throw Error("Nondecisive game cannot enter approved projection");
    run=removeObjectIds(run);
    if(run.opening_hand!==null||run.opening_hands_by_seat!==null||
       run.ui_observations.some(t=>t.hand!==null||t.opponent_hands!==null))
      throw Error("Projected hidden hand leaked");
    verified.push({game_id:entry.game_id,chain:entry.chain,
      source_sha256:entry.source_sha256,run});
  }
  const rounds=Math.max(...verified.map(g=>g.run.completed_rounds));
  const batchEnvelope={format:"commander-gorge-outcomes-v1",schema_version:1,
    engine:"gorge",deck_key:deck,deck_sha256:sha,
    scenario:"four_real_commander_decks",pilot_style:"gorge_bot",
    provisional_mode:"not_applicable",
    opponent_fidelity:"gorge_native_full_100_card_decks",
    outcomes_are_competitive_win_rates:false,requested_rounds:rounds,
    runs:verified.map(g=>({...g.run,outcome:{...g.run.outcome,
      requested_rounds:rounds}})),
    example_replays:[]};
  if(!renderer.validate(batchEnvelope))throw Error("Original UI rejected projected batch");
  return {schema:"gorge-r2-original-ui-projection-v1",source_batch:batch,
    deck,shard:input.shard,games:verified};
}
if(require.main===module){
  if(process.argv.length!==4)throw Error("Usage: node tools/gorge_original_ui_projection.cjs input.json output.json");
  const out=generate(JSON.parse(fs.readFileSync(process.argv[2],"utf8")));
  fs.writeFileSync(process.argv[3],JSON.stringify(out)+"\n");
  process.stdout.write(JSON.stringify({games:out.games.length,
    deck:out.deck,schema:out.schema})+"\n");
}
module.exports={generate};
