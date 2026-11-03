"""Fetch a provenance-labelled precon opponent library from a pinned gorge tree.

Download is an explicit setup operation, never called during a simulation.
No Forge card scripts, abilities, or GPL corpus are copied to this repo.
Do not relabel interim approximations or upgraded lists as stock precons.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from urllib.request import urlopen

GORGE_COMMIT="b78e4c8b16078f6decbc48875bba953ce5535b85"
BASE=f"https://raw.githubusercontent.com/adams-shaun/gorge/{GORGE_COMMIT}/testkit/testutil/decks"
@dataclass(frozen=True)
class Precon:
    slug: str
    kind: str
    provenance: str

PRECONS=(
    Precon("avengers-assemble","stock_precon",
           "MTGGoldfish stock Avengers Assemble list as documented upstream"),
    Precon("cavalry-charge","stock_precon",
           "March of the Machine Cavalry Charge list as documented upstream"),
    Precon("deadly-disguise","stock_precon",
           "Wizards/MTGGoldfish Deadly Disguise list as documented upstream"),
    Precon("science-pip","stock_precon",
           "Fallout Science! precon list as documented upstream"),
    # These are extra archetypes, NOT official stock precons:
    Precon("ulalek-eldrazi","community_list",
           "MTGGoldfish Ulalek Eldrazi Commander list, not stock precon"),
    Precon("valgavoth-endless-punishment","upgraded_precon",
           "MTGGoldfish upgrade of Endless Punishment, not stock precon"),
)
STOCK_SLUGS=tuple(p.slug for p in PRECONS if p.kind=="stock_precon")


def validate_precon(doc,slug):
    if not isinstance(doc,dict) or doc.get("format")!="commander":
        raise ValueError(f"{slug}: not a Commander deck")
    commander=doc.get("commander")
    rows=doc.get("cards")
    if not isinstance(commander,str) or not commander.strip() or not isinstance(rows,list):
        raise ValueError(f"{slug}: missing commander/cards")
    names=set()
    count=0
    commander_count=0
    for row in rows:
        if not isinstance(row,dict):
            raise ValueError(f"{slug}: malformed card row")
        name,n=row.get("name"),row.get("count")
        if not isinstance(name,str) or not name or type(n) is not int or n<=0:
            raise ValueError(f"{slug}: invalid card/count")
        if name in names:
            raise ValueError(f"{slug}: repeated name row")
        names.add(name);count+=n
        if name==commander: commander_count+=n
    if count!=100 or commander_count!=1:
        raise ValueError(f"{slug}: expected 100 cards and exactly one commander")
    return doc


def fetch_precons(directory,include_community=False,fetch=None):
    """Fetch only names on the pinned allowlist; return a source audit manifest."""
    target=Path(directory)
    target.mkdir(parents=True,exist_ok=True)
    fetch=fetch or (lambda url: urlopen(url,timeout=35).read())
    inventory=[]
    for p in PRECONS:
        if p.kind!="stock_precon" and not include_community:
            continue
        url=f"{BASE}/{p.slug}.json"
        doc=validate_precon(json.loads(fetch(url)),p.slug)
        path=target/(p.slug+".json")
        path.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        inventory.append({"key":p.slug,"kind":p.kind,"source":url,
                          "provenance":p.provenance,"commander":doc["commander"],
                          "count":100})
    manifest={"schema":"gorge-precon-library-v1",
              "gorge_commit":GORGE_COMMIT,"decks":inventory}
    (target/"library_manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--out",type=Path,required=True)
    cli.add_argument("--include-community",action="store_true")
    args=cli.parse_args()
    result=fetch_precons(args.out,args.include_community)
    print(json.dumps({"downloaded":len(result["decks"]),
                      "stock_precons":sum(x["kind"]=="stock_precon" for x in result["decks"]),
                      "gorge_commit":GORGE_COMMIT}))
