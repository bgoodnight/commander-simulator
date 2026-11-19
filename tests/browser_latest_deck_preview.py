"""Exercise the preliminary preview against its actual recorded game data."""
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

root=Path(os.environ["BROWSER_SITE_DIR"]).resolve()
out=Path(os.environ["BROWSER_ARTIFACT_DIR"]);out.mkdir(parents=True,exist_ok=True)
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(root),**kw)
    def log_message(self,*args): pass
server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        for deck in ("magnus_v1_7","mortarion_v2_3"):
            for mode,viewport in (("desktop",{"width":1440,"height":960}),("mobile",{"width":390,"height":844})):
                page=browser.new_page(viewport=viewport);errors=[]
                page.on("pageerror",lambda err:errors.append(str(err)))
                page.goto(f"http://127.0.0.1:{server.server_port}/results.html?deck={deck}",wait_until="domcontentloaded")
                page.wait_for_function("key => window.R2OriginalResults?.ownsRenderedDeck(key)",arg=deck,timeout=60000)
                assert "PRELIMINARY" in page.locator("body").inner_text()
                assert "4 preliminary native Gorge games" in page.locator("#game-outcome-status").inner_text()
                assert page.locator("#game-outcome-results .game-outcome-hero").count()==1
                assert page.locator("#turn-reviewer-panel").is_visible()
                assert page.locator("#turn-reviewer-results .insight-turn-row").count()>0
                assert not errors,errors
                page.screenshot(path=str(out/f"{deck}-{mode}.png"),full_page=True)
                page.close()
        browser.close()
finally:
    server.shutdown()
