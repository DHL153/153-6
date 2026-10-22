"""5 러스트 바실 — 몸(두 팔·건틀릿 지운 원화를 합친 그림 work/body512.png)을 부품별로 나누기(씨앗 + watershed, 경계 = 외곽선) — seg20 구조
  몸 그림 = 원화 + 가까운 팔 자리는 프롬프트 2(nonear_2052), 먼 팔 자리는 프롬프트 3(nofar_2105) — 팔이 없으니 몸만 나눔
  팔 쪽(건틀릿·윗팔)은 build_basil5.py 에서 '원화 − 지운 원화'로 따로 오림
출력: work/body512.png · work/labels.npy · work/label_names.json · review/seg_labels.png
실행: python3 -I seg5.py
"""
import json, os
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work'); os.makedirs(W, exist_ok=True); os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
RA = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA')).astype(int)
B = RA.copy()
for nm in ('nonear_2052', 'nofar_2105'):
    X = np.array(Image.open(os.path.join(HERE, 'sheets', nm + '.png')).convert('RGBA')).astype(int)
    ch = cv2.dilate((np.abs(RA - X).max(-1) > 24).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    B[ch] = X[ch]
B = B.astype(np.uint8)
n_, cc_, st_, _ = cv2.connectedComponentsWithStats((B[..., 3] > 0).astype(np.uint8), 8)   # 떨어진 작은 섬 지움
for i in range(1, n_):
    if st_[i, 4] < 40: B[cc_ == i] = 0
Image.fromarray(B).save(os.path.join(W, 'body512.png'))
AL = B[..., 3] > 24; YY, XX = np.mgrid[0:512, 0:512].astype(float)
NAMES = ['head', 'pony', 'torso', 'belt', 'hips', 'legN', 'legF']
ID = {n: i + 1 for i, n in enumerate(NAMES)}
def disk(c, r): return (XX - c[0]) ** 2 + (YY - c[1]) ** 2 <= r * r
def D(*ps, r=5): return np.logical_or.reduce([disk(p, r) for p in ps])
seeds = {
  'pony': D((130, 70), (112, 118), (160, 58), (145, 95), (110, 140), (180, 118), (170, 132), (190, 60), (200, 82), (182, 45), r=5),
  'head': D((265, 215), (240, 135), (205, 165), (178, 205), (300, 252), (275, 100), (330, 150), (235, 250), r=6) | D((205, 215), (212, 238), (218, 252), (292, 190), (300, 172), r=3),
  'torso': D((150, 250), (140, 300), (330, 250), (320, 300), (255, 300), (285, 320), (215, 320), (255, 282), (175, 330), r=5),
  'belt': D((205, 356), (270, 372), (325, 368), (160, 360), (240, 372), r=4),
  'hips': D((175, 402), (250, 398), (318, 402), (145, 392), (290, 410), (210, 410), r=4),
  'legN': D((150, 440), (128, 462), (162, 425), (110, 470), r=4), 'legF': D((308, 440), (335, 462), (302, 425), (355, 470), r=4),
}
mk = np.zeros((512, 512), np.int32)
for n in NAMES: mk[seeds[n] & AL] = ID[n]
mk[~cv2.dilate(AL.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)] = 99
img = cv2.cvtColor(B[..., :3], cv2.COLOR_RGB2BGR); al = B[..., 3:4] / 255.0; img = (img * al + 255 * (1 - al)).astype(np.uint8)
ALLOW = {'pony': (YY < 165) & (XX < 215), 'head': (YY < 292) & ~((YY < 96) & (XX < 212)), 'belt': (YY > 330) & (YY < 396), 'hips': (YY > 372) & (YY < 445),
         'legN': (YY > 398) & (XX < 235), 'legF': (YY > 398) & (XX > 250), 'torso': (YY > 180) & (YY < 360)}
lab = None
for it in range(2):
    m_ = mk if lab is None else lab.astype(np.int32).copy()
    if lab is not None: m_[~cv2.dilate(AL.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)] = 99
    lab = cv2.watershed(img, m_.copy()); lab[lab < 0] = 0; lab[lab == 99] = 0
    for n, A_ in ALLOW.items(): lab[(lab == ID[n]) & ~A_] = 0
for _ in range(40):
    und = AL & (lab == 0)
    if not und.any(): break
    for n in range(1, len(NAMES) + 1):
        A_ = ALLOW.get(NAMES[n - 1], np.ones((512, 512), bool)); g = (cv2.dilate((lab == n).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & und & A_; lab[g] = n; und &= ~g
for _ in range(8):
    und = AL & (lab == 0)
    if not und.any(): break
    for n in range(1, len(NAMES) + 1): g = (cv2.dilate((lab == n).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & und; lab[g] = n; und &= ~g
edge = (B[..., 3] > 0) & (lab == 0)
for _ in range(3):
    for n in range(1, len(NAMES) + 1):
        g = (cv2.dilate((lab == n).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & edge; lab[g] = n; edge &= ~g
for bn in NAMES:   # 작은 섬(< 200px) → 둘레에 가장 많은 라벨
    n_, cc_, st_, _ = cv2.connectedComponentsWithStats((lab == ID[bn]).astype(np.uint8), 8)
    big = st_[1:, 4].max() if n_ > 1 else 0
    for i in range(1, n_):
        if st_[i, 4] >= 200 or st_[i, 4] == big: continue
        isl = cc_ == i; ring = (cv2.dilate(isl.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & ~isl; vals = lab[ring]; vals = vals[(vals > 0) & (vals != ID[bn])]
        if len(vals): lab[isl] = np.bincount(vals).argmax()
np.save(os.path.join(W, 'labels.npy'), lab.astype(np.uint8)); json.dump(NAMES, open(os.path.join(W, 'label_names.json'), 'w'))
pal = np.array([[0, 0, 0], [230, 80, 80], [255, 220, 120], [90, 160, 60], [255, 120, 200], [150, 100, 50], [60, 120, 230], [40, 200, 220]], np.uint8)
vis = pal[lab]; base = np.array(Image.fromarray(img[..., ::-1]).convert('RGB')).astype(float)
out = (base * .45 + vis * .55).astype(np.uint8); out[lab == 0] = base[lab == 0].astype(np.uint8)
Image.fromarray(out).resize((1024, 1024), Image.NEAREST).save(os.path.join(HERE, 'review', 'seg_labels.png'))
print({n: int((lab == ID[n]).sum()) for n in NAMES}, '빈 곳', int((AL & (lab == 0)).sum()))
