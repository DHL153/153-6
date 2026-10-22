"""15 네온 바실 조각 시트 1 검수 — python3 -I tools/check_sheet5.py (check_sheet20 구조)
  ①1번 pose ↔ 원화 SIFT(배율·이동) ②머리·표정·깜빡임 9장 ↔ 원화 머리 SIFT(배율·자리 — 대기 머리와 같은 자리에 놓을 변환) ③조각 길이 ÷ 선 길이(measure15)·굵기 ÷ 원화 굵기
  ④도끼 ↔ 원화 먼 도끼 머리 SIFT(배율) ⑤표정 확대 그림(눈 뜸 판정) → review/sheet15_faces.png
"""
import json, os, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = os.path.join(S, 'pieces')
RA = np.array(Image.open(os.path.join(S, 'ref512.png')).convert('RGBA')); M = json.load(open(os.path.join(S, 'measure15.json')))
idx = json.load(open(os.path.join(P, 'index.json')))
g = lambda a: cv2.cvtColor(np.ascontiguousarray(a[..., :3]), cv2.COLOR_RGB2GRAY)
sf = cv2.SIFT_create(4000)
def sift(a, b, ma=None, mb=None):
    k1, d1 = sf.detectAndCompute(g(a), ma); k2, d2 = sf.detectAndCompute(g(b), mb)
    m = [p for p, q in cv2.BFMatcher().knnMatch(d1, d2, k=2) if p.distance < .75 * q.distance]
    if len(m) < 6: return None
    A, inl = cv2.estimateAffinePartial2D(np.float32([k1[x.queryIdx].pt for x in m]), np.float32([k2[x.trainIdx].pt for x in m]), ransacReprojThreshold=3)
    return A, int(inl.sum()), len(m)
ld = lambda n: np.array(Image.open(os.path.join(P, n + '.png')).convert('RGBA'))
pose = ld('pose'); r = sift(pose, RA)
A, ni, nm = r; print(f"pose → 원화: SIFT {ni}/{nm} 배율 {math.hypot(A[0,0],A[1,0]):.4f} 회전 {math.degrees(math.atan2(A[1,0],A[0,0])):+.2f}° 이동 ({A[0,2]:.1f},{A[1,2]:.1f}) (시트 자리 {idx['pose'][:2]})")
YY, XX = np.mgrid[0:512, 0:512]
hm = ((YY > 60) & (YY < 270) & (XX > 165) & (XX < 330) & (RA[..., 3] > 128)).astype(np.uint8) * 255
for n in ('head', 'face_neutral', 'face_happy', 'face_angry', 'face_focus', 'face_shout', 'face_effort', 'blink_half', 'blink_closed'):
    p = ld(n); r = sift(p, RA, (p[..., 3] > 128).astype(np.uint8) * 255, hm)
    if r is None: print(n, '못 맞춤'); continue
    A, ni, nm = r; print(f"{n:13s} → 원화 머리: SIFT {ni:3d}/{nm:3d} 배율 {math.hypot(A[0,0],A[1,0]):.4f} 회전 {math.degrees(math.atan2(A[1,0],A[0,0])):+.2f}° 왼쪽 위 → ({A[0,2]:.1f},{A[1,2]:.1f})")
# 조각 길이·굵기
for n, L, w0 in (('thighN', M['legs']['near']['len']['thigh'], None), ('shinN', M['legs']['near']['len']['shin'], None),
                 ('thighF', M['legs']['far']['len']['thigh'], None), ('shinF', M['legs']['far']['len']['shin'], None)):
    p = ld(n); a = p[..., 3] > 128; ys, xs = np.nonzero(a); h = ys.max() - ys.min() + 1; wmid = int(a[(ys.min() + ys.max()) // 2].sum())
    print(f"{n:7s} 세로 {h} 가운데 굵기 {wmid} · 선 {L:.1f} → 세로/선 {h / L:.2f} · (세로−굵기)/선 {(h - wmid) / L:.2f}")
# 윗팔(길이 = 선 + 양 끝 마디, 굵기 = 원화 먼 윗팔 ≈ 26) · 건틀릿 ↔ 원화 SIFT 배율
for n, L in (('upperN', M['near']['len']['upper']), ('upperF', M['far']['len']['upper'])):
    p = ld(n); a = p[..., 3] > 128; ys, xs = np.nonzero(a); h = ys.max() - ys.min() + 1; wmid = int(a[(ys.min() + ys.max()) // 2].sum())
    print(f"{n:7s} 세로 {h} 가운데 굵기 {wmid} · 선 {L:.1f} → 세로/선 {h / L:.2f} · (세로−굵기)/선 {(h - wmid) / L:.2f}")
from matplotlib.path import Path as _P
for n, sd in (('gauntN', 'near'), ('gauntF', 'far')):
    pm = _P(M[sd]['gaunt']).contains_points(np.c_[XX.ravel(), YY.ravel()]).reshape(512, 512) & (RA[..., 3] > 128)
    p = ld(n); r = sift(p, RA, (p[..., 3] > 128).astype(np.uint8) * 255, pm.astype(np.uint8) * 255)
    if r: A, ni, nm = r; print(f"{n} → 원화: SIFT {ni}/{nm} 배율 {math.hypot(A[0,0],A[1,0]):.4f} 회전 {math.degrees(math.atan2(A[1,0],A[0,0])):+.1f}° 이동 ({A[0,2]:.1f},{A[1,2]:.1f})")
    else: print(n, '못 맞춤')
# 표정 확대
names = ['head', 'face_neutral', 'face_happy', 'face_angry', 'face_focus', 'face_shout', 'face_effort', 'blink_half', 'blink_closed']
tiles = []
for n in names:
    q = Image.new('RGBA', (200, 190), (52, 52, 62, 255)); im = Image.fromarray(ld(n)); q.alpha_composite(im, (5, 5)); q = q.convert('RGB').crop((60, 40, 170, 155)).resize((300, 314), Image.LANCZOS)
    d = ImageDraw.Draw(q); d.text((6, 4), n, fill=(255, 255, 120)); tiles.append(q)
W = Image.new('RGB', (5 * 305, 2 * 320), (20, 20, 20))
for i, t in enumerate(tiles): W.paste(t, ((i % 5) * 305, (i // 5) * 320))
W.save(os.path.join(S, 'review', 'sheet15_faces.png')); print('그림 review/sheet15_faces.png')
