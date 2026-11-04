"""Chromium regression: original card-first Deck Lab results with real Gorge data."""
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
    manifest=json.loads((ROOT/"gorge-data"/"manifest.json").read_text())
    assert manifest["schema"]=="gorge-public-replay-manifest-v1"
    assert {g["seed"] for g in manifest["games"]}=={300,301}
    expected={g["seed"]:json.loads(
        (ROOT/"gorge-data"/g["file"]).read_text()) for g in manifest["games"]}
    errors=[]
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    server.daemon_threads=True
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            page=browser.new_page(viewport={"width":1440,"height":1000},device_scale_factor=1)
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.goto(f"http://127.0.0.1:{server.server_port}/results.html?deck=mortarion_current",
                      wait_until="domcontentloaded",timeout=45000)
            insight=page.locator("#key-insights-grid .insight-featured-panel").first
            insight.wait_for(state="visible",timeout=25000)
            assert page.locator("#key-insights-grid .game-outcome-hero").count()==1
            assert page.locator("#key-insights-grid .insight-featured-panel").count()>=2
            assert not page.locator("#simulation-snapshot").is_visible()
            assert not page.locator("#turn-reviewer-panel").is_visible(), \
                "The main reviewer should not displace original inline insights"
            assert page.locator("#long-game-panel").is_visible()
            assert page.locator("#gorge-dashboard").count()==0
            assert not page.locator("#archive-observation-details").is_visible()
            assert "gorge" in page.locator("#game-outcome-status").inner_text().lower()
            insight.locator(".game-outcome-summary").click()
            assert insight.evaluate("(e)=>e.open")
            assert insight.locator(".insight-featured-compare").is_visible()
            assert insight.locator(".insight-featured-card-art").is_visible()
            preview=insight.locator(".insight-featured-card-art img").first
            assert preview.is_visible()
            assert "/normal/" in preview.get_attribute("src"), \
                "Featured card must show complete printed artwork, not a crop"
            assert insight.locator(".insight-featured-bars .insight-featured-bar").count()>=2
            tiles=insight.locator(".insight-featured-metrics .insight-featured-metric-link")
            assert tiles.count()==2
            assert "Times played" in tiles.first.inner_text()
            assert "Median event turn" in tiles.nth(1).inner_text()
            tracker=insight.locator(".insight-inline-tracker-compact")
            tracker.locator("summary").first.click()
            assert tracker.evaluate("(e)=>e.open")
            select=tracker.locator(".gorge-insight-example-select")
            assert select.is_visible()
            assert select.locator("option").count()>=1
            timeline=tracker.locator(".gorge-example-timeline")
            assert timeline.locator(".gorge-original-turn").count()>=9, \
                "Draw/opening plus individual turn rows expected"
            assert "Played Swamp" in timeline.locator(".gorge-original-turn").nth(1).inner_text(), \
                "Public-zone object identity should name the first played land"
            assert "Draw" in timeline.locator(".gorge-original-turn").first.inner_text()
            turn=timeline.locator(".gorge-original-turn").nth(1)
            assert turn.locator(".insight-turn-cover").count()==1
            assert turn.locator(".insight-turn-metrics").count()==1
            assert turn.locator(".insight-turn-row-summary .gorge-mana-pips").count()==1
            turn.locator(".insight-turn-row-summary").click()
            assert turn.evaluate("(e)=>e.open")
            state=turn.locator(".gorge-boundary-state")
            assert state.is_visible()
            assert "not an end-of-turn snapshot" in state.inner_text().lower()
            assert "hand" in state.inner_text().lower()
            assert "battlefield" in state.inner_text().lower()
            assert "creatures" in state.inner_text().lower()
            assert "artifacts" in state.inner_text().lower()
            assert "graveyard" in state.inner_text().lower()
            page.screenshot(path=str(OUT/"original-insight-desktop.png"),full_page=False)
            # Capture the OPENED insight, including old metrics and example
            # turns, before raw-replay changes re-render the results gallery.
            # Frame the original reference region (stats, selector, continuous
            # collapsed turns), not the expanded diagnostics or card preview.
            turn.locator(".insight-turn-row-summary").click()
            assert not turn.evaluate("(e)=>e.open")
            page.set_viewport_size({"width":390,"height":844})
            tiles.first.evaluate("""(e)=>{
              const bar=document.querySelector('.topbar');
              const offset=bar?bar.getBoundingClientRect().height+12:72;
              window.scrollTo(0,e.getBoundingClientRect().top+window.scrollY-offset);
            }""")
            picker=tracker.locator(".gorge-insight-example-select").bounding_box()
            reviewer_button=tracker.locator(".insight-example-full-link").bounding_box()
            assert picker and reviewer_button
            assert abs(picker["y"]-reviewer_button["y"])<=3, \
                "Classic mobile layout keeps picker and full-reviewer action side by side"
            assert picker["x"]+picker["width"]<reviewer_button["x"], \
                "Picker precedes the right-hand reviewer button"
            heights=[timeline.locator(".gorge-original-turn .insight-turn-row-summary").nth(i).bounding_box()["height"] for i in range(3)]
            assert all(45<=h<=85 for h in heights), \
                "Classic collapsed turn rows must stay compact: "+str(heights)
            page.screenshot(path=str(OUT/"original-insight-mobile.png"),full_page=False)
            widths=page.evaluate("""() => ({
              viewport: window.innerWidth,
              document: document.documentElement.scrollWidth,
              cards: document.querySelector('#key-insights-grid').getBoundingClientRect().width,
              selected: document.querySelector('.insight-featured-panel[open]').getBoundingClientRect().width
            })""")
            print("MOBILE WIDTHS",json.dumps(widths),flush=True)
            assert widths["document"]<=widths["viewport"]+2, \
                "Horizontal overflow: "+str(widths)
            assert insight.is_visible()
            assert timeline.locator(".gorge-original-turn").first.is_visible()
            page.set_viewport_size({"width":1440,"height":1000})
            # Original "Open full reviewer" should reveal the same source game
            # in a separate deep dive only when requested.
            tracker.locator(".insight-example-full-link").click()
            reviewer=page.locator("#turn-reviewer-panel")
            assert reviewer.is_visible()
            assert reviewer.locator(".insight-turn-row").count()>=9
            reviewer.locator(".gorge-full-review-head button").click()
            assert not reviewer.is_visible()
            # Source Gorge panel remains in a subordinate, collapsed area.
            raw=page.locator("#gorge-replay-panel")
            assert raw.is_visible()
            assert not raw.evaluate("(e)=>e.open")
            raw.locator("summary").first.click()
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
                assert "first pending decision" in page.locator(".gorge-replay-caution").inner_text().lower()
                turn_one=page.locator(".gorge-replay-turn").nth(1)
                assert turn_one.evaluate("(e)=>e.open")
                state=turn_one.locator(".gorge-replay-state")
                state.locator("summary").first.click()
                boxes=state.locator(".gorge-replay-state-player")
                assert boxes.count()==4
                assert "Life 40" in boxes.first.inner_text()
                assert "Hand 7" in boxes.first.inner_text()
                zones=boxes.first.locator(".gorge-replay-zone")
                assert zones.count()==4
                zones.nth(3).locator("summary").click()
                assert zones.nth(3).locator("a").count()>=1
                expected_name=expected[seed]["snapshots"][0]["players"][0]["zones"]["command"][0]["name"]
                assert expected_name in zones.nth(3).inner_text()
                assert turn_one.locator(".gorge-replay-event").count()==expected[seed]["turns"][1]["event_count"]
                assert page.locator(".gorge-replay-error").count()==0
            raw.locator("summary").first.click()
            assert not errors,"Browser JavaScript errors: "+"; ".join(errors[:8])
            browser.close()
        print("PASS: original card-insight layout, inline game viewer, source state, desktop/mobile")
    finally:
        server.shutdown()
        server.server_close()

if __name__=="__main__":
    check()
