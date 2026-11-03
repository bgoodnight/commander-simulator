// Experimental gorge driver for four actual pinned Commander decks.
//
// Copy into a scratch gorge checkout and build THERE. This is not part of
// the Python simulation engine and imports no Forge card script sources.
package main

import (
  "encoding/json"
  "flag"
  "fmt"
  "os"
  "path/filepath"
  "strings"
  "time"

  "github.com/adams-shaun/gorge/bots"
  _ "github.com/adams-shaun/gorge/bots/all"
  "github.com/adams-shaun/gorge/engine/cards"
  "github.com/adams-shaun/gorge/engine/deck"
  "github.com/adams-shaun/gorge/engine/replay"
  "github.com/adams-shaun/gorge/engine/rules"
  "github.com/adams-shaun/gorge/engine/seat"
  "github.com/adams-shaun/gorge/engine/state"
  "github.com/adams-shaun/gorge/testkit/bench"
  "github.com/adams-shaun/gorge/testkit/testutil"
)

type Result struct {
  Seed uint64 `json:"seed"`
  Decks []string `json:"decks"`
  Finished bool `json:"finished"`
  Draw bool `json:"draw"`
  WinnerSeat *int `json:"winner_seat,omitempty"`
  StallReason string `json:"stall_reason,omitempty"`
  Error string `json:"error,omitempty"`
  Turns int32 `json:"turns"`
  Intents int `json:"intents"`
  Events int `json:"events"`
  ReplayVerified bool `json:"replay_verified"`
  ElapsedSeconds float64 `json:"elapsed_seconds"`
  Policies []string `json:"policies"`
  ReplayChain string `json:"replay_chain,omitempty"`
  NativeTrace string `json:"native_trace,omitempty"`
}

// Snapshots are captured at the first pending decision of each turn.
// They are NOT end-of-turn snapshots. Every field comes from gorge's state.
func snapshot(e *rules.Engine) map[string]any {
  players:=make([]any,len(e.G.Players))
  for i,p:=range e.G.Players {
    zones:=map[string]any{}
    for _,z:=range []state.Zone{state.ZHand,state.ZBattlefield,
      state.ZLibrary,state.ZGraveyard,state.ZExile,state.ZCommand} {
      ids:=make([]uint32,0,len(e.G.Zone(z,state.PlayerID(i))))
      for _,id:=range e.G.Zone(z,state.PlayerID(i)){ids=append(ids,uint32(id))}
      zones[z.String()]=ids
    }
    players[i]=map[string]any{"seat":i,"life":p.Life,"lost":p.Lost,
      "mana_pool":p.Pool,"zones":zones}
  }
  return map[string]any{"turn":e.G.Turn,"active_seat":e.G.Active,
    "step":e.G.Step.String(),"after_event_seq":len(e.L.Events)-1,
    "boundary":"first_pending_decision_of_turn","players":players}
}

// Card identity is stable in the pinned corpus, but the numeric object
// identifier is scoped to one game. Record minted objects as well as cards.
func objectCrosswalk(e *rules.Engine) []any {
  rows:=make([]any,0,len(e.G.Objs))
  for i:=range e.G.Objs {
    o:=&e.G.Objs[i]
    name:=""
    printed:=""
    types:=[]string{}
    if f:=o.Face();f!=nil{name=f.Name;types=append(types,f.Types...)}
    if o.Card!=nil&&len(o.Card.Faces)>0&&o.Card.Faces[0]!=nil {
      printed=o.Card.Faces[0].Name
    }
    rows=append(rows,map[string]any{
      "object_id":o.ID,"card_name":printed,"effective_name":name,
      "owner":o.Owner,"controller_at_end":o.Controller,
      "is_token":o.IsToken,"is_copy":o.IsCopy,"types_at_end":types})
  }
  return rows
}

func main() {
  corpus:=flag.String("corpus",".cards","compiled Forge card corpus")
  directory:=flag.String("deck-dir","","directory of deck JSON exported from pinned lists")
  games:=flag.Int("games",3,"number of four-player runs")
  seed:=flag.Uint64("seed",100,"first deterministic seed")
  maxTurns:=flag.Int("max-turns",50,"cap for complete Commander game")
  verify:=flag.Bool("verify",true,"replay each completed game")
  deckPool:=flag.String("decks","mortarion_current,magnus_premium,necron_dynasties,wretched_ranks","comma-separated pool of four or more Commander deck names")
  policy:=flag.String("pilot","bot","gorge-native AI: bot, forge-heuristic, forge-heuristic-hold, lethal-pressure")
  firstSeatPolicy:=flag.String("hero-pilot","","optional policy for seat zero")
  nativeDir:=flag.String("native-dir","","directory for gorge-native raw event/intent logs")
  nativeLimit:=flag.Int("native-limit",2,"how many initial game traces to store")
  flag.Parse()
  if *directory==""||*games<=0||*games>1000||*maxTurns<=0 { panic("invalid probe arguments") }
  names:=strings.Split(*deckPool,",")
  for i:=range names {names[i]=strings.TrimSpace(names[i])}
  if len(names)<4 {panic("Need at least four unique deck names")}
  unique:=map[string]bool{}
  for _,name:=range names {
    if name==""||strings.Contains(name,"/")||strings.Contains(name,"..")||unique[name]{
      panic("Invalid, unsafe or duplicate deck key")
    }
    unique[name]=true
  }
  allowed:=map[string]bool{"bot":true,"forge-heuristic":true,
    "forge-heuristic-hold":true,"lethal-pressure":true}
  if !allowed[*policy]||(*firstSeatPolicy!=""&&!allowed[*firstSeatPolicy]){
    panic("Unknown or unsupported Commander pilot policy")
  }
  if *nativeLimit<0||*nativeLimit>100{panic("Invalid trace count")}
  if *nativeDir!=""{if err:=os.MkdirAll(*nativeDir,0700);err!=nil{panic(err)}}
  reg,err:=testutil.OpenCorpusRegistry(*corpus);if err!=nil {panic(err)}
  decks:=make([][]*cards.Card,len(names))
  commanders:=make([][]int,len(names))
  for i,name:=range names {
    f,cs,loadErr:=deck.Load(reg,filepath.Join(*directory,name+".json"))
    if loadErr!=nil {panic(fmt.Sprintf("%s import: %v",name,loadErr))}
    if err:=f.ValidateCommander(reg);err!=nil {panic(fmt.Sprintf("%s commander invalid: %v",name,err))}
    decks[i]=cs;commanders[i]=f.CommanderIndices()
    if len(cs)!=100||len(commanders[i])!=1 {panic(fmt.Sprintf("%s is not a single-commander 100-card deck",name))}
  }
  failed:=false
  for g:=0;g<*games;g++ {
    gs:=*seed+uint64(g)
    // Deterministically rotate decks, so seat and turn-order bias can be
    // separated from deck advantage when more seeds are collected.
    ids:=make([]string,4); ds:=make([][]*cards.Card,4); cs:=make([][]int,4)
    policies:=make([]string,4)
    players:=make([]seat.Seat,4)
    for i:=0;i<4;i++ {
      k:=(i+g)%len(names)
      ids[i]=names[k];ds[i]=decks[k];cs[i]=commanders[k]
      policies[i]=*policy
      if i==0&&*firstSeatPolicy!=""{policies[i]=*firstSeatPolicy}
      players[i],err=bots.New(policies[i],bots.Options{
        Seed:gs^uint64(i+1),AutoPayMana:true,Deps:bots.Deps{Cards:reg}})
      if err!=nil {panic(err)}
    }
    // Gorge defaults to 20 life. Commander requires an explicit 40-life genesis.\n    cfg:=rules.Config{Seed:gs,Names:ids,Decks:ds,Commanders:cs,
      Format:rules.FormatCommander,StartingLife:40,Mulligans:7,Tokens:reg.Tokens,NameUniverse:reg.Universe()}
    start:=time.Now()
    capture:=*nativeDir!=""&&g<*nativeLimit
    observations:=[]any{}
    lastTurn:=int32(-1)
    hooks:=bench.Hooks{EnvSeats:true,HonestRoot:true}
    if capture {
      hooks.Guard=func(engine *rules.Engine)(string,string) {
        if engine.G.Turn>0&&engine.G.Turn!=lastTurn {
          lastTurn=engine.G.Turn
          observations=append(observations,snapshot(engine))
        }
        return "",""
      }
    }
    o,e,playErr:=bench.PlayGame(cfg,players,*maxTurns,400000,hooks)
    rec:=Result{Seed:gs,Decks:ids,Turns:o.Turns,Intents:o.Intents,
      Draw:o.Draw,StallReason:o.StallOn,ElapsedSeconds:time.Since(start).Seconds(),Policies:policies}
    if e!=nil {rec.Events=len(e.L.Events)}
    if playErr!=nil {rec.Error=playErr.Error()}
    rec.Finished=playErr==nil&&!o.IsStalled()&&e!=nil&&e.G.Over
    if rec.Finished&&!o.Draw {
      w:=o.WinnerSeat;rec.WinnerSeat=&w
    }
    if e!=nil{rec.ReplayChain=e.L.Head()}
    if rec.Finished&&*verify {
      reconstructed,rerr:=replay.Replay(e.L,cfg)
      if rerr==nil&&reconstructed!=nil&&reconstructed.L.Head()==e.L.Head(){
        rec.ReplayVerified=true
      }else{
        if rerr!=nil {rec.Error="replay: "+rerr.Error()} else {rec.Error="replay hash mismatch"}
      }
    }
    if e!=nil&&*nativeDir!=""&&g<*nativeLimit {
      filename:=fmt.Sprintf("gorge-seed-%d.json",gs)
      target:=filepath.Join(*nativeDir,filename)
      payload:=map[string]any{
        "schema":"gorge-native-trace-v1","engine":"gorge",
        "seed":gs,"decks":ids,"policies":policies,
        "format":"commander","chain":e.L.Head(),
        "log":e.L,
        "enrichment_schema":"gorge-physical-state-v1",
        "objects":objectCrosswalk(e),
        "snapshots":observations,
        "snapshots_are":"first_pending_decision_of_turn",
        "object_identity_scope":"one_game_only",
      }
      data,marshalErr:=json.Marshal(payload)
      if marshalErr!=nil{
        rec.Error="native serialization: "+marshalErr.Error()
      }else if writeErr:=os.WriteFile(target,data,0600);writeErr!=nil{
        rec.Error="native write: "+writeErr.Error()
      }else{rec.NativeTrace=filename}
    }
    out,_:=json.Marshal(rec);fmt.Println(string(out))
    if rec.Error!=""||!rec.Finished||(*verify&&!rec.ReplayVerified){failed=true}
  }
  if failed {os.Exit(2)}
}
