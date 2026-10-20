"""20 네온 브루노 — 원화를 부품별로 나누기(씨앗 + watershed, 경계 = 원화 외곽선) — 2026-10-21 06:23 (seg10 구조)
  10 과 다른 곳: 포니테일 없음 · 철퇴(띠 + 공 원) · 가까운 어깨갑 + 그 밑 검은 소매 = pauldN(가까운 맨살 윗팔이 상체 앞·어깨갑 밑으로 나오게 따로)
  씨앗: 철퇴 = 축 띠·공 원, 주먹 = 원, 팔뚝·윗팔 = 관절 사이 가는 캡슐, 나머지 = 손으로 찍은 원(4·3배 격자에서 읽음)
출력: work/labels.npy · work/label_names.json · review/seg_labels.png
실행: python3 -I seg20.py
"""
import json, os
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work'); os.makedirs(W, exist_ok=True); os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
RA = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA')); M = json.load(open(os.path.join(HERE, 'measure20.json')))
AL = RA[..., 3] > 24; YY, XX = np.mgrid[0:512, 0:512].astype(float)
NAMES = ['head', 'torso', 'hips', 'legN', 'legF', 'pauldN', 'upperN', 'foreN', 'fistN', 'maceN', 'upperF', 'foreF', 'fistF', 'maceF']
ID = {n: i + 1 for i, n in enumerate(NAMES)}
V = lambda p: np.array(p, float)
def cap(p, q, r):
    p, q = V(p), V(q); d = q - p; L2 = max(d @ d, 1e-9); t = np.clip(((XX - p[0]) * d[0] + (YY - p[1]) * d[1]) / L2, 0, 1)
    return (XX - (p[0] + t * d[0])) ** 2 + (YY - (p[1] + t * d[1])) ** 2 <= r * r
def disk(c, r): return (XX - c[0]) ** 2 + (YY - c[1]) ** 2 <= r * r
def mace(sd, big=False):
    s = M[sd]; Fi, B = V(s['fist']), V(s['ball']); ax = (B - Fi) / np.linalg.norm(B - Fi); nv = np.array([-ax[1], ax[0]]); L = np.linalg.norm(B - Fi)
    u = (XX - Fi[0]) * ax[0] + (YY - Fi[1]) * ax[1]; v = (XX - Fi[0]) * nv[0] + (YY - Fi[1]) * nv[1]
    if big: return ((u > -40) & (u < L) & (np.abs(v) < 15)) | disk(B, s['ballR'] + 8)
    return ((u > 24) & (u < L - 45) & (np.abs(v) < 4)) | disk(B, 34)
N, F = M['near'], M['far']
seeds = {
  'maceN': mace('near'), 'maceF': mace('far'),
  'fistN': disk(N['fist'], 9), 'fistF': disk(F['fist'], 9),
  'foreN': cap(N['EL'], N['WR'], 5) & ~disk(N['EL'], 6), 'foreF': cap(F['EL'], F['WR'], 5) & ~disk(F['EL'], 6),
  'upperN': cap((160, 308), (194, 326), 4) & ~disk(N['EL'], 7), 'upperF': cap((303, 343), F['EL'], 4) & ~disk(F['EL'], 7),
  'pauldN': disk((209, 314), 6) | disk((198, 306), 2),   # 크림 어깨갑만(밑 검은 천 = 상체, 자줏빛 띠·검은 고리 = 윗팔 — 색 표본으로 고침)
  'head': disk((222, 205), 20) | disk((180, 232), 9) | disk((282, 192), 10) | disk((303, 238), 7) | disk((268, 282), 12) | disk((240, 290), 5) | disk((252, 240), 6)
          | disk((214, 266), 4) | disk((257, 166), 5) | disk((190, 270), 5) | disk((300, 300), 5),
  'torso': disk((210, 341), 3) | disk((256, 345), 6) | disk((232, 340), 5) | disk((252, 326), 3) | disk((290, 345), 5) | disk((280, 326), 5) | disk((250, 360), 4),
  'hips': disk((252, 377), 5) | disk((216, 380), 4) | disk((290, 377), 4) | disk((235, 392), 3) | disk((265, 392), 3),
  'legN': disk((207, 428), 6) | disk((188, 467), 7) | disk((222, 402), 4) | disk((196, 450), 5), 'legF': disk((302, 426), 6) | disk((318, 468), 7) | disk((285, 402), 4) | disk((310, 450), 5),
}
mk = np.zeros((512, 512), np.int32)
for n in ['head', 'torso', 'hips', 'legN', 'legF', 'pauldN', 'upperN', 'upperF', 'foreN', 'foreF', 'maceN', 'maceF', 'fistN', 'fistF']:   # 뒤에 쓴 것이 이김
    mk[seeds[n] & AL] = ID[n]
mk[~cv2.dilate(AL.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)] = 99
img = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2BGR); al = RA[..., 3:4] / 255.0; img = (img * al + 255 * (1 - al)).astype(np.uint8)
lab = cv2.watershed(img, mk.copy()); lab[lab < 0] = 0; lab[lab == 99] = 0
ALLOW = {'maceN': mace('near', True), 'maceF': mace('far', True), 'fistN': disk(N['fist'], 25), 'fistF': disk(F['fist'], 25),
         'foreN': cap(N['EL'], N['WR'], 20), 'foreF': cap(F['EL'], F['WR'], 20), 'upperN': cap(N['SH'], N['EL'], 17), 'upperF': cap(F['SH'], F['EL'], 17),
         'pauldN': (XX > 160) & (XX < 236) & (YY > 288) & (YY < 346), 'hips': (YY > 352) & (YY < 402), 'legN': (YY > 380) & (XX < 262), 'legF': (YY > 378) & (XX > 238)}
for n, A_ in ALLOW.items(): lab[(lab == ID[n]) & ~A_] = 0
mk2 = lab.astype(np.int32).copy(); mk2[~cv2.dilate(AL.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)] = 99
lab = cv2.watershed(img, mk2); lab[lab < 0] = 0; lab[lab == 99] = 0
for n, A_ in ALLOW.items(): lab[(lab == ID[n]) & ~A_] = 0
und = AL & (lab == 0)
for _ in range(30):
    for n in range(1, len(NAMES) + 1):
        A_ = ALLOW.get(NAMES[n - 1], np.ones((512, 512), bool)); grow = (cv2.dilate((lab == n).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & und & A_; lab[grow] = n; und &= ~grow
for _ in range(8):
    und = AL & (lab == 0)
    if not und.any(): break
    for n in range(1, len(NAMES) + 1): g = (cv2.dilate((lab == n).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & und; lab[g] = n; und &= ~g
lab[~AL & (RA[..., 3] > 0)] = 0
edge = (RA[..., 3] > 0) & (lab == 0)
for _ in range(2):
    for n in range(1, len(NAMES) + 1):
        g = (cv2.dilate((lab == n).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & edge; lab[g] = n; edge &= ~g
# 앞 부품(철퇴·주먹·팔뚝·윗팔) 외곽선이 뒤 부품 라벨에 남은 것 → 앞 부품으로(49번 ③)
LUMI = RA[..., :3].astype(int).mean(-1)
for fr, bk in (('maceN', ('head',)), ('fistN', ('head',)), ('foreN', ('head', 'torso')), ('upperN', ('torso',)), ('maceF', ('head', 'torso')), ('fistF', ('torso',)), ('foreF', ('torso',))):
    near_fr = cv2.dilate((lab == ID[fr]).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    for bn in bk:
        mv = (lab == ID[bn]) & near_fr & (LUMI < 70) & ALLOW.get(fr, True); lab[mv] = ID[fr]
for bn in ('head', 'torso', 'hips', 'pauldN'):
    n_, cc_, st_, _ = cv2.connectedComponentsWithStats((lab == ID[bn]).astype(np.uint8), 8)
    for i in range(1, n_):
        if st_[i, 4] >= 300: continue
        isl = cc_ == i; ring = (cv2.dilate(isl.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & ~isl; vals = lab[ring]; vals = vals[(vals > 0) & (vals != ID[bn])]
        if len(vals): lab[isl] = np.bincount(vals).argmax()
np.save(os.path.join(W, 'labels.npy'), lab.astype(np.uint8)); json.dump(NAMES, open(os.path.join(W, 'label_names.json'), 'w'))
pal = np.array([[0, 0, 0], [230, 80, 80], [90, 160, 60], [150, 100, 50], [60, 120, 230], [40, 200, 220], [255, 170, 60], [120, 60, 160], [255, 220, 120], [255, 120, 200], [200, 200, 200], [100, 40, 120], [240, 240, 120], [220, 140, 255], [120, 120, 120]], np.uint8)
vis = pal[lab]; base = np.array(Image.fromarray(img[..., ::-1]).convert('RGB')).astype(float)
out = (base * .45 + vis * .55).astype(np.uint8); out[lab == 0] = base[lab == 0].astype(np.uint8)
Image.fromarray(out).resize((1024, 1024), Image.NEAREST).save(os.path.join(HERE, 'review', 'seg_labels.png'))
print({n: int((lab == ID[n]).sum()) for n in NAMES})
