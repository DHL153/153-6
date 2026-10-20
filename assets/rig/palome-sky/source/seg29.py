# 29 스카이 팔로메: 원화를 부품별로 나누기 (2026-10-20, 9 러스트 seg9.py 와 같은 방식)
#   대략 다각형(polys29.json) 안쪽 = 씨앗, 경계 띠는 원화 외곽선(어두운 선)을 따라 watershed. 외곽선은 앞 부품 것(FRONT 쌍), 떨어진 섬은 이웃으로(칼 제외)
#   출력: work/labels.npy · review/seg_labels.png    python3 -I seg29.py
import json, os
import numpy as np, cv2
from PIL import Image, ImageDraw
from skimage.segmentation import watershed
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work'); RV = os.path.join(HERE, 'review')
os.makedirs(W, exist_ok=True)
RA = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA'))
A = RA[..., 3] > 40
PO = json.load(open(os.path.join(HERE, 'polys29.json')))
NAMES = ['head', 'sword', 'handF', 'foreF', 'upperF', 'pauldron', 'upperN', 'foreN', 'cape', 'legN', 'legF', 'body']
LID = {n: i + 1 for i, n in enumerate(NAMES)}
def poly(pts):
    m = Image.new('L', (512, 512), 0); ImageDraw.Draw(m).polygon([tuple(map(float, p)) for p in pts], fill=255); return np.array(m) > 0
def ero(m, r): return cv2.erode(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
def dil(m, r): return cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
# 칼: 날(가장자리 맞춤 선 ± 여유) + 날밑(날에 수직 띠) + 손잡이 띠 + 폼멜
(ta, tb), (ba, bb) = PO['bladeLines']['top'], PO['bladeLines']['bot']; x0, x1 = PO['bladeX']
blade = [(x0, ta * x0 + tb - 6), (x1, ta * x1 + tb - 6), (x1, ba * x1 + bb + 6), (x0, ba * x0 + bb + 6)]
g0, g1 = np.array(PO['guardLine'], float); ub = np.array([1.0, (ta + ba) / 2]); ub /= np.linalg.norm(ub); GHW = PO['guardHW']
guard = [g0 - ub * GHW, g0 + ub * GHW, g1 + ub * GHW, g1 - ub * GHW]
ha, hb = np.array(PO['handleAxis'], float); u = (hb - ha) / np.linalg.norm(hb - ha); nrm = np.array([-u[1], u[0]]); HW = 9
handle = [ha + nrm * HW, hb + nrm * HW, hb - nrm * HW, ha - nrm * HW]
M = {'sword': poly(blade) | poly(guard) | poly(handle) | poly(PO['pommel']) | poly(PO['guardTop'])}   # guardTop: 날밑 위 금 덩어리(날밑 띠 밖이라 몸으로 갔음 → 칼을 휘두르면 몸에 남아 떠 보였음)
for n in ['head', 'handF', 'foreF', 'upperF', 'pauldron', 'upperN', 'foreN', 'cape', 'legN', 'legF']: M[n] = poly(PO[n])
FRONT_ORDER = ['handF', 'head', 'foreN', 'pauldron', 'upperN', 'foreF', 'sword', 'upperF', 'cape', 'legN', 'legF']   # 겹치는 다각형에서 앞이 이김
seeds = np.zeros((512, 512), np.int32); taken = np.zeros((512, 512), bool)
for n in FRONT_ORDER:
    r = 2 if n in ('handF', 'upperN', 'upperF', 'legN', 'legF', 'foreF') else 3
    s = ero(M[n], r) & A & ~taken; seeds[s] = LID[n]; taken |= dil(M[n], 1) if n in ('handF', 'head') else s
others = np.zeros((512, 512), bool)
for n in FRONT_ORDER: others |= M[n]
seeds[A & ~dil(others, 4) & (seeds == 0)] = LID['body']
lum = RA[..., :3].astype(float).mean(-1)
elev = cv2.GaussianBlur((255 - lum).astype(np.float32), (3, 3), 0.7)
lab = watershed(elev, markers=seeds, mask=A)
FRONT = [('head', 'sword'), ('handF', 'sword'), ('head', 'pauldron'), ('sword', 'foreF'), ('handF', 'foreF'), ('head', 'body'), ('foreF', 'upperF'),
         ('foreN', 'body'), ('pauldron', 'upperN'), ('foreN', 'upperN'), ('pauldron', 'body'), ('upperN', 'body'), ('foreF', 'body'), ('handF', 'body'),
         ('body', 'legN'), ('body', 'legF'), ('sword', 'body'), ('head', 'handF'), ('body', 'cape'), ('foreN', 'cape'), ('pauldron', 'cape'), ('body', 'upperF'), ('sword', 'upperF')]
dark = lum < 70
for f, b in FRONT:
    near = dil(lab == LID[f], 2); mv = near & (lab == LID[b]) & dark; lab[mv] = LID[f]
for n in NAMES:
    if n == 'sword': continue
    m = (lab == LID[n]).astype(np.uint8); k, cc, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if k <= 2: continue
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    for j in range(1, k):
        if j == big or st[j, 4] > 600: continue
        isl = cc == j; ring = dil(isl, 1) & ~isl & (lab > 0) & (lab != LID[n]) & (lab != LID['sword'])
        if ring.any(): nb = np.bincount(lab[ring]).argmax(); lab[isl] = nb; print(f'  island {n} {int(st[j, 4])}px @({st[j, 0]},{st[j, 1]}) -> {NAMES[nb - 1]}')
# 먼 팔: 가죽 끈 오른쪽(x 376~400, y 228~325)의 몸 라벨은 먼 소매·토시 위 끝 → 먼 윗팔로 (몸에 남으면 팔이 떠난 뒤 남색 깃발처럼 보였음, 10-20 09:00)
_YY, _XX = np.mgrid[0:512, 0:512]; _m = (lab == LID['body']) & (_XX >= 376) & (_XX <= 400) & (_YY >= 228) & (_YY <= 325)
_nv = (np.abs(RA[..., :3].astype(int) - np.array([46, 45, 54])).max(-1) < 45) | (lum < 45)   # 남색 소매·외곽선 → 먼 윗팔, 나머지(크림·금·강철 = 토시 위 끝) → 먼 토시
lab[_m & _nv] = LID['upperF']; lab[_m & ~_nv] = LID['foreF']; print('  far sleeve from body', int((_m & _nv).sum()), 'vambrace', int((_m & ~_nv).sum()))
# 가까운 소매(upperN)에 섞인 남색 아닌 점(토시 윗선 밝은 점·가죽 띠 조각)은 이웃 부품으로 — 소매는 남색 관으로 메우므로
NAVY = np.array([46, 45, 54]); un = (lab == LID['upperN']) & (np.abs(RA[..., :3].astype(int) - NAVY).max(-1) >= 60) & (lum >= 45)
for y, x in zip(*np.nonzero(un)):
    win = lab[max(0, y - 4):y + 5, max(0, x - 4):x + 5].ravel(); win = win[(win > 0) & (win != LID['upperN'])]
    if len(win): lab[y, x] = np.bincount(win).argmax()
print('  upperN non-navy moved', int(un.sum()))
np.save(os.path.join(W, 'labels.npy'), lab)
COL = {'head': (255, 80, 80), 'sword': (80, 80, 255), 'handF': (255, 220, 0), 'foreF': (255, 140, 0), 'upperF': (0, 120, 120), 'pauldron': (0, 200, 200), 'upperN': (200, 0, 200),
       'foreN': (0, 180, 0), 'cape': (120, 0, 200), 'legN': (120, 60, 0), 'legF': (180, 120, 60), 'body': (160, 160, 160)}
ov = np.zeros((512, 512, 3), np.uint8)
for n, c in COL.items(): ov[lab == LID[n]] = c
base = RA[..., :3].astype(float) * .45 + ov * .55; base[~A] = 255
Image.fromarray(base.astype(np.uint8)).resize((1024, 1024), Image.NEAREST).save(os.path.join(RV, 'seg_labels.png'))
for n in NAMES: print(f'{n:9s} px {int((lab == LID[n]).sum())}')
