"""End-to-end browser contract: real native Gorge -> Worker batch -> original UI.

The only mocked component is the network response from the already-tested
Worker batch projection. No experimental response is sent to public R2.
"""
import json
import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT=Path(os.environ["BROWSER_SITE_DIR"])
OUT=Path(os.environ["BROWSER_ARTIFACT_DIR"])
OUT.mkdir(parents=True,exist_ok=True)
DOCUMENT=json.loads(Path(os.environ["ORIGINAL_UI_BATCH"]).read_text())
DECK=DOCUMENT["deck"]
API="https://gorge-r2-direct-api-preview.darbosama.workers.dev"

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
                # The legacy renderer must remain usable before the first materialized pointer is published.\n                page.route(API+"/v1/ui/catalog?*",lambda request: request.fulfill(\n                    status=404,content_type="application/json",\n                    headers={"Access-Control-Allow-Origin":"*"},\n                    body=json.dumps({"error":"materialized_not_published"})))\n                page.route(API+"/v1/ui/batch?*",route)
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

if __name__=="__main__":
    test()
