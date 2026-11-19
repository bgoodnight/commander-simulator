"""Build an isolated, explicitly preliminary Results preview from smoke traces."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from tools.gorge_ui_export import convert
from tools.validate_gorge_enrichment import validate_trace

def build(source: Path, out: Path):
    import commander_sim.deck_lab_api as api
    import tools.build_pages_deck_lab as pages
    from commander_sim.deck_fixtures import USER_FIXTURES
    api.EXPERIMENTAL_FIXTURES += USER_FIXTURES
    pages.EXPERIMENTAL_FIXTURES += USER_FIXTURES
    pages.build(out)
    payload = {}
    for key in ("magnus_v1_7", "mortarion_v2_3"):
        root = source / key
        deckfile = Path("decklists") / (key + "_simulation.txt")
        sha = hashlib.sha256(deckfile.read_bytes()).hexdigest()
        expected = Counter()
        for line in deckfile.read_text().splitlines():
            match = re.fullmatch(r"(\d+)\s+(.+)", line.strip())
            if match:
                expected[match.group(2)] += int(match.group(1))
        if sum(expected.values()) != 100:
            raise ValueError("Expected a 100-card deck")
        rows = [json.loads(s) for s in (root / "runs.jsonl").read_text().splitlines() if s.strip()]
        if len(rows) != 4 or len({r["seed"] for r in rows}) != 4:
            raise ValueError("Expected four distinct recorded smoke games")
        games = []
        for row in rows:
            native = json.loads((root / "native" / f"gorge-seed-{row['seed']}.json").read_text())
            validate_trace(native)
            if (not row.get("finished") or not row.get("replay_verified") or row.get("error") or
                row.get("draw") or native.get("chain") != row.get("replay_chain") or
                native.get("seed") != row["seed"] or native.get("decks") != row.get("decks") or
                native.get("hero_seat") != row.get("hero_seat") or
                row["decks"][row["hero_seat"]] != key):
                raise ValueError("Unverified or mismatched smoke recording")
            names = {item["object_id"]: item.get("card_name") for item in native["objects"]}
            initial = next(p for p in native["snapshots"][0]["players"] if p["seat"] == row["hero_seat"])
            observed = Counter(names[oid] for zone in initial["zones"].values() for oid in zone)
            if observed != expected:
                raise ValueError("Native initial deck differs from requested revision")
            replay = convert(native, include_hidden=True)
            replay["player_seat"] = row["hero_seat"]
            replay["player_deck"] = key
            games.append({"replay": replay, "winner": row["winner_seat"]})
        payload[key] = {"sha": sha, "games": games}
    path = out / "projection-input.json"
    path.write_text(json.dumps(payload, separators=(",", ":")))
    subprocess.run(["node", "tools/build_latest_deck_preview.cjs", str(path), str(out)], check=True)
    path.unlink()
    html = out / "results.html"
    text = html.read_text().replace("<head>", '<head>\n<script src="./preliminary-data.js"></script>', 1)
    text = text.replace("<main", '<div style="background:#704c11;color:white;padding:12px;text-align:center;font:600 15px sans-serif">PRELIMINARY · 4 games per deck · diagnostic data, not production</div>\n<main', 1)
    html.write_text(text)
    js = out / "r2_original_results.js"
    text = js.read_text().replace("approved_current_decisive_only", "preliminary_decisive_only")
    text = text.replace("approved native Gorge", "preliminary native Gorge").replace("approved Gorge", "preliminary Gorge").replace("approved games", "preliminary games")
    js.write_text(text)
    js = out / "game_outcomes.js"
    js.write_text(js.read_text().replace("approved games with complete recorded card observations", "preliminary games with complete recorded card observations"))
    js = out / "app.js"
    text = js.read_text().replace('magnus_premium:"Magnus · Premium",', 'magnus_v1_7:"Magnus · v1.7",magnus_premium:"Magnus · Premium",')
    text = text.replace('mortarion_current:"Mortarion · Current",', 'mortarion_v2_3:"Mortarion · v2.3",mortarion_current:"Mortarion · Current",')
    js.write_text(text)
    (out / "preliminary-data.js").write_text('''(() => {
 const original=window.fetch.bind(window);
 window.fetch=async(input,options)=>{
  const u=new URL(typeof input==="string"?input:(input instanceof URL?input.href:input.url),location.href);
  if(u.hostname==="gorge-r2-direct-api-preview.darbosama.workers.dev" && u.pathname.startsWith("/v1/ui/")){
   if(u.pathname!=="/v1/ui/batch")return new Response("{}",{status:404});
   const deck=u.searchParams.get("deck");
   if(!["magnus_v1_7","mortarion_v2_3"].includes(deck))return new Response("{}",{status:404});
   const batch=await (await original(`./${deck}-preliminary.json`)).json();
   return new Response(JSON.stringify({schema:"gorge-r2-original-ui-batch-response-v1",population:"preliminary_decisive_only",deck,status:"ready",batch}),{status:200,headers:{"Content-Type":"application/json"}});
  }
  return original(input,options);
 };
})();\n''')
    # This is a Results-only preview: avoid copying old simulation archives
    # into a second permanent Pages tree or presenting them as this batch.
    for name in ("game-outcomes", "simulation-data", "replay-data"):
        shutil.rmtree(out / name, ignore_errors=True)
    datafile = out / "decks.json"
    data = json.loads(datafile.read_text())
    data["decks"] = [d for d in data["decks"] if d["key"] in {"magnus_v1_7", "mortarion_v2_3"}]
    datafile.write_text(json.dumps(data, separators=(",", ":")))
    html.write_text(re.sub(r'<a class="site-link" data-page="(?:summary|editor)"[^>]*>.*?</a>', "", html.read_text()))

if __name__ == "__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();build(a.source,a.out)
