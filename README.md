# Riya Gandhi, portfolio

Plain HTML, CSS and classic JavaScript. No frameworks, no bundler, no runtime dependencies.

## Open it

Double-click `index.html`. Every page is a static file with relative links, so it works from the folder as well as from any static host.

## Edit copy

All copy lives in `content/site.json`. Every page is rendered from it:

```bash
python3 scripts/build.py
```

That rewrites `index.html`, `work.html`, `about.html`, `b-roll.html` and the four `case-*.html` pages from `templates/`. Commit the built HTML.

To add the podcast episode embed, paste the YouTube URL into `cases[1].evidence[0].episodeUrl` in `content/site.json` and rebuild. The slide becomes a click-to-load player (youtube-nocookie).

## Checks

```bash
python3 scripts/check.py
```

Fails on em or en dashes, forbidden tokens, visible text that is not in `site.json`, numbers outside the allowed list, missing files, images without alt, width or height, and pages without exactly one h1, a title, a description and Open Graph tags. Prints page weights.

Browser checks need the project-local venv (Playwright is installed there, browsers under `.cache/pw`):

```bash
PLAYWRIGHT_BROWSERS_PATH=.cache/pw .venv/bin/python scripts/shots.py
```

```bash
PLAYWRIGHT_BROWSERS_PATH=.cache/pw .venv/bin/python scripts/qa.py
```

`shots.py` saves every page at 390, 768, 1366 and 1440 px (plus Dark, Paper and reduced-motion variants) into `qa/shots/`, checks for horizontal scroll and console errors, and measures the home hero. `qa.py` walks the menu, the About panel, galleries, the lightbox, the copy button, the marquee control, the mood toggle and the hover states by keyboard.

## Assets

`scripts/assets.py` rebuilds every image, the compressed studio video, its poster and the video frames from `source/` into `assets/`. `scripts/og.py` renders `assets/og-image.jpg`. Both run inside the venv.

## Layout

```
content/site.json      locked copy, numbers, links, alt text
templates/             page skeleton and shared partials
scripts/               build.py, check.py, shots.py, qa.py, assets.py, og.py
assets/css/styles.css  the design system (moods, type scale, motion)
assets/js/main.js      moods, overlays, reveal, typing, galleries, media
assets/img, video      WebP photos and frames, the MP4 and its poster
qa/reference           screenshots of the reference site
qa/shots               generated screenshots and summary.json
source/                original inputs (never served)
```
