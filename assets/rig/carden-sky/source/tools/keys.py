#!/usr/bin/env python3
"""동작 시트(키 포즈·브레이크다운) → 프레임 분리 + 자세 측정 (18 네온 니콜, 2026-10-17)

python3 keys.py SHEET.png OUT_DIR [--rows 2]
  1) 배경(마젠타 또는 밝은 단색)을 빼고 프레임(캐릭터 덩어리)을 줄·순서대로 나눔 — 창처럼 떨어진 조각은 가장 가까운 몸에 붙임
  2) 프레임마다 측정 (원화 시트 0 기준 리그 단위로 환산 — 머리 폭으로 배율을 맞춤):
     ground(발바닥 선), headTop(머리카락 위), headW(머리 폭), feet(왼·오른 부츠 x), hands(피부색 주먹 덩어리 중심),
     spear(자루 직선: 각도·양 끝), pelvisDrop(서 있을 때 대비 머리 위가 내려간 양)
  3) OUT_DIR/frames/NN.png + keys.json + overview.png (측정점을 그린 확인용)
측정은 '위치를 잰다'까지만 한다. 리그 동작 키에 넣는 일은 compare 단계에서 사람이 그림을 보고 판정한 뒤.
"""
import os, sys, json, math
import cv2
WEAPON = None; S0_HEADW = 1; S0_WEAPON_LEN = 1308
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

def alpha_of(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    corner = np.median(np.concatenate([a[:6, :6].reshape(-1, 3), a[-6:, -6:].reshape(-1, 3)]), 0)
    if corner[0] > 180 and corner[2] > 180 and corner[1] < 90:          # 마젠타
        s = np.minimum(r, b) - g; return np.clip((175 - s) / 80, 0, 1)
    d = np.abs(a - corner).sum(-1); return np.clip((d - 18) / 40, 0, 1)   # 밝은 단색 배경

def hsv(a):
    rgb = a / 255; mx = rgb.max(-1); mn = rgb.min(-1); d = np.maximum(mx - mn, 1e-6); s = (mx - mn) / np.maximum(mx, 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, s, mx

def split(fn, rows=None):
    a = np.asarray(Image.open(fn).convert('RGB')).astype(float); al = alpha_of(a)
    m = al > .5; lab, n = nd.label(nd.binary_dilation(m, iterations=4)); sl = nd.find_objects(lab)
    blobs = [(i + 1, s) for i, s in enumerate(sl) if (lab[s] == i + 1).sum() > 1500]
    big = max((s[0].stop - s[0].start) * (s[1].stop - s[1].start) for _, s in blobs)
    bodies = [(i, s) for i, s in blobs if (s[0].stop - s[0].start) * (s[1].stop - s[1].start) > big * .25]
    small = [(i, s) for i, s in blobs if (i, s) not in bodies]
    owner = {i: i for i, _ in bodies}
    for i, s in small:                                    # 떨어진 조각(창 끝 등) → 가장 가까운 몸
        cy, cx = (s[0].start + s[0].stop) / 2, (s[1].start + s[1].stop) / 2
        best = min(bodies, key=lambda b: (cx - (b[1][1].start + b[1][1].stop) / 2) ** 2 + (cy - (b[1][0].start + b[1][0].stop) / 2) ** 2); owner[i] = best[0]
    frames = []
    for bi, bs in bodies:
        mask = np.isin(lab, [k for k, v in owner.items() if v == bi]) & m
        ys, xs = np.nonzero(mask); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        rgba = np.dstack([a[y0:y1, x0:x1], (al[y0:y1, x0:x1] * mask[y0:y1, x0:x1] * 255)]).astype(np.uint8)
        frames.append(dict(x=int(x0), y=int(y0), cx=(x0 + x1) / 2, cy=(y0 + y1) / 2, bottom=int(y1), img=rgba))
    # 줄 나누기: 바닥 높이로 묶음
    frames.sort(key=lambda f: f['bottom']); groups = []
    for f in frames:
        if groups and abs(f['bottom'] - groups[-1][-1]['bottom']) < 120: groups[-1].append(f)
        else: groups.append([f])
    out = []
    for gi, g in enumerate(sorted(groups, key=lambda g: np.mean([f['bottom'] for f in g]))):
        for f in sorted(g, key=lambda f: f['cx']): f['row'] = gi; out.append(f)
    return out

def measure(img, ref_headW=None, faceW=None):
    a = img[..., :3].astype(float); A = img[..., 3] > 128; H, W = A.shape
    h, s, v = hsv(a); lum = a.mean(-1)
    ys, xs = np.nonzero(A); ground = int(ys.max())
    # 얼굴 = 위쪽 절반의 가장 큰 피부 덩어리 → 머리 = 얼굴 기둥 폭의 절반 이상이 불투명한 가장 위 줄 (가는 창은 걸리지 않음)
    skin = A & (h > 10) & (h < 42) & (s > .2) & (s < .82) & (v > .5)
    lb, n = nd.label(nd.binary_opening(skin, iterations=1)); sz = np.array(nd.sum(skin, lb, range(1, n + 1))) if n else np.array([])
    head = None; face_id = None
    for i in np.argsort(-sz):
        yy, xx = np.nonzero(lb == i + 1)
        if yy.mean() < H * .5: face_id = i + 1; fx0, fx1, fcy = xx.min(), xx.max(), yy.mean(); break
    if face_id:
        fw = fx1 - fx0; cols = A[:, fx0:fx1 + 1].sum(1); rows_ = np.nonzero(cols > fw * .5)[0]
        top = int(rows_.min()) if len(rows_) else int(fcy - fw)
        hw = A[top + int(fw * .35)]; hx = np.nonzero(hw)[0]
        head = dict(top=top, w=int(fw), cx=float((fx0 + fx1) / 2))
    hands = []
    for i in range(1, n + 1):
        if i == face_id: continue
        m = lb == i; k = int(m.sum())
        if k < 60: continue
        yy, xx = np.nonzero(m); hands.append(dict(c=[round(float(xx.mean()), 1), round(float(yy.mean()), 1)], area=k))
    hands = sorted(hands, key=lambda d: -d['area'])[:2]
    # 부츠: 바닥 근처 불투명 열 묶음 2개
    band = A[max(0, ground - int(H * .06)):ground + 1].any(0); xs_ = np.nonzero(band)[0]
    runs = np.split(xs_, np.nonzero(np.diff(xs_) > 6)[0] + 1) if len(xs_) else []
    runs = sorted([r for r in runs if len(r) > W * .07], key=len, reverse=True)[:2]   # 부츠만 (창 끝은 좁아서 빠짐)
    feet = sorted([float((r[0] + r[-1]) / 2) for r in runs])
    spear = None
    if WEAPON is not None and head:   # 창 그림(원화 비율 단독 시트)을 머리 폭 비율로 줄여 각도·위치 탐색 (색 겹침이 가장 작은 곳)
        f = .5; k0 = (faceW or head['w']) / S0_HEADW * S0_WEAPON_LEN / WEAPON.shape[0] * f
        Wp = cv2.resize(WEAPON, None, fx=k0, fy=k0, interpolation=cv2.INTER_AREA).astype(np.float32)
        Fr = cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_AREA).astype(np.float32)
        def rot(deg):
            hh, ww = Wp.shape[:2]; M = cv2.getRotationMatrix2D((ww / 2, hh / 2), deg, 1); c_, s_ = abs(M[0, 0]), abs(M[0, 1]); nw, nh = int(hh * s_ + ww * c_) + 2, int(hh * c_ + ww * s_) + 2
            M[0, 2] += nw / 2 - ww / 2; M[1, 2] += nh / 2 - hh / 2; return cv2.warpAffine(Wp, M, (nw, nh), borderValue=(0, 0, 0, 0)), M
        best = None
        for deg in list(range(-180, 180, 4)):
            T, M = rot(deg); m_ = (T[..., 3] > 200).astype(np.float32)
            pad = ((0, max(0, T.shape[0] - Fr.shape[0] + 2)), (0, max(0, T.shape[1] - Fr.shape[1] + 2)), (0, 0)); Fp = np.pad(Fr, pad)
            r_ = cv2.matchTemplate(Fp[..., :3], T[..., :3], cv2.TM_SQDIFF, mask=np.dstack([m_] * 3)) / max(1, m_.sum())
            mn, _, loc, _ = cv2.minMaxLoc(r_)
            if best is None or mn < best[0]: best = (mn, deg, loc, M, T.shape)
        mn, deg, loc, M, shp = best
        hh, ww = Wp.shape[:2]; P = lambda p: ((M[:, :2] @ np.array(p, float) + M[:, 2]) + loc) / f
        tip = P((ww / 2, 0)); butt = P((ww / 2, hh))
        spear = dict(p1=[round(float(butt[0]), 1), round(float(butt[1]), 1)], p2=[round(float(tip[0]), 1), round(float(tip[1]), 1)],
                     angDeg=round(math.degrees(math.atan2(-(tip[1] - butt[1]), tip[0] - butt[0])), 1), err=round(float(mn), 1))
    k = (ref_headW / (faceW or head['w'])) if (ref_headW and head) else 1.0
    return dict(W=W, H=H, ground=ground, head=head, hands=hands, feet=feet, spear=spear, toRig=round(k, 4))

if __name__ == '__main__':
    sheet, out = sys.argv[1], sys.argv[2]; os.makedirs(os.path.join(out, 'frames'), exist_ok=True)
    REF_HEADW = None   # 아래에서 원화(시트 0)를 같은 방법으로 재서 정함 (얼굴 폭 기준)
    _r = split(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sheets', 'sheet0.png'))[0]; _m = measure(_r['img']); REF_HEADW = _m['head']['w'] * .7675   # 시트0 → 리그 배율 0.7675
    S0_HEADW = _m['head']['w']
    _w = np.asarray(Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cut', 'weaponW.png'))); _a = _w[..., 3] > 128; _ys, _xs = np.nonzero(_a)
    WEAPON = _w[_ys.min():_ys.max() + 1, _xs.min():_xs.max() + 1].copy()
    fr = split(sheet); res = []
    WEAPON_ = WEAPON; WEAPON = None   # 1차: 얼굴 폭만 (모든 프레임 같은 배율로 그려졌다고 보고 중앙값)
    fw = [measure(f['img'])['head'] for f in fr]; FACEW = float(np.median([h['w'] for h in fw if h])); WEAPON = WEAPON_
    for i, f in enumerate(fr):
        Image.fromarray(f['img'], 'RGBA').save(os.path.join(out, 'frames', f'{i:02d}.png'))
        m = measure(f['img'], REF_HEADW, FACEW); m.update(row=f['row'], idx=i); res.append(m)
    # 같은 줄 첫 프레임 대비 머리 위 변화(골반 내려감 근사, 리그 단위)
    for r in set(m['row'] for m in res):
        R = [m for m in res if m['row'] == r]; base = R[0]
        for m in R:
            if m['head'] and base['head']: m['headDrop'] = round(((m['ground'] - m['head']['top']) - (base['ground'] - base['head']['top'])) * -m['toRig'], 1)
    json.dump(res, open(os.path.join(out, 'keys.json'), 'w'), indent=1)
    # 확인 그림
    cols = max(sum(1 for m in res if m['row'] == r) for r in set(m['row'] for m in res)); cw, chh = 320, 360
    o = Image.new('RGB', (cw * cols, chh * (max(m['row'] for m in res) + 1)), (255, 255, 255)); d = ImageDraw.Draw(o)
    cnt = {}
    for m, f in zip(res, fr):
        j = cnt.get(m['row'], 0); cnt[m['row']] = j + 1
        im = Image.fromarray(f['img'], 'RGBA'); sc = min((cw - 10) / im.width, (chh - 30) / im.height); im2 = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))))
        X, Y = j * cw + 5, m['row'] * chh + 25; bg = Image.new('RGBA', im2.size, (250, 244, 214, 255)); bg.alpha_composite(im2); o.paste(bg.convert('RGB'), (X, Y))
        P = lambda p: (X + p[0] * sc, Y + p[1] * sc)
        d.line([P((0, m['ground'])), P((m['W'], m['ground']))], fill=(120, 120, 120))
        if m['head']: d.line([P((0, m['head']['top'])), P((m['W'], m['head']['top']))], fill=(0, 160, 255))
        for hnd in m['hands']: x, y = P(hnd['c']); d.ellipse([x - 4, y - 4, x + 4, y + 4], outline=(255, 0, 0), width=2)
        for fx in m['feet']: x, y = P((fx, m['ground'])); d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(0, 170, 0))
        if m['spear']: d.line([P(m['spear']['p1']), P(m['spear']['p2'])], fill=(255, 0, 200), width=2)
        d.text((X, m['row'] * chh + 4), f"#{m['idx']} 창{m['spear']['angDeg'] if m['spear'] else '-'}° 머리↓{m.get('headDrop', '-')}", fill=(0, 0, 0))
    o.save(os.path.join(out, 'overview.png')); print(len(res), 'frames →', out)
