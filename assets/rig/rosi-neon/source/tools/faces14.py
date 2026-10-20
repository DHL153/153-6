# 14 네온 로시 표정·깜빡임: 조각 시트(parts1_0759) 머리 9장을 원화 머리(art_v1_0730, 2048 공간)에 맞춤 → 얼굴만 오린 조각 (4 러스트 faces4.py 와 같은 방법)
#  맞춤 = 머리카락·귀(얼굴 빼고, 머리 라벨 안)에 SIFT 닮음 → ECC affine · 살빛 맞춤
#  표정 7(웃음·화남·슬픔·놀람·외침·집중·윙크) = 얼굴 전체 · 깜빡임 2 = 눈 부분만(코·입 = 원화)
#  python3 -I tools/faces14.py  → ../parts/face_*.png · blink_*.png · work/faces14.json · review/faces14.png
import os, json, cv2, numpy as np
from PIL import Image, ImageDraw
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R = os.path.dirname(H); W = os.path.join(H, 'work')
J = json.load(open(os.path.join(W, 'build14_parts.json')))['J']
def up(p, n):
    a = np.array(Image.open(p).convert('RGBA')).astype(np.float32); return cv2.resize(a, (n, n), interpolation=cv2.INTER_LANCZOS4)
O = up(os.path.join(H, 'sheets/art_v1_0730.png'), 2048); bg = O[..., :3] * (O[..., 3:4] / 255.) + np.array([255, 0, 255]) * (1 - O[..., 3:4] / 255.); O4 = np.clip(bg, 0, 255).astype(np.uint8)
LAB = np.load(os.path.join(W, 'labels14.npy')); NAMES = json.load(open(os.path.join(W, 'labels14.json')))
headM = cv2.resize((LAB == NAMES.index('head') + 1).astype(np.uint8), (2048, 2048), interpolation=cv2.INTER_NEAREST) > 0
def pmask(poly):
    m = Image.new('L', (2048, 2048), 0); ImageDraw.Draw(m).polygon([(x * 4, y * 4) for x, y in poly], fill=255); return np.array(m) > 0
FACE = [(236, 186), (256, 176), (280, 168), (300, 170), (309, 188), (307, 212), (297, 227), (281, 235), (263, 238), (247, 233), (236, 222), (230, 204)]
EYE = [(234, 184), (256, 178), (278, 180), (300, 182), (308, 192), (307, 212), (291, 213), (288, 204), (279, 204), (276, 209), (252, 209), (236, 206), (231, 196)]
HB = (200, 70, 370, 260); X0, Y0 = HB[0] * 4, HB[1] * 4; Wd, Hd = (HB[2] - HB[0]) * 4, (HB[3] - HB[1]) * 4; ref = O4[Y0:Y0 + Hd, X0:X0 + Wd]
fm = pmask(FACE)[Y0:Y0 + Hd, X0:X0 + Wd]
tmask = (headM[Y0:Y0 + Hd, X0:X0 + Wd] & ~(cv2.dilate(fm.astype(np.uint8), np.ones((41, 41))) > 0)).astype(np.uint8)
g = lambda a: cv2.GaussianBlur(cv2.cvtColor(a, cv2.COLOR_RGB2GRAY), (0, 0), 2).astype(np.float32)
def feath(poly):
    m = pmask(poly); f = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 7); return np.minimum(1, f * 1.7) * m
S = np.array(Image.open(os.path.join(H, 'sheets/parts1_0759.png')).convert('RGB')); cells = json.load(open(os.path.join(W, 'cells14.json')))
JOBS = [(2, 'face_happy', FACE), (3, 'face_angry', FACE), (4, 'face_sad', FACE), (5, 'face_surprised', FACE), (6, 'face_shout', FACE), (7, 'face_focus', FACE), (8, 'face_wink', FACE), (9, 'blink_half', EYE), (10, 'blink_closed', EYE)]
sift = cv2.SIFT_create(5000)
def crop(ci):
    cx, cy, cw, ch = cells[ci]; m = 24; C = S[max(0, cy - m):cy + ch + m, max(0, cx - m):cx + cw + m].copy(); return C, ~((C[..., 0] > 190) & (C[..., 2] > 190) & (C[..., 1] < 100))
def reg(src, smask, dst, dmask, ecc_mask, size):   # src → dst (닮음 SIFT → affine ECC), 결과 = src 좌표 → dst 좌표 3×3
    k1, d1 = sift.detectAndCompute(cv2.cvtColor(src, cv2.COLOR_RGB2GRAY), smask.astype(np.uint8) * 255); k2, d2 = sift.detectAndCompute(cv2.cvtColor(dst, cv2.COLOR_RGB2GRAY), dmask.astype(np.uint8) * 255)
    good = [a for a, b in cv2.BFMatcher().knnMatch(d1, d2, k=2) if a.distance < .75 * b.distance]
    A, inl = cv2.estimateAffinePartial2D(np.float32([k1[a.queryIdx].pt for a in good]), np.float32([k2[a.trainIdx].pt for a in good]), method=cv2.RANSAC, ransacReprojThreshold=5)
    wp = cv2.warpAffine(src, A, size, flags=cv2.INTER_CUBIC, borderValue=(255, 0, 255)); cc = None; D = np.eye(2, 3, dtype=np.float32)
    try: cc, D = cv2.findTransformECC(g(dst), g(wp), np.eye(2, 3, dtype=np.float32), cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 400, 1e-6), ecc_mask.astype(np.uint8), 5)
    except Exception: cc = None; D = np.eye(2, 3, dtype=np.float32)
    return np.linalg.inv(np.vstack([D, [0, 0, 1]])) @ np.vstack([A, [0, 0, 1]]), int(inl.sum()), cc
# ① 시트 기본 머리(2번) → 원화: 얼굴(눈·코·입·턱·흉터)로 맞춤 — 같은 표정이라 얼굴이 가장 정확
C2, C2m = crop(1); faceRing = cv2.dilate(fm.astype(np.uint8), np.ones((31, 31))) > 0
M2, n2, c2 = reg(C2, C2m, ref, faceRing & (headM[Y0:Y0 + Hd, X0:X0 + Wd] | faceRing), faceRing, (Wd, Hd)); print('기본 머리 → 원화', n2, c2)
inv2 = np.linalg.inv(M2)
fm2 = cv2.warpAffine(fm.astype(np.uint8), inv2[:2], (C2.shape[1], C2.shape[0]), flags=cv2.INTER_NEAREST) > 0   # 원화 얼굴 다각형을 2번 칸 좌표로
hair2 = C2m & ~(cv2.dilate(fm2.astype(np.uint8), np.ones((25, 25))) > 0)
parts = {}; rep = {}; prev = [ref]
for ci, name, poly in JOBS:
    C, Cm = crop(ci)
    # ② 이 칸 → 2번 칸: 머리카락(같은 그림 결)로 맞춤
    Mk, nk, ck = reg(C, Cm, C2, hair2, hair2, (C2.shape[1], C2.shape[0]))
    M = M2 @ Mk; M[0, 2] += X0; M[1, 2] += Y0; cc = ck; inl = nk
    full = cv2.warpAffine(C.astype(np.float32), M[:2], (2048, 2048), flags=cv2.INTER_CUBIC, borderValue=(255, 0, 255))
    mag = (full[..., 0] > 180) & (full[..., 2] > 180) & (full[..., 1] < 110); fe = feath(poly) * (~mag)
    sk = lambda a: (a[..., 0] > 170) & (a[..., 1] > 110) & (a[..., 1] < 210) & (a[..., 2] > 80) & (a[..., 2] < 185) & (a[..., 0] > a[..., 1] + 15)
    rg_ = fe > .3; so = sk(O4.astype(np.float32)) & rg_; sc_ = sk(full) & rg_
    gain = np.median(O4[so].astype(np.float32), 0) / np.maximum(np.median(full[sc_], 0), 1) if so.sum() > 200 and sc_.sum() > 200 else np.ones(3)
    full = np.clip(full * gain, 0, 255)
    patch = np.dstack([full, fe * 255]).astype(np.uint8); ys, xs = np.nonzero(patch[..., 3] > 3); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    Image.fromarray(patch[y0:y1, x0:x1]).save(os.path.join(R, 'parts', name + '.png'))
    parts[name] = {'src': f'parts/{name}.png', 'pivot': [float(J['head'][0] * 4 - x0), float(J['head'][1] * 4 - y0)], 'scale': .5}
    rep[name] = dict(inliers=inl, ecc=round(float(cc), 3) if cc else None, scale=round(float(np.hypot(*M[:2, 0])), 3), gain=gain.round(3).tolist())
    pv = O4.astype(np.float32) * (1 - fe[..., None]) + full * fe[..., None]; prev.append(np.clip(pv[Y0:Y0 + Hd, X0:X0 + Wd], 0, 255).astype(np.uint8)); print(name, rep[name])
json.dump({'parts': parts, 'rep': rep}, open(os.path.join(W, 'faces14.json'), 'w'), indent=1)
row = lambda L: np.hstack(L); blank = np.full_like(ref, 255)
Image.fromarray(np.vstack([row(prev[:5]), row(prev[5:])])).resize((5 * 272, 2 * 304)).save(os.path.join(H, 'review', 'faces14.png'))
