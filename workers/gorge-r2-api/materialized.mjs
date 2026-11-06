import {isApproved} from "./core.mjs";

const MATERIALIZED_PREFIX="results/materialized/v1/";
async function verifiedJson(bucket,key,expectedHash,maxBytes=4*1024*1024) {
  const object=await bucket.get(key);
  if(!object || object.size>maxBytes)throw Error("missing_or_oversized_materialized_object");
  const data=await object.arrayBuffer();
  const digest=await crypto.subtle.digest("SHA-256",data);
  const actual=[...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,"0")).join("");
  if(actual!==expectedHash)throw Error("materialized_digest_mismatch");
  return JSON.parse(new TextDecoder().decode(data));
}
export async function getMaterialized(bucket,deck,registry,page=null,gameId=null,kind="summary",eventPart=0) {
  const pointerObject=await bucket.get(MATERIALIZED_PREFIX+"current.json");
  if(!pointerObject)return null; // Existing source-backed legacy route stays available.
  if(pointerObject.size>1024)throw Error("oversized_materialized_pointer");
  const pointer=await pointerObject.json();
  if(pointer.schema!=="gorge-r2-results-current-v1" ||
     !/^[a-f0-9]{64}$/.test(pointer.version||"") ||
     !/^[a-f0-9]{64}$/.test(pointer.manifest_sha256||""))
    throw Error("invalid_materialized_pointer");
  const prefix=MATERIALIZED_PREFIX+"versions/"+pointer.version+"/";
  const manifest=await verifiedJson(bucket,prefix+"manifest.json",pointer.manifest_sha256);
  if(manifest.schema!=="gorge-r2-materialized-results-v1" ||
     manifest.version!==pointer.version)throw Error("invalid_materialized_manifest");
  const entry=manifest.decks?.[deck];
  if(!entry)return {schema:"gorge-r2-materialized-response-v1",deck,
    version:pointer.version,status:"no_approved_games"};
  const cohort=registry.cohorts.find(c=>c.cohort_id===entry.cohort_id &&
    c.status==="current"&&c.approved===true&&c.deck===deck&&c.approval_ref);
  if(!cohort || !(await isApproved({
    ...Object.fromEntries(["engine_commit","rules_patch_sha256","card_corpus_sha256",
      "player_deck_sha256","pilot_version","opponent_panel_sha256",
      "oracle_bulk_sha256","simulation_protocol_sha256"].map(k=>[k,cohort[k]])),
    cohort_id:entry.cohort_id,cohort_manifest_sha256:entry.cohort_fingerprint,
    deck,finished:true,replay_verified:true,error:null,draw:false,
    hero_seat:0,winner_seat:0,source_sha256:"a".repeat(64)
  },registry)))throw Error("materialized_cohort_not_current");
  if(!Number.isSafeInteger(entry.n)||entry.n<1||
     entry.n!==entry.wins+entry.losses||
     !/^[a-f0-9]{64}$/.test(entry.ui_deck_sha256||"")||
     !Array.isArray(entry.pages)||entry.pages.length!==Math.ceil(entry.n/25))
    throw Error("invalid_materialized_deck_manifest");
  if(kind==="insights"){
    if(entry.insights===null || entry.insights===undefined)
      return {schema:"gorge-r2-materialized-response-v1",deck,
        version:pointer.version,status:"insights_pending",total:entry.n};
    if(entry.insights.path!=="insights.json" ||
       !/^[a-f0-9]{64}$/.test(entry.insights.sha256||""))
      throw Error("invalid_materialized_insights_reference");
    const report=await verifiedJson(bucket,prefix+deck+"/insights.json",
      entry.insights.sha256,8*1024*1024);
    if(report.deck!==deck||report.cohort_version!==pointer.version||
       report.verified_games!==entry.n||report.observed_games!==entry.n||
       report.coverage?.missing!==0||
       report.coverage?.denominator!==entry.n||
       report.coverage?.level!=="full-cohort"||
       !report.categories||typeof report.categories!=="object")
      throw Error("invalid_materialized_insights_coverage");
    return {schema:"gorge-r2-materialized-response-v1",deck,
      version:pointer.version,status:"ready",total:entry.n,insights:report};
  }
  const target=page===null?entry.summary:entry.pages[page];
  if(!target || (page!==null && page>=entry.pages.length))
    return {schema:"gorge-r2-materialized-response-v1",deck,
      version:pointer.version,status:"page_not_found"};
  const path=page===null?"summary.json":"pages/"+String(page).padStart(6,"0")+".json";
  if(target.path!==path || !/^[a-f0-9]{64}$/.test(target.sha256||""))
    throw Error("invalid_materialized_object_reference");
  const payload=await verifiedJson(bucket,prefix+deck+"/"+path,target.sha256);
  if(payload.deck!==deck || (payload.cohort_version!==undefined &&
     payload.cohort_version!==pointer.version) ||
     (page===null && (payload.n!==entry.n || payload.wins!==entry.wins ||
       payload.losses!==entry.losses || payload.schema!=="gorge-r2-live-summary-v1")) ||
     (page!==null && (payload.schema!=="gorge-r2-materialized-page-v1" ||
       payload.version!==pointer.version||payload.page!==page||
       payload.total!==entry.n||!Array.isArray(payload.games)||
       payload.games.length!==target.count)))
    throw Error("materialized_payload_mismatch");
  if(gameId!==null){
    if(page===null)throw Error("game_page_required");
    const found=payload.games.filter(g=>g.game_id===gameId);
    if(found.length!==1)throw Error("game_not_in_page");
    const keyDigest=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(gameId));
    const hex=[...new Uint8Array(keyDigest)].map(x=>x.toString(16).padStart(2,"0")).join("");
    if(!/^[a-f0-9]{64}$/.test(found[0].sha256||""))
      throw Error("invalid_game_digest");
    const detail=await verifiedJson(bucket,prefix+deck+"/games/"+hex+".json",found[0].sha256);
    if(detail.schema!=="gorge-r2-materialized-game-v1" ||
       detail.deck!==deck || detail.version!==pointer.version ||
       detail.game_id!==gameId || detail.batch?.deck_sha256!==entry.ui_deck_sha256 ||
       detail.batch?.runs?.length!==1)
      throw Error("materialized_game_identity_mismatch");
    if(kind==="events"){
      const parts=detail.event_parts;
      if(!Array.isArray(parts)||parts.length<1)
        return {schema:"gorge-r2-materialized-response-v1",deck,
          version:pointer.version,status:"events_pending",total:entry.n};
      const part=parts[eventPart];
      const path="events/"+hex+"/"+String(eventPart).padStart(6,"0")+".json";
      if(!part||part.path!==path||
         !/^[a-f0-9]{64}$/.test(part.sha256||""))
        throw Error("invalid_native_event_part_reference");
      const record=await verifiedJson(bucket,prefix+deck+"/"+path,
        part.sha256,6*1024*1024);
      if(record.schema!=="gorge-r2-native-event-part-v1" ||
         record.deck!==deck||record.version!==pointer.version ||
         record.game_id!==gameId||record.part!==eventPart||
         record.total!==detail.native_event_count||
         !Array.isArray(record.events)||record.events.length!==part.count||
         part.count>500||part.count<1)
        throw Error("invalid_native_event_part");
      return {schema:"gorge-r2-materialized-response-v1",deck,
        version:pointer.version,status:"ready",total:entry.n,
        game_id:gameId,part:eventPart,part_count:parts.length,
        native_event_count:detail.native_event_count,events:record.events};
    }
    return {schema:"gorge-r2-materialized-response-v1",deck,
      version:pointer.version,status:"ready",total:entry.n,game:detail};
  }
  return {schema:"gorge-r2-materialized-response-v1",deck,
    version:pointer.version,status:"ready",
    total:entry.n,page_count:entry.pages.length,
    ...(page===null?{summary:payload}:{page:payload})};
}

