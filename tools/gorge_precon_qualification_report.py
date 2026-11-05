"""Per-deck empirical qualification of staged official precons.

Six exposures from two heroes demonstrate bounded stability, not card-mechanics
or pilot fidelity. Never promote to production/approved analytical cohorts.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

SCHEMA = "gorge-precon-qualification-evidence-v1"
HEROES = ("mortarion_current", "magnus_premium")


def report(queue, by_hero):
    if queue.get("schema") != "gorge-precon-qualification-queue-v1":
        raise ValueError("Unexpected queue schema")
    decks = queue.get("decks")
    if not isinstance(decks, list) or len(decks) != 60 or len({d["key"] for d in decks}) != 60:
        raise ValueError("Expected exact 60 candidate queue")
    if set(by_hero) != set(HEROES):
        raise ValueError("Both named hero trials required")
    by_deck = defaultdict(lambda: defaultdict(list))
    for hero in HEROES:
        games = by_hero[hero]
        if len(games) != 60 or {r.get("seed") for r in games} != set(range(186000,186060)):
            raise ValueError("Trial must contain 60 distinct, fixed seeds")
        for r in games:
            seat = r.get("hero_seat")
            names = r.get("decks")
            if (type(seat) is not int or seat not in range(4)
                    or not isinstance(names,list) or len(names)!=4
                    or len(set(names))!=4 or names[seat]!=hero):
                raise ValueError("Invalid hero or opponent seat")
            for i,key in enumerate(names):
                if i == seat:
                    continue
                if key not in {d["key"] for d in decks}:
                    raise ValueError("Non-stock or unknown opponent entered trial")
                by_deck[key][hero].append(r)
    rows = []
    for d in decks:
        observations = {}
        for hero in HEROES:
            games = by_deck[d["key"]][hero]
            observations[hero] = {
                "exposed": len(games),
                "finished_replay_verified": sum(r.get("finished") is True and
                    r.get("replay_verified") is True and not r.get("error") and
                    r.get("draw") is False and type(r.get("winner_seat")) is int
                    for r in games),
                "turn_cap": sum(r.get("stall_reason") == "turns" for r in games),
                "engine_error": sum(bool(r.get("error")) for r in games),
                "seeds": [r["seed"] for r in games],
            }
        stable = (d.get("oracle_complete") is True and
                  all(x["exposed"] >= 3 and
                      x["finished_replay_verified"] == x["exposed"] and
                      x["engine_error"] == 0 and x["turn_cap"] == 0
                      for x in observations.values()))
        rows.append({
            "key": d["key"], "name": d["name"], "commander": d["commander"],
            "color_identity": d["color_identity"],
            "decklist_sha256": d["decklist_sha256"],
            "oracle_complete": d["oracle_complete"],
            "observations": observations,
            "bounded_stability": "passed" if stable else "needs_review",
            "rules_fidelity": "not_certified",
            "pilot_fidelity": "not_certified",
            "production_eligible": False,
            "trial_opponent_eligible": stable,
        })
    return {
        "schema": SCHEMA,
        "source_oracle_sha256": queue["oracle_bulk_sha256"],
        "source_catalog_commit": queue["source_catalog_commit"],
        "source_seeds": [186000, 186059],
        "panel_size": 60,
        "eligible_bounded_trial": sum(d["trial_opponent_eligible"] for d in rows),
        "approved_production_opponents": 0,
        "limitations": "Each precon has three exposures per hero. Passing shows bounded stability only; requires independent rules/pilot review before production.",
        "decks": rows,
    }


def select_trial_pool(evidence, proposed):
    if evidence.get("schema") != SCHEMA or proposed.get("schema") != "gorge-initial-trial-opponents-v1":
        raise ValueError("Wrong evidence or requested trial panel")
    if evidence.get("source_oracle_sha256") != proposed.get("source_oracle_sha256"):
        raise ValueError("Oracle panel provenance mismatch")
    rows = {r["key"]: r for r in evidence["decks"]}
    keys = proposed.get("opponents")
    if not isinstance(keys,list) or len(keys) < 3 or len(set(keys)) != len(keys):
        raise ValueError("Trial requires distinct named precons")
    for key in keys:
        r = rows.get(key)
        if r is None or not r["trial_opponent_eligible"] or r["production_eligible"]:
            raise ValueError(f"{key}: not a validated bounded experimental opponent")
        if any(r.get(field)!="not_certified" for field in ("rules_fidelity","pilot_fidelity")):
            raise ValueError("Unexpected qualification declaration")
    return {"schema": "gorge-experimental-opponent-pool-v1",
            "status": "experimental_rotation_only",
            "oracle_sha256": evidence["source_oracle_sha256"],
            "opponents": keys,
            "production_approved": False,
            "eligible_for_analytics": False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--queue",required=True,type=Path)
    p.add_argument("--mortarion",required=True,type=Path)
    p.add_argument("--magnus",required=True,type=Path)
    p.add_argument("--panel",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    def read_run(path):
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    queue=json.loads(a.queue.read_text())
    evidence=report(queue,{"mortarion_current":read_run(a.mortarion),
                           "magnus_premium":read_run(a.magnus)})
    trial=select_trial_pool(evidence,json.loads(a.panel.read_text()))
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"precon-qualification.json").write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    (a.out/"experimental-opponents.json").write_text(json.dumps(trial,indent=2,sort_keys=True)+"\n")
    (a.out/"opponents.txt").write_text(",".join(trial["opponents"])+"\n")
    print(json.dumps({"stable_for_bounded_trial":evidence["eligible_bounded_trial"],
                      "initial_experimental_opponents":len(trial["opponents"]),
                      "approved_production_opponents":0}))


if __name__ == "__main__":
    main()
