"""Actual Nov 3 game_outcomes.js renderer, driven by source Gorge fixtures."""
from __future__ import annotations
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import os
from playwright.sync_api import sync_playwright

ROOT=Path(os.environ["BROWSER_SITE_DIR"]) if "BROWSER_SITE_DIR" in os.environ else Path(__file__).resolve().parents[1]/"docs"/"deck-lab"
OUT=Path(os.getenv("BROWSER_ARTIFACT_DIR","/tmp/gorge-browser-evidence"))
OUT.mkdir(parents=True,exist_ok=True)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,format,*args):
        pass

def check():
    assert (ROOT/"results.html").is_file()
    assert (ROOT/"gorge_legacy_adapter.js").is_file()
    manifest=json.loads((ROOT/"gorge-data"/"manifest.json").read_text())
    assert manifest["schema"]=="gorge-public-replay-manifest-v1"
    assert {g["seed"] for g in manifest["games"]}=={300,301}
    errors=[]
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    server.daemon_threads=True
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            page=browser.new_page(viewport={"width":1440,"height":1000},device_scale_factor=1)
            page.on("pageerror",lambda e:errors.append(str(e)))
            site=f"http://127.0.0.1:{server.server_port}/results.html"
            page.goto(site+"?deck=mortarion_current",wait_until="domcontentloaded",timeout=60000)
            insight=page.locator("#game-outcome-results .insight-featured-panel").first
            insight.wait_for(state="visible",timeout=40000)
            # The exact original module creates the cards and nested replay.
            # Fake/rebuilt GorgeDashboard card classes are not acceptable.
            assert page.locator("#game-outcome-results .game-outcome-hero").count()==1
            assert page.locator("#game-outcome-results .insight-featured-panel").count()>=3
            assert page.locator("#key-insights-panel").is_hidden()
            assert page.locator("#gorge-dashboard").count()==0
            assert "1 real Gorge game" in page.locator("#game-outcome-status").inner_text()
            assert "Wins" in page.locator(".game-outcome-hero-stats").inner_text()
            assert "1/1" in page.locator(".game-outcome-hero-stats").inner_text(), \
                "Mortarion native game-over marker identifies the winner"
            limits=page.locator("#game-outcome-results .game-outcome-limits")
            limits.locator("summary").click()
            assert "genuine 100-card decks" in limits.inner_text().lower()
            assert "NOT at turn end" in limits.inner_text()
            limits.locator("summary").click()
            insight.locator(".game-outcome-summary").click()
            assert insight.evaluate("(e)=>e.open")
            assert insight.locator(".insight-featured-compare").is_visible()
            assert insight.locator(".insight-featured-card-art img").is_visible()
            assert insight.locator(".insight-featured-bars .insight-featured-bar").count()>=2
            stats=insight.locator(".insight-featured-metrics .insight-featured-metric-link")
            assert stats.count()==2
            assert "Times played" in stats.first.inner_text()
            assert "Median event turn" in stats.nth(1).inner_text()
            tracker=insight.locator(".insight-inline-tracker")
            tracker.locator("summary").first.click()
            assert tracker.evaluate("(e)=>e.open")
            picker=tracker.locator(".gorge-legacy-example-select")
            assert picker.is_visible()
            assert "Seed 300" in picker.locator("option").first.inner_text()
            assert "Win" in picker.locator("option").first.inner_text()
            reviewer_link=tracker.locator(".insight-example-full-link")
            assert reviewer_link.is_visible()
            select_box=picker.bounding_box()
            button_box=reviewer_link.bounding_box()
            assert select_box and button_box
            assert abs(select_box["y"]-button_box["y"])<5, \
                "Original seed picker and full-reviewer action should share a row"
            timeline=tracker.locator(".insight-turn-timeline")
            assert timeline.locator(".insight-turn-row").count()>=9
            opening=timeline.locator(".insight-turn-row").first
            assert "Opening hand" in opening.inner_text()
            assert "identities private" in opening.inner_text()
            first=timeline.locator(".insight-turn-row").nth(1)
            assert "Played Swamp" in first.locator(".insight-turn-row-summary").inner_text()
            assert "Sol Ring" in first.locator(".insight-turn-row-summary").inner_text()
            assert first.locator(".insight-turn-cover").count()==1
            assert "Hand 6" in first.locator(".insight-turn-metrics").inner_text()
            first.locator(".insight-turn-row-summary").click()
            assert first.evaluate("(e)=>e.open")
            assert "Recorded turn-entry state" in first.locator(".insight-end-state").inner_text()
            assert "Individual identities are private" in first.locator(".insight-end-state").inner_text()
            assert "Lands" in first.locator(".insight-end-state").inner_text()
            page.screenshot(path=str(OUT/"original-renderer-desktop.png"),full_page=False)
            first.locator(".insight-turn-row-summary").click()
            page.set_viewport_size({"width":390,"height":844})
            stats.first.scroll_into_view_if_needed()
            page.screenshot(path=str(OUT/"original-renderer-mobile.png"),full_page=False)
            widths=page.evaluate("""() => ({
              viewport: window.innerWidth,
              document: document.documentElement.scrollWidth
            })""")
            print("MOBILE WIDTHS",json.dumps(widths),flush=True)
            assert widths["document"]<=widths["viewport"]+2, \
                "Horizontal overflow "+str(widths)
            assert insight.is_visible()
            assert tracker.is_visible()
            # Clicking a ranked contender reuses the SAME legacy statistics
            # and source-linked examples, not a separate Gorge renderer.
            bars=insight.locator(".insight-featured-bar")
            bars.nth(1).click()
            assert bars.nth(1).get_attribute("aria-pressed")=="true"
            # Full reviewer comes from the original module as well.
            page.set_viewport_size({"width":1440,"height":1000})
            tracker=insight.locator(".insight-inline-tracker")
            if not tracker.evaluate("(e)=>e.open"):
                tracker.locator("summary").first.click()
            tracker.locator(".insight-example-full-link").click()
            reviewer=page.locator("#turn-reviewer-results")
            assert reviewer.locator(".insight-turn-row").count()>=9
            # Original source inspector remains independent, in a collapsed drawer.
            raw=page.locator("#gorge-replay-panel")
            assert raw.is_visible()
            assert not raw.evaluate("(e)=>e.open")
            raw.locator("summary").first.click()
            page.locator("#gorge-replay-root h3").filter(
                has_text="Gorge Commander · Game 300").wait_for(timeout=25000)
            assert page.locator(".gorge-replay-turn").count()>=38
            raw.locator("summary").first.click()
            # Selected hero may be elsewhere in original seat order.
            page.goto(site+"?deck=magnus_premium",wait_until="domcontentloaded",timeout=60000)
            page.locator("#game-outcome-results .insight-featured-panel").first.wait_for(timeout=40000)
            assert "2 real Gorge games" in page.locator("#game-outcome-status").inner_text()
            hero=page.locator("#game-outcome-results .game-outcome-hero")
            assert "Losses" in hero.inner_text()
            assert "2/2" in hero.inner_text()
            assert not errors,"Browser page errors: "+"; ".join(errors[:9])
            browser.close()
        print("PASS: actual original renderer, real Gorge outcomes, evidence, mobile and source isolation")
    finally:
        server.shutdown()
        server.server_close()

if __name__=="__main__":
    check()
