"""17 네온 루시아 — 원화를 부품별로 나누기 (2026-10-21, seg7·seg20 구조 + 지운 원화 두 장)
  ① 방패 = 원화 ↔ 방패만 지운 원화(sheets/noshield_1132.png) 다른 곳 · 먼 팔 + 도끼 = 원화 ↔ 먼 팔·도끼만 지운 원화(sheets/nofar_1136.png) 다른 곳
  ② 몸 그림 BODY = 원화에서 방패 자리는 noshield, 먼 팔 자리는 nofar 픽셀로 바꾼 것(방패·먼 팔 없는 온전한 몸) — 떨어진 부스러기 섬 지움
  ③ 먼 팔 칸(원화 픽셀) → axe · fistF · foreF(크림 팔뚝 갑 + 회색 손목 고리) · upF(회색 네모 윗팔 판 + 금색 줄 + 짙은 소매) · pauldron(크림 둥근 어깨갑)
     몸 칸(BODY 픽셀) → head(모자·머리·얼굴·귀) · collar(짙은 회색 목 가리개 — 상체에 붙고 머리 앞) · torso · hips(허리띠 + 가운데 크림 허리 판) · legN · legF
  씨앗 = 격자 확대(grid17.py 4·5배)에서 읽은 원 · 캡슐, 경계 = 외곽선 watershed (cv2), 허용 구역 밖은 다시 나눔
출력: work/labels.npy(원화 기준 — 방패·먼 팔 칸은 원화 픽셀 주인) · work/labels_body.npy(BODY 기준 몸 칸) · work/body.png · work/label_names.json · review/seg17_labels.png
실행: python3 -I seg17.py
"""
import json, os
import numpy as np, cv2
from scipy import ndimage
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work'); os.makedirs(W, exist_ok=True); os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
L = lambda p: np.array(Image.open(os.path.join(HERE, p)).convert('RGBA'))
RA, NS, NF = L('ref512.png'), L('sheets/noshield_1132.png'), L('sheets/nofar_1136.png')
M = json.load(open(os.path.join(HERE, 'measure17.json')))
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
# ① 방패·먼 팔 칸 (원화 픽셀)
SHIELD = big_only(diff(RA, NS) & AL & (XX < 250))
SHIELD = AL & (XX < 250) & ndimage.binary_fill_holes(cv2.morphologyEx(SHIELD.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0)   # 원화·지운 원화 색이 우연히 같은 방패 테 점(초록 반점) 메움
_op = cv2.morphologyEx(SHIELD.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))) > 0
SHIELD &= dil(_op, 1)   # 방패 오른쪽 테 밖 가는 부스러기(무릎판·다리 흰 테 끝, 머리카락 끝 — 원화에서 방패 테에 닿은 1~2px 줄) → 몸으로. 달릴 때 방패 옆에 흰·회색 줄로 남았음(DHL 12:27 '방패쪽 지저분한 것')
#   방패 오른쪽 아래 곧은 테(y 300~446) = 줄마다 오른쪽 끝에 바깥으로만 튀는 점을 빼며 맞춘 직선 — y 340 아래에서 선 + 1.5px 밖(가까운 무릎판 왼쪽 4~9px 띠가 방패 칸에 들어가 있었음)은 몸으로
_ys = np.arange(300, 446); _xr = np.array([np.nonzero(SHIELD[y])[0].max() for y in _ys], float); _kp = np.ones(len(_ys), bool)
for _ in range(8): _ln = np.polyfit(_ys[_kp], _xr[_kp], 1); _kp = _xr - np.polyval(_ln, _ys) <= 1.0
SHIELD &= ~((YY >= 340) & (YY <= 446) & (XX > np.polyval(_ln, YY) + 1.5))
FAR = big_only(diff(RA, NF) & AL & (XX > 296))
# ② 몸 그림
BODY = RA.copy(); BODY[SHIELD] = NS[SHIELD]; BODY[FAR] = NF[FAR]
_d = diff(RA, NS) & ~SHIELD; BODY[_d] = NS[_d]; _d = diff(RA, NF) & ~FAR; BODY[_d] = NF[_d]   # 가장자리 반투명 차이도 지운 원화 쪽으로
n_, l_, st_, _ = cv2.connectedComponentsWithStats((BODY[..., 3] > 24).astype(np.uint8), 8)
_main = 1 + int(np.argmax(st_[1:, 4])); _junk = (l_ != _main) & (BODY[..., 3] > 0)
print('  BODY 떨어진 섬 지움', [(int(s[0]), int(s[1]), int(s[4])) for i, s in enumerate(st_) if i and i != _main])
BODY[_junk] = 0
FAR |= _junk & AL & (XX > 300) & (YY < 262)   # 가이드 빨강 밖에 남았던 도끼 쇠 판 외곽선 부스러기(339–341,180–184) → 도끼
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
# ③-가 먼 팔 칸 나누기(원화 픽셀)
far_seeds = {
    'pauldron': disk((372, 270), 7) | disk((388, 280), 3) | disk((356, 266), 3),
    'upF': disk((361, 306), 4) | disk((357, 333), 2),
    'foreF': disk((395, 325), 7) | disk((380, 342), 3) | disk((409, 306), 2),
    'fistF': disk((436, 289), 10),
    'axe': (FAR & (YY < 250) & ~disk((372, 270), 30)) | cap((448, 335), (454, 368), 3),
    'torsoF': cap((345, 262), (347, 312), 1),   # 원화 가슴 판 끝 ~ 어깨갑 사이 짙은 띠 = 상체 옆(nofar 가 둥근 어깨로 다시 그려 FAR 에 든 곳) → 몸 칸(BODY 픽셀)
}
far_allow = {'pauldron': (YY < 312) & (XX < 404) & (XX >= 343), 'upF': cap(F['SH'], F['EL'], 20) & (XX < 385) & ((XX >= 348) | (YY >= 318)), 'torsoF': (XX < 356) & (YY < 318), 'foreF': cap(F['EL'], F['WR'], 26) | ((YY > 335) & (XX < 412)),
             'fistF': disk(F['G'], 32) & (YY > 255), 'axe': (YY < 262) | cap((440, 316), (456, 380), 17)}
FL = ws(RA, FAR, far_seeds, ['torsoF', 'pauldron', 'upF', 'foreF', 'axe', 'fistF'], far_allow,
        front=(('fistF', ('axe', 'foreF')), ('foreF', ('pauldron', 'upF')), ('upF', ('pauldron',))))
# ③-나 몸 칸 나누기(BODY 픽셀)
body_seeds = {
    'head': disk((292, 198), 12) | disk((262, 212), 5) | disk((322, 212), 5) | disk((300, 245), 7) | disk((240, 230), 5) | disk((256, 243), 3) | disk((338, 248), 3) | disk((275, 250), 3),
    'collar': disk((314, 282), 5) | disk((288, 270), 4) | disk((266, 268), 3) | disk((334, 284), 2),
    'torso': disk((300, 315), 8) | disk((330, 305), 4) | disk((215, 262), 9) | disk((250, 320), 5) | disk((352, 283), 5) | disk((200, 285), 4) | disk((338, 330), 3) | disk((270, 300), 3),
    'hips': disk((300, 352), 5) | disk((250, 350), 4) | disk((338, 350), 3) | disk((290, 378), 5) | disk((268, 375), 3) | disk((300, 392), 2),
    'legN': disk((225, 365), 4) | disk((215, 385), 6) | disk((215, 415), 6) | disk((200, 440), 5) | disk((245, 437), 3),
    'legF': disk((322, 378), 4) | disk((348, 372), 3) | disk((360, 390), 6) | disk((372, 435), 5) | disk((335, 420), 4) | disk((320, 440), 3),
}
body_allow = {'head': (YY < 280) & (XX < 349), 'collar': (YY > 245) & (YY < 300) & (XX > 248) & (XX < 350), 'hips': (YY > 330) & (YY < 402) & ~((YY > 366) & ((XX < 252) | (XX > 322))),
              'legN': (YY > 350) & (XX < 268), 'legF': (YY > 355) & (XX > 300)}
BLB = ws(BODY, BL, body_seeds, ['torso', 'hips', 'legN', 'legF', 'head', 'collar'], body_allow,
         front=(('collar', ('head', 'torso')), ('head', ('torso',)), ('hips', ('legN', 'legF', 'torso'))))
NAMES = ['head', 'collar', 'torso', 'hips', 'legN', 'legF', 'shield', 'pauldron', 'upF', 'foreF', 'axe', 'fistF']
lab = np.zeros((512, 512), np.uint8); labB = np.zeros((512, 512), np.uint8)
for i, n in enumerate(NAMES):
    if n in BLB:
        labB[BLB[n]] = i + 1; lab[BLB[n] & ~SHIELD & ~FAR & AL] = i + 1
lab[SHIELD] = NAMES.index('shield') + 1
for n, m in FL.items(): lab[m] = NAMES.index('torso' if n == 'torsoF' else n) + 1
lab[FAR & (lab == 0)] = NAMES.index('foreF') + 1
np.save(os.path.join(W, 'labels.npy'), lab); np.save(os.path.join(W, 'labels_body.npy'), labB); json.dump(NAMES, open(os.path.join(W, 'label_names.json'), 'w'))
print('  원화 칸', {n: int((lab == i + 1).sum()) for i, n in enumerate(NAMES)}, '· 빈 불투명', int((AL & (lab == 0)).sum()))
print('  BODY 칸', {n: int((labB == i + 1).sum()) for i, n in enumerate(NAMES) if n in BLB}, '· 빈 불투명', int((BL & (labB == 0)).sum()))
pal = np.array([[0, 0, 0], [230, 80, 80], [255, 0, 200], [90, 160, 60], [150, 100, 50], [60, 120, 230], [40, 200, 220], [60, 60, 255], [0, 200, 120], [255, 170, 60],
                [255, 140, 0], [0, 200, 255], [255, 220, 0]], np.uint8)
def vis(img, lb):
    al = img[..., 3:4] / 255.0; base = (img[..., :3] * al + 255 * (1 - al)); out = (base * .45 + pal[lb] * .55).astype(np.uint8); out[lb == 0] = base[lb == 0].astype(np.uint8); return out
Image.fromarray(np.hstack([vis(RA, lab), np.full((512, 6, 3), 255, np.uint8), vis(BODY, labB)])).resize((2060, 1024), Image.NEAREST).save(os.path.join(HERE, 'review', 'seg17_labels.png'))
print('  그림 review/seg17_labels.png')
