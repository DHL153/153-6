# 맞춘 칸(원화 좌표)을 확대 + 10px 격자(50마다 숫자) — 관절점 찍기용.  python3 kit5/zoomgrid.py CELL X0 Y0 X1 Y1 SCALE OUT
import sys, json, cv2, numpy as np
from PIL import Image, ImageDraw
c, x0, y0, x1, y1, S, out = int(sys.argv[1]), *map(int, sys.argv[2:6]), int(sys.argv[6]), sys.argv[7]
G = json.load(open('kit5/geom.json')); sh = np.asarray(Image.open('sheets/kit5_v1.png').convert('RGB'))
M = np.array(G[f'cell{c}']['M']).copy(); M = np.vstack([M, [0, 0, 1]]); T = np.array([[S, 0, -x0 * S], [0, S, -y0 * S], [0, 0, 1]]) @ M
w = cv2.warpAffine(sh, T[:2], ((x1 - x0) * S, (y1 - y0) * S), flags=cv2.INTER_CUBIC, borderValue=(255, 0, 255))
im = Image.fromarray(w); d = ImageDraw.Draw(im)
for x in range((x0 // 10) * 10, x1 + 1, 10):
    X = (x - x0) * S; d.line([(X, 0), (X, im.height)], fill=(255, 255, 255) if x % 50 == 0 else (150, 90, 150), width=1)
    if x % 50 == 0: d.text((X + 2, 2), str(x), fill=(255, 255, 0))
for y in range((y0 // 10) * 10, y1 + 1, 10):
    Y = (y - y0) * S; d.line([(0, Y), (im.width, Y)], fill=(255, 255, 255) if y % 50 == 0 else (150, 90, 150), width=1)
    if y % 50 == 0: d.text((2, Y + 2), str(y), fill=(255, 255, 0))
im.save(out)
