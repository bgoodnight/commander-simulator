"""Safe, evidence-only projection of gorge's authoritative turn-entry states.

NEVER copy hidden hand/library object IDs or their order to the public UI.
"""
def project(source):
    if source.get("enrichment_schema")!="gorge-physical-state-v1":
        return []
    objects=source.get("objects")
    snaps=source.get("snapshots")
    if not isinstance(objects,list) or not isinstance(snaps,list) or not snaps:
        raise ValueError("Missing gorge physical state")
    by_id={}
    for obj in objects:
        oid=obj.get("object_id")
        if type(oid) is not int or oid<1 or oid in by_id:
            raise ValueError("Invalid/duplicate object")
        by_id[oid]=obj
    if not set(range(1,401)).issubset(by_id):
        raise ValueError("Incomplete 400-card identity pool")
    if any(not by_id[i].get("card_name") for i in range(1,401)):
        raise ValueError("Unknown printed card")
    output=[]
    last_turn=0
    for snap in snaps:
        turn=snap.get("turn")
        if (type(turn) is not int or turn<=last_turn
            or snap.get("boundary")!="first_pending_decision_of_turn"
            or type(snap.get("after_event_seq")) is not int):
            raise ValueError("Invalid snapshot boundary")
        last_turn=turn
        players=snap.get("players")
        if not isinstance(players,list) or len(players)!=4:
            raise ValueError("Not four seats")
        visible_players=[]
        seen=set()
        for seat,p in enumerate(players):
            zones=p.get("zones")
            pool=p.get("mana_pool")
            if (p.get("seat")!=seat or type(p.get("life")) is not int
                or type(p.get("lost")) is not bool
                or not isinstance(pool,list) or len(pool)!=6
                or any(type(n) is not int or n<0 for n in pool)
                or not isinstance(zones,dict)):
                raise ValueError("Invalid player snapshot")
            for key in ("hand","library","battlefield","graveyard","exile","command"):
                if not isinstance(zones.get(key),list):
                    raise ValueError("Missing zone "+key)
            public_zones={}
            for key in ("battlefield","graveyard","exile","command"):
                entries=[]
                for oid in zones[key]:
                    if type(oid) is not int or oid not in by_id or oid in seen:
                        raise ValueError("Invalid or duplicated zone object")
                    seen.add(oid)
                    card=by_id[oid]
                    name=card.get("card_name") or card.get("effective_name")
                    if not isinstance(name,str) or not name:
                        raise ValueError("No name for public permanent")
                    entries.append({"object_id":oid,"name":name,
                                    "token":bool(card.get("is_token"))})
                public_zones[key]=entries
            visible_players.append({
                "seat":seat,"life":p["life"],"lost":p["lost"],
                "mana_pool":list(pool),
                "hand_count":len(zones["hand"]),
                "library_count":len(zones["library"]),
                "zones":public_zones,
            })
        output.append({"turn":turn,"active_seat":snap.get("active_seat"),
            "step":snap.get("step"),"boundary":snap["boundary"],
            "after_event_seq":snap["after_event_seq"],
            "players":visible_players})
    if any(p["life"]!=40 for p in output[0]["players"]):
        raise ValueError("Not a 40-life Commander game")
    return output
