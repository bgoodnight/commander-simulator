"""Stream sparse card features one Gorge game at a time."""
import argparse
import json
from pathlib import Path
from tools.gorge_sparse_card_features import extract_card_rows

def stream(root, hero, run_attempt, output, turns=(4,8,12)):
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    counts={"attempts":0,"native":0,"rows":0,"missing":[]}
    seen=set()
    with output.open("w") as target:
        for runfile in sorted(Path(root).rglob("runs.jsonl")):
            for line in runfile.read_text().splitlines():
                if not line.strip(): continue
                run=json.loads(line)
                seat=run.get("hero_seat")
                decks=run.get("decks")
                if not isinstance(decks,list) or type(seat) is not int or seat not in range(4):
                    continue
                if decks[seat]!=hero: continue
                seed=run["seed"]
                if seed in seen: raise ValueError("Duplicate seed")
                seen.add(seed)
                counts["attempts"]+=1
                source=runfile.parent/"native"/f"gorge-seed-{seed}.json"
                if not source.exists():
                    counts["missing"].append(seed)
                    continue
                native=json.loads(source.read_text())
                if native.get("seed")!=seed or native.get("chain")!=run.get("replay_chain") or native.get("decks")!=decks:
                    raise ValueError("Native source mismatch")
                rows,_=extract_card_rows(native,seat,run_attempt,turns)
                for row in rows: target.write(json.dumps(row,sort_keys=True)+"\n")
                counts["native"]+=1
                counts["rows"]+=len(rows)
    if not counts["attempts"]: raise ValueError("No matching games")
    return counts

def main():
    p=argparse.ArgumentParser()
    for arg in ("native-root","hero","run-attempt","output"):
        p.add_argument("--"+arg,required=True)
    a=p.parse_args()
    print(json.dumps(stream(a.native_root,a.hero,a.run_attempt,a.output),sort_keys=True))

if __name__=="__main__":main()
