import { parquetReadObjects, parquetMetadataAsync, parquetSchema } from "hyparquet";
import { compressors } from "hyparquet-compressors";
import registry from "../../data/gorge_analytics_cohort_registry_v1.json";
import { aggregate, isApproved, validateDeck, normalizeRow, approvedGameIndex, approvedGameDetail, approvedEventSegments } from "./core.mjs";

// Read-only Cloudflare Worker. The R2 binding has no credentials in JS or HTML.
// Never return native logs, intents, event_json, object catalog, or hidden zones.
const PREFIX="warehouse/v1/";
const MAX_SHARDS=40;
const MAX_OBJECT_SIZE=16*1024*1024;  // initial latency/memory guardrail
const ORIGIN="https://bgoodnight.github.io";
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
      "opponent_panel_sha256","oracle_bulk_sha256","simulation_protocol_sha256"];
  const rows=(await parquetReadObjects({file,compressors,
    columns:requested.filter(key=>columnsAvailable.has(key))})).map(normalizeRow);
  if(rows.length!==manifest.files["games.parquet"].rows)
    throw Error("parquet_row_count_mismatch");
  return rows;
}

// Events are private omniscient data. Read only a bounded set of safe columns,
// and only after game + cohort approval. Never request event_json or object IDs.
async function readEventSegments(bucket,shard,manifest,gameId) {
  const expected=manifest.files?.["events.parquet"];
  if(!expected || !Number.isInteger(expected.rows) || expected.rows>100000)
    throw Error("event_count_limit");
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
  const rows=(await parquetReadObjects({file,compressors,columns:required}))
    .map(row=>({
      game_id:row.game_id,
      seq:typeof row.seq==="bigint"?Number(row.seq):row.seq,
      kind_id:typeof row.kind_id==="bigint"?Number(row.kind_id):row.kind_id,
      secret:row.secret
    }));
  if(rows.length!==expected.rows)throw Error("event_row_count_mismatch");
  return approvedEventSegments(rows,gameId);
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
      const segments=await readEventSegments(env.GORGE_R2,shard,manifest,gameId);
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
async function getApprovedGames(env,deck,limit,metrics,gameId=null) {
  const {shards,truncated}=await listShards(env.GORGE_R2);
  const matching=shards.filter(x=>x.deck===deck);
  metrics.shards_scanned=matching.length;
  metrics.list_truncated=truncated;
  if(truncated)throw Error("shard_scan_limit_reached");
  const approved=registry.cohorts.filter(c=>c.status==="current"&&c.approved===true);
  if(!approved.length)return gameId===null?
    {...approvedGameIndex([],deck,limit),
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
  return {...approvedGameIndex(rows,deck,limit),
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
    if(url.pathname!=="/v1/summary" && url.pathname!=="/v1/games" && !detailMatch)
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
    let limit=20;
    if(url.pathname==="/v1/games"){
      const rawLimit=url.searchParams.get("limit");
      if(rawLimit!==null){
        if(!/^(?:[1-9]|1[0-9]|2[0-5])$/.test(rawLimit))
          return fail(400,"invalid_limit",started);
        limit=Number(rawLimit);
      }
    }
    const metrics={};
    try{
      const payload=detailMatch?.[2]?await getApprovedTimeline(env,deck,gameId,metrics):
        (url.pathname==="/v1/games" || gameId!==null)?
        await getApprovedGames(env,deck,limit,metrics,gameId):
        await getSummary(env,deck,metrics);
      return json({...payload,query:{...metrics,server_ms:duration(started)}},200,duration(started));
    }catch(err){
      console.error("R2 approved query failed:",String(err?.message||err));
      return fail(503,"r2_query_unavailable",started);
    }
  }
};
