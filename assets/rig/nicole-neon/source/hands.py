"""쥔 손 조각 다듬기 (18 네온, 2026-10-17)
- 자루 중심선: 주먹이 없는 줄(가로 토막=열, 세로 토막=행)의 불투명 구간 가운데를 직선 맞춤
- 자루 띠(굵기/2 + 2px) 안에서 주먹(피부 + 외곽선 4px)이 아닌 것은 전부 지움 → 게임 창이 같은 선에 그려짐
- fist_only=True: 주먹만 남김(8 니콜 handL/fistF 방식 — 팔뚝은 foreF 가 그림)
결과: parts_work/<이름>.png + 측정값(dict)"""
import os, json
import numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'parts_work'); os.makedirs(OUT, exist_ok=True)

def hsv(a):
    rgb = a[..., :3] / 255; mx = rgb.max(-1); mn = rgb.min(-1); d = np.maximum(mx - mn, 1e-6); s = (mx - mn) / np.maximum(mx, 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, s, mx

def skin_mask(a):
    h, s, v = hsv(a.astype(float)); al = a[..., 3] > 128
    m = al & (h > 10) & (h < 42) & (s > .2) & (s < .82) & (v > .5)
    lb, n = nd.label(m); sz = np.array(nd.sum(m, lb, range(1, n + 1))); big = 1 + int(np.argmax(sz))
    near = nd.binary_dilation(lb == big, iterations=12)
    keepL = [i + 1 for i in range(n) if sz[i] >= sz.max() * .03 and (near & (lb == i + 1)).any()]   # 엄지처럼 외곽선으로 갈라진 피부 덩어리도 포함
    m = np.isin(lb, keepL)
    return nd.binary_fill_holes(nd.binary_closing(m, iterations=3))

def shaft_axis(a, skin, vertical):
    al = a[..., 3] > 128; H, W = al.shape; pts = []; wid = []
    skinD = nd.binary_dilation(skin, iterations=6)
    rng = range(H) if vertical else range(W)
    for i in rng:
        col = al[i, :] if vertical else al[:, i]; sk = skinD[i, :] if vertical else skinD[:, i]
        if sk.any(): continue
        idx = np.nonzero(col)[0]
        if len(idx) < 10: continue
        runs = np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1)
        for r in runs:
            w = r[-1] - r[0] + 1
            if 18 <= w <= 48: pts.append((i, (r[0] + r[-1]) / 2)); wid.append(w)
    pts = np.array(pts, float); wid = np.array(wid, float)
    # 직선: c = k*i + b (세로면 x = k*y + b, 가로면 y = k*x + b); 이상치 제거
    ok = np.abs(wid - np.median(wid)) < 5
    for _ in range(3):
        A = np.c_[pts[ok, 0], np.ones(ok.sum())]; k, b = np.linalg.lstsq(A, pts[ok, 1], rcond=None)[0]
        res = np.abs(pts[:, 1] - (k * pts[:, 0] + b)); ok &= res < max(1.5, 3 * np.median(res[ok]))
    th = float(np.median(wid[ok])) / np.sqrt(1 + k * k)
    if vertical: P0 = np.array([b, 0.]); U = np.array([k, 1.])
    else: P0 = np.array([0., b]); U = np.array([1., k])
    U /= np.linalg.norm(U)
    return P0, U, th, int(ok.sum())

def process(name, vertical, fist_only, flipU=False, keep_extra=None, full_band=True):
    a = np.asarray(Image.open(os.path.join(HERE, 'cut', name + '.png')).convert('RGBA')).copy(); al = a[..., 3] > 20
    skin = skin_mask(a); P0, U, th, n = shaft_axis(a, skin, vertical)
    if vertical and U[1] > 0: U = -U        # 세로 토막: 자루 방향 = 위(집게 쪽)
    if not vertical and U[0] < 0: U = -U    # 가로 토막: 오른쪽(집게 쪽)
    H, W = al.shape; yy, xx = np.mgrid[0:H, 0:W]; N = np.array([-U[1], U[0]])
    sgn = (xx - P0[0]) * N[0] + (yy - P0[1]) * N[1]
    band = np.abs(sgn) <= th / 2 + 2.5
    mode_full_band = full_band
    fistP = nd.binary_dilation(skin, iterations=4)
    t = (xx - P0[0]) * U[0] + (yy - P0[1]) * U[1]
    # 자루만 있는 구간(앞·뒤 끝): 축을 따라 불투명 폭이 자루 굵기 + 6 이하인 t 범위 중 양 끝과 이어진 부분
    tb = np.round(t).astype(int); tmin, tmax = tb[al].min(), tb[al].max(); ext = {}
    for tv in range(tmin, tmax + 1):
        sel = al & (tb == tv)
        if sel.any(): o = sgn[sel]; ext[tv] = o.max() - o.min()
    stubT = set(); 
    for rng_ in (range(tmin, tmax + 1), range(tmax, tmin - 1, -1)):
        for tv in rng_:
            if tv in ext and ext[tv] <= th + 6: stubT.add(tv)
            else: break
    stub = band & np.isin(tb, list(stubT))
    if not full_band:   # 뒷팔: 자루가 소매 앞을 지나는 구간(뒤쪽 토막 끝 ~ 팔 보호대 테 시작)도 비움 → 게임 창이 그 자리에 보임
        h_, s_, v_ = hsv(a.astype(float)); light = al & (s_ < .25) & (v_ > .7)
        tl = max([tv for tv in stubT if tv < (tmin + tmax) / 2] or [tmin])
        gs = None
        for tv in range(tl + 1, tmax):
            sel = band & (tb == tv)
            if (light & sel).sum() >= 4: gs = tv; break
        if gs: stub |= band & (tb > tl) & (tb < gs - 1)
    keep = ~(stub | (band & ~fistP & mode_full_band))
    if fist_only:
        # 주먹만: 피부를 외곽선 두께(4px)만큼 키운 뒤, 가는 잔선(자루 테두리 조각)은 열기로 깎음 → 매끈한 주먹 실루엣 (2026-10-17 확대 검수에서 조각 발견)
        disk = lambda r: (lambda y, x: x * x + y * y <= r * r)(*np.mgrid[-r:r + 1, -r:r + 1])
        import cv2
        sk = nd.binary_closing(skin, structure=disk(3)).astype(np.uint8); cnts, _ = cv2.findContours(sk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        hull = np.zeros_like(sk); cv2.fillPoly(hull, [cv2.convexHull(np.vstack(cnts))], 1)
        lum = a[..., :3].astype(int).mean(-1); h_, s_, v_ = hsv(a.astype(float))
        shaftc = al & (s_ < .25) & (lum >= 42)                     # 자루 회색·흰 띠
        keep = nd.binary_dilation(hull.astype(bool), structure=disk(4)) & ~(shaftc & ~hull.astype(bool))   # 주먹 = 피부 볼록 껍질 + 외곽선 4px, 껍질 밖 자루색은 뺌
    a[..., 3] = np.where(keep, a[..., 3], 0)
    # 가는 잔선 정리 + 작은 덩어리 제거
    m0 = a[..., 3] > 20; body = nd.binary_dilation(nd.binary_opening(m0, iterations=2), iterations=3) & m0
    a[..., 3] = np.where(body, a[..., 3], 0)
    m = a[..., 3] > 20; lb, nn = nd.label(m); sz = nd.sum(m, lb, range(1, nn + 1)); a[..., 3] = np.where(np.isin(lb, np.nonzero(sz >= sz.max() * .05)[0] + 1), a[..., 3], 0)
    sy, sx = np.nonzero(skin); fc = np.array([sx.mean(), sy.mean()]); G = P0 + U * ((fc - P0) @ U)
    ys, xs = np.nonzero(a[..., 3] > 0); x0, y0 = int(max(0, xs.min() - 3)), int(max(0, ys.min() - 3))
    a = a[y0:ys.max() + 4, x0:xs.max() + 4]
    Image.fromarray(a, 'RGBA').save(os.path.join(OUT, name + '.png'))
    off = np.array([x0, y0], float)
    return dict(file=f'parts_work/{name}.png', grip=(G - off).round(1).tolist(), shaftDir=U.round(4).tolist(), thick=round(th, 1), axisPts=n,
                fistC=(fc - off).round(1).tolist(), off=off.tolist(), fistW=int(np.ptp(sx)))
if __name__ == '__main__':
    R = {}
    R['handL'] = process('handL', False, True)
    R['handR'] = process('handR', False, False, full_band=False)
    R['fistF'] = process('fistF', True, True)
    json.dump(R, open(os.path.join(HERE, 'hands.json'), 'w'), indent=1); print(json.dumps(R, indent=0))

def process2(name, keep_left=False):
    """쥔 손 2차 시트(2026-10-17 14:14, 자루 수평): 자루 축 = 양 끝 자루만 있는 기둥의 위·아래 테 가운데(수평 고정),
    손 = 피부 ∪ 밝은 장갑(흰 테·금 단추) 볼록 껍질 + 외곽선 4px. 자루 띠에서 손 밖은 지움(keep_left: 왼쪽 자루는 남김 — 팔뚝 뒤로 지나가는 자루)"""
    import cv2
    a = np.asarray(Image.open(os.path.join(HERE, 'cut', name + '.png')).convert('RGBA')).copy(); al = a[..., 3] > 128; H, W = al.shape
    skin = skin_mask(a); sy, sx = np.nonzero(skin)
    cols = [x for x in list(range(2, 12)) + list(range(W - 12, W - 2)) if al[:, x].any()]
    tops = [np.nonzero(al[:, x])[0].min() for x in cols]; bots = [np.nonzero(al[:, x])[0].max() for x in cols]
    rx = [x for x in range(sx.max() + 6, W - 2) if al[:, x].any()]
    ty = np.median([np.nonzero(al[:, x])[0].min() for x in rx]); by = np.median([np.nonzero(al[:, x])[0].max() for x in rx])
    cy = (ty + by) / 2; th = by - ty + 1; P0 = np.array([0., cy]); U = np.array([1., 0.])
    h_, s_, v_ = hsv(a.astype(float)); light = al & (s_ < .3) & (v_ > .72); gold = al & (h_ > 35) & (h_ < 60) & (s_ > .5) & (v_ > .55)
    skin = skin & ~nd.binary_dilation(gold | light, iterations=3); sy, sx = np.nonzero(skin)   # 금 단추·흰 테가 피부로 잡히지 않게
    yy0 = np.mgrid[0:H, 0:W][0]; bandL = np.abs(yy0 - cy) <= th / 2 + 3   # 자루 위 밝은 반사는 손이 아님
    hand = (skin | ((light | gold) & ~bandL)).astype(np.uint8); hand = nd.binary_opening(hand, iterations=1).astype(np.uint8)
    cnts, _ = cv2.findContours(hand, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cnts = [c for c in cnts if cv2.contourArea(c) > 30]
    hull = np.zeros_like(hand); cv2.fillPoly(hull, [cv2.convexHull(np.vstack(cnts))], 1)
    disk = lambda r: (lambda y, x: x * x + y * y <= r * r)(*np.mgrid[-r:r + 1, -r:r + 1])
    hullD = nd.binary_dilation(hull.astype(bool), structure=disk(4))
    yy, xx = np.mgrid[0:H, 0:W]; band = np.abs(yy - cy) <= th / 2 + 2.5
    drop = band & ~hullD
    if keep_left: drop &= xx > sx.mean()
    else:   # 주먹 왼쪽 자루 토막(장갑 테 위)도 지움 — 테(밝은 장갑·금 단추)는 남김
        cuff = nd.binary_dilation((light | gold) & ~bandL, iterations=2); drop |= band & (xx < sx.min() - 2) & ~cuff & ~nd.binary_dilation(skin, iterations=7)
    a[..., 3] = np.where(drop, 0, a[..., 3])
    m = a[..., 3] > 20; lb, nn = nd.label(m); sz = nd.sum(m, lb, range(1, nn + 1)); a[..., 3] = np.where(np.isin(lb, np.nonzero(sz >= sz.max() * .05)[0] + 1), a[..., 3], 0)
    fc = np.array([sx.mean(), sy.mean()]); G = np.array([fc[0], cy])
    ys, xs = np.nonzero(a[..., 3] > 0); x0, y0 = int(max(0, xs.min() - 3)), int(max(0, ys.min() - 3))
    a = a[y0:ys.max() + 4, x0:xs.max() + 4]; Image.fromarray(a, 'RGBA').save(os.path.join(OUT, name + '.png')); off = np.array([x0, y0], float)
    return dict(file=f'parts_work/{name}.png', grip=(G - off).round(1).tolist(), shaftDir=[1.0, 0.0], thick=round(float(th), 1), axisPts=len(rx),
                fistC=(fc - off).round(1).tolist(), off=off.tolist(), fistW=int(np.ptp(sx)))
