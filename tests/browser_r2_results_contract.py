"""Exercise the real built Results page and mocked deployed-Worker contracts.

No approval is manufactured in repository data; these are browser-local mock
responses. Tests assert privacy/empty/failure/ready flows across desktop/mobile.
"""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import os
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright

ROOT=Path(os.environ["BROWSER_SITE_DIR"])
OUT=Path(os.environ["BROWSER_ARTIFACT_DIR"])
OUT.mkdir(parents=True,exist_ok=True)
API="https://gorge-r2-direct-api-preview.darbosama.workers.dev"

class StaticHandler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,*args):
        pass

def run():
    server=ThreadingHTTPServer(("127.0.0.1",0),StaticHandler)
    Thread(target=server.serve_forever,daemon=True).start()
    failures=[]
    try:
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True)
            for form,viewport in [
                ("desktop",{"width":1440,"height":960}),
                ("mobile",{"width":390,"height":844}),
            ]:
                page=browser.new_page(viewport=viewport)
                page.on("pageerror",lambda error: failures.append(str(error)))
                mode={"value":"awaiting"}
                requests=[]
                def handle(route):
                    parsed=urlparse(route.request.url)
                    path=parsed.path
                    params=parse_qs(parsed.query)
                    deck=params.get("deck",["mortarion_current"])[0]
                    requests.append((path,deck))
                    if mode["value"]=="error":
                        route.fulfill(status=503,content_type="application/json",
                            headers={"Access-Control-Allow-Origin":"*"},
                            body=json.dumps({"error":"r2_query_unavailable"}))
                        return
                    if path=="/v1/summary":
                        state=mode["value"]
                        body={"schema":"gorge-r2-live-summary-v1",
                            "deck":deck,"source":"r2-direct-parquet",
                            "population":"approved_current_decisive_only",
                            "status":"ready" if state=="ready" else "awaiting_cohort_approval",
                            "n":2 if state=="ready" else 0,
                            "wins":1 if state=="ready" else 0,
                            "losses":1 if state=="ready" else 0,
                            "win_rate":.5 if state=="ready" else None,
                            "raw_shards_seen":1,"groups":{"opponents":[]},
                            "query":{"server_ms":5,"shards_scanned":1}}
                    elif path=="/v1/games":
                        body={"schema":"gorge-r2-approved-game-index-v1",
                            "deck":deck,"status":"ready","total":1,"limit":10,
                            "games":[{"game_id":"browser-test-1","result":"win",
                                      "turns":14,"opponent_decks":["a","b","c"]}]}
                    elif path=="/v1/games/browser-test-1/timeline":
                        body={"schema":"gorge-r2-game-timeline-v1",
                            "deck":deck,"status":"ready",
                            "game":{"timeline":{"schema":"gorge-r2-event-segments-v1",
                                "event_count":5,"raw_events_exposed":False,
                                "segments":[{"segment":0,"public_events":3,
                                             "withheld_events":2,"kinds":{"cast":3}}]}}}
                    else:
                        route.fulfill(status=404,body="{}")
                        return
                    route.fulfill(status=200,content_type="application/json",
                        headers={"Access-Control-Allow-Origin":"*"},
                        body=json.dumps(body))
                page.route(API+"/**",handle)
                page.goto(f"http://127.0.0.1:{server.server_port}/results.html?deck=mortarion_current",
                          wait_until="domcontentloaded")
                page.wait_for_function("window.__deckLabActiveKey && document.querySelector('#gorge-r2-live .gorge-r2-live-panel')",
                                       timeout=45000)
                root=page.locator("#gorge-r2-live")
                assert "no current cohort has been approved" in root.inner_text().lower()
                assert "approved decisive games" not in root.inner_text()
                assert page.locator("#game-outcome-results").count()==1
                assert requests and any(p=="/v1/summary" for p,_ in requests)
                page.screenshot(path=str(OUT/(form+"-awaiting.png")))
                # Switching active decks must requery the selected source rather
                # than reusing the preceding commander's metrics.
                page.evaluate("""() => {
                    window.__deckLabActiveKey='magnus_premium';
                    document.dispatchEvent(new Event('change'));
                }""")
                page.wait_for_function(
                    "() => document.querySelector('#gorge-r2-live')?.textContent.includes('source shards found')",
                    timeout=20000)
                page.wait_for_timeout(300)
                assert any(p=="/v1/summary" and d=="magnus_premium" for p,d in requests)
                mode["value"]="ready"
                root.get_by_role("button",name="Refresh live R2 results").click()
                root.get_by_text("2 approved decisive games",exact=False).wait_for(timeout=20000)
                root.get_by_text("Approved games · R2 timeline preview").wait_for(timeout=20000)
                try:
                    root.get_by_role("button",name="Win · 14 turns",exact=False).click(timeout=10000)
                except Exception:
                    print("DEBUG R2 index body:",root.inner_text())
                    print("DEBUG API requests:",requests)
                    raise
                root.get_by_text("5 native events",exact=False).wait_for(timeout=20000)
                assert any(p=="/v1/games/browser-test-1/timeline" for p,_ in requests)
                assert "event_json" not in root.inner_text()
                page.screenshot(path=str(OUT/(form+"-approved-contract.png")))
                mode["value"]="error"
                root.get_by_role("button",name="Refresh live R2 results").click()
                root.get_by_text("R2 live query unavailable",exact=False).wait_for(timeout=20000)
                assert "existing published UI remains available" in root.inner_text()
                assert page.locator("#game-outcome-results").count()==1
                page.screenshot(path=str(OUT/(form+"-api-error.png")))
                page.close()
            browser.close()
        assert not failures,failures
        print("PASS: built Deck Lab R2 awaiting/ready/timeline/error desktop+mobile browser contracts")
    finally:
        server.shutdown()

if __name__=="__main__":
    run()
