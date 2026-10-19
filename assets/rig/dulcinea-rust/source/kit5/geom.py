# 2 둘시네 내려찍기 키 자세 시트(kit5_v1, DHL 20:18) — 칸마다 얼굴(머리·안경·흰 앞머리)을 원화 ref512 얼굴에 SIFT 닮음 변환으로 맞춤
#  출력 kit5/geom.json: cell{1..4}.M (시트 px → 원화 px), scale, rotDeg, inliers
import json, os
import cv2, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
cv2.setRNGSeed(7)
sheet = np.asarray(Image.open(os.path.join(SRC, 'sheets', 'kit5_v1.png')).convert('RGB'))
r = Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA'); bg = Image.new('RGBA', r.size, (255, 0, 255, 255)); bg.alpha_composite(r); ref = np.asarray(bg.convert('RGB'))
CELLS = {1: (0, 0), 2: (627, 0), 3: (0, 627), 4: (627, 627)}
RX0, RY0, RX1, RY1 = 168, 88, 335, 258      # 원화 얼굴(머리 앞부분·안경·흰 앞머리·귀) — 포니테일은 자세마다 흔들려서 뺌
def sift(A, B, oa, ob, ratio):
    s = cv2.SIFT_create(4000); ka, da = s.detectAndCompute(A, None); kb, db = s.detectAndCompute(B, None)
    m = cv2.BFMatcher().knnMatch(da, db, k=2); g = [x for x, y in m if x.distance < ratio * y.distance]
    pa = np.float32([ka[x.queryIdx].pt for x in g]) + oa; pb = np.float32([kb[x.trainIdx].pt for x in g]) + ob
    M, inl = cv2.estimateAffinePartial2D(pa, pb, ransacReprojThreshold=3, maxIters=8000, confidence=.999); return M, int(inl.sum()), len(g)
G = {}
B = cv2.cvtColor(ref[RY0:RY1, RX0:RX1], cv2.COLOR_RGB2GRAY)
for c, (x0, y0) in CELLS.items():
    A = cv2.cvtColor(sheet[y0:y0 + 627, x0:x0 + 627], cv2.COLOR_RGB2GRAY)
    A = cv2.resize(A, None, fx=1, fy=1)
    M, n, ng = sift(A, B, [x0, y0], [RX0, RY0], .8)
    G[f'cell{c}'] = {'M': M.tolist(), 'inliers': n, 'good': ng, 'scale': float(np.hypot(M[0, 0], M[1, 0])), 'rotDeg': float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))}
json.dump(G, open(os.path.join(HERE, 'geom.json'), 'w'), indent=1)
print({k: (round(v['scale'], 4), round(v['rotDeg'], 2), v['inliers'], v['good']) for k, v in G.items()})
