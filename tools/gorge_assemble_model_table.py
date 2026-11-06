"""Join Gorge native landmark features to one-hero game outcomes.

Creates one row per observed/missing global-turn landmark. Never forward fills
missing snapshots and never uses postgame game duration as a predictor.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def assemble(games:list[dict], landmarks:list[dict], events:list[dict]|None=None)->list[dict]:
    event_lookup={}
    if events is not None:
        for e in events:
            key=(e.get('seed'),e.get('landmark_global_turn'))
            if key in event_lookup:
                raise ValueError('Duplicate event-feature landmark')
            event_lookup[key]=e
    by_seed={}
    for r in games:
        seed=r.get("seed")
        if type(seed) is not int or seed in by_seed:
            raise ValueError("Invalid or duplicate game seed")
        by_seed[seed]=r
    seen=set()
    output=[]
    for l in landmarks:
        seed=l.get("seed")
        t=l.get("landmark_global_turn")
        key=(seed,t)
        if key in seen:
            raise ValueError("Duplicate game/landmark")
        seen.add(key)
        game=by_seed.get(seed)
        if game is None or game.get("deck")!=l.get("hero"):
            raise ValueError("Landmark without matching hero game")
        if events is not None and key not in event_lookup:
            raise ValueError("Missing event feature row at landmark")
        # The existence of a source snapshot is not enough to establish
        # that the hero was still alive or the game was nonterminal.
        # Terminal timing must be added from verified event history before
        # fitting landmark survival-risk models.
        out={
          "seed":seed,"deck":game["deck"],
          "hero_seat":game.get("hero_seat"),
          "opponent_decks":game.get("opponent_decks"),
          "landmark_global_turn":t,
          "landmark_observed":l.get("landmark_observed") is True,
          "native_available":l.get("native_available") is True,
          "status":game.get("status"),
          "won":game.get("won"),
          "first_decision_opening_basic_lands":game.get("opening_basic_lands"),
          "first_decision_sol_ring":game.get("opening_sol_ring"),
          "first_decision_arcane_signet":game.get("opening_arcane_signet"),
          "source_sha256":game.get("source_sha256"),
          "source_snapshot_index":l.get("source_snapshot_index"),
          "source_event_seq":l.get("source_event_seq"),
          "hero_life":l.get("hero_life"),
          "hero_hand_count":l.get("hero_hand_count"),
          "hero_battlefield_count":l.get("hero_battlefield_count"),
          "hero_graveyard_count":l.get("hero_graveyard_count"),
          "hero_basic_lands_on_battlefield":l.get("hero_basic_lands_on_battlefield"),
          "hero_tokens_on_battlefield":l.get("hero_tokens_on_battlefield"),
          "model_eligible":False,
          "model_eligibility_reason":"Requires verified terminal-time risk set and cohort approval",
        }
        if not out["landmark_observed"]:
            for f in ("hero_life","hero_hand_count","hero_battlefield_count",
                      "hero_graveyard_count","hero_basic_lands_on_battlefield",
                      "hero_tokens_on_battlefield"):
                if out[f] is not None:
                    raise ValueError("Missing landmark carries non-null derived state")
        if events is not None:
            ev=event_lookup[key]
            if ev.get("hero") != out["deck"] or (ev.get("landmark_observed") is True) != out["landmark_observed"]:
                raise ValueError("Event feature identity/landmark mismatch")
            if ev.get("landmark_observed") and ev.get("event_cutoff_seq") != out["source_event_seq"]:
                raise ValueError("Event cutoff differs from snapshot evidence")
            for field in ("pod_cast_events","pod_mana_events","pod_land_play_events",
                          "pod_token_creation_events","pod_ability_activation_events",
                          "pod_trigger_events","pod_damage_events",
                          "hero_owned_card_cast_events","hero_owned_card_cast_unique_cards",
                          "hero_owned_cast_attribution_complete",
                          "sacrifice_event_count","hero_mana_generated","hero_spell_cost_reduction"):
                out[field]=ev.get(field)
            out["event_evidence_sequences"]=ev.get("evidence_event_sequences")
        output.append(out)
    # Ensure no game silently disappears from a given landmark if a batch
    # has explicit landmark specifications.
    if not output:
        raise ValueError("No joined landmark rows")
    if events is not None and set(event_lookup)!=seen:
        raise ValueError("Unexpected extra event-feature landmark")
    return sorted(output,key=lambda r:(r["seed"],r["landmark_global_turn"]))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--games",type=Path,required=True)
    p.add_argument("--landmarks",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--events",type=Path)
    a=p.parse_args()
    read=lambda path:[json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    rows=assemble(read(a.games),read(a.landmarks),read(a.events) if a.events else None)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text("".join(json.dumps(x,sort_keys=True)+"\n" for x in rows))
    print(json.dumps({"rows":len(rows),"observed":sum(x["landmark_observed"] for x in rows),
                      "model_eligible":0,"status":"analytic_table_not_approved"}))


if __name__=="__main__":
    main()
