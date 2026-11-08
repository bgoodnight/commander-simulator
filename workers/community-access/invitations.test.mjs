import test from "node:test";
import assert from "node:assert/strict";
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import { submitInvitation, reviewInvitation, listInvitations } from "./invitations.mjs";
import intake from "../invitation-intake/index.mjs";

function db(){
  const sql=new DatabaseSync(":memory:");
  sql.exec(readFileSync(new URL("./migrations/0002_invitation_requests.sql",import.meta.url),"utf8"));
  return {
    sql,
    prepare(query){
      const statement=sql.prepare(query);
      let args=[];
      const queryObj={
        bind(...values){args=values;return queryObj;},
        async run(){return {meta:{changes:statement.run(...args).changes}};},
        async all(){return {results:statement.all(...args)};}
      };
      return queryObj;
    }
  };
}
const admin={role:"owner",subject:"access:owner"};
const user={role:"member",subject:"access:guest"};
test("request intake deduplicates by normalized email without revealing status",async()=>{
  const storage=db();
  assert.deepEqual(await submitInvitation(storage,{email:"FOO@Example.com",display_name:"Friend"}),{received:true});
  assert.deepEqual(await submitInvitation(storage,{email:"foo@example.com"}),{received:true});
  const count=storage.sql.prepare("SELECT count(*) AS n FROM invitation_requests").get().n;
  assert.equal(count,1);
  const records=await listInvitations(storage,admin);
  assert.equal(records[0].email,"foo@example.com");
  await assert.rejects(submitInvitation(storage,{email:"invalid"}),/invalid_email/);
  await assert.rejects(listInvitations(storage,user),/forbidden/);
});
test("review is one-way pending to declined or needs manual Cloudflare allowlist",async()=>{
  const storage=db();
  await submitInvitation(storage,{email:"foo@example.com"});
  const id=storage.sql.prepare("SELECT id FROM invitation_requests").get().id;
  await assert.rejects(reviewInvitation(storage,user,id,"declined"),/forbidden/);
  await assert.rejects(reviewInvitation(storage,admin,id,"active"),/invalid_review_status/);
  assert.deepEqual(await reviewInvitation(storage,admin,id,"awaiting_access_allowlist"),{
    id,status:"awaiting_access_allowlist",cloudflare_allowlist_updated:false
  });
  await assert.rejects(reviewInvitation(storage,admin,id,"declined"),/not_pending/);
});
test("public intake fails closed without Turnstile and origin",async()=>{
  const e={REQUEST_DB:db(),ENABLE_INVITATION_INTAKE:"true",TURNSTILE_SECRET_KEY:"test",
    REQUEST_FORM_ORIGIN:"https://site.example",REQUEST_FORM_HOSTNAME:"site.example"};
  const req=origin=>new Request("https://api.example/request-invitation",{
    method:"POST",headers:{"content-type":"application/json","origin":origin},
    body:JSON.stringify({email:"foo@example.com",turnstile_token:"token-1234567890"})
  });
  assert.equal((await intake.fetch(req("https://site.example"),{...e,TURNSTILE_SECRET_KEY:null})).status,503);
  assert.equal((await intake.fetch(req("https://other.example"),e)).status,403);
});
test("Turnstile hostname and challenge result must both match",async()=>{
  const e={REQUEST_DB:db(),ENABLE_INVITATION_INTAKE:"true",TURNSTILE_SECRET_KEY:"test",
    REQUEST_FORM_ORIGIN:"https://site.example",REQUEST_FORM_HOSTNAME:"site.example"};
  const request=()=>new Request("https://api.example/request-invitation",{
    method:"POST",headers:{"content-type":"application/json","origin":"https://site.example"},
    body:JSON.stringify({email:"test@example.com",turnstile_token:"token-1234567890"})
  });
  const oldFetch=globalThis.fetch;
  try{
    globalThis.fetch=async()=>new Response(JSON.stringify({success:true,hostname:"another.example"}),{status:200});
    assert.equal((await intake.fetch(request(),e)).status,403);
    globalThis.fetch=async()=>new Response(JSON.stringify({success:true,hostname:"site.example"}),{status:200});
    const r=await intake.fetch(request(),e);
    assert.equal(r.status,202);
    assert.deepEqual(await r.json(),{received:true});
    assert.equal(e.REQUEST_DB.sql.prepare("SELECT count(*) AS n FROM invitation_requests").get().n,1);
  }finally{globalThis.fetch=oldFetch;}
});
