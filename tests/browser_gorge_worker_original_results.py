"""End-to-end browser contract: real native Gorge -> Worker batch -> original UI.

The only mocked component is the network response from the already-tested
Worker batch projection. No experimental response is sent to public R2.
"""
import json
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlparse
from playwright.sync_api import sync_playwright

ROOT=Path(os.environ["BROWSER_SITE_DIR"])
OUT=Path(os.environ["BROWSER_ARTIFACT_DIR"])
OUT.mkdir(parents=True,exist_ok=True)
DOCUMENT=json.loads(Path(os.environ["ORIGINAL_UI_BATCH"]).read_text())
DECK=DOCUMENT["deck"]
API="https://gorge-r2-direct-api-preview.darbosama.workers.dev"
VERSION="a"*64

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,*args):
        pass

def test():
    assert DOCUMENT["status"]=="ready" and DOCUMENT["batch"]["runs"]
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    Thread(target=server.serve_forever,daemon=True).start()
    errors=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            for mode,viewport in (("desktop",{"width":1440,"height":960}),
                                  ("mobile",{"width":390,"height":844})):
                page=browser.new_page(viewport=viewport)
                page.on("pageerror",lambda err:errors.append(str(err)))
                def route(request):
                    request.fulfill(status=200,content_type="application/json",
                        headers={"Access-Control-Allow-Origin":"*"},
                        body=json.dumps(DOCUMENT))
                # This scenario exercises the legacy route on a Worker without
                # materialized results. Do not depend on an external Worker or
                # whatever deployment happens to be live while CI is running.
                page.route(API+"/v1/ui/catalog?*",lambda route: route.fulfill(
                    status=404,content_type="application/json",
                    headers={"Access-Control-Allow-Origin":"*"},body="{}"))
                page.route(API+"/v1/ui/batch?*",route)
                page.goto(f"http://127.0.0.1:{server.server_port}/results.html?deck={DECK}",
                          wait_until="domcontentloaded")
                hero=page.locator("#game-outcome-results .game-outcome-hero-frame")
                hero.wait_for(state="visible",timeout=60000)
                assert page.evaluate("(key)=>window.R2OriginalResults.ownsRenderedDeck(key)",DECK)
                assert page.locator("#game-outcome-results .game-outcome-stacked-bar").count()>0
                assert page.locator("#game-outcome-results .game-outcome-hero").count()==1
                # Missing optional card-level insights are a legitimate placeholder.
                # They must not suppress the source-backed outcome hero.
                assert "No approved simulations match" not in hero.inner_text()
                assert "No simulations have been run" not in hero.inner_text()
                assert page.locator("#turn-reviewer-panel").is_visible()
                # A valid R2 batch enables all three sections together.
                # Card findings must state their actual recorded-game coverage.
                assert page.evaluate("document.body.dataset.r2ResultsState")=="ready"
                assert page.locator("#key-insights-panel").is_visible()
                assert page.evaluate("""() => {
                  const results=document.getElementById('long-game-panel');
                  const insights=document.getElementById('key-insights-panel');
                  const reviewer=document.getElementById('turn-reviewer-panel');
                  return Boolean(results.compareDocumentPosition(insights)&Node.DOCUMENT_POSITION_FOLLOWING)
                    && Boolean(insights.compareDocumentPosition(reviewer)&Node.DOCUMENT_POSITION_FOLLOWING);
                }"""), "Results, Key Insights, Turn Reviewer must appear in that order"
                # Named-card insight headings use the shared mana-symbol component,
                # rather than rendering the raw {W}/{U}/{B}/{R}/{G} text.
                mana=page.evaluate("""() => [...document.querySelectorAll(
                    '#key-insights-panel .insight-featured-panel')].map(panel=>{
                      const name=panel.querySelector('.insight-head-name')?.textContent;
                      const printed=window.GorgeDeckLabCardInfo?.(name)?.mana_cost||'';
                      const symbols=panel.querySelectorAll('.insight-head-mana img.mana-symbol');
                      return {name,printed,count:symbols.length,
                        fallback:panel.querySelector('.insight-head-mana')?.textContent||''};
                    })""")
                for item in mana:
                    if item["printed"] and "{" in item["printed"]:
                        assert item["count"]>0 or item["printed"] in item["fallback"],item
                page.locator("#key-insights-grid .insight-methodology summary").click()
                insights=page.locator("#key-insights-panel").inner_text()
                assert ("approved games with complete recorded card observations" in insights
                        or "No named card observations are available" in insights)
                assert "Complete-cohort card insights are not yet available" not in page.locator("#game-outcome-results").inner_text()
                first=page.locator("#key-insights-grid .insight-featured-panel").first
                if first.count():
                    first.locator("summary").first.click()
                    assert first.get_by_role("group",name="Card type and ranking").is_visible()
                    link=first.get_by_role("button",name="View an example game",exact=False)
                    if link.count():
                        link.click()
                        assert page.locator("#turn-reviewer-results .insight-turn-row[open]").count()>0
                page.screenshot(path=str(OUT/f"{DECK}-{mode}-original-results.png"),full_page=True)
                print(f"PASS {DECK} {mode}: real 12-game Worker batch renders original outcome cards")
                page.close()
            browser.close()
        assert not errors,errors
    finally:
        server.shutdown()

def test_materialized():
    """Exercise 201-game paging and on-demand replay in desktop and mobile.

    Game records are fixture IDs; the selected replay is the real validated
    Gorge batch supplied to this existing CI test. Counts are synthetic.
    """
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    Thread(target=server.serve_forever,daemon=True).start()
    errors=[]
    calls=[]
    summary={"schema":"gorge-r2-live-summary-v1","cohort_version":VERSION,
             "n":201,"wins":50,"losses":151,"win_rate":50/201,
             "groups":{"opponents":[{"name":"Fixture opponent","wins":50,"losses":151,"n":201,"win_rate":50/201}]},
             "game_turn_histogram":[{"turn":10,"games":101},{"turn":11,"games":100}]}
    one_batch={**DOCUMENT["batch"],"runs":[DOCUMENT["batch"]["runs"][0]]}
    source_card=next((name for name in one_batch["runs"][0].get("opening_hand",[])
                      if name not in {"Swamp","Island","Plains","Mountain","Forest"}),
                     one_batch["runs"][0].get("opening_hand",["Swamp"])[0])
    def response(route):
        parsed=urlparse(route.request.url)
        query=parse_qs(parsed.query)
        calls.append((parsed.path,query))
        common={"schema":"gorge-r2-materialized-response-v1","deck":DECK,
                "version":VERSION,"status":"ready","total":201}
        if parsed.path.endswith("/catalog"):
            payload={**common,"page_count":9,"summary":summary}
        elif parsed.path.endswith("/insights"):
            payload={**common,"insights":{"cohort_version":VERSION,
                     "verified_games":201,"observed_games":201,
                     "coverage":{"missing":0,"level":"full-cohort"},
                     "categories":{"creature":[],"artifact":[],"enchantment":[],
                         "instant":[],"spell":[],"land":[],"activated":[],"triggered":[],
                         "played":[{"name":source_card,"games":90,
                         "eventCount":100,"score":90,"average":100/201,
                         "median":0,"heldMedian":None,"timesPlayed":100,
                         "seenGames":90,"turns":[3],"exampleEvents":[],
                         "exampleSeenSeeds":[],"exampleGames":[{"game_id":"fixture-1-0","turn":1}]}]}}}
        elif parsed.path.endswith("/page"):
            number=int(query["page"][0])
            count=min(25,201-number*25)
            games=[{"game_id":f"fixture-{number}-{i}","result":"loss",
                    "turns":10,"opponent_decks":["precon"]} for i in range(count)]
            payload={**common,"page":{"page":number,"total":201,"games":games,
                     "has_more":number<8}}
        elif parsed.path.endswith("/game"):
            payload={**common,"game":{"game_id":query["game_id"][0],"batch":one_batch}}
        else:
            raise AssertionError("Unexpected materialized route: "+parsed.path)
        route.fulfill(status=200,content_type="application/json",
                      headers={"Access-Control-Allow-Origin":"*"},body=json.dumps(payload))
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            for mode,viewport in (("desktop",{"width":1440,"height":960}),
                                  ("mobile",{"width":390,"height":844})):
                calls.clear()
                page=browser.new_page(viewport=viewport)
                page.on("pageerror",lambda err: errors.append(str(err)))
                page.route(API+"/v1/ui/catalog?*",response)
                page.route(API+"/v1/ui/insights?*",response)
                page.route(API+"/v1/ui/page?*",response)
                page.route(API+"/v1/ui/game?*",response)
                page.goto(f"http://127.0.0.1:{server.server_port}/results.html?deck={DECK}&materializedResults=1",
                          wait_until="domcontentloaded")
                page.get_by_text("201 games · complete cohort",exact=False).wait_for(timeout=60000)
                assert page.evaluate("document.body.dataset.r2ResultsState")=="ready"
                assert page.locator("#key-insights-panel").is_visible()
                assert page.locator("#key-insights-grid").get_by_text(source_card,exact=False).first.is_visible()
                assert page.get_by_role("heading",name="Key insights").count()==1
                assert page.locator("#gorge-r2-live").is_hidden()
                assert page.locator("#gorge-replay-panel").is_hidden()
                assert page.get_by_text(source_card,exact=False).first.is_visible()
                search=page.get_by_role("searchbox",name="Find a game or opponent")
                assert search.count()==1
                page.get_by_text("201 matching games",exact=True).wait_for(timeout=60000)
                assert page.locator('select[aria-label="Choose recorded game"]:visible').count()==0
                assert page.get_by_role("button",name="Next 25").count()==0
                assert not any(path.endswith("/game") for path,_ in calls)
                insight=page.locator("#key-insights-grid .insight-featured-panel").first
                insight.locator("summary").first.click()
                assert insight.get_by_role("group",name="Card type and ranking").is_visible()
                insight.get_by_role("button",name="View an example game",exact=False).click()
                page.locator("#turn-reviewer-results .insight-turn-row[open]").first.wait_for(timeout=15000)
                assert any(path.endswith("/game") and q.get("page")==["1"] and q.get("game_id")==["fixture-1-0"] for path,q in calls)
                search.fill("Game 201")
                with page.expect_response(lambda response: "/v1/ui/game?" in response.url and "page=8" in response.url):
                    page.get_by_role("button",name="Game 201 · Loss",exact=False).click()
                page.locator("#turn-reviewer-results .insight-turn-row").first.wait_for(timeout=15000)
                assert any(path.endswith("/game") and q.get("page")==["8"] for path,q in calls)
                assert page.locator("#turn-reviewer-results .insight-turn-row").count()>0
                if one_batch["runs"][0].get("gorge_source",{}).get("opening_hand_boundary")=="first_pending_decision_of_turn":
                    assert page.get_by_text("First recorded hand",exact=False).first.is_visible()
                assert page.get_by_text("201 games · complete cohort",exact=False).is_visible()
                assert page.get_by_text(source_card,exact=False).first.is_visible()
                # A selected replay must not render misleading one-game
                # outcome statistics alongside the full-cohort dashboard.
                assert page.locator("#game-outcome-results .game-outcome-hero-frame:visible").count()==1
                assert any(path.endswith("/game") and q.get("page")==["1"] for path,q in calls)
                # A full-page screenshot does not scroll lazy images into view.
                # Force the already-selected card art to load before capture,
                # and report failed external images separately from missing DOM.
                covers=page.locator("#turn-reviewer-results .insight-turn-cover")
                assert covers.count()>0, "No turn artwork was selected from the card catalog"
                artwork=page.evaluate("""async () => {
                  const images=[...document.querySelectorAll('#turn-reviewer-results .insight-turn-cover')];
                  for(const img of images) img.loading='eager';
                  await Promise.race([Promise.all(images.map(img=>img.decode().catch(()=>{}))),
                    new Promise(resolve=>setTimeout(resolve,10000))]);
                  return images.map(img=>({src:img.currentSrc||img.src,complete:img.complete,
                    width:img.naturalWidth,display:getComputedStyle(img).display}));
                }""")
                print("Turn artwork diagnostics:",json.dumps(artwork))
                assert all(item["display"]!="none" for item in artwork)
                page.screenshot(path=str(OUT/f"{DECK}-{mode}-materialized-results.png"),full_page=True)
                page.locator("#turn-reviewer-results .insight-turn-row summary").first.click()
                page.screenshot(path=str(OUT/f"{DECK}-{mode}-expanded-turn.png"),full_page=True)
                page.close()
            browser.close()
        assert not errors,errors
    finally:
        server.shutdown()

if __name__=="__main__":
    test()
    test_materialized()
