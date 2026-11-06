import test from "node:test";
import assert from "node:assert/strict";
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import worker from "./index.mjs";
import { sha256 } from "./store.mjs";

const migration=readFileSync(new URL("./migrations/0001_deck_visibility.sql",import.meta.url),"utf8");
const baseEnv={ENABLE_COMMUNITY_ACCESS:"true",ACCESS_OWNER_EMAILS:"owner@example.test"};
const context=(email,id=email)=>({access:{getIdentity:async()=>({email,id})}});
const alice=context("owner@example.test","alice");
const bob=context("bob@example.test","bob");
const req=(path,method="GET",body,origin="https://api.test")=>new Request("https://api.test"+path,{
  method,...(method==="GET"?{}:{headers:{origin,"content-type":"application/json"},
  ...(body!==undefined?{body:JSON.stringify(body)}:{})})
});
async function call(env,who,path,method="GET",body,origin) {
  const r=await worker.fetch(req(path,method,body,origin),env,who);
  return {status:r.status,data:await r.json()};
}
function makeD1(){
  const sql=new DatabaseSync(":memory:");
  sql.exec(migration);
  const prepare=(query)=>{
    let args=[];
    const stmt=sql.prepare(query);
    const prepared={
      bind(...values){args=values;return prepared;},
      async first(){return stmt.get(...args)||null;},
      async all(){return {results:stmt.all(...args)};},
      async run(){const x=stmt.run(...args);return {meta:{changes:x.changes}};}
    };
    return prepared;
  };
  return {
    prepare,
    async batch(statements){
      sql.exec("BEGIN");
      try{
        const r=[];
        for(const statement of statements)r.push(await statement.run());
        sql.exec("COMMIT");return r;
      }catch(e){sql.exec("ROLLBACK");throw e;}
    },
    sql
  };
}
function makeR2(){
  const objects=new Map();
  return {
    objects,
    async head(key){return objects.has(key)?{key}:null;},
    async put(key,text){objects.set(key,text);return {key};},
    async get(key){return objects.has(key)?{text:async()=>objects.get(key)}:null;}
  };
}
const env=()=>({...baseEnv,COMMUNITY_DB:makeD1(),COMMUNITY_DECKS_R2:makeR2()});
const draft=(label,card="Sol Ring")=>({label,decklist:"1 "+card+"\n99 Swamp"});
async function newDeck(e,who=alice,label="Magnus",card="Sol Ring"){
  const result=await call(e,who,"/v1/decks","POST",draft(label,card));
  assert.equal(result.status,201,JSON.stringify(result.data));
  return result.data.deck;
}
test("Access fails closed even if storage bindings exist",async()=>{
  const e=env();
  assert.equal((await worker.fetch(req("/v1/decks"),e,{})).status,403);
  assert.equal((await call({...e,ENABLE_COMMUNITY_ACCESS:"false"},alice,"/v1/decks")).status,403);
  assert.equal((await call({...baseEnv,COMMUNITY_DB:e.COMMUNITY_DB},alice,"/v1/decks")).status,503);
  assert.equal((await call(e,bob,"/v1/decks","POST",draft("Bad"),"https://bad.example")).status,403);
});
test("private deck storage persists and never leaks to other accounts",async()=>{
  const e=env(),d=await newDeck(e);
  assert.equal(e.COMMUNITY_DECKS_R2.objects.size,1);
  const owner=await call(e,alice,"/v1/decks/"+d.id);
  assert.equal(owner.status,200);assert.equal(owner.data.deck.decklist,draft("Magnus").decklist);
  assert.equal((await call(e,bob,"/v1/decks/"+d.id)).status,404);
  const bobList=await call(e,bob,"/v1/decks");
  assert.deepEqual(bobList.data.decks,[]);
  const e2=await call(e,alice,"/v1/decks");
  assert.equal(e2.data.decks[0].id,d.id);
  assert.ok(!JSON.stringify(e2).includes("private_content_key"));
  assert.equal((await call(e,alice,"/v1/decks","POST",{label:"x",decklist:""})).status,400);
});
test("private edits reject stale revisions and bad source hashes",async()=>{
  const e=env(),d=await newDeck(e);
  let r=await call(e,alice,"/v1/decks/"+d.id,"PUT",{
    ...draft("Magnus upgraded","Arcane Signet"),expected_revision:1
  });
  assert.equal(r.status,200);assert.equal(r.data.deck.revision,2);
  r=await call(e,alice,"/v1/decks/"+d.id,"PUT",{
    ...draft("overwritten"),expected_revision:1
  });
  assert.equal(r.status,409);
  assert.equal((await call(e,bob,"/v1/decks/"+d.id,"PUT",{
    ...draft("stolen"),expected_revision:2
  })).status,404);
  const key=e.COMMUNITY_DB.sql.prepare("SELECT private_content_key FROM decks WHERE id=?").get(d.id).private_content_key;
  e.COMMUNITY_DECKS_R2.objects.set(key,"TAMPERED");
  assert.equal((await call(e,alice,"/v1/decks/"+d.id)).status,503);
});
test("publication and replacement preserve original revisions and exact content hashes",async()=>{
  const e=env(),d=await newDeck(e);
  let r=await call(e,alice,"/v1/decks/"+d.id+"/publications","POST");
  assert.equal(r.status,201,JSON.stringify(r.data));
  const pub=r.data.publication;
  assert.equal(pub.content_sha256,await sha256(draft("Magnus").decklist));
  const before=await call(e,bob,"/v1/publications/"+pub.id);
  assert.equal(before.status,200);
  assert.equal(before.data.publication.decklist,draft("Magnus").decklist);
  assert.equal((await call(e,bob,"/v1/publications")).data.publications.length,1);
  const changed=await call(e,alice,"/v1/decks/"+d.id,"PUT",{
    ...draft("Magnus v2","Arcane Signet"),expected_revision:1
  });
  assert.equal(changed.status,200);
  const previous=await call(e,bob,"/v1/publications/"+pub.id);
  assert.equal(previous.data.publication.content_sha256,pub.content_sha256);
  r=await call(e,alice,"/v1/publications/"+pub.id+"/replace","POST",{
    source_deck_id:d.id,expected_revision_id:pub.current_revision_id
  });
  assert.equal(r.status,200,JSON.stringify(r.data));
  assert.equal(r.data.publication.revision_no,2);
  assert.notEqual(r.data.publication.content_sha256,pub.content_sha256);
  assert.equal((await call(e,alice,"/v1/publications/"+pub.id+"/replace","POST",{
    source_deck_id:d.id,expected_revision_id:pub.current_revision_id
  })).status,409);
  const revisions=e.COMMUNITY_DB.sql.prepare(
    "SELECT revision_no,content_sha256 FROM publication_revisions WHERE publication_id=? ORDER BY revision_no"
  ).all(pub.id);
  assert.equal(revisions.length,2);
  assert.equal(revisions[0].content_sha256,pub.content_sha256);
  assert.equal((await call(e,bob,"/v1/publications/"+pub.id)).data.publication.decklist,
    draft("Magnus v2","Arcane Signet").decklist);
  assert.equal((await call(e,bob,"/v1/decks/"+d.id)).status,404);
});
test("unpublish hides from community but preserves revisions, and copy is independent",async()=>{
  const e=env(),d=await newDeck(e),p=(await call(e,alice,"/v1/decks/"+d.id+"/publications","POST")).data.publication;
  assert.equal((await call(e,bob,"/v1/publications/"+p.id+"/unpublish","POST")).status,404);
  const copied=await call(e,bob,"/v1/publications/"+p.id+"/copy","POST");
  assert.equal(copied.status,201,JSON.stringify(copied.data));
  const copy=copied.data.deck;
  assert.equal((await call(e,bob,"/v1/decks/"+copy.id)).status,200);
  const provenance=e.COMMUNITY_DB.sql.prepare("SELECT source_publication_revision_id FROM decks WHERE id=?").get(copy.id);
  assert.equal(provenance.source_publication_revision_id,p.current_revision_id);
  const unlisted=await call(e,alice,"/v1/publications/"+p.id+"/unpublish","POST");
  assert.equal(unlisted.status,200);
  assert.equal((await call(e,bob,"/v1/publications/"+p.id)).status,404);
  assert.equal((await call(e,bob,"/v1/publications/"+p.id+"/copy","POST")).status,404);
  assert.equal((await call(e,bob,"/v1/publications")).data.publications.length,0);
  assert.equal((await call(e,bob,"/v1/decks/"+copy.id)).status,200);
  assert.equal(e.COMMUNITY_DB.sql.prepare(
    "SELECT count(*) AS n FROM publication_revisions WHERE publication_id=?"
  ).get(p.id).n,1);
});
test("invalid cross-origin and disabled simulation mutations",async()=>{
  const e=env();
  assert.equal((await call(e,alice,"/v1/decks","POST",draft("X"),"https://evil.test")).status,403);
  assert.equal((await call(e,alice,"/v1/simulations","POST")).status,501);
  assert.equal((await call(e,bob,"/v1/simulations","POST")).status,403);
  assert.equal((await call(e,alice,"/v1/decks/magnus/visibility","PATCH",{visibility:"community"})).status,410);
});
