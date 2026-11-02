"""Replay-ready, source-traced life and outcome observations for four-seat runs.

This *reads* the authoritative kernel life ledger; no shadow life engine and
no invented opponent-card activity. Only zero-life modeled eliminations are
supported. Commander damage, poison, concession, alternative victory,
replacement/priority, and opponent deck fidelity require separate engines.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Elimination:
    seat: int
    round: int
    cause: str
    source_object_id: int | None
    life_after: int

    def as_dict(self):
        return {"seat":self.seat,"round":self.round,"cause":self.cause,
                "source_object_id":self.source_object_id,
                "life_after":self.life_after}


class LifeOutcomeRecorder:
    def __init__(self, initial_totals, *, opponent_model=False):
        if (not isinstance(initial_totals,dict)
                or set(initial_totals)!=set(range(4))
                or any(type(n) is not int or n<=0
                       for n in initial_totals.values())
                or type(opponent_model) is not bool):
            raise ValueError("Expected four positive physical starting totals")
        self.initial=dict(initial_totals)
        self.current=dict(initial_totals)
        self.opponent_model=opponent_model
        self.eliminations={}
        self.post_elimination_effects=[]
        self.history=[{"round":0,"life_totals":dict(initial_totals),
                       "alive_seats":list(range(4)),
                       "new_eliminations":[],"life_changes":[]}]

    def record_round(self, round_id, life_changes, final_totals):
        """Verify ordered ledger continuity and persist every physical delta."""
        if (type(round_id) is not int or round_id!=len(self.history)
                or not isinstance(final_totals,dict)
                or set(final_totals)!=set(self.initial)
                or any(type(n) is not int for n in final_totals.values())):
            raise ValueError("Out-of-order or incompatible life observation")
        previous=dict(self.current)
        changes=[]
        new_eliminations=[]
        for entry in life_changes:
            seat=entry.seat
            if (seat not in previous or entry.kind not in {"gain","loss","damage"}
                    or type(entry.amount) is not int or entry.amount<0):
                raise ValueError("Unrecognized kernel life ledger event")
            before=previous[seat]
            after=before+entry.amount if entry.kind=="gain" else before-entry.amount
            delta=after-before
            row={"seat":seat,"kind":entry.kind,"amount":entry.amount,
                 "delta":delta,"before":before,"after":after,
                 "source_object_id":entry.source_id}
            if seat in self.eliminations:
                # The bounded host may still run an unsupported effect on a
                # life-zero seat. Log rather than 'resurrect' that player.
                self.post_elimination_effects.append({
                    "round":round_id,**row})
            changes.append(row)
            previous[seat]=after
            if after<=0 and seat not in self.eliminations:
                defeated=Elimination(seat,round_id,"modeled_life_zero",
                                     entry.source_id,after)
                self.eliminations[seat]=defeated
                new_eliminations.append(defeated.as_dict())
        if previous!=final_totals:
            raise AssertionError("Life ledger does not reconcile to kernel totals")
        for seat,total in previous.items():
            if total<=0 and seat not in self.eliminations:
                defeated=Elimination(seat,round_id,"modeled_life_zero",None,total)
                self.eliminations[seat]=defeated
                new_eliminations.append(defeated.as_dict())
        self.current=previous
        record={"round":round_id,"life_totals":dict(previous),
                "alive_seats":[s for s in range(4)
                               if s not in self.eliminations],
                "new_eliminations":new_eliminations,
                "life_changes":changes}
        self.history.append(record)
        return record

    def outcome(self, *, requested_rounds):
        if (type(requested_rounds) is not int or requested_rounds<1
                or len(self.history)<1):
            raise ValueError("Invalid outcome horizon")
        living=[s for s in range(4) if s not in self.eliminations]
        if not self.opponent_model:
            status,reason,winner="not_evaluated","no_opponent_game_model",None
        elif not living:
            status,reason,winner="draw","all_seats_reached_zero_life",None
        elif 0 not in living:
            status,reason,winner="loss","pilot_life_zero",living[0] if len(living)==1 else None
        elif living==[0]:
            status,reason,winner="win","all_opponents_life_zero",0
        else:
            status,reason,winner="unresolved","round_limit",None
        complete=self.opponent_model and status in {"win","loss","draw"}
        return {
            "status":status,"reason":reason,
            "winner_seat":winner,
            "pilot_seat":0,
            "complete":complete,
            "requested_rounds":requested_rounds,
            "completed_rounds":len(self.history)-1,
            "surviving_seats":living,
            "eliminations":[self.eliminations[s].as_dict()
                            for s in sorted(self.eliminations,
                                            key=lambda key:(
                                                self.eliminations[key].round,key))],
            "post_elimination_life_effects":list(self.post_elimination_effects),
            "fidelity":("abstract_opponent_pressure_not_real_decks"
                        if self.opponent_model else "goldfish_no_opponents"),
            "rules_limits":[
                "Only life-zero eliminations are detected",
                "No commander-damage, poison, concession or alternate-win checks",
                "Abstract opponents are not playable 100-card decks",
                "No complete priority/stack or simultaneous elimination rules",
            ],
        }
