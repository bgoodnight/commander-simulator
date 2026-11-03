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
  "time"

  "github.com/adams-shaun/gorge/bots"
  _ "github.com/adams-shaun/gorge/bots/all"
  "github.com/adams-shaun/gorge/engine/cards"
  "github.com/adams-shaun/gorge/engine/deck"
  "github.com/adams-shaun/gorge/engine/replay"
  "github.com/adams-shaun/gorge/engine/rules"
  "github.com/adams-shaun/gorge/engine/seat"
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
}

func main() {
  corpus:=flag.String("corpus",".cards","compiled Forge card corpus")
  directory:=flag.String("deck-dir","","directory of deck JSON exported from pinned lists")
  games:=flag.Int("games",3,"number of four-player runs")
  seed:=flag.Uint64("seed",100,"first deterministic seed")
  maxTurns:=flag.Int("max-turns",50,"cap for complete Commander game")
  verify:=flag.Bool("verify",true,"replay each completed game")
  flag.Parse()
  if *directory==""||*games<=0||*games>1000||*maxTurns<=0 { panic("invalid probe arguments") }
  names:=[]string{"mortarion_current","magnus_premium","necron_dynasties","wretched_ranks"}
  reg,err:=testutil.OpenCorpusRegistry(*corpus);if err!=nil {panic(err)}
  decks:=make([][]*cards.Card,4)
  commanders:=make([][]int,4)
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
    players:=make([]seat.Seat,4)
    for i:=0;i<4;i++ {
      k:=(i+g)%4
      ids[i]=names[k];ds[i]=decks[k];cs[i]=commanders[k]
      players[i],err=bots.New("bot",bots.Options{
        Seed:gs^uint64(i+1),AutoPayMana:true,Deps:bots.Deps{Cards:reg}})
      if err!=nil {panic(err)}
    }
    cfg:=rules.Config{Seed:gs,Names:ids,Decks:ds,Commanders:cs,
      Format:rules.FormatCommander,Tokens:reg.Tokens,NameUniverse:reg.Universe()}
    start:=time.Now()
    o,e,playErr:=bench.PlayGame(cfg,players,*maxTurns,400000,
      bench.Hooks{EnvSeats:true,HonestRoot:true})
    rec:=Result{Seed:gs,Decks:ids,Turns:o.Turns,Intents:o.Intents,
      Draw:o.Draw,StallReason:o.StallOn,ElapsedSeconds:time.Since(start).Seconds()}
    if e!=nil {rec.Events=len(e.L.Events)}
    if playErr!=nil {rec.Error=playErr.Error()}
    rec.Finished=playErr==nil&&!o.IsStalled()&&e!=nil&&e.G.Over
    if rec.Finished&&!o.Draw {
      w:=o.WinnerSeat;rec.WinnerSeat=&w
    }
    if rec.Finished&&*verify {
      reconstructed,rerr:=replay.Replay(e.L,cfg)
      if rerr==nil&&reconstructed!=nil&&reconstructed.L.Head()==e.L.Head(){
        rec.ReplayVerified=true
      }else{
        if rerr!=nil {rec.Error="replay: "+rerr.Error()} else {rec.Error="replay hash mismatch"}
      }
    }
    out,_:=json.Marshal(rec);fmt.Println(string(out))
    if rec.Error!=""||!rec.Finished||(*verify&&!rec.ReplayVerified){failed=true}
  }
  if failed {os.Exit(2)}
}
