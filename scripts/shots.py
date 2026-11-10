#!/usr/bin/env python3
"""Screenshots and browser checks with Playwright (project-local venv).
    PLAYWRIGHT_BROWSERS_PATH=.cache/pw .venv/bin/python scripts/shots.py [page ...]
Saves qa/shots/<page>-<width>[-mood|-rm].png, prints horizontal-scroll,
console-error and hero-measurement results, and writes qa/shots/summary.json.
"""
import json
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'qa', 'shots')
os.makedirs(OUT, exist_ok=True)
PAGES = ['index', 'work', 'about', 'b-roll', 'case-monthly-mix', 'case-podcast', 'case-content-engine', 'case-paid-vs-organic']
SIZES = [(390, 844), (768, 1024), (1366, 768), (1440, 900)]
only = sys.argv[1:]
if only:
    PAGES = [p for p in PAGES if p in only]


def url(p):
    return 'file://' + os.path.join(ROOT, p + '.html')


def settle(page):
    """Scroll through so every reveal has fired, then return to the top."""
    h = page.evaluate('document.documentElement.scrollHeight')
    y = 0
    while y < h:
        page.evaluate('window.scrollTo({top: %d, behavior: "instant"})' % y)
        page.wait_for_timeout(120)
        y += 500
    page.evaluate('window.scrollTo({top: 0, behavior: "instant"})')
    page.wait_for_timeout(1400)


def run(browser, p, w, h, mood='light', rm=False, suffix=''):
    ctx = browser.new_context(viewport={'width': w, 'height': h}, reduced_motion='reduce' if rm else 'no-preference', device_scale_factor=1)
    ctx.add_init_script("try{localStorage.setItem('mood','%s')}catch(e){}" % mood)
    page = ctx.new_page()
    errors = []
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(url(p))
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(600)
    rec = {'page': p, 'w': w, 'h': h, 'mood': mood, 'rm': rm}
    if p == 'index' and w in (1366, 1440) and mood == 'light' and not rm:
        page.wait_for_timeout(1500)
        rec['hero'] = page.evaluate("""() => { const r = s => { const e = document.querySelector(s); if(!e) return null; const b = e.getBoundingClientRect(); return {top: Math.round(b.top), bottom: Math.round(b.bottom), left: Math.round(b.left), right: Math.round(b.right)} };
          return {viewport: innerHeight, role: r('.hero__role'), btn1: r('.hero__btns a:first-child'), btn2: r('.hero__btns a:last-child'), pic: r('.hero__pic')} }""")
    settle(page)
    rec['scrollWidth'] = page.evaluate('document.documentElement.scrollWidth')
    rec['innerWidth'] = page.evaluate('innerWidth')
    rec['errors'] = errors
    name = '%s-%d%s%s.png' % (p, w, '-' + mood if mood != 'light' else '', '-rm' if rm else '')
    page.screenshot(path=os.path.join(OUT, name), full_page=True)
    rec['shot'] = name
    ctx.close()
    flag = '' if rec['scrollWidth'] == rec['innerWidth'] else '  HSCROLL %d>%d' % (rec['scrollWidth'], rec['innerWidth'])
    err = '' if not errors else '  ERRORS %d' % len(errors)
    print(name, flag, err)
    if 'hero' in rec:
        print('  hero', json.dumps(rec['hero']))
    for e in errors:
        print('   !', e[:200])
    return rec


def main():
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for p in PAGES:
            for w, h in SIZES:
                results.append(run(browser, p, w, h))
            results.append(run(browser, p, 1440, 900, rm=True))
            if p == 'index':
                results.append(run(browser, p, 1440, 900, mood='dark'))
                results.append(run(browser, p, 1440, 900, mood='paper'))
                results.append(run(browser, p, 390, 844, mood='dark'))
        browser.close()
    with open(os.path.join(OUT, 'summary.json'), 'w') as f:
        json.dump(results, f, indent=1)
    bad = [r for r in results if r['scrollWidth'] != r['innerWidth'] or r['errors']]
    print('\n%d shots, %d with problems' % (len(results), len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
