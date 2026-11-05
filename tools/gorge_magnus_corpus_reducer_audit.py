"""Audit key cost-reducer fields from pinned private Forge corpus scripts.

Emit only scoped syntactic facts. This is *not* a functional cost test.
"""
import json
from pathlib import Path
import sys

root=Path(sys.argv[1])
names={
  "Magnus the Red":("magnus","the_red"),
  "Baral, Chief of Compliance":("baral",),
  "Goblin Electromancer":("goblin","electromancer"),
  "Stormcatch Mentor":("stormcatch",),
  "Primal Amulet":("primal","amulet"),
}
def check(name,parts):
    candidates=[p for p in root.rglob("*.txt") if all(x in p.stem.lower() for x in parts)]
    if not candidates: return {"card":name,"script_found":False}
    text=candidates[0].read_text(errors="replace")
    static=[line for line in text.splitlines() if line.startswith("S:") and "ReduceCost" in line]
    svars={s.split(":",2)[1]:s.split(":",2)[2] for s in text.splitlines() if s.startswith("SVar:") and s.count(":")>=2}
    arms=[]
    for line in static:
        chunks=[t.strip() for t in line[2:].split("|")]
        params={x.split("$",1)[0].strip():x.split("$",1)[1].strip() for x in chunks if "$" in x}
        amount=params.get("Amount")
        meaning=svars.get(amount,amount)
        arms.append({"type":params.get("Type"),"valid_card":params.get("ValidCard"),
             "valid_spell":params.get("ValidSpell"),"caster":params.get("Activator") or params.get("Caster"),
             "amount_expression":meaning,"dynamic":bool(meaning and "Count$" in meaning)})
    return {"card":name,"script_found":True,"reduce_arms":arms}
out={"scope":"pinned Forge corpus script fields only; no behavior claim",
     "cards":[check(n,v) for n,v in names.items()]}
print("MAGNUS_CORPUS_STATIC "+json.dumps(out,sort_keys=True))
