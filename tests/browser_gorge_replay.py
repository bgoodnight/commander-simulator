"""Headless browser smoke test of the ACTUAL built static Deck Lab replay UI.

Requires playwright + installed Chromium. Serves committed docs/deck-lab as
GitHub Pages serves it, with no mocked UI or replay JSON.
"""
from __future__ import annotations
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
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
    assert (ROOT/"results.html").is_file(), "Published results.html missing"
    assert (ROOT/"gorge-data"/"manifest.json").is_file(), "Public gorge data absent"
    manifest=json.loads((ROOT/"gorge-data"/"manifest.json").read_text())
    assert manifest["schema"]=="gorge-public-replay-manifest-v1"
    assert {g["seed"] for g in manifest["games"]}=={300,301}
    game_by_seed={g["seed"]:json.loads(
        (ROOT/"gorge-data"/g["file"]).read_text()) for g in manifest["games"]}
    errors=[]
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    server.daemon_threads=True
    Thread(target=server.serve_forever,daemon=True).start()
    url=f"http://127.0.0.1:{server.server_port}/results.html"
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            page=browser.new_page(viewport={"width":1440,"height":1000},
                                     device_scale_factor=1)
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.goto(url,wait_until="domcontentloaded",timeout=45000)
            # Gorge has to be in the active Results pane, not hidden behind
            # the old Python simulated-results archive.
            page.locator("#gorge-replay-root h3").filter(
                has_text="Gorge Commander · Game 300").wait_for(state="attached",timeout=20000)
            # Diagnose visibility from REAL computed styles, including app
            # container/accordion ancestry. Save a screenshot even on failure.
            page.wait_for_timeout(2500)
            ancestors=page.evaluate("""() => {
              const el=document.querySelector('#gorge-replay-root h3');
              let p=el, out=[];
              while(p&&out.length<16){
                const st=getComputedStyle(p);
                out.push({id:p.id,tag:p.tagName,cls:p.className,
                  hidden:p.hidden,open:p.open,display:st.display,
                  visibility:st.visibility,rect:p.getBoundingClientRect().height});
                p=p.parentElement;
              }
              return out;
            }""")
            print("VISIBILITY",json.dumps(ancestors),flush=True)
            print("BROWSER ERRORS",errors,flush=True)
            page.screenshot(path=str(OUT/"before-fix-diagnostic.png"),full_page=False)
            page.locator("#gorge-replay-root h3").filter(
                has_text="Gorge Commander · Game 300").wait_for(timeout=15000)
            # The ORIGINAL Results components must be restored outside the
            # retired Python archive, not replaced by a new visual design.
            page.locator("#game-outcome-results .game-outcome-hero").wait_for(timeout=20000)
            for original_id in (
                "simulation-snapshot","key-insights-panel","long-game-panel",
                "turn-reviewer-panel","development-panel"):
                assert page.locator("#"+original_id).is_visible(), original_id
                assert page.locator("#"+original_id).evaluate(
                    "(el)=>!el.closest('#legacy-simulation-archive')"), (
                    original_id+" is still inside the Python archive")
            assert page.locator("#game-outcome-results .game-outcome-hero-highlight").count()==4
            assert page.locator("#key-insights-grid .insight-report").count()>=2
            assert page.locator("#gorge-recorded-deck-select").is_visible()
            assert page.locator("#game-outcome-status").inner_text().lower().count("gorge")==1
            assert page.locator("#turn-reviewer-panel #gorge-replay-panel").count()==1
            # The exact old hero/insight/reviewer styling remains present.
            assert page.locator(".game-outcome-grid.latest-insight-grid").count()==1
            assert page.locator(".insight-summary").count()>=1
            page.screenshot(path=str(OUT/"gorge-restored-original-dashboard.png"),
                            full_page=False)
            # Changing the original commander context changes the selected
            # gorge cohort (not the retired Python cohort).
            page.locator("#gorge-recorded-deck-select").select_option("magnus_premium")
            page.locator("#game-outcome-status").filter(
                has_text="2 gorge Commander games").wait_for(timeout=12000)
            assert "0%" in page.locator(".game-outcome-hero-stat.is-win").first.inner_text()
            assert page.locator("#key-insights-grid .insight-report").count()>=2
            page.locator("#gorge-recorded-deck-select").select_option("mortarion_current")
            page.locator("#game-outcome-status").filter(
                has_text="1 gorge Commander game").wait_for(timeout=12000)
            assert "100%" in page.locator(".game-outcome-hero-stat.is-win").first.inner_text()
            assert page.locator("#gorge-replay-samples").is_visible()
            assert page.locator("#gorge-replay-panel").is_visible()
            assert not page.locator("#legacy-simulation-archive").evaluate(
                "(el)=>el.open"), "Legacy Python archive should be collapsed"
            assert page.locator(".gorge-replay-player").count()==4
            for seed in (300,301):
                expected=game_by_seed[seed]
                if seed!=300:
                    page.locator("#gorge-replay-sample-select").select_option(
                        f"gorge-seed-{seed}.ui.json")
                    page.locator("#gorge-replay-load").click()
                    page.locator("#gorge-replay-root h3").filter(
                        has_text=f"Gorge Commander · Game {seed}").wait_for(timeout=20000)
                assert page.locator(".gorge-replay-turn").count()==len(expected["turns"])
                assert page.locator(".gorge-replay-player").count()==4
                assert "first pending decision" in page.locator(
                    ".gorge-replay-caution").inner_text().lower()
                turn_one=page.locator(".gorge-replay-turn").nth(1)
                assert turn_one.evaluate("(el)=>el.open")
                state=turn_one.locator(".gorge-replay-state")
                assert state.count()==1, f"Turn one lacks authoritative state for {seed}"
                state.locator("summary").first.click()
                boxes=state.locator(".gorge-replay-state-player")
                assert boxes.count()==4
                life=boxes.first.inner_text()
                assert "Life 40" in life and "Hand 7" in life, (seed,life)
                assert "Library 92" in life, (seed,life)
                zones=boxes.first.locator(".gorge-replay-zone")
                assert zones.count()==4, f"Not four public zones in seed {seed}"
                command=zones.nth(3)
                command.locator("summary").click()
                assert command.locator("a").count()>=1
                assert "scryfall.com/search" in command.locator("a").first.get_attribute("href")
                # Ensure the actual displayed battlefield cards belong to
                # source snapshot, not pre-canned fixture strings.
                expected_name=expected["snapshots"][0]["players"][0]["zones"]["command"][0]["name"]
                assert expected_name in command.inner_text(),(seed,expected_name)
                # Native event lines are present in the UI after turn expansion.
                assert turn_one.locator(".gorge-replay-event").count()==expected["turns"][1]["event_count"]
                # Visible card identity is not a secret-zone lookup.
                assert page.locator(".gorge-replay-error").count()==0
                page.screenshot(path=str(OUT/f"gorge-seed-{seed}-desktop.png"),
                                full_page=False)
                print(f"PASS seed {seed}: {len(expected['turns'])} turns, "
                      f"{len(expected['snapshots'])} authoritative snapshots, 4 player states, "
                      f"command-zone card {expected_name}")
            # Mobile sizing and control accessibility.
            page.set_viewport_size({"width":390,"height":844})
            page.screenshot(path=str(OUT/"gorge-seed-301-mobile.png"),full_page=False)
            widths=page.evaluate("""() => ({
              viewport: window.innerWidth,
              page: document.documentElement.scrollWidth,
              panel: document.querySelector('#gorge-replay-panel').getBoundingClientRect().width,
              panelScroll: document.querySelector('#gorge-replay-panel').scrollWidth
            })""")
            print("MOBILE WIDTHS",json.dumps(widths),flush=True)
            assert widths["page"]<=widths["viewport"]+2, (
                "Horizontal mobile overflow: "+str(widths))
            assert page.locator("#gorge-replay-load").is_visible()
            assert page.locator("#gorge-replay-sample-select").is_visible()
            # Unknown JS errors should be reported instead of silently hidden.
            assert not errors, "Unexpected browser JavaScript errors: "+"; ".join(errors[:8])
            browser.close()
        print("PASS: actual Deck Lab built site, desktop/mobile, two source games")
    finally:
        server.shutdown()
        server.server_close()


if __name__=="__main__":
    check()
