"""17 네온 루시아 조각 시트 1 검수 (DHL 10-21 11:03 그림 = sheets/parts1_1103.png → cut17.py → pieces/) — check_sheet20 구조
  ①1번 pose ↔ 원화 SIFT(배율·회전·이동) ②머리·표정·깜빡임 9장 ↔ 원화 머리 SIFT(배율·자리)
  ③도끼 ↔ 원화 도끼 SIFT(배율·회전 — 시트 도끼는 곧게 세움) ④어깨갑 ↔ 원화 먼 어깨갑 크기
  ⑤윗팔·팔뚝·허벅지·정강이 길이 ÷ 선 길이(measure17) — 둥근 끝 빼고(세로 − 굵기)
실행: python3 -I tools/check_sheet17.py
"""
import json, os, math
import numpy as np, cv2
from PIL import Image
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = os.path.join(S, 'pieces')
RA = np.array(Image.open(os.path.join(S, 'ref512.png')).convert('RGBA')); M = json.load(open(os.path.join(S, 'measure17.json')))
idx = json.load(open(os.path.join(P, 'index.json')))
g = lambda a: cv2.cvtColor(np.ascontiguousarray(a[..., :3]), cv2.COLOR_RGB2GRAY)
sf = cv2.SIFT_create(4000)
def sift(a, b, ma=None, mb=None):
    k1, d1 = sf.detectAndCompute(g(a), ma); k2, d2 = sf.detectAndCompute(g(b), mb)
    if d1 is None or d2 is None: return None
    m = [p for p, q in cv2.BFMatcher().knnMatch(d1, d2, k=2) if p.distance < .75 * q.distance]
    if len(m) < 6: return None
    A, inl = cv2.estimateAffinePartial2D(np.float32([k1[x.queryIdx].pt for x in m]), np.float32([k2[x.trainIdx].pt for x in m]), ransacReprojThreshold=3)
    return A, int(inl.sum()), len(m)
sc = lambda A: math.hypot(A[0, 0], A[1, 0]); rot = lambda A: math.degrees(math.atan2(A[1, 0], A[0, 0]))
ld = lambda n: np.array(Image.open(os.path.join(P, n + '.png')).convert('RGBA'))
msk = lambda p: (p[..., 3] > 128).astype(np.uint8) * 255
YY, XX = np.mgrid[0:512, 0:512]
pose = ld('pose'); A, ni, nm = sift(pose, RA)
print(f"pose → 원화: SIFT {ni}/{nm} 배율 {sc(A):.4f} 회전 {rot(A):+.2f}° 이동 ({A[0,2]:.1f},{A[1,2]:.1f})")
hm = ((YY > 170) & (YY < 290) & (XX > 220) & (XX < 360) & (RA[..., 3] > 128)).astype(np.uint8) * 255
for n in ('head', 'face_neutral', 'face_happy', 'face_angry', 'face_focus', 'face_shout', 'face_effort', 'blink_half', 'blink_closed'):
    p = ld(n); r = sift(p, RA, msk(p), hm)
    if r is None: print(n, '못 맞춤'); continue
    A, ni, nm = r; print(f"{n:13s} → 원화 머리: SIFT {ni:3d}/{nm:3d} 배율 {sc(A):.4f} 회전 {rot(A):+.2f}° 왼쪽 위 → ({A[0,2]:.1f},{A[1,2]:.1f})")
am = (((YY < 262) & (XX > 296) & ~(((XX < 344) & (YY > 176)) | ((XX < 352) & (YY > 205)))) & (RA[..., 3] > 128)).astype(np.uint8) * 255
p = ld('axe'); r = sift(p, RA, msk(p), am)
if r: A, ni, nm = r; print(f"axe → 원화 도끼 머리: SIFT {ni}/{nm} 배율 {sc(A):.4f} 회전 {rot(A):+.1f}° (원화 자루 축 세로에서 {M['axe']['deg_from_vertical']}°)")
ys, xs = np.nonzero(p[..., 3] > 128); print('axe 세로', ys.max() - ys.min() + 1, '가로', xs.max() - xs.min() + 1, '· 원화 도끼 위 끝 52 → 마개 아래 377 축 길이 ≈', round((377 - 52) / math.cos(math.radians(M['axe']['deg_from_vertical'])), 1))
p = ld('pauldron'); ys, xs = np.nonzero(p[..., 3] > 128); print('pauldron', xs.max() - xs.min() + 1, '×', ys.max() - ys.min() + 1, '(원화 먼 어깨갑 크림 둥근 판 ≈ x 343–400 · y 253–312)')
fa = M['far']; L = M['legs']
for n, Ln in (('upF', fa['len']['upper']), ('foreF', fa['len']['fore']), ('thighN', L['near']['len']['thigh']), ('thighF', L['far']['len']['thigh'])):
    p = ld(n); a = p[..., 3] > 128; ys, xs = np.nonzero(a); h = ys.max() - ys.min() + 1; w = int(a[(ys.min() + ys.max()) // 2].sum())
    print(f"{n:7s} 세로 {h} 가운데 굵기 {w} · 선 {Ln:.1f} → 세로/선 {h / Ln:.2f} · (세로−굵기)/선 {(h - w) / Ln:.2f}")
for n, sd in (('bootN', 'near'), ('bootF', 'far')):
    p = ld(n); a = p[..., 3] > 128; ys, xs = np.nonzero(a); print(f"{n} {xs.max() - xs.min() + 1}×{ys.max() - ys.min() + 1} · 정강이 선 {L[sd]['len']['shin']} (원화 무릎→발바닥 {450 - L[sd]['knee'][1]})")
for n in ('kneeN', 'kneeF'):
    p = ld(n); a = p[..., 3] > 128; ys, xs = np.nonzero(a); print(n, xs.max() - xs.min() + 1, '×', ys.max() - ys.min() + 1)
