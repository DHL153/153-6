"""조각 → 기준 그림(ref1024) 닮음변환을 SIFT 특징점 + RANSAC 으로 (가림·배율 편향에 강함).  python3 -I sift_match.py name:roi ..."""
import json, sys, os, numpy as np, cv2
from PIL import Image
def load(fn, k=1):
    a = np.asarray(Image.open(fn).convert('RGBA')).astype(np.float32); al = a[..., 3:4] / 255
    g = cv2.cvtColor((a[..., :3] * al + 255 * (1 - al)).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    if k != 1: g = cv2.resize(g, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
    return g, (a[..., 3] > 128).astype(np.uint8)
REF, RM = load('ref1024.png')
sift = cv2.SIFT_create(nfeatures=4000, contrastThreshold=.02)
def run(name, fn, roi, up=2.0):
    g, m = load(fn); G = cv2.resize(g, None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC); M_ = cv2.resize(m, None, fx=up, fy=up, interpolation=cv2.INTER_NEAREST)
    x0, y0, x1, y1 = roi; R = cv2.resize(REF[y0:y1, x0:x1], None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC); RMk = cv2.resize(RM[y0:y1, x0:x1], None, fx=up, fy=up, interpolation=cv2.INTER_NEAREST)
    k1, d1 = sift.detectAndCompute(G, cv2.erode(M_, np.ones((5, 5), np.uint8))); k2, d2 = sift.detectAndCompute(R, RMk)
    if d1 is None or d2 is None: return None
    mt = cv2.BFMatcher().knnMatch(d1, d2, k=2); good = [a for a, b in mt if a.distance < .78 * b.distance]
    if len(good) < 4: return dict(name=name, n=len(good))
    p1 = np.float32([k1[a.queryIdx].pt for a in good]) / up; p2 = np.float32([k2[a.trainIdx].pt for a in good]) / up + [x0, y0]
    M, inl = cv2.estimateAffinePartial2D(p1, p2, method=cv2.RANSAC, ransacReprojThreshold=3.0, maxIters=5000, confidence=.999)
    if M is None: return dict(name=name, n=len(good))
    ni = int(inl.sum()); s = float(np.hypot(M[0, 0], M[1, 0])); deg = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
    err = float(np.median(np.linalg.norm((p1[inl[:, 0] > 0] @ M[:, :2].T + M[:, 2]) - p2[inl[:, 0] > 0], axis=1))) if ni else 99
    return dict(name=name, file=fn, n=len(good), inliers=ni, s=round(s, 4), deg=round(deg, 2), err=round(err, 2), M=M.tolist())
if __name__ == '__main__':
    jobs = json.load(open(sys.argv[1])); out = {}
    if os.path.exists('sift_result.json'): out = json.load(open('sift_result.json'))
    for name, j in jobs.items():
        r = run(name, j['file'], j['roi']); out[name] = r; print(name, {k: v for k, v in (r or {}).items() if k not in ('M', 'file')})
    json.dump(out, open('sift_result.json', 'w'), indent=1)
