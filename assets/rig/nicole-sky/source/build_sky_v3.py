"""니콜 스카이 v3 조각 만들기 (2026-10-16)
입력: sheets_v3/ (N 뒷손 3각도+윗팔, F 앞손 3각도, TH 찌름 팔, T 허리 늘린 상체, L 다리)
출력: ../parts/*.png + parts_v3.json (조각마다 쥔 점·자루 방향·팔꿈치·어깨·배율)
실행: cd source && python3 -I build_sky_v3.py
원칙: 자루 토막은 지운다(게임 창이 같은 선 위에 그려짐). 배율 = 주먹 폭 54(원본 48~52) 기준, 창 나무 자루 심 16으로 얇게(원본 19).
"""
import json, os, sys
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from measure import masks
from shaftline import shaft
SH = os.path.join(HERE, 'sheets_v3'); OUT = os.path.join(HERE, '..', 'parts'); TMP = os.path.join(HERE, '_v3tmp')
os.makedirs(TMP, exist_ok=True)

def split(sheet):
    a = np.asarray(Image.open(os.path.join(SH, sheet)).convert('RGB')).astype(float); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    bgc = np.median(a[:8, :8].reshape(-1, 3), 0); s = np.minimum(r, b) - g
    alpha = np.clip((175 - s) / (175 - 95), 0, 1); A = alpha[..., None]
    col = np.clip(np.where(A > .02, (a - (1 - A) * bgc) / np.maximum(A, 1e-3), 0), 0, 255)
    rgba = np.dstack([col, alpha * 255]).astype(np.uint8)
    lab, n = nd.label(nd.binary_dilation(alpha > .5, iterations=3)); out = []
    for i, sl in enumerate(nd.find_objects(lab)):
        m = lab[sl] == i + 1
        if m.sum() < 400: continue
        p = rgba[sl].copy(); p[..., 3] = (p[..., 3] * m).astype(np.uint8); out.append((sl[1].start, sl[0].start, p))
    return out

def save_piece(p, name):
    fn = os.path.join(TMP, name + '.png'); Image.fromarray(p, 'RGBA').save(fn); return fn

def strip_shaft(fn, outname, k, extra):
    """자루 토막(갈색 + 그 바깥 잉크)을 지우고 주먹·팔은 남김. 좌표는 원본 조각 기준 그대로 유지 후 여백 잘라냄."""
    sh = shaft(fn); a, al, brown, skin = masks(fn); A = np.asarray(Image.open(fn).convert('RGBA')).copy()
    H, W = al.shape; yy, xx = np.mgrid[0:H, 0:W]; u = np.array(sh['shaftDir']); n_ = np.array([-u[1], u[0]]); G = np.array(sh['grip'])
    dist = np.abs((xx - G[0]) * n_[0] + (yy - G[1]) * n_[1])
    # 자루 전체 굵기(테두리 포함): 주먹·팔이 없는 열에서 중심선이 지나는 불투명 구간의 길이
    sgn = (xx - G[0]) * n_[0] + (yy - G[1]) * n_[1]; along = (xx - G[0]) * u[0] + (yy - G[1]) * u[1]
    tot = []; fa = along[nd.binary_dilation(skin, iterations=3)].max()
    for t0 in range(int(fa) + 12, 401, 4):
        sel = (np.abs(along - t0) < 1.5) & (np.abs(sgn) < 90)
        if sel.sum() < 10: continue
        if (skin & sel).any(): continue
        o = sgn[sel]; op = al[sel]; order = np.argsort(o); o = o[order]; op = op[order]
        c = np.argmin(np.abs(o)); 
        if not op[c]: continue
        lo = c; hi = c
        while lo > 0 and op[lo - 1]: lo -= 1
        while hi < len(op) - 1 and op[hi + 1]: hi += 1
        tot.append((o[lo], o[hi]))
    tot = np.array(tot); top = float(np.median(tot[:, 0])); bot = float(np.median(tot[:, 1])); mid = (top + bot) / 2
    G = G + n_ * mid; sh['grip'] = [round(float(G[0]), 1), round(float(G[1]), 1)]          # 쥔 점을 자루 실제 가운데로 보정
    sgn = sgn - mid; top -= mid; bot -= mid
    sh['totalBand'] = [round(top, 1), round(bot, 1)]
    band = (sgn >= top - 7) & (sgn <= bot + 7)                                   # 자루 심 + 잉크 테두리 + 여유
    lum = A[..., :3].astype(int).mean(-1); ink = (lum < 55) & al
    r_, g_, b_ = [A[..., i].astype(int) for i in range(3)]
    armcol = al & ~brown & ~skin & ~ink & ~((r_ > g_ + 25) & (g_ > b_) & (lum < 150))   # 은색·금색·남색 (나무색 제외)
    rgb = A[..., :3].astype(float) / 255; mx = rgb.max(-1); mn = rgb.min(-1); dd = np.maximum(mx - mn, 1e-6); sat = (mx - mn) / np.maximum(mx, 1e-6)
    hue = np.where(mx == rgb[..., 0], ((rgb[..., 1] - rgb[..., 2]) / dd) % 6, np.where(mx == rgb[..., 1], (rgb[..., 2] - rgb[..., 0]) / dd + 2, (rgb[..., 0] - rgb[..., 1]) / dd + 4)) * 60
    skinL = al & (hue > 8) & (hue < 42) & (sat > .18) & (sat < .78) & (mx > .55) & ~brown & nd.binary_dilation(skin, iterations=8)   # 그늘진 손가락 끝까지 (나무 밝은 결 제외)
    lbS, nS = nd.label(skinL); szS = np.array(nd.sum(skinL, lbS, range(1, nS + 1))); skinL = lbS == 1 + int(np.argmax(szS))
    fist = nd.binary_fill_holes(nd.binary_closing(skinL | skin, iterations=6))
    # 자루 토막만 지운다 (v3.1): 자루 띠(테두리 포함) 안에서 팔·주먹 색이 아닌 것은 전부 지움.
    #   팔 색 = 피부 · 은색/크림(채도 낮고 밝음) · 금색(노랑 계열 진함) · 남색. 나무색·나무 끝 밝은 결은 팔 색이 아님.
    #   (이전 v3: 색으로 팔을 고르다 금색 그늘이 빠져 TH 팔뚝이 잘리고, 띠 가장자리 잉크 선이 남아 창이 휘어 보였음)
    fistD = nd.binary_dilation(fist, iterations=2)
    bandW = (sgn >= top - 10) & (sgn <= bot + 10)
    silver = (sat < .22) & (mx > .42); gold = (hue >= 36) & (hue <= 62) & (sat > .35) & (mx > .45); navy = (hue >= 190) & (hue <= 270) & (mx > .12)
    armc = al & (silver | gold | navy | fist) & ~brown
    lbA, nA = nd.label(armc | fistD); szA = np.array(nd.sum(armc | fistD, lbA, range(1, nA + 1)))
    armc = armc & np.isin(lbA, np.nonzero(szA >= szA.max() * .05)[0] + 1)            # 띠 속 작은 반짝임 조각은 팔 아님
    protect = nd.binary_dilation(armc | fistD, iterations=2) | (ink & (nd.distance_transform_edt(~(armc | fistD)) <= 5))
    A[..., 3] = np.where(bandW & ~protect, 0, A[..., 3])
    # 남은 가는 선(두께 6px 이하) 정리: 굵은 몸통을 열고 다시 테두리만큼 되돌림
    m0 = A[..., 3] > 20; body = nd.binary_dilation(nd.binary_opening(m0, iterations=3), iterations=4) & m0
    A[..., 3] = np.where(body, A[..., 3], 0)
    m = A[..., 3] > 20; lb, n = nd.label(m); sz = np.array(nd.sum(m, lb, range(1, n + 1)))
    A[..., 3] = np.where(np.isin(lb, np.nonzero(sz >= sz.max() * .02)[0] + 1), A[..., 3], 0)
    ys, xs = np.nonzero(A[..., 3] > 0); x0, y0 = max(0, xs.min() - 4), max(0, ys.min() - 4)
    A = A[y0:ys.max() + 5, x0:xs.max() + 5]
    Image.fromarray(A, 'RGBA').save(os.path.join(OUT, outname + '.png'))
    x0, y0 = int(x0), int(y0); sub = lambda p: [round(float(p[0]) - x0, 1), round(float(p[1]) - y0, 1)]
    d = dict(src=f'parts/{outname}.png', scale=k, grip=sub(sh['grip']), shaftDir=sh['shaftDir'], stubCore=sh['thick'], stubBand=sh['totalBand'], fistW=sh['fistW'])
    for key, v in extra.items(): d[key] = sub(v)
    return d

geo = {}
# ---------- N: 뒷손(가까운 팔) 팔뚝+주먹 3각도 + 윗팔 ----------
N = sorted(split('N.png'), key=lambda t: (t[1] > 600, t[0]))   # 윗줄 왼→오, 아랫줄(윗팔)
kN = .5
nfn = [save_piece(p, f'N_{i}') for i, (_, _, p) in enumerate(N)]
elbN = [(100, 55), (158, 55), (95, 50)]                          # 둥근 팔꿈치 끝의 원 중심 (조각 픽셀, 눈금으로 읽음)
for i in range(3):
    geo[f'handN{i}'] = strip_shaft(nfn[i], f'handN{i}', kN, {'elbow': elbN[i]})
up = N[3][2]; Image.fromarray(up, 'RGBA').save(os.path.join(OUT, 'armU3.png'))
geo['armU3'] = dict(src='parts/armU3.png', scale=kN, shoulder=[55, 85], elbow=[235, 185])
# ---------- F: 앞손(먼 팔) 3각도 ----------
F = sorted(split('F.png'), key=lambda t: t[0]); kF = .335
ffn = [save_piece(p, f'F_{i}') for i, (_, _, p) in enumerate(F)]
elbF = [(100, 160), (90, 170), (90, 200)]
for i in range(3):
    geo[f'handF{i}'] = strip_shaft(ffn[i], f'handF{i}', kF, {'elbow': elbF[i]})
# ---------- TH: 찌른 순간 가까운 팔 한 장 (어깨 갑옷 포함) ----------
TH = split('TH.png'); kT = .30
tfn = save_piece(TH[0][2], 'TH_0')
geo['armTH'] = strip_shaft(tfn, 'armTH', kT, {'shoulder': (150, 165), 'elbow': (185, 300)})
# ---------- T: 허리 늘린 상체 + 주머니(치마 위) ----------
T = split('T.png'); tp = T[0][2]; tfn2 = save_piece(tp, 'T_0')
MT = json.load(open(os.path.join(HERE, 'T_ref.json'))); M = np.array(MT['M']); kT_ = MT['s']   # 조각 → 1024 원본 캔버스(=리그 단위, 원점 500,950)
M1 = M.copy(); M1[:, :2] /= kT_; M1[:, 2] /= kT_                                                   # 회전만 적용한 조각 공간 (배율 kT_로 그림)
h, w = tp.shape[:2]; cs = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]]).T; q = M1 @ cs
ox, oy = q[0].min() - 6, q[1].min() - 6; M1[0, 2] -= ox; M1[1, 2] -= oy; W2, H2 = int(q[0].max() - ox + 12), int(q[1].max() - oy + 12)
def warp(img): return cv2.warpAffine(img, M1, (W2, H2), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
torso = warp(tp); Image.fromarray(torso, 'RGBA').save(os.path.join(OUT, 'torso3.png'))
hip = (np.array([505., 645.]) / kT_ - [ox, oy]).astype(float)                                                        # 엉덩이 뼈(5,-305) = 캔버스(505,645)
geo['torso3'] = dict(src='parts/torso3.png', scale=round(kT_, 4), pivot=[round(float(hip[0]), 1), round(float(hip[1]), 1)])
# 주머니: 실루엣 다각형 ∩ 천(크림·남색) 아닌 픽셀 → 치마 위에 한 번 더 그림
from PIL import ImageDraw
A = tp.astype(int); r, g, b = A[..., 0], A[..., 1], A[..., 2]; lum = A[..., :3].mean(-1)
poly = [(44, 553), (120, 548), (236, 545), (258, 556), (266, 585), (262, 640), (259, 748), (232, 768), (100, 764), (30, 762), (14, 720), (20, 660), (36, 600)]
pm = Image.new('L', (w, h), 0); ImageDraw.Draw(pm).polygon(poly, fill=255); pm = np.asarray(pm) > 0
cloth = ((r > 170) & (g > 150) & (b > 110)) | ((b >= r - 5) & (lum > 45))
m = pm & (A[..., 3] > 10) & ~cloth; m = nd.binary_opening(m, iterations=1); lb, n = nd.label(m); sz = nd.sum(m, lb, range(1, n + 1)); m = nd.binary_fill_holes(lb == 1 + int(np.argmax(sz)))
P = tp.copy(); P[..., 3] = (tp[..., 3] * np.clip(nd.gaussian_filter(m.astype(float), .6) * 1.5 - .25, 0, 1)).astype(np.uint8)
Image.fromarray(warp(P), 'RGBA').save(os.path.join(OUT, 'pouch3.png'))
geo['pouch3'] = dict(src='parts/pouch3.png', scale=round(kT_, 4), pivot=geo['torso3']['pivot'])
# ---------- 창: 나무 자루 줄만 가로로 0.68배 (심 23.4 → 16, 원본 19). 창날·쇠고리는 그대로 ----------
wsrc = np.asarray(Image.open(os.path.join(HERE, 'weapon_v2.png')).convert('RGBA')).copy(); wout = wsrc.copy(); cx = 60.0; f = .68
for y0, y1 in [(320, 366), (392, 805)]:
    for y in range(y0, y1 + 1):
        row = wsrc[y:y + 1].astype(np.float32); Mx = np.array([[f, 0, cx - cx * f], [0, 1, 0]], np.float32)   # dst x = f·src + cx(1−f) → 가운데 기준으로 좁힘
        wout[y] = cv2.warpAffine(row, Mx, (row.shape[1], 1), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))[0].astype(np.uint8)
Image.fromarray(wout, 'RGBA').save(os.path.join(OUT, 'weapon.png'))
geo['weapon'] = dict(axisX=cx, gripRow=347.4, scale=1.1166, woodRows=[[320, 366], [392, 805]], core=round(21 * f * 1.1166, 1))
open(os.path.join(HERE, 'parts_v3.json'), 'w').write(json.dumps(geo, ensure_ascii=False, indent=1))
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ('grip', 'elbow', 'shaftDir', 'stubCore', 'fistW', 'scale', 'shoulder')} for k, v in geo.items() if not k.startswith('_')}, ensure_ascii=False, indent=0))
