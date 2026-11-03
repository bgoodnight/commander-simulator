"""Source-pinned game audits for the two owned Commander precons.

Real seat-zero legal-action game observations are compared with the existing
registered suboperation inventory; opponents are explicitly abstract.
Missing card registration is never equated with invalid printed Oracle text.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import run_bounded_early_game
from commander_sim.named_effect_coverage import named_effect_coverage
from tools.audit_effect_gaps import audit_effect_gaps,candidate_families

DECKS=("necron_dynasties","wretched_ranks")
SCENARIOS=("mixed","control")
GAP_TERMS=("unsupported","unmodeled","provisional","inconclusive","missing")
def run_cohort(deck, scenario, seeds,output):
    if deck not in DECKS or scenario not in SCENARIOS or seeds<1:
        raise ValueError("Unsupported precon/scenario/batch")
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("w",encoding="utf8") as f:
        for seed in range(seeds):
            try:
                run=run_bounded_early_game(deck,seed=seed,turns=25,
                    opponent_scenario=scenario,provisional_mode="safe",
                    pilot_style="adaptive",pilot_archetype="auto")
                row={"deck_key":deck,"scenario":scenario,"seed":seed,
                     "status":"completed","run":run}
            except Exception as exc:
                # Safety/correctness exceptions must be visible, NEVER losses.
                row={"deck_key":deck,"scenario":scenario,"seed":seed,
                     "status":"engine_error","error_type":type(exc).__name__,
                     "error":str(exc)}
            f.write(json.dumps(row,separators=(",",":"),default=str)+"\n")
    print(f"Saved {seeds} attempts: {deck} / {scenario}")

def summarize(source):
    fixture={f.key:f for f in FIXTURES if f.key in DECKS}
    named=named_effect_coverage(fixtures=tuple(fixture.values()))["decks"]
    gaps=audit_effect_gaps(tuple(fixture.values()))["by_deck"]
    evidence={deck:{"games":0,"engine_errors":[],"terminal":Counter(),
        "first_seen_unsupported":defaultdict(list),"unsupported_hand_turns":Counter(),
        "unsupported_events":Counter(),"provisional_events":Counter(),
        "action_events":Counter(),"narratives":[]} for deck in DECKS}
    keys=set()
    paths=sorted(Path(source).rglob("*.jsonl"))
    if not paths:raise ValueError("No game files")
    for p in paths:
        for line in p.read_text().splitlines():
            if not line.strip():continue
            row=json.loads(line)
            deck=row["deck_key"]
            if deck not in DECKS:raise ValueError("Unexpected deck")
            key=(deck,row["scenario"],row["seed"])
            if key in keys:raise ValueError("Repeated scenario seed")
            keys.add(key)
            x=evidence[deck]
            x["games"]+=1
            if row["status"]!="completed":
                x["engine_errors"].append({"scenario":row["scenario"],"seed":row["seed"],
                                          "type":row["error_type"],"detail":row["error"]})
                continue
            game=row["run"]
            x["terminal"][game["outcome"]["status"]]+=1
            turn_notes=[]
            for turn in game["events"]:
                n=turn["turn"]
                unsupported=turn.get("unsupported_cards_in_hand",[])
                for name in set(unsupported):
                    x["unsupported_hand_turns"][name]+=1
                    x["first_seen_unsupported"][name].append(
                        {"scenario":row["scenario"],"seed":row["seed"],"round":n})
                for event in turn.get("events",[]):
                    kind=str(event.get("type","unknown"))
                    x["action_events"][kind]+=1
                    if "unsupported" in kind or "unmodeled" in kind:
                        x["unsupported_events"][kind]+=1
                        turn_notes.append({"round":n,"type":kind,
                                           "card":event.get("card")})
                    elif any(v in kind for v in ("provisional","approx")):
                        x["provisional_events"][kind]+=1
            x["narratives"].append({"scenario":row["scenario"],"seed":row["seed"],
                "rounds":game["completed_rounds"],
                "outcome":game["outcome"]["status"],
                "opening_hand":game["mulligan"]["opening_hand"],
                "gap_events":turn_notes[:30],
                "unsupported_cards_final_hand":game["events"][-1]["unsupported_cards_in_hand"]
                    if game["events"] else []})
    result={"format":"two-precon-game-rules-audit-v1",
            "provenance":"real precon seat zero; three ABSTRACT opponent seats; no precon-vs-precon games",
            "decks":{},"attempts":len(keys),
            "limitations":["A card appearing unsupported in hand does not prove it was affordable or legal to cast that round",
                           "A named suboperation is not proof of full-card coverage",
                           "Printed-text ability family classification is diagnostic only",
                           "Abstract opponent cards, spells, resources and priority are not validated real precon gameplay",
                           "Outcomes are not meaningful head-to-head precon win rates"]}
    for deck,x in evidence.items():
        src=json.loads(fixture[deck].snapshot_path.read_text())["cards"]
        card_data={c["deck_name"]:c["card"] for c in src}
        card_gaps=[]
        for name,count in x["unsupported_hand_turns"].most_common():
            raw=card_data.get(name,{})
            registrations=named[deck]["cards"].get(name,{}).get("reviewed_suboperations",[])
            card_gaps.append({"card":name,"unsupported_hand_turns":count,
                              "games_seen":len(set((t["scenario"],t["seed"]) for t in
                                                  x["first_seen_unsupported"][name])),
                              "first_observations":x["first_seen_unsupported"][name][:8],
                              "printed_candidate_families":candidate_families(raw.get("oracle_text","")),
                              "registered_suboperations":registrations})
        result["decks"][deck]={
            "attempted_games":x["games"],"completed_games":sum(x["terminal"].values()),
            "engine_errors":x["engine_errors"],"terminal_statuses":dict(x["terminal"]),
            "static_registration_counts":gaps[deck]["status_counts"],
            "unsupported_cards_observed_in_hand":card_gaps,
            "unsupported_event_counts":dict(x["unsupported_events"]),
            "provisional_event_counts":dict(x["provisional_events"]),
            "action_event_counts":dict(x["action_events"]),
            "game_narrative_index":x["narratives"],
            "unregistered_printed_family_candidates":
                gaps[deck]["candidate_families_with_no_registered_recipe"]}
    return result

def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="cmd",required=True)
    run=sub.add_parser("run")
    run.add_argument("--deck",choices=DECKS,required=True)
    run.add_argument("--scenario",choices=SCENARIOS,required=True)
    run.add_argument("--seeds",type=int,default=5)
    run.add_argument("--output",type=Path,required=True)
    report=sub.add_parser("report")
    report.add_argument("--source",type=Path,required=True)
    report.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.cmd=="run":
        run_cohort(args.deck,args.scenario,args.seeds,args.output)
    else:
        result=summarize(args.source)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2,default=list)+"\n")
        print(json.dumps({"attempts":result["attempts"],
          "decks":{k:{"games":v["completed_games"],"errors":len(v["engine_errors"]),
                     "top_unsupported":v["unsupported_cards_observed_in_hand"][:8]}
                   for k,v in result["decks"].items()}},indent=2,default=list))
if __name__=="__main__":main()
