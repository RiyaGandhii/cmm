#!/usr/bin/env python3
"""Render every page of the portfolio from content/site.json and templates/.
Python 3 standard library only. Run from anywhere:
    python3 scripts/build.py
Writes index.html, work.html, about.html, b-roll.html and the four case pages
into the project root.
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, 'templates')
with open(os.path.join(ROOT, 'content', 'site.json'), encoding='utf-8') as f:
    S = json.load(f)
UI = S['ui']
C = S['contact']


def esc(t):
    return html.escape(str(t), quote=True)


def tpl(name):
    with open(os.path.join(TPL, name), encoding='utf-8') as f:
        return f.read()


def fill(t, **kw):
    for k, v in kw.items():
        t = t.replace('{{' + k + '}}', v)
    left = re.findall(r'{{\w+}}', t)
    if left:
        raise SystemExit('unfilled placeholders: ' + ', '.join(left))
    return t


def img_size(name):
    """Pixel size of a WebP in assets/img by reading its header."""
    path = os.path.join(ROOT, 'assets', 'img', name + '.webp')
    with open(path, 'rb') as f:
        head = f.read(40)
    if head[12:16] == b'VP8X':
        w = 1 + int.from_bytes(head[24:27], 'little')
        h = 1 + int.from_bytes(head[27:30], 'little')
    elif head[12:16] == b'VP8L':
        b = head[21:25]
        w = 1 + (((b[1] & 0x3F) << 8) | b[0])
        h = 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
    else:
        w = int.from_bytes(head[26:28], 'little') & 0x3FFF
        h = int.from_bytes(head[28:30], 'little') & 0x3FFF
    return w, h


def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, wa):
    ra, rb = hex_rgb(a), hex_rgb(b)
    return '#%02X%02X%02X' % tuple(round(ra[i] * wa + rb[i] * (1 - wa)) for i in range(3))


# ---------- atoms ----------

def roll(text, hidden=True):
    """Letter-roll markup: each letter an inline-block span with a stagger index."""
    out, k = [], 0
    for wi, word in enumerate(text.split(' ')):
        if wi:
            out.append(' ')
            k += 1
        letters = ''.join('<span class="l" style="--k:%d">%s</span>' % (k + i, esc(ch)) for i, ch in enumerate(word))
        k += len(word)
        out.append('<span class="w">%s</span>' % letters)
    ah = ' aria-hidden="true"' if hidden else ''
    return '<span class="roll"%s>%s</span>' % (ah, ''.join(out))


def swap(a, b):
    def line(t, cls):
        return '<span class="%s">%s</span>' % (cls, ''.join(
            '<span class="l" style="--k:%d">%s</span>' % (i, '&nbsp;' if ch == ' ' else esc(ch)) for i, ch in enumerate(t)))
    return '<span class="swap" aria-hidden="true">%s%s</span>' % (line(a, 'swap__a'), line(b, 'swap__b'))


def btag(label, href, arrow='', external=False, download=False, cls=''):
    attrs = ' target="_blank" rel="noopener"' if external else ''
    if download:
        attrs += ' download'
    a = ' <span aria-hidden="true">%s</span>' % arrow if arrow else ''
    return '<a class="btag %s" href="%s"%s>[%s]%s</a>' % (cls, esc(href), attrs, esc(label), a)


def link_for(key):
    return {'linkedin': (C['linkedin'], True, False), 'youtube': (C['youtube'], True, False),
            'whatsapp': (C['whatsapp'], True, False), 'email': ('mailto:' + C['email'], False, False),
            'resume': ('assets/' + C['resumeFile'], False, True)}[key]


def pic(name, alt, widths, sizes, cls='', loading='lazy', priority=False, extra=''):
    w, h = img_size('%s-%d' % (name, widths[0]))
    srcset = ', '.join('assets/img/%s-%d.webp %dw' % (name, x, img_size('%s-%d' % (name, x))[0]) for x in widths)
    attrs = ' fetchpriority="high"' if priority else ' loading="%s"' % loading
    return ('<img class="%s" src="assets/img/%s-%d.webp" srcset="%s" sizes="%s" width="%d" height="%d" alt="%s" decoding="async"%s%s>'
            % (cls, name, widths[0], srcset, sizes, w, h, esc(alt), attrs, extra))


def underline_svg():
    return ('<svg viewBox="0 0 100 12" preserveAspectRatio="none" aria-hidden="true"><path d="M2 8.5C18 4 34 10 50 6.5S84 4.5 98 7.5" '
            'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" vector-effect="non-scaling-stroke"/></svg>')


def row(number, name, href=None, tags=None, result=None, hook=None, thumbs='', aria=None, size='', arrow=None,
        external=False, sr=None, reveal=True, delay=0, cls='', tag_arrow=None):
    tag_html = ''
    if tags or result or hook or thumbs:
        parts = ''
        for t in (tags or []):
            parts += '<span class="row__tag tag">[%s]</span>' % esc(t)
        if result:
            parts += '<span class="row__result tag">[%s]</span>' % esc(result)
        if hook or thumbs:
            parts += '<span class="row__visual"><span class="row__thumbs">%s</span><span class="row__hook tag">%s</span></span>' % (thumbs, esc(hook or ''))
        tag_html = '<span class="row__meta" aria-hidden="true">%s</span>' % parts
    arrow_html = ' <span class="row__arrow" aria-hidden="true">%s</span>' % arrow if arrow else ''
    if tag_arrow:
        arrow_html = '<span class="row__tagarrow tag" aria-hidden="true">%s</span>' % tag_arrow
    sr_html = '<span class="vh">%s</span>' % esc(sr) if sr else ''
    n_html = '<span class="row__n tag" aria-hidden="true">[%s]</span>' % number if number is not None else ''
    inner = '%s%s<span class="row__name">%s</span>%s%s' % (sr_html, n_html, roll(name), tag_html, arrow_html)
    rv = ' data-reveal style="--d:%dms"' % delay if reveal else ''
    classes = ('row %s %s' % (size, cls)).strip()
    if href:
        ext = ' target="_blank" rel="noopener"' if external else ''
        al = ' aria-label="%s"' % esc(aria) if aria else ''
        return '<a class="%s" href="%s"%s%s%s>%s</a>' % (classes, esc(href), ext, al, rv, inner)
    return '<div class="%s"%s>%s</div>' % (classes, rv, inner)


# ---------- thumbnails and figures (SVG) ----------

def thumb_svg_chart(c):
    bg, ink = c['colours']['bg'], c['colours']['ink']
    ev = c['evidence'][0]
    before = ev['before']['items'][0]['value']
    after = [i['value'] for i in ev['after']['items']]
    mx = max([before] + after)
    def bar(x, v, w):
        h = 74 * v / mx
        return '<rect x="%d" y="%.1f" width="%d" height="%.1f" fill="%s"/>' % (x, 100 - h, w, h, ink)
    bars = bar(22, before, 22) + ''.join(bar(72 + i * 26, v, 22) for i, v in enumerate(after))
    return ('<svg viewBox="0 0 160 120" role="img" aria-label="%s"><rect width="160" height="120" fill="%s"/>%s'
            '<line x1="14" y1="100.5" x2="146" y2="100.5" stroke="%s" stroke-opacity=".5"/></svg>' % (esc(c['thumbs'][0]['alt']), bg, bars, ink))


def thumb_svg_bar(c):
    bg, ink = c['colours']['bg'], c['colours']['ink']
    return ('<svg viewBox="0 0 160 120" role="img" aria-label="%s"><rect width="160" height="120" fill="%s"/>'
            '<rect x="16" y="46" width="128" height="28" fill="none" stroke="%s" stroke-width="2"/>'
            '<rect x="16" y="46" width="108.8" height="28" fill="%s"/></svg>' % (esc(c['thumbs'][0]['alt']), bg, ink, ink))


def thumb_svg_card(c):
    bg, ink = c['colours']['bg'], c['colours']['ink']
    return ('<svg viewBox="0 0 160 120" role="img" aria-label="%s"><rect width="160" height="120" fill="%s"/>'
            '<text x="14" y="62" font-size="34" font-weight="500" letter-spacing="-1.5" fill="%s" font-family="Inter, Arial, sans-serif">About 3x</text>'
            '<text x="14" y="86" font-size="9" fill="%s" font-family="Inter, Arial, sans-serif">YouTube-referred store sessions,</text>'
            '<text x="14" y="98" font-size="9" fill="%s" font-family="Inter, Arial, sans-serif">year on year</text></svg>'
            % (esc(c['thumbs'][1]['alt']), bg, ink, ink, ink))


def thumbs_for(c):
    out = ''
    for t in c['thumbs']:
        if t['type'] == 'image':
            w, h = img_size(t['src'] + '-320')
            inner = '<img src="assets/img/%s-320.webp" width="%d" height="%d" alt="%s" loading="lazy" decoding="async">' % (t['src'], w, h, esc(t['alt']))
        elif t['type'] == 'svg-chart':
            inner = thumb_svg_chart(c)
        elif t['type'] == 'svg-bar':
            inner = thumb_svg_bar(c)
        else:
            inner = thumb_svg_card(c)
        out += '<span class="thumb"><span class="thumb__in">%s</span></span>' % inner
    return out


def fig_chart(ev):
    """Horizontal bars: before and after, labels from the locked copy."""
    rows = [(ev['before']['label'], ev['before']['items']), (ev['after']['label'], ev['after']['items'])]
    mx = max(i['value'] for _, items in rows for i in items)
    y, out = 46, []
    for label, items in rows:
        out.append('<text x="0" y="%d" font-size="15" opacity=".7">%s</text>' % (y - 14, esc(label)))
        for it in items:
            w = 360 * it['value'] / mx
            out.append('<rect x="0" y="%d" width="%.1f" height="22" fill="currentColor"/>' % (y, max(w, 6)))
            out.append('<text x="%.1f" y="%d" font-size="15">%s</text>' % (max(w, 6) + 12, y + 16, esc(it['label'])))
            y += 32
        y += 34
    return ('<figure class="panelbox chart"><span class="tag">[%s]</span><svg viewBox="0 0 560 %d" role="img" aria-label="%s">%s</svg></figure>'
            % (esc(ev['title']), y - 20, esc(ev['title']), ''.join(out)))


def fig_flow(ev):
    steps = ev['steps']
    out, boxes = [], []
    bw, bh, gx, gy = 120, 44, 24, 64
    for i, s in enumerate(steps):
        r, col = divmod(i, 4)
        x, yy = col * (bw + gx), 20 + r * (bh + gy)
        boxes.append((x, yy))
        out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"/>' % (x, yy, bw, bh))
        out.append('<text x="%d" y="%d" font-size="14" text-anchor="middle">%s</text>' % (x + bw / 2, yy + 27, esc(s)))
        if i < len(steps) - 1:
            if col < 3:
                out.append('<path d="M%d %dh%d" stroke="currentColor" stroke-width="1.5" marker-end="url(#ah)"/>' % (x + bw, yy + bh / 2, gx - 8))
            else:
                nx, ny = boxes[0][0] + bw / 2, yy + bh + gy
                out.append('<path d="M%d %dv%dH%.0fV%d" fill="none" stroke="currentColor" stroke-width="1.5" marker-end="url(#ah)"/>'
                           % (x + bw / 2, yy + bh, gy / 2, nx, ny - 8))
    lx, ly = boxes[-1][0] + bw / 2, boxes[-1][1] + bh
    py = boxes[0][1] + bh / 2
    out.append('<path d="M%d %dv24H-22V%dH-10" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 4" marker-end="url(#ah)"/>'
               % (lx, ly, py))
    out.append('<text x="%d" y="%d" font-size="13" opacity=".7">%s</text>' % (lx - bw / 2, ly + 42, esc(ev['loop'])))
    defs = '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="currentColor"/></marker></defs>'
    return ('<figure class="panelbox chart"><span class="tag">[%s]</span><svg viewBox="-30 0 590 %d" role="img" aria-label="%s">%s%s</svg></figure>'
            % (esc(ev['title']), ly + 56, esc(' → '.join(steps) + ' → ' + ev['loop']), defs, ''.join(out)))


def fig_lanes(ev):
    out = []
    defs = '<defs><marker id="ah2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="currentColor"/></marker></defs>'
    def lane(y, lane_data, dashed=False):
        steps = lane_data['steps']
        out.append('<text x="0" y="%d" font-size="14" opacity=".7">%s</text>' % (y - 12, esc(lane_data['label'])))
        n = len(steps)
        bw = (560 - (n - 1) * 20) / n
        for i, s in enumerate(steps):
            x = i * (bw + 20)
            out.append('<rect x="%.1f" y="%d" width="%.1f" height="40" rx="2" fill="none" stroke="currentColor" stroke-width="1.5"%s/>'
                       % (x, y, bw, ' stroke-dasharray="5 4"' if dashed else ''))
            out.append('<text x="%.1f" y="%d" font-size="14" text-anchor="middle">%s</text>' % (x + bw / 2, y + 25, esc(s)))
            if i < n - 1:
                out.append('<path d="M%.1f %dh10" stroke="currentColor" stroke-width="1.5" marker-end="url(#ah2)"/>' % (x + bw, y + 20))
        return bw
    bw = lane(30, ev['before'], dashed=True)
    nx = bw * 2 + 40 - 6
    out.append('<path d="M%.1f 104v-26" fill="none" stroke="currentColor" stroke-width="1.5" marker-end="url(#ah2)"/>' % nx)
    out.append('<text x="%.1f" y="122" font-size="13" text-anchor="middle">%s <tspan>%s</tspan></text>' % (nx, esc(ev['before']['note']), esc(ev['before']['noteAt'])))
    lane(170, ev['after'])
    label = '%s: %s. %s: %s. %s %s.' % (ev['before']['label'], ' → '.join(ev['before']['steps']), ev['after']['label'],
                                           ' → '.join(ev['after']['steps']), ev['before']['note'], ev['before']['noteAt'])
    return ('<figure class="panelbox chart"><span class="tag">[%s]</span><svg viewBox="-2 0 564 224" role="img" aria-label="%s">%s%s</svg>'
            '<figcaption class="tag muted">[%s]</figcaption></figure>' % (esc(ev['title']), esc(label), defs, ''.join(out), esc(ev['caption'])))


def fig_bar(ev):
    paid, org = ev['segments']
    pv = float(paid['value'].rstrip('%'))
    return ('<figure class="panelbox single"><span class="tag">[%s]</span>'
            '<svg class="bar-fig" viewBox="0 0 1000 120" role="img" aria-label="%s %s, %s %s" width="1000" height="120" style="width:100%%;height:auto">'
            '<rect x="0" y="20" width="1000" height="56" fill="none" stroke="currentColor" stroke-width="2"/>'
            '<rect x="0" y="20" width="%d" height="56" fill="currentColor"/>'
            '<text x="0" y="110" font-size="18" fill="currentColor" font-family="Inter, Arial, sans-serif">%s %s</text>'
            '<text x="1000" y="110" font-size="18" fill="currentColor" text-anchor="end" font-family="Inter, Arial, sans-serif">%s %s</text></svg>'
            '<figcaption class="tag muted">[%s]</figcaption></figure>'
            % (esc(ev['label']), esc(paid['label']), esc(paid['value']), esc(org['label']), esc(org['value']), int(1000 * pv / 100),
               esc(paid['label']), esc(paid['value']), esc(org['label']), esc(org['value']), esc(ev['caption'])))


def impact_number(n):
    if len(n) <= 14:
        return '<span class="nb">%s</span>' % esc(n)
    return ' '.join('<span class="nb">%s</span>' % esc(t) if re.search(r'\d', t) else esc(t) for t in n.split(' '))


def fig_card(ev):
    return ('<div class="panelbox card"><span class="tag">[%s]</span><ul>%s</ul></div>'
            % (esc(ev['title']), ''.join('<li>%s</li>' % esc(l) for l in ev['lines'])))


def yt_id(url):
    m = re.search(r'(?:v=|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})', url or '')
    return m.group(1) if m else ''


MISSING = []


def fig_episode(ev):
    vid = yt_id(ev.get('episodeUrl', ''))
    if vid:
        body = ('<button class="yt" type="button" data-yt="%s" data-title="%s"><img src="https://i.ytimg.com/vi/%s/hqdefault.jpg" width="480" height="360" alt="%s" loading="lazy" decoding="async">'
                '<span class="tag">[Play]</span></button>' % (vid, esc(ev['title']), vid, esc(ev['title'])))
    else:
        MISSING.append('Episode link for “%s” (episodeUrl is empty); the slide links to the YouTube channel instead.' % ev['title'])
        body = ('<a class="panelbox card" href="%s" target="_blank" rel="noopener"><span class="tag">[Play] <span aria-hidden="true">↗</span></span><span>%s</span></a>'
                % (esc(C['youtube']), esc(ev['title'])))
    return '%s<figcaption class="tag">[%s]</figcaption>' % (body, esc(ev['caption']))


def fig_link(ev):
    url, ext, _ = link_for(ev['key'])
    return ('<a class="panelbox card" href="%s" target="_blank" rel="noopener"><span class="tag"><span aria-hidden="true">↗</span></span><span>%s</span>'
            '<span class="tag" style="margin-top:var(--s3)">%s</span></a>' % (esc(url), esc(ev['text']), esc(ev['display'])))


def gallery(slides, media=False):
    n = len(slides)
    body = ''.join('<figure class="gal__slide">%s</figure>' % s for s in slides)
    return ('<section class="gal%s" aria-roledescription="carousel"><div class="gal__bar"><span class="gal__count tag" aria-live="polite">[1/%d]</span>'
            '<div class="gal__nav"><button class="gal__btn" type="button" data-prev><span aria-hidden="true">←</span><span class="vh">←</span></button>'
            '<button class="gal__btn" type="button" data-next><span aria-hidden="true">→</span><span class="vh">→</span></button></div></div>'
            '<div class="gal__track" tabindex="0">%s</div></section>' % (' gal--media' if media else '', n, body))


# ---------- shared chrome ----------

def header():
    return fill(tpl('partials/header.html'), wordmark=UI['wordmark'], about_me=UI['aboutMe'],
                swap=swap(S['home']['hero']['role'], UI['aboutMe']), menu_label=UI['menu'], contact=UI['contact'])


def panel():
    emp = ' · '.join(S['about']['employers']) + ' · '
    return fill(tpl('partials/panel.html'), wordmark=UI['wordmark'], about_me=UI['aboutMe'], close=UI['close'],
                bio=esc(S['about']['shortBio']), read=UI['readFullStory'], employers=esc(emp))


def menu():
    rows = ''.join(row('%02d' % (i + 1), m['label'], m['href'], reveal=False) for i, m in enumerate(S['menu']))
    links = ''
    for m in S['menuBottom']:
        url, ext, dl = link_for(m['key'])
        links += btag(m['label'], url, '↗' if ext else '', external=ext)
    return fill(tpl('partials/menu.html'), wordmark=UI['wordmark'], close=UI['close'], menu_label=UI['menu'], rows=rows, links=links)


def bar():
    return fill(tpl('partials/bar.html'), change_mood=UI['changeMood'], mood=UI['mood'])


def sayhi():
    sh = S['sayHi']
    email = C['email']
    email_roll = roll(email.replace('@', '@​'))
    email_roll = email_roll.replace('​', '<wbr>')
    pills = ''
    for p in sh['pills']:
        url, ext, dl = link_for(p['key'])
        pills += btag(p['label'], url, '↓' if dl else '↗', external=ext, download=dl)
    return fill(tpl('partials/sayhi.html'), kicker=esc(sh['kicker']), email=esc(email), email_roll=email_roll, pills=pills)


def footer():
    f = S['footer']
    labels = f['columnLabels']
    pages = [(m['label'], m['href'], False) for m in S['menu'][:3]]
    cases = [(m['label'], m['href'], False) for m in S['menu'][3:]]
    elsewhere = []
    for m in S['menuBottom']:
        url, ext, dl = link_for(m['key'])
        elsewhere.append((m['label'], url, ext))
    cols = ''
    for lab, items in zip(labels, (pages, cases, elsewhere)):
        lis = ''.join('<li><a href="%s"%s>%s%s</a></li>' % (esc(h), ' target="_blank" rel="noopener"' if ext else '', esc(t),
                                                            ' <span aria-hidden="true">↗</span>' if ext else '') for t, h, ext in items)
        cols += '<div><span class="tag muted">[%s]</span><ul>%s</ul></div>' % (esc(lab), lis)
    return fill(tpl('partials/footer.html'), marquee=esc(f['marquee']), cols=cols, legal=esc(f['legal']))


def page(key, main, html_class='', html_style='', theme='#FFFFFF', jsonld='', extra=''):
    seo = S['seo'][key]
    return fill(tpl('base.html'), title=esc(seo['title']), description=esc(seo['description']), theme=theme,
                html_class=html_class, html_style=html_style, jsonld=jsonld, header=header(), main=main,
                footer=sayhi() + footer(), bar=bar(), veil='<div class="veil"></div>', panel=panel(), menu=menu(), extra=extra)


def case_index(prefix=''):
    rows = ''.join(row(c['number'], c['menuLabel'], c['id'] + '.html', tags=[c['tagsLine']], result=c['resultLine'], hook=c['hook'],
                       thumbs=thumbs_for(c), aria=c['accessibleName'], cls='row--case', delay=i * 40) for i, c in enumerate(S['cases']))
    return '<div class="index">%s</div>' % rows


# ---------- pages ----------

def brand_cell(i, b, total):
    """One logo cell. Uses assets/logos/<slug>.(svg|png|webp) when present, else a typeset wordmark."""
    logo = ''
    for ext in ('svg', 'png', 'webp'):
        path = os.path.join(ROOT, 'assets', 'logos', b['slug'] + '.' + ext)
        if os.path.exists(path):
            wd, ht = (160, 56)
            if ext == 'png':
                with open(path, 'rb') as f:
                    hd = f.read(24)
                wd, ht = int.from_bytes(hd[16:20], 'big'), int.from_bytes(hd[20:24], 'big')
            logo = ('<img class="brand__logo" src="assets/logos/%s.%s" alt="%s" width="%d" height="%d" loading="lazy" decoding="async">'
                    % (b['slug'], ext, esc(b['name']), wd, ht))
            break
    if not logo:
        head, _, tail = b['name'].partition(' ')
        logo = '<span class="brand brand--%s"><b>%s</b>%s</span>' % (b['slug'], esc(head), ('<span>%s</span>' % esc(tail)) if tail else '')
        logo = '<span class="vh">%s</span><span aria-hidden="true">%s</span>' % (esc(b['name']), logo)
    return ('<li class="brands__cell" data-reveal style="--d:%dms"><span class="tag muted" aria-hidden="true">[%02d]</span>%s</li>'
            % (i * 60, i + 1, logo))


def brands_section():
    br = S['home']['brands']
    cells = ''.join(brand_cell(i, b, len(br['items'])) for i, b in enumerate(br['items']))
    return ('<section class="sec wrap brands" aria-labelledby="brands-k"><span class="kicker tag" id="brands-k">[%s]</span>'
            '<ul class="brands__grid">%s</ul></section>' % (esc(br['heading']), cells))


def build_index():
    h = S['home']['hero']
    hero = ('<section class="hero wrap" aria-labelledby="h1">'
            '<h1 id="h1" class="vh">%s</h1>'
            '<div class="hero__txt">'
            '<p class="hero__name big row" aria-hidden="true" data-reveal>%s</p>'
            '<p class="hero__role big" aria-hidden="true" data-reveal style="--d:40ms">%s</p>'
            '<p class="hero__sub lead" data-reveal style="--d:80ms">%s</p>'
            '<p class="hero__proof muted" data-reveal style="--d:120ms">%s</p>'
            '<div class="hero__btns tag" data-reveal style="--d:160ms">%s%s</div>'
            '</div>'
            '<div class="hero__pic pic" data-reveal>%s<div class="badge" aria-hidden="true"><svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="50"/>'
            '<defs><path id="bp" d="M50 50m-36 0a36 36 0 1 1 72 0a36 36 0 1 1-72 0"/></defs><text><textPath href="#bp">%s</textPath></text></svg></div></div>'
            '</section>') % (
        esc(h['hiddenHeading']), roll(h['nameLine'], hidden=False), esc(h['role']), esc(h['subLine']), esc(h['proofLine']),
        btag(h['buttons'][0], 'work.html', '→'), btag(h['buttons'][1], 'assets/' + C['resumeFile'], '↓', download=True),
        pic('hero', S['images']['hero']['alt'], [800, 1600], '(min-width: 1024px) 40vw, 86vw', priority=True),
        esc(h['badge']))
    pq = S['home']['pullQuote']
    pull = ('<section class="pull wrap"><p class="mega big"><span class="type" data-type>%s</span></p><span class="tag">[%s]</span></section>'
            % (esc(pq['quote']), esc(pq['caption'])))
    w = S['home']['whoIAm']
    skills = ''.join(row('%02d' % (i + 1), s, size='row--s', sr=s, delay=i * 40) for i, s in enumerate(w['skills']))
    who = ('<section class="sec wrap"><div class="two"><h2 class="rowsize big" data-reveal>%s</h2>'
           '<div><p class="lead" data-reveal>%s</p><div class="links tag">%s%s</div></div></div>'
           '<div class="index index--left" style="margin-top:var(--s8)">%s</div></section>'
           % (esc(w['statement']), esc(w['paragraph']), btag(w['buttons'][0], 'work.html', '→'), btag(w['buttons'][1], '#say-hi', '→'), skills))
    work = ('<section class="sec wrap" aria-labelledby="work-k"><span class="kicker tag" id="work-k">[%s]</span>%s</section>'
            % (esc(S['home']['workStripHeading']), case_index()))
    sp = S['seo']['searchProfile']
    work += brands_section()
    ld = {"@context": "https://schema.org", "@type": "Person", "name": sp['name'], "jobTitle": sp['jobTitle'],
          "address": {"@type": "PostalAddress", "addressLocality": sp['addressLocality'], "addressCountry": sp['addressCountry']},
          "alumniOf": [{"@type": "CollegeOrUniversity", "name": n} for n in sp['alumniOf']],
          "sameAs": sp['sameAs'], "email": "mailto:" + C['email'], "image": "assets/og-image.jpg"}
    jsonld = '<script type="application/ld+json">%s</script>' % json.dumps(ld, ensure_ascii=False)
    return page('index', hero + pull + who + work, jsonld=jsonld)


def build_work():
    w = S['work']
    stay = ' '.join([w['backgroundWord']] * 8) + ' '
    head = ('<section class="workhead wrap"><div class="marquee outline mega big" aria-hidden="true"><div class="marquee__track"><span>%s</span><span>%s</span></div></div>'
            '<h1 class="mega big" data-reveal>%s</h1><span class="tag">[%s]</span></section>' % (esc(stay), esc(stay), esc(w['heading']), esc(w['line'])))
    idx = '<section class="sec--tight wrap">%s</section>' % case_index()
    ip = w['inPrint']
    arts = ''.join(row('%02d' % (i + 1), a['title'], a['url'], tags=[ip['source']], size='row--s', external=True, delay=i * 40,
                       aria=a['title'], tag_arrow='↗') for i, a in enumerate(ip['articles']))
    print_sec = ('<section class="sec wrap" aria-labelledby="ip-k"><span class="kicker tag" id="ip-k">[%s] <span class="muted">%s</span></span>'
                 '<div class="index index--left">%s</div><p class="tag" style="margin-top:var(--s8)">%s</p></section>'
                 % (esc(ip['heading']), esc(ip['line']), arts, btag(w['endLink'], 'about.html')))
    return page('work', head + idx + print_sec)


def build_case(c, i):
    nxt = S['cases'][(i + 1) % len(S['cases'])]
    L = S['caseLabels']
    bg, ink = c['colours']['bg'], c['colours']['ink']
    muted = mix(ink, bg, 0.7)
    r, g, b = hex_rgb(ink)
    style = '--case-bg:%s;--case-ink:%s;--case-muted:%s;--case-line:rgba(%d,%d,%d,.18);--case-panel:%s' % (bg, ink, muted, r, g, b, mix(bg, '#FFFFFF', 0.88))
    # title with the handwritten accent word
    words = []
    for wd in c['title'].split(' '):
        if c['accentWord'] in wd:
            a, b = wd.split(c['accentWord'], 1)
            words.append('<span class="nb">%s<span class="hand">%s%s</span>%s</span>' % (esc(a), esc(c['accentWord']), underline_svg(), esc(b)))
        else:
            words.append(esc(wd))
    title_html = ' '.join(words)
    top = ('<section class="case-top wrap"><span class="tag">[%s]</span><h1 class="case-title big" data-reveal><span>%s</span><span class="tag">[%s]</span></h1></section>'
           % (esc(c['label']), title_html, esc(c['tags'])))
    if c.get('topImage'):
        top += '<div class="case-hero wrap pic" data-reveal>%s</div>' % pic(c['topImage'], S['images'][c['topImage']]['alt'], [800, 1280], '(min-width: 1440px) 1360px, 100vw', loading='eager')
    meta = ('<dl class="case-meta"><div><dt class="tag muted">[%s]</dt><dd>%s</dd></div><div><dt class="tag muted">[%s]</dt><dd>%s</dd></div><div><dt class="tag muted">[%s]</dt><dd>%s</dd></div></dl>'
            % (esc(L['brief']), esc(c['brief']), esc(L['myRole']), esc(c['myRole']), esc(L['result']), esc(c['result'])))
    intro = '<div class="case-intro lead">%s</div>' % ''.join('<p data-reveal style="--d:%dms">%s</p>' % (k * 40, esc(p)) for k, p in enumerate(c['intro']))
    cols = '<section class="sec--tight wrap case-cols">%s%s</section>' % (meta, intro)
    # evidence
    slides = []
    single = ''
    for ev in c['evidence']:
        t = ev['type']
        if t == 'chart':
            slides.append(fig_chart(ev))
        elif t == 'card':
            slides.append(fig_card(ev))
        elif t == 'flow':
            slides.append(fig_flow(ev))
        elif t == 'lanes':
            slides.append(fig_lanes(ev))
        elif t == 'episode':
            slides.append(fig_episode(ev))
        elif t == 'link':
            slides.append(fig_link(ev))
        elif t == 'bar':
            single = '<section class="wrap" data-reveal>%s</section>' % fig_bar(ev)
    evid = single if single else gallery(slides)
    secs = ''
    for k, s in enumerate(c['sections']):
        body = ''.join('<p>%s</p>' % esc(p) for p in s['body'])
        if s.get('list'):
            body += '<ol>%s</ol>' % ''.join('<li>%s</li>' % esc(x) for x in s['list'])
        secs += ('<div class="csec" data-reveal><h3><span class="tag muted">[%02d]</span><br>%s</h3><div>%s</div></div>' % (k + 1, esc(s['label']), body))
    secs = '<section class="sec wrap">%s</section>' % secs
    pull = '<section class="pulline wrap"><p class="mega big" data-reveal>%s</p></section>' % esc(c['pullLine'])
    imp = ''.join('<div data-reveal style="--d:%dms"><span class="impact__n">%s</span><span class="impact__l tag">[%s]</span></div>' % (k * 40, impact_number(x['number']), esc(x['label']))
                  for k, x in enumerate(c['impact']))
    impact = ('<section class="sec--tight wrap" aria-labelledby="imp-k"><span class="tag" id="imp-k">[%s]</span>%s<div class="impact">%s</div>%s</section>'
              % (esc(L['impact']), ('<p class="lead" style="margin-top:var(--s3)">%s</p>' % esc(c['impactIntro'])) if c.get('impactIntro') else '', imp,
                 ('<p class="footnote tag muted">%s</p>' % esc(c['footnote'])) if c.get('footnote') else ''))
    nxt_sec = ('<section class="sec--tight wrap csec"><h3><span class="tag muted">[%s]</span></h3><p>%s</p></section>' % (esc(L['next']), esc(c['next'])))
    nextcase = ('<section class="nextcase wrap"><span class="kicker tag">[%s]</span>%s<p class="tag" style="margin-top:var(--s5)">%s</p></section>'
                % (esc(UI['nextCase']), row(nxt['number'], nxt['menuLabel'], nxt['id'] + '.html', aria=nxt['accessibleName'], arrow='→'),
                   btag(UI['allWork'], 'work.html', '→')))
    main = top + cols + evid + secs + pull + impact + nxt_sec + nextcase
    return page(c['id'], main, html_class='case', html_style=style, theme=bg)


def build_about():
    a = S['about']
    hero = ('<section class="about-hero wrap"><div><h1 class="mega big" data-reveal>%s</h1><span class="tag" style="display:block;margin-top:var(--s4)">[%s]</span></div>'
            '<div class="about-hero__pic pic" data-reveal>%s</div></section>'
            % (esc(a['statement']), esc(a['subLine']), pic(a['photo'], S['images'][a['photo']]['alt'], [800, 1600], '(min-width: 900px) 40vw, 100vw', loading='eager')))
    bio = ('<section class="sec--tight wrap"><p class="lead" style="max-width:60ch" data-reveal>%s</p><div class="chips tag">%s</div></section>'
           % (esc(a['shortBio']), ''.join('<span>[%s]</span>' % esc(t) for t in a['toolkit'])))
    rows = ''
    for k, j in enumerate(a['career']):
        sub = '<span class="tag">[%s]</span><span>%s</span>' % (esc(j['field']), esc(j['line']))
        rows += ('<li class="tl__row" data-reveal style="--d:%dms"><span class="tag">[%s]</span><span>%s</span><span class="tag">[%s]</span><span class="tl__sub muted">%s</span></li>'
                 % (k * 40, esc(j['dates']), esc(j['title']), esc(j['company']), sub))
    career = ('<section class="sec wrap" aria-labelledby="car-k"><span class="kicker tag" id="car-k">[%s] <span class="muted">[%s]</span></span><ol class="tl">%s</ol></section>'
              % (esc(a['careerHeading']), esc(a['careerLabel']), rows))
    certs = ('<section class="sec--tight wrap" aria-labelledby="cert-k"><span class="kicker tag" id="cert-k">[%s]</span><ul class="certs">%s</ul></section>'
             % (esc(a['certificationsHeading']), ''.join('<li class="tag"><span class="muted">[%s]</span> %s</li>' % (esc(x['issuer']), esc(x['title'])) for x in a['certifications'])))
    lessons = ''.join(row('%03d' % (i + 1), l, size='row--s', sr=l, delay=i * 40) for i, l in enumerate(a['lessons']))
    les = ('<section class="sec wrap" aria-labelledby="les-k"><span class="kicker tag" id="les-k">[%s]</span><div class="index index--left">%s</div></section>'
           % (esc(a['lessonsHeading']), lessons))
    return page('about', hero + bio + career + certs + les)


def build_broll():
    b = S['broll']
    head = '<section class="wrap" style="padding-top:var(--s4)"><h1 class="mega big" data-reveal>%s</h1><span class="tag">[%s]</span></section>' % (esc(b['title']), esc(b['subLine']))
    slides, tiles = [], ''
    for it in b['items']:
        if it['type'] == 'video':
            media = ('<div data-video><video src="assets/video/studio-pan.mp4" poster="assets/video/studio-pan-poster.webp" width="720" height="1280" muted loop playsinline preload="none" aria-label="%s"></video>'
                     '<div class="vctl tag" style="margin-top:var(--s2)"><button class="btag" type="button" data-play>[Play]</button><span data-time aria-live="off"></span><button class="btag" type="button" data-fs>[Fullscreen]</button></div></div>' % esc(it['alt']))
            tile = ('<button class="tile" type="button" data-tile data-kind="video" data-src="assets/video/studio-pan.mp4" data-poster="assets/video/studio-pan-poster.webp" data-alt="%s" data-cap="%s">'
                    '<img src="assets/video/studio-pan-poster.webp" width="720" height="1280" alt="%s" loading="lazy" decoding="async"></button>' % (esc(it['alt']), esc(it['caption']), esc(it['alt'])))
        else:
            widths = [800, 1280] if it['src'] == 'podcast' else [800, 1600]
            media = pic(it['src'], it['alt'], widths, '(min-width: 900px) 512px, 86vw')
            w, h = img_size(it['src'] + '-' + str(widths[-1]))
            tile = ('<button class="tile" type="button" data-tile data-kind="image" data-src="assets/img/%s-%d.webp" data-w="%d" data-h="%d" data-alt="%s" data-cap="%s">%s</button>'
                    % (it['src'], widths[-1], w, h, esc(it['alt']), esc(it['caption']), pic(it['src'], it['alt'], [800], '240px')))
        slides.append('%s<figcaption class="tag">[%s]</figcaption>' % (media, esc(it['caption'])))
        tiles += tile
    gal = gallery(slides, media=True)
    grid = '<section class="wrap"><div class="grid">%s</div></section>' % tiles
    lb = ('<dialog class="lb" id="lightbox" aria-label="%s"><div class="lb__in"><div class="lb__top tag"><span class="lb__count"></span><span class="lb__cap"></span>'
          '<div class="lb__nav"><button class="gal__btn" type="button" data-lbprev><span aria-hidden="true">←</span><span class="vh">←</span></button>'
          '<button class="gal__btn" type="button" data-lbnext><span aria-hidden="true">→</span><span class="vh">→</span></button>'
          '<button class="close" type="button" data-lbclose>%s</button></div></div><div class="lb__media"></div></div></dialog>' % (esc(b['title']), UI['close']))
    return page('b-roll', head + gal + grid, extra=lb)


def main():
    out = {'index.html': build_index(), 'work.html': build_work(), 'about.html': build_about(), 'b-roll.html': build_broll()}
    for i, c in enumerate(S['cases']):
        out[c['id'] + '.html'] = build_case(c, i)
    for name, body in out.items():
        with open(os.path.join(ROOT, name), 'w', encoding='utf-8') as f:
            f.write(body)
        print('wrote', name, len(body.encode('utf-8')) // 1024, 'KB')
    if MISSING:
        print('MISSING:', *MISSING, sep='\n  ')


if __name__ == '__main__':
    main()
