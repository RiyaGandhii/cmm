#!/usr/bin/env python3
"""Copy, number, dash and structure checks for the built site. Stdlib only.
    python3 scripts/check.py
Exit code 1 on any failure. Prints page weights and CSS/JS sizes.
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SELF = os.path.abspath(__file__)
PAGES = ['index', 'work', 'about', 'b-roll', 'case-monthly-mix', 'case-podcast', 'case-content-engine', 'case-paid-vs-organic']
fails = []


def fail(msg):
    fails.append(msg)
    print('FAIL', msg)


def rel(p):
    return os.path.relpath(p, ROOT)


with open(os.path.join(ROOT, 'content', 'site.json'), encoding='utf-8') as f:
    SITE = json.load(f)

# ---- allowed words and numbers ----
UI_LABELS = set()
for v in SITE['ui'].values():
    if isinstance(v, list):
        UI_LABELS.update(v)
    else:
        UI_LABELS.add(v)
UI_LABELS.update(['© 2026', 'Copy', 'Copied', 'Play', 'Pause', 'Fullscreen', 'Light', 'Dark', 'Paper'])
UI_LABELS.update(SITE['about']['employers'])

ALLOWED_NUMBERS = {'49.2K', '100K', '19', '7', '1M', '4', '26', '1', '6', '17', '500K+', '3x', '14M+', '13', '73K+', '85%', '15%',
                   '38%', '1.6M+', '10.5M', '0:50', '50', '500K', '2026'}
YEARS = {str(y) for y in range(2017, 2027)}

NEVER = ['92M+', '94M', '94.5M', '80M+', '60M+', '60.7M+', '55M+', '24M+', '344%', '121,400', '84K', '845K', '80.3%', '58%', '42%',
         '74.8%', '45.9%', '75 to 97%', '1.2M+', '1.22M+', '509K+', '16.5K', '12.5M', '23,107', '27,839', 'CPV', 'earned, not bought',
         'LPA', 'salary', 'Mohak', 'Vibe', 'MBA', 'TVC', 'ATL', 'people management', 'Gurgaon', 'Zee Media', 'notice period',
         'resignation', 'agency management', 'brand tracking', 'TSYS retention']
NEVER_RE = [(t, re.compile(r'(?<![A-Za-z0-9])' + re.escape(t) + r'(?![A-Za-z0-9])', re.I if t.islower() or ' ' in t else 0)) for t in NEVER]
INSTAGRAM_RE = re.compile(r'Instagram(?! Shorts)(?! reach)')
PRESENT_RE = re.compile(r'\b[Pp]resent\b')
DERM_RE = re.compile(r'dermatolog', re.I)
DERM_OK = ['Simplified by Dermatologists and AI', 'Healthcare and dermatology']


def corpus_strings(o, out):
    if isinstance(o, dict):
        for v in o.values():
            corpus_strings(v, out)
    elif isinstance(o, list):
        for v in o:
            corpus_strings(v, out)
    elif isinstance(o, str):
        out.append(o)
    return out


CORPUS = '\n'.join(corpus_strings(SITE, []))

# ---- file scans ----
TEXT_EXT = ('.html', '.css', '.js', '.json', '.md', '.py')
files = []
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in ('.git', '.venv', '.cache', 'node_modules', 'source', 'qa')]
    for n in fn:
        if n.endswith(TEXT_EXT):
            files.append(os.path.join(dp, n))

for p in files:
    with open(p, encoding='utf-8') as f:
        txt = f.read()
    for ch, name in ((chr(0x2014), 'em dash'), (chr(0x2013), 'en dash')):
        if ch in txt:
            line = txt[:txt.index(ch)].count('\n') + 1
            fail('%s in %s line %d' % (name, rel(p), line))
    if os.path.abspath(p) == SELF:
        continue
    for t, rx in NEVER_RE:
        if rx.search(txt):
            fail('forbidden token "%s" in %s' % (t, rel(p)))
    if INSTAGRAM_RE.search(txt):
        fail('"Instagram" outside the allowed phrases in %s' % rel(p))
    if p.endswith(('.html', '.json', '.md')):
        for m in DERM_RE.finditer(txt):
            ctx = txt[max(0, m.start() - 60):m.end() + 60]
            if not any(ok in ctx for ok in DERM_OK):
                fail('"dermatolog" outside the allowed phrases in %s: ...%s...' % (rel(p), ctx.strip().replace('\n', ' ')[:90]))


# ---- HTML parsing ----
class Page(HTMLParser):
    BLOCK_SKIP = ('script', 'style', 'head', 'title', 'noscript')

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.units = []      # visible text units
        self.roll = None     # accumulating a letter-roll word
        self.imgs = []
        self.h1 = 0
        self.title = ''
        self.in_title = False
        self.meta = {}
        self.refs = []
        self.variants = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get('class') or '').split()
        self.stack.append((tag, cls))
        if tag in self.BLOCK_SKIP:
            self.skip += 1
        if tag == 'title':
            self.in_title = True
        if tag == 'h1':
            self.h1 += 1
        if tag == 'meta':
            key = a.get('name') or a.get('property')
            if key:
                self.meta[key] = a.get('content', '')
        if tag == 'img':
            self.imgs.append(a)
        for k in ('src', 'href', 'poster'):
            if a.get(k):
                self.refs.append(a[k])
        for k in ('data-src', 'data-poster'):
            if a.get(k):
                self.variants.append(a[k])
        if a.get('srcset'):
            cands = [part.strip().split(' ') for part in a['srcset'].split(',')]
            cands.sort(key=lambda c: int(c[1].rstrip('w')) if len(c) > 1 else 0)
            self.refs.append(cands[0][0])
            for c in cands[1:]:
                self.variants.append(c[0])
        if ('roll' in cls or 'swap__a' in cls or 'swap__b' in cls) and self.roll is None:
            self.roll = {'tag': tag, 'depth': len(self.stack), 'text': ''}
        if self.roll and tag == 'wbr':
            pass

    def handle_endtag(self, tag):
        if tag in self.BLOCK_SKIP:
            self.skip = max(0, self.skip - 1)
        if tag == 'title':
            self.in_title = False
        if self.roll and len(self.stack) == self.roll['depth'] and self.stack and self.stack[-1][0] == tag:
            self.units.append(self.roll['text'])
            self.roll = None
        if self.stack:
            # tolerate void elements left on the stack
            while self.stack and self.stack[-1][0] != tag and self.stack[-1][0] in ('img', 'br', 'wbr', 'meta', 'link', 'input', 'source', 'path', 'rect', 'line', 'circle'):
                self.stack.pop()
            if self.stack and self.stack[-1][0] == tag:
                self.stack.pop()

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.stack.pop()

    def handle_data(self, data):
        if self.in_title:
            self.title += data
            return
        if self.skip:
            return
        if self.roll is not None:
            self.roll['text'] += data
            return
        t = data.strip()
        if t:
            self.units.append(data)


STRIP = ' \t\n[]→↗↓←×✱·©:'
COUNTER = re.compile(r'^(\d{2,3}|\d+/\d+)$')


def norm(u):
    u = re.sub(r'\s+', ' ', u.replace('\xa0', ' ')).strip()
    return u.strip(STRIP).strip()


def check_text(name, units):
    bad = []
    for u in units:
        n = norm(u)
        if not n or n in UI_LABELS or COUNTER.match(n) or n in ('2026', '© 2026'):
            continue
        # a unit may carry a trailing bracket label or arrow next to copy
        if n in CORPUS:
            continue
        pieces = [norm(x) for x in re.split(r'[\[\]·]', u)]
        if all((not p) or p in CORPUS or p in UI_LABELS or COUNTER.match(p) for p in pieces):
            continue
        words = n.split(' ')
        if len(set(words)) == 1 and words[0] in CORPUS:
            continue
        bad.append(n)
    for b in sorted(set(bad)):
        fail('%s.html: visible text not in site.json: "%s"' % (name, b[:120]))


def check_numbers(name, units):
    bad = set()
    for u in units:
        for word in re.split(r'[\s\(\)\[\]“”",;]+', u.replace('\xa0', ' ')):
            for tok in word.split('-'):
                tok = tok.strip('.,:;!?)(“”"\'')
                if not tok or not tok[0].isdigit():
                    continue
                if tok in ALLOWED_NUMBERS or tok in YEARS or COUNTER.match(tok):
                    continue
                bad.add(tok)
    for b in sorted(bad):
        fail('%s.html: numeric token not allowed: "%s"' % (name, b))


def check_present(name, units):
    for u in units:
        if PRESENT_RE.search(u):
            fail('%s.html: "present" used as a date: "%s"' % (name, norm(u)[:80]))


def local_path(ref):
    if re.match(r'^(https?:|mailto:|tel:|#|data:)', ref):
        return None
    return os.path.join(ROOT, ref.split('#')[0].split('?')[0])


def size_of(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def check_page(name):
    path = os.path.join(ROOT, name + '.html')
    if not os.path.exists(path):
        fail('missing page %s.html' % name)
        return
    with open(path, encoding='utf-8') as f:
        html = f.read()
    pg = Page()
    pg.feed(html)
    if pg.h1 != 1:
        fail('%s.html has %d h1 elements' % (name, pg.h1))
    if not pg.title.strip():
        fail('%s.html has no title' % name)
    if not pg.meta.get('description'):
        fail('%s.html has no meta description' % name)
    for og in ('og:title', 'og:description', 'og:image', 'og:type'):
        if not pg.meta.get(og):
            fail('%s.html lacks %s' % (name, og))
    for a in pg.imgs:
        for req in ('alt', 'width', 'height'):
            if req not in a or (req != 'alt' and not a[req]):
                fail('%s.html: img %s without %s' % (name, a.get('src', '?'), req))
    weight = size_of(path)
    seen = set()
    for r in pg.refs:
        lp = local_path(r)
        if lp is None:
            continue
        if not os.path.exists(lp):
            fail('%s.html references a missing file: %s' % (name, r))
        elif lp not in seen and not lp.endswith('.mp4'):
            seen.add(lp)
            weight += size_of(lp)
    extra = 0
    for r in pg.variants:
        lp = local_path(r)
        if lp and not os.path.exists(lp):
            fail('%s.html references a missing file: %s' % (name, r))
        elif lp and lp not in seen and not lp.endswith(".mp4"):
            seen.add(lp)
            extra += size_of(lp)
    check_text(name, pg.units)
    check_numbers(name, pg.units)
    check_present(name, pg.units)
    if weight > 1024 * 1024:
        fail('%s.html weighs %d KB (over 1 MB excluding video)' % (name, weight // 1024))
    print('%-26s %4d KB at 1x (html %d KB, %d files, video excluded); %d KB with every srcset variant' % (name + '.html', weight // 1024, size_of(path) // 1024, len(seen), (weight + extra) // 1024))


for name in PAGES:
    check_page(name)

css = size_of(os.path.join(ROOT, 'assets', 'css', 'styles.css'))
js = size_of(os.path.join(ROOT, 'assets', 'js', 'main.js'))
print('CSS %d bytes (%.1f KB), JS %d bytes (%.1f KB)' % (css, css / 1024, js, js / 1024))
if css > 45 * 1024:
    fail('CSS over 45 KB')
if js > 20 * 1024:
    fail('JS over 20 KB')
for req in ('assets/og-image.jpg', 'assets/favicon.svg', 'assets/Riya_Gandhi_Resume.pdf', 'assets/video/studio-pan.mp4', 'assets/video/studio-pan-poster.webp'):
    if not os.path.exists(os.path.join(ROOT, req)):
        fail('missing asset %s' % req)
og = size_of(os.path.join(ROOT, 'assets', 'og-image.jpg'))
if og > 200 * 1024:
    fail('og-image.jpg is %d KB (over 200 KB)' % (og // 1024))
mp4 = size_of(os.path.join(ROOT, 'assets', 'video', 'studio-pan.mp4'))
if mp4 > 4 * 1024 * 1024:
    fail('studio-pan.mp4 is %d KB (over 4 MB)' % (mp4 // 1024))

print('\n%s' % ('ALL CHECKS PASSED' if not fails else '%d FAILURE(S)' % len(fails)))
sys.exit(1 if fails else 0)
