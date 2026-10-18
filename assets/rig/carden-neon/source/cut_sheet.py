#!/usr/bin/env python3
"""6 카르덴 조각 시트(6×6, 자홍 배경) 자르기 + 1차 검수 (2026-10-17 21:50 준비, 시트 오기 전 작성·가짜 시트로 시험)
python3 -I cut_sheet.py sheets/parts1.png [--names names.json]
  1) 자홍(#FF00FF) 키잉 → 덩어리(조각) 찾기 (가까운 작은 덩어리는 큰 조각에 붙임)
  2) 줄(세로 위치로 묶음) → 줄 안에서 왼쪽→오른쪽 = 프롬프트 칸 번호 순서로 이름 붙임
  3) cut/<이름>.png + cut/_index.json + review/overview.png(번호·이름·판정 표시)
  4) 자동 판정(합격 기준 중 숫자로 볼 수 있는 것): 조각 수 31 · 곧은 팔다리(긴 축이 세로 ±8°) · 봉 길이/굵기 비(원화 대비 ±5%)
     · 표정 6장 크기 같음(±4%) · 몸 대비 크기(머리 폭 기준 배율로 원화와 같은 배율로 맞췄을 때 팔·다리 길이 ±12%)
  사람(Claude)이 그림으로 보는 것: 엄지·손 좌우·빛 방향·머리에 수염 없음 — review/side_*.png (원화 같은 부위와 나란히)
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = ['head', 'beard', 'tuftL', 'tuftR', 'torso', 'pouch', 'pauldron', 'shoulderF',
         'armU', 'armL', 'armLF', 'armF', 'foreF', 'fistF', 'handL', 'handR', 'waveHand',
         'hips', 'thighN', 'thighF', 'shinN', 'shinF', 'bootN', 'bootF', 'weapon',
         'face_neutral', 'face_happy', 'face_angry', 'face_focus', 'face_sad', 'face_shout']
STRAIGHT = ['armU', 'armLF', 'armF', 'foreF', 'thighN', 'thighF', 'shinN', 'shinF', 'weapon']
J = json.load(open(os.path.join(HERE, 'measure', 'joints_ref.json')))

def key(a):
    """자홍 배경 → 알파 (가장자리 자홍 번짐 제거)"""
    a = a.astype(float); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    s = np.minimum(r, b) - g; alpha = np.clip((175 - s) / 80, 0, 1); A = alpha[..., None]
    bg = np.array([255., 0, 255]); col = np.clip(np.where(A > .02, (a[..., :3] - (1 - A) * bg) / np.maximum(A, 1e-3), 0), 0, 255)
    return np.dstack([col, alpha * 255]).astype(np.uint8), alpha

def blobs(alpha, minpx=300):
    lab, n = nd.label(alpha > .5); sz = nd.sum(alpha > .5, lab, range(1, n + 1)); objs = nd.find_objects(lab)
    big = [i for i in range(n) if sz[i] >= minpx]; small = [i for i in range(n) if 30 <= sz[i] < minpx]
    groups = {i: [i] for i in big}
    for i in small:   # 작은 덩어리(금 단추·떨어진 털)는 가장 가까운 큰 조각에 붙임 (12px 안)
        sy, sx = objs[i]; cy, cx = (sy.start + sy.stop) / 2, (sx.start + sx.stop) / 2; best, bd = None, 1e9
        for j in big:
            by, bx = objs[j]; dy = max(by.start - cy, 0, cy - by.stop); dx = max(bx.start - cx, 0, cx - bx.stop); d = math.hypot(dx, dy)
            if d < bd: bd, best = d, j
        if best is not None and bd < 12: groups[best].append(i)
    out = []
    for j, ids in groups.items():
        m = np.isin(lab, [k + 1 for k in ids]); ys, xs = np.nonzero(m)
        out.append(dict(mask=m, x0=xs.min(), x1=xs.max() + 1, y0=ys.min(), y1=ys.max() + 1, cx=xs.mean(), cy=ys.mean(), px=int(m.sum())))
    return out

def rows_order(bs, W=None, H=None, grid=6):
    """칸(grid×grid, 같은 크기) 기준: 조각 가운데가 든 칸 — 칸보다 긴 조각(봉)은 위 끝이 든 칸. 줄 위→아래, 줄 안 왼쪽→오른쪽"""
    W = W or max(b['x1'] for b in bs); H = H or max(b['y1'] for b in bs); cw, ch = W / grid, H / grid
    def cell(b):
        y = b['y0'] + ch * .3 if b['y1'] - b['y0'] > ch * .9 else b['cy']
        return int(min(grid - 1, y // ch)), int(min(grid - 1, b['cx'] // cw))
    cells = sorted(((cell(b), b) for b in bs), key=lambda t: t[0])
    rows = {}
    for (r, c), b in cells: rows.setdefault(r, []).append(b)
    return [b for (r_, c_), b in cells], [len(rows[r]) for r in sorted(rows)]

def axis_angle(m):
    """조각 긴 축 각도(세로 = 0°, 도) · 길이 · 굵기"""
    ys, xs = np.nonzero(m); P = np.c_[xs - xs.mean(), ys - ys.mean()]; w, v = np.linalg.eigh(np.cov(P.T)); u = v[:, 1]
    t = P @ u; nrm = P @ v[:, 0]
    return math.degrees(math.atan2(u[0], u[1])) % 180, float(np.ptp(t)), float(np.percentile(np.abs(nrm), 90) * 2)

if __name__ == '__main__':
    src = sys.argv[1]; names = json.load(open(sys.argv[sys.argv.index('--names') + 1])) if '--names' in sys.argv else NAMES
    rgba, alpha = key(np.asarray(Image.open(src).convert('RGB')))
    bs, per_row = rows_order(blobs(alpha), alpha.shape[1], alpha.shape[0])
    os.makedirs(os.path.join(HERE, 'cut'), exist_ok=True); os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
    rep = {'sheet': src, 'pieces': len(bs), 'expected': len(names), 'rows': per_row, 'items': {}, 'fails': []}
    if len(bs) != len(names): rep['fails'].append(f'조각 수 {len(bs)} ≠ {len(names)} — 칸이 붙었거나 빠짐, 이름 붙이기 전 그림 확인')
    for i, b in enumerate(bs):
        nm = names[i] if i < len(names) else f'extra{i}'; p = rgba[b['y0']:b['y1'], b['x0']:b['x1']].copy()
        p[..., 3] = (p[..., 3] * b['mask'][b['y0']:b['y1'], b['x0']:b['x1']]).astype(np.uint8)
        Image.fromarray(p, 'RGBA').save(os.path.join(HERE, 'cut', nm + '.png'))
        ang, L, T = axis_angle(b['mask']); tilt = min(ang, 180 - ang)
        rep['items'][nm] = dict(box=[int(b['x0']), int(b['y0']), int(b['x1'] - b['x0']), int(b['y1'] - b['y0'])], px=b['px'], axisTilt=round(tilt, 1), len=round(L, 1), thick=round(T, 1))
    it = rep['items']
    for nm in STRAIGHT:
        if nm in it and it[nm]['axisTilt'] > 8: rep['fails'].append(f'{nm} 비스듬함 {it[nm]["axisTilt"]}° (곧게 세운 조각이어야 함)')
    if 'weapon' in it:   # 봉 길이 ÷ 굵기: 원화 = 484 / 자루 굵기(원화에서 잰 값은 조립 때) → 여기선 길이 ÷ 머리 폭 비교
        r_ref = (J['staffBottom'][1] - J['staffTop'][1]) / 130.0   # 원화 봉 길이 ÷ 대머리 폭(약 130px)
        if 'head' in it:
            r = it['weapon']['len'] / max(1, it['head']['box'][2] * .62)   # 머리 조각 폭에는 귀가 들어가 0.62 곱(시트 오면 보정)
            rep['weaponRatio'] = round(r / r_ref, 3)
            if abs(r / r_ref - 1) > .05: rep['fails'].append(f'봉 길이 비율 원화 대비 {r / r_ref:.2f}배 (±5% 밖) — 단독 시트 재요청 후보')
    faces = [it[n]['box'] for n in names if n.startswith('face_') and n in it]
    if faces:
        ws = [f[2] for f in faces]; hs = [f[3] for f in faces]
        if (max(ws) - min(ws)) / np.mean(ws) > .08 or (max(hs) - min(hs)) / np.mean(hs) > .08: rep['fails'].append('표정 6장 크기가 다름(±4% 밖) — 머리 각도·크기 확인')
    json.dump(rep, open(os.path.join(HERE, 'cut', '_index.json'), 'w'), ensure_ascii=False, indent=1)
    # 확인 그림: 시트 위에 번호·이름·판정
    ov = Image.new('RGBA', (rgba.shape[1], rgba.shape[0]), (245, 240, 225, 255)); ov.alpha_composite(Image.fromarray(rgba, 'RGBA')); d = ImageDraw.Draw(ov)
    bad = {f.split(' ')[0] for f in rep['fails']}
    for i, b in enumerate(bs):
        nm = names[i] if i < len(names) else f'extra{i}'; c = (220, 30, 30, 255) if nm in bad else (20, 140, 60, 255)
        d.rectangle((b['x0'], b['y0'], b['x1'], b['y1']), outline=c, width=3); d.text((b['x0'] + 4, b['y0'] + 2), f'{i + 1} {nm}', fill=c)
    ov.convert('RGB').save(os.path.join(HERE, 'review', 'overview.png'))
    print(json.dumps({k: rep[k] for k in ['pieces', 'expected', 'rows', 'fails']} | ({'weaponRatio': rep['weaponRatio']} if 'weaponRatio' in rep else {}), ensure_ascii=False, indent=1))
