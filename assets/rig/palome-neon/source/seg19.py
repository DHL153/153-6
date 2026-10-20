# 19 네온 팔로메: 새 원화(러스트 9 자세)를 부품별로 나누기 — 29 seg29.py 와 같은 방식, 망토 없음 (2026-10-20 18:40 준비)
#   대략 다각형(polys19.json) 안쪽 = 씨앗, 경계 띠는 원화 외곽선(어두운 선)을 따라 watershed. 외곽선은 앞 부품 것(FRONT 쌍), 떨어진 섬은 이웃으로(칼 제외)
#   칼 = polys19.json 'sword' 의 날밑·칼끝·폼멜 점(가이드 ref_sword_fit19 자리)에서 날 띠·날밑 띠·손잡이 띠·폼멜 원
#   먼 윗팔(upperF)은 polys 에 있을 때만(프롬프트 0 = 먼 윗팔은 수염·몸 뒤로 숨음)
#   출력: work/labels.npy · work/label_names.json · review/seg_labels.png
#   실행: python3 -I seg19.py [원화.png]   (기본 = source/ref512.png)
import json, os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw
from skimage.segmentation import watershed
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work'); RV = os.path.join(HERE, 'review')
os.makedirs(W, exist_ok=True); os.makedirs(RV, exist_ok=True)
ART = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'ref512.png')
if not os.path.exists(ART): sys.exit(f'원화 없음: {ART} — 새 원화를 source/ref512.png 로 넣거나 경로를 주세요')
RA = np.array(Image.open(ART).convert('RGBA'))
if RA.shape[:2] != (512, 512): RA = np.array(Image.open(ART).convert('RGBA').resize((512, 512), Image.LANCZOS))
A = RA[..., 3] > 40
PO = json.load(open(os.path.join(HERE, 'polys19.json')))
NAMES = ['head', 'sword', 'handF', 'foreF'] + (['upperF'] if 'upperF' in PO else []) + ['pauldron', 'upperN', 'foreN', 'legN', 'legF', 'body']
LID = {n: i + 1 for i, n in enumerate(NAMES)}
def poly(pts):
    m = Image.new('L', (512, 512), 0); ImageDraw.Draw(m).polygon([tuple(map(float, p)) for p in pts], fill=255); return np.array(m) > 0
def ero(m, r): return cv2.erode(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
def dil(m, r): return cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
# 칼: 날밑 G → 칼끝 T 축(u), 날 띠 ±bladeHW, 날밑 = 축 방향 guardHW[0] · 옆 guardHW[1], 손잡이 G → 폼멜 ±handleHW, 폼멜 원
S = PO['sword']; G, T, P = (np.array(S[k], float) for k in ('guard', 'tip', 'pommel'))
u = (T - G) / np.linalg.norm(T - G); nr = np.array([-u[1], u[0]])
YY, XX = np.mgrid[0:512, 0:512]; D = np.stack([XX - G[0], YY - G[1]], -1); tg, sg = D @ u, D @ nr
L = np.linalg.norm(T - G)
blade = (tg >= 0) & (tg <= L + 4) & (np.abs(sg) <= S['bladeHW'] * np.clip((L + 4 - tg) / 30, 0.25, 1))   # 칼끝 쪽은 좁게
guard = (np.abs(tg) <= S['guardHW'][0]) & (np.abs(sg) <= S['guardHW'][1])
uh = (P - G) / np.linalg.norm(P - G); nh = np.array([-uh[1], uh[0]]); Dh = D @ uh; Sh = D @ nh
handle = (Dh >= 0) & (Dh <= np.linalg.norm(P - G)) & (np.abs(Sh) <= S['handleHW'])
pommel = np.hypot(XX - P[0], YY - P[1]) <= S['pommelR']
M = {'sword': blade | guard | handle | pommel}
for n in NAMES:
    if n not in ('sword', 'body'): M[n] = poly(PO[n])
FRONT_ORDER = ['handF', 'head', 'foreN', 'pauldron', 'upperN', 'foreF', 'sword'] + (['upperF'] if 'upperF' in PO else []) + ['legN', 'legF']   # 겹치는 다각형에서 앞이 이김
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
         ('body', 'legN'), ('body', 'legF'), ('sword', 'body'), ('head', 'handF'), ('head', 'foreF'), ('body', 'upperF'), ('sword', 'upperF')]
dark = lum < 70
for f, b in FRONT:
    if f not in LID or b not in LID: continue
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
# 가까운 소매(upperN)에 섞인 소매 색 아닌 점(토시 윗선 밝은 점·끈 조각)은 이웃 부품으로 — polys19.json 'sleeveRGB'(새 원화에서 잼)가 있을 때만
if 'sleeveRGB' in PO:
    SL = np.array(PO['sleeveRGB']); un = (lab == LID['upperN']) & (np.abs(RA[..., :3].astype(int) - SL).max(-1) >= 60) & (lum >= 45)
    for y, x in zip(*np.nonzero(un)):
        win = lab[max(0, y - 4):y + 5, max(0, x - 4):x + 5].ravel(); win = win[(win > 0) & (win != LID['upperN'])]
        if len(win): lab[y, x] = np.bincount(win).argmax()
    print('  upperN non-sleeve moved', int(un.sum()))
np.save(os.path.join(W, 'labels.npy'), lab); json.dump(NAMES, open(os.path.join(W, 'label_names.json'), 'w'))
COL = {'head': (255, 80, 80), 'sword': (80, 80, 255), 'handF': (255, 220, 0), 'foreF': (255, 140, 0), 'upperF': (0, 120, 120), 'pauldron': (0, 200, 200), 'upperN': (200, 0, 200),
       'foreN': (0, 180, 0), 'legN': (120, 60, 0), 'legF': (180, 120, 60), 'body': (160, 160, 160)}
ov = np.zeros((512, 512, 3), np.uint8)
for n in NAMES: ov[lab == LID[n]] = COL[n]
base = RA[..., :3].astype(float) * .45 + ov * .55; base[~A] = 255
Image.fromarray(base.astype(np.uint8)).resize((1024, 1024), Image.NEAREST).save(os.path.join(RV, 'seg_labels.png'))
for n in NAMES: print(f'{n:9s} px {int((lab == LID[n]).sum())}')
