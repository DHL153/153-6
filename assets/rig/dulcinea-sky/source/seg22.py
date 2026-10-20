# 12 네온 둘시네: 새 원화를 부품별로 나누기 (29 스카이 팔로메 seg29.py 와 같은 watershed — 씨앗 = 다각형 대신 러스트 둘시네 부품 칸)
#   새 원화는 러스트 둘시네와 같은 자세·크기(프롬프트 0 합격선) → 러스트 원화 부품 칸(refs/rust_labels.npz, build_dulcinea 의 own)을 깎아 씨앗으로,
#   경계 띠는 새 원화 외곽선(어두운 선)을 따라 나눔. 외곽선은 앞 부품 것(FRONT), 떨어진 섬은 이웃으로.
#   python3 -I seg12.py [원화.png=ref512.png] [깎는 px=6] → work/labels.npy · review/seg_labels.png · 러스트와 같은 그림이면 일치율도
#   (10-20 07:35 원화 오기 전 준비 — 러스트 원화로 시험: 자기 칸 깎아 씨앗 → 다시 나눈 결과가 원래 칸과 얼마나 같은지)
import os, sys, json
import numpy as np, cv2
from PIL import Image
from skimage.segmentation import watershed
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work'); RV = os.path.join(HERE, 'review')
os.makedirs(W, exist_ok=True); os.makedirs(RV, exist_ok=True)
fn = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'ref512.png'); ER = int(sys.argv[2]) if len(sys.argv) > 2 else 6
RA = np.array(Image.open(fn).convert('RGBA')); A = RA[..., 3] > 40
L = np.load(os.path.join(HERE, 'refs', 'rust_labels.npz'))
# 러스트 칸 → 네온 부품 (포니테일·천자락은 네온에 없음: 천자락은 골반으로, 포니테일은 씨앗 안 씀 → 이웃이 차지)
MAP = {'head': ['head'], 'hammer': ['hammer'], 'fistF': ['fistF'], 'foreF': ['foreF'], 'padN': ['pauldron'], 'upperN': ['armU'], 'foreN': ['armL'],
       'torso': ['torso'], 'hips': ['hips', 'belt', 'flapC', 'flapN'], 'thighN': ['thighN'], 'thighF': ['thighF'], 'bootN': ['bootN'], 'bootF': ['bootF']}
NAMES = list(MAP); LID = {n: i + 1 for i, n in enumerate(NAMES)}
def ero(m, r): return cv2.erode(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0 if r > 0 else m
def dil(m, r): return cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
M = {n: np.logical_or.reduce([L[k] for k in ks]) for n, ks in MAP.items()}
POLYS = os.environ.get('POLYS')   # (10-20 08:43) 네온 새 원화용: 러스트 칸 대신 polys12.json 다각형을 씨앗으로 (POLYS=polys12.json)
RER = {'foreF': 2, 'upperN': 2, 'thighN': 3, 'thighF': 3, 'fistF': 4}   # 가는 부품은 조금만 깎음
seeds = np.zeros((512, 512), np.int32)
if POLYS:
    from PIL import ImageDraw
    PJ = json.load(open(os.path.join(HERE, POLYS)))
    def pm(pts):
        im_ = Image.new('L', (512, 512), 0); ImageDraw.Draw(im_).polygon([tuple(p) for p in pts], fill=255); return np.array(im_) > 0
    for n in NAMES: seeds[pm(PJ[n]) & A & (seeds == 0)] = LID[n]
    sh = PJ.get('_shaft')
    if sh:   # 자루 띠(축 위 구간 [t0, t1, 반폭]) = 망치 씨앗 — 주먹 위·아래로 보이는 자루
        yy_, xx_ = np.mgrid[0:512, 0:512].astype(float); Gs = np.array(sh['G'], float); Us = np.array(sh['U'], float); Us /= np.linalg.norm(Us)
        tu = (xx_ - Gs[0]) * Us[0] + (yy_ - Gs[1]) * Us[1]; tn = (xx_ - Gs[0]) * -Us[1] + (yy_ - Gs[1]) * Us[0]
        for t0, t1, hw in sh['hammer_bands']: seeds[(tu >= t0) & (tu <= t1) & (np.abs(tn) <= hw) & A] = LID['hammer']
    M = {n: pm(PJ[n]) for n in NAMES}   # 아래 '같은 곳' 비율 = 씨앗 다각형 기준
else:
    for n in NAMES:
        s = ero(M[n], RER.get(n, ER)) & A & (seeds == 0); seeds[s] = LID[n]
lum = RA[..., :3].astype(float).mean(-1)
elev = cv2.GaussianBlur((255 - lum).astype(np.float32), (3, 3), 0.7)
lab = watershed(elev, markers=seeds, mask=A)
# 겹친 곳의 외곽선(어두운 선)은 앞 부품 것 — 러스트 v6.4 그리는 순서(대기) 기준 앞 → 뒤
FRONT = [('fistF', 'hammer'), ('head', 'hammer'), ('foreN', 'padN'), ('padN', 'upperN'), ('foreN', 'upperN'), ('padN', 'torso'), ('upperN', 'torso'), ('head', 'torso'),
         ('foreN', 'torso'), ('foreN', 'hips'), ('fistF', 'foreF'), ('fistF', 'torso'), ('torso', 'foreF'), ('hammer', 'torso'), ('hammer', 'hips'), ('hips', 'thighN'), ('hips', 'thighF'),
         ('thighN', 'bootN'), ('thighF', 'bootF'), ('bootN', 'bootF'), ('hammer', 'thighF'), ('hammer', 'bootF'), ('fistF', 'hips')]
dark = lum < 70
for f, b in FRONT:
    near = dil(lab == LID[f], 2); mv = near & (lab == LID[b]) & dark; lab[mv] = LID[f]
for n in NAMES:   # 떨어진 작은 섬 → 이웃
    m = (lab == LID[n]).astype(np.uint8); k, cc, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if k <= 2: continue
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    for j in range(1, k):
        if j == big or st[j, 4] > 400: continue
        isl = cc == j; ring = dil(isl, 1) & ~isl & (lab > 0) & (lab != LID[n])
        if ring.any(): lab[isl] = np.bincount(lab[ring]).argmax()
np.save(os.path.join(W, 'labels.npy'), lab)
COL = {'head': (255, 80, 80), 'hammer': (80, 80, 255), 'fistF': (255, 220, 0), 'foreF': (255, 140, 0), 'padN': (0, 200, 200), 'upperN': (200, 0, 200), 'foreN': (0, 180, 0),
       'torso': (160, 160, 160), 'hips': (120, 90, 200), 'thighN': (120, 60, 0), 'thighF': (180, 120, 60), 'bootN': (60, 120, 60), 'bootF': (90, 160, 120)}
ov = np.zeros((512, 512, 3), np.uint8)
for n, c in COL.items(): ov[lab == LID[n]] = c
base = RA[..., :3].astype(float) * .45 + ov * .55; base[~A] = 255
tag = os.path.splitext(os.path.basename(fn))[0]
Image.fromarray(base.astype(np.uint8)).resize((1024, 1024), Image.NEAREST).save(os.path.join(RV, f'seg_{tag}.png'))
for n in NAMES:
    same = (lab == LID[n]) & M[n]; print(f'{n:7s} px {int((lab == LID[n]).sum()):6d}  러스트 칸과 같은 곳 {int(same.sum()) / max(1, int(M[n].sum())):.2f}')
print('→', os.path.join('review', f'seg_{tag}.png'))
