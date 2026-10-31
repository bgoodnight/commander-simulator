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
    versions:localVersions.slice(0,60),extraCards
  }));return true}
  catch(e){note("Browser storage unavailable. Export the decklist to keep it.",true);return false}
}
function imageNode(card,art=true,className=""){
  if(!card||!(art?card.art:card.image)){
    const fallback=el("div","✧  "+safeText(card?.name||"Unknown Legend"),"no-image");
    fallback.classList.add(className||"");return fallback;
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
function buildDeckRail(){
  const rail=$("commander-rail");clear(rail);
  for(const deck of data.decks){
    const c=commanderCard(deck),btn=el("button",null,"commander-tile");
    btn.type="button";btn.draggable=true;btn.dataset.key=deck.key;
    btn.setAttribute("aria-label","Summon "+(LABELS[deck.key]||deck.commander));
    const art=imageNode(c,true);btn.appendChild(art);
    const desc=el("span",LABELS[deck.key]||deck.commander);
    desc.appendChild(el("em",deck.label.replace(/_/g," ")));
    btn.appendChild(desc);
    btn.addEventListener("click",()=>summon(deck.key));
    btn.addEventListener("dragstart",e=>{
      e.dataTransfer.setData("text/plain",deck.key);
      e.dataTransfer.effectAllowed="copy";originalSound("click");
    });
    rail.appendChild(btn);
  }
  const drop=$("drop-ring");
  drop.addEventListener("dragover",e=>{e.preventDefault();drop.classList.add("dragover")});
  drop.addEventListener("dragleave",()=>drop.classList.remove("dragover"));
  drop.addEventListener("drop",e=>{
    e.preventDefault();drop.classList.remove("dragover");
    const key=e.dataTransfer.getData("text/plain");
    if(data.decks.some(d=>d.key===key))summon(key);
  });
  drop.addEventListener("click",()=>{
    if(!selected)note("Tap a commander portrait below, or drag it into this rune.");
    else{originalSound("page");openTab("overview")}
  });
}
function summon(key){
  if(!data.decks.some(d=>d.key===key))return;
  selected=key;activeCounts=null;history=[];
  const deck=selectedDeck(),c=commanderCard(deck);
  const ring=$("drop-ring");clear(ring);
  ring.appendChild(imageNode(c,true,"selected-portrait"));
  ring.appendChild(el("span",LABELS[key]||deck.commander,"selected-label"));
  ring.classList.remove("summoned");
  void ring.offsetWidth;
  ring.classList.add("summoned");
  $("drop-ring").setAttribute("aria-label","Selected "+deck.commander);
  for(const btn of $("commander-rail").children){
    btn.classList.toggle("active",btn.dataset.key===key);
    btn.setAttribute("aria-pressed",String(btn.dataset.key===key));
  }
  $("app-content").hidden=false;
  $("app-content").style.animation="none";
  void $("app-content").offsetWidth;$("app-content").style.animation="";
  originalSound("summon");
  selectedSeed=String(data.seeds[0]);
  renderOverview();renderLibrary();renderRecords();initializeDraft();openTab("overview",false);
  try{history.replaceState(null,"","?deck="+encodeURIComponent(key))}
  catch(e){/* query string is optional */}
}
function openTab(tab,withSound=true){
  activeTab=tab;
  for(const button of document.querySelectorAll(".navtab")){
    const enabled=button.dataset.tab===tab;button.classList.toggle("selected",enabled);
    button.setAttribute("aria-current",enabled?"page":"false");
  }
  for(const pane of document.querySelectorAll(".tab-pane"))
    pane.hidden=pane.id!=="pane-"+tab;
  if(withSound)originalSound("page");
}
function renderOverview(){
  const deck=selectedDeck(),c=commanderCard(deck);
  $("overview-name").textContent=deck.commander;
  const art=$("overview-art");clear(art);
  const node=imageNode(c,true,"big-portrait");node.classList.add("big-portrait");art.appendChild(node);
  const metrics=$("overview-metrics");clear(metrics);
  const unique=deck.cards.length;
  const lands=deck.cards.filter(x=>cardForId(x.oracle_id)?.category==="Land")
    .reduce((n,x)=>n+x.qty,0);
  for(const [value,label] of [[100,"Cards"],[unique,"Unique names"],[lands,"Lands"]]){
    const x=el("div",null,"metric");
    x.appendChild(el("strong",value));x.appendChild(el("span",label));metrics.appendChild(x);
  }
  const tags=$("overview-tags");clear(tags);
  for(const txt of [LABELS[deck.key],deck.label.replace(/_/g," "),"Pinned metadata","6-turn cached records"]){
    tags.appendChild(el("span",txt,"chip"));
  }
  const types=Object.entries(deck.types||{}).sort((a,b)=>b[1]-a[1]);
  const typeBox=$("type-chart");clear(typeBox);typeBox.appendChild(makeBars(types,{color:"#bda46d"}));
  const curve=Array.from({length:9},(_,i)=>[i===8?"8+":String(i),0]);
  for(const x of deck.cards){
    const item=cardForId(x.oracle_id);
    if(!item||item.category==="Land")continue;
    const mv=Math.max(0,Math.min(8,Math.floor(Number(item.mana_value)||0)));
    curve[mv][1]+=x.qty;
  }
  const curveBox=$("mana-chart");clear(curveBox);
  curveBox.appendChild(makeBars(curve,{color:"#80bdb2"}));
}
function libraryRows(){
  const deck=selectedDeck();
  const needle=$("library-search").value.trim().toLowerCase();
  const category=$("library-category").value;
  return deck.cards.filter(x=>{
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
  displayRecord();
}
function displayRecord(){
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
  activeCounts=initialCounts();history=[];
  $("add-name").value="";$("draft-title").value="";
  renderDraft();renderVersions();
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
  if(title.length<1||title.length>70){note("Give this deck version a title (1–70 characters).",true);return}
  try{validateCounts(activeCounts)}catch(err){note(err.message,true);return}
  const id="v-"+Date.now().toString(36)+"-"+Math.random().toString(36).slice(2,7);
  const record={id,title,baseKey:selected,counts:{...activeCounts},created:new Date().toISOString()};
  localVersions.unshift(record);
  if(localVersions.length>60)localVersions=localVersions.slice(0,60);
  persist();renderVersions();originalSound("success");
  note("Saved in this browser. Download the decklist for a durable copy.");
}
function renderVersions(){
  const root=$("saved-versions");clear(root);
  const versions=localVersions.filter(v=>v.baseKey===selected);
  if(!versions.length){root.appendChild(el("p","No saved local versions for this commander.","small"));return}
  for(const version of versions){
    const row=el("div",null,"saved-row");
    const label=el("div");
    label.appendChild(el("strong",version.title));
    label.appendChild(el("div",version.created.slice(0,10)+" · local to this browser","micro"));
    const actions=el("div",null,"control-row");
    const load=el("button","Load","glyph-button");
    load.onclick=()=>{
      try{validateCounts(version.counts);activeCounts={...version.counts};history=[];
        renderDraft();$("draft-title").value=version.title;originalSound("page");
        note("Local deck loaded. Its edits have no cached simulation results.");
      }catch(e){note("Invalid saved deck: "+e.message,true)}
    };
    const del=el("button","Delete","glyph-button");
    del.onclick=()=>{
      localVersions=localVersions.filter(v=>v.id!==version.id);
      persist();renderVersions();originalSound("click");
    };
    actions.append(load,del);row.append(label,actions);root.append(row);
  }
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
  for(const tab of document.querySelectorAll(".navtab"))
    tab.onclick=()=>openTab(tab.dataset.tab);
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
    if(data.decks.some(d=>d.key===key))summon(key);
    else note("Choose a commander. The archive holds "+data.decks.length+" validated decks.");
  }catch(err){
    const rail=$("commander-rail");clear(rail);
    rail.appendChild(el("p","Unable to open the archive: "+err.message));
    note("Deck archive unavailable. Verify the static data build.",true);
  }
}
boot();
