/**
 * Password-gated workflow dispatch. Never include secrets in the Pages bundle.
 * Both RUN_PASSWORD and GITHUB_TOKEN are Cloudflare encrypted secrets.
 */
const REPO="bgoodnight/commander-simulator";
const WORKFLOW="deep-simulations.yml";
const DECKS=new Set(["magnus_premium","magnus_budget","magnus_physical_trial","mortarion_current","mortarion_ideal","mortarion_physical_final","necron_dynasties","wretched_ranks"]);
const SCENARIOS=new Set(["balanced","aggressive","control","combo","mixed"]);
const STYLES=new Set(["adaptive","balanced","engine","tempo","conservative"]);
const MODES=new Set(["off","safe"]);
const encoder=new TextEncoder();
function reply(data,status,origin){
  const headers={"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store","X-Content-Type-Options":"nosniff","Vary":"Origin"};
  if(origin)headers["Access-Control-Allow-Origin"]=origin;
  return new Response(JSON.stringify(data),{status,headers});
}
async function equalSecret(input,configured){
  const [left,right]=await Promise.all([
    crypto.subtle.digest("SHA-256",encoder.encode(input)),
    crypto.subtle.digest("SHA-256",encoder.encode(configured))
  ]);
  let difference=0;
  const a=new Uint8Array(left),b=new Uint8Array(right);
  for(let i=0;i<a.length;i++)difference|=a[i]^b[i];
  return difference===0;
}
function validatedSettings(body){
  const deck=body.deck,scenario=body.scenario;
  const style=body.pilot_style??"adaptive",mode=body.provisional_mode??"safe";
  const seeds=body.seeds??100,rounds=body.rounds??30,start=body.start_seed??0;
  if(!DECKS.has(deck)||!SCENARIOS.has(scenario)||!STYLES.has(style)||!MODES.has(mode)
    ||!Number.isInteger(seeds)||seeds<1||seeds>200
    ||!Number.isInteger(rounds)||rounds<1||rounds>30
    ||!Number.isInteger(start)||start<0||start>10000000)return null;
  return {deck,scenario,pilot_style:style,provisional_mode:mode,
    seeds:String(seeds),rounds:String(rounds),start_seed:String(start)};
}
export default {
  async fetch(request,env){
    const origin=request.headers.get("Origin");
    const allowedOrigin=env.ALLOWED_ORIGIN;
    if(!allowedOrigin||origin!==allowedOrigin)
      return reply({error:"Origin not allowed."},403,null);
    if(new URL(request.url).pathname!=="/run")
      return reply({error:"Not found."},404,allowedOrigin);
    if(request.method==="OPTIONS")
      return new Response(null,{status:204,headers:{
        "Access-Control-Allow-Origin":allowedOrigin,
        "Access-Control-Allow-Methods":"POST, OPTIONS",
        "Access-Control-Allow-Headers":"Content-Type",
        "Access-Control-Max-Age":"600",
        "Cache-Control":"no-store","Vary":"Origin"
      }});
    if(request.method!=="POST")
      return reply({error:"Method not allowed."},405,allowedOrigin);
    if(!env.RUN_PASSWORD||env.RUN_PASSWORD.length<16||!env.GITHUB_TOKEN||!env.ATTEMPT_LIMIT||!env.RUN_LIMIT)
      return reply({error:"Simulation service not configured."},503,allowedOrigin);
    if(!request.headers.get("Content-Type")?.startsWith("application/json"))
      return reply({error:"Expected JSON."},415,allowedOrigin);
    if(Number(request.headers.get("Content-Length")||0)>2048)
      return reply({error:"Request too large."},413,allowedOrigin);
    const attempt=await env.ATTEMPT_LIMIT.limit({key:request.headers.get("CF-Connecting-IP")||"unknown"});
    if(!attempt.success)
      return reply({error:"Too many attempts; try later."},429,allowedOrigin);
    let body;
    try{
      const raw=await request.text();
      if(raw.length>2048)return reply({error:"Request too large."},413,allowedOrigin);
      body=JSON.parse(raw);
    }catch{return reply({error:"Invalid JSON."},400,allowedOrigin);}
    if(!body||Array.isArray(body)||typeof body!=="object"||typeof body.password!=="string"
      ||body.password.length>256||!(await equalSecret(body.password,env.RUN_PASSWORD)))
      return reply({error:"Invalid password."},401,allowedOrigin);
    const inputs=validatedSettings(body);
    if(!inputs)return reply({error:"Invalid simulation settings."},400,allowedOrigin);
    const allowed=await env.RUN_LIMIT.limit({key:"shared-deck-lab"});
    if(!allowed.success)
      return reply({error:"Too many new simulations; try later."},429,allowedOrigin);
    const upstream=await fetch(
      "https://api.github.com/repos/"+REPO+"/actions/workflows/"+WORKFLOW+"/dispatches",
      {method:"POST",headers:{
        Authorization:"Bearer "+env.GITHUB_TOKEN,
        Accept:"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
        "User-Agent":"commander-simulator-gateway",
        "Content-Type":"application/json"
      },body:JSON.stringify({ref:"main",inputs})}
    ).catch(()=>null);
    if(!upstream?.ok)return reply({error:"Could not queue simulation."},502,allowedOrigin);
    return reply({
      status:"queued",
      message:"GitHub Actions accepted the request. Results publish after validation.",
      workflow_url:"https://github.com/"+REPO+"/actions/workflows/"+WORKFLOW
    },202,allowedOrigin);
  }
};