"use strict";
const fs=require("node:fs"),path=require("node:path");
const adapter=require("../web/pages/gorge_legacy_adapter.js");
const renderer=require("../web/pages/game_outcomes.js");
const data=JSON.parse(fs.readFileSync(process.argv[2],"utf8")),out=process.argv[3];
for(const [key,entry] of Object.entries(data)){
  const games=entry.games.map(({replay,winner})=>{
    if(!adapter.validateReplay(replay)||adapter.realWinner(replay)!==winner)
      throw Error("Replay or winner mismatch");
    return replay;
  });
  const batch=adapter.adapt(games,key,{[key]:entry.sha});
  if(!batch||!renderer.validate(batch)||batch.runs.length!==4)throw Error("Invalid preview batch");
  fs.writeFileSync(path.join(out,key+"-preliminary.json"),JSON.stringify(batch)+"\n");
}
