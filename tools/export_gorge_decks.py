"""Export pinned Commander fixture lists to gorge's ordinary deck-file format.

This is input conversion, not a rules-engine switch. No card scripts or
new Oracle abilities are generated or copied into the repository.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from commander_sim.deck_fixtures import FIXTURES

_LINE = re.compile(r"^(\d+)\s+(.+?)\s*$")


def export_deck(fixture):
    entries = []
    section = None
    for raw in fixture.deck_path.read_text(encoding="utf-8").splitlines():
        line=raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower() in {"commander","library","deck","mainboard"}:
            section = line.lower()
            continue
        if section not in {"commander","library","deck","mainboard"}:
            raise ValueError(f"Deck entry outside supported section: {line!r}")
        match = _LINE.fullmatch(line)
        if not match:
            raise ValueError(f"Unsupported deck entry: {line!r}")
        count=int(match.group(1))
        if count < 1:
            raise ValueError("Count must be positive")
        entries.append((match.group(2),count,section))
    if sum(count for _,count,_ in entries)!=100:
        raise ValueError(f"{fixture.key}: expected 100 physical cards")
    command=[name for name,count,section in entries if section=="commander"
             for _ in range(count)]
    if command!=[fixture.commander]:
        raise ValueError(f"{fixture.key}: commander section disagrees with pinned fixture")
    counts=Counter()
    for name,n,_ in entries:
        counts[name]+=n
    if counts[fixture.commander]!=1:
        raise ValueError("Commander must appear exactly once")
    raw=json.loads(fixture.snapshot_path.read_text(encoding="utf-8"))
    if raw.get("problems"):
        raise ValueError("Pinned identity snapshot has unresolved problems")
    pinned={item["deck_name"] for item in raw["cards"]}
    missing=sorted(set(counts)-pinned)
    if missing:
        raise ValueError("Deck names absent from pinned identities: "+", ".join(missing))
    # Commander must remain first for correct CommanderIndices in gorge.
    rows=[{"name":fixture.commander,"count":1}]
    rows.extend({"name":name,"count":count} for name,count in sorted(counts.items())
                if name!=fixture.commander)
    return {"name":fixture.key,"format":"commander",
            "commander":fixture.commander,"cards":rows}


def export_all(directory,deck_keys=None):
    root=Path(directory)
    root.mkdir(parents=True,exist_ok=True)
    keys=set(deck_keys) if deck_keys is not None else None
    fixtures=[f for f in FIXTURES if keys is None or f.key in keys]
    if keys is not None and len(fixtures)!=len(keys):
        raise ValueError("Unknown fixture key")
    result={}
    for f in fixtures:
        doc=export_deck(f)
        path=root/(f.key+".json")
        path.write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n",
                        encoding="utf-8")
        result[f.key]=str(path)
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--decks",nargs="*",default=None)
    a=p.parse_args()
    print(json.dumps(export_all(a.out,a.decks),indent=2))
