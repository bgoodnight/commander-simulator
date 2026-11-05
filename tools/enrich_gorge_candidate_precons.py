"""Enrich candidate precons from a pinned Scryfall Oracle bulk snapshot.

Read-only analytical export; no changes to active opponent roles or game code.
Strict name resolution, explicit unknowns, conservative mechanical proxies.
Run as an offline preparation step outside simulation, and save compact evidence
and source fingerprint for reproducibility.
"""
from __future__ import annotations
import argparse
import collections
import datetime as dt
import gzip
import hashlib
import io
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

from tools.audit_gorge_candidate_catalog import validate_catalog, DEFAULT as CATALOG

COLORS = "WUBRG"
METRICS = ("creatures", "lands", "artifacts", "enchantments", "instants", "sorceries",
           "planeswalkers", "battles", "mana_rocks_proxy", "ramp_text_proxy",
           "draw_text_proxy", "removal_text_proxy", "counterspell_text_proxy",
           "token_text_proxy", "reanimation_text_proxy", "graveyard_text_proxy",
           "tutor_text_proxy", "sacrifice_text_proxy", "life_loss_text_proxy")
# These are intentionally restrictive word/phrase-pattern flags, NOT
# authoritative role or rules classifications. They can under/over-count.
PATTERNS = {
    "ramp_text_proxy": r"\b(add \{|search your library for (?:a|up to|two|three).*land|put (?:a|up to|two|three).*land.*onto the battlefield)\b",
    "draw_text_proxy": r"\bdraw (?:a|one|two|three|four|x|that many|cards?)\b",
    "removal_text_proxy": r"\b(destroy target|exile target|return target .* to (?:its owner's|their owner's) hand|deals? [^\.]*damage to target)\b",
    "counterspell_text_proxy": r"\bcounter target (?:spell|activated|triggered)\b",
    "token_text_proxy": r"\bcreate (?:a|an|one|two|three|four|x|that many|\\d+) [^\.]* token",
    "reanimation_text_proxy": r"\breturn target [^\.]* card from (?:your|a|an|target player's) graveyard to the battlefield\b",
    "graveyard_text_proxy": r"\bgraveyard\b",
    "tutor_text_proxy": r"\bsearch your library for\b",
    "sacrifice_text_proxy": r"\bsacrifice (?:a|an|another|target|one|two|three|x|any number|a number|this|~)\b",
    "life_loss_text_proxy": r"\b(?:lose|loses) (?:one|two|three|four|x|[0-9]+|that much|that many) life\b",
}
REGEX = {k: re.compile(v, re.I) for k,v in PATTERNS.items()}
BAD_LAYOUTS = {"token", "emblem", "art_series", "scheme", "planar", "vanguard"}
BULK_METADATA = "https://api.scryfall.com/bulk-data/oracle-cards"
USER_AGENT = "CommanderSimulatorEnrichment/1.0 (offline research; GitHub Actions)"


def strings(record):
    faces = record.get("card_faces") or []
    parts = [record.get("oracle_text") or ""]
    for f in faces:
        parts.append(f.get("oracle_text") or "")
    return " ".join(parts)


def build_index(cards):
    # Exact full printed Oracle names always outrank a different card's
    # face alias (e.g. standalone Brainstorm vs a Prepared card face).
    exact={}
    exact_ambiguous=set()
    aliases={}
    alias_ambiguous=set()
    for c in cards:
        if c.get("lang", "en") != "en" or c.get("layout") in BAD_LAYOUTS:
            continue
        name=c.get("name")
        if name:
            key=name.casefold().strip()
            prior=exact.get(key)
            if prior and prior.get("oracle_id")!=c.get("oracle_id"):
                exact_ambiguous.add(key)
            else:
                exact[key]=c
        for face in c.get("card_faces") or []:
            label=face.get("name")
            if not label:continue
            key=label.casefold().strip()
            prior=aliases.get(key)
            if prior and prior.get("oracle_id")!=c.get("oracle_id"):
                alias_ambiguous.add(key)
            else:
                aliases[key]=c
    for key in exact_ambiguous:
        exact.pop(key,None)
    for key,c in aliases.items():
        if key not in exact and key not in alias_ambiguous and key not in exact_ambiguous:
            exact[key]=c
    return exact,exact_ambiguous|{k for k in alias_ambiguous if k not in exact}


def decode_bulk(raw):
    if raw.startswith(b"\x1f\x8b"):
        raw=gzip.decompress(raw)
    if raw.lstrip().startswith(b"["):
        return json.loads(raw)
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def fetch_oracle_bulk():
    request=Request(BULK_METADATA,headers={"User-Agent":USER_AGENT,"Accept":"application/json"})
    with urlopen(request,timeout=30) as f:
        metadata=json.load(f)
    url=metadata.get("jsonl_download_uri") or metadata.get("download_uri")
    if not isinstance(url,str) or not url.startswith("https://data.scryfall.io/"):
        raise ValueError("Unsupported Oracle bulk source URL")
    request=Request(url,headers={"User-Agent":USER_AGENT})
    with urlopen(request,timeout=180) as f:
        raw=f.read(180*1024*1024+1)
    if len(raw)>180*1024*1024:
        raise ValueError("Bulk source exceeds 180 MiB safety cap")
    return raw,{"bulk_source":url,"bulk_updated_at":metadata.get("updated_at"),
                "bulk_type":metadata.get("type","oracle_cards")}


def primary_types(c):
    # Multi-faced cards may have types on individual faces.
    line = " ".join([c.get("type_line") or ""]+[f.get("type_line") or "" for f in c.get("card_faces") or []])
    return set(re.findall(r"\b(Creature|Land|Artifact|Enchantment|Instant|Sorcery|Planeswalker|Battle)\b",line,re.I))


def card_metrics(c):
    found=set()
    types=primary_types(c)
    mapping={"creatures":"Creature","lands":"Land","artifacts":"Artifact",
             "enchantments":"Enchantment","instants":"Instant",
             "sorceries":"Sorcery","planeswalkers":"Planeswalker","battles":"Battle"}
    for col,typename in mapping.items():
        if typename in types:
            found.add(col)
    t=strings(c)
    for field,pattern in REGEX.items():
        if pattern.search(t):
            found.add(field)
    if "Artifact" in types and "Land" not in types and re.search(r"\badd \{[WUBRGC0-9]",t,re.I):
        found.add("mana_rocks_proxy")
    return found


def enrich(catalog, source_bytes, *, as_of="2026-11-05", bulk_metadata=None):
    validate_catalog(catalog)
    raw=json.loads(Path(catalog).read_text())
    cutoff=dt.date.fromisoformat(as_of)
    all_rows=[d for d in raw["decks"] if dt.date.fromisoformat(d["release_date"])<=cutoff]
    exact={}
    dups=[]
    for d in all_rows:
        sig=(d["commander"],tuple(sorted((x["name"],x["count"]) for x in d["cards"])))
        if sig in exact:
            dups.append({"variant":d["key"],"canonical":exact[sig]})
        else:
            exact[sig]=d["key"]
    cards=decode_bulk(source_bytes)
    index,ambiguous=build_index(cards)
    out=[]
    unresolved=collections.Counter()
    by_colors=collections.Counter()
    flag_totals=collections.Counter()
    for d in all_rows:
        card_rows=[]
        counts=collections.Counter()
        identity_card=index.get(d["commander"].casefold().strip())
        color_identity=identity_card.get("color_identity") if identity_card else None
        if not isinstance(color_identity,list) or any(c not in COLORS for c in color_identity):
            color_identity=None
        oracle_ids=[]
        curve=[]
        keywords=collections.Counter()
        for item in d["cards"]:
            qty=item["count"]
            c=index.get(item["name"].casefold().strip())
            if not c:
                unresolved[item["name"]]+=qty
                card_rows.append({"name":item["name"],"count":qty,"resolved":False})
                continue
            tags=card_metrics(c)
            for tag in tags:counts[tag]+=qty
            for kw in c.get("keywords") or []:keywords[kw]+=qty
            mv=c.get("cmc")
            if isinstance(mv,(float,int)) and "Land" not in primary_types(c):
                curve.extend([float(mv)]*qty)
            oid=c.get("oracle_id")
            oracle_ids.append((item["name"],oid))
            card_rows.append({"name":item["name"],"count":qty,"resolved":True,
                              "oracle_id":oid,"mana_value":mv,
                              "types":sorted(primary_types(c)),
                              "color_identity":c.get("color_identity") or [],
                              "keywords":c.get("keywords") or [],
                              "proxy_tags":sorted(tags)})
        coverage=sum(c["count"] for c in card_rows if c["resolved"])
        sig=(d["commander"],tuple(sorted((x["name"],x["count"]) for x in d["cards"])))
        is_variant=exact[sig]!=d["key"]
        entry={
            "key":d["key"],"name":d["name"],"commander":d["commander"],
            "release_date":d["release_date"],"set_code":d["set_code"],
            "is_duplicate_variant":is_variant,"canonical_key":exact[sig],
            "color_identity":sorted(color_identity) if color_identity is not None else None,
            "color_count":len(color_identity) if color_identity is not None else None,
            "identity_resolution":bool(identity_card),
            "cards_resolved":coverage,"cards_total":100,
            "card_name_coverage":round(coverage/100,4),
            "nonland_mean_mana_value":round(sum(curve)/len(curve),3) if curve else None,
            "nonland_mana_value_count":len(curve),
            "mechanic_keywords":dict(keywords.most_common()),
            "counts":{key:counts.get(key,0) for key in METRICS},
            "proxy_definition":"conservative regex indicators on Oracle text, unreviewed; not exhaustive role counts",
            "primary_archetype":None,"secondary_archetypes":[],
            "archetype_status":"requires_curated_review",
            "gorge_rules_compatibility":"not_tested",
            "gorge_pilot_quality":"not_tested",
            "active_opponent":False,
            "cards":card_rows
        }
        out.append(entry)
        if not is_variant and color_identity is not None:
            by_colors["".join(c for c in COLORS if c in color_identity) or "C"]+=1
        if not is_variant:
            flag_totals.update({k:int(v>0) for k,v in counts.items()})
    unique=[x for x in out if not x["is_duplicate_variant"]]
    return {
        "schema":"gorge-precon-card-metadata-enrichment-v1",
        "source_catalog_commit":raw["source"]["commit"],
        "oracle_bulk_sha256":hashlib.sha256(source_bytes).hexdigest(),
        "oracle_bulk_metadata":bulk_metadata or {},
        "as_of":as_of,"released_products":len(all_rows),
        "distinct_decklists":len(unique),"duplicate_variants":dups,
        "distinct_commanders":len({d["commander"] for d in unique}),
        "color_identity_distribution":dict(sorted(by_colors.items())),
        "complete_deck_resolution":sum(x["cards_resolved"]==100 for x in unique),
        "unresolved_card_quantities":dict(unresolved.most_common(200)),
        "unresolved_card_name_count":len(unresolved),
        "commander_identity_resolved":sum(x["color_identity"] is not None for x in unique),
        "mechanic_proxy_prevalence":dict(sorted(flag_totals.items())),
        "caveats":[
          "Card identity and color are derived from Scryfall Oracle metadata; not inferred from basic lands.",
          "Functional counts are conservative Oracle-text heuristics. They are not validated measures of deck roles, causal effects, or Gorge support.",
          "Color identity of the named deck commander may not cover partners/backgrounds; manually validate such products before qualification.",
          "Identical decklist variants remain in the catalog but count only once in distributions.",
          "Cards missing from Oracle bulk are explicitly unresolved, not guessed.",
        ],
        "decks":out,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--catalog",type=Path,default=CATALOG)
    parser.add_argument("--as-of",default="2026-11-05")
    parser.add_argument("--oracle-bulk-file",type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    if args.oracle_bulk_file:
        source=args.oracle_bulk_file.read_bytes()
        metadata={"source":"provided_local_file"}
    else:
        source,metadata=fetch_oracle_bulk()
    result=enrich(args.catalog,source,as_of=args.as_of,bulk_metadata=metadata)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    summary={k:result[k] for k in ("released_products","distinct_decklists","complete_deck_resolution","commander_identity_resolved","unresolved_card_name_count","color_identity_distribution")}
    print(json.dumps(summary,sort_keys=True))


if __name__=="__main__":
    main()
