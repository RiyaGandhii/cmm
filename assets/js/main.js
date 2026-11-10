/* Riya Gandhi portfolio: moods, layers, roll helpers, galleries, media. Classic JS, no dependencies. */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var rm = window.matchMedia ? matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
  function $(s, c) { return (c || d).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); }
  var IO = 'IntersectionObserver' in window;

  /* mood */
  var MOODS = ['light', 'dark', 'paper'];
  var NAMES = { light: 'Light', dark: 'Dark', paper: 'Paper' };
  var BG = { light: '#FFFFFF', dark: '#0E0E0E', paper: '#F5F2EA' };
  function mood() { return root.getAttribute('data-mood') || 'light'; }
  function setMood(m, save) {
    root.setAttribute('data-mood', m);
    var b = $('.mood');
    if (b) {
      $('.mood__name', b).textContent = NAMES[m];
      b.setAttribute('aria-label', 'Mood: ' + NAMES[m] + '. Change mood');
    }
    var t = $('meta[name="theme-color"]');
    if (t && !root.classList.contains('case')) t.setAttribute('content', BG[m]);
    if (save) { try { localStorage.setItem('mood', m); } catch (e) {} }
  }
  setMood(mood(), false);
  var mb = $('.mood');
  if (mb) mb.addEventListener('click', function () { setMood(MOODS[(MOODS.indexOf(mood()) + 1) % 3], true); });

  /* layers: about panel and menu, one at a time, focus trapped */
  var FOC = 'a[href],button:not([disabled]),input,select,textarea,[tabindex]:not([tabindex="-1"])';
  var layer = null;
  function visible(el) { return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length); }
  function trap(e, el) {
    if (e.key !== 'Tab') return;
    var f = $$(FOC, el).filter(visible);
    if (!f.length) { e.preventDefault(); return; }
    var a = f[0], b = f[f.length - 1];
    if (e.shiftKey && (d.activeElement === a || !el.contains(d.activeElement))) { e.preventDefault(); b.focus(); }
    else if (!e.shiftKey && (d.activeElement === b || !el.contains(d.activeElement))) { e.preventDefault(); a.focus(); }
  }
  function openLayer(el, opener, cls, veil) {
    if (layer) closeLayer();
    el.classList.add(cls);
    if (veil) veil.classList.add('is-on');
    root.classList.add('is-locked');
    opener.setAttribute('aria-expanded', 'true');
    layer = { el: el, opener: opener, cls: cls, veil: veil };
    var f = $$(FOC, el).filter(visible)[0];
    setTimeout(function () { (f || el).focus(); }, 60);
  }
  function closeLayer() {
    if (!layer) return;
    var l = layer; layer = null;
    l.el.classList.remove(l.cls);
    if (l.veil) l.veil.classList.remove('is-on');
    root.classList.remove('is-locked');
    l.opener.setAttribute('aria-expanded', 'false');
    l.opener.focus();
  }
  d.addEventListener('keydown', function (e) {
    if (!layer) return;
    if (e.key === 'Escape') { e.preventDefault(); closeLayer(); } else trap(e, layer.el);
  });
  var veil = $('.veil'), panel = $('#about-panel'), menu = $('#menu');
  var roleBtn = $('.hdr__role'), menuBtn = $('.hdr__menu');
  if (roleBtn && panel) roleBtn.addEventListener('click', function () { openLayer(panel, roleBtn, 'is-open', veil); });
  if (menuBtn && menu) menuBtn.addEventListener('click', function () { openLayer(menu, menuBtn, 'is-open', null); });
  $$('[data-close]').forEach(function (b) { b.addEventListener('click', closeLayer); });
  if (veil) veil.addEventListener('click', closeLayer);
  if (menu) $$('a', menu).forEach(function (a) { a.addEventListener('click', function () { if (a.getAttribute('href').charAt(0) === '#') closeLayer(); }); });

  /* scroll reveal: a bounding-box check rather than IntersectionObserver,
     because a clip-path that hides the element also hides it from the observer */
  var rv = $$('[data-reveal]');
  function unclip(el) { el.style.clipPath = 'none'; }
  function reveal(el) {
    el.classList.add('is-in');
    el.addEventListener('transitionend', function h(ev) { if (ev.target === el) { unclip(el); el.removeEventListener('transitionend', h); } });
    setTimeout(function () { unclip(el); }, 2000);
  }
  if (!rm.matches && rv.length) {
    var pending = rv.slice(), ticking = false;
    var check = function () {
      ticking = false;
      var vh = innerHeight;
      pending = pending.filter(function (el) {
        var r = el.getBoundingClientRect();
        if (r.top < vh * 0.94 && r.bottom > 0) { reveal(el); return false; }
        return true;
      });
      if (!pending.length) { removeEventListener('scroll', onScroll); removeEventListener('resize', onScroll); }
    };
    var onScroll = function () { if (!ticking) { ticking = true; requestAnimationFrame(check); } };
    addEventListener('scroll', onScroll, { passive: true });
    addEventListener('resize', onScroll);
    check();
    setTimeout(check, 300);
  } else rv.forEach(function (el) { el.classList.add('is-in'); unclip(el); });

  /* typing */
  $$('[data-type]').forEach(function (el) {
    var txt = el.textContent;
    if (rm.matches || !IO) { el.classList.add('is-done'); return; }
    var sr = d.createElement('span'); sr.className = 'vh'; sr.textContent = txt;
    el.parentNode.insertBefore(sr, el);
    el.setAttribute('aria-hidden', 'true');
    el.parentNode.style.minHeight = el.parentNode.offsetHeight + 'px';
    el.textContent = '';
    var tio = new IntersectionObserver(function (es) {
      if (!es[0].isIntersecting) return;
      tio.disconnect();
      var i = 0;
      var t = setInterval(function () {
        i++; el.textContent = txt.slice(0, i);
        if (i >= txt.length) { clearInterval(t); el.classList.add('is-done'); }
      }, 46);
    }, { threshold: 0.4 });
    tio.observe(el);
  });

  /* copy */
  function fallbackCopy(t) {
    var ta = d.createElement('textarea'); ta.value = t; ta.setAttribute('readonly', '');
    ta.style.position = 'fixed'; ta.style.opacity = '0'; d.body.appendChild(ta); ta.select();
    try { d.execCommand('copy'); } catch (e) {}
    d.body.removeChild(ta);
  }
  $$('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      var t = b.getAttribute('data-copy');
      var done = function () {
        b.textContent = '[Copied]';
        setTimeout(function () { b.textContent = '[Copy]'; }, 2000);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, function () { fallbackCopy(t); done(); });
      else { fallbackCopy(t); done(); }
    });
  });

  /* marquee pause */
  $$('.marquee__ctl').forEach(function (b) {
    var m = b.closest('.marquee');
    b.addEventListener('click', function () {
      var p = m.classList.toggle('is-paused');
      b.setAttribute('aria-pressed', p ? 'true' : 'false');
      b.textContent = p ? '[Play]' : '[Pause]';
    });
  });

  /* galleries */
  $$('.gal').forEach(function (g) {
    var tr = $('.gal__track', g), sl = $$('.gal__slide', g), cnt = $('.gal__count', g);
    var prev = $('[data-prev]', g), next = $('[data-next]', g), n = sl.length, i = 0;
    if (!tr || !n) return;
    function pad() { return parseFloat(getComputedStyle(tr).paddingLeft) || 0; }
    function pos(k) { return sl[k].getBoundingClientRect().left - tr.getBoundingClientRect().left + tr.scrollLeft - pad(); }
    function go(k) {
      k = Math.max(0, Math.min(n - 1, k));
      tr.scrollTo({ left: pos(k), behavior: rm.matches ? 'auto' : 'smooth' });
      i = k; paint();
    }
    function nearest() {
      var x = tr.scrollLeft, best = 0, bd = 1e9;
      if (x >= tr.scrollWidth - tr.clientWidth - 2) return n - 1;
      for (var k = 0; k < n; k++) { var dd = Math.abs(pos(k) - x); if (dd < bd) { bd = dd; best = k; } }
      return best;
    }
    function paint() {
      if (cnt) cnt.textContent = '[' + (i + 1) + '/' + n + ']';
      if (prev) prev.disabled = i === 0;
      if (next) next.disabled = i === n - 1;
    }
    var tick = false;
    tr.addEventListener('scroll', function () {
      if (tick) return; tick = true;
      requestAnimationFrame(function () { tick = false; var k = nearest(); if (k !== i) { i = k; paint(); } });
    }, { passive: true });
    if (prev) prev.addEventListener('click', function () { go(i - 1); });
    if (next) next.addEventListener('click', function () { go(i + 1); });
    tr.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { e.preventDefault(); go(i + 1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); go(i - 1); }
      else if (e.key === 'Home') { e.preventDefault(); go(0); }
      else if (e.key === 'End') { e.preventDefault(); go(n - 1); }
    });
    paint();
  });

  /* YouTube facade */
  $$('.yt[data-yt]').forEach(function (b) {
    b.addEventListener('click', function () {
      var f = d.createElement('iframe');
      f.src = 'https://www.youtube-nocookie.com/embed/' + b.getAttribute('data-yt') + '?autoplay=1&rel=0';
      f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
      f.setAttribute('allowfullscreen', '');
      f.title = b.getAttribute('data-title') || '';
      b.innerHTML = ''; b.appendChild(f); b.setAttribute('disabled', '');
    });
  });

  /* studio video */
  $$('[data-video]').forEach(function (w) {
    var v = $('video', w), play = $('[data-play]', w), time = $('[data-time]', w), fs = $('[data-fs]', w);
    if (!v) return;
    var userPaused = false;
    function fmt(s) { s = Math.floor(isFinite(s) ? s : 0); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
    function upd() { if (time) time.textContent = fmt(v.currentTime) + ' / ' + fmt(v.duration); }
    v.addEventListener('loadedmetadata', upd);
    v.addEventListener('timeupdate', upd);
    v.addEventListener('play', function () { if (play) play.textContent = '[Pause]'; });
    v.addEventListener('pause', function () { if (play) play.textContent = '[Play]'; });
    if (play) play.addEventListener('click', function () {
      if (v.paused) { userPaused = false; v.play(); } else { userPaused = true; v.pause(); }
    });
    if (fs) fs.addEventListener('click', function () {
      if (v.requestFullscreen) v.requestFullscreen();
      else if (v.webkitEnterFullscreen) v.webkitEnterFullscreen();
    });
    if (!rm.matches && IO) {
      new IntersectionObserver(function (es) {
        es.forEach(function (en) {
          if (en.intersectionRatio >= 0.5) { if (!userPaused) { var p = v.play(); if (p && p.catch) p.catch(function () {}); } }
          else if (!v.paused) v.pause();
        });
      }, { threshold: [0, 0.5, 1] }).observe(v);
    }
  });

  /* lightbox */
  var lb = $('#lightbox');
  if (lb && lb.showModal) {
    var tiles = $$('[data-tile]'), media = $('.lb__media', lb), cap = $('.lb__cap', lb), lcnt = $('.lb__count', lb), idx = 0, opener = null;
    function show(k) {
      idx = (k + tiles.length) % tiles.length;
      var t = tiles[idx];
      media.innerHTML = '';
      if (t.getAttribute('data-kind') === 'video') {
        var v = d.createElement('video');
        v.src = t.getAttribute('data-src'); v.poster = t.getAttribute('data-poster');
        v.muted = true; v.loop = true; v.controls = true; v.playsInline = true; v.setAttribute('playsinline', '');
        v.width = 720; v.height = 1280;
        v.setAttribute('aria-label', t.getAttribute('data-alt'));
        media.appendChild(v);
        if (!rm.matches) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }
      } else {
        var im = new Image();
        im.src = t.getAttribute('data-src'); im.alt = t.getAttribute('data-alt');
        im.width = +t.getAttribute('data-w'); im.height = +t.getAttribute('data-h');
        media.appendChild(im);
      }
      if (cap) cap.textContent = '[' + t.getAttribute('data-cap') + ']';
      if (lcnt) lcnt.textContent = '[' + (idx + 1) + '/' + tiles.length + ']';
    }
    tiles.forEach(function (t, k) {
      t.addEventListener('click', function () { opener = t; show(k); lb.showModal(); });
    });
    lb.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { e.preventDefault(); show(idx + 1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); show(idx - 1); }
    });
    lb.addEventListener('close', function () { media.innerHTML = ''; if (opener) opener.focus(); });
    lb.addEventListener('click', function (e) { if (e.target === lb) lb.close(); });
    $$('[data-lbclose]', lb).forEach(function (b) { b.addEventListener('click', function () { lb.close(); }); });
    $$('[data-lbprev]', lb).forEach(function (b) { b.addEventListener('click', function () { show(idx - 1); }); });
    $$('[data-lbnext]', lb).forEach(function (b) { b.addEventListener('click', function () { show(idx + 1); }); });
  }
})();
