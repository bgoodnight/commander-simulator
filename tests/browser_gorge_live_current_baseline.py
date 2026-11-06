"""Smoke the actual published Results page and deployed approved R2 Worker.

No mocked Worker responses. Results must show exactly the approved baseline
rather than historical/experimental or empty sample panels.
"""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

BASE="https://bgoodnight.github.io/commander-simulator/deck-lab/results.html"
API="https://gorge-r2-direct-api-preview.darbosama.workers.dev"
OUT=Path(os.environ.get("BROWSER_ARTIFACT_DIR","/tmp/gorge-live-ui"))
OUT.mkdir(parents=True,exist_ok=True)

def run():
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True)
        for deck in ("mortarion_current","magnus_premium"):
            for form,viewport in [("desktop",{"width":1440,"height":960}),
                                  ("mobile",{"width":390,"height":844})]:
                page=browser.new_page(viewport=viewport)
                errors=[]
                seen=[]
                page.on("pageerror",lambda error:errors.append(str(error)))
                page.on("response",lambda response:seen.append((
                    response.url,response.status)) if "/v1/ui/batch" in response.url else None)
                try:
                    response=page.goto(BASE+"?deck="+deck,wait_until="domcontentloaded",timeout=60000)
                print("NAV",deck,form,"status",response.status if response else None,"url",page.url,"title",page.title())
                    page.wait_for_function(
                        "(key)=>window.R2OriginalResults?.ownsRenderedDeck(key)===true",
                        arg=deck,timeout=60000)
                    hero=page.locator("#game-outcome-results .game-outcome-hero-frame")
                    hero.wait_for(state="visible",timeout=30000)
                    assert page.locator("#game-outcome-results .game-outcome-stacked-bar").count()>0
                    assert page.locator("#turn-reviewer-panel").is_visible()
                    assert any("/v1/ui/batch?deck="+deck in url and status==200
                               for url,status in seen),seen
                    status=page.locator("#game-outcome-status").inner_text()
                    assert "12 approved native Gorge games" in status,status
                    assert not errors,errors
                    page.screenshot(path=str(OUT/f"{deck}-{form}-live.png"),
                                    full_page=True,timeout=30000)
                    print(f"PASS {deck} {form}: 12 real approved games in original Results UI")
                except Exception:
                    print("DEBUG",deck,form,"url",page.url,
                          "title",page.title(),
                          "body",page.locator("body").inner_text(timeout=5000)[:1200] if page.locator("body").count() else "(missing)",
                          "status",page.locator("#game-outcome-status").inner_text(timeout=3000) if page.locator("#game-outcome-status").count() else "(missing)",
                          "responses",seen,"pageerrors",errors)
                    page.screenshot(path=str(OUT/f"{deck}-{form}-failure.png"),
                                    full_page=True,timeout=30000)
                    raise
                finally:
                    page.close()
        browser.close()
if __name__=="__main__":run()
