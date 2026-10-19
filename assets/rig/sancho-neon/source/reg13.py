# 13 네온 산초: 조각 시트 조각 → 원화 닮음 변환(SIFT, RANSAC) — geom.json (러스트 reg3.py 와 같은 방법)
import json, os, sys, numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
art = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA'))
def gray(a, bg=255):
    g = a[..., :3].astype(np.float32).mean(2); al = a[..., 3] / 255.0; return (g * al + bg * (1 - al)).astype(np.uint8)
sift = cv2.SIFT_create()
def fit(n, ref=art, k=None, region=None, thr=2.5):
    p = np.array(Image.open(os.path.join(HERE, 'pieces', n + '.png')).convert('RGBA')); pad = 30
    pp = np.zeros((p.shape[0] + 2 * pad, p.shape[1] + 2 * pad, 4), np.uint8); pp[pad:-pad, pad:-pad] = p
    k = k or (3 if max(p.shape) < 120 else 1)
    gb = cv2.resize(gray(pp), None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
    ga = gray(ref); ka_s = 2 if k > 1 else 1; gA = cv2.resize(ga, None, fx=ka_s, fy=ka_s, interpolation=cv2.INTER_CUBIC)
    mA = None
    if region is not None: mA = np.zeros(gA.shape, np.uint8); x0, y0, x1, y1 = [v * ka_s for v in region]; mA[y0:y1, x0:x1] = 255
    ka, da = sift.detectAndCompute(gA, mA); kb, db = sift.detectAndCompute(gb, None)
    if db is None or da is None: return None
    mt = cv2.BFMatcher().knnMatch(db, da, k=2); good = [m for m, nn in [x for x in mt if len(x) == 2] if m.distance < .75 * nn.distance]
    if len(good) < 4: return dict(matches=len(good))
    src = np.float32([kb[m.queryIdx].pt for m in good]) / k - pad; dst = np.float32([ka[m.trainIdx].pt for m in good]) / ka_s
    M, inl = cv2.estimateAffinePartial2D(src, dst, ransacReprojThreshold=thr, maxIters=5000)
    if M is None: return dict(matches=len(good))
    w = cv2.warpAffine(p, M.astype(np.float32), (512, 512), flags=cv2.INTER_LINEAR)
    wa = w[..., 3] > 128; aa = art[..., 3] > 128
    return {'M': M.tolist(), 'scale': round(float(np.hypot(M[0, 0], M[1, 0])), 4), 'rotDeg': round(float(np.degrees(np.arctan2(M[1, 0], M[0, 0]))), 2),
            'inliers': int(inl.sum()), 'matches': len(good), 'cover': round(float((wa & aa).sum() / max(1, wa.sum())), 3)}
if __name__ == '__main__':
    names = sys.argv[1:] or ['pose', 'head', 'face_neutral', 'sword', 'torso', 'hips', 'padN', 'padF', 'upperN', 'foreN', 'upperF', 'foreF', 'gNv', 'gFv', 'thighN', 'thighF', 'kneeN', 'kneeF', 'bootN', 'bootF']
    G = json.load(open(os.path.join(HERE, 'geom.json'))) if os.path.exists(os.path.join(HERE, 'geom.json')) else {}
    for n in names:
        r = fit(n); print(n, {k: v for k, v in (r or {}).items() if k != 'M'})
        if r and 'M' in r: G[n] = r
    json.dump(G, open(os.path.join(HERE, 'geom.json'), 'w'), indent=1)
