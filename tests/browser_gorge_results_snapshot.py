"""Browser checks for the current published Gorge snapshot and its insights."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import os
from playwright.sync_api import sync_playwright

ROOT = Path(os.environ['BROWSER_SITE_DIR'])
OUT = Path(os.environ['BROWSER_ARTIFACT_DIR'])
OUT.mkdir(parents=True, exist_ok=True)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def log_message(self, *args):
        pass

def check():
    manifest = json.loads((ROOT/'gorge-data'/'manifest.json').read_text())
    cards = json.loads((ROOT/'gorge-data'/'card-insights.json').read_text())
    cohort = json.loads((ROOT/'gorge-data'/'cohort.json').read_text())
    key = 'wretched_ranks'
    assert any(g.get('player_deck') == key for g in manifest['games'])
    assert cards['decks'][key]['verified_games'] == cohort['decks'][key]['n']
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    errors = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for name, size in [('desktop', {'width':1440,'height':1000}),
                               ('mobile', {'width':390,'height':844})]:
                page = browser.new_page(viewport=size, device_scale_factor=1)
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(f'http://127.0.0.1:{server.server_port}/results.html?deck={key}',
                          wait_until='domcontentloaded')
                hero = page.locator('#game-outcome-results .game-outcome-hero-frame')
                hero.wait_for(state='visible', timeout=60000)
                page.get_by_text('Best matchup', exact=True).wait_for(timeout=60000)
                assert 'Verified games' not in hero.inner_text()
                assert 'Replay coverage' not in hero.inner_text()
                tiles = hero.locator('.gorge-highlight-details')
                assert tiles.count() == 4
                tiles.nth(0).locator('summary').first.click()
                matchup = tiles.nth(0)
                assert matchup.locator('table tbody tr').count() > 0
                selector = matchup.get_by_label('Compare full-cohort performance by')
                selector.select_option('identities')
                assert matchup.locator('table tbody tr').count() > 0
                tiles.nth(0).locator('summary').first.click()
                tiles.nth(1).locator('summary').first.click()
                tiles.nth(2).locator('summary').first.click()
                assert tiles.nth(2).locator('.gorge-sample-chart').count() == 1
                tiles.nth(2).locator('summary').first.click()
                tiles.nth(3).locator('summary').first.click()
                assert tiles.nth(3).locator('.gorge-sample-chart').count() == 1
                page.evaluate('window.scrollTo(0,0)')
                page.screenshot(path=str(OUT/(name+'-life.png')), full_page=True)
                tiles.nth(3).locator('summary').first.click()
                assert tiles.nth(1).locator('.game-outcome-finish-row').count() > 0
                tiles.nth(1).locator('summary').first.click()
                insight = page.locator('#game-outcome-results .insight-featured-panel').first
                insight.locator('summary').first.click()
                chooser = insight.get_by_label('Choose card type')
                assert chooser.is_visible()
                chooser.select_option('creature')
                replacement = page.locator('#game-outcome-results .insight-featured-panel').first
                assert 'Most played creature' in replacement.locator('summary').first.inner_text()
                replacement.locator('summary').first.click()
                assert page.locator('.gorge-full-cohort-regressions').count() == 1
                assert page.locator('#turn-reviewer-panel').is_visible()
                page.evaluate('window.scrollTo(0,0)')
                page.screenshot(path=str(OUT/(name+'-results.png')), full_page=True)
                tiles.nth(0).locator('summary').first.click()
                page.screenshot(path=str(OUT/(name+'-matchups.png')), full_page=True)
                page.close()
            browser.close()
        assert not errors, errors
    finally:
        server.shutdown()

if __name__ == '__main__':
    check()
