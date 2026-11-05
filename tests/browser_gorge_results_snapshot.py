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
    cohort = json.loads((ROOT/'gorge-data'/'cohort.json').read_text())
    if manifest.get('eligibility') == 'approved_current_only' and not manifest['games']:
        # This is the real, fail-closed production state before signoff.
        # Detailed visual regression is exercised on the UI staging branch;
        # never manufacture an approved cohort for this deployment test.
        assert cohort['total_verified_games'] == 0
        assert cohort['decks'] == {}
        assert not (ROOT/'gorge-data'/'card-insights.json').exists()
        print('PASS: no stale card insights, sample outcomes or regressions published')
        return
    cards = json.loads((ROOT/'gorge-data'/'card-insights.json').read_text())
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
                assert 'Draws' not in hero.inner_text()
                baseline = hero.locator('.game-outcome-baseline')
                assert baseline.count() == 1
                assert baseline.get_attribute('aria-label') == '25 percent equal-chance four-player baseline'
                offset = baseline.evaluate('(e) => (e.getBoundingClientRect().left + e.getBoundingClientRect().width / 2 - e.parentElement.getBoundingClientRect().left) / e.parentElement.getBoundingClientRect().width')
                assert abs(offset - .25) < .005
                dialog = hero.locator('.gorge-cohort-dialog')
                hero.locator('.game-outcome-hero-summary').click()
                assert dialog.is_visible()
                assert dialog.locator('.gorge-compare-row').count() >= 3
                assert dialog.get_by_label('Compare by opponent deck').get_attribute('aria-pressed') == 'true'
                assert dialog.get_by_label('Sort highest win rate first').get_attribute('aria-pressed') == 'true'
                dialog.get_by_label('Sort lowest win rate first').click()
                assert dialog.get_by_label('Sort lowest win rate first').get_attribute('aria-pressed') == 'true'
                dialog.get_by_label('Compare by opponent color').click()
                assert dialog.get_by_label('Compare by opponent color').get_attribute('aria-pressed') == 'true'
                assert dialog.get_by_label('Compare by opponent deck').get_attribute('aria-pressed') == 'false'
                assert dialog.locator('.gorge-compare-row').count() > 0
                dialog.get_by_label('How matchup rates are calculated').click()
                assert 'multiple rows' in dialog.inner_text()
                page.screenshot(path=str(OUT/(name+'-outcomes.png')))
                dialog.get_by_label('Close details').click()
                assert not dialog.is_visible()
                tiles = hero.locator('.gorge-highlight-button')
                assert tiles.count() == 4
                tiles.nth(0).click()
                assert dialog.locator('table tbody tr').count() > 0
                assert 'Deadly Disguise' in dialog.inner_text()
                selector = dialog.get_by_label('Compare full-cohort performance by')
                selector.select_option('identities')
                assert dialog.locator('table tbody tr').count() > 0
                page.keyboard.press('Escape')
                assert not dialog.is_visible()
                tiles.nth(1).click()
                assert dialog.locator('.gorge-turn-column').count() > 0
                chart = dialog.locator('.gorge-turn-chart')
                assert chart.evaluate('(e) => e.scrollWidth <= e.clientWidth')
                dialog.get_by_label('Close details').click()
                for index in (2,3):
                    tiles.nth(index).click()
                    assert dialog.locator('.gorge-sample-chart').count() == 1
                    if index == 3:
                        page.screenshot(path=str(OUT/(name+'-life.png')))
                    dialog.get_by_label('Close details').click()
                insight = page.locator('#game-outcome-results .insight-featured-panel').first
                insight.locator('summary').first.click()
                assert insight.get_by_role('button', name='All cards').get_attribute('aria-pressed') == 'true'
                insight.get_by_role('button', name='Creatures').click()
                replacement = page.locator('#game-outcome-results .insight-featured-panel').first
                assert 'Most played creature' in replacement.locator('summary').first.inner_text()
                replacement.get_by_role('button', name='Show least played first').click()
                replacement = page.locator('#game-outcome-results .insight-featured-panel').first
                assert 'Least played' in replacement.locator('summary').first.inner_text()
                assert 'may be absent' in replacement.inner_text()
                replacement.locator('summary').first.click()
                assert page.get_by_text('Most frequently seen card', exact=False).count() == 0
                assert page.get_by_text('Most often left unplayed', exact=False).count() == 0
                held = page.locator('#game-outcome-results .insight-featured-panel').filter(has_text='Longest held in hand').first
                held.locator('summary').first.click()
                assert 'mean rounds held' in held.inner_text()
                assert 'headline shows the median' in held.inner_text()
                held.locator('summary').first.click()
                assert page.locator('.gorge-full-cohort-regressions').count() == 1
                model = page.locator('.gorge-full-cohort-regressions')
                model.locator('summary').click()
                assert 'opponent:' not in model.inner_text()
                assert 'Opponent:' in model.inner_text()
                model.locator('summary').click()
                assert page.locator('#turn-reviewer-panel').is_visible()
                page.evaluate('window.scrollTo(0,0)')
                page.screenshot(path=str(OUT/(name+'-results.png')), full_page=True)
                tiles.nth(0).click()
                page.screenshot(path=str(OUT/(name+'-matchups.png')))
                dialog.get_by_label('Close details').click()
                page.close()
            browser.close()
        assert not errors, errors
    finally:
        server.shutdown()

if __name__ == '__main__':
    check()
