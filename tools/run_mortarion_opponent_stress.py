"""Seeded Mortarion opponent-pressure stress trial.

Uses real physical Mortarion cards, source-paid reviewed actions, and three
varied abstract adversary seats. These are NOT opponent decklists, legal
four-player matches, or Commander win-rate predictions. Narrative traces
are emitted to expose misplays and unsupported mechanics.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from commander_sim.early_game_runner import run_bounded_early_game
from commander_sim.opponent_stress import SCENARIOS


def summarize(runs, turns):
    counts=Counter()
    first=Counter()
    finished=[]
    life=[]
    for r in runs:
        ev=[e for phase in r["events"] for e in phase["events"]]
        counts.update(e["type"] for e in ev)
        played=next((phase["turn"] for phase in r["events"] if
                     any(e["type"]=="reviewed_commander_cast"
                         for e in phase["events"])),None)
        first[str(played) if played is not None else "never"]+=1
        finished.append(r["completed_turns"])
        life.append(r["life_totals"][0])
    return {
        "seeds":len(runs),
        "eliminated_by_horizon":sum(r["seat_zero_defeated"] for r in runs),
        "survived_by_horizon":sum(not r["seat_zero_defeated"] for r in runs),
        "average_turns_observed":round(sum(finished)/len(runs),2),
        "mean_life_at_last_observation":round(sum(life)/len(runs),2),
        "mean_last_hand_size":round(sum(
            r["events"][-1]["hand_size"] for r in runs)/len(runs),2),
        "mean_last_unsupported_hand_size":round(sum(
            len(r["events"][-1]["unsupported_cards_in_hand"])
            for r in runs)/len(runs),2),
        "mean_blocked_attacks_per_seed":round(
            counts["opponent_abstract_blocked_combat"]/len(runs),2),
        "mean_unblocked_damage_per_seed":round(sum(
            e.get("amount",0) for r in runs for phase in r["events"]
            for e in phase["events"]
            if e["type"]=="opponent_abstract_unblocked_damage")/len(runs),2),
        "commander_cast_turn_counts":dict(first),
        "events":dict(counts),
        "average_reviewed_removal_per_seed":round(
            counts["reviewed_removal_resolved"]/len(runs),2),
        "average_paid_mortarion_triggers_per_seed":round(
            counts["reviewed_composed_end_step"]/len(runs),2),
        "average_opponent_exiles_per_seed":round(
            counts["opponent_abstract_exile"]/len(runs),2),
    }


def narrative(r):
    return {
        "seed":r["seed"],"scenario":r["opponent_scenario"],
        "seat_roles":r["opponent_roles"],
        "eliminated":r["seat_zero_defeated"],
        "turns":[{
            "turn":phase["turn"],
            "life":phase["life_totals"].get(0),
            "lands":phase["land_count"],
            "creatures":phase["creature_count"],
            "hand_size":phase["hand_size"],
            "events":[
                {k:e[k] for k in ("type","card","seat","role","amount",
                                    "target_object_id","destroyed_count")
                 if k in e}
                for e in phase["events"]
                if e["type"] in {
                    "land_play","reviewed_commander_cast",
                    "reviewed_common_spell_resolved",
                    "reviewed_removal_resolved",
                    "reviewed_composed_activated",
                    "reviewed_composed_end_step",
                    "reviewed_precast_mana_sacrifice",
                    "reviewed_sacrifice_activated",
                    "reviewed_utility_activated",
                    "opponent_abstract_creature","opponent_abstract_exile",
                    "opponent_abstract_blocked_combat",
                    "opponent_abstract_unblocked_damage",
                    "reviewed_composed_upkeep",
                    "reviewed_enter_resolved",
                    "opponent_abstract_combo_loss","opponent_life_zero",
                    "opponent_reviewed_opponent_upkeep"}]
        } for phase in r["events"]]
    }


def run(*,seeds=24,turns=10):
    if not (1<=seeds<=200 and 1<=turns<=10):
        raise ValueError("Bounded opponent stress supports 1..200 seeds, 1..10 turns")
    results={}
    all_scenarios=("balanced","aggressive","control","combo")
    for scenario in all_scenarios:
        games=[run_bounded_early_game(
            "mortarion_physical_final",seed=i,turns=turns,
            opponent_scenario=scenario) for i in range(seeds)]
        results[scenario]={"summary":summarize(games,turns),
                           "narratives":[narrative(g) for g in games[:3]]}
    baseline=[run_bounded_early_game(
        "mortarion_physical_final",seed=i,turns=turns)
        for i in range(seeds)]
    results["goldfish"]={"summary":summarize(baseline,turns),
                        "narratives":[narrative(g) for g in baseline[:2]]}
    # Review signals flag rule/pilot questions, not conclusively prove a bug.
    anomalies=[]
    for scenario,entry in results.items():
        summary=entry["summary"]
        if (summary["events"].get("reviewed_removal_resolved",0)==0 and
                scenario!="goldfish"):
            anomalies.append({"scenario":scenario,
                              "issue":"No reviewed removal chosen against opponent board"})
        if summary["events"].get("reviewed_precast_mana_sacrifice",0)==0:
            anomalies.append({"scenario":scenario,
                              "issue":"No pre-cast mana-sacrifice conversion observed"})
        if summary["events"].get("unsupported_mana_preview_exhausted",0):
            anomalies.append({"scenario":scenario,
                              "issue":"Bounded mana-preview search budget exhausted"})
    return {
        "deck":"mortarion_physical_final","seeds_per_scenario":seeds,
        "turn_horizon":turns,"scenarios":results,
        "review_flags":anomalies,
        "warning":"Abstract enemy pressure, not real opponent deck mechanics or win rates; "
                  "no general combat/blockers, opponent spell priority or tuned targeting."
    }


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--seeds",type=int,default=24)
    p.add_argument("--turns",type=int,default=10)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    r=run(seeds=a.seeds,turns=a.turns)
    if a.output:
        a.output.write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8")
    for scenario,entry in r["scenarios"].items():
        print("OPPONENT_STRESS",json.dumps({"scenario":scenario,
                                            **entry["summary"]},sort_keys=True),
              flush=True)
    print("NARRATIVE_REVIEW_FLAGS",json.dumps(r["review_flags"]),flush=True)
