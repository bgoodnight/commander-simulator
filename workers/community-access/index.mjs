import { resolveAccount, canRunSimulations } from "./permissions.mjs";
import {
  ApiError, createDeck, getPrivateDeck, updateDeck, listPrivateDecks,
  publishDeck, replacePublication, unpublish, getListedPublication,
  listPublications, copyPublication
} from "./store.mjs";
import { listInvitations, reviewInvitation } from "./invitations.mjs";

// Development-only Worker; Access protects ALL routes. No external deployment
// or mutations to the current Results Worker.
const json=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{
  "content-type":"application/json; charset=utf-8",
  "cache-control":"private, no-store",
  "x-content-type-options":"nosniff","vary":"Cookie"
}});
const idPattern="([a-zA-Z0-9_-]{1,100})";
async function bodyJson(request) {
  if(Number(request.headers.get("content-length"))>110_000)
    throw new ApiError(413,"request_too_large");
  const raw=await request.text();
  if(new TextEncoder().encode(raw).length>110_000)
    throw new ApiError(413,"request_too_large");
  try {return JSON.parse(raw);} catch {throw new ApiError(400,"invalid_json");}
}
export default {
  async fetch(request,env,ctx) {
    const url=new URL(request.url),path=url.pathname,method=request.method;
    if(!["GET","POST","PUT","PATCH","DELETE"].includes(method))
      return json({error:"method_not_allowed"},405);
    if(env.ENABLE_COMMUNITY_ACCESS!=="true"||!ctx?.access)
      return json({error:"access_not_configured"},403);
    let identity;
    try {identity=await ctx.access.getIdentity();}
    catch {return json({error:"invalid_access_identity"},403);}
    const account=resolveAccount(identity,env);
    if(!account)return json({error:"identity_required"},403);
    if(method==="GET"&&path==="/v1/account/me")
      return json({account,permissions:{run_simulations:canRunSimulations(account)}});
    if(method==="POST"&&path==="/v1/simulations")
      return canRunSimulations(account)
        ?json({error:"simulation_dispatch_not_implemented"},501)
        :json({error:"forbidden"},403);
    // Previous direct visibility toggle intentionally removed.
    if(method==="PATCH"&&/\/visibility$/.test(path))
      return json({error:"visibility_toggle_retired_use_publish_snapshot"},410);
    if(!env.COMMUNITY_DB||!env.COMMUNITY_DECKS_R2)
      return json({error:"deck_storage_not_configured"},503);
    if(method!=="GET"&&request.headers.get("origin")!==url.origin)
      return json({error:"origin_forbidden"},403);
    try {
      if(method==="GET"&&path==="/v1/admin/invitations")
        return json({requests:await listInvitations(env.COMMUNITY_DB,account)});
      const review=path.match(/^\/v1\/admin\/invitations\/([a-z0-9-]{36})\/review$/);
      if(method==="POST"&&review) {
        const body=await bodyJson(request);
        if(!body||Object.keys(body).length!==1)
          return json({error:"invalid_review_request"},400);
        return json({request:await reviewInvitation(env.COMMUNITY_DB,account,review[1],body.status)});
      }
      if(method==="GET"&&path==="/v1/decks")
        return json({decks:await listPrivateDecks(env,account)});
      if(method==="POST"&&path==="/v1/decks")
        return json({deck:await createDeck(env,account,await bodyJson(request))},201);
      if(method==="GET"&&["/v1/publications","/v1/decks/community"].includes(path))
        return json({publications:await listPublications(env)});
      const privateDeck=path.match(new RegExp("^/v1/decks/"+idPattern+"$"));
      if(privateDeck&&method==="GET")
        return json({deck:await getPrivateDeck(env,account,privateDeck[1])});
      if(privateDeck&&method==="PUT")
        return json({deck:await updateDeck(env,account,privateDeck[1],await bodyJson(request))});
      const publish=path.match(new RegExp("^/v1/decks/"+idPattern+"/publications$"));
      if(publish&&method==="POST")
        return json({publication:await publishDeck(env,account,publish[1])},201);
      const publication=path.match(new RegExp("^/v1/publications/"+idPattern+"$"));
      if(publication&&method==="GET")
        return json({publication:await getListedPublication(env,publication[1])});
      const replace=path.match(new RegExp("^/v1/publications/"+idPattern+"/replace$"));
      if(replace&&method==="POST")
        return json({publication:await replacePublication(env,account,replace[1],await bodyJson(request))});
      const unlist=path.match(new RegExp("^/v1/publications/"+idPattern+"/unpublish$"));
      if(unlist&&method==="POST")
        return json({publication:await unpublish(env,account,unlist[1])});
      const copy=path.match(new RegExp("^/v1/publications/"+idPattern+"/copy$"));
      if(copy&&method==="POST")
        return json({deck:await copyPublication(env,account,copy[1])},201);
      return json({error:"not_found"},404);
    }catch(e){
      if(e instanceof ApiError)return json({error:e.code},e.status);
      // Keep DB details, object keys, and stack traces out of public responses.
      return json({error:"storage_operation_failed"},503);
    }
  }
};
