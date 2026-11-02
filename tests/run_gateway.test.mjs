import { test } from "node:test";
import assert from "node:assert/strict";
import worker from "../infra/simulation-gateway/worker.mjs";

const origin="https://bgoodnight.github.io";
const env={
  ALLOWED_ORIGIN:origin,
  RUN_PASSWORD:"test-password-a-long-and-random-one",
  GITHUB_TOKEN:"fake-test-token",
  ATTEMPT_LIMIT:{limit:async()=>({success:true})},
  RUN_LIMIT:{limit:async()=>({success:true})}
};
const payload={password:env.RUN_PASSWORD,deck:"necron_dynasties",scenario:"mixed",seeds:100,rounds:30,pilot_style:"adaptive",provisional_mode:"safe"};
function req(data,from=origin){
  return new Request("https://gateway.example/run",{
    method:"POST",headers:{Origin:from,"Content-Type":"application/json"},
    body:JSON.stringify(data)
  });
}
test("password, origin and settings validation prevent unauthorized dispatch",async()=>{
  const initial=globalThis.fetch;
  const calls=[];
  globalThis.fetch=async(url,options)=>{
    calls.push({url,options});return new Response(null,{status:204});
  };
  try{
    assert.equal((await worker.fetch(req({...payload,password:"guess"}),env)).status,401);
    assert.equal((await worker.fetch(req(payload,"https://example.invalid"),env)).status,403);
    assert.equal((await worker.fetch(req({...payload,seeds:9999}),env)).status,400);
    assert.equal(calls.length,0);
    const response=await worker.fetch(req(payload),env);
    assert.equal(response.status,202);
    assert.equal(calls.length,1);
    assert.equal(calls[0].url,"https://api.github.com/repos/bgoodnight/commander-simulator/actions/workflows/deep-simulations.yml/dispatches");
    const body=JSON.parse(calls[0].options.body);
    assert.equal(body.ref,"main");
    assert.deepEqual(body.inputs,{
      deck:"necron_dynasties",scenario:"mixed",pilot_style:"adaptive",
      provisional_mode:"safe",seeds:"100",rounds:"30",start_seed:"0"
    });
    assert.ok(!calls[0].options.body.includes(payload.password));
    assert.ok(!JSON.stringify(await response.json()).includes(env.GITHUB_TOKEN));
  }finally{globalThis.fetch=initial;}
});
test("only approved origin receives preflight permission",async()=>{
  const make=o=>new Request("https://gateway.example/run",{method:"OPTIONS",headers:{Origin:o}});
  const allowed=await worker.fetch(make(origin),env);
  assert.equal(allowed.status,204);
  assert.equal(allowed.headers.get("Access-Control-Allow-Origin"),origin);
  assert.equal((await worker.fetch(make("https://evil.invalid"),env)).status,403);
});
test("missing secrets and rate limits block dispatch",async()=>{
  assert.equal((await worker.fetch(req(payload),{...env,GITHUB_TOKEN:""})).status,503);
  assert.equal((await worker.fetch(req(payload),{...env,ATTEMPT_LIMIT:{limit:async()=>({success:false})}})).status,429);
  assert.equal((await worker.fetch(req(payload),{...env,RUN_LIMIT:{limit:async()=>({success:false})}})).status,429);
});
