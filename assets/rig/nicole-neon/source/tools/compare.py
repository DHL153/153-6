"""기준 그림 vs 리그 렌더: 나란히 + 겹침(빨강 기준 / 파랑 리그). python3 compare.py render.png out.png [crop x0,y0,x1,y1]"""
import sys, numpy as np
from PIL import Image
ref = Image.open(sys.argv[3] if len(sys.argv) > 4 else 'ref1024.png') if False else Image.open('ref1024.png'); r = Image.open(sys.argv[1]).convert('RGBA')
box = tuple(int(v) for v in sys.argv[3].split(',')) if len(sys.argv) > 3 else (0, 0, 1024, 1024)
bg = lambda im: (lambda b: (b.alpha_composite(im), b)[1])(Image.new('RGBA', im.size, (255, 240, 120, 255)))
A = np.asarray(ref)[..., 3] > 128; B = np.asarray(r)[..., 3] > 128
ov = np.full((1024, 1024, 3), 255, np.uint8); ov[A & ~B] = (230, 60, 60); ov[B & ~A] = (40, 90, 230); ov[A & B] = (160, 140, 180)
tiles = [bg(ref).convert('RGB').crop(box), bg(r).convert('RGB').crop(box), Image.fromarray(ov).crop(box)]
w, h = tiles[0].size; o = Image.new('RGB', (w * 3 + 20, h), (255, 255, 255))
for i, t in enumerate(tiles): o.paste(t, (i * (w + 10), 0))
o.save(sys.argv[2])
