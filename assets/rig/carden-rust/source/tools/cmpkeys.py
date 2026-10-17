#!/usr/bin/env python3
"""동작 시트 프레임 vs 리그 같은 시점: 시트 · 리그 · 겹침(빨강 시트/파랑 리그). 가로는 가장 잘 겹치는 곳.
python3 cmpkeys.py PKG scene out.png t:frame,t:frame,..."""
import os, sys, glob, subprocess, numpy as np
from PIL import Image, ImageDraw
pkg, scene, out, spec = sys.argv[1:5]; here = os.path.dirname(os.path.abspath(__file__)); MF = os.path.join(here, '..', 'motion', 'frames')
pairs = [(float(a), int(b)) for a, b in (x.split(':') for x in spec.split(','))]
tmp = out + '_r'
for f in glob.glob(tmp + '_*.png'): os.remove(f)
subprocess.run([sys.executable, os.path.join(here, 'render.py'), pkg, tmp, scene, ','.join(str(t) for t, _ in pairs), '2000', '1200', '700', '1120', '1'], check=True, stdout=subprocess.DEVNULL)
tiles = []
for i, (t, fi) in enumerate(pairs):
    R = Image.open(f'{tmp}_{i:02d}.png'); RA = np.asarray(R)[..., 3] > 128
    F = Image.open(os.path.join(MF, f's{fi:02d}.png')); FA = np.asarray(F)[..., 3] > 128; h, w = FA.shape; y0 = 1120 - h + 1
    best = (0, 0)
    for x0 in range(0, 2000 - w, 4):
        C = RA[y0:y0 + h, x0:x0 + w]; inter = (C & FA).sum(); u = RA.sum() + FA.sum() - inter; s = inter / u
        if s > best[0]: best = (s, x0)
    s, x0 = best; bx0, bx1 = max(0, x0 - 60), min(2000, x0 + w + 60); by0 = max(0, y0 - 60)
    bg = lambda im: (lambda b: (b.alpha_composite(im), b)[1])(Image.new('RGBA', im.size, (250, 244, 214, 255)))
    sheet = Image.new('RGBA', (2000, 1200), (0, 0, 0, 0)); sheet.alpha_composite(F, (x0, y0))
    SA = np.asarray(sheet)[..., 3] > 128
    ov = np.full((1200, 2000, 3), 255, np.uint8); ov[SA & ~RA] = (230, 60, 60); ov[RA & ~SA] = (40, 90, 230); ov[SA & RA] = (160, 140, 180)
    box = (bx0, by0, bx1, 1130)
    row = [bg(sheet).convert('RGB').crop(box), bg(R).convert('RGB').crop(box), Image.fromarray(ov).crop(box)]
    tw, th = row[0].size; T = Image.new('RGB', (tw * 3 + 20, th + 20), (255, 255, 255)); d = ImageDraw.Draw(T)
    for j, r in enumerate(row): T.paste(r, (j * (tw + 10), 20))
    d.text((4, 4), f't={t} 시트#{fi} IoU={s:.3f}', fill=(0, 0, 0)); tiles.append(T); os.remove(f'{tmp}_{i:02d}.png')
W = max(t.width for t in tiles); Hh = sum(t.height for t in tiles); o = Image.new('RGB', (W, Hh), (255, 255, 255)); y = 0
for t in tiles: o.paste(t, (0, y)); y += t.height
o.thumbnail((2400, 4000)); o.save(out); print(out)
