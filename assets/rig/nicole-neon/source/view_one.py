"""한 조각 배치 확인: 기준 그림 위에 조각 외곽(초록)·반투명 조각. python3 -I view_one.py result.json name1,name2 out.png"""
import json, sys, numpy as np, cv2
from PIL import Image
res = json.load(open(sys.argv[1])); names = sys.argv[2].split(','); out = sys.argv[3]
ref = np.asarray(Image.open('ref1024.png').convert('RGBA')).astype(np.float32)
bg = np.full((1024, 1024, 3), 255, np.float32); al = ref[..., 3:4] / 255; base = ref[..., :3] * al + bg * (1 - al)
tiles = []
for n in names:
    r = res[n]; img = np.asarray(Image.open(r['file']).convert('RGBA'))
    w = cv2.warpAffine(img, np.array(r['M']), (1024, 1024), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)).astype(np.float32)
    a = (w[..., 3:4] / 255) * .55; comp = base * (1 - a) + w[..., :3] * a
    m = (w[..., 3] > 128).astype(np.uint8); cnt, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    comp = comp.astype(np.uint8).copy(); cv2.drawContours(comp, cnt, -1, (0, 200, 0), 2)
    ys, xs = np.where(m > 0)
    if len(xs) == 0: continue
    x0, x1, y0, y1 = max(0, xs.min() - 30), min(1024, xs.max() + 30), max(0, ys.min() - 30), min(1024, ys.max() + 30)
    t = Image.fromarray(comp[y0:y1, x0:x1]); t.thumbnail((340, 340)); tiles.append((n, t))
W = Image.new('RGB', (350 * len(tiles), 360), (255, 255, 255))
from PIL import ImageDraw
d = ImageDraw.Draw(W)
for i, (n, t) in enumerate(tiles): W.paste(t, (i * 350, 18)); d.text((i * 350 + 4, 2), n, fill=(0, 0, 0))
W.save(out)
