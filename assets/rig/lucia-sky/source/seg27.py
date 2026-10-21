"""27 스카이 루시아 — 원화를 부품별로 나누기 (2026-10-21, seg17(17 네온) 구조 + 가까운 주먹(7 러스트처럼 방패 자식))
  ① 방패 + 가까운 주먹 = 원화 ↔ noshield 다른 곳 → 주먹(fistN)을 watershed 로 떼어 냄 · 먼 팔 + 도끼 = 원화 ↔ nofar 다른 곳
  ② 몸 그림 BODY = 원화에서 방패 자리는 noshield, 먼 팔 자리는 nofar 픽셀
  ③ 먼 팔 칸(원화) → axe · fistF · foreF(회색·금색 팔뚝 갑) · upF(남색 소매) · pauldron · 몸 칸(BODY) → head(투구·볏·가리개·얼굴·머리카락) · torso(스카프·가까운 어깨갑 포함) · hips · legN · legF
실행: python3 -I seg27.py"""
import json, os
import numpy as np, cv2
from scipy import ndimage
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work'); os.makedirs(W, exist_ok=True); os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
L = lambda p: np.array(Image.open(os.path.join(HERE, p)).convert('RGBA'))
RA, NS, NF = L('ref512.png'), L('sheets/noshield_1921.png'), L('sheets/nofar_1921.png')
M = json.load(open(os.path.join(HERE, 'measure27.json')))
YY, XX = np.mgrid[0:512, 0:512].astype(float)
V = lambda p: np.array(p, float)
def cap(p, q, r):
    p, q = V(p), V(q); d = q - p; L2 = max(d @ d, 1e-9); t = np.clip(((XX - p[0]) * d[0] + (YY - p[1]) * d[1]) / L2, 0, 1)
    return (XX - (p[0] + t * d[0])) ** 2 + (YY - (p[1] + t * d[1])) ** 2 <= r * r
def disk(c, r): return (XX - c[0]) ** 2 + (YY - c[1]) ** 2 <= r * r
def dil(m, r): return cv2.dilate(m.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0
def diff(a, b):
    a, b = a.astype(int), b.astype(int); pa = a[..., :3] * a[..., 3:4] / 255; pb = b[..., :3] * b[..., 3:4] / 255
    return (np.abs(pa - pb).max(-1) > 18) | (np.abs(a[..., 3] - b[..., 3]) > 30)
def big_only(m, minpx=60):
    n, l, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8); keep = np.zeros_like(m)
    for i in range(1, n):
        if st[i, 4] >= minpx: keep |= l == i
    return keep
AL = RA[..., 3] > 24
SHF = big_only(diff(RA, NS) & AL & (XX < 250))
SHF = AL & (XX < 250) & ndimage.binary_fill_holes(cv2.morphologyEx(SHF.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0)
_op = cv2.morphologyEx(SHF.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))) > 0
SHF &= dil(_op, 1)
FAR = big_only(diff(RA, NF) & AL & (XX > 320))
BODY = RA.copy(); BODY[SHF] = NS[SHF]; BODY[FAR] = NF[FAR]
_d = diff(RA, NS) & ~SHF; BODY[_d] = NS[_d]; _d = diff(RA, NF) & ~FAR; BODY[_d] = NF[_d]
n_, l_, st_, _ = cv2.connectedComponentsWithStats((BODY[..., 3] > 24).astype(np.uint8), 8)
_main = 1 + int(np.argmax(st_[1:, 4])); _junk = (l_ != _main) & (BODY[..., 3] > 0)
print('  BODY 떨어진 섬 지움', [(int(s[0]), int(s[1]), int(s[4])) for i, s in enumerate(st_) if i and i != _main])
BODY[_junk] = 0
FAR |= _junk & AL & (XX > 300) & (YY < 262)
Image.fromarray(BODY).save(os.path.join(W, 'body.png'))
BL = BODY[..., 3] > 24
def ws(img_rgba, mask, seeds, order, allow, front=()):
    """seeds: 이름 → bool, order 뒤가 이김. allow: 이름 → 허용 bool. front: (앞, 뒤들) — 경계 어두운 외곽선은 앞 부품으로"""
    ID = {n: i + 1 for i, n in enumerate(order)}
    mk = np.zeros((512, 512), np.int32)
    for n in order: mk[seeds[n] & mask] = ID[n]
    mk[~dil(mask, 1)] = 99
    al = img_rgba[..., 3:4] / 255.0; img = (cv2.cvtColor(img_rgba[..., :3], cv2.COLOR_RGB2BGR) * al + 255 * (1 - al)).astype(np.uint8)
    lab = cv2.watershed(img, mk.copy()); lab[(lab < 0) | (lab == 99)] = 0
    for n, A_ in allow.items(): lab[(lab == ID[n]) & ~A_] = 0
    mk2 = lab.astype(np.int32).copy(); mk2[~dil(mask, 1)] = 99
    lab = cv2.watershed(img, mk2); lab[(lab < 0) | (lab == 99)] = 0
    for n, A_ in allow.items(): lab[(lab == ID[n]) & ~A_] = 0
    for _ in range(40):
        und = mask & (lab == 0)
        if not und.any(): break
        for n in order:
            A_ = allow.get(n, np.ones((512, 512), bool)); g = dil(lab == ID[n], 1) & und & (A_ if _ < 30 else True); lab[g] = ID[n]; und &= ~g
    lab[~mask] = 0
    LUMI = img_rgba[..., :3].astype(int).mean(-1)
    for fr, bks in front:
        nf = dil(lab == ID[fr], 3)
        for bn in bks: lab[(lab == ID[bn]) & nf & (LUMI < 70) & allow.get(fr, True)] = ID[fr]
    for bn in order:   # 작은 섬 → 둘레 다수
        n2, cc, st, _ = cv2.connectedComponentsWithStats((lab == ID[bn]).astype(np.uint8), 8)
        if n2 <= 2: continue
        bigi = 1 + int(np.argmax(st[1:, 4]))
        for i in range(1, n2):
            if i == bigi or st[i, 4] >= 150: continue
            isl = cc == i; ring = dil(isl, 2) & ~isl; vals = lab[ring]; vals = vals[(vals > 0) & (vals != ID[bn])]
            if len(vals): lab[isl] = np.bincount(vals).argmax()
    return {n: lab == ID[n] for n in order}
F = M['far']
# ③-0 방패 ↔ 가까운 주먹 (원화 픽셀)
FN_ = M['FIST_N']
SL0 = ws(RA, SHF, {'shield': SHF & ((XX < 205) | (YY < 316) | (YY > 366)), 'fistN': disk(FN_, 5)}, ['shield', 'fistN'], {'fistN': disk(FN_, 22) & (XX > 212)})   # 방패 오른쪽 검은 테는 방패 칸(주먹을 지워도 방패 외곽선이 남게 — DHL 20:33)
SHIELD, FISTN = SL0['shield'], SL0['fistN']
# ③-가 먼 팔 칸 나누기(원화 픽셀)
far_seeds = {
    'pauldron': disk((365, 276), 7) | disk((350, 264), 3) | disk((386, 292), 3),
    'upF': disk((368, 322), 4) | disk((360, 332), 2),
    'foreF': disk((400, 326), 6) | disk((388, 340), 3) | disk((416, 316), 2),
    'fistF': disk((432, 288), 10),
    'axe': (FAR & (YY < 250) & ~disk((365, 276), 30)) | cap((446, 335), (450, 356), 3),
}
far_allow = {'pauldron': (YY < 316) & (XX < 400) & (XX >= 338), 'upF': cap(F['SH'], F['EL'], 20) & (XX < 392), 'foreF': cap(F['EL'], F['WR'], 26) | ((YY > 330) & (XX < 436)),
             'fistF': disk(F['G'], 32) & (YY > 267), 'axe': (YY < 262) | cap((442, 316), (456, 365), 17)}
FL = ws(RA, FAR, far_seeds, ['pauldron', 'upF', 'foreF', 'axe', 'fistF'], far_allow,
        front=(('fistF', ('axe', 'foreF')), ('foreF', ('pauldron', 'upF')), ('upF', ('pauldron',))))
# ③-나 몸 칸 나누기(BODY 픽셀)
body_seeds = {
    'head': disk((292, 198), 10) | disk((240, 195), 5) | disk((330, 205), 4) | disk((300, 272), 8) | disk((332, 245), 3) | disk((232, 238), 4) | disk((268, 262), 4) | disk((315, 160), 6),
    'torso': disk((305, 318), 7) | disk((250, 305), 5) | disk((213, 278), 6) | disk((340, 315), 4) | disk((232, 330), 4) | disk((270, 330), 3),
    'hips': disk((295, 350), 5) | disk((250, 348), 4) | disk((338, 347), 3) | disk((285, 382), 5) | disk((265, 372), 3) | disk((305, 395), 2),
    'legN': disk((215, 390), 6) | disk((205, 436), 5) | disk((232, 418), 3),
    'legF': disk((346, 396), 6) | disk((330, 436), 5) | disk((320, 415), 3),
}
body_allow = {'head': (YY < 302), 'hips': (YY > 333) & (YY < 406) & ~((YY > 368) & ((XX < 245) | (XX > 318))),
              'legN': (YY > 360) & (XX < 268), 'legF': (YY > 362) & (XX > 298)}
BLB = ws(BODY, BL, body_seeds, ['torso', 'hips', 'legN', 'legF', 'head'], body_allow,
         front=(('head', ('torso',)), ('hips', ('legN', 'legF', 'torso'))))
NAMES = ['head', 'torso', 'hips', 'legN', 'legF', 'shield', 'fistN', 'pauldron', 'upF', 'foreF', 'axe', 'fistF']
lab = np.zeros((512, 512), np.uint8); labB = np.zeros((512, 512), np.uint8)
for i, n in enumerate(NAMES):
    if n in BLB:
        labB[BLB[n]] = i + 1; lab[BLB[n] & ~SHF & ~FAR & AL] = i + 1
lab[SHIELD] = NAMES.index('shield') + 1; lab[FISTN] = NAMES.index('fistN') + 1
for n, m in FL.items(): lab[m] = NAMES.index(n) + 1
lab[FAR & (lab == 0)] = NAMES.index('foreF') + 1
np.save(os.path.join(W, 'labels.npy'), lab); np.save(os.path.join(W, 'labels_body.npy'), labB); json.dump(NAMES, open(os.path.join(W, 'label_names.json'), 'w'))
print('  원화 칸', {n: int((lab == i + 1).sum()) for i, n in enumerate(NAMES)}, '· 빈 불투명', int((AL & (lab == 0)).sum()))
print('  BODY 칸', {n: int((labB == i + 1).sum()) for i, n in enumerate(NAMES) if n in BLB}, '· 빈 불투명', int((BL & (labB == 0)).sum()))
pal = np.array([[0, 0, 0], [230, 80, 80], [255, 0, 200], [90, 160, 60], [150, 100, 50], [60, 120, 230], [40, 200, 220], [60, 60, 255], [0, 200, 120], [255, 170, 60],
                [255, 140, 0], [0, 200, 255], [255, 220, 0], [120, 255, 120]], np.uint8)
def vis(img, lb):
    al = img[..., 3:4] / 255.0; base = (img[..., :3] * al + 255 * (1 - al)); out = (base * .45 + pal[lb] * .55).astype(np.uint8); out[lb == 0] = base[lb == 0].astype(np.uint8); return out
Image.fromarray(np.hstack([vis(RA, lab), np.full((512, 6, 3), 255, np.uint8), vis(BODY, labB)])).resize((2060, 1024), Image.NEAREST).save(os.path.join(HERE, 'review', 'seg27_labels.png'))
print('  그림 review/seg27_labels.png')
