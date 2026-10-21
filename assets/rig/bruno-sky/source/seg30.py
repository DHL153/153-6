"""30 스카이 브루노 — 원화를 부품별로 나누기(씨앗 + watershed, 경계 = 원화 외곽선) — seg20 구조
  20 과 다른 곳: 포니테일 다발 pony(남색 끈 뒤로 뻗은 머리 다발 + 땋은 가닥 — 10 러스트처럼 pony 뼈) · 남색 스카프 꼬리 scarf(streamers) · 도끼(자루 캡슐 + 머리 원)
                 가까운 은색 어깨갑 = pauldN(그 밑 남색 소매·팔꿈치 맨살 = 윗팔) · 먼 어깨갑·소매 = 상체(먼 윗팔은 팔꿈치 맨살만 보임)
  씨앗: 도끼 = 축 캡슐·머리 원, 주먹 = 원, 팔뚝 = 관절 사이 가는 캡슐, 나머지 = 손으로 찍은 원(3~5배 격자에서 읽음)
출력: work/labels.npy · work/label_names.json · review/seg_labels.png
실행: python3 -I seg30.py
"""
import json, os
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work'); os.makedirs(W, exist_ok=True); os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
RA = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA')); M = json.load(open(os.path.join(HERE, 'measure30.json')))
AL = RA[..., 3] > 24; YY, XX = np.mgrid[0:512, 0:512].astype(float)
NAMES = ['head', 'pony', 'scarf', 'torso', 'hips', 'legN', 'legF', 'pauldN', 'upperN', 'foreN', 'fistN', 'axeN', 'upperF', 'foreF', 'fistF', 'axeF']
ID = {n: i + 1 for i, n in enumerate(NAMES)}
V = lambda p: np.array(p, float)
def cap(p, q, r):
    p, q = V(p), V(q); d = q - p; L2 = max(d @ d, 1e-9); t = np.clip(((XX - p[0]) * d[0] + (YY - p[1]) * d[1]) / L2, 0, 1)
    return (XX - (p[0] + t * d[0])) ** 2 + (YY - (p[1] + t * d[1])) ** 2 <= r * r
def disk(c, r): return (XX - c[0]) ** 2 + (YY - c[1]) ** 2 <= r * r
# 도끼 머리 모양 = 옛 원화 먼 도끼 머리를 SIFT 로 옮긴 것(guides30 과 같음)
OLD = np.array(Image.open(os.path.join(HERE, 'refs', 'ref_design_char0030.png')).convert('RGBA'))
_g = lambda a: cv2.cvtColor(np.ascontiguousarray(a[..., :3]), cv2.COLOR_RGB2GRAY); sf = cv2.SIFT_create(4000)
HM = (OLD[..., 3] > 0) & (((YY <= 146) & (XX >= 352)) | ((YY > 146) & (YY <= 184) & (XX >= 466)))
_n, _cc, _st, _ = cv2.connectedComponentsWithStats(HM.astype(np.uint8), connectivity=8); HM = _cc == 1 + int(np.argmax(_st[1:, cv2.CC_STAT_AREA]))
def head_shape(reg):
    k1, d1 = sf.detectAndCompute(_g(OLD), (HM * 255).astype(np.uint8)); k2, d2 = sf.detectAndCompute(_g(RA), ((AL & reg) * 255).astype(np.uint8))
    mm = [a for a, b in cv2.BFMatcher().knnMatch(d1, d2, k=2) if a.distance < 0.75 * b.distance]
    T, _ = cv2.estimateAffinePartial2D(np.float32([k1[a.queryIdx].pt for a in mm]), np.float32([k2[a.trainIdx].pt for a in mm]), ransacReprojThreshold=4.0)
    return cv2.warpAffine(HM.astype(np.uint8) * 255, T, (512, 512)) > 60
AXH = {'near': head_shape((XX < 230) & (YY < 220)), 'far': head_shape((XX > 330) & (YY < 280))}
N, F = M['near'], M['far']
def axe(sd, big=False):
    s = M[sd]
    if big: return cap(s['head'], s['fist'], 14) | cap(s['fist'], s['pommel'], 15) | (cv2.dilate(AXH[sd].astype(np.uint8), np.ones((7, 7), np.uint8)) > 0)
    Fi, Hd = V(s['fist']), V(s['head']); u = (Hd - Fi) / np.linalg.norm(Hd - Fi)
    return cap(Fi + 24 * u, Hd - 30 * u, 3) | (cv2.erode(AXH[sd].astype(np.uint8), np.ones((7, 7), np.uint8)) > 0) | cap(Fi - 22 * u, Fi - 30 * u, 2)
seeds = {
  'axeN': axe('near'), 'axeF': axe('far'),
  'fistN': disk(N['fist'], 9), 'fistF': disk(F['fist'], 9),
  'foreN': cap(N['EL'], N['WR'], 5) & ~disk(N['EL'], 6), 'foreF': cap(F['EL'], F['WR'], 4) & ~disk(F['EL'], 5),
  'upperN': cap((168, 330), (190, 334), 4), 'upperF': disk((318, 341), 3),
  'pauldN': disk((198, 309), 5) | disk((212, 318), 3),
  'head': disk((288, 282), 12) | disk((300, 238), 10) | disk((262, 232), 8) | disk((225, 266), 4) | disk((280, 305), 6) | disk((272, 182), 6) | disk((318, 205), 6) | disk((246, 290), 4),
  'pony': disk((150, 205), 10) | disk((120, 255), 8) | disk((112, 300), 4) | disk((150, 352), 5) | disk((185, 178), 6) | disk((205, 160), 4) | disk((205, 262), 4) | disk((175, 240), 6),
  'scarf': disk((100, 322), 5) | disk((140, 318), 4) | disk((72, 332), 3),
  'torso': disk((240, 335), 4) | disk((275, 338), 5) | disk((255, 352), 3) | disk((305, 345), 4) | disk((230, 318), 3) | disk((262, 322), 3),
  'hips': disk((265, 371), 5) | disk((205, 372), 5) | disk((215, 396), 4) | disk((305, 390), 4) | disk((250, 385), 3) | disk((235, 375), 3),
  'legN': disk((210, 422), 6) | disk((185, 462), 7) | disk((200, 442), 5) | disk((230, 410), 3), 'legF': disk((308, 420), 6) | disk((318, 465), 7) | disk((285, 408), 4) | disk((312, 444), 5),
}
mk = np.zeros((512, 512), np.int32)
for n in ['head', 'pony', 'scarf', 'torso', 'hips', 'legN', 'legF', 'pauldN', 'upperN', 'upperF', 'foreN', 'foreF', 'axeN', 'axeF', 'fistN', 'fistF']:   # 뒤에 쓴 것이 이김
    mk[seeds[n] & AL] = ID[n]
mk[~cv2.dilate(AL.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)] = 99
img = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2BGR); al = RA[..., 3:4] / 255.0; img = (img * al + 255 * (1 - al)).astype(np.uint8)
lab = cv2.watershed(img, mk.copy()); lab[lab < 0] = 0; lab[lab == 99] = 0
ALLOW = {'axeN': axe('near', True), 'axeF': axe('far', True), 'fistN': disk(N['fist'], 24), 'fistF': disk(F['fist'], 24),
         'foreN': cap(N['EL'], N['WR'], 19), 'foreF': cap(F['EL'], F['WR'], 18), 'upperN': cap((160, 326), (200, 334), 16), 'upperF': cap(F['SH'], F['EL'], 12) & (XX > 308),
         'pauldN': (XX > 170) & (XX < 230) & (YY > 294) & (YY < 332), 'pony': (XX < 250) & (YY < 395), 'scarf': (XX < 210) & (YY > 280) & (YY < 352),
         'hips': (YY > 356) & (YY < 416), 'legN': (YY > 384) & (XX < 266), 'legF': (YY > 384) & (XX > 244), 'head': (YY < 330)}
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
# 스카프 꼬리: 포니테일·머리 라벨에 들어간 남색 천(파랑이 빨강보다 뚜렷이 큼) → scarf, 그 둘레 어두운 외곽선 2px 도
_rgb = RA[..., :3].astype(int); _blue = (_rgb[..., 2] - _rgb[..., 0] > 18) & (RA[..., 3] > 128) & (XX < 212) & (YY > 282) & (YY < 352)
_nc, _cc = cv2.connectedComponents(_blue.astype(np.uint8), 8); _bb = np.zeros_like(_blue)
for _i in range(1, _nc):
    if (_cc == _i).sum() >= 25: _bb |= _cc == _i
_sc = (_bb | ((cv2.dilate(_bb.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & (RA[..., :3].astype(int).mean(-1) < 60))) & ((lab == ID['pony']) | (lab == ID['head']) | (lab == ID['scarf']))
lab[_sc] = ID['scarf']; print('스카프 색으로 옮김', int(_sc.sum()))
# 허리띠에 달린 크림 앞자락 두 장(허벅지 위로 늘어짐) → 골반(달리면 허리띠와 같이) — 크림 + 둘레 외곽선 2px
_lum2 = RA[..., :3].astype(int).mean(-1); _sat2 = RA[..., :3].max(-1).astype(int) - RA[..., :3].min(-1)
_cr = (_lum2 > 170) & (_sat2 >= 22) & (_sat2 < 90) & (RA[..., 3] > 128) & (YY >= 376) & (YY <= 414) & (((XX >= 186) & (XX <= 242)) | ((XX >= 280) & (XX <= 330))) & ((lab == ID['legN']) | (lab == ID['legF']) | (lab == ID['hips']))
_nc, _cc = cv2.connectedComponents(_cr.astype(np.uint8), 8); _cb = np.zeros_like(_cr)
for _i in range(1, _nc):
    if (_cc == _i).sum() >= 30: _cb |= _cc == _i
_cbf = cv2.morphologyEx(_cb.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) > 0   # 앞자락 속 금 리벳·주름 선까지
_fl = (_cbf | ((cv2.dilate(_cb.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & (_lum2 < 70))) & ((lab == ID['legN']) | (lab == ID['legF']))
lab[_fl] = ID['hips']; print('크림 앞자락 다리 → 골반', int(_fl.sum()))
#   골반 칸 아래쪽(y ≥ 398)에서 앞자락·가랑이(x 240~280) 밖 = 무릎판 윗부분·허벅지 → 다리(달리면 골반에 회색 쐐기가 남지 않게)
_flD = cv2.dilate(_cb.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
_mv = (lab == ID['hips']) & (YY >= 398) & ~_flD & ((XX < 240) | (XX > 280))
_mv |= (lab == ID['hips']) & (YY >= 394) & (_lum2 >= 85) & (_sat2 < 22) & ((XX < 242) | (XX > 280))   # 은색 무릎판 윗부분(앞자락에 반쯤 덮임)
_mv |= (lab == ID['hips']) & (YY >= 394) & ~_cb & (cv2.dilate(((_lum2 >= 85) & (_sat2 < 22) & (YY >= 394)).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & (_lum2 < 70) & ((XX < 242) | (XX > 280))
_cr0 = (_lum2 > 170) & (_sat2 >= 22)   # 크림(앞자락)은 은색 뺀 뒤에도 골반
_mv &= ~(_cb & _cr0)
lab[_mv & (XX < 258)] = ID['legN']; lab[_mv & (XX >= 258)] = ID['legF']; print('골반 아래 끝 → 다리', int(_mv.sum()))
# 은색 어깨갑·금 테가 상체·윗팔 칸에 들어간 것 → 어깨갑(대기에 윗팔 이음 남색이 어깨갑 위로 비쳤음)
_rgb3 = RA[..., :3].astype(int)
_pdc = ((_lum2 >= 105) & (_sat2 < 30)) | ((_rgb3[..., 0] > 150) & (_rgb3[..., 2] < 110) & (_rgb3[..., 0] - _rgb3[..., 2] > 60))
_pbox = (XX >= 176) & (XX <= 226) & (YY >= 296) & (YY <= 332)
_pm = _pbox & _pdc & ((lab == ID['torso']) | (lab == ID['upperN'])) & (RA[..., 3] > 128)
_nc, _cc = cv2.connectedComponents((_pm | (lab == ID['pauldN'])).astype(np.uint8), 8); _pid = np.bincount(_cc[lab == ID['pauldN']]).argmax()
_pm &= _cc == _pid; _pm |= (cv2.dilate(_pm.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & _pbox & (_lum2 < 60) & ((lab == ID['torso']) | (lab == ID['upperN']))
lab[_pm] = ID['pauldN']; print('어깨갑 은색·금 테 → 어깨갑', int(_pm.sum()))
# 앞 부품(도끼·주먹·팔뚝·윗팔) 외곽선이 뒤 부품 라벨에 남은 것 → 앞 부품으로(49번 ③)
LUMI = RA[..., :3].astype(int).mean(-1)
for fr, bk in (('axeN', ('head', 'pony')), ('fistN', ('head', 'pony')), ('foreN', ('head', 'pony', 'scarf', 'torso')), ('upperN', ('torso', 'pony', 'scarf')), ('axeF', ('head', 'torso')), ('fistF', ('torso', 'head')), ('foreF', ('torso',))):
    near_fr = cv2.dilate((lab == ID[fr]).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    for bn in bk:
        mv = (lab == ID[bn]) & near_fr & (LUMI < 70) & ALLOW.get(fr, True); lab[mv] = ID[fr]
for bn in ('head', 'pony', 'scarf', 'torso', 'hips', 'pauldN'):
    n_, cc_, st_, _ = cv2.connectedComponentsWithStats((lab == ID[bn]).astype(np.uint8), 8)
    for i in range(1, n_):
        if st_[i, 4] >= 300: continue
        isl = cc_ == i; ring = (cv2.dilate(isl.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & ~isl; vals = lab[ring]; vals = vals[(vals > 0) & (vals != ID[bn])]
        if len(vals): lab[isl] = np.bincount(vals).argmax()
np.save(os.path.join(W, 'labels.npy'), lab.astype(np.uint8)); json.dump(NAMES, open(os.path.join(W, 'label_names.json'), 'w'))
pal = np.array([[0, 0, 0], [230, 80, 80], [255, 120, 40], [40, 60, 255], [90, 160, 60], [150, 100, 50], [60, 120, 230], [40, 200, 220], [255, 255, 255], [255, 170, 60], [120, 60, 160], [255, 220, 120], [255, 120, 200],
                [200, 200, 200], [100, 40, 120], [240, 240, 120], [220, 140, 255]], np.uint8)
vis = pal[lab]; base = np.array(Image.fromarray(img[..., ::-1]).convert('RGB')).astype(float)
out = (base * .4 + vis * .6).astype(np.uint8); out[lab == 0] = base[lab == 0].astype(np.uint8)
Image.fromarray(out).resize((1024, 1024), Image.NEAREST).save(os.path.join(HERE, 'review', 'seg_labels.png'))
print({n: int((lab == ID[n]).sum()) for n in NAMES})
