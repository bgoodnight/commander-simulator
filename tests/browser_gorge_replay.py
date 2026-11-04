"""Real Chromium verification: original Nov 3 Deck Lab layout, powered by Gorge.

Builds the actual Pages output. Tests the original metrics/insight/turn
containers and drills into verified Gorge public snapshots without exposing
private hand or library identities.
"""
from __future__ import annotations
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import os
from playwright.sync_api import sync_playwright

ROOT=(Path(os.environ["BROWSER_SITE_DIR"]) if "BROWSER_SITE_DIR" in os.environ
      else Path(__file__).resolve().parents[1]/"docs"/"deck-lab")
OUT=Path(os.getenv("BROWSER_ARTIFACT_DIR","/tmp/gorge-browser-evidence"))
OUT.mkdir(parents=True,exist_ok=True)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,format,*args):
        pass

def check():
    assert (ROOT/"results.html").is_file()
    manifest=json.loads((ROOT/"gorge-data"/"manifest.json").read_text())
    assert manifest["schema"]=="gorge-public-replay-manifest-v1"
    assert {g["seed"] for g in manifest["games"]}=={300,301}
    expected={g["seed"]:json.loads(
        (ROOT/"gorge-data"/g["file"]).read_text()) for g in manifest["games"]}
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    server.daemon_threads=True
    Thread(target=server.serve_forever,daemon=True).start()
    errors=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            page=browser.new_page(viewport={"width":1440,"height":1000},
                                     device_scale_factor=1)
            page.on("pageerror",lambda error:errors.append(str(error)))
            page.goto(f"http://127.0.0.1:{server.server_port}/results.html?deck=mortarion_current",
                      wait_until="domcontentloaded",timeout=45000)
            page.locator("#turn-reviewer-results .insight-turn-row").first.wait_for(
                state="visible",timeout=25000)
            assert page.locator("#simulation-snapshot").is_visible()
            assert page.locator("#key-insights-panel").is_visible()
            assert page.locator("#key-insights-grid .game-outcome-hero").count()==1
            assert page.locator("#key-insights-grid .insight-featured-panel").count()>=3
            assert page.locator("#long-game-panel").is_visible()
            assert page.locator("#turn-reviewer-panel").is_visible()
            assert page.locator("#turn-reviewer-results .insight-turn-row").count()>=8
            assert page.locator("#gorge-dashboard").count()==0, "Duplicate redesign surfaced"
            assert page.locator("#legacy-simulation-archive").count()==0
            assert not page.locator("#archive-observation-details").is_visible(), \
                "Retired Python snapshots should not appear in Gorge results"
            assert "gorge" in page.locator("#game-outcome-status").inner_text().lower()
            # Preserve old artwork and compact source-based mana/hand/life bars.
            turn=page.locator("#turn-reviewer-results .insight-turn-row").first
            assert turn.locator(".insight-turn-row-summary").is_visible()
            assert turn.locator(".insight-turn-activity").is_visible()
            turn.locator("summary").click()
            assert turn.locator(".insight-action-phase.is-player").is_visible()
            assert "not turn end" in turn.inner_text().lower() or \
                "not end" in turn.inner_text().lower()
            assert "hand" in turn.inner_text().lower()
            assert "battlefield" in turn.inner_text().lower()
            assert page.locator("#gorge-replay-panel").is_visible()
            assert not page.locator("#gorge-replay-panel").evaluate("(e)=>e.open"), \
                "Source inspector should not displace the original visual interface"
            page.screenshot(path=str(OUT/"restored-original-desktop.png"),full_page=False)
            page.locator("#gorge-replay-panel>summary").click()
            page.locator("#gorge-replay-root h3").filter(
                has_text="Gorge Commander · Game 300").wait_for(timeout=20000)
            assert page.locator("#gorge-replay-samples").is_visible()
            for seed in (300,301):
                if seed!=300:
                    page.locator("#gorge-replay-sample-select").select_option(
                        f"gorge-seed-{seed}.ui.json")
                    page.locator("#gorge-replay-load").click()
                    page.locator("#gorge-replay-root h3").filter(
                        has_text=f"Gorge Commander · Game {seed}").wait_for(timeout=20000)
                assert page.locator(".gorge-replay-turn").count()==len(expected[seed]["turns"])
                assert page.locator(".gorge-replay-player").count()==4
                assert "first pending decision" in page.locator(
                    ".gorge-replay-caution").inner_text().lower()
                one=page.locator(".gorge-replay-turn").nth(1)
                assert one.evaluate("(e)=>e.open")
                state=one.locator(".gorge-replay-state")
                assert state.count()==1
                state.locator("summary").first.click()
                boxes=state.locator(".gorge-replay-state-player")
                assert boxes.count()==4
                life=boxes.first.inner_text()
                assert "Life 40" in life and "Hand 7" in life
                zones=boxes.first.locator(".gorge-replay-zone")
                assert zones.count()==4
                zones.nth(3).locator("summary").click()
                assert zones.nth(3).locator("a").count()>=1
                expected_name=expected[seed]["snapshots"][0]["players"][0]["zones"]["command"][0]["name"]
                assert expected_name in zones.nth(3).inner_text()
                assert one.locator(".gorge-replay-event").count()==expected[seed]["turns"][1]["event_count"]
                assert page.locator(".gorge-replay-error").count()==0
            page.locator("#gorge-replay-panel>summary").click()
            page.set_viewport_size({"width":390,"height":844})
            page.evaluate("window.scrollTo(0,0)")
            page.screenshot(path=str(OUT/"restored-original-mobile.png"),full_page=False)
            widths=page.evaluate("""() => ({
              viewport: window.innerWidth,
              document: document.documentElement.scrollWidth,
              hero: document.querySelector('#key-insights-grid').getBoundingClientRect().width
            })""")
            print("MOBILE WIDTHS",json.dumps(widths),flush=True)
            assert widths["document"]<=widths["viewport"]+2, \
                "Horizontal overflow: "+str(widths)
            assert page.locator("#key-insights-grid").is_visible()
            assert page.locator("#turn-reviewer-results .insight-turn-row").first.is_visible()
            assert not errors,"Browser errors: "+"; ".join(errors[:8])
            browser.close()
        print("PASS restored original desktop/mobile Results UI with two Gorge samples")
    finally:
        server.shutdown()
        server.server_close()

if __name__=="__main__":
    check()
