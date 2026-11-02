"""Review seeded physical Commander games, action by action, without UI changes.

Each report separates unsupported action opportunities, heuristic choices, and
actual modeled outcomes. An absence of an observed action is *not* proof that a
legal action existed. This audit never changes combat, priority, or card rules.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import median
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from commander_sim.deck_fixtures import FIXTURES,EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import run_bounded_early_game
from commander_sim.opponent_stress import SCENARIOS
from commander_sim.pilot_policy import STYLES

DECKS=tuple(f.key for f in (*FIXTURES,*EXPERIMENTAL_FIXTURES))
FORMAT="commander-pilot-narrative-audit-v1"


def summarize_run(run,*,turn_examples=12):
    if (not isinstance(run,dict) or type(turn_examples) is not int
            or not 1<=turn_examples<=30):
        raise ValueError("Invalid pilot narrative")
    action_counts=Counter()
    role_counts=Counter()
    unmodeled=Counter()
    problem_turns=[]
    timeline=[]
    for item in run["events"]:
        turn=item["turn"]
        events=item["events"]
        choices=item.get("pilot_decisions",[])
        for event in events:
            action_counts[event["type"]]+=1
        for choice in choices:
            role_counts[choice["role"]]+=1
        for name in item["unsupported_cards_in_hand"]:
            unmodeled[name]+=1
        # Heuristic diagnostics are suggestions for narrative review, not
        # legal or factual accusations that the engine is incorrect.
        diagnostics=[]
        if not choices and len(item["unsupported_cards_in_hand"])>=3:
            diagnostics.append("idle_with_unimplemented_hand")
        if (turn>=8 and item["resource_start"]["available_fixed_mana"]>=9
                and any(c["role"]=="ramp" for c in choices)):
            diagnostics.append("late_ramp_even_with_mana")
        if (item.get("cleanup_discard_count",0)>0
                and any(c["role"]=="draw" for c in choices)):
            diagnostics.append("draw_then_cleanup")
        if (run["opponent_scenario"] is not None
                and item["life_totals"][0]<=15
                and len(item.get("alive_seats",[]))>=2
                and not any(c["role"]=="removal" for c in choices)):
            diagnostics.append("low_life_no_selected_removal")
        if diagnostics:
            problem_turns.append({"turn":turn,"signals":diagnostics})
        if turn<=turn_examples:
            timeline.append({
                "turn":turn,
                "life_totals":item["life_totals"],
                "mana_at_start":item["resource_start"]["available_fixed_mana"],
                "hand_size":item["hand_size"],
                "creatures":item["creature_count"],
                "lands":item["land_count"],
                "unsupported_in_hand":list(item["unsupported_cards_in_hand"]),
                "pilot_choices":list(choices),
                "pilot_combat":item.get("pilot_combat"),
                "events":[{"type":e["type"],
                           **({"card":e["card"]} if "card" in e else {}),
                           **({"target_seat":e["target_seat"]}
                              if "target_seat" in e else {}),
                           **({"amount":e["amount"]}
                              if "amount" in e else {})}
                          for e in events],
                "life_changes":item.get("life_changes",[]),
                "review_signals":diagnostics,
            })
    return {
        "deck_key":run["deck_key"],
        "deck_sha256":run["deck_sha256"],
        "seed":run["seed"],
        "scenario":run["opponent_scenario"],
        "pilot_style":run.get("pilot_style"),
        "provisional_mode":run["provisional_mode"],
        "pilot_signals":run.get("pilot_signals"),
        "completed_rounds":run["completed_rounds"],
        "outcome":run["outcome"]["status"],
        "end_life":run["life_totals"],
        "decisions_by_role":dict(sorted(role_counts.items())),
        "event_counts":dict(sorted(action_counts.items())),
        "turns_without_main_actions":sum(
            not x.get("pilot_decisions") for x in run["events"]),
        "attackers_committed":sum(
            (x.get("pilot_combat") or {}).get("selected_attackers",0)
            for x in run["events"]),
        "frequently_unmodeled_hand_cards":[
            {"card":name,"turns_seen":count}
            for name,count in unmodeled.most_common(12)],
        "review_turns":problem_turns,
        "sample_timeline":timeline,
    }


def run_audit(deck_keys=DECKS,*,seeds=2,rounds=12,
              scenario="mixed",style="adaptive",
              provisional_mode="safe",first_seed=0,
              turn_examples=12,runner=run_bounded_early_game):
    if (not deck_keys or any(d not in DECKS for d in deck_keys)
            or type(seeds) is not int or not 1<=seeds<=15
            or type(rounds) is not int or not 1<=rounds<=30
            or type(first_seed) is not int or first_seed<0
            or scenario not in SCENARIOS or style not in STYLES
            or provisional_mode not in {"off","safe"}
            or type(turn_examples) is not int or not 1<=turn_examples<=30):
        raise ValueError("Invalid narrative audit configuration")
    runs=[]
    for deck in deck_keys:
        for seed in range(first_seed,first_seed+seeds):
            run=runner(deck,seed=seed,turns=rounds,
                opponent_scenario=scenario,
                pilot_style=style,provisional_mode=provisional_mode)
            runs.append(summarize_run(run,turn_examples=turn_examples))
    by_deck={}
    for key in deck_keys:
        matches=[row for row in runs if row["deck_key"]==key]
        outcomes=Counter(row["outcome"] for row in matches)
        unmodeled=Counter()
        for row in matches:
            for item in row["frequently_unmodeled_hand_cards"]:
                unmodeled[item["card"]]+=item["turns_seen"]
        by_deck[key]={
            "sample_games":len(matches),
            "outcomes":dict(sorted(outcomes.items())),
            "median_completed_rounds":median(
                x["completed_rounds"] for x in matches),
            "idle_turns":sum(x["turns_without_main_actions"] for x in matches),
            "review_signal_counts":dict(sorted(Counter(
                label for run in matches for row in run["review_turns"]
                for label in row["signals"]).items())),
            "priority_unmodeled_cards":[
                {"card":name,"observed_turns":count}
                for name,count in unmodeled.most_common(12)],
        }
    return {
        "format":FORMAT,
        "configuration":{"deck_keys":list(deck_keys),"seeds":seeds,
            "first_seed":first_seed,"rounds":rounds,"scenario":scenario,
            "style":style,"provisional_mode":provisional_mode},
        "deck_summaries":by_deck,"runs":runs,
        "disclaimer":(
            "Narrative choices were source-paid and ordered by a bounded pilot; "
            "review signals are advisory, and unmodeled card text is not "
            "permission to cast. Opponents are abstract policies, not decks."),
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deck",choices=("all",)+DECKS,default="all")
    parser.add_argument("--seeds",type=int,default=2)
    parser.add_argument("--rounds",type=int,default=12)
    parser.add_argument("--scenario",choices=sorted(SCENARIOS),default="mixed")
    parser.add_argument("--pilot-style",choices=STYLES,default="adaptive")
    parser.add_argument("--provisional-mode",choices=("off","safe"),default="safe")
    parser.add_argument("--first-seed",type=int,default=0)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv)
    keys=DECKS if args.deck=="all" else (args.deck,)
    result=run_audit(keys,seeds=args.seeds,rounds=args.rounds,
        scenario=args.scenario,style=args.pilot_style,
        provisional_mode=args.provisional_mode,first_seed=args.first_seed)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(
        result,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps(result["deck_summaries"],sort_keys=True,indent=2))
    print("Wrote",len(result["runs"]),"seeded narrative reviews to",args.output)


if __name__=="__main__":
    main()
