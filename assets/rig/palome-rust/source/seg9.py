# 9 러스트 팔로메: 원화를 부품별로 나누기 (2026-10-19 22:00)
#   대략 다각형(polys.json, ±3px) 안쪽 = 씨앗, 경계 띠는 원화 외곽선(어두운 선)을 따라 watershed 로 나눔.
#   외곽선은 앞 부품 것으로(뒤 부품이 움직여도 앞 부품 테두리가 그대로) — FRONT 쌍.
#   출력: work/labels.npy(512×512, 0 = 빈 곳) · review/seg_labels.png(색 표시) · review/seg_parts.png(부품별)
#   python3 -I seg9.py
import json, os
import numpy as np, cv2
from PIL import Image, ImageDraw
from skimage.segmentation import watershed
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work'); RV = os.path.join(HERE, 'review')
os.makedirs(W, exist_ok=True)
RA = np.array(Image.open(os.path.join(HERE, 'refs', 'ref_art_char0009.png')).convert('RGBA'))
A = RA[..., 3] > 40
PO = json.load(open(os.path.join(HERE, 'polys.json')))
NAMES = ['head', 'sword', 'handF', 'foreF', 'pauldron', 'upperN', 'foreN', 'legN', 'legF', 'body']
LID = {n: i + 1 for i, n in enumerate(NAMES)}
def poly(pts):
    m = Image.new('L', (512, 512), 0); ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255); return np.array(m) > 0
def ero(m, r): return cv2.erode(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
def dil(m, r): return cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
# 칼 다각형: 날(원화 가장자리 맞춤 선 ± 여유) + 날밑 + 손잡이 띠 + 폼멜
TOP = (0.6475, -32.93); BOT = (0.6951, 7.24); x0, x1 = PO['bladeX']
blade = [(x0 - 10, TOP[0] * (x0 - 10) + TOP[1] - 8), (x1, TOP[0] * x1 + TOP[1] - 8), (x1, BOT[0] * x1 + BOT[1] + 8), (x0 - 10, BOT[0] * (x0 - 10) + BOT[1] + 8)]
ha, hb = np.array(PO['handleAxis'], float); u = (hb - ha) / np.linalg.norm(hb - ha); nrm = np.array([-u[1], u[0]]); HW = 11
handle = [ha + nrm * HW, hb + nrm * HW, hb - nrm * HW, ha - nrm * HW]
M = {'sword': poly(blade) | poly(PO['guard']) | poly(handle) | poly(PO['pommel'])}
for n in ['head', 'handF', 'foreF', 'pauldron', 'upperN', 'foreN', 'legN', 'legF']: M[n] = poly(PO[n])
FRONT_ORDER = ['handF', 'head', 'foreN', 'pauldron', 'upperN', 'sword', 'foreF', 'legN', 'legF']   # 겹치는 다각형에서 앞이 이김
seeds = np.zeros((512, 512), np.int32); taken = np.zeros((512, 512), bool)
for n in FRONT_ORDER:
    r = 2 if n in ('handF', 'upperN', 'legN', 'legF', 'foreF') else 3
    s = ero(M[n], r) & A & ~taken; seeds[s] = LID[n]; taken |= dil(M[n], 1) if n in ('handF', 'head') else s
others = np.zeros((512, 512), bool)
for n in FRONT_ORDER: others |= M[n]
seeds[A & ~dil(others, 4) & (seeds == 0)] = LID['body']
lum = RA[..., :3].astype(float).mean(-1)
elev = cv2.GaussianBlur((255 - lum).astype(np.float32), (3, 3), 0.7)
lab = watershed(elev, markers=seeds, mask=A)
# 외곽선은 앞 부품 것으로: 뒤 부품의 어두운 점이 앞 부품 2px 안이면 앞으로
FRONT = [('head', 'sword'), ('handF', 'sword'), ('head', 'pauldron'), ('sword', 'foreF'), ('handF', 'foreF'), ('head', 'foreF'), ('head', 'body'),
         ('foreN', 'body'), ('pauldron', 'upperN'), ('foreN', 'upperN'), ('pauldron', 'body'), ('upperN', 'body'), ('foreF', 'body'), ('handF', 'body'),
         ('body', 'legN'), ('body', 'legF'), ('sword', 'body'), ('head', 'handF')]
dark = lum < 70
for f, b in FRONT:
    near = dil(lab == LID[f], 2); mv = near & (lab == LID[b]) & dark; lab[mv] = LID[f]
# 떨어진 섬(가장 큰 덩어리가 아닌 조각)은 가장 많이 맞닿은 다른 부품으로 — 대기 땐 안 보이다 팔이 움직이면 몸에 붙은 채 떠 보임(먼 손 옆 몸 섬 385px)
for n in NAMES:
    if n == 'sword': continue   # 칼은 머리·손에 가려 여러 덩어리가 맞음(날 오른쪽·손잡이 끝)
    m = (lab == LID[n]).astype(np.uint8); k, cc, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if k <= 2: continue
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    for j in range(1, k):
        if j == big or st[j, 4] > 600: continue
        isl = cc == j; ring = dil(isl, 1) & ~isl & (lab > 0) & (lab != LID[n]) & (lab != LID['sword'])   # 칼(손잡이)로는 안 보냄 — 손 옆 섬은 토시 판
        if ring.any(): nb = np.bincount(lab[ring]).argmax(); lab[isl] = nb; print(f'  island {n} {int(st[j, 4])}px @({st[j, 0]},{st[j, 1]}) -> {NAMES[nb - 1]}')
np.save(os.path.join(W, 'labels.npy'), lab)
COL = {'head': (255, 80, 80), 'sword': (80, 80, 255), 'handF': (255, 220, 0), 'foreF': (255, 140, 0), 'pauldron': (0, 200, 200), 'upperN': (200, 0, 200),
       'foreN': (0, 180, 0), 'legN': (120, 60, 0), 'legF': (180, 120, 60), 'body': (160, 160, 160)}
ov = np.zeros((512, 512, 3), np.uint8)
for n, c in COL.items(): ov[lab == LID[n]] = c
base = RA[..., :3].astype(float) * .45 + ov * .55; base[~A] = 255
big = Image.fromarray(base.astype(np.uint8)).resize((1024, 1024), Image.NEAREST); d = ImageDraw.Draw(big)
for n in FRONT_ORDER:
    for p, q in zip(PO.get(n, []) if n != 'sword' else [], (PO.get(n, [])[1:] + PO.get(n, [])[:1]) if n != 'sword' else []): d.line([p[0] * 2, p[1] * 2, q[0] * 2, q[1] * 2], fill=(0, 0, 0), width=1)
big.save(os.path.join(RV, 'seg_labels.png'))
for n in NAMES: print(f'{n:9s} px {int((lab == LID[n]).sum())}')
