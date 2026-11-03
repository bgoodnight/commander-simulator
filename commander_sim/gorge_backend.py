"""Opt-in native gorge rules backend for four-player Commander batches.

All card rules, legal actions and AI decisions are evaluated by the pinned
external gorge executable, not by the Python approximation kernel. Does not
fetch card scripts, compile Go, or modify our own authoritative Python state.

Run only after explicitly preparing the external engine and deck library:
  python -m commander_sim.gorge_backend --binary /tmp/commander-probe \
    --corpus /tmp/gorge/.cards --deck-dir /tmp/gorge-decks \
    --decks mortarion_current,magnus_premium,necron_dynasties,wretched_ranks \
    --games 8 --pilot bot --native-dir /tmp/recordings
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess

PILOTS=frozenset({"bot","forge-heuristic","forge-heuristic-hold",
                  "lethal-pressure"})


class GorgeBackendError(RuntimeError):
    """Explicit external-execution, validation or engine failure."""


def run_gorge_batch(*, binary, corpus, deck_dir, decks, games=8, seed=0,
                    max_turns=50, pilot="bot", hero_pilot=None,
                    native_dir=None, native_limit=2, timeout=300):
    """Return versioned metadata and unmodified gorge game summaries.

    A raw trace directory contains full hidden zones and must be secured.
    This function NEVER treats a source-name match as card-rule authorization.
    It is an adapter around gorge's real kernel, not a replacement rules loop.
    """
    if type(games) is not int or games<1 or games>1000:
        raise ValueError("games must be in 1..1000")
    if type(seed) is not int or seed<0 or type(max_turns) is not int or max_turns<1:
        raise ValueError("invalid simulation seed or turn cap")
    if type(native_limit) is not int or not 0<=native_limit<=100:
        raise ValueError("invalid native trace count")
    if pilot not in PILOTS or (hero_pilot is not None and hero_pilot not in PILOTS):
        raise ValueError("unsupported gorge Commander AI pilot")
    if not isinstance(decks,(list,tuple)) or len(decks)<4:
        raise ValueError("provide at least four deck names")
    if len(set(decks))!=len(decks) or any(
            not isinstance(name,str) or not name
            or "/" in name or ".." in name or "," in name
            for name in decks):
        raise ValueError("invalid or duplicate deck name")
    path=Path(binary)
    root=Path(corpus)
    deckpath=Path(deck_dir)
    if not path.is_file():
        raise FileNotFoundError("gorge executable is not built")
    if not root.is_dir() or not deckpath.is_dir():
        raise FileNotFoundError("gorge corpus and deck folder must exist")
    for name in decks:
        if not (deckpath/(name+".json")).is_file():
            raise FileNotFoundError("missing gorge deck: "+name)
    cmd=[str(path.resolve()),
         "-corpus",str(root.resolve()),"-deck-dir",str(deckpath.resolve()),
         "-decks",",".join(decks),"-games",str(games),
         "-seed",str(seed),"-max-turns",str(max_turns),
         "-verify=true","-pilot",pilot,"-native-limit",str(native_limit)]
    if hero_pilot is not None:
        cmd+=["-hero-pilot",hero_pilot]
    if native_dir is not None:
        output=Path(native_dir)
        output.mkdir(parents=True,exist_ok=True)
        cmd+=["-native-dir",str(output.resolve())]
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,
                         timeout=timeout,check=False)
    except subprocess.TimeoutExpired as exc:
        raise GorgeBackendError("gorge backend timed out") from exc
    results=[]
    for line in p.stdout.splitlines():
        if not line.strip():
            continue
        try:
            row=json.loads(line)
        except json.JSONDecodeError as exc:
            raise GorgeBackendError("gorge emitted non-JSON output") from exc
        if (not isinstance(row,dict) or type(row.get("seed")) is not int
            or not isinstance(row.get("decks"),list)
            or len(row["decks"])!=4 or not isinstance(row.get("policies"),list)
            or len(row["policies"])!=4):
            raise GorgeBackendError("invalid gorge game result shape")
        results.append(row)
    if p.returncode!=0 or len(results)!=games:
        detail=p.stderr.strip()[-800:] or "no engine diagnostics"
        raise GorgeBackendError(
            f"gorge returned code {p.returncode} with {len(results)}/{games} "
            f"game summaries: {detail}")
    if any(not r.get("finished") or not r.get("replay_verified")
           or r.get("error") for r in results):
        raise GorgeBackendError("one or more gorge games failed completion/replay checks")
    return {
        "schema":"gorge-backend-batch-v1",
        "mode":"gorge_native_four_player_commander",
        "engine":"gorge",
        "pilot":pilot,"hero_pilot":hero_pilot,
        "deck_pool":list(decks),
        "games":results,
        "native_trace_schema":"gorge-native-trace-v1",
        "notes":"Full gorge rules + native pilot; does not use the Python abstract-opponent engine",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("binary","corpus","deck-dir","decks"):
        p.add_argument("--"+name,required=True)
    p.add_argument("--games",type=int,default=8)
    p.add_argument("--seed",type=int,default=0)
    p.add_argument("--max-turns",type=int,default=50)
    p.add_argument("--pilot",choices=sorted(PILOTS),default="bot")
    p.add_argument("--hero-pilot",choices=sorted(PILOTS))
    p.add_argument("--native-dir")
    p.add_argument("--native-limit",type=int,default=2)
    p.add_argument("--jsonl",action="store_true",
                   help="emit original per-game JSON lines for benchmark compatibility")
    a=p.parse_args()
    result=run_gorge_batch(
        binary=a.binary,corpus=a.corpus,deck_dir=a.deck_dir,
        decks=a.decks.split(","),games=a.games,seed=a.seed,
        max_turns=a.max_turns,pilot=a.pilot,hero_pilot=a.hero_pilot,
        native_dir=a.native_dir,native_limit=a.native_limit)
    if a.jsonl:
        for row in result["games"]:
            print(json.dumps(row,separators=(",",":")))
    else:
        print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
