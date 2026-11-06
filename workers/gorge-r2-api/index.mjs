import { parquetReadObjects, parquetMetadataAsync, parquetSchema } from "hyparquet";
import { compressors } from "hyparquet-compressors";
import registry from "../../data/gorge_analytics_cohort_registry_v1.json";
import { aggregate, uiOverview, originalUiBatch, isApproved, isDecisive, isDiagnosticAuthorized, validateDeck, normalizeRow, approvedGameIndex, approvedGameDetail, approvedEventSegments, approvedEventWindow } from "./core.mjs";

// Read-only Cloudflare Worker. The R2 binding has no credentials in JS or HTML.
// Never return native logs, intents, event_json, object catalog, or hidden zones.
const PREFIX="warehouse/v1/";
const MAX_SHARDS=40;
const MAX_OBJECT_SIZE=16*1024*1024;  // initial latency/memory guardrail
const ORIGIN="https://bgoodnight.github.io";
const DIAGNOSTIC_BATCH="42129260132-1";
const DIAGNOSTIC_DECKS=new Set(["mortarion_current","magnus_premium"]);
function diagnosticJson(value,status=200) {
  // No public CORS and no browser/proxy caching for experimental recordings.
  return new Response(JSON.stringify(value),{status,headers:{
    "Content-Type":"application/json; charset=utf-8",
    "Cache-Control":"private, no-store, max-age=0",
    "X-Content-Type-Options":"nosniff"
  }});
}

const now=()=>performance.now();
const duration=t=>Math.round((now()-t)*10)/10;
function json(value,status=200,ms=0) {
  return new Response(JSON.stringify(value),{
    status,headers:{
      "Content-Type":"application/json; charset=utf-8",
      "Cache-Control":"public, max-age=30, stale-while-revalidate=30",
      "Access-Control-Allow-Origin":ORIGIN,
      "Vary":"Origin",
      "X-Gorge-Api-Ms":String(ms),
      "X-Content-Type-Options":"nosniff"
    }
  });
}
function fail(status,code,t) {return json({error:code},status,duration(t));}
async function listShards(bucket) {
  let cursor, pages=0, truncated=false;
  const shards=[];
  do {
    const listing=await bucket.list({prefix:PREFIX,limit:500,...(cursor?{cursor}:{})});
    for (const obj of listing.objects) {
      if (!obj.key.endsWith("/manifest.json")) continue;
      const match=obj.key.match(/^warehouse\/v1\/([0-9]+-[0-9]+)\/([a-z0-9_-]+)\/([0-9]+)\/manifest\.json$/);
      if (!match) continue;
      shards.push({manifestKey:obj.key,batch:match[1],deck:match[2],shard:match[3]});
      if (shards.length>=MAX_SHARDS) {truncated=true;break;}
    }
    if(truncated)break;
    cursor=listing.truncated?listing.cursor:null;
    pages++;
  } while (cursor && pages<4);
  if(cursor)truncated=true;
  return {shards:shards.sort((a,b)=>b.batch.localeCompare(a.batch)),truncated};
}
async function readManifest(bucket,shard) {
  const file=await bucket.get(shard.manifestKey);
  if (!file) throw Error("missing_manifest");
  const manifest=await file.json();
  if(manifest.schema!=="gorge-warehouse-shard-v1" ||
     manifest.batch_id!==shard.batch ||
     manifest.player_deck!==shard.deck ||
     String(manifest.shard)!==shard.shard ||
     !manifest.files?.["games.parquet"]?.sha256)throw Error("invalid_manifest");
  return manifest;
}
async function readGames(bucket,shard,manifest) {
  const key=shard.manifestKey.replace(/manifest\.json$/,"games.parquet");
  const info=await bucket.head(key);
  if(!info || info.size!==manifest.files["games.parquet"].bytes)
    throw Error("parquet_file_mismatch");
  if(info.size>MAX_OBJECT_SIZE)throw Error("parquet_file_too_large");
  // AsyncBuffer from private R2 byte ranges: no signed URLs, no full event scans.
  const file={
    byteLength:info.size,
    async slice(begin,end) {
      const from=Math.max(0,begin<0?info.size+begin:begin);
      const to=end===undefined?info.size:Math.min(info.size,end<0?info.size+end:end);
      if(to<from)throw Error("invalid_range");
      const length=to-from;
      if(!length)return new ArrayBuffer(0);
      const chunk=await bucket.get(key,{range:{offset:from,length}});
      if(!chunk)throw Error("missing_parquet_range");
      return chunk.arrayBuffer();
    }
  };
  const metadata=await parquetMetadataAsync(file);
  const columnsAvailable=new Set(parquetSchema(metadata).children.map(x=>x.element.name));
  const requested=["game_id","deck","finished","replay_verified","error","draw",
      "hero_seat","winner_seat","turns","decks_json","source_sha256","cohort_id",
      "cohort_manifest_sha256","engine_commit","rules_patch_sha256",
      "card_corpus_sha256","player_deck_sha256","pilot_version",
      "opponent_panel_sha256","oracle_bulk_sha256","simulation_protocol_sha256",
      "event_start_row","native_event_count","batch_id","seed","chain"];
  const rows=(await parquetReadObjects({file,compressors,
    columns:requested.filter(key=>columnsAvailable.has(key))})).map(normalizeRow);
  if(rows.length!==manifest.files["games.parquet"].rows)
    throw Error("parquet_row_count_mismatch");
  return rows;
}

// Events are private omniscient data. Read only a bounded set of safe columns,
// and only after game + cohort approval. Never request event_json or object IDs.
async function readEventSegments(bucket,shard,manifest,game) {
  const expected=manifest.files?.["events.parquet"];
  if(!expected)throw Error("missing_event_manifest");
  const window=approvedEventWindow(game,expected.rows);
  const key=shard.manifestKey.replace(/manifest\.json$/,"events.parquet");
  const info=await bucket.head(key);
  if(!info || info.size!==expected.bytes || info.size>MAX_OBJECT_SIZE)
    throw Error("event_parquet_unavailable");
  const file={byteLength:info.size,async slice(begin,end) {
    const from=Math.max(0,begin<0?info.size+begin:begin);
    const to=end===undefined?info.size:Math.min(info.size,end<0?info.size+end:end);
    if(to<from)throw Error("invalid_event_range");
    if(to===from)return new ArrayBuffer(0);
    const part=await bucket.get(key,{range:{offset:from,length:to-from}});
    if(!part)throw Error("event_range_unavailable");
    return part.arrayBuffer();
  }};
  const metadata=await parquetMetadataAsync(file);
  const present=new Set(parquetSchema(metadata).children.map(c=>c.element.name));
  const required=["game_id","seq","kind_id","secret"];
  if(required.some(c=>!present.has(c)))throw Error("missing_event_columns");
  const rows=(await parquetReadObjects({file,compressors,columns:required,
    rowStart:window.rowStart,rowEnd:window.rowEnd}))
    .map(row=>({
      game_id:row.game_id,
      seq:typeof row.seq==="bigint"?Number(row.seq):row.seq,
      kind_id:typeof row.kind_id==="bigint"?Number(row.kind_id):row.kind_id,
      secret:row.secret
    }));
  if(rows.length!==window.count || rows.some(row=>row.game_id!==game.game_id))
    throw Error("event_window_source_mismatch");
  return approvedEventSegments(rows,game.game_id);
}
// Strictly private test bridge: a pinned experimental recording is allowed to
// exercise the REAL R2 Parquet path but is never approved for public analytics.
// The bearer token is installed only during deployment and revoked afterward.
async function getDiagnosticGame(env,deck,gameId) {
  const {shards,truncated}=await listShards(env.GORGE_R2);
  if(truncated)throw Error("shard_scan_limit_reached");
  const pinned=shards.filter(s=>s.batch===DIAGNOSTIC_BATCH && s.deck===deck);
  if(pinned.length!==1 || pinned[0].shard!=="0")
    throw Error("missing_or_duplicate_pinned_experiment");
  const shard=pinned[0];
  const manifest=await readManifest(env.GORGE_R2,shard);
  const games=await readGames(env.GORGE_R2,shard,manifest);
  const valid=games.filter(g=>g.deck===deck && g.batch_id===DIAGNOSTIC_BATCH &&
    g.cohort_id==null && isDecisive(g) &&
    typeof g.source_sha256==="string" &&
    /^[a-f0-9]{64}$/i.test(g.source_sha256) &&
    Number.isSafeInteger(g.native_event_count) &&
    g.native_event_count>0);
  // A partial or unexpectedly modified experimental source fails closed.
  if(valid.length!==(deck==="mortarion_current"?12:11) ||
     valid.length!==games.length)
    throw Error("experimental_source_population_mismatch");
  if(gameId===null){
    const index=approvedGameIndex(valid,deck,5);
    return {schema:"gorge-r2-private-diagnostic-index-v1",
      status:"experimental_not_certified",
      population:"pinned_experimental_not_approved",
      deck,batch:DIAGNOSTIC_BATCH,
      total:index.total,games:index.games};
  }
  const match=valid.filter(g=>g.game_id===gameId);
  if(match.length!==1)return {schema:"gorge-r2-private-diagnostic-timeline-v1",
    status:"game_not_found",deck,game:null};
  const g=match[0];
  const detail=approvedGameIndex([g],deck,1).games[0];
  const timeline=await readEventSegments(env.GORGE_R2,shard,manifest,g);
  return {schema:"gorge-r2-private-diagnostic-timeline-v1",
    status:"experimental_not_certified",
    population:"pinned_experimental_not_approved",
    deck,game:{...detail,timeline}};
}
async function getApprovedTimeline(env,deck,gameId,metrics) {
  const {shards,truncated}=await listShards(env.GORGE_R2);
  if(truncated)throw Error("shard_scan_limit_reached");
  const matching=shards.filter(s=>s.deck===deck);
  metrics.shards_scanned=matching.length;
  if(!registry.cohorts.some(c=>c.status==="current"&&c.approved===true))
    return {schema:"gorge-r2-game-timeline-v1",deck,game:null,
      status:matching.length?"awaiting_cohort_approval":"no_warehouse_shards"};
  let found=null;
  const fingerprints=new Map();
  for(const shard of matching) {
    const manifest=await readManifest(env.GORGE_R2,shard);
    const games=await readGames(env.GORGE_R2,shard,manifest);
    for(const g of games) {
      if(g.game_id!==gameId)continue;
      if(found)throw Error("duplicate_game_id");
      if(!(await isApproved(g,registry,fingerprints)))
        continue;
      const detail=approvedGameDetail([g],deck,gameId);
      const segments=await readEventSegments(env.GORGE_R2,shard,manifest,g);
      found={...detail,timeline:segments};
    }
  }
  return {schema:"gorge-r2-game-timeline-v1",deck,game:found,
    status:found?"ready":"game_not_found"};
}

async function getSummary(env,deck,metrics) {
  const {shards,truncated}=await listShards(env.GORGE_R2);
  const matching=shards.filter(x=>x.deck===deck);
  metrics.shards_scanned=matching.length;
  metrics.list_truncated=truncated;
  if(truncated)throw Error("shard_scan_limit_reached");
  // Critical optimization: no approved registry means no Parquet decompression.
  const approved=registry.cohorts.filter(c=>c.status==="current"&&c.approved===true);
  if(!approved.length) {
    return {schema:"gorge-r2-live-summary-v1",source:"r2-direct-parquet",
      population:"approved_current_decisive_only",deck,n:0,wins:0,losses:0,
      win_rate:null,baseline:.25,groups:{opponents:[]},
      median_game_turns:null,regressions:{status:"not_precomputed"},
      status:matching.length?"awaiting_cohort_approval":"no_warehouse_shards",
      raw_shards_seen:matching.length};
  }
  const rows=[];
  const fingerprintCache=new Map();
  for(const shard of matching) {
    const manifest=await readManifest(env.GORGE_R2,shard);
    const games=await readGames(env.GORGE_R2,shard,manifest);
    for(const game of games)if(await isApproved(game,registry,fingerprintCache))rows.push(game);
  }
  return {...aggregate(rows,deck),status:rows.length?"ready":"awaiting_cohort_approval",
    raw_shards_seen:matching.length};
}
// R2 stores the source-backed original-renderer projection alongside the
// Parquet shard. It is created by a separate verified native replay exporter.
// The Worker alone decides which games are approved to enter a public batch.
async function getOriginalUiBatch(env,deck,metrics) {
  const {shards,truncated}=await listShards(env.GORGE_R2);
  if(truncated)throw Error("shard_scan_limit_reached");
  const matching=shards.filter(shard=>shard.deck===deck);
  metrics.shards_scanned=matching.length;
  const unavailable=matching.length?"awaiting_cohort_approval":"no_warehouse_shards";
  const empty=(status)=>({schema:"gorge-r2-original-ui-batch-response-v1",
    population:"approved_current_decisive_only",deck,status,batch:null});
  if(!registry.cohorts.some(c=>c.status==="current"&&c.approved===true))
    return empty(unavailable);
  const selected=[], projected=[],fingerprints=new Map();
  const projectionUiHashes=new Set(),projectionSourceHashes=new Set();
  let missingProjection=false;
  for(const shard of matching) {
    const manifest=await readManifest(env.GORGE_R2,shard);
    const games=await readGames(env.GORGE_R2,shard,manifest);
    const approved=[];
    for(const game of games)
      if(await isApproved(game,registry,fingerprints))approved.push(game);
    if(!approved.length)continue;
    selected.push(...approved);
    const key=shard.manifestKey.slice(0,-"manifest.json".length)+"ui-original.v1.json";
    const object=await env.GORGE_R2.get(key);
    if(!object) {missingProjection=true;continue;}
    if(object.size>4*1024*1024)throw Error("oversized_original_ui_projection");
    const projection=await object.json();
    if(projection.schema!=="gorge-r2-original-ui-projection-v1"||
       projection.deck!==deck||projection.source_batch!==shard.batch||
       String(projection.shard)!==shard.shard||
       !Array.isArray(projection.games)||
       !/^[a-f0-9]{64}$/.test(projection.ui_deck_sha256||"")||
       !/^[a-f0-9]{64}$/.test(projection.source_deck_sha256||""))
      throw Error("unverified_original_ui_projection");
    // Never accept rows that are not approved, even when the R2 object
    // happens to contain experimental or historical game projections.
    const allowed=new Set(approved.map(g=>g.game_id));
    if(projection.games.some(g=>!allowed.has(g?.game_id)))
      throw Error("unapproved_original_ui_projection_game");
    projectionUiHashes.add(projection.ui_deck_sha256);
    projectionSourceHashes.add(projection.source_deck_sha256);
    projected.push(...projection.games);
  }
  if(!selected.length)return empty(unavailable);
  if(selected.length>200)throw Error("original_ui_batch_limit");
  if(missingProjection)return empty("projection_pending");
  if(projectionUiHashes.size!==1||projectionSourceHashes.size!==1)
    throw Error("mixed_original_ui_projection_revisions");
  const batch=originalUiBatch(selected,
    {schema:"gorge-r2-original-ui-projection-v1",deck,
      ui_deck_sha256:[...projectionUiHashes][0],
      source_deck_sha256:[...projectionSourceHashes][0],games:projected},deck);
  return {...empty("ready"),batch};
}


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
async function getMaterialized(env,deck,page=null) {
  const pointerObject=await env.GORGE_R2.get(MATERIALIZED_PREFIX+"current.json");
  if(!pointerObject)return null; // Existing source-backed legacy route stays available.
  if(pointerObject.size>1024)throw Error("oversized_materialized_pointer");
  const pointer=await pointerObject.json();
  if(pointer.schema!=="gorge-r2-results-current-v1" ||
     !/^[a-f0-9]{64}$/.test(pointer.version||"") ||
     !/^[a-f0-9]{64}$/.test(pointer.manifest_sha256||""))
    throw Error("invalid_materialized_pointer");
  const prefix=MATERIALIZED_PREFIX+"versions/"+pointer.version+"/";
  const manifest=await verifiedJson(env.GORGE_R2,prefix+"manifest.json",pointer.manifest_sha256);
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
  const target=page===null?entry.summary:entry.pages[page];
  if(!target || (page!==null && page>=entry.pages.length))
    return {schema:"gorge-r2-materialized-response-v1",deck,
      version:pointer.version,status:"page_not_found"};
  const path=page===null?"summary.json":"pages/"+String(page).padStart(6,"0")+".json";
  if(target.path!==path || !/^[a-f0-9]{64}$/.test(target.sha256||""))
    throw Error("invalid_materialized_object_reference");
  const payload=await verifiedJson(env.GORGE_R2,prefix+deck+"/"+path,target.sha256);
  if(payload.deck!==deck || (payload.cohort_version!==undefined &&
     payload.cohort_version!==pointer.version) ||
     (page===null && (payload.n!==entry.n || payload.wins!==entry.wins ||
       payload.losses!==entry.losses || payload.schema!=="gorge-r2-live-summary-v1")) ||
     (page!==null && (payload.schema!=="gorge-r2-materialized-page-v1" ||
       payload.version!==pointer.version||payload.page!==page||
       payload.total!==entry.n||payload.batch?.deck_sha256!==entry.ui_deck_sha256||
       payload.batch?.runs?.length!==target.count)))
    throw Error("materialized_payload_mismatch");
  return {schema:"gorge-r2-materialized-response-v1",deck,
    version:pointer.version,status:"ready",
    total:entry.n,page_count:entry.pages.length,
    ...(page===null?{summary:payload}:{page:payload})};
}

async function getApprovedGames(env,deck,limit,metrics,gameId=null,after=null) {
  const {shards,truncated}=await listShards(env.GORGE_R2);
  const matching=shards.filter(x=>x.deck===deck);
  metrics.shards_scanned=matching.length;
  metrics.list_truncated=truncated;
  if(truncated)throw Error("shard_scan_limit_reached");
  const approved=registry.cohorts.filter(c=>c.status==="current"&&c.approved===true);
  if(!approved.length)return gameId===null?
    {...approvedGameIndex([],deck,limit,after),
      status:matching.length?"awaiting_cohort_approval":"no_warehouse_shards",
      raw_shards_seen:matching.length}:
    {schema:"gorge-r2-approved-game-detail-v1",deck,
      population:"approved_current_decisive_only",game:null,
      status:matching.length?"awaiting_cohort_approval":"no_warehouse_shards"};
  const rows=[],fingerprints=new Map();
  for(const shard of matching) {
    const manifest=await readManifest(env.GORGE_R2,shard);
    const games=await readGames(env.GORGE_R2,shard,manifest);
    for(const game of games)
      if(await isApproved(game,registry,fingerprints))rows.push(game);
  }
  if(gameId!==null) {
    const game=approvedGameDetail(rows,deck,gameId);
    return {schema:"gorge-r2-approved-game-detail-response-v1",
      deck,population:"approved_current_decisive_only",game,
      status:game?"ready":"game_not_found",raw_shards_seen:matching.length};
  }
  return {...approvedGameIndex(rows,deck,limit,after),
    status:rows.length?"ready":"awaiting_cohort_approval",
    raw_shards_seen:matching.length};
}

export default {
  async fetch(request,env) {
    const started=now();
    if(request.method!=="GET")return fail(405,"method_not_allowed",started);
    const url=new URL(request.url);
    if(url.pathname==="/health")
      return json({ok:true,service:"gorge-r2-direct-api",schema:1,
        r2_binding:!!env.GORGE_R2},200,duration(started));
    if(url.pathname==="/v1/diagnostic/games" ||
       url.pathname.startsWith("/v1/diagnostic/games/")){
      const expected=env.BENCHMARK_TOKEN;
      if(!isDiagnosticAuthorized(request.headers.get("Authorization"),expected))
        return diagnosticJson({error:"diagnostic_not_authorized"},401);
      if(!env.GORGE_R2)return diagnosticJson({error:"r2_binding_missing"},503);
      const match=url.pathname.match(/^\/v1\/diagnostic\/games\/([^/]+?)\/timeline$/);
      if(url.pathname!=="/v1/diagnostic/games" && !match)
        return diagnosticJson({error:"not_found"},404);
      const deck=url.searchParams.get("deck");
      if(!DIAGNOSTIC_DECKS.has(deck))
        return diagnosticJson({error:"invalid_diagnostic_deck"},400);
      let gameId=null;
      if(match) {
        try{
          gameId=decodeURIComponent(match[1]);
          if(!/^[a-zA-Z0-9_.:/-]{1,200}$/.test(gameId))
            throw Error("invalid_game_id");
        }catch{return diagnosticJson({error:"invalid_game_id"},400);}
      }
      try{return diagnosticJson(await getDiagnosticGame(env,deck,gameId));}
      catch(err){
        console.error("Private experimental Gorge read failed:",String(err?.message||err));
        return diagnosticJson({error:"diagnostic_source_unavailable"},503);
      }
    }
    // Authenticated diagnostic only: time a REAL raw R2 ZSTD Parquet read
    // without returning source game data or granting statistical approval.
    if(url.pathname==="/v1/benchmark"){
      const token=env.BENCHMARK_TOKEN;
      if(!token || request.headers.get("Authorization")!==("Bearer "+token))
        return fail(401,"benchmark_not_authorized",started);
      if(!env.GORGE_R2)return fail(503,"r2_binding_missing",started);
      let selected;
      try { selected=validateDeck(url.searchParams.get("deck")); }
      catch {return fail(400,"invalid_deck",started);}
      try{
        const tList=now();
        const listing=await listShards(env.GORGE_R2);
        const listing_ms=duration(tList);
        if(listing.truncated)throw Error("too_many_shards");
        const shard=listing.shards.find(x=>x.deck===selected);
        if(!shard)return json({schema:"gorge-r2-benchmark-v1",deck:selected,
          status:"no_shards",list_ms:listing_ms},200,duration(started));
        const tManifest=now();
        const manifest=await readManifest(env.GORGE_R2,shard);
        const manifest_ms=duration(tManifest);
        const tRead=now();
        const rows=await readGames(env.GORGE_R2,shard,manifest);
        const parquet_ms=duration(tRead);
        return json({schema:"gorge-r2-benchmark-v1",deck:selected,
          status:"ok",rows_read:rows.length,source_batch:shard.batch,
          timing_ms:{listing:listing_ms,manifest:manifest_ms,
            parquet:parquet_ms,total:duration(started)}},200,duration(started));
      }catch(error){
        console.error("R2 benchmark failed:",String(error?.message||error));
        return fail(503,"benchmark_unavailable",started);
      }
    }
    const detailMatch=url.pathname.match(/^\/v1\/games\/([^/]+?)(\/timeline)?$/);
    if(url.pathname!=="/v1/summary" && url.pathname!=="/v1/ui/overview" && url.pathname!=="/v1/ui/batch" && url.pathname!=="/v1/ui/catalog" && url.pathname!=="/v1/ui/page" && url.pathname!=="/v1/games" && !detailMatch)
      return fail(404,"not_found",started);
    let gameId=null;
    if(detailMatch) {
      try {
        gameId=decodeURIComponent(detailMatch[1]);
        if(!/^[a-zA-Z0-9_.:/-]{1,200}$/.test(gameId))throw Error("invalid_game_id");
      }catch{return fail(400,"invalid_game_id",started);}
    }
    if(!env.GORGE_R2)return fail(503,"r2_binding_missing",started);
    let deck;
    try { deck=validateDeck(url.searchParams.get("deck")); }
    catch {return fail(400,"invalid_deck",started);}
    let limit=25,after=null;
    if(url.pathname==="/v1/games"){
      after=url.searchParams.get("cursor");
      if(after!==null && (after.length>200 || !/^[a-zA-Z0-9_.:/-]+$/.test(after)))
        return fail(400,"invalid_cursor",started);
      const rawLimit=url.searchParams.get("limit");
      if(rawLimit!==null){
        if(!/^(?:[1-9]|1[0-9]|2[0-5])$/.test(rawLimit))
          return fail(400,"invalid_limit",started);
        limit=Number(rawLimit);
      }
    }
    const metrics={};
    try{
      if(url.pathname==="/v1/ui/catalog" || url.pathname==="/v1/ui/page"){
        let page=null;
        if(url.pathname==="/v1/ui/page"){
          const raw=url.searchParams.get("page");
          if(raw===null||!/^(0|[1-9][0-9]{0,5})$/.test(raw))
            return fail(400,"invalid_page",started);
          page=Number(raw);
        }
        const materialized=await getMaterialized(env,deck,page);
        if(!materialized)return fail(404,"materialized_not_published",started);
        return json(materialized,materialized.status==="page_not_found"?404:200,duration(started));
      }
      const payload=url.pathname==="/v1/ui/batch"?
        await getOriginalUiBatch(env,deck,metrics):
        detailMatch?.[2]?await getApprovedTimeline(env,deck,gameId,metrics):
        (url.pathname==="/v1/games" || gameId!==null)?
        await getApprovedGames(env,deck,limit,metrics,gameId,after):
        await getSummary(env,deck,metrics);
      const projected=url.pathname==="/v1/ui/overview"?uiOverview(payload):payload;
      return json({...projected,query:{...metrics,server_ms:duration(started)}},200,duration(started));
    }catch(err){
      console.error("R2 approved query failed:",String(err?.message||err));
      return fail(503,"r2_query_unavailable",started);
    }
  }
};
