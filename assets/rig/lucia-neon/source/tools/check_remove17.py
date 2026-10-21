"""17 네온 루시아 — 프롬프트 2(방패만 지운 원화)·3(먼 팔·도끼만 지운 원화) 검수 — check_remove20(20 네온 브루노) 구조
  지운 곳 = guides17 의 빨간 곳(SHIELD · FARARM | AXE 다각형) — 원화 라벨이 아직 없어 가이드 마스크로 잼
  보는 것: SIFT 배율·이동 · 지운 곳(+4px) 밖 색 차이·바뀐 px(덩어리) · 지운 곳 안에 남은 불투명(= 새로 그린 뒤 그림) · 떨어진 작은 섬(점·부스러기)
출력: ../review/check_remove17_<이름>.png (원화 · 받은 그림 · 바뀐 곳 빨강 · 지운 곳 확대) + 숫자
실행: python3 -I check_remove17.py shield|far 받은그림.png
"""
import os, sys
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
_g = {'__file__': os.path.join(HERE, 'guides17.py')}
exec(open(os.path.join(HERE, 'guides17.py')).read().split('FN = ')[0], _g)   # 가이드와 같은 마스크(그림 저장 부분은 안 돌림)
RA = _g['RA']; AL = _g['AL']
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
rem = _g['SHIELD'] if sd == 'shield' else (_g['FARARM'] | _g['AXE'])
remD = cv2.dilate(rem.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
n, ni, sc, t = sift(RA, B)
pa = RA[..., :3].astype(float) * RA[..., 3:4] / 255; pb = B[..., :3].astype(float) * B[..., 3:4] / 255
d = np.abs(pa - pb).max(-1); da = np.abs(RA[..., 3].astype(int) - B[..., 3].astype(int)); ch = (d > 24) | (da > 40); out = ch & ~remD
print(f'{os.path.basename(path)} ({sd}) 크기 {_b.size} · SIFT {n}/{ni} 배율 {sc:.4f} 이동 ({t[0]:.2f},{t[1]:.2f})')
print(f'  지운 곳(+4px) 밖 평균 차 {d[~remD].mean():.3f} · 밖 바뀐 px {int(out.sum())} · 지운 곳 {int(rem.sum())}px 중 바뀐 px {int((ch & remD).sum())} · 지운 곳 안 불투명(뒤 그림) {int((rem & (B[..., 3] > 128)).sum())}')
if out.any():
    nl, cc, st, _ = cv2.connectedComponentsWithStats(out.astype(np.uint8), 8)
    big = sorted([(int(st[i, 4]), int(st[i, 0]), int(st[i, 1]), int(st[i, 2]), int(st[i, 3])) for i in range(1, nl)], reverse=True)[:8]
    print('  밖 바뀐 덩어리(px, x, y, 가로, 세로):', big)
nl, cc, st, _ = cv2.connectedComponentsWithStats((B[..., 3] > 40).astype(np.uint8), 8)
isl = [(int(st[i, 4]), int(st[i, 0]), int(st[i, 1]), int(st[i, 2]), int(st[i, 3])) for i in range(1, nl) if st[i, 4] < 400]
print('  떨어진 작은 섬(px, x, y, 가로, 세로):', isl[:10])
ys, xs = np.nonzero(B[..., 3] > 128); print('  불투명 범위 x', xs.min(), '–', xs.max(), '· y', ys.min(), '–', ys.max())
v = onbg(B); r = onbg(RA).copy(); r[ch] = (r[ch] * .3 + np.array([255, 40, 40]) * .7).astype(np.uint8)
ys, xs = np.nonzero(remD); bx = (max(0, xs.min() - 10), max(0, ys.min() - 10), min(512, xs.max() + 10), min(512, ys.max() + 10))
z = Image.fromarray(onbg(B, (235, 238, 245))).crop(bx); zs = 512 / max(z.size); z = np.array(z.resize((int(z.width * zs), int(z.height * zs)), Image.LANCZOS))
zz = np.full((512, 512, 3), 255, np.uint8); zz[:z.shape[0], :z.shape[1]] = z
sp = np.full((512, 8, 3), 255, np.uint8)
os.makedirs(os.path.join(S, 'review'), exist_ok=True); op = os.path.join(S, 'review', f'check_remove17_{os.path.splitext(os.path.basename(path))[0]}.png')
Image.fromarray(np.hstack([onbg(RA), sp, v, sp, r, sp, zz])).save(op); print('  그림', op)
