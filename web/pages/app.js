/* Commander Deck Lab — standalone static frontend, no framework.
 * Original audio cues generated with Web Audio; no borrowed game sound files.
 * No simulation logic is executed: all observation traces come from Python.
 */
"use strict";
const $ = id => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";
const BASIC = new Set(["Plains","Island","Swamp","Mountain","Forest","Wastes",
  "Snow-Covered Plains","Snow-Covered Island","Snow-Covered Swamp",
  "Snow-Covered Mountain","Snow-Covered Forest"]);
const LABELS = {
  magnus_premium:"Magnus · Premium",magnus_budget:"Magnus · Budget",
  wretched_ranks:"Wretched Ranks · Gisa",
  mortarion_current:"Mortarion · Current",mortarion_ideal:"Mortarion · Ideal",
  necron_dynasties:"Necron Dynasties"
};
const MODE_NOTE = "Precomputed observation only · no spells, abilities, combat or win rates modeled.";
let data=null, archives=null, allNames=[], selected=null, activeTab="overview";
let cachedByName = new Map(),extraCards={},activeCounts=null,history=[],localVersions=[];
let selectedSeed="0",soundEnabled=false,audio=null,lastRecord=null,autoTimer=null;
let selectedVersionId=null,preferredByCommander={},lastCommanderId=null;
const pageName=location.pathname.endsWith("/summary.html")?"summary":
  location.pathname.endsWith("/editor.html")?"editor":"results";
const PAGE_INFO={
  results:["The Archive of Outcomes","Study cached opening turns, then descend through a visual chronicle of the selected seed."],
  summary:["The Commander's Ledger","Inspect commander art, card-type composition and the mana curve of this verified deck."],
  editor:["The Decksmith's Forge","Search the card list, make validated browser-local changes and export a new decklist."]
};
let scrollObserver=null;
const storageKey="commander-deck-lab-pages-v1";
const el=(tag,text,className)=>{
  const node=document.createElement(tag);
  if(text!==undefined&&text!==null)node.textContent=String(text);
  if(className)node.className=className;
  return node;
};
function clear(node){if(node)node.replaceChildren();}
function note(msg,error=false){
  const status=$("toast");
  status.textContent=msg;status.hidden=false;
  status.style.borderColor=error?"#d9a196":"#dabb80";
  clearTimeout(note._timeout);
  note._timeout=setTimeout(()=>status.hidden=true,4100);
}
function originalSound(kind="click"){
  if(!soundEnabled)return;
  try{
    const Audio=window.AudioContext||window.webkitAudioContext;
    if(!Audio)return;
    if(!audio)audio=new Audio();
    if(audio.state==="suspended")audio.resume();
    const now=audio.currentTime;
    const notes={
      click:[[370,.06,.045],[555,.08,.025]],
      summon:[[174,.18,.12],[260,.3,.14],[392,.45,.09]],
      success:[[392,.12,.07],[494,.16,.07],[660,.22,.07]],
      error:[[147,.11,.08],[131,.14,.05]],
      page:[[240,.055,.03],[340,.09,.02]]
    };
    for(const [freq,duration,volume] of (notes[kind]||notes.click)){
      const osc=audio.createOscillator(),gain=audio.createGain();
      osc.type=kind==="summon"?"sine":"triangle";
      osc.frequency.setValueAtTime(freq,now);
      osc.frequency.exponentialRampToValueAtTime(Math.max(40,freq*.93),now+duration);
      gain.gain.setValueAtTime(.001,now);
      gain.gain.exponentialRampToValueAtTime(volume,now+.012);
      gain.gain.exponentialRampToValueAtTime(.001,now+duration);
      osc.connect(gain).connect(audio.destination);
      osc.start(now);osc.stop(now+duration+.015);
    }
  }catch(e){soundEnabled=false;$("audio-toggle").textContent="♫ Sound unavailable";}
}
function enableSound(){
  soundEnabled=!soundEnabled;
  $("audio-toggle").setAttribute("aria-pressed",String(soundEnabled));
  $("audio-toggle").textContent=soundEnabled?"♫ Sound on":"♫ Sound off";
  if(soundEnabled)originalSound("success");
}
function safeText(value){return String(value??"");}
function cardInfo(name){
  return cachedByName.get(name.toLowerCase())||null;
}
function cardForId(id){return extraCards[id]||data.cards[id]||null;}
function addAliases(item){
  if(!item||!item.oracle_id)return;
  cachedByName.set(item.name.toLowerCase(),item);
  for(const face of item.face_names||[])cachedByName.set(face.toLowerCase(),item);
}
function loadLocal(){
  try{
    const stored=JSON.parse(localStorage.getItem(storageKey)||"{}");
    if(stored&&typeof stored==="object"){
      const arr=Array.isArray(stored.versions)?stored.versions:[];
      localVersions=arr.filter(v=>v&&typeof v.id==="string"&&
        typeof v.baseKey==="string"&&v.counts&&typeof v.counts==="object").slice(0,60);
      preferredByCommander=stored.preferredByCommander&&typeof stored.preferredByCommander==="object"?
        stored.preferredByCommander:{};
      lastCommanderId=typeof stored.lastCommanderId==="string"?stored.lastCommanderId:null;
      if(stored.extraCards&&typeof stored.extraCards==="object"){
        for(const item of Object.values(stored.extraCards)){
          if(item&&typeof item.name==="string"&&typeof item.oracle_id==="string"&&
              Array.isArray(item.color_identity)){
            extraCards[item.oracle_id]=item;addAliases(item);
          }
        }
      }
    }
  }catch(e){localVersions=[];extraCards={};}
}
function persist(){
  try{localStorage.setItem(storageKey,JSON.stringify({
    versions:localVersions.slice(0,60),preferredByCommander,lastCommanderId,extraCards
  }));return true}
  catch(e){note("Browser storage unavailable. Export the decklist to keep it.",true);return false}
}
function imageNode(card,art=true,className=""){
  if(!card||!(art?card.art:card.image)){
    const fallback=el("div","✧  "+safeText(card?.name||"Unknown Legend"),"no-image");
    if(className)fallback.classList.add(className);return fallback;
  }
  const img=el("img",null,className);
  img.src=art?card.art:card.image;
  img.alt=card.name+" card illustration";
  img.loading="lazy";img.referrerPolicy="no-referrer";
  img.onerror=()=>{
    const fallback=el("div","✧  "+card.name,"no-image");
    if(img.parentElement)img.replaceWith(fallback);
  };
  return img;
}
function selectedDeck(){return data.decks.find(d=>d.key===selected);}
function commanderCard(deck){return cardForId(deck.commander_id);}
function svg(tag,attrs={}){
  const node=document.createElementNS(NS,tag);
  for(const [k,v] of Object.entries(attrs))node.setAttribute(k,String(v));
  return node;
}
function makeBars(items,{color="#bfa066",maxHeight=130}={}){
  const width=540,height=185,left=20,right=8,top=12,bottom=36;
  const chart=svg("svg",{class:"bar-chart",viewBox:`0 0 ${width} ${height}`,
    role:"img","aria-label":items.map(x=>x[0]+": "+x[1]).join(", ")});
  const max=Math.max(1,...items.map(i=>i[1]));
  for(let k=0;k<=3;k++){
    const y=top+(maxHeight*k/3);
    chart.appendChild(svg("line",{x1:left,y1:y,x2:width-right,y2:y,class:"gridline"}));
  }
  const gap=7,barWidth=(width-left-right-(items.length-1)*gap)/Math.max(1,items.length);
  items.forEach(([label,value],i)=>{
    const x=left+i*(barWidth+gap);
    const barHeight=value/max*maxHeight;
    chart.appendChild(svg("rect",{x,y:top+maxHeight-barHeight,width:barWidth,
      height:Math.max(1,barHeight),rx:3,fill:color,
      class:"bar "+(label==="Land"?"bar-land":"")}));
    const val=svg("text",{x:x+barWidth/2,y:top+maxHeight-barHeight-6,
      "text-anchor":"middle"});val.textContent=value;chart.appendChild(val);
    const text=svg("text",{x:x+barWidth/2,y:height-21,
      "text-anchor":"middle"});text.textContent=label.length>10?label.slice(0,9)+"…":label;
    chart.appendChild(text);
  });
  return chart;
}
function sameCommanderDecks(commanderId){
  return data.decks.filter(deck=>deck.commander_id===commanderId);
}
function deckVersionsForCommander(commanderId){
  const keys=new Set(sameCommanderDecks(commanderId).map(d=>d.key));
  return localVersions.filter(v=>keys.has(v.baseKey))
    .sort((a,b)=>String(b.updated||b.created||"").localeCompare(String(a.updated||a.created||"")));
}
function latestSelectionForCommander(commanderId){
  const saved=deckVersionsForCommander(commanderId)[0];
  if(saved)return {key:saved.baseKey,version:saved.id};
  const preferred=preferredByCommander[commanderId];
  if(preferred?.key&&sameCommanderDecks(commanderId).some(d=>d.key===preferred.key)){
    const version=localVersions.some(v=>v.id===preferred.version&&v.baseKey===preferred.key)?
      preferred.version:null;
    return {key:preferred.key,version};
  }
  return {key:sameCommanderDecks(commanderId)[0]?.key,version:null};
}
function versionById(id){
  return localVersions.find(v=>v.id===id&&v.baseKey===selected)||null;
}
function activeVersion(){return selectedVersionId?versionById(selectedVersionId):null;}
function isUnsimulatedVersion(){return !!activeVersion();}
function visibleCounts(){
  if(activeCounts&&typeof activeCounts==="object")return activeCounts;
  return initialCounts();
}
function displayDeckCards(){
  const deck=selectedDeck();
  if(!deck)return [];
  const commander=deck.cards.find(c=>c.zone==="Commander");
  const result=commander?[commander]:[];
  for(const [name,qty] of Object.entries(visibleCounts())){
    if(!qty)continue;
    const card=cardInfo(name);
    result.push({name,qty,zone:"Library",oracle_id:card?.oracle_id||null});
  }
  return result;
}
function activeDeckTitle(){
  return activeVersion()?.title||LABELS[selected]||selectedDeck()?.commander||"";
}
function updateSelectionBadge(){
  if(!selected)return;
  const deck=selectedDeck(),card=commanderCard(deck),portrait=$("medallion-portrait");
  clear(portrait);portrait.appendChild(imageNode(card,true,"medallion-art"));
  $("commander-medallion").setAttribute("aria-label","Change commander from "+deck.commander);
  $("active-commander").textContent=deck.commander;
  $("active-deck-name").textContent=activeDeckTitle();
  $("active-deck-state").textContent=isUnsimulatedVersion()?
    "Browser deck · no cached results":"Cached results available";
  const link=$("change-deck-link"),url=new URL("./editor.html",location.href);
  url.searchParams.set("deck",selected);
  if(selectedVersionId)url.searchParams.set("version",selectedVersionId);
  link.href=url.href;
}
function buildDeckRail(){
  const rail=$("commander-rail");clear(rail);
  const seen=new Set();
  for(const deck of data.decks){
    if(seen.has(deck.commander_id))continue;
    seen.add(deck.commander_id);
    const card=commanderCard(deck),button=el("button",null,"commander-choice");
    button.type="button";button.dataset.commander=deck.commander_id;
    button.appendChild(imageNode(card,true,"choice-art"));
    const details=el("span");details.appendChild(el("strong",deck.commander));
    details.appendChild(el("small",sameCommanderDecks(deck.commander_id).length+
      " built-in deck(s) · "+deckVersionsForCommander(deck.commander_id).length+" saved"));
    button.appendChild(details);
    button.addEventListener("click",()=>{
      const choice=latestSelectionForCommander(deck.commander_id);
      summon(choice.key,{versionId:choice.version});
      closeCommanderPicker();originalSound("summon");
    });
    rail.appendChild(button);
  }
}
function closeCommanderPicker(){
  $("commander-picker").hidden=true;
  $("commander-medallion").setAttribute("aria-expanded","false");
}
function toggleCommanderPicker(){
  const open=$("commander-picker").hidden;
  $("commander-picker").hidden=!open;
  $("commander-medallion").setAttribute("aria-expanded",String(open));
  if(open)buildDeckRail();
  originalSound("click");
}
function syncPageNavigation(){
  const params=new URLSearchParams(location.search);
  params.set("deck",selected);
  if(selectedVersionId)params.set("version",selectedVersionId);
  else params.delete("version");
  try{window.history.replaceState(null,"",location.pathname+"?"+params.toString())}
  catch(e){/* history may be unavailable in local previews */}
  for(const link of document.querySelectorAll(".site-link")){
    const target=new URL(link.href,location.href);
    target.searchParams.set("deck",selected);
    if(selectedVersionId)target.searchParams.set("version",selectedVersionId);
    else target.searchParams.delete("version");
    link.href=target.href;
  }
  updateSelectionBadge();
}
function summon(key,{versionId=null,remember=true}={}){
  const deck=data.decks.find(d=>d.key===key);
  if(!deck)return;
  selected=key;
  selectedVersionId=versionId&&localVersions.some(v=>v.id===versionId&&v.baseKey===key)?
    versionId:null;
  activeCounts=selectedVersionId?{...versionById(selectedVersionId).counts}:null;
  history=[];
  if(remember){
    lastCommanderId=deck.commander_id;
    preferredByCommander[deck.commander_id]={key,version:selectedVersionId};
    persist();
  }
  $("app-content").hidden=false;
  $("app-content").style.animation="none";
  void $("app-content").offsetWidth;$("app-content").style.animation="";
  selectedSeed=String(data.seeds[0]);
  renderOverview();renderLibrary();renderRecords();initializeDraft();
  showPage();syncPageNavigation();
}
function showPage(){
  const enabled={
    results:["records","insights"],
    summary:["overview"],
    editor:["library","workshop"]
  }[pageName];
  for(const pane of document.querySelectorAll(".tab-pane"))
    pane.hidden=!enabled.includes(pane.id.replace("pane-",""));
  for(const link of document.querySelectorAll(".site-link")){
    const active=link.dataset.page===pageName;
    link.classList.toggle("active",active);
    if(active)link.setAttribute("aria-current","page");
    else link.removeAttribute("aria-current");
  }
  const intro=$("page-introduction");clear(intro);
  const [title,desc]=PAGE_INFO[pageName];
  intro.append(el("h1",title),el("p",desc));
  document.title=title+" | Commander Deck Lab";
  if(pageName==="results")installScrollStory();
}
function renderOverview(){
  const deck=selectedDeck(),c=commanderCard(deck);
  $("overview-name").textContent=deck.commander;
  const art=$("overview-art");clear(art);
  const node=imageNode(c,true,"big-portrait");node.classList.add("big-portrait");art.appendChild(node);
  const metrics=$("overview-metrics");clear(metrics);
  const cards=displayDeckCards();
  const unique=cards.length;
  const lands=cards.filter(x=>cardForId(x.oracle_id)?.category==="Land")
    .reduce((n,x)=>n+x.qty,0);
  for(const [value,label] of [[100,"Cards"],[unique,"Unique names"],[lands,"Lands"]]){
    const x=el("div",null,"metric");
    x.appendChild(el("strong",value));x.appendChild(el("span",label));metrics.appendChild(x);
  }
  const tags=$("overview-tags");clear(tags);
  for(const txt of [activeDeckTitle(),deck.label.replace(/_/g," "),
       isUnsimulatedVersion()?"Edited in browser · no cached results":"Pinned metadata",
       isUnsimulatedVersion()?"Export for new observations":"6-turn cached records"]){
    tags.appendChild(el("span",txt,"chip"));
  }
  const typeCounts={};
  for(const item of cards){
    const kind=cardForId(item.oracle_id)?.category||"Other";
    typeCounts[kind]=(typeCounts[kind]||0)+item.qty;
  }
  const types=Object.entries(typeCounts).sort((a,b)=>b[1]-a[1]);
  const typeBox=$("type-chart");clear(typeBox);typeBox.appendChild(makeBars(types,{color:"#bda46d"}));
  const curve=Array.from({length:9},(_,i)=>[i===8?"8+":String(i),0]);
  for(const x of cards){
    const item=cardForId(x.oracle_id);
    if(!item||item.category==="Land")continue;
    const mv=Math.max(0,Math.min(8,Math.floor(Number(item.mana_value)||0)));
    curve[mv][1]+=x.qty;
  }
  const curveBox=$("mana-chart");clear(curveBox);
  curveBox.appendChild(makeBars(curve,{color:"#80bdb2"}));
}
function libraryRows(){
  const needle=$("library-search").value.trim().toLowerCase();
  const category=$("library-category").value;
  return displayDeckCards().filter(x=>{
    const card=cardForId(x.oracle_id);
    return (!needle||[x.name,card?.type_line,card?.oracle_text].join(" ").toLowerCase().includes(needle))
      && (category==="all"||card?.category===category);
  }).sort((a,b)=>a.zone==="Commander"?-1:b.zone==="Commander"?1:
    a.name.localeCompare(b.name));
}
function renderLibrary(){
  const root=$("library-rows");clear(root);
  const rows=libraryRows();
  $("library-count").textContent=" · "+rows.reduce((n,x)=>n+x.qty,0)+" cards";
  for(const item of rows){
    const card=cardForId(item.oracle_id),tr=el("tr");
    tr.appendChild(el("td",item.qty));
    const col=el("td"),btn=el("button",item.name,"selectable-card");
    btn.type="button";btn.addEventListener("click",()=>showCard(item.oracle_id));
    col.appendChild(btn);
    tr.append(col,el("td",card?.type_line||"Unknown"));
    tr.appendChild(el("td",card?.mana_cost||"—"));root.appendChild(tr);
  }
  if(!rows.length){
    const tr=el("tr"),td=el("td","No matching cards.");td.colSpan=4;tr.appendChild(td);root.appendChild(tr);
  }
}
function showCard(id){
  const card=cardForId(id);if(!card)return;
  const box=$("modal-art");clear(box);box.appendChild(imageNode(card,false));
  $("card-dialog-title").textContent=card.name;
  $("modal-meta").textContent=card.type_line+" · Mana value "+card.mana_value;
  $("modal-oracle").textContent=card.oracle_text||"No Oracle text in the saved record.";
  $("modal-scryfall").href=card.scryfall||"https://scryfall.com/";
  $("dialog-backdrop").hidden=false;$("modal-close").focus();
  originalSound("click");
}
function closeCard(){$("dialog-backdrop").hidden=true}
function renderRecords(){
  const select=$("seed-select");clear(select);
  for(const seed of data.seeds){
    const opt=el("option","Seed "+seed);opt.value=String(seed);select.appendChild(opt);
  }
  select.value=selectedSeed;
  const warning=$("results-current-warning");
  if(isUnsimulatedVersion()){
    warning.hidden=false;
    warning.textContent="“"+activeDeckTitle()+"” is a browser-edited deck. No cached Python observations exist for this version. The records below are unavailable until you export and prepare this deck in the simulator. Choose a built-in deck in the editor to view its existing records.";
    $("show-record").disabled=true;
    $("export-record").disabled=true;
    clear($("record-info"));clear($("turn-timeline"));
    $("record-info").appendChild(el("p","No cached observations for this saved deck.","warning"));
    $("turn-timeline").appendChild(el("p","Export this decklist from the Card List & Editor page, then generate new observations with Python.","small"));
    lastRecord=null;
    for(const section of document.querySelectorAll(".story-step"))section.hidden=true;
    return;
  }
  warning.hidden=true;
  $("show-record").disabled=false;
  $("export-record").disabled=false;
  for(const section of document.querySelectorAll(".story-step"))section.hidden=false;
  displayRecord();
}
function displayRecord(){
  if(isUnsimulatedVersion()){
    renderRecords();return;
  }
  const deck=selectedDeck(),seed=$("seed-select").value;
  const record=archives[deck.key]?.[seed];
  if(!record){note("Cached result not available for this seed.",true);return}
  selectedSeed=seed;lastRecord=record;
  const turns=Math.min(Number($("turn-select").value),record.trace.length);
  const info=$("record-info");clear(info);
  const box=el("div",null,"metrics");
  for(const [val,label] of [[seed,"Seed"],[record.opening_hand.length,"Opening cards"],[turns,"Turns shown"]]){
    const row=el("div",null,"metric");row.append(el("strong",val),el("span",label));box.append(row);
  }
  info.appendChild(box);
  info.appendChild(el("h3","Opening hand"));
  const chips=el("div",null,"chips");
  for(const name of record.opening_hand){
    const ch=el("span",name,"chip");chips.appendChild(ch);
  }
  info.appendChild(chips);
  const timeline=$("turn-timeline");clear(timeline);
  for(const t of record.trace.slice(0,turns)){
    const node=el("div",null,"turn");
    node.appendChild(el("div",t.turn,"number"));
    const body=el("div",null,"turn-body");
    const draw=el("div");draw.append(el("strong","Draw "),el("span",t.drawn||"Empty library","muted"));body.append(draw);
    const land=el("div");land.append(el("strong","Modeled land "),el("span",t.land_played||"No modeled land play","muted"));body.append(land);
    const sourceCount=t.modeled_sources?.length??t.battlefield_count;
    body.appendChild(el("div",sourceCount+" modeled mana sources · "+t.hand_count+" cards in hand","small"));
    const candidates=t.candidate_if_supported||[];
    body.appendChild(el("div",candidates.length?
      "Mana-value candidates: "+candidates.map(c=>c.card).join(", "):
      "No mana-value candidates identified","small"));
    node.appendChild(body);timeline.appendChild(node);
  }
  if(pageName==="results")renderScrollStory();
}
/* Scroll-linked chart story. D3 transitions are progressive enhancement; native
 * SVG always renders when the D3 CDN is unavailable or motion is reduced.
 * Every value comes from the selected fixed-seed Python observation.
 */
function scrollValue(t,kind){
  if(kind==="sources")return Array.isArray(t.modeled_sources)?t.modeled_sources.length:
    Number(t.battlefield_count)||0;
  if(kind==="hand")return Number(t.hand_count)||0;
  return Array.isArray(t.candidate_if_supported)?t.candidate_if_supported.length:0;
}
function renderScrollChart(id,kind,trace){
  const root=$(id);if(!root)return;
  clear(root);
  const points=trace.map(t=>[String(t.turn),scrollValue(t,kind)]);
  const chart=makeBars(points,{color:kind==="sources"?"#73bdb1":
    kind==="hand"?"#dbb973":"#ae9ad6"});
  chart.classList.add("reveal-chart");
  root.appendChild(chart);
  const bars=chart.querySelectorAll("rect.bar");
  const item=chart.closest(".story-step");
  const reduced=window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  if(!reduced&&item&&!item.classList.contains("visible")){
    for(const bar of bars){
      const y=Number(bar.getAttribute("y")),h=Number(bar.getAttribute("height"));
      bar.dataset.targetY=String(y);
      bar.dataset.targetHeight=String(h);
      bar.setAttribute("y",String(y+h));
      bar.setAttribute("height","0");
    }
  }
}
function unveilChart(section){
  section.classList.add("visible");
  const bars=section.querySelectorAll("rect.bar[data-target-y]");
  if(!bars.length)return;
  const reduced=window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  if(!reduced&&window.d3){
    const d3=window.d3;
    d3.select(section).selectAll("rect.bar[data-target-y]")
      .transition().duration(760).ease(d3.easeCubicOut)
      .attr("y",function(){return this.dataset.targetY})
      .attr("height",function(){return this.dataset.targetHeight})
      .on("end",function(){
        delete this.dataset.targetY;
        delete this.dataset.targetHeight;
      });
  }else{
    for(const bar of bars){
      bar.setAttribute("y",bar.dataset.targetY);
      bar.setAttribute("height",bar.dataset.targetHeight);
      delete bar.dataset.targetY;
      delete bar.dataset.targetHeight;
    }
  }
}
function installScrollStory(){
  if(scrollObserver){scrollObserver.disconnect();scrollObserver=null}
  const sections=[...document.querySelectorAll(".story-step")];
  if(!("IntersectionObserver" in window)){
    sections.forEach(unveilChart);return;
  }
  scrollObserver=new IntersectionObserver(entries=>{
    for(const e of entries)if(e.isIntersecting){
      unveilChart(e.target);scrollObserver.unobserve(e.target);
    }
  },{threshold:.18,rootMargin:"0px 0px -8% 0px"});
  for(const section of sections)scrollObserver.observe(section);
}
function renderScrollStory(){
  if(!lastRecord){
    for(const id of ["scroll-sources","scroll-hand","scroll-candidates"])clear($(id));
    return;
  }
  for(const section of document.querySelectorAll(".story-step"))
    section.classList.remove("visible");
  const trace=lastRecord.trace.slice(0,Number($("turn-select").value)||6);
  renderScrollChart("scroll-sources","sources",trace);
  renderScrollChart("scroll-hand","hand",trace);
  renderScrollChart("scroll-candidates","candidates",trace);
  installScrollStory();
}
function exportFile(filename,content,type="text/plain"){
  const object=new Blob([content],{type});
  const url=URL.createObjectURL(object);
  const anchor=document.createElement("a");anchor.href=url;anchor.download=filename;
  document.body.appendChild(anchor);anchor.click();anchor.remove();
  setTimeout(()=>URL.revokeObjectURL(url),4000);
}
function exportRecord(){
  if(!lastRecord)return;
  exportFile(selected+"-seed-"+selectedSeed+"-cached-observation.json",
    JSON.stringify(lastRecord,null,2),"application/json");
  originalSound("click");
}
function initialCounts(){
  return Object.fromEntries(selectedDeck().cards.filter(x=>x.zone!=="Commander").map(x=>[x.name,x.qty]));
}
function sumCounts(counts){return Object.values(counts).reduce((a,b)=>a+Number(b||0),1)}
function normalizedCounts(counts){
  const normalized={};
  for(const [name,num] of Object.entries(counts))
    if(Number.isInteger(num)&&num>0)normalized[name]=num;
  return normalized;
}
function validateCounts(counts){
  const deck=selectedDeck(),cmd=commanderCard(deck);
  if(sumCounts(counts)!==100)throw Error("A Commander deck must have exactly 100 cards, including its commander.");
  const identities=new Set([deck.commander_id]);
  for(const [name,qty] of Object.entries(counts)){
    if(!Number.isInteger(qty)||qty<0)throw Error("Card quantities must be whole positive numbers.");
    const card=cardInfo(name);
    if(!card)throw Error("Missing verified metadata: "+name+". Use Fetch card details first.");
    if(card.commander_legality!=="legal")throw Error(name+" is not marked Commander-legal in cached metadata.");
    if(name===deck.commander||card.oracle_id===deck.commander_id)throw Error("The commander cannot also be in the library.");
    if([...card.color_identity].some(color=>!cmd.color_identity.includes(color)))
      throw Error(name+" has colors outside "+deck.commander+"'s color identity.");
    if(!card.is_basic && qty>1)throw Error("Commander singleton: "+name+" cannot appear "+qty+" times.");
    if(identities.has(card.oracle_id))throw Error("One Oracle card occurs under multiple names: "+name);
    identities.add(card.oracle_id);
  }
  return true;
}
function initializeDraft(){
  activeCounts=isUnsimulatedVersion()?{...activeVersion().counts}:initialCounts();
  history=[];
  $("add-name").value="";
  $("draft-title").value=activeVersion()?.title||"";
  renderDraft();renderVersions();renderDeckVersionSelector();
}
function activeDelta(){
  const initial=initialCounts(),names=new Set([...Object.keys(initial),...Object.keys(activeCounts)]);
  return [...names].filter(name=>(initial[name]||0)!==(activeCounts[name]||0))
    .sort((a,b)=>a.localeCompare(b)).map(name=>({
      name,before:initial[name]||0,after:activeCounts[name]||0,
      delta:(activeCounts[name]||0)-(initial[name]||0)
    }));
}
function renderDraft(){
  if(!selected)return;
  const remove=$("remove-name");clear(remove);
  for(const name of Object.keys(activeCounts).sort((a,b)=>a.localeCompare(b))){
    if(activeCounts[name]<=0)continue;
    const o=el("option",activeCounts[name]+" × "+name);o.value=name;remove.appendChild(o);
  }
  const diff=$("workshop-diff");clear(diff);
  const changes=activeDelta();
  if(!changes.length){diff.appendChild(el("p","No changes yet. Your original deck remains intact.","small"));}
  for(const item of changes){
    const row=el("div",null,"deck-row");
    row.appendChild(el("strong",item.name));
    row.appendChild(el("span",(item.delta>0?"+":"")+item.delta,
      item.delta>0?"diff-up":"diff-down"));diff.appendChild(row);
  }
  $("undo-button").disabled=!history.length;
  $("reset-button").disabled=!changes.length;
  $("workshop-message").textContent=changes.length?
    changes.length+" card quantities modified · "+sumCounts(activeCounts)+" cards including commander. "+MODE_NOTE:
    "Choose a card to remove, then choose a new card to add.";
}
function trySwap(){
  const remove=$("remove-name").value,add=$("add-name").value.trim();
  if(!remove||!add){note("Choose one card to remove and one to add.",true);return}
  const candidate={...activeCounts};
  if(!candidate[remove]){note("Selected card is no longer in the draft.",true);return}
  candidate[remove]--;
  if(candidate[remove]===0)delete candidate[remove];
  candidate[add]=(candidate[add]||0)+1;
  try{
    validateCounts(candidate);
    history.push({...activeCounts});activeCounts=candidate;
    renderDraft();originalSound("success");
    $("add-name").value="";
  }catch(err){note(err.message,true);originalSound("error")}
}
function undo(){
  if(history.length){activeCounts=history.pop();renderDraft();originalSound("click")}
}
function revertDraft(){activeCounts=initialCounts();history=[];renderDraft();originalSound("click")}
function saveVersion(){
  const title=$("draft-title").value.trim();
  if(title.length<1||title.length>70){
    note("Give this deck version a title (1–70 characters).",true);return;
  }
  try{validateCounts(activeCounts)}catch(err){note(err.message,true);return}
  const now=new Date().toISOString();
  const id="v-"+Date.now().toString(36)+"-"+Math.random().toString(36).slice(2,9);
  const record={id,title,baseKey:selected,counts:{...activeCounts},
    created:now,updated:now};
  localVersions.unshift(record);
  if(localVersions.length>60)localVersions=localVersions.slice(0,60);
  // Save As always creates a separately named revision. The original remains intact.
  summon(selected,{versionId:id});
  originalSound("success");
  note("Saved “"+title+"” in this browser. Download the decklist to keep a durable copy.");
}
function renderDeckVersionSelector(){
  const control=$("deck-version-select");clear(control);
  const commanderId=selectedDeck().commander_id;
  const presets=el("optgroup");presets.label="Built-in decks · cached results";
  for(const deck of sameCommanderDecks(commanderId)){
    const option=el("option",LABELS[deck.key]||deck.key);
    option.value="preset:"+deck.key;presets.appendChild(option);
  }
  control.appendChild(presets);
  const versions=deckVersionsForCommander(commanderId);
  if(versions.length){
    const saved=el("optgroup");saved.label="Your saved browser decks · not simulated";
    for(const version of versions){
      const option=el("option",version.title+" · saved "+String(version.updated||version.created||"").slice(0,10));
      option.value="saved:"+version.id;saved.appendChild(option);
    }
    control.appendChild(saved);
  }
  control.value=selectedVersionId?"saved:"+selectedVersionId:"preset:"+selected;
}
function loadDeckSelection(value){
  if(value.startsWith("preset:")){
    const deck=data.decks.find(d=>d.key===value.slice(7));
    if(deck&&deck.commander_id===selectedDeck().commander_id)
      summon(deck.key);
    return;
  }
  if(value.startsWith("saved:")){
    const version=localVersions.find(v=>v.id===value.slice(6));
    if(!version||!sameCommanderDecks(selectedDeck().commander_id)
      .some(d=>d.key===version.baseKey))return;
    const previous=selected;
    selected=version.baseKey;
    try{validateCounts(version.counts)}
    catch(e){selected=previous;note("Saved deck cannot be loaded: "+e.message,true);renderDeckVersionSelector();return}
    selected=previous;
    summon(version.baseKey,{versionId:version.id});
    note("Loaded “"+version.title+"”. No cached simulation is associated with this edited version.");
  }
}
function renderVersions(){
  const root=$("saved-versions");clear(root);
  const versions=deckVersionsForCommander(selectedDeck().commander_id);
  if(!versions.length){
    root.appendChild(el("p","No named browser decks saved for this commander.","small"));
    return;
  }
  for(const version of versions){
    const row=el("div",null,"saved-row");
    if(version.id===selectedVersionId)row.classList.add("selected-version");
    const label=el("div");
    label.appendChild(el("strong",version.title));
    label.appendChild(el("div",
      (LABELS[version.baseKey]||version.baseKey)+" · "+
      String(version.updated||version.created||"").slice(0,10)+" · browser only",
      "micro"));
    const actions=el("div",null,"control-row");
    const load=el("button","Load","glyph-button");
    load.onclick=()=>loadDeckSelection("saved:"+version.id);
    const del=el("button","Delete","glyph-button");
    del.onclick=()=>{
      localVersions=localVersions.filter(v=>v.id!==version.id);
      if(selectedVersionId===version.id){
        summon(version.baseKey);
      }else{
        persist();renderVersions();renderDeckVersionSelector();
      }
      originalSound("click");
    };
    actions.append(load,del);row.append(label,actions);root.append(row);
  }
}
function newDeckVersion(){
  // This is a fresh, unsaved draft derived from the currently visible deck.
  // It does not mutate any original or saved deck.
  selectedVersionId=null;
  history=[];
  $("draft-title").value="";
  renderDraft();
  renderDeckVersionSelector();
  $("version-help").textContent="New unsaved draft. Enter a name and choose Save as named deck.";
  note("New draft started from the visible card list.");
}
function exportDeck(){
  if(!selected)return;
  try{validateCounts(activeCounts)}catch(err){note(err.message,true);return}
  const commander=selectedDeck().commander;
  const lines=[
    "# Exported from Commander Deck Lab (static version; no game results)",
    "Commander","1 "+commander,"","Library"
  ];
  for(const name of Object.keys(activeCounts).sort((a,b)=>a.localeCompare(b)))
    lines.push(activeCounts[name]+" "+name);
  const name=(selectedDeck().key+"-"+($("draft-title").value||"custom"))
    .replace(/[^a-z0-9-]+/gi,"-").slice(0,70).toLowerCase();
  exportFile(name+".txt",lines.join("\n")+"\n");
  originalSound("success");
  note("Decklist exported. Import it into the Python simulator to generate new results.");
}
function matchesForName(q){
  const needle=q.toLowerCase().trim();
  if(needle.length<2)return [];
  const candidates=allNames.filter(name=>name.toLowerCase().startsWith(needle)).slice(0,25);
  if(candidates.length<15){
    for(const name of allNames){
      if(name.toLowerCase().includes(needle)&&!candidates.includes(name)){
        candidates.push(name);
        if(candidates.length>=25)break;
      }
    }
  }
  return candidates.slice(0,25);
}
function suggestNames(){
  const term=$("add-name").value.trim()||$("fetch-name").value.trim();
  const matches=matchesForName(term),box=$("name-suggestions");clear(box);
  for(const name of matches){const option=el("option");option.value=name;box.appendChild(option)}
}
function listenToNameInput(){
  clearTimeout(autoTimer);
  autoTimer=setTimeout(suggestNames,100);
}
function normalizeFetched(raw){
  if(!raw||!raw.oracle_id||!raw.name||!raw.type_line||!Array.isArray(raw.color_identity))
    throw Error("Scryfall did not return a complete card identity.");
  const face=Array.isArray(raw.card_faces)?raw.card_faces.find(f=>f?.image_uris)||{}:{};
  const imagery=raw.image_uris||face.image_uris||{};
  const print=raw.legalities?.commander||"unknown";
  return {
    oracle_id:raw.oracle_id,name:raw.name,type_line:raw.type_line,
    category:["Land","Creature","Artifact","Enchantment","Planeswalker","Instant","Sorcery"]
      .find(t=>raw.type_line.includes(t))||"Other",
    mana_value:raw.cmc,mana_cost:raw.mana_cost||"",
    color_identity:raw.color_identity,commander_legality:print,
    oracle_text:raw.oracle_text||raw.card_faces?.map(f=>f.oracle_text||"").join("\n")||"",
    power:raw.power,toughness:raw.toughness,
    image:imagery.normal||null,art:imagery.art_crop||null,
    scryfall:raw.scryfall_uri||null,
    is_basic:raw.type_line.includes("Basic Land"),
    face_names:raw.card_faces?.map(f=>f.name).filter(Boolean)||[]
  };
}
async function fetchCard(){
  const name=$("fetch-name").value.trim();
  if(!name||name.length>200){note("Enter an exact card name before fetching.",true);return}
  const existing=cardInfo(name);
  if(existing){$("fetch-status").textContent=existing.name+" already has cached metadata.";
    originalSound("click");return}
  const status=$("fetch-status");
  status.textContent="Requesting this card from Scryfall…";
  $("fetch-card").disabled=true;
  try{
    // Explicit user action only. Scryfall exposes this public CORS JSON API.
    const response=await fetch("https://api.scryfall.com/cards/named?exact="+encodeURIComponent(name),
      {headers:{"Accept":"application/json"}});
    if(!response.ok)throw Error(response.status===404?"Name not found in Scryfall. Check spelling.":
      "Scryfall request failed (HTTP "+response.status+").");
    const raw=await response.json(),card=normalizeFetched(raw);
    const aliases=[card.name,...card.face_names].map(x=>x.toLowerCase());
    if(!aliases.includes(name.toLowerCase()))throw Error("Returned card name did not match the requested name.");
    extraCards[card.oracle_id]=card;addAliases(card);persist();
    status.textContent=card.name+" cached in this browser. You can now try swapping it into a deck.";
    $("add-name").value=name;
    note(card.name+" is ready for validation.");
    originalSound("success");
  }catch(err){
    status.textContent="Unable to fetch: "+err.message+
      " You can still download the decklist and import it using Python.";
    originalSound("error");
  }finally{$("fetch-card").disabled=false}
}
function registerEvents(){
  $("audio-toggle").onclick=enableSound;
  // Navigation links lead to independent static pages (no client router).
  $("library-search").oninput=renderLibrary;
  $("library-category").onchange=renderLibrary;
  $("show-record").onclick=()=>{displayRecord();originalSound("page")};
  $("export-record").onclick=exportRecord;
  $("turn-select").onchange=displayRecord;
  $("seed-select").onchange=displayRecord;
  $("swap-button").onclick=trySwap;
  $("undo-button").onclick=undo;
  $("reset-button").onclick=revertDraft;
  $("save-local").onclick=saveVersion;
  $("export-deck").onclick=exportDeck;
  $("fetch-card").onclick=fetchCard;
  $("add-name").oninput=listenToNameInput;
  $("fetch-name").oninput=listenToNameInput;
  $("modal-close").onclick=closeCard;
  $("dialog-backdrop").onclick=e=>{if(e.target.id==="dialog-backdrop")closeCard()};
  document.addEventListener("keydown",e=>{if(e.key==="Escape")closeCard()});
}
async function boot(){
  registerEvents();
  try{
    const response=await Promise.all([
      fetch("./decks.json"),fetch("./observations.json"),fetch("./names.json")
    ]);
    if(response.some(r=>!r.ok))throw Error("Site data could not be loaded. Check the Pages deployment.");
    [data,archives,allNames]=await Promise.all(response.map(r=>r.json()));
    if(data.format!=="commander-deck-lab-static-v1"||!data.decks.length)
      throw Error("Unexpected static dataset format.");
    allNames.sort((a,b)=>a.localeCompare(b));
    for(const card of Object.values(data.cards))addAliases(card);
    loadLocal();buildDeckRail();
    const key=new URLSearchParams(location.search).get("deck");
    const start=data.decks.find(d=>d.key===key)?.key||
      data.decks.find(d=>d.key==="magnus_premium")?.key||data.decks[0].key;
    summon(start);
  }catch(err){
    const rail=$("commander-rail");clear(rail);
    rail.appendChild(el("p","Unable to open the archive: "+err.message));
    note("Deck archive unavailable. Verify the static data build.",true);
  }
}
boot();
