# 다각형·관절을 원화 위에 그려 봄: python3 -I polyview.py polys.json joints.json out.png [배율 3] [x0 y0 x1 y1]
import sys, json, os
from PIL import Image, ImageDraw
P = json.load(open(sys.argv[1])); J = json.load(open(sys.argv[2])); out = sys.argv[3]; k = int(sys.argv[4]) if len(sys.argv) > 4 else 3
box = tuple(map(int, sys.argv[5:9])) if len(sys.argv) > 8 else (0, 0, 512, 512)
a = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref512.png')).convert('RGBA'); bg = Image.new('RGBA', a.size, (255, 255, 255, 255)); bg.alpha_composite(a)
c = bg.crop(box).convert('RGB').resize(((box[2] - box[0]) * k, (box[3] - box[1]) * k), Image.LANCZOS); d = ImageDraw.Draw(c)
T = lambda p: ((p[0] - box[0]) * k, (p[1] - box[1]) * k)
COL = [(255, 0, 0), (0, 160, 0), (0, 0, 255), (200, 0, 200), (0, 170, 170), (230, 120, 0), (120, 60, 0), (0, 0, 0)]
for i, (n, pts) in enumerate((n, v) for n, v in P.items() if not n.startswith('_')):
    col = COL[i % len(COL)]; d.line([T(p) for p in pts] + [T(pts[0])], fill=col, width=2); d.text(T(pts[0]), n, fill=col)
def dot(p, n):
    x, y = T(p); d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(255, 0, 0), width=2); d.text((x + 6, y - 6), n, fill=(255, 0, 0))
for n in ['O', 'HIP', 'NECK', 'SH_N', 'EL_N', 'SH_F', 'EL_F', 'WR_F']:
    if n in J: dot(J[n], n)
if 'handle' in J: dot(J['handle']['collar'], 'collar'); dot(J['handle']['pommel'], 'pommel')
if 'eyes' in J:
    for n, p in J['eyes'].items():
        if not n.startswith('_'): dot(p, n)
if 'legs' in J:
    for sd in ('near', 'far'):
        for kk in ('h', 'k', 'a'): dot(J['legs'][sd][kk], sd[0] + kk)
c.save(out)
