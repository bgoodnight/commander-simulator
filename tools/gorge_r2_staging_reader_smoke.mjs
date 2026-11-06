/** R2 staging readback using the actual Worker materialized reader.
 * The bucket is deliberately file-backed from objects downloaded from R2:
 * every Worker SHA/registry/content check is exercised without changing live bindings.
 * Usage: node tools/gorge_r2_staging_reader_smoke.mjs <readback> <pointer> <run-id-attempt>
 */
import fs from "node:fs";
import path from "node:path";
import {getMaterialized} from "../workers/gorge-r2-api/materialized.mjs";

const [root,pointerFile,run]=process.argv.slice(2);
if(!root||!pointerFile||!/^[0-9]+-[0-9]+$/.test(run))
  throw Error("Usage: smoke readback pointer run-id-attempt");
const prefix="results/materialized/staging/"+run+"/";
const registry=JSON.parse(fs.readFileSync("data/gorge_analytics_cohort_registry_v1.json","utf8"));
const bucket={async get(key){
  if(!key.startsWith(prefix))throw Error("Unexpected bucket prefix: "+key);
  const relative=key.slice(prefix.length);
  const filename=relative==="current.json"?pointerFile:path.join(root,relative);
  const full=path.resolve(filename);
  if(relative!=="current.json" && !full.startsWith(path.resolve(root)+path.sep))
    throw Error("Invalid relative bucket key");
  if(!fs.existsSync(full))return null;
  const raw=fs.readFileSync(full);
  return {size:raw.length,
    async arrayBuffer(){return raw.buffer.slice(raw.byteOffset,raw.byteOffset+raw.byteLength);},
    async json(){return JSON.parse(raw.toString("utf8"));}};
}};
let checked=0;
for(const deck of ["mortarion_current","magnus_premium"]){
  const catalog=await getMaterialized(bucket,deck,registry,null,null,"summary",0,prefix);
  if(catalog.status!=="ready")throw Error("Missing approved stage deck "+deck);
  if(catalog.total!==12||catalog.summary.n!==12||catalog.summary.wins+catalog.summary.losses!==12)
    throw Error("Stage totals inconsistent "+deck);
  const insights=await getMaterialized(bucket,deck,registry,null,null,"insights",0,prefix);
  if(insights.status!=="ready"||insights.insights.verified_games!==12||
     insights.insights.coverage?.missing!==0)
    throw Error("Complete native insights were not built for "+deck);
  const index=await getMaterialized(bucket,deck,registry,0,null,"summary",0,prefix);
  if(index.page.games.length!==12)throw Error("Incomplete game page "+deck);
  for(const candidate of [index.page.games[0],index.page.games.at(-1)]){
    const gid=candidate.game_id;
    const replay=await getMaterialized(bucket,deck,registry,0,gid,"summary",0,prefix);
    const detail=replay.game;
    const run=detail.batch.runs[0];
    if(run.gorge_source.visibility!=="omniscient"||
       run.gorge_source.synthetic_simulation_only!==true||
       !Array.isArray(run.opening_hand)||
       run.opening_hand.length!==run.opening_hand_count||
       !Array.isArray(run.opening_hands_by_seat)||
       run.opening_hands_by_seat.length!==3||
       !Array.isArray(run.opening_board_states)||
       run.opening_board_states.length!==4||
       run.opening_board_states.some(s=>!Array.isArray(s.library)||!Array.isArray(s.hand)))
      throw Error("Missing omniscient four-seat state "+gid);
    let seen=0,secret=0,prev=-1;
    for(let part=0;part<detail.event_parts.length;part++){
      const item=await getMaterialized(bucket,deck,registry,0,gid,"events",part,prefix);
      if(item.status!=="ready"||item.version!==catalog.version||
         item.native_event_count!==detail.native_event_count||
         item.part_count!==detail.event_parts.length)
        throw Error("Event part/version mismatch "+gid);
      for(const event of item.events){
        if(!Number.isInteger(event.seq)||event.seq<=prev)
          throw Error("Out-of-order native event "+gid);
        prev=event.seq;
        seen++;
        if(event.secret===true)secret++;
      }
    }
    if(seen!==detail.native_event_count||secret<1)
      throw Error("Missing source native/hidden events "+gid);
    checked++;
    console.log("PASS",deck,gid,"event count",seen,"secret",secret,
      "hand",run.opening_hand.length,"version",catalog.version.slice(0,12));
  }
}
if(checked!==4)throw Error("Incomplete stage Worker smoke");
console.log("PASS full R2-readback Worker API checks",checked,"games across two decks");
