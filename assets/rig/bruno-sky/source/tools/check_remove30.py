"""30 스카이 브루노 — 프롬프트 2·3 '팔·도끼만 지운 원화' 검수 (check_remove20 구조)
  지운 곳 = guides30 의 빨간 곳(관절 캡슐 + 도끼 자루 캡슐 + 도끼 머리 모양, measure30.json)
  보는 것: SIFT 배율·이동 · 지운 곳(+4px) 밖 색 차이·바뀐 px(상자) · 지운 곳 안에 남은 불투명(= 새로 그린 뒤 그림 또는 남은 흔적)
출력: ../review/check_remove30_<이름>.png (원화 · 받은 그림 · 바뀐 곳 빨강 · 지운 곳 안 새 그림 확대, 어두운 배경) + 숫자
실행: python3 -I check_remove30.py near|far 받은그림.png
"""
import json, os, sys
import numpy as np, cv2
from PIL import Image
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RA = np.array(Image.open(os.path.join(S, 'ref512.png')).convert('RGBA')); M = json.load(open(os.path.join(S, 'measure30.json')))
OLD = np.array(Image.open(os.path.join(S, 'refs', 'ref_design_char0030.png')).convert('RGBA'))
AL = RA[..., 3] > 20; YY, XX = np.mgrid[0:512, 0:512].astype(float)
V = lambda p: np.array(p, float)
def cap(p, q, r):
    p, q = V(p), V(q); d = q - p; L2 = max(d @ d, 1e-9); t = np.clip(((XX - p[0]) * d[0] + (YY - p[1]) * d[1]) / L2, 0, 1)
    return (XX - (p[0] + t * d[0])) ** 2 + (YY - (p[1] + t * d[1])) ** 2 <= r * r
# 도끼 머리 모양: 옛 원화 먼 도끼 머리 → 새 원화(SIFT)
_g = lambda a: cv2.cvtColor(np.ascontiguousarray(a[..., :3]), cv2.COLOR_RGB2GRAY); sf = cv2.SIFT_create(4000)
HM = (OLD[..., 3] > 0) & (((YY <= 146) & (XX >= 352)) | ((YY > 146) & (YY <= 184) & (XX >= 466)))
_n, _cc, _st, _ = cv2.connectedComponentsWithStats(HM.astype(np.uint8), connectivity=8); HM = _cc == 1 + int(np.argmax(_st[1:, cv2.CC_STAT_AREA]))
def head_mask(reg):
    k1, d1 = sf.detectAndCompute(_g(OLD), (HM * 255).astype(np.uint8)); k2, d2 = sf.detectAndCompute(_g(RA), ((AL & reg) * 255).astype(np.uint8))
    mm = [a for a, b in cv2.BFMatcher().knnMatch(d1, d2, k=2) if a.distance < 0.75 * b.distance]
    T, _ = cv2.estimateAffinePartial2D(np.float32([k1[a.queryIdx].pt for a in mm]), np.float32([k2[a.trainIdx].pt for a in mm]), ransacReprojThreshold=4.0)
    w = cv2.warpAffine(HM.astype(np.uint8) * 255, T, (512, 512)) > 60
    return cv2.dilate(w.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
HEADM = {'near': head_mask((XX < 230) & (YY < 220)), 'far': head_mask((XX > 330) & (YY < 280))}
UP_END = {'near': (182, 322), 'far': (308, 338)}                                   # 윗팔 = 팔꿈치 → 어깨갑·소매 앞 가장자리까지(그 안은 몸)
def arm(sd):
    s = M[sd]
    return AL & (cap(s['EL'], UP_END[sd], 13) | cap(s['EL'], s['WR'], 16) | cap(s['WR'], s['fist'], 17) | cap(s['fist'], s['fist'], 21))
def axe(sd):
    s = M[sd]; return AL & (cap(s['head'], s['fist'], 13) | cap(s['fist'], s['pommel'], 14) | HEADM[sd])
def sift(a, b):
    s = cv2.SIFT_create(); g = lambda x: cv2.cvtColor(np.ascontiguousarray(x[..., :3]), cv2.COLOR_RGB2GRAY)
    k1, d1 = s.detectAndCompute(g(a), None); k2, d2 = s.detectAndCompute(g(b), None)
    m = [p for p, q in cv2.BFMatcher().knnMatch(d1, d2, k=2) if p.distance < .7 * q.distance]
    P = np.float32([k1[x.queryIdx].pt for x in m]); Q = np.float32([k2[x.trainIdx].pt for x in m])
    A, inl = cv2.estimateAffinePartial2D(P, Q, ransacReprojThreshold=2)
    return len(m), int(inl.sum()), float(np.hypot(A[0, 0], A[0, 1])), A[:, 2]
def onbg(im, c=(52, 52, 62)):
    b = Image.new('RGBA', (512, 512), c + (255,)); b.alpha_composite(Image.fromarray(im)); return np.array(b.convert('RGB'))
sd, path = sys.argv[1], sys.argv[2]
_b = Image.open(path).convert('RGBA'); B = np.array(_b if _b.size == (512, 512) else _b.resize((512, 512), Image.LANCZOS))
rem = arm(sd) | axe(sd); remD = cv2.dilate(rem.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
n, ni, sc, t = sift(RA, B)
pa = RA[..., :3].astype(float) * RA[..., 3:4] / 255; pb = B[..., :3].astype(float) * B[..., 3:4] / 255
d = np.abs(pa - pb).max(-1); da = np.abs(RA[..., 3].astype(int) - B[..., 3].astype(int)); ch = (d > 24) | (da > 40); out = ch & ~remD
print(f'{os.path.basename(path)} ({sd}) 크기 {_b.size} · SIFT {n}/{ni} 배율 {sc:.4f} 이동 ({t[0]:.2f},{t[1]:.2f})')
print(f'  지운 곳(+4px) 밖 평균 차 {d[~remD].mean():.3f} · 밖 바뀐 px {int(out.sum())} · 지운 곳 {int(rem.sum())}px 중 바뀐 px {int((ch & remD).sum())} · 지운 곳 안 불투명(뒤 그림) {int((rem & (B[..., 3] > 128)).sum())}')
if out.any():
    nl, cc, st, _ = cv2.connectedComponentsWithStats(out.astype(np.uint8), 8)
    big = sorted([(st[i, 4], st[i, 0], st[i, 1], st[i, 2], st[i, 3]) for i in range(1, nl)], reverse=True)[:6]
    print('  밖 바뀐 덩어리(px, x, y, 가로, 세로):', big)
# 떨어진 작은 불투명 섬(지운 자리에 남은 점·부스러기)
nl, cc, st, _ = cv2.connectedComponentsWithStats((B[..., 3] > 40).astype(np.uint8), 8)
isl = [(int(st[i, 4]), int(st[i, 0]), int(st[i, 1]), int(st[i, 2]), int(st[i, 3])) for i in range(1, nl) if st[i, 4] < 400]
print('  떨어진 작은 섬(px, x, y, 가로, 세로):', isl[:10])
v = onbg(B); r = onbg(RA).copy(); r[ch] = (r[ch] * .3 + np.array([255, 40, 40]) * .7).astype(np.uint8)
ys, xs = np.nonzero(remD); bx = (max(0, xs.min() - 10), max(0, ys.min() - 10), min(512, xs.max() + 10), min(512, ys.max() + 10))
z = Image.fromarray(onbg(B, (235, 238, 245))).crop(bx); zs = 512 / max(z.size); z = np.array(z.resize((int(z.width * zs), int(z.height * zs)), Image.LANCZOS))
zz = np.full((512, 512, 3), 255, np.uint8); zz[:z.shape[0], :z.shape[1]] = z
sp = np.full((512, 8, 3), 255, np.uint8)
os.makedirs(os.path.join(S, 'review'), exist_ok=True); op = os.path.join(S, 'review', f'check_remove30_{os.path.splitext(os.path.basename(path))[0]}.png')
Image.fromarray(np.hstack([onbg(RA), sp, v, sp, r, sp, zz])).save(op); print('  그림', op)
