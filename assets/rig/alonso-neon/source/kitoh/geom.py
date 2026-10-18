# 키트 v1 좌표 맞춤(SIFT) → kitoh/geom.json
#  head: 키트 전체 자세 머리 → 원화(ref512) 머리 (닮음 변환: 키트 px → 원화 px)
#  armN·armF: 따로 그린 팔 조각 → 키트 전체 자세 (조각 px → 키트 px)
import json, os
import cv2, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
cv2.setRNGSeed(7)
kit = np.asarray(Image.open(os.path.join(SRC, 'sheets', 'kitOH_v1.png')).convert('RGB')); ref = np.asarray(Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA'))
def sift(A, B, oa, ob, ratio):
    s = cv2.SIFT_create(4000); ka, da = s.detectAndCompute(A, None); kb, db = s.detectAndCompute(B, None)
    m = cv2.BFMatcher().knnMatch(da, db, k=2); g = [x for x, y in m if x.distance < ratio * y.distance]
    pa = np.float32([ka[x.queryIdx].pt for x in g]) + oa; pb = np.float32([kb[x.trainIdx].pt for x in g]) + ob
    M, inl = cv2.estimateAffinePartial2D(pa, pb, ransacReprojThreshold=4, maxIters=8000, confidence=.999); return M, int(inl.sum())
G = {}
M, n = sift(cv2.cvtColor(kit[250:700, 330:820], cv2.COLOR_RGB2GRAY), cv2.cvtColor(ref[40:310, 60:340, :3], cv2.COLOR_RGB2GRAY), [330, 250], [60, 40], .75)
G['head'] = {'M': M.tolist(), 'inliers': n}
for nm, f, reg in [('armN', 'kitArmN.png', (250, 120, 560, 520)), ('armF', 'kitArmF.png', (430, 100, 820, 700))]:
    a = np.asarray(Image.open(os.path.join(SRC, 'pieces', 'kitOH', f)).convert('RGBA')); g = a[..., :3].copy(); g[a[..., 3] < 128] = (255, 0, 255)
    x0, y0, x1, y1 = reg; M, n = sift(cv2.cvtColor(g, cv2.COLOR_RGB2GRAY), cv2.cvtColor(kit[y0:y1, x0:x1], cv2.COLOR_RGB2GRAY), [0, 0], [x0, y0], .8)
    G[nm] = {'M': M.tolist(), 'inliers': n}
for k, v in G.items(): M = np.array(v['M']); v['scale'] = float(np.hypot(M[0, 0], M[1, 0])); v['rotDeg'] = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
json.dump(G, open(os.path.join(HERE, 'geom.json'), 'w'), indent=1); print({k: (round(v['scale'], 4), round(v['rotDeg'], 2), v['inliers']) for k, v in G.items()})
