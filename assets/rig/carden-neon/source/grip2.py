#!/usr/bin/env python3
"""16 네온 카르덴 찌르기 쥔 손 시트(2026-10-18 11:28 받음, sheets/grip2_both.png) → parts_work/handL2·handR2 + hands2.json
- 러스트 grip2_both 와 실루엣이 거의 같음(자루 y 392~490 / 러스트 395~488, 주먹 자리 같음) → 러스트 grip2.py 의 점을 그대로 씀
- 배율 = 주먹 길이 기준: 원화 봉 쥔 주먹(손가락 4줄, 자루 방향) 76px@512 = 152 리그 / 시트 주먹 285px → 0.533
  (자루 굵기 기준이면 48/98 = 0.49 로 주먹이 원화보다 8% 작아짐 — 네온 원화 봉이 주먹에 비해 가늘어서. 주먹 크기가 대기↔찌르기에서 같아야 하므로 주먹 기준)
- 앞 주먹(왼쪽): 소매가 주먹 왼쪽 아래(약 8시) → 팔뚝이 왼쪽 아래에서 옴. 자루 토막 양쪽 지움
- 뒷손(오른쪽): 팔뚝(왼쪽, 9시) + 주먹. 자루 토막 오른쪽만 지움(왼쪽 짧은 띠 = 봉과 같은 선, 러스트와 같음)"""
import json, os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'parts_work')

def key(a):
    """자홍 배경 → 알파 (가장자리 자홍 번짐 제거) — carden-rust/source/cut_sheet.py 와 같음"""
    a = a.astype(float); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    s = np.minimum(r, b) - g; alpha = np.clip((175 - s) / 80, 0, 1); A = alpha[..., None]
    bg = np.array([255., 0, 255]); col = np.clip(np.where(A > .02, (a[..., :3] - (1 - A) * bg) / np.maximum(A, 1e-3), 0), 0, 255)
    return np.dstack([col, alpha * 255]).astype(np.uint8), alpha

SHAFT_Y = (392, 490); SHAFT_C = 441.0; FIST_SHEET = 285.0; FIST_RIG = 152.0; SCALE = FIST_RIG / FIST_SHEET
# 자르는 띠 y 388~492: 자루 알파 391~490. 러스트 띠(386~496)를 그대로 쓰면 뒷주먹 엄지 끝(x1354, y≤386)과 앞 소매 윗선(x<166, y≥495)이 잘림 (11:35 확인)
P = {'handL': dict(x=(0, 700), cut=[(0, 166, 388, 492), (527, 700, 388, 492)], grip=(380, SHAFT_C), wrist=(165, 592), toElbow=(-0.80, 0.60)),
     'handR': dict(x=(700, 1536), cut=[(1354, 1536, 388, 492)], grip=(1160, SHAFT_C), elbow=(760, 545))}
if __name__ == '__main__':
    rgba, alpha = key(np.asarray(Image.open(os.path.join(HERE, 'sheets', 'grip2_both.png')).convert('RGB')))
    R = {}
    for nm, p in P.items():
        a = rgba.copy(); al = a[..., 3].astype(float); yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        al[(xx < p['x'][0]) | (xx >= p['x'][1])] = 0
        for x0, x1, y0, y1 in p['cut']:
            al[(yy >= y0) & (yy <= y1) & (xx >= x0) & (xx < x1)] = 0
        a[..., 3] = al.astype(np.uint8); ys, xs = np.nonzero(a[..., 3] > 8); ox, oy = int(xs.min()), int(ys.min())
        a = a[oy:ys.max() + 1, ox:xs.max() + 1]; Image.fromarray(a, 'RGBA').save(os.path.join(OUT, nm + '2.png'))
        loc = lambda q: [round(q[0] - ox, 1), round(q[1] - oy, 1)]
        r = dict(file=f'parts_work/{nm}2.png', grip=loc(p['grip']), shaftDir=[1, 0], scale=round(SCALE, 4), off=[ox, oy])
        if 'wrist' in p: r['wrist'] = loc(p['wrist']); r['toElbow'] = list(p['toElbow'])
        if 'elbow' in p: r['elbow'] = loc(p['elbow'])
        R[nm] = r
    json.dump(R, open(os.path.join(HERE, 'hands2.json'), 'w'), indent=1); print(json.dumps(R))
