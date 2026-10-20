"""10 러스트 브루노 — 원화를 부품별로 나누기(씨앗 + watershed, 경계 = 원화 외곽선) — 2026-10-20 22:45
  씨앗: 도끼 = 축 띠·머리 상자(guides10 와 같은 꼴), 주먹 = 주먹 가운데 원, 팔뚝·소매 = 관절 사이 가는 캡슐, 나머지 = 손으로 찍은 원(머리·포니테일·상체·골반·두 다리)
출력: work/labels.npy · work/label_names.json · review/seg_labels.png
실행: python3 -I seg10.py
"""
import json, os
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work'); os.makedirs(W, exist_ok=True)
RA = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA')); M = json.load(open(os.path.join(HERE, 'measure10.json')))
AL = RA[..., 3] > 24; YY, XX = np.mgrid[0:512, 0:512].astype(float)
NAMES = ['head', 'pony', 'torso', 'hips', 'legN', 'legF', 'upperN', 'foreN', 'fistN', 'axeN', 'upperF', 'foreF', 'fistF', 'axeF']
ID = {n: i + 1 for i, n in enumerate(NAMES)}
V = lambda p: np.array(p, float)
def cap(p, q, r):
    p, q = V(p), V(q); d = q - p; L2 = max(d @ d, 1e-9); t = np.clip(((XX - p[0]) * d[0] + (YY - p[1]) * d[1]) / L2, 0, 1)
    return (XX - (p[0] + t * d[0])) ** 2 + (YY - (p[1] + t * d[1])) ** 2 <= r * r
def disk(c, r): return (XX - c[0]) ** 2 + (YY - c[1]) ** 2 <= r * r
def axe(sd, shrink=0, big=False):
    s = M[sd]; Fi, Hd = V(s['fist']), V(s['head']); ax = (Hd - Fi) / np.linalg.norm(Hd - Fi); nv = np.array([-ax[1], ax[0]]); hu = np.linalg.norm(Hd - Fi)
    u = (XX - Fi[0]) * ax[0] + (YY - Fi[1]) * ax[1]; v = (XX - Fi[0]) * nv[0] + (YY - Fi[1]) * nv[1]
    if big: return ((u > -34) & (u < hu) & (np.abs(v) < 13)) | ((u > hu - 75) & (u < hu + 90) & (v > -70) & (v < 108))
    return ((u > -30 + shrink) & (u < hu) & (np.abs(v) < 9 - shrink)) | ((u > hu - 50) & (u < hu + 70) & (v > -55) & (v < 85))
N, F = M['near'], M['far']
seeds = {
  'axeN': axe('near', 3) & ~disk(N['fist'], 22), 'axeF': axe('far', 3) & ~disk(F['fist'], 22),
  'fistN': disk(N['fist'], 11), 'fistF': disk(F['fist'], 11),
  'foreN': cap(N['EL'], N['WR'], 6) & ~disk(N['EL'], 5), 'foreF': cap(F['EL'], F['WR'], 6) & ~disk(F['EL'], 4),
  'upperN': cap(N['EL'], (np.array(N['EL']) * .6 + np.array(N['SH']) * .4), 3) & ~disk(N['EL'], 8), 'upperF': cap(F['EL'], (np.array(F['EL']) * .6 + np.array(F['SH']) * .4), 3) & ~disk(F['EL'], 8),
  'pony': ((XX < 118) & (YY > 382)),
  'head': disk((240, 200), 25) | disk((262, 262), 14) | disk((205, 245), 10) | disk((120, 300), 22) | disk((80, 330), 12) | disk((170, 210), 14) | disk((290, 215), 10)
          | disk((292, 248), 6) | disk((289, 272), 5) | disk((266, 286), 5) | disk((130, 352), 10) | disk((170, 352), 8) | disk((95, 360), 8) | disk((60, 345), 6),
  'torso': disk((215, 330), 7) | disk((250, 318), 7) | disk((285, 340), 7) | disk((245, 290), 4),
  'hips': disk((248, 368), 6) | disk((205, 374), 6) | disk((288, 372), 5) | disk((228, 384), 4) | disk((262, 384), 4),
  'legN': disk((206, 428), 6) | disk((186, 470), 8) | disk((218, 402), 5) | disk((196, 450), 5), 'legF': disk((290, 428), 6) | disk((310, 468), 8) | disk((276, 402), 4) | disk((300, 450), 5),
}
mk = np.zeros((512, 512), np.int32)
for n in ['pony', 'head', 'torso', 'hips', 'legN', 'legF', 'upperN', 'upperF', 'foreN', 'foreF', 'axeN', 'axeF', 'fistN', 'fistF']:   # 뒤에 쓴 것이 이김
    mk[seeds[n] & AL] = ID[n]
mk[~cv2.dilate(AL.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)] = 99   # 배경
img = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2BGR); al = RA[..., 3:4] / 255.0; img = (img * al + 255 * (1 - al)).astype(np.uint8)
lab = cv2.watershed(img, mk.copy()); lab[lab < 0] = 0; lab[lab == 99] = 0
# 경계선(-1) 픽셀 → 이웃 중 많은 라벨
und = AL & (lab == 0)
for _ in range(3):
    if not und.any(): break
    for n in range(1, len(NAMES) + 1):
        grow = (cv2.dilate((lab == n).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & und; lab[grow] = n; und &= ~grow
# 자리 제한(첫 결과: 먼 도끼가 얼굴 오른쪽 머리카락으로, 포니테일이 머리숱·골반으로 번짐) → 제한 밖은 지우고 다시 watershed(고정 씨앗 = 남은 라벨)
ALLOW = {'axeN': axe('near', big=True), 'axeF': axe('far', big=True),
         'pony': (XX < 130) & (YY > 374), 'fistN': disk(N['fist'], 25), 'fistF': disk(F['fist'], 25), 'foreN': cap(N['EL'], N['WR'], 18), 'foreF': cap(F['EL'], F['WR'], 18),
         'upperN': cap(N['SH'], N['EL'], 15), 'upperF': cap(F['SH'], F['EL'], 15), 'hips': (YY > 350) & (YY < 398), 'legN': (YY > 376) & (XX < 262), 'legF': (YY > 376) & (XX > 232)}
for n, A_ in ALLOW.items(): lab[(lab == ID[n]) & ~A_] = 0
mk2 = lab.astype(np.int32).copy(); mk2[mk2 == 0] = 0; mk2[~cv2.dilate(AL.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)] = 99
lab = cv2.watershed(img, mk2); lab[lab < 0] = 0; lab[lab == 99] = 0
for n, A_ in ALLOW.items(): lab[(lab == ID[n]) & ~A_] = 0   # 2차에서도 넘친 것은 이웃 허용 라벨로
und = AL & (lab == 0)
for _ in range(30):
    for n in range(1, len(NAMES) + 1):
        A_ = ALLOW.get(NAMES[n - 1], np.ones((512, 512), bool)); grow = (cv2.dilate((lab == n).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & und & A_; lab[grow] = n; und &= ~grow
for _ in range(8):   # 남은 몇 px(도끼 날 끝 외곽선 등) = 가장 가까운 라벨
    und = AL & (lab == 0)
    if not und.any(): break
    for n in range(1, len(NAMES) + 1): g = (cv2.dilate((lab == n).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & und; lab[g] = n; und &= ~g
lab[~AL & (RA[..., 3] > 0)] = 0
for n in range(1, len(NAMES) + 1):   # 경계 안쪽 반투명 가장자리도 같은 라벨(알파 > 0)
    pass
edge = (RA[..., 3] > 0) & (lab == 0)
for _ in range(2):
    for n in range(1, len(NAMES) + 1):
        g = (cv2.dilate((lab == n).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & edge; lab[g] = n; edge &= ~g
# 앞 부품(도끼·주먹·팔뚝) 외곽선이 뒤 부품(머리·상체) 라벨에 남은 것 → 앞 부품으로(첫 렌더: 가까운 도끼가 움직이면 머리 옆에 자루 외곽선 줄이 남음 — 49번 ③)
LUMI = RA[..., :3].astype(int).mean(-1)
for fr, bk in (('axeN', ('head', 'torso', 'pony')), ('fistN', ('head', 'torso')), ('foreN', ('head', 'torso')), ('upperN', ('torso', 'head')), ('axeF', ('head', 'torso')), ('fistF', ('torso', 'head')), ('foreF', ('torso',))):
    near_fr = cv2.dilate((lab == ID[fr]).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    for bn in bk:
        mv = (lab == ID[bn]) & near_fr & (LUMI < 70); lab[mv] = ID[fr]
# 작은 조각(머리·상체 라벨의 떨어진 섬 < 300px — 도끼 자루 가장자리 등) → 둘레에서 가장 많은 다른 라벨로
for bn in ('head', 'torso', 'hips', 'pony'):
    n_, cc_, st_, _ = cv2.connectedComponentsWithStats((lab == ID[bn]).astype(np.uint8), 8)
    for i in range(1, n_):
        if st_[i, 4] >= 300: continue
        isl = cc_ == i; ring = (cv2.dilate(isl.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & ~isl; vals = lab[ring]; vals = vals[(vals > 0) & (vals != ID[bn])]
        if len(vals): lab[isl] = np.bincount(vals).argmax()
np.save(os.path.join(W, 'labels.npy'), lab.astype(np.uint8)); json.dump(NAMES, open(os.path.join(W, 'label_names.json'), 'w'))
pal = np.array([[0, 0, 0], [230, 80, 80], [255, 170, 60], [90, 160, 60], [150, 100, 50], [60, 120, 230], [40, 200, 220], [120, 60, 160], [255, 220, 120], [255, 120, 200], [200, 200, 200], [100, 40, 120], [240, 240, 120], [220, 140, 255], [120, 120, 120]], np.uint8)
vis = pal[lab]; base = np.array(Image.fromarray(img[..., ::-1]).convert('RGB')).astype(float)
out = (base * .45 + vis * .55).astype(np.uint8); out[lab == 0] = base[lab == 0].astype(np.uint8)
Image.fromarray(out).resize((1024, 1024), Image.NEAREST).save(os.path.join(HERE, 'review', 'seg_labels.png'))
print({n: int((lab == ID[n]).sum()) for n in NAMES})
