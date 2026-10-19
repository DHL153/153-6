# 29 스카이 팔로메: 시트 조각 → 원화 자리 맞춤 (SIFT + RANSAC 닮음) — python3 -I reg29.py → work/geom.json + review/reg_<이름>.png
#   시트 1번(전체 자세)은 원화와 같지만 조각들은 다시 그린 그림(1:1 복사 아님) → 큰 조각만 SIFT, 작은 조각은 build 에서 관절 두 점으로
import json, os, math, sys
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); PC = os.path.join(HERE, 'pieces')
RA = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA'))
def bgr(a, bg=(255, 0, 255)):   # 알파를 자홍 배경으로 (원화·조각 같게)
    f = a[..., 3:4] / 255.0; return (a[..., :3] * f + np.array(bg) * (1 - f)).astype(np.uint8)[..., ::-1]
S = cv2.SIFT_create(nfeatures=4000, contrastThreshold=0.01)
UP = 2   # 작은 그림이라 2배로 키워 특징점
kA, dA = S.detectAndCompute(cv2.resize(bgr(RA), None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC), None)
def match(n, region=None):
    p = np.array(Image.open(os.path.join(PC, n + '.png')).convert('RGBA')); g = cv2.resize(bgr(p), None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
    m = cv2.resize((p[..., 3] > 128).astype(np.uint8) * 255, None, fx=UP, fy=UP, interpolation=cv2.INTER_NEAREST)
    kP, dP = S.detectAndCompute(g, m)
    if dP is None or len(kP) < 6: return None
    bf = cv2.BFMatcher(); ms = bf.knnMatch(dP, dA, k=2); good = [a for a, b in ms if a.distance < .8 * b.distance]
    if region is not None:   # 원화에서 찾을 곳 제한 [x0,y0,x1,y1]
        good = [g_ for g_ in good if region[0] * UP <= kA[g_.trainIdx].pt[0] <= region[2] * UP and region[1] * UP <= kA[g_.trainIdx].pt[1] <= region[3] * UP]
    if len(good) < 6: return dict(n=len(good))
    src = np.float32([kP[g_.queryIdx].pt for g_ in good]) / UP; dst = np.float32([kA[g_.trainIdx].pt for g_ in good]) / UP
    M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=2.5, maxIters=5000)
    if M is None: return dict(n=len(good))
    warp = cv2.warpAffine(p.astype(np.float32), M, (512, 512)); mm = (warp[..., 3] > 200) & (RA[..., 3] > 200)
    d = float(np.abs(warp[..., :3] - RA[..., :3].astype(np.float32))[mm].mean()) if mm.any() else -1
    out = Image.fromarray(RA.copy()); ov = Image.fromarray(np.clip(warp, 0, 255).astype(np.uint8)); ov.putalpha(Image.fromarray((warp[..., 3] * .55).astype(np.uint8)))
    bg = Image.new('RGBA', (512, 512), (255, 255, 255, 255)); bg.alpha_composite(out); bg.alpha_composite(ov); bg.save(os.path.join(HERE, 'review', f'reg_{n}.png'))
    return dict(M=M.tolist(), inl=int(inl.sum()), good=len(good), scale=round(math.hypot(M[0, 0], M[1, 0]), 4), rot=round(math.degrees(math.atan2(M[1, 0], M[0, 0])), 2),
                xy=[round(float(M[0, 2]), 1), round(float(M[1, 2]), 1)], diff=round(d, 1))
REG = {'head': [180, 105, 345, 295], 'face_neutral': [180, 105, 345, 295], 'beard': [215, 180, 345, 295], 'torso': [140, 230, 420, 400], 'hips': [120, 340, 410, 440],
       'pauldron': [60, 160, 250, 300], 'cape': [25, 300, 140, 430], 'foreF': [370, 230, 455, 320], 'upperF': [350, 240, 420, 320], 'upperN': [70, 250, 180, 310],
       'pauldronF': [320, 190, 390, 300], 'bootN': [145, 425, 230, 480], 'bootF': [295, 425, 390, 480], 'sword': [20, 40, 490, 270]}
if __name__ == '__main__':
    out = {}
    for n, rg in REG.items():
        r = match(n, rg); out[n] = r
        print(f"{n:13s}", {k: v for k, v in (r or {}).items() if k != 'M'})
    json.dump(out, open(os.path.join(HERE, 'work', 'geom.json'), 'w'), indent=0)
