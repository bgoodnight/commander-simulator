"""Inspect conservative import-derived card support without changing game state.

Works with any completed pinned M1 snapshot, including a new deck that is not
registered in historical fixtures. Emits machine-readable fidelity and
omissions for a UI/import review queue. This tool does not cast anything.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from commander_sim.deck_fixtures import FIXTURES, EXPERIMENTAL_FIXTURES
from commander_sim.provisional_import import provisional_report

def inspect_snapshot(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data.get("cards"),list):
        raise ValueError("Expected complete Scryfall snapshot card list")
    rows=provisional_report(data["cards"])
    counts=dict(Counter(x["status"] for x in rows))
    kinds=dict(Counter(x["kind"] for x in rows if x["kind"] is not None))
    return {"snapshot":str(path),"total_cards":len(rows),
            "counts":counts,"provisional_kinds":kinds,"cards":rows,
            "notice":"Provisional profiles are incomplete and never override "
                     "more specific pinned reviewed rules. Unknown effects "
                     "do not execute. Fixed costs and physical legality "
                     "still gate all actions."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--snapshot",type=Path,
                   help="Pinned card snapshot JSON from any newly imported deck")
    g.add_argument("--all",action="store_true",
                   help="Audit all existing deck fixtures")
    p.add_argument("--output",type=Path,
                   help="Write JSON file for UI import report")
    a=p.parse_args()
    if a.all:
        out={fixture.key:inspect_snapshot(fixture.snapshot_path)
             for fixture in (*FIXTURES,*EXPERIMENTAL_FIXTURES)}
    else:
        out=inspect_snapshot(a.snapshot)
    result=json.dumps(out,indent=2)+"\n"
    if a.output:a.output.write_text(result,encoding="utf-8")
    print(result,end="")

if __name__=="__main__":
    main()
