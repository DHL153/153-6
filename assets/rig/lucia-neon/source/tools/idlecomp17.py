"""17 네온 루시아 — 오린 조각(work/*Art.png + offsets.json)을 리그 그리는 순서로 제자리에 겹쳐 원화와 비교 (idlecomp7 구조)
  순서 = build_lucia17 의 draw(먼 팔뚝 → 도끼 → 쥔 주먹 → 다리 → 상체 → 윗팔 → 어깨갑 → 골반 → 머리 → 가리개 → 방패)
  출력: ../review/idlecomp17.png (원화 · 겹친 것 · 차이 빨강 · 조각 따로 어두운 배경) + 차이 px
실행: python3 -I tools/idlecomp17.py   (build_lucia17.py 를 먼저 — work/ 갱신)
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); W = os.path.join(S, 'work')
RA = np.array(Image.open(os.path.join(S, 'ref512.png')).convert('RGBA')); OFF = json.load(open(os.path.join(W, 'offsets.json')))
ORDER = ['foreF', 'axe', 'fistF', 'thighF', 'bootF', 'thighN', 'bootN', 'torso', 'upF', 'pauldron', 'hips', 'head', 'collar', 'shield']
can = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
for n in ORDER:
    p = Image.open(os.path.join(W, n + 'Art.png')).convert('RGBA'); o = OFF[n]; can.alpha_composite(p, (int(o[0]), int(o[1])))
C = np.array(can)
def onbg(a, c=(235, 238, 245)):
    b = Image.new('RGBA', (512, 512), c + (255,)); b.alpha_composite(Image.fromarray(a)); return np.array(b.convert('RGB')).astype(int)
a, b = onbg(RA), onbg(C); d = np.abs(a - b).max(-1); bad = d > 40
print('차이 px(>40)', int(bad.sum()), '· 평균 차', round(float(d.mean()), 3), '· 겹친 것 알파만 있는 곳', int(((C[..., 3] > 128) & (RA[..., 3] < 40)).sum()), '· 원화만 있는 곳', int(((RA[..., 3] > 128) & (C[..., 3] < 40)).sum()))
r = a.copy(); r[bad] = (r[bad] * .3 + np.array([255, 30, 30]) * .7).astype(int)
tiles = Image.new('RGB', (512, 512), (40, 42, 52)); dd = ImageDraw.Draw(tiles); x, y, rh = 4, 4, 0
for n in ORDER:
    p = Image.open(os.path.join(W, n + 'Art.png')).convert('RGBA'); s = min(1.0, 150 / max(p.size)); p = p.resize((max(1, int(p.width * s)), max(1, int(p.height * s))), Image.LANCZOS)
    if x + p.width > 508: x, y, rh = 4, y + rh + 14, 0
    tiles.paste(p, (x, y), p); dd.text((x, y + p.height), n, fill=(255, 255, 120)); x += p.width + 6; rh = max(rh, p.height)
sp = np.full((512, 6, 3), 255)
Image.fromarray(np.hstack([a, sp, b, sp, r, sp, np.array(tiles)]).astype(np.uint8)).save(os.path.join(S, 'review', 'idlecomp17.png')); print('그림 review/idlecomp17.png')
