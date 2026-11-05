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
  HeroSeat *int `json:"hero_seat,omitempty"`
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
  heroDeck:=flag.String("hero-deck","","fixed player deck, never placed in opponent seats")
  opponentPool:=flag.String("opponents","","comma-separated pool of stock precon opponents (>=3); requires -hero-deck")
  policy:=flag.String("pilot","bot","gorge-native AI: bot, forge-heuristic, forge-heuristic-hold, lethal-pressure")
  firstSeatPolicy:=flag.String("hero-pilot","","optional policy for seat zero")
  nativeDir:=flag.String("native-dir","","directory for gorge-native raw event/intent logs")
  nativeLimit:=flag.Int("native-limit",2,"how many initial game traces to store")
  retryUnverified:=flag.Bool("retry-unverified",false,"retry failed or unverified games with fresh seeds until the requested count succeeds")
  maxAttempts:=flag.Int("max-attempts",0,"maximum attempts including rejected games (default: games)")
  flag.Parse()
  if *maxAttempts==0 {*maxAttempts=*games}
  if *maxAttempts<*games||*maxAttempts>5000 {panic("invalid attempt limit")}
  if *directory==""||*games<=0||*games>1000||*maxTurns<=0 { panic("invalid probe arguments") }
  names:=strings.Split(*deckPool,",")
  for i:=range names {names[i]=strings.TrimSpace(names[i])}
  restricted:=*heroDeck!=""||*opponentPool!=""
  if restricted {
    if *heroDeck==""||*opponentPool=="" {
      panic("Player-vs-precon mode requires both -hero-deck and -opponents")
    }
    opponents:=strings.Split(*opponentPool,",")
    if len(opponents)<3 {panic("Need at least 3 distinct precon opponents")}
    for i:=range opponents {opponents[i]=strings.TrimSpace(opponents[i])}
    names=append([]string{strings.TrimSpace(*heroDeck)},opponents...)
  }
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
  // A pinned Forge token corpus may omit a script referenced by a card.
  // Mortarion's end-step ability correctly resolves its X payment but would
  // otherwise emit "unknown token script" instead of creating permanents.
  // Supply the missing canonical 2/2 black Astartes Warrior with menace to
  // the shared token registry, not to Mortarion's card or the pilot.
  const astartesStem="b_2_2_astartes_warrior_menace"
  if _,ok:=reg.Tokens[astartesStem];!ok {
    text:="Name:Astartes Warrior Token\nTypes:Creature Astartes Warrior\nColors:B\nPT:2/2\nK:Menace\nOracle:Token\n"
    token,diags:=cards.ParseBytes(astartesStem,[]byte(text))
    if token==nil||len(diags)>0 {panic(fmt.Sprintf("Astartes token parse: %v",diags))}
    if d:=token.Link();len(d)>0 {panic(fmt.Sprintf("Astartes token link: %v",d))}
    for _,face:=range token.Faces {face.ApplyIntrinsics()}
    reg.Tokens[astartesStem]=token
  }

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
  succeeded:=0
  skipped:=0
  for g:=0;g<*maxAttempts&&succeeded<*games;g++ {
    gs:=*seed+uint64(g)
    // Deterministically rotate decks, so seat and turn-order bias can be
    // separated from deck advantage when more seeds are collected.
    ids:=make([]string,4); ds:=make([][]*cards.Card,4); cs:=make([][]int,4)
    policies:=make([]string,4)
    players:=make([]seat.Seat,4)
    heroSeat:=0
    if restricted {heroSeat=g%4}
    for i:=0;i<4;i++ {
      k:=(i+g)%len(names)
      if restricted {
        if i==heroSeat {
          k=0
        }else{
          // Three distinct precons per pod; rotate pool and seating.
          before:=i
          if i>heroSeat {before--}
          k=1+(before+g)% (len(names)-1)
        }
      }
      ids[i]=names[k];ds[i]=decks[k];cs[i]=commanders[k]
      policies[i]=*policy
      if i==heroSeat&&*firstSeatPolicy!=""{policies[i]=*firstSeatPolicy}
      players[i],err=bots.New(policies[i],bots.Options{
        Seed:gs^uint64(i+1),AutoPayMana:true,Deps:bots.Deps{Cards:reg}})
      if err!=nil {panic(err)}
    }
    // Gorge defaults to 20 life. Commander requires an explicit 40-life genesis.
    cfg:=rules.Config{Seed:gs,Names:ids,Decks:ds,Commanders:cs,
      Format:rules.FormatCommander,StartingLife:40,Mulligans:7,Tokens:reg.Tokens,NameUniverse:reg.Universe()}
    start:=time.Now()
    capture:=*nativeDir!=""&&
      ((!*retryUnverified&&g<*nativeLimit)||(*retryUnverified&&succeeded<*nativeLimit))
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
    if restricted {rec.HeroSeat=&heroSeat}
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
    verified:=rec.Error==""&&rec.Finished&&(!*verify||rec.ReplayVerified)
    if e!=nil&&capture&&(!*retryUnverified||verified) {
      filename:=fmt.Sprintf("gorge-seed-%d.json",gs)
      target:=filepath.Join(*nativeDir,filename)
      payload:=map[string]any{
        "schema":"gorge-native-trace-v1","engine":"gorge",
        "seed":gs,"decks":ids,"policies":policies,
        "hero_seat":heroSeat,"opponent_mode":restricted,
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
    verified=rec.Error==""&&rec.Finished&&(!*verify||rec.ReplayVerified)
    if !verified {
      failed=true
      if *retryUnverified {
        skipped++
        fmt.Fprintf(os.Stderr,"Skipped unverified seed %d: finished=%t verified=%t stall=%s error=%s\\n",
          gs,rec.Finished,rec.ReplayVerified,rec.StallReason,rec.Error)
        continue
      }
    }
    out,_:=json.Marshal(rec);fmt.Println(string(out))
    if verified {succeeded++}
  }
  if *retryUnverified {
    fmt.Fprintf(os.Stderr,"Gorge benchmark: %d verified games, %d excluded attempts\\n",succeeded,skipped)
  }
  if succeeded!=*games||(failed&&!*retryUnverified) {os.Exit(2)}
}
