#!/usr/bin/env python3
"""6 카르덴 동작 시트(4×4 같은 칸, 흰 배경, 칸마다 땅선) → 프레임 분리 + 관절점 측정 (2026-10-17 23:00 준비)
python3 -I keys6.py SHEET.png [OUT_DIR=motion] [--grid 4x4] [--n 14]
  1) 칸 나누기: 같은 크기 격자. 칸마다 배경(모서리 색)을 빼고, 가로로 긴 얇은 줄(땅선)·작은 덩어리(칸 번호)는 지움 → 땅선 y 는 따로 기록
  2) 배율: 봉 조각(cut/weapon.png)을 회전·크기 맞춤으로 찾음. 서 있는 칸(9번)에서 크기를 정하고(봉 = 원화 484px = 리그 968) 모든 칸에 같은 크기
  3) 칸마다: 땅(그린 땅선, 없으면 부츠 바닥) · 두 발 x(부츠 바닥 덩어리) · 머리 위(가장 큰 살색 덩어리 = 대머리+얼굴의 맨 위) ·
     봉(양 끝: 링 머리 / 집게, 각도) · 주먹(어두운 갈색 장갑 덩어리 중 봉 선 가까운 것)
  4) OUT/frames/sNN.png (cmpkeys 용, 땅 = 그림 맨 아래) + keys6.json + overview6.png (측정점 표시 — 사람이 보고 판정)
리그 단위: x = 두 발 가운데 기준, y = 땅 0, 위가 −. 측정은 '잰다'까지만, 키 판정은 그림을 보고.
"""
import json, math, os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
STAFF_RIG = 968.0                                    # 원화 봉 484px × 2

def hsv(a):
    rgb = a[..., :3] / 255; mx = rgb.max(-1); mn = rgb.min(-1); d = np.maximum(mx - mn, 1e-6); s = (mx - mn) / np.maximum(mx, 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, s, mx

def cells(fn, gx, gy, n):
    a = np.asarray(Image.open(fn).convert('RGB')).astype(float); H, W = a.shape[:2]; cw, ch = W / gx, H / gy; out = []
    for i in range(n):
        x0, y0 = int(round((i % gx) * cw)), int(round((i // gx) * ch)); c = a[y0:int(round(y0 + ch)), x0:int(round(x0 + cw))]
        bg = np.median(np.concatenate([c[:8, :8].reshape(-1, 3), c[:8, -8:].reshape(-1, 3), c[-8:, -8:].reshape(-1, 3)]), 0)
        al = np.clip((np.abs(c - bg).sum(-1) - 24) / 40, 0, 1); m = al > .5
        # 땅선: 칸 폭 55% 이상 이어진 얇은 가로 줄
        gl = None; rows = m.sum(1)
        for y in np.nonzero(rows > c.shape[1] * .55)[0]:
            band = m[max(0, y - 4):y + 5]
            if band.sum(1).max() > c.shape[1] * .55 and (m[max(0, y - 12):y + 13].sum(1) > c.shape[1] * .55).sum() <= 8: gl = int(y) if gl is None else max(gl, int(y))   # 가장 아래 얇은 줄(가로 봉은 굵어서 빠짐)
        if gl is not None:
            th = np.nonzero(m.sum(1) > c.shape[1] * .55)[0]; th = th[np.abs(th - gl) <= 8]
            for y in th: al[y] = np.where(m[y], 0, al[y])      # 땅선만 지움(캐릭터가 덮은 곳은 같이 지워지지만 2~6줄이라 무시)
            gl = int(th.max())
        m = al > .5; lb, k = nd.label(nd.binary_dilation(m, iterations=3)); sz = nd.sum(m, lb, range(1, k + 1))
        keep = [j + 1 for j in range(k) if sz[j] >= max(400, sz.max() * .02)]   # 칸 번호·티끌 제외
        m &= np.isin(lb, keep); al = al * m
        ys, xs = np.nonzero(m); bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
        out.append(dict(i=i, x0=x0, y0=y0, img=np.dstack([c, al * 255]).astype(np.uint8), box=[int(bx0), int(by0), int(bx1), int(by1)], groundLine=gl))
    return out

WEAPON = None
def load_weapon():
    w = np.asarray(Image.open(os.path.join(SRC, 'cut', 'weapon.png')).convert('RGBA')).astype(np.float32); ys, xs = np.nonzero(w[..., 3] > 128)
    return w[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

def find_staff(img, scale=None, angs=None, f=.5):
    """봉 찾기: 크기 scale(시트 px / 봉 조각 px), 각도(도, 0 = 링 머리 위). 반환 dict(head, claw, angDeg, scale, err)"""
    Fr = cv2.resize(img.astype(np.float32), None, fx=f, fy=f, interpolation=cv2.INTER_AREA); Fr[..., :3] *= Fr[..., 3:] / 255
    best = None
    for s in ([scale] if scale else np.exp(np.linspace(np.log(.25), np.log(2.5), 40))):
        Wp = cv2.resize(WEAPON, None, fx=s * f, fy=s * f, interpolation=cv2.INTER_AREA); Wp[..., :3] *= Wp[..., 3:] / 255
        if Wp.shape[0] > max(Fr.shape[:2]) * 1.05 or Wp.shape[0] < 20: continue
        for deg in (angs if angs is not None else range(-180, 180, 3)):
            hh, ww = Wp.shape[:2]; M = cv2.getRotationMatrix2D((ww / 2, hh / 2), -deg, 1); c_, s_ = abs(M[0, 0]), abs(M[0, 1]); nw, nh = int(hh * s_ + ww * c_) + 2, int(hh * c_ + ww * s_) + 2
            M[0, 2] += nw / 2 - ww / 2; M[1, 2] += nh / 2 - hh / 2; T = cv2.warpAffine(Wp, M, (nw, nh), borderValue=(0, 0, 0, 0))
            mk = (T[..., 3] > 200).astype(np.float32)
            if mk.sum() < 30: continue
            pad = ((0, max(0, nh - Fr.shape[0] + 2)), (0, max(0, nw - Fr.shape[1] + 2)), (0, 0)); Fp = np.pad(Fr, pad)
            r_ = cv2.matchTemplate(Fp[..., :3], T[..., :3], cv2.TM_SQDIFF, mask=np.dstack([mk] * 3)) / mk.sum()
            # 봉이 없는 곳(배경)에 맞춰지는 것 방지: 겹친 곳 불투명도 평균이 낮으면 벌점
            mn, _, loc, _ = cv2.minMaxLoc(r_)
            cover = (Fp[loc[1]:loc[1] + nh, loc[0]:loc[0] + nw, 3] > 128)[:mk.shape[0], :mk.shape[1]]
            cov = float((cover * (mk > 0)).sum() / mk.sum()); sc = mn + (1 - cov) * 20000
            if best is None or sc < best[0]: best = (sc, s, deg, loc, M, (hh, ww), cov)
    sc, s, deg, loc, M, (hh, ww), cov = best
    P = lambda p: (M[:, :2] @ np.array(p, float) + M[:, 2] + loc) / f
    head, claw = P((ww / 2, 0)), P((ww / 2, hh))
    return dict(head=[round(float(head[0]), 1), round(float(head[1]), 1)], claw=[round(float(claw[0]), 1), round(float(claw[1]), 1)],
                angDeg=round(math.degrees(math.atan2(-(head[1] - claw[1]), head[0] - claw[0])), 1), scale=round(float(s), 4), err=round(float(sc), 1), cover=round(cov, 2))

def staff_line(c, exp_len):
    """봉 = 칸에서 가장 긴 곧은 선(자루). 캐니 + 확률 허프 → 가장 긴 선 방향, 그 방향 좁은 띠의 불투명 픽셀 양 끝 = 봉 양 끝.
    링 머리 쪽 = 띠 끝 중 폭이 넓은 쪽(링 3개)."""
    img = c['img']; A = (img[..., 3] > 128).astype(np.uint8); g = cv2.cvtColor(img[..., :3], cv2.COLOR_RGB2GRAY); g[A == 0] = 255
    e = cv2.Canny(g, 60, 160); L = cv2.HoughLinesP(e, 1, np.pi / 360, 60, minLineLength=int(exp_len * .25), maxLineGap=12)
    if L is None: return None
    L = sorted([tuple(int(v) for v in l) for l in L.reshape(-1, 4)], key=lambda l: -np.hypot(l[2] - l[0], l[3] - l[1]))[:6]
    us = []
    for l in L:
        u = np.array([l[2] - l[0], l[3] - l[1]], float); u /= np.linalg.norm(u); us.append((u, np.array(l[:2], float)))
    u, p = us[0]; ys, xs = np.nonzero(A); P = np.c_[xs, ys].astype(float); nrm = np.array([-u[1], u[0]])
    # 띠 가운데: 가장 긴 두 선(자루 양 테두리) 가운데로
    off = [((q - p) @ nrm) for (v, q) in us if abs(v @ u) > .995]; mid = p + nrm * (np.median(off) if off else 0)
    d = (P - mid) @ nrm; t = (P - mid) @ u; band = np.abs(d) < exp_len * .09
    tb = np.round(t[band]).astype(int); lo, hi = np.percentile(tb, .3), np.percentile(tb, 99.7)
    wid = lambda a, b: np.ptp(d[band][(tb >= a) & (tb <= b)]) if ((tb >= a) & (tb <= b)).any() else 0
    E1, E2 = mid + u * lo, mid + u * hi; seg = (hi - lo) * .22
    head, claw = (E2, E1) if wid(hi - seg, hi) >= wid(lo, lo + seg) else (E1, E2)
    # 링 머리는 더 넓고 덩어리짐 → 띠 안 폭(가까운 픽셀 수)으로 판정
    cnt = lambda a, b: int(((tb >= a) & (tb <= b)).sum())
    head, claw = (E2, E1) if cnt(hi - seg, hi) >= cnt(lo, lo + seg) else (E1, E2)
    head = head + [c['x0'], c['y0']]; claw = claw + [c['x0'], c['y0']]
    return dict(head=[round(float(head[0]), 1), round(float(head[1]), 1)], claw=[round(float(claw[0]), 1), round(float(claw[1]), 1)],
                angDeg=round(math.degrees(math.atan2(-(head[1] - claw[1]), head[0] - claw[0])), 1), len=round(float(hi - lo), 1), scale=1, cover=1)

def measure(c, staff):
    img = c['img']; a = img[..., :3].astype(float); A = img[..., 3] > 128; H, W = A.shape; h, s, v = hsv(a)
    ys, xs = np.nonzero(A); ground = c['groundLine'] if c['groundLine'] is not None else int(ys.max())
    # 발: 땅 위 8% 띠의 불투명 열 묶음 (봉 집게처럼 좁은 것은 빠짐)
    bh = int(max(8, (ground - ys.min()) * .08)); band = A[max(0, ground - bh):ground + 1].any(0); xs_ = np.nonzero(band)[0]
    runs = np.split(xs_, np.nonzero(np.diff(xs_) > 6)[0] + 1) if len(xs_) else []
    runs = sorted([r for r in runs if len(r) > W * .035], key=len, reverse=True)[:2]; feet = sorted([float((r[0] + r[-1]) / 2) for r in runs])
    # 머리: 가장 큰 살색 덩어리(대머리·얼굴·코), 맨 위 = 머리 위
    skin = A & (h > 12) & (h < 38) & (s > .3) & (s < .8) & (v > .55)
    lb, n = nd.label(nd.binary_opening(skin, iterations=1)); head = None
    if n:
        sz = nd.sum(skin, lb, range(1, n + 1)); j = int(np.argmax(sz)) + 1; yy, xx = np.nonzero(lb == j)
        head = dict(top=int(yy.min()), cx=float(xx[yy < yy.min() + 6].mean()), area=int(sz[j - 1]))
    # 주먹: 어두운 갈색 장갑(명도 낮음) 덩어리 중 봉 선에서 가까운 것
    glove = A & (v < .36) & (v > .08) & (s > .18) & (h > 5) & (h < 45)
    p1, p2 = np.array(staff['claw']) - [c['x0'], c['y0']], np.array(staff['head']) - [c['x0'], c['y0']]; u = (p2 - p1) / max(1e-6, np.linalg.norm(p2 - p1)); nrm = np.array([-u[1], u[0]])
    lb, n = nd.label(nd.binary_opening(glove, iterations=2)); fists = []
    for j in range(1, n + 1):
        yy, xx = np.nonzero(lb == j)
        if len(yy) < 120: continue
        cc = np.array([xx.mean(), yy.mean()]); d_ = abs((cc - p1) @ nrm); t_ = (cc - p1) @ u
        if d_ < 30 * max(1, staff['scale']) and -20 < t_ < np.linalg.norm(p2 - p1) + 20 and cc[1] < ground - (ground - ys.min()) * .2: fists.append(dict(c=[round(float(cc[0]), 1), round(float(cc[1]), 1)], t=round(float(t_), 1), area=len(yy)))
    fists = sorted(fists, key=lambda d: -d['t'])[:2]   # 링 머리 쪽(앞손)이 먼저
    return dict(ground=int(ground), feet=feet, head=head, fists=fists, W=W, H=H)

if __name__ == '__main__':
    args = [x for x in sys.argv[1:] if not x.startswith('--')]; sheet = args[0]; out = args[1] if len(args) > 1 else HERE
    gx, gy = (map(int, sys.argv[sys.argv.index('--grid') + 1].split('x')) if '--grid' in sys.argv else (4, 4)); n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 14
    STAND = int(sys.argv[sys.argv.index('--stand') + 1]) if '--stand' in sys.argv else 8   # 서 있는 칸(0부터) — 배율 기준
    os.makedirs(os.path.join(out, 'frames'), exist_ok=True); WEAPON = load_weapon()
    C = cells(sheet, gx, gy, n)
    # 배율: 서 있는 칸의 대머리 위 ~ 땅 = 원화 (500−152)×2 = 696 리그 단위 (봉 맞춤은 작은 크기로 쏠려서 안 씀, 23:00 확인)
    m0 = measure(C[STAND], dict(head=[0, 0], claw=[0, 1], scale=1)); toRig = 696.0 / (m0['ground'] - m0['head']['top']); SCALE = 1
    EXP = STAFF_RIG / toRig
    res = []
    for c in C:
        st = staff_line(c, EXP)
        m = measure(c, st); G = m['ground']; mid = (m['feet'][0] + m['feet'][-1]) / 2 if m['feet'] else c['img'].shape[1] / 2
        R = lambda x, y: [round((x - mid) * toRig, 1), round((y - G) * toRig, 1)]
        loc = lambda p: R(p[0] - c['x0'], p[1] - c['y0'])
        rig = dict(half=round(abs(m['feet'][-1] - m['feet'][0]) / 2 * toRig, 1) if len(m['feet']) > 1 else 0.0,
                   head=R(m['head']['cx'], m['head']['top']) if m['head'] else None, staffHead=loc(st['head']), staffClaw=loc(st['claw']), angDeg=st['angDeg'],
                   fists=[R(*f['c']) for f in m['fists']])
        if len(rig['fists']) == 2: rig['handsGap'] = round(float(np.hypot(*(np.array(rig['fists'][0]) - rig['fists'][1]))), 1)
        res.append(dict(idx=c['i'], staff=st, meas=m, rig=rig))
        A_ = c['img'][..., 3] > 128; ys, xs = np.nonzero(A_); fr = c['img'][ys.min():G + 1, xs.min():xs.max() + 1]   # 위 빈 줄 없이, 아래 = 땅
        Image.fromarray(fr, 'RGBA').save(os.path.join(out, 'frames', f's{c["i"]:02d}.png'))
    json.dump(dict(toRig=round(toRig, 4), staffScale=SCALE, frames=res), open(os.path.join(out, 'keys6.json'), 'w'), indent=1)
    # 확인 그림: 칸마다 측정점
    cw, chh = 360, 340; o = Image.new('RGB', (cw * gx, chh * gy), 'white'); d = ImageDraw.Draw(o)
    for r_, c in zip(res, C):
        im = Image.fromarray(c['img'], 'RGBA'); sc = min((cw - 10) / im.width, (chh - 24) / im.height); im2 = im.resize((int(im.width * sc), int(im.height * sc)))
        X, Y = (c['i'] % gx) * cw + 5, (c['i'] // gx) * chh + 20; bg = Image.new('RGBA', im2.size, (250, 244, 214, 255)); bg.alpha_composite(im2); o.paste(bg.convert('RGB'), (X, Y))
        P = lambda p: (X + p[0] * sc, Y + p[1] * sc); m = r_['meas']; st = r_['staff']
        d.line([P((0, m['ground'])), P((m['W'], m['ground']))], fill=(120, 120, 120))
        if m['head']: x, y = P((m['head']['cx'], m['head']['top'])); d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(0, 140, 255))
        for fx in m['feet']: x, y = P((fx, m['ground'])); d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(0, 170, 0))
        d.line([P((st['claw'][0] - c['x0'], st['claw'][1] - c['y0'])), P((st['head'][0] - c['x0'], st['head'][1] - c['y0']))], fill=(255, 0, 200), width=2)
        x, y = P((st['head'][0] - c['x0'], st['head'][1] - c['y0'])); d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(255, 0, 200), width=2)
        for k_, f_ in enumerate(m['fists']): x, y = P(f_['c']); d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(255, 0, 0) if k_ == 0 else (255, 150, 0), width=3)
        d.text((X, (c['i'] // gx) * chh + 3), f"#{c['i'] + 1} 봉 {st['angDeg']}° 덮임{st['cover']} 주먹{len(m['fists'])}", fill=(0, 0, 0))
    o.save(os.path.join(out, 'overview6.png')); print(len(res), 'frames toRig', round(toRig, 3), '→', out)
