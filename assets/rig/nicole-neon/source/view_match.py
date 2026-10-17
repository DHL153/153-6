"""매칭 결과 확인: 왼쪽 기준 그림, 가운데 조각만 합성, 오른쪽 겹침(기준 빨강 / 조각 파랑)."""
import json, sys, numpy as np, cv2
from PIL import Image
order = sys.argv[2].split(',') if len(sys.argv) > 2 else None
res = json.load(open('match_result.json')); ref = Image.open('ref1024.png').convert('RGBA')
comp = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
names = order or list(res.keys())
for n in names:
    r = res[n]; img = np.asarray(Image.open(r['file']).convert('RGBA'))
    w = cv2.warpAffine(img, np.array(r['M']), (1024, 1024), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    comp.alpha_composite(Image.fromarray(w, 'RGBA'))
bg = lambda im: (lambda b: (b.alpha_composite(im), b)[1])(Image.new('RGBA', (1024, 1024), (255, 240, 120, 255)))
A = np.asarray(ref)[..., 3] > 128; B = np.asarray(comp)[..., 3] > 128
ov = np.full((1024, 1024, 3), 255, np.uint8); ov[A & ~B] = (230, 60, 60); ov[B & ~A] = (40, 90, 230); ov[A & B] = (150, 120, 170)
row = Image.new('RGB', (3072, 1024)); row.paste(bg(ref).convert('RGB'), (0, 0)); row.paste(bg(comp).convert('RGB'), (1024, 0)); row.paste(Image.fromarray(ov), (2048, 0))
row.resize((1536, 512)).save(sys.argv[1])
