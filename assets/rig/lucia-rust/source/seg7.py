# 7 러스트 루시아: 새 원화(27 자세)를 부품별로 나누기 — 19 seg19.py 와 같은 방식(대략 다각형 씨앗 + 원화 외곽선 따라 watershed) (10-20 20:40)
#   부품: head(투구·볏·가리개·머리카락) · shield · handN(방패 쥔 가까운 주먹) · axe(날·쇠 목·자루·마개) · handF(먼 주먹) · foreF(먼 팔 소매·팔뚝·손목 띠) · pauldron(먼 어깨 보호대) · hips(허리띠·튜닉 자락) · legN · legF · body(상체: 목도리·튜닉·가죽 끈)
#   도끼 = polys7.json 'axe' 의 날 다각형 + 자루 띠(마개 → 쇠 목 축 ±handleHW) + 마개 원
#   출력: work/labels.npy · work/label_names.json · review/seg_labels.png ·   실행: python3 -I seg7.py [원화.png]
import json, os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw
from skimage.segmentation import watershed
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work'); RV = os.path.join(HERE, 'review')
os.makedirs(W, exist_ok=True); os.makedirs(RV, exist_ok=True)
ART = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'ref512.png')
RA = np.array(Image.open(ART).convert('RGBA')); A = RA[..., 3] > 40
PO = json.load(open(os.path.join(HERE, 'polys7.json')))
NAMES = ['head', 'shield', 'handN', 'axe', 'handF', 'foreF', 'pauldron', 'hips', 'legN', 'legF', 'body']
LID = {n: i + 1 for i, n in enumerate(NAMES)}
def poly(pts):
    m = Image.new('L', (512, 512), 0); ImageDraw.Draw(m).polygon([tuple(map(float, p)) for p in pts], fill=255); return np.array(m) > 0
def ero(m, r): return cv2.erode(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
def dil(m, r): return cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
X = PO['axe']; P, C = np.array(X['pommel'], float), np.array(X['collar'], float)
u = (C - P) / np.linalg.norm(C - P); nr = np.array([-u[1], u[0]])
YY, XX = np.mgrid[0:512, 0:512]; D = np.stack([XX - P[0], YY - P[1]], -1); t_, s_ = D @ u, D @ nr
handle = (t_ >= -4) & (t_ <= np.linalg.norm(C - P) + 6) & (np.abs(s_) <= X['handleHW'])
M = {'axe': poly(X['blade']) | handle | (np.hypot(XX - P[0], YY - P[1]) <= X['pommelR'])}
for n in NAMES:
    if n not in ('axe', 'body'): M[n] = poly(PO[n])
FRONT_ORDER = ['handN', 'shield', 'handF', 'axe', 'head', 'pauldron', 'foreF', 'legN', 'legF', 'hips']   # 겹치는 다각형에서 앞이 이김(원화 겹침 순서)
seeds = np.zeros((512, 512), np.int32); taken = np.zeros((512, 512), bool)
for n in FRONT_ORDER:
    r = 2 if n in ('handN', 'handF', 'foreF', 'legN', 'legF') else 3
    s = ero(M[n], r) & A & ~taken; seeds[s] = LID[n]; taken |= s
others = np.zeros((512, 512), bool)
for n in FRONT_ORDER: others |= M[n]
seeds[A & ~dil(others, 4) & (seeds == 0)] = LID['body']
lum = RA[..., :3].astype(float).mean(-1)
elev = cv2.GaussianBlur((255 - lum).astype(np.float32), (3, 3), 0.7)
lab = watershed(elev, markers=seeds, mask=A)
# 경계 외곽선(어두운 선)은 앞 부품 것
FRONT = [('shield', 'head'), ('shield', 'body'), ('shield', 'legN'), ('shield', 'hips'), ('handN', 'shield'), ('handN', 'body'), ('handN', 'hips'),
         ('handF', 'axe'), ('handF', 'foreF'), ('pauldron', 'body'), ('pauldron', 'head'), ('pauldron', 'foreF'), ('head', 'body'), ('foreF', 'body'),
         ('hips', 'body'), ('hips', 'legN'), ('hips', 'legF'), ('foreF', 'hips')]
dark = lum < 70
for f, b in FRONT:
    near = dil(lab == LID[f], 2); mv = near & (lab == LID[b]) & dark; lab[mv] = LID[f]
for n in NAMES:
    m = (lab == LID[n]).astype(np.uint8); k, cc, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if k <= 2: continue
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    for j in range(1, k):
        if j == big or st[j, 4] > 600: continue
        isl = cc == j; ring = dil(isl, 1) & ~isl & (lab > 0) & (lab != LID[n])
        if ring.any(): nb = np.bincount(lab[ring]).argmax(); lab[isl] = nb; print(f'  island {n} {int(st[j, 4])}px @({st[j, 0]},{st[j, 1]}) -> {NAMES[nb - 1]}')
np.save(os.path.join(W, 'labels.npy'), lab); json.dump(NAMES, open(os.path.join(W, 'label_names.json'), 'w'))
COL = {'head': (255, 80, 80), 'shield': (60, 60, 255), 'handN': (255, 0, 255), 'axe': (0, 200, 255), 'handF': (255, 220, 0), 'foreF': (255, 140, 0),
       'pauldron': (0, 200, 120), 'hips': (150, 90, 30), 'legN': (120, 200, 0), 'legF': (0, 120, 60), 'body': (170, 170, 170)}
ov = np.zeros((512, 512, 3), np.uint8)
for n in NAMES: ov[lab == LID[n]] = COL[n]
base = RA[..., :3].astype(float) * .45 + ov * .55; base[~A] = 255
img = Image.fromarray(base.astype(np.uint8)).resize((1024, 1024), Image.NEAREST); d = ImageDraw.Draw(img)
for n in NAMES:
    ys, xs = np.nonzero(lab == LID[n])
    if len(xs): d.text((int(xs.mean() * 2) - 12, int(ys.mean() * 2)), n, fill=(0, 0, 0))
img.save(os.path.join(RV, 'seg_labels.png'))
for n in NAMES: print(f'{n:9s} px {int((lab == LID[n]).sum())}')
