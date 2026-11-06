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
             "groups":{"opponents":[]},"game_turn_histogram":[]}
    one_batch={**DOCUMENT["batch"],"runs":[DOCUMENT["batch"]["runs"][0]]}
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
                     "categories":{"played":[{"name":"Fixture Card","games":90,
                         "eventCount":100,"score":90,"average":100/201,
                         "median":0,"heldMedian":None,"timesPlayed":100,
                         "seenGames":90,"turns":[3],"exampleEvents":[],
                         "exampleSeenSeeds":[]}]}}}
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
                page.get_by_text("201 games · 50 wins · 151 losses",exact=False).wait_for(timeout=60000)
                assert page.get_by_text("Fixture Card · 90 games · 100 recorded events").is_visible()
                assert page.get_by_text("Page 1 of 9",exact=False).is_visible()
                assert not any(path.endswith("/game") for path,_ in calls)
                page.get_by_role("button",name="Next 25").click()
                page.get_by_text("Page 2 of 9",exact=False).wait_for(state="visible",timeout=60000)
                page.locator(".game-outcome-game-select").first.click()
                try:
                    page.get_by_text("Selected game replay · individual game",exact=False).wait_for(timeout=15000)
                except Exception:
                    print("Replay diagnostic:",page.locator("#game-outcome-results").inner_text())
                    print("Browser errors:",errors)
                    raise
                assert page.locator("#turn-reviewer-results .insight-turn-row").count()>0
                assert page.get_by_text("201 games · 50 wins · 151 losses",exact=False).is_visible()
                assert page.get_by_text("Fixture Card · 90 games · 100 recorded events").is_visible()
                assert any(path.endswith("/game") and q.get("page")==["1"] for path,q in calls)
                page.screenshot(path=str(OUT/f"{DECK}-{mode}-materialized-results.png"),full_page=True)
                page.close()
            browser.close()
        assert not errors,errors
    finally:
        server.shutdown()

if __name__=="__main__":
    test()
    test_materialized()
