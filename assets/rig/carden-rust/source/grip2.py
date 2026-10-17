#!/usr/bin/env python3
"""6 카르덴 찌르기 쥔 손 2차 시트(2026-10-17 22:55, 자루 수평·자홍 배경, 두 손 한 장 sheets/grip2_both.png) → handL2·handR2
- 자루 굵기(93px) = 원화 봉 자루 굵기(리그 50) → 배율 0.538 (주먹 폭 285px → 153, 원화 주먹 154와 같음)
- 앞 주먹(왼쪽 조각): 소매가 주먹 왼쪽 아래(약 8시) → 팔뚝이 왼쪽 아래에서 옴. 자루 토막 양쪽 지움
- 뒷손(오른쪽 조각): 팔뚝(왼쪽, 9시) + 주먹. 자루 토막 오른쪽만 지움(왼쪽은 소매 테와 주먹 사이 짧은 띠 — 봉과 같은 선)
점(시트 px)은 격자 확대(review/grip_grid.png)에서 읽음. 결과: parts_work/handL2.png·handR2.png + hands2.json"""
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cut_sheet import key
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'parts_work')
SHAFT_Y = (395, 488); SHAFT_C = 441.5; SCALE = 50.0 / (SHAFT_Y[1] - SHAFT_Y[0])
P = {'handL': dict(x=(0, 700), fist=(240, 525), cut=[(0, 166, 386, 496), (527, 700, 386, 496)], grip=(380, SHAFT_C), wrist=(165, 592), toElbow=(-0.80, 0.60)),
     'handR': dict(x=(700, 1536), fist=(1020, 1292), cut=[(1354, 1536, 386, 496)], grip=(1160, SHAFT_C), elbow=(760, 545))}   # 뒷주먹 cut 1294 였을 때 넷째 손가락 끝이 지워져 자루가 손가락 앞으로 보였음 → 1354 (10-18 00:21)
rgba, alpha = key(np.asarray(Image.open(os.path.join(HERE, 'sheets', 'grip2_both.png')).convert('RGB')))
R = {}
for nm, p in P.items():
    a = rgba.copy(); al = a[..., 3].astype(float); yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    al[(xx < p['x'][0]) | (xx >= p['x'][1])] = 0
    for x0, x1, y0, y1 in p['cut']:
        k = np.ones_like(al); band = (yy >= y0) & (yy <= y1)
        k[band & (xx >= x0) & (xx < x1)] = 0
        al *= k
    a[..., 3] = al.astype(np.uint8); ys, xs = np.nonzero(a[..., 3] > 8); ox, oy = int(xs.min()), int(ys.min())
    a = a[oy:ys.max() + 1, ox:xs.max() + 1]; Image.fromarray(a, 'RGBA').save(os.path.join(OUT, nm + '2.png'))
    loc = lambda q: [round(q[0] - ox, 1), round(q[1] - oy, 1)]
    r = dict(file=f'parts_work/{nm}2.png', grip=loc(p['grip']), shaftDir=[1, 0], scale=round(SCALE, 4), off=[ox, oy])
    if 'wrist' in p: r['wrist'] = loc(p['wrist']); r['toElbow'] = list(p['toElbow'])
    if 'elbow' in p: r['elbow'] = loc(p['elbow'])
    R[nm] = r
json.dump(R, open(os.path.join(HERE, 'hands2.json'), 'w'), indent=1); print(json.dumps(R))
