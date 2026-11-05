"use strict";
// Optional preview adapter: never receives R2 credentials or private source logs.
// Approved live endpoint; URL overrides are optional for preview diagnostics.
(function(){
  const query=new URLSearchParams(location.search);
  const candidate=query.get("r2Api")||window.GORGE_R2_API_BASE||
    "https://gorge-r2-direct-api-preview.darbosama.workers.dev";
  let api;
  try{
    api=new URL(candidate);
    if(api.protocol!=="https:" || !/^[a-z0-9-]+\.[a-z0-9-]+\.workers\.dev$/i.test(api.hostname))
      api=null;
  }catch{api=null;}
  if(!api)return;
  const root=document.getElementById("gorge-r2-live");
  if(!root)return;
  const el=(tag,cls,txt)=>{
    const n=document.createElement(tag);if(cls)n.className=cls;
    if(txt!==undefined)n.textContent=String(txt);return n;
  };
  const percent=x=>Number.isFinite(x)?(100*x).toFixed(1)+"%":"—";
  let deck="",seq=0;
  function render(result,latency){
    root.replaceChildren();
    const card=el("section","panel gorge-r2-live-panel");
    const heading=el("h3","panel-title","Live R2 results");
    const refreshButton=el("button","game-outcome-refresh","↻");
    refreshButton.type="button";
    refreshButton.setAttribute("aria-label","Refresh live R2 results");
    refreshButton.title="Refresh live R2 results";
    refreshButton.addEventListener("click",()=>refresh(true));
    const header=el("div","latest-results-topline");
    header.append(heading,refreshButton);
    const meta=el("p","micro","Direct R2 Parquet query · read-only API · "+latency+" ms browser round trip");
    card.append(header,meta);
    if(result.status==="awaiting_cohort_approval"){
      card.append(el("p","small","Recorded games are present in R2, but no current cohort has been approved for these statistics."));
      card.append(el("p","micro",result.raw_shards_seen+" source shards found · historical and experimental games remain excluded"));
    }else if(result.status==="no_warehouse_shards"){
      card.append(el("p","small","No R2 warehouse shards found for this player deck (the latest experimental smoke run may still be stored only as a GitHub artifact)."));
    }else if(result.n){
      card.append(el("p","small",result.n+" approved decisive games · "+result.wins+" wins · "+result.losses+" losses"));
      const bar=el("div","game-outcome-stacked-bar");
      bar.style.position="relative";
      bar.style.maxWidth="100%";
      bar.setAttribute("role","img");
      bar.setAttribute("aria-label",percent(result.win_rate)+" win rate; 25% four-player parity reference");
      const win=el("span","is-win");
      win.style.width=percent(result.win_rate);
      const loss=el("span","is-loss");
      loss.style.width=percent(1-result.win_rate);
      const parity=el("span","game-outcome-baseline");
      parity.title="25% · equal-chance four-player reference";
      bar.append(win,loss,parity);
      card.append(bar,el("p","micro",percent(result.win_rate)+" wins · expected even-pod reference 25%"));
      const details=el("details","board-report");
      details.append(el("summary",null,"Opponent matchups"));
      const list=el("div","small");
      for(const g of (result.groups?.opponents||[]).slice(0,15))
        list.append(el("p",null,(window.DeckDisplayNames?.deck(g.name)||g.name)+" · "+g.wins+"/"+g.n+" wins ("+percent(g.win_rate)+")"));
      details.append(list);card.append(details);
    }else card.append(el("p","small","No approved decisive games for this deck."));
    card.append(el("p","micro","Server processing: "+(result.query?.server_ms??"—")+" ms · "+(result.query?.shards_scanned??"—")+" shard(s) scanned"));
    root.append(card);
  }
  async function refresh(force=false){
    const selected=window.__deckLabActiveKey;
    if(!selected || (!force && selected===deck))return;
    deck=selected;const ticket=++seq;
    const started=performance.now();
    root.replaceChildren(el("p","micro","Querying approved R2 game records…"));
    const endpoint=new URL("/v1/summary",api);
    endpoint.searchParams.set("deck",selected);
    try{
      const response=await fetch(endpoint.toString(),{cache:"no-store"});
      if(!response.ok)throw Error("Worker returned HTTP "+response.status);
      const data=await response.json();
      if(ticket!==seq || data.deck!==selected || data.schema!=="gorge-r2-live-summary-v1")
        return;
      render(data,Math.round(performance.now()-started));
    }catch(err){
      if(ticket!==seq)return;
      inFlight=false;
      const message=el("p","micro","R2 live query unavailable; existing published UI remains available. "+String(err.message||err));
      const retry=el("button","game-outcome-refresh","Try again");
      retry.type="button";retry.addEventListener("click",()=>refresh(true));
      root.replaceChildren(message,retry);
    }
  }
  addEventListener("DOMContentLoaded",()=>{
    refresh();setTimeout(refresh,150);
    const existingRefresh=document.getElementById("game-outcome-refresh");
    existingRefresh?.addEventListener("click",()=>refresh(true));
    document.addEventListener("change",()=>setTimeout(refresh,0));
    document.addEventListener("click",()=>setTimeout(refresh,100));
    addEventListener("popstate",refresh);
  });
})();
