# 3 러스트 산초: 조각 시트 조각 → 원화 닮음 변환(SIFT + ECC) — geom.json
import json, os, numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
art = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA'))
def gray(a, bg=255):
    g = a[..., :3].astype(np.float32).mean(2); al = a[..., 3] / 255.0; return (g * al + bg * (1 - al)).astype(np.uint8)
ga = gray(art); sift = cv2.SIFT_create(); ka, da = sift.detectAndCompute(ga, None)
G = {}
for n in ['sword', 'head', 'face_neutral', 'torso', 'pauldronF', 'pose']:
    p = np.array(Image.open(os.path.join(HERE, 'pieces', n + '.png')).convert('RGBA')); pad = 30
    pp = np.zeros((p.shape[0] + 2 * pad, p.shape[1] + 2 * pad, 4), np.uint8); pp[pad:-pad, pad:-pad] = p
    k = 3 if max(p.shape) < 120 else 1
    gb = cv2.resize(gray(pp), None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
    kb, db = sift.detectAndCompute(gb, None); mt = cv2.BFMatcher().knnMatch(db, da, k=2); good = [m for m, nn in mt if m.distance < .75 * nn.distance]
    src = np.float32([kb[m.queryIdx].pt for m in good]) / k - pad; dst = np.float32([ka[m.trainIdx].pt for m in good])
    M, inl = cv2.estimateAffinePartial2D(src, dst, ransacReprojThreshold=2.5, maxIters=5000)
    # ECC 다듬기 (조각 알파 안에서)
    w = cv2.warpAffine(pp, np.c_[M[:, :2], M[:, 2] + M[:, :2] @ np.array([-pad, -pad], float)].astype(np.float32), (512, 512), flags=cv2.INTER_LINEAR)
    s = float(np.hypot(M[0, 0], M[1, 0])); r = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
    G[n] = {'M': M.tolist(), 'scale': round(s, 4), 'rotDeg': round(r, 2), 'inliers': int(inl.sum()), 'matches': len(good)}
    # 겹침 점수: 원화 알파와 조각 알파 IoU (조각 자리 안에서)
    wa = w[..., 3] > 128; aa = art[..., 3] > 128; iou = (wa & aa).sum() / max(1, wa.sum())
    G[n]['cover'] = round(float(iou), 3)
    print(n, G[n])
json.dump(G, open(os.path.join(HERE, 'geom.json'), 'w'), indent=1)
