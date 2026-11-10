#!/usr/bin/env python3
"""Keyboard, hover and console pass with Playwright (project-local venv).
    PLAYWRIGHT_BROWSERS_PATH=.cache/pw .venv/bin/python scripts/qa.py
Covers: menu overlay, About panel, galleries, lightbox, copy button,
marquee pause, index-row hover thumbnails, mood toggle, console errors.
Saves hover and overlay screenshots to qa/shots/ and exits 1 on failure.
"""
import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'qa', 'shots')
PAGES = ['index', 'work', 'about', 'b-roll', 'case-monthly-mix', 'case-podcast', 'case-content-engine', 'case-paid-vs-organic']
fails = []


def ok(cond, msg):
    print(('ok   ' if cond else 'FAIL ') + msg)
    if not cond:
        fails.append(msg)


def url(p):
    return 'file://' + os.path.join(ROOT, p + '.html')


def active(page):
    return page.evaluate("() => { const a = document.activeElement; return a ? (a.tagName + '|' + (a.className || '') + '|' + (a.textContent || '').trim().slice(0, 30)) : '' }")


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
        ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
        errors = {}
        page = ctx.new_page()
        page.on('console', lambda m: errors.setdefault(page.url, []).append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: errors.setdefault(page.url, []).append(str(e)))

        # ---- console errors on every page ----
        for p in PAGES:
            page.goto(url(p))
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(300)
        ok(not any(errors.values()), 'zero console errors on every page %s' % ({k.split('/')[-1]: v for k, v in errors.items() if v} or ''))

        # ---- home: menu overlay ----
        page.goto(url('index'))
        page.wait_for_load_state('networkidle')
        page.keyboard.press('Tab')
        ok('skip' in active(page), 'first Tab lands on the skip link')
        page.focus('.hdr__menu')
        page.keyboard.press('Enter')
        page.wait_for_timeout(200)
        ok(page.evaluate("document.getElementById('menu').classList.contains('is-open')"), 'MENU opens the overlay')
        ok(page.evaluate("document.documentElement.classList.contains('is-locked')"), 'page behind the overlay does not scroll')
        first = active(page)
        ok('close' in first or 'row' in first, 'focus moves into the overlay (%s)' % first)
        for _ in range(14):
            page.keyboard.press('Tab')
        ok(page.evaluate("document.getElementById('menu').contains(document.activeElement)"), 'Tab stays trapped inside the overlay')
        page.keyboard.press('Shift+Tab')
        ok(page.evaluate("document.getElementById('menu').contains(document.activeElement)"), 'Shift+Tab stays trapped inside the overlay')
        page.screenshot(path=os.path.join(OUT, 'qa-menu-1440.png'))
        page.keyboard.press('Escape')
        page.wait_for_timeout(200)
        ok(not page.evaluate("document.getElementById('menu').classList.contains('is-open')"), 'Esc closes the overlay')
        ok('hdr__menu' in active(page), 'focus returns to MENU')

        # ---- About panel ----
        page.focus('.hdr__role')
        page.keyboard.press('Enter')
        page.wait_for_timeout(700)
        ok(page.evaluate("document.getElementById('about-panel').classList.contains('is-open')"), 'role button opens the About panel')
        ok(page.evaluate("document.querySelector('.veil').classList.contains('is-on')"), 'veil dims the page')
        for _ in range(6):
            page.keyboard.press('Tab')
        ok(page.evaluate("document.getElementById('about-panel').contains(document.activeElement)"), 'Tab trapped inside the About panel')
        page.screenshot(path=os.path.join(OUT, 'qa-about-panel-1440.png'))
        page.keyboard.press('Escape')
        page.wait_for_timeout(700)
        ok(not page.evaluate("document.getElementById('about-panel').classList.contains('is-open')"), 'Esc closes the About panel')
        ok('hdr__role' in active(page), 'focus returns to the role button')
        page.focus('.hdr__role')
        page.keyboard.press('Enter')
        page.wait_for_timeout(700)
        page.mouse.click(1300, 500)
        page.wait_for_timeout(700)
        ok(not page.evaluate("document.getElementById('about-panel').classList.contains('is-open')"), 'click on the dimmed page closes the panel')

        # ---- copy button ----
        page.evaluate("document.getElementById('say-hi').scrollIntoView()")
        page.wait_for_timeout(300)
        page.focus('[data-copy]')
        page.keyboard.press('Enter')
        page.wait_for_timeout(200)
        ok(page.evaluate("document.querySelector('[data-copy]').textContent") == '[Copied]', 'copy button shows [Copied]')
        try:
            clip = page.evaluate('navigator.clipboard.readText()')
        except Exception:
            clip = ''
        ok(clip == 'itsriyagandhi@gmail.com', 'clipboard holds the address (%s)' % (clip or 'clipboard not readable here'))
        page.wait_for_timeout(2100)
        ok(page.evaluate("document.querySelector('[data-copy]').textContent") == '[Copy]', 'copy button returns to [Copy] after 2 s')

        # ---- marquee pause ----
        page.focus('.ftr .marquee__ctl')
        page.keyboard.press('Enter')
        ok(page.evaluate("document.querySelector('.ftr .marquee__ctl').getAttribute('aria-pressed')") == 'true', 'marquee [Pause] sets aria-pressed')
        ok(page.evaluate("getComputedStyle(document.querySelector('.ftr .marquee__track')).animationPlayState") == 'paused', 'marquee animation paused')
        page.keyboard.press('Enter')
        ok(page.evaluate("document.querySelector('.ftr .marquee__ctl').textContent") == '[Pause]', 'marquee control toggles back')

        # ---- mood toggle ----
        page.focus('.mood')
        page.keyboard.press('Enter')
        ok(page.evaluate("document.documentElement.getAttribute('data-mood')") == 'dark', 'mood toggle cycles to Dark')
        ok(page.evaluate("document.querySelector('.mood').getAttribute('aria-label')") == 'Mood: Dark. Change mood', 'mood aria-label updates')
        page.keyboard.press('Enter')
        page.keyboard.press('Enter')
        ok(page.evaluate("document.documentElement.getAttribute('data-mood')") == 'light', 'mood toggle cycles back to Light')

        # ---- hover states on index rows ----
        page.evaluate("document.querySelector('.row--case').scrollIntoView({block:'center'})")
        page.wait_for_timeout(1200)
        page.hover('.row--case')
        page.wait_for_timeout(1300)
        tr = page.evaluate("getComputedStyle(document.querySelector('.row--case .l')).transform")
        ok(tr != 'none', 'letters roll up on hover (transform %s)' % tr)
        th = page.evaluate("getComputedStyle(document.querySelector('.row--case .thumb__in')).transform")
        ok(th in ('none', 'matrix(1, 0, 0, 1, 0, 0)'), 'thumbnails slide in on hover')
        hk = page.evaluate("getComputedStyle(document.querySelector('.row--case .row__hook')).opacity")
        ok(hk == '1', 'hook caption shows on hover')
        col = page.evaluate("getComputedStyle(document.querySelector('.row--case .row__n')).color")
        ok(col == 'rgb(216, 60, 39)', 'bracket number fades to the accent (%s)' % col)
        page.screenshot(path=os.path.join(OUT, 'qa-hover-row-1440.png'))
        page.hover('.hdr__role')
        page.wait_for_timeout(1200)
        page.screenshot(path=os.path.join(OUT, 'qa-hover-role-1440.png'), clip={'x': 0, 'y': 0, 'width': 520, 'height': 56})
        page.mouse.move(5, 500)

        # keyboard focus triggers the roll too
        page.focus('.row--case')
        page.wait_for_timeout(1200)
        ok(page.evaluate("getComputedStyle(document.querySelector('.row--case .l')).transform") != 'none', 'letters roll on keyboard focus')

        # ---- gallery keyboard ----
        page.goto(url('case-monthly-mix'))
        page.wait_for_load_state('networkidle')
        page.evaluate("document.querySelector('.gal').scrollIntoView()")
        page.focus('.gal__track')
        page.keyboard.press('ArrowRight')
        page.wait_for_timeout(900)
        ok(page.evaluate("document.querySelector('.gal__count').textContent") == '[2/2]', 'ArrowRight moves the gallery to [2/2]')
        page.keyboard.press('ArrowLeft')
        page.wait_for_timeout(900)
        ok(page.evaluate("document.querySelector('.gal__count').textContent") == '[1/2]', 'ArrowLeft moves back to [1/2]')
        page.focus('[data-next]')
        page.keyboard.press('Enter')
        page.wait_for_timeout(900)
        ok(page.evaluate("document.querySelector('.gal__count').textContent") == '[2/2]', 'next arrow button works by keyboard')
        page.hover('.nextcase .row')
        page.wait_for_timeout(1300)
        page.screenshot(path=os.path.join(OUT, 'qa-hover-nextcase-1440.png'), clip={'x': 0, 'y': 0, 'width': 1440, 'height': 900})

        # ---- b-roll: lightbox and video ----
        page.goto(url('b-roll'))
        page.wait_for_load_state('networkidle')
        page.evaluate("document.querySelector('.grid').scrollIntoView()")
        page.focus('[data-tile]')
        page.keyboard.press('Enter')
        page.wait_for_timeout(300)
        ok(page.evaluate("document.getElementById('lightbox').open"), 'lightbox opens from a tile')
        page.keyboard.press('ArrowRight')
        page.wait_for_timeout(200)
        ok(page.evaluate("document.querySelector('.lb__count').textContent") == '[2/6]', 'ArrowRight moves the lightbox to [2/6]')
        page.keyboard.press('ArrowLeft')
        page.keyboard.press('ArrowLeft')
        page.wait_for_timeout(200)
        ok(page.evaluate("document.querySelector('.lb__count').textContent") == '[6/6]', 'ArrowLeft wraps to [6/6]')
        page.screenshot(path=os.path.join(OUT, 'qa-lightbox-1440.png'))
        page.keyboard.press('Escape')
        page.wait_for_timeout(200)
        ok(not page.evaluate("document.getElementById('lightbox').open"), 'Esc closes the lightbox')
        ok('tile' in active(page), 'focus returns to the tile')
        page.evaluate("document.querySelector('[data-video]').scrollIntoView({block:'center'})")
        page.wait_for_timeout(1500)
        ok(page.evaluate("!document.querySelector('[data-video] video').paused"), 'studio video plays while at least half visible')
        ok(page.evaluate("document.querySelector('[data-video] video').muted"), 'studio video is muted')
        page.evaluate("document.querySelector('.ftr').scrollIntoView()")
        page.wait_for_timeout(1200)
        ok(page.evaluate("document.querySelector('[data-video] video').paused"), 'studio video pauses when scrolled away')
        page.evaluate("document.querySelector('[data-video]').scrollIntoView({block:'center'})")
        page.wait_for_timeout(800)
        page.focus('[data-play]')
        page.keyboard.press('Enter')
        page.wait_for_timeout(200)
        ok(page.evaluate("document.querySelector('[data-video] video').paused"), '[Pause] stops the video')
        ok(page.evaluate("document.querySelector('[data-play]').textContent") == '[Play]', 'control reads [Play] when paused')

        # ---- reduced motion: typing shows full text at once, no roll ----
        rctx = browser.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        rp = rctx.new_page()
        rp.goto(url('index'))
        rp.wait_for_load_state('networkidle')
        rp.wait_for_timeout(300)
        ok(rp.evaluate("document.querySelector('.pull [data-type]').textContent") == 'will they stay?', 'reduced motion: pull quote shown in full at once')
        rp.evaluate("document.querySelector('.row--case').scrollIntoView({block:'center'})")
        rp.hover('.row--case')
        rp.wait_for_timeout(600)
        ok(rp.evaluate("getComputedStyle(document.querySelector('.row--case .l')).transform") == 'none', 'reduced motion: no letter roll on hover')
        ok(rp.evaluate("getComputedStyle(document.querySelector('.ftr .marquee__track')).animationName") == 'none', 'reduced motion: marquee static')
        rctx.close()

        # ---- touch: no thumbnails ----
        tctx = browser.new_context(viewport={'width': 1024, 'height': 768}, has_touch=True, is_mobile=True)
        tp = tctx.new_page()
        tp.goto(url('index'))
        tp.wait_for_load_state('networkidle')
        ok(tp.evaluate("getComputedStyle(document.querySelector('.row--case .row__thumbs')).display") == 'none', 'touch device: thumbnails hidden')
        tctx.close()
        browser.close()
    print('\n%s' % ('QA PASSED' if not fails else '%d QA FAILURE(S)' % len(fails)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
