#!/usr/bin/env python3
"""Asset pipeline for riya-portfolio.
Reads source/ (and the optimised hero from ../cmm-portfolio/assets/img),
writes WebP images, the compressed studio video, its poster and the
video frames into assets/. Run from the project root with the venv:
    .venv/bin/python scripts/assets.py [stage1|stage2|all]
Stage 1: HEIC to JPEG, base photos, video, 1 fps frame sheet.
Stage 2: crops that depend on the frames chosen in CROPS below.
"""
import os, subprocess, sys
from PIL import Image, ImageOps
import pillow_heif
import imageio_ffmpeg

pillow_heif.register_heif_opener()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'source')
CACHE = os.path.join(ROOT, '.cache')
IMG = os.path.join(ROOT, 'assets', 'img')
VID = os.path.join(ROOT, 'assets', 'video')
OLD = os.path.join(os.path.dirname(ROOT), 'cmm-portfolio', 'assets', 'img')
FF = imageio_ffmpeg.get_ffmpeg_exe()
Q = 78
for d in (CACHE, IMG, VID):
    os.makedirs(d, exist_ok=True)

def save_webp(im, name, widths, ratio=None, box=None):
    """Crop im to box (then to ratio, centred) and save at each width."""
    if box:
        im = im.crop(box)
    if ratio:
        w, h = im.size
        tw, th = ratio
        if w / h > tw / th:
            nw = int(h * tw / th); x = (w - nw) // 2; im = im.crop((x, 0, x + nw, h))
        else:
            nh = int(w * th / tw); y = (h - nh) // 2; im = im.crop((0, y, w, y + nh))
    out = []
    for wd in widths:
        w, h = im.size
        if wd >= w:
            r = im.copy(); wd = w
        else:
            r = im.resize((wd, round(h * wd / w)), Image.LANCZOS)
        path = os.path.join(IMG, f'{name}-{wd}.webp')
        r.save(path, 'WEBP', quality=Q, method=6)
        out.append((path, r.size, os.path.getsize(path)))
    for p, s, b in out:
        print(f'{os.path.relpath(p, ROOT)} {s[0]}x{s[1]} {b//1024} KB')
    return im

def stage1():
    # HEIC to JPEG with EXIF rotation applied. By content this file is the
    # hero portrait (green velvet blouse, palm leaves), not the on-set photo.
    im = Image.open(os.path.join(SRC, 'IMG_0697.HEIC'))
    im = ImageOps.exif_transpose(im).convert('RGB')
    im.save(os.path.join(CACHE, 'hero.jpg'), quality=92)
    print('hero.jpg', im.size)
    # podcast still: JPEG with EXIF rotation applied
    pm = ImageOps.exif_transpose(Image.open(os.path.join(SRC, 'C0203T01.JPG'))).convert('RGB')
    pm.save(os.path.join(CACHE, 'podcast.jpg'), quality=92)
    print('podcast.jpg', pm.size)
    # video: 720x1280 H.264, CRF 27, preset slow, no audio, faststart
    mov = os.path.join(SRC, 'IMG_2188.MOV')
    out = os.path.join(VID, 'studio-pan.mp4')
    subprocess.run([FF, '-y', '-hide_banner', '-loglevel', 'error', '-i', mov,
                    '-map', '0:v:0', '-vf', 'scale=720:1280', '-c:v', 'libx264', '-crf', '27',
                    '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', out], check=True)
    print('studio-pan.mp4', os.path.getsize(out) // 1024, 'KB')
    # poster from the first frame
    subprocess.run([FF, '-y', '-hide_banner', '-loglevel', 'error', '-i', out, '-frames:v', '1',
                    os.path.join(CACHE, 'poster.png')], check=True)
    Image.open(os.path.join(CACHE, 'poster.png')).convert('RGB').save(
        os.path.join(VID, 'studio-pan-poster.webp'), 'WEBP', quality=Q, method=6)
    print('poster', os.path.getsize(os.path.join(VID, 'studio-pan-poster.webp')) // 1024, 'KB')
    # one frame per second from the original for picking the three stills
    subprocess.run([FF, '-y', '-hide_banner', '-loglevel', 'error', '-i', mov, '-map', '0:v:0',
                    '-vf', 'fps=1', '-q:v', '2', os.path.join(CACHE, 'f_%02d.jpg')], check=True)
    frames = sorted(f for f in os.listdir(CACHE) if f.startswith('f_'))
    thumbs = [Image.open(os.path.join(CACHE, f)).resize((270, 480)) for f in frames]
    sheet = Image.new('RGB', (270 * 8, 480 * 2), 'white')
    for i, t in enumerate(thumbs):
        sheet.paste(t, ((i % 8) * 270, (i // 8) * 480))
    sheet.save(os.path.join(CACHE, 'sheet.jpg'), quality=85)
    print('frames', len(frames))

# Crop boxes chosen after looking at the frames (left, top, right, bottom)
CROPS = {
    'hero': (0, 150, 2954, 3842),
    # the on-set photo was not supplied; frame 15 of the studio pan stands in
    'onset_src': 'f_15.jpg', 'onset': (0, 1000, 2160, 3700), 'onset_thumb': (0, 1500, 2160, 3120),
    'podcast_thumb': (45, 0, 1005, 720),
    'two-chairs_src': 'f_02.jpg', 'two-chairs': (0, 700, 2160, 3400), 'two-chairs_thumb': (0, 1500, 2160, 3120),
    'crew_src': 'f_10.jpg', 'crew': (0, 900, 2160, 3600), 'crew_thumb': (0, 1600, 2160, 3220),
    'softbox_src': 'f_13.jpg', 'softbox': (0, 300, 2160, 3000), 'softbox_thumb': (0, 400, 2160, 2020),
}

def stage2():
    hero = Image.open(os.path.join(CACHE, 'hero.jpg'))
    # 4:5 portrait: headroom kept, eyes on the upper third, cut above the hands
    save_webp(hero, 'hero', [800, 1600], box=CROPS['hero'])
    onset = Image.open(os.path.join(CACHE, CROPS['onset_src']))
    save_webp(onset, 'onset', [800, 1600], box=CROPS['onset'])
    save_webp(onset, 'onset-thumb', [320], box=CROPS['onset_thumb'])
    pod = Image.open(os.path.join(CACHE, 'podcast.jpg'))
    save_webp(pod, 'podcast', [800, 1280])
    save_webp(pod, 'podcast-thumb', [320], box=CROPS['podcast_thumb'])
    for key in ('two-chairs', 'crew', 'softbox'):
        fr = Image.open(os.path.join(CACHE, CROPS[key + '_src']))
        save_webp(fr, 'frame-' + key, [800, 1600], box=CROPS[key])
        save_webp(fr, 'frame-' + key + '-thumb', [320], box=CROPS[key + '_thumb'])

if __name__ == '__main__':
    stage = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if stage in ('stage1', 'all'):
        stage1()
    if stage in ('stage2', 'all'):
        stage2()
