# 칸 나누기 확대 확인: python3 tools/labzoom.py x0 y0 x1 y1 k out.png
import sys, numpy as np
from PIL import Image, ImageDraw
x0, y0, x1, y1, k = map(int, sys.argv[1:6]); out = sys.argv[6]
LAB = np.load('work/labels.npy'); RA = np.array(Image.open('ref512.png').convert('RGBA'))
PRIO = ['armL', 'pauldron', 'armU', 'fistF', 'hammer', 'head', 'torso', 'foreF', 'flapC', 'flapN', 'hips', 'thighN', 'bootN', 'thighF', 'bootF', 'pony']
sub = LAB[y0:y1, x0:x1]; rgb = RA[y0:y1, x0:x1, :3].astype(float); al = RA[y0:y1, x0:x1, 3] > 8
c = Image.fromarray(np.where(al[..., None], rgb, 255).astype(np.uint8)).resize(((x1 - x0) * k, (y1 - y0) * k), Image.NEAREST); d = ImageDraw.Draw(c)
for y in range(sub.shape[0]):
    for x in range(sub.shape[1]):
        l = sub[y, x]
        if l < 0: continue
        if x + 1 < sub.shape[1] and sub[y, x + 1] != l: d.line(((x + 1) * k, y * k, (x + 1) * k, (y + 1) * k), fill=(255, 0, 255), width=2)
        if y + 1 < sub.shape[0] and sub[y + 1, x] != l: d.line((x * k, (y + 1) * k, (x + 1) * k, (y + 1) * k), fill=(255, 0, 255), width=2)
for i, n in enumerate(PRIO):
    ys, xs = np.nonzero(sub == i)
    if len(xs): d.text((int(np.median(xs)) * k, int(np.median(ys)) * k), n, fill=(0, 0, 255))
for v in range(x0 - x0 % 10 + 10, x1, 10): d.text(((v - x0) * k + 1, 1), str(v), fill=(255, 0, 0))
for v in range(y0 - y0 % 10 + 10, y1, 10): d.text((1, (v - y0) * k + 1), str(v), fill=(255, 0, 0))
c.save(out)
