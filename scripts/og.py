#!/usr/bin/env python3
"""Render assets/og-image.jpg (1200 x 630, Light mood) with Playwright.
Inter is loaded from Google Fonts inside the page, so no font file is stored.
    PLAYWRIGHT_BROWSERS_PATH=.cache/pw .venv/bin/python scripts/og.py
"""
import base64
import json
import os

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'content', 'site.json'), encoding='utf-8') as f:
    S = json.load(f)
share = S['seo']['shareImage']
with open(os.path.join(ROOT, 'assets', 'img', 'hero-800.webp'), 'rb') as f:
    hero = 'data:image/webp;base64,' + base64.b64encode(f.read()).decode('ascii')
HTML = """<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400..700&display=block">
<style>
html,body{margin:0;width:1200px;height:630px;background:#FFFFFF;color:#0B0B0B;font-family:Inter,Arial,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{display:grid;grid-template-columns:1fr 420px;height:630px}
.txt{padding:72px 0 72px 72px;display:flex;flex-direction:column;justify-content:space-between}
.role{font-size:70px;line-height:.98;letter-spacing:-.045em;font-weight:400;max-width:9ch}
.name{font-size:30px;font-weight:600;letter-spacing:-.02em}
.tag{font-size:20px;color:#6B6B6B;font-variant-numeric:tabular-nums}
.pic{width:420px;height:630px;object-fit:cover;object-position:50%% 20%%}
</style></head><body><div class="wrap"><div class="txt"><div class="tag">[%s]</div><div class="role">%s</div><div class="name">%s</div></div><img class="pic" src="%s"></div></body></html>"""


def main():
    html = HTML % (S['identity']['location'], share['line1'], share['line2'], hero)
    out = os.path.join(ROOT, 'assets', 'og-image.jpg')
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        p = b.new_page(viewport={'width': 1200, 'height': 630}, device_scale_factor=1)
        p.set_content(html)
        p.wait_for_load_state('networkidle')
        p.evaluate('document.fonts.ready')
        p.wait_for_timeout(500)
        q = 82
        while True:
            p.screenshot(path=out, type='jpeg', quality=q)
            if os.path.getsize(out) < 200 * 1024 or q <= 40:
                break
            q -= 6
        b.close()
    print('og-image.jpg', os.path.getsize(out) // 1024, 'KB, quality', q)


if __name__ == '__main__':
    main()
