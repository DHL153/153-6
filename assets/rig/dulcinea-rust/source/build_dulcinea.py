"""2 러스트 둘시네 리그 조립 (2026-10-19 v1 대기·달리기). 구조 = 엔진 기본 길(자유 팔 armU→armL = 가까운 팔·주먹, 무기 팔 armF→foreF→fistF→weapon = 먼 팔·망치)
입력: ref512.png(손 고친 원화 = 게임 char_0002) · polys.json · cut/(조각 시트 1, cut_parts.py) · cut/upperN 등(시트 4 팔·허벅지)
출력: ../rig.json, ../rig.def.js, ../parts/*.png    실행: cd source && python3 -I build_dulcinea.py
원칙: 대기 = 원화(보이는 곳은 원화를 오림), 가려진 곳만 시트·inpaint. 손 조각 뒤집기 금지. 팔다리 길이 고정.
좌표: 원화 512px 로 적고 ×2 = 리그 단위."""
import json, math, os, shutil, hashlib, sys
import numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(HERE, 'cut'); W = os.path.join(HERE, 'work'); OUT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(HERE, 'tools'))
from place import sift_M, refine
os.makedirs(os.path.join(OUT, 'parts'), exist_ok=True); os.makedirs(W, exist_ok=True)
for f in os.listdir(os.path.join(OUT, 'parts')): os.remove(os.path.join(OUT, 'parts', f))
img = lambda p: np.array(Image.open(p).convert('RGBA'))
RA = img(os.path.join(HERE, 'ref512.png')); AL = RA[..., 3] > 8
POLY = {k: v for k, v in json.load(open(os.path.join(HERE, 'polys.json'))).items() if not k.startswith('_')}
def pmask(pts):
    m = Image.new('L', (512, 512), 0); ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255); return np.array(m) > 0
def dil(m, r): return cv2.dilate(m.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0
def ero(m, r): return cv2.erode(m.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0

# ---------------- 원화 관절 (512 px) ----------------
O = np.array([207.0, 485.0])                                     # 뿌리: 두 발 가운데 땅
HIP = np.array([232.0, 316.0]); NECK = np.array([244.0, 250.0])   # 골반(허리띠 버클) · 목(턱 밑 = 머리 회전 중심)
SH_N, EL_N, WR_N = np.array([170.0, 248.0]), np.array([146.0, 280.0]), np.array([133.0, 299.0])   # 가까운 팔(엔진 armU→armL): 어깨(어깨 보호대 안) · 팔꿈치 · 손목(붕대)
SH_F, EL_F, WR_F = np.array([270.0, 262.0]), np.array([255.0, 300.0]), np.array([288.0, 304.0])   # 먼 팔(엔진 armF→foreF→fistF): 어깨·팔꿈치 = 재킷 밑(안 보임)
HU = np.array([0.574, -0.819]); HU /= np.linalg.norm(HU)          # 망치 자루 방향(쥔 손 → 쇠 머리), 세로에서 오른쪽 35° — 자루 가운데 (357,250)·(280,360)
G = np.array([357.0 - 0.70 * (311 - 250), 311.0])                 # 쥔 점(먼 주먹 가운데, 자루 축 위)
PONY = np.array([232.0, 112.0])                                   # 포니테일 묶은 곳(머리 위)
LJ = {'near': dict(h=np.array([192.0, 334]), k=np.array([189.0, 369]), a=np.array([146.0, 448])),
      'far': dict(h=np.array([254.0, 334]), k=np.array([273.0, 386]), a=np.array([272.0, 452]))}
print('  G', np.round(G, 1).tolist())

# ---------------- 원화 칸 나누기 (주인 = 앞에 그리는 조각) ----------------
mk = {n: pmask(p) for n, p in POLY.items()}
# 망치: 쇠 머리 다각형 + 자루 띠(축에서 ±16px, 쥔 점 아래 70px 까지)
yy, xx = np.mgrid[0:512, 0:512].astype(np.float32); rel_x, rel_y = xx - G[0], yy - G[1]
t_ax = rel_x * HU[0] + rel_y * HU[1]; n_ax = rel_x * (-HU[1]) + rel_y * HU[0]
#   자루 가로 단면 색으로 잼(10-19 11:20): 주먹 위는 축 가운데, 주먹 밑은 축에서 7px 왼쪽 위로 그려져 있음, 끝(쇠 마개) = t −58
mk['hammer'] = (mk['hammerHead'] | ((np.abs(n_ax) <= 14) & (t_ax > -5) & (t_ax < 170)) | ((np.abs(n_ax + 7) <= 14) & (t_ax > -59) & (t_ax <= 0))) & ~mk['hairArea']
# 머리: 시트 머리(2칸)를 원화에 맞춘 알파 (SIFT + 미세조정) ∪ 흰 앞머리·귀는 그 안
_hd = img(os.path.join(C, 'head.png')); _M, _i, _g = sift_M(_hd, RA); _b = refine(_hd, RA, _M); MH = _b[1]
HEADS = cv2.warpAffine(_hd, MH, (512, 512), flags=cv2.INTER_LINEAR); mk['head'] = (HEADS[..., 3] > 100) & (yy < 252)
print('  head sheet→원화 err', round(float(_b[0]), 1), 'scale', round(float(np.hypot(MH[0, 0], MH[1, 0])), 3))
# 천자락·허리띠 (10-19 12:55 DHL '천자락에 살이 붙어 이상 — 옷 천만'): 다각형 안에서 색으로 나눔
#   천자락 = 올리브·크림 천 덩어리 + 둘러싼 외곽선 + 안쪽 구멍 / 살(허벅지) = 허벅지 조각 / 반바지 = 골반
#   허리띠 = 골반 다각형 중 허리띠 아래 선 위 — 천자락 앞에 그림(원화처럼 천자락 위 끝이 허리띠 밑, 천자락이 흔들려도 위 끝이 안 보임)
_h3 = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV).astype(int); _OP = RA[..., 3] > 200
SKINC = _OP & (_h3[..., 0] >= 5) & (_h3[..., 0] <= 16) & (_h3[..., 1] > 110) & (_h3[..., 2] > 140)
CLOTH = _OP & (((_h3[..., 0] >= 17) & (_h3[..., 0] <= 40) & (_h3[..., 2] >= 45)) | ((_h3[..., 1] < 70) & (_h3[..., 2] > 140) & (_h3[..., 0] <= 40)))   # 올리브 천 + 밝은 크림 찢긴 끝
LINE = _OP & (_h3[..., 2] < 45)
BELT_LINE = [[146, 323], [162, 323], [190, 325], [206, 328], [212, 331], [230, 332], [245, 332], [262, 333], [275, 336], [296, 336]]   # 허리띠 아래 외곽선(원화에서 잼)
ABOVE_BELT = yy <= np.interp(xx, [q[0] for q in BELT_LINE], [q[1] for q in BELT_LINE])
_flapPoly = mk['flapN'] | mk['flapC']; _old = {n: mk[n].copy() for n in ('flapN', 'flapC', 'hips')}
_CL = CLOTH & ~(ABOVE_BELT & ~dil(CLOTH & ~ABOVE_BELT, 1)); _taken = np.zeros((512, 512), bool)
for n in ('flapC', 'flapN'):   # 앞 천자락(가운데, 왼쪽 크림 찢긴 끝 포함) 먼저 — 두 천은 외곽선 틈으로 붙어 있어 1px 깎아 나눈 뒤 되돌림
    _pm = dil(mk[n], 3); _core = mk[n]; _c = _pm & _CL & ~_taken; _e = ero(_c, 1) if n == 'flapC' else _c
    _lb, _k = ndimage.label(_e); _sz = ndimage.sum(_e, _lb, range(1, _k + 1)); _hit = ndimage.sum(_core, _lb, range(1, _k + 1))
    _keep = np.isin(_lb, 1 + np.nonzero((_sz >= 30) & (_hit >= _sz * .5))[0])
    if n == 'flapC':
        for _ in range(2): _keep = _keep | (dil(_keep, 1) & _c)
    _keep = ndimage.binary_fill_holes(_keep | (LINE & dil(_keep, 1))); _keep = _keep | (LINE & dil(_keep, 2) & _pm)
    mk[n] = _keep & _OP & ~SKINC & ~_taken; _taken |= mk[n]
mk['belt'] = _old['hips'] & ABOVE_BELT & ~mk['flapN'] & ~mk['flapC']
mk['hips'] = _old['hips'] & ~ABOVE_BELT & ~SKINC
_skz = SKINC & (_old['flapN'] | _old['flapC'] | _old['hips']) & ~ABOVE_BELT   # 천자락·골반 다각형 안의 살 = 허벅지
_skz = _skz | ((_old['flapN'] | _old['flapC']) & ~ABOVE_BELT & ~mk['flapN'] & ~mk['flapC'] & ~mk['hips'])   # 천자락 다각형의 나머지(허벅지 외곽선 등)도 그 다리로 — 가장 가까운 칸(주먹·부츠)으로 가지 않게
mk['thighN'] = mk['thighN'] | (_skz & (xx < 220)); mk['thighF'] = mk['thighF'] | (_skz & (xx >= 220))
print('  flap px', {n: int(mk[n].sum()) for n in ('flapN', 'flapC')}, 'belt', int(mk['belt'].sum()), 'skin→thigh', int(_skz.sum()))
PRIO = ['armL', 'pauldron', 'armU', 'fistF', 'head', 'hammer', 'torso', 'foreF', 'belt', 'flapC', 'flapN', 'hips', 'thighN', 'bootN', 'thighF', 'bootF', 'pony']
mk['pony'] = mk['hairArea']
LAB = np.full((512, 512), -1, np.int16)
for i, n in enumerate(PRIO):
    LAB[(LAB < 0) & mk[n] & AL] = i
_un = AL & (LAB < 0); print('  unlabeled px', int(_un.sum()))
if _un.any():   # 주인 없는 불투명 픽셀 → 가장 가까운 칸
    d, (iy, ix) = ndimage.distance_transform_edt(LAB < 0, return_indices=True); LAB[_un] = LAB[iy[_un], ix[_un]]
#   턱 아래(가까운 쪽 멜빵 위 끝·올리브 깃·목 그늘)는 머리 시트 알파 안이라 머리 칸이 됐음 → 몸통으로 (10-19 16:20)
#   머리가 몸통에 대해 돌면(내려찍기 예비에서 몸을 젖힐 때) 멜빵 위 끝이 머리와 함께 떠서 목 옆에 흰 틈 — 턱 외곽선은 머리에 남김(선 2px 아래부터)
UNDER_JAW = pmask([[183, 221], [195, 220], [204, 220], [212, 223], [219, 229], [225, 234], [231, 238], [240, 242], [250, 246], [262, 248], [272, 249], [272, 262], [183, 262]])
_uj = (LAB == PRIO.index('head')) & UNDER_JAW; LAB[_uj] = PRIO.index('torso'); print('  under-jaw head→torso px', int(_uj.sum()))
np.save(os.path.join(W, 'labels.npy'), LAB)
_pal = np.array([[230, 30, 30], [230, 0, 200], [255, 140, 0], [255, 220, 0], [90, 90, 100], [120, 60, 20], [0, 170, 0], [255, 255, 120], [0, 210, 210], [130, 0, 255],
                 [0, 0, 230], [200, 0, 100], [150, 90, 0], [0, 130, 255], [90, 160, 0], [60, 30, 10], [255, 90, 160]], np.uint8)
_v = np.full((512, 512, 3), 255, np.uint8); _v[AL] = (_pal[LAB[AL]] * .55 + RA[..., :3][AL] * .45).astype(np.uint8)
Image.fromarray(_v).resize((1024, 1024), Image.NEAREST).save(os.path.join(W, '_labels.png'))
print('  labels ->', os.path.join(W, '_labels.png'))
if '--labels' in sys.argv: sys.exit(0)

# ---------------- 조각 오리기: 주인 칸 + 앞 조각 밑 3px 겹침(이음매 없게) + 가려진 곳 메우기 ----------------
DRAW_ART = ['pony', 'armF', 'thighF', 'bootF', 'thighN', 'bootN', 'hips', 'flapN', 'flapC', 'belt', 'foreF', 'torso', 'hammer', 'head', 'fistF', 'armU', 'pauldron', 'armL']
own = {n: (LAB == PRIO.index(n)) & AL for n in PRIO}
# (10-20 06:00 망치 = 머리 뒤, DHL 05:54) 흰 앞머리 오른쪽 외곽선이 망치 칸에 들어가 있음(원화에선 앞머리가 망치 위) → 머리로:
#   망치 칸 중 머리에 붙은 떨어진 조각(초승달) + 머리 4px 안 어두운 선(앞머리 ↔ 쇠 머리 경계선)
_hc_n, _hc_l, _hc_s, _ = cv2.connectedComponentsWithStats((own['hammer'] & (RA[..., 3] > 10)).astype(np.uint8), 8)
_hc_big = 1 + int(np.argmax(_hc_s[1:, cv2.CC_STAT_AREA])); _near_head = dil(own['head'], 2)
_to_head = np.zeros((512, 512), bool)
for _i in range(1, _hc_n):
    if _i != _hc_big and (_near_head & (_hc_l == _i)).any(): _to_head |= _hc_l == _i
_to_head |= own['hammer'] & dil(own['head'], 4) & (RA[..., :3].max(2) < 70)
own['head'] = own['head'] | _to_head; own['hammer'] = own['hammer'] & ~_to_head
print('  앞머리 외곽선 망치 → 머리 px', int(_to_head.sum()))
COVER = np.zeros((512, 512), np.uint8)
def above(n):   # n 보다 앞(뒤에 그림)에 그리는 조각들의 칸
    i = DRAW_ART.index(n); return np.logical_or.reduce([own[m] for m in DRAW_ART[i + 1:] if m in own] + [np.zeros((512, 512), bool)])
def inpaint_into(a, region, src_ok, r=5):
    """region(가려진 곳)을 src_ok 픽셀 색으로 메움 — 둘레 다른 색은 끌어오지 않게 src 밖은 가장 가까운 src 색으로 먼저 칠함"""
    rgb = np.ascontiguousarray(a[..., :3].copy()); d, (iy, ix) = ndimage.distance_transform_edt(~src_ok, return_indices=True)
    rgb[~src_ok] = rgb[iy[~src_ok], ix[~src_ok]]
    out = cv2.inpaint(rgb, region.astype(np.uint8) * 255, r, cv2.INPAINT_TELEA); a = a.copy(); a[..., :3][region] = out[region]; a[..., 3][region] = 255; return a
def outline_cut(a, cutmask, w=2.4):
    """잘린 실루엣 가장자리에 원화 같은 외곽선(가려졌던 곳이 드러날 때 경계가 그림처럼)"""
    A = a[..., 3] > 128; d = ndimage.distance_transform_edt(A); e = A & dil(cutmask, 1) & (d <= w + .2)
    k = np.clip(w + .4 - d, 0, 1)[e][:, None]; a = a.copy(); a[..., :3][e] = (a[..., :3][e] * (1 - k) + np.array([34, 26, 22]) * k).astype(np.uint8); return a
def save_crop(a, name):
    ys, xs = np.nonzero(a[..., 3] > 0); x0, y0 = xs.min() - 2, ys.min() - 2
    Image.fromarray(a[y0:ys.max() + 3, x0:xs.max() + 3]).save(os.path.join(W, name + '.png')); return np.array([x0, y0], float)
ART = {}
for n in DRAW_ART:
    if n == 'armF': continue
    _ab = dil(own[n], 3) & above(n) & AL
    if n in ('torso', 'hips', 'flapN', 'flapC', 'belt', 'thighN', 'thighF', 'bootF'): _ab &= ~(own['armL'] | own['armU'] | own['foreF'] | own['fistF'] | own['hammer'])   # 움직이는 팔·주먹·망치 밑 겹침은 안 가져옴(외곽선 조각이 떠 보임) — 그 밑은 메우기로   # 흔드는 팔 밑 겹침에 팔 외곽선(검은 줄)은 안 가져옴 — 팔이 움직이면 줄이 떠 보였음
    if n == 'hammer': _ab &= ~own['head']   # (10-20 06:00 망치 = 머리 뒤) 머리 밑 겹침은 머리카락이라 안 가져옴 — 머리 밑 쇠 머리 모서리는 _fix_hammer 가 메움
    m = own[n] | _ab
    a = RA.copy(); a[..., 3] = np.where(m, RA[..., 3], 0); ART[n] = a; COVER[:] = np.maximum(COVER, np.where(own[n], RA[..., 3], 0))
# 포니테일: 머리 밑(머리카락 띠 12px) 메움 — 머리가 숨 쉬고 끄덕여도 틈 없게
_pm = dil(own['head'], 12) & ~own['head'] & mk['hairArea'] | (dil(own['pony'], 2) & own['head'] & ~ero(own['head'], 12))
_reg = (dil(own['pony'], 14) & (own['head'] | own['torso'] | own['pauldron'])) & ~own['pony'] & mk['hairArea']
ART['pony'] = inpaint_into(ART['pony'], _reg & ~(ART['pony'][..., 3] > 200), own['pony'] & (RA[..., 3] > 200))
_reg = dil(own['pony'], 24) & ero((own['pauldron'] | own['armU']) & (RA[..., 3] > 250), 2) & (yy < 264) & ~own['pony'] & ~(ART['pony'][..., 3] > 200)   # 가까운 어깨갑 위쪽 밑 머리카락(내려찍기에서 어깨가 앞으로 가면 드러나는 흰 틈, 10-19) — 재킷 위 끝(y 264) 위만
ART['pony'] = outline_cut(inpaint_into(ART['pony'], _reg, own['pony'] & (RA[..., 3] > 200) & ~dil(~AL, 2)), _reg)
# 몸통: 팔·어깨 보호대·머리(턱) 밑 메움 — 달릴 때 팔이 흔들리면 드러남
_reg = (((mk['torso'] | mk['fillTorso']) & (own['armU'] | own['pauldron'] | own['armL'] | own['foreF'] | own['fistF'] | (own['head'] & dil(own['torso'], 8)))) | (ero(own['pauldron'] & (RA[..., 3] > 250), 2) & dil(mk['torso'], 12) & ~own['head']) | (own['head'] & dil(own['torso'] | own['pauldron'], 10) & (xx < 215) & (yy > 195)) | (own['pauldron'] & (RA[..., 3] > 250) & dil(own['torso'], 14) & (yy < 245))) & ~(ART['torso'][..., 3] > 200)   # + 어깨갑 밑 몸통 둘레 12px(팔을 흔들어 어깨갑이 돌면 목 옆 흰 틈, 10-19 15:55)   # 먼 팔뚝·주먹 밑도(내려찍기에서 먼 팔이 움직임)   # + 가까운 쪽 뺨 밑 10px(머리가 몸에 대해 돌면 멜빵 위 끝 위가 드러남, 10-19 16:25) + 어깨갑 위 모서리 밑(테두리까지, 어깨갑이 대기 때보다 덜 돌면 드러남)
ART['torso'] = outline_cut(inpaint_into(ART['torso'], _reg, own['torso'] & (RA[..., 3] > 200) & ~dil(~AL, 2)), _reg)
_aa = dil(_reg, 2) & ~ero(ART['torso'][..., 3] > 128, 1); _sm = cv2.GaussianBlur(ART['torso'][..., 3].astype(np.float32), (0, 0), .9)   # 메운 곳 바깥 경계 계단(2배 확대에서 톱니) → 알파만 살짝 부드럽게
ART['torso'][..., 3][_aa] = np.minimum(ART['torso'][..., 3][_aa], _sm[_aa].astype(np.uint8))
# 허리띠: 주먹·자루 밑 메움 / 반바지: 천자락 밑(천자락 3px 겹침까지 반바지 색으로 — 천자락이 흔들려도 천 색 테두리가 안 남게)·주먹·자루 밑
_hv = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV); _shorts = own['hips'] & (RA[..., 3] > 200) & (_hv[..., 2] > 45) & (_hv[..., 2] < 95) & (_hv[..., 1] < 110) & ~dil(~AL, 2)
_beltSrc = own['belt'] & (RA[..., 3] > 200) & ~dil(~AL, 2)
# 먼 팔 밑 몸 옆(내려찍기에서 먼 팔이 올라가면 드러남, 10-19 14:20): 허리띠는 띠 모양 그대로 왼쪽 띠를 옮겨 이어 그리고 끝을 둥글게,
#   그 위(띠 위 ~ 재킷 아래)는 배 살색. 다각형 = 재킷 오른쪽 아래 끝 ~ 허리띠 오른쪽 끝
FAR_SIDE = pmask([[262, 288], [276, 289], [281, 300], [285, 312], [288, 322], [289, 337], [262, 338]])   # 몸 옆 선: 재킷 아래 끝 → 허리띠 끝으로 둥글게
BELT_TOP = [[150, 304], [200, 306], [240, 312], [270, 317], [296, 320]]
_btop = np.interp(xx, [q[0] for q in BELT_TOP], [q[1] for q in BELT_TOP]); _bbot = np.interp(xx, [q[0] for q in BELT_LINE], [q[1] for q in BELT_LINE])
_band = (yy >= _btop) & (yy <= _bbot)
_rb = (mk['belt'] | (_old['hips'] & ABOVE_BELT)) & (own['armL'] | (own['hammer'] & (xx <= 286))) & ~FAR_SIDE & ~(ART['belt'][..., 3] > 200)   # 망치 자루 밑은 허리띠 끝(x 286)까지만
ART['belt'] = inpaint_into(ART['belt'], _rb, _beltSrc)
_fb = FAR_SIDE & _band & ~(ART['belt'][..., 3] > 200)
_sh = cv2.warpAffine(ART['belt'], np.float32([[1, 0, 24], [0, 1, 2.9]]), (512, 512), flags=cv2.INTER_LINEAR)   # 왼쪽 24px 띠를 오른쪽으로(띠 기울기 0.12)
ART['belt'][_fb] = _sh[_fb]; ART['belt'][..., 3][_fb] = np.maximum(ART['belt'][..., 3][_fb], 0)
_fbm = (ART['belt'][..., 3] > 128) & (FAR_SIDE & _band) & (xx <= 286); ART['belt'][..., 3][FAR_SIDE & _band & ~_fbm] = 0
ART['belt'] = outline_cut(ART['belt'], FAR_SIDE & _band & (xx >= 285))
# 허리띠 위 배 띠(상체 밑): 상체가 숙여지면(내려찍기 lean 0.3) 상체 아래 끝과 허리띠 사이가 벌어짐 → 허리띠 그림에 상체 아래 끝 16px 를 깔아 둠(상체 뒤라 대기에선 안 보임)
_bt = np.interp(xx, [q[0] for q in BELT_TOP], [q[1] for q in BELT_TOP]); _ub = (yy >= _bt - 16) & (yy <= _bt + 2) & (ART['torso'][..., 3] > 200) & ~(ART['belt'][..., 3] > 200) & (cv2.cvtColor(np.ascontiguousarray(ART['torso'][..., :3]), cv2.COLOR_RGB2HSV)[..., 2] > 70) & (xx >= 150) & (xx <= 300)   # 외곽선(어두운 색)은 빼고 허리띠 폭 안만
ART['belt'][_ub] = ART['torso'][_ub]; ART['belt'][..., 3][_ub] = 255
_ft = FAR_SIDE & (yy < _btop + 8) & (yy > 286) & ~(ART['torso'][..., 3] > 200)   # 허리띠 밑으로 8px 겹침(상체가 기울어도 틈 없음)
_skin0 = (lambda h: (h[..., 0] >= 5) & (h[..., 0] <= 25) & (h[..., 1] > 80) & (h[..., 2] > 140))(cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV)) & (RA[..., 3] > 200) & (yy > 292) & (yy < 312) & (xx > 200) & (xx < 262)
# → 따로 조각 sideF(공격 그리는 순서에만 — 대기에선 먼 팔뚝이 이 자리 위에 있어 원화 그대로)
_SD = ART['torso'].copy(); _SD[..., 3] = 0
_jk = cv2.warpAffine(ART['torso'], np.float32([[1, 0, 0], [0, 1, 20]]), (512, 512), flags=cv2.INTER_NEAREST)   # 재킷 오른쪽 자락을 20px 아래로 이어 그림(허리띠 위까지 늘어진 자락)
_ftj = _ft & (_jk[..., 3] > 128); _SD[_ftj] = _jk[_ftj]
_ft2 = _ft & ~_ftj
if _ft2.any(): _SD = inpaint_into(_SD, _ft2, _skin0)
_SD[..., 3][~_ft] = 0; _SD[..., 3][_ft & ~(_SD[..., 3] > 128)] = 0
_SD = outline_cut(_SD, _ft & ~ero(FAR_SIDE, 1)); ART['sideF'] = _SD
print('  far side fill belt', int(_fb.sum()), 'belly', int(_ft.sum()))
_hz = _old['hips'] & ~ABOVE_BELT
_rs = (_hz & ((own['armL'] | own['hammer'] | ((own['foreF'] | own['fistF']) & (xx < 284))) & ~(ART['hips'][..., 3] > 200)))   # (10-20 18:32 망치 = 골반 뒤) 자루 밑은 반바지 다각형 끝(밑단 288@336)까지 — 전엔 x 284 에서 세로로 잘림   # 먼 주먹 밑은 반바지 오른쪽 끝(x 284)까지만 | (_hz & dil(own['flapN'] | own['flapC'], 1))
ART['hips'] = inpaint_into(ART['hips'], _rs, _shorts)
ART['hips'] = outline_cut(ART['hips'], _rs & dil(~_hz, 1))
_aa = dil(_rs & own['hammer'], 2) & ~ero(ART['hips'][..., 3] > 128, 1); _sm = cv2.GaussianBlur(ART['hips'][..., 3].astype(np.float32), (0, 0), .8)   # (10-20 18:32) 자루 앞 밑단 계단 → 알파만 부드럽게
ART['hips'][..., 3][_aa] = np.minimum(ART['hips'][..., 3][_aa], _sm[_aa].astype(np.uint8))
# 천자락 위 끝: 허리띠 밑으로 6px 이어 그림(허리띠가 앞이라 대기에선 안 보임, 흔들려도 위 끝 틈 없음)
for n in ('flapN', 'flapC'):
    _up = dil(own[n], 6) & (own['belt'] | (_old['hips'] & ABOVE_BELT)) & (ART['belt'][..., 3] > 200) & ~(ART[n][..., 3] > 200)   # 허리띠가 덮는 곳만(팔이 움직여도 안 보임)
    ART[n] = inpaint_into(ART[n], _up, own[n] & CLOTH)
print('  belt fill px', int(_rb.sum()), 'shorts fill px', int(_rs.sum()), 'shorts src', int(_shorts.sum()))
# 망치 자루: 주먹 밑(쥔 곳) — 주먹 아래 감은 자루를 축 따라 위로 옮겨 채움
_hreg = (np.abs(n_ax + 7 * (t_ax < 0)) <= 13) & (t_ax > -30) & (t_ax < 26) & own['fistF']
_src = ART['hammer'].copy(); _sh = 46
_M = np.float32([[1, 0, HU[0] * _sh], [0, 1, HU[1] * _sh]])   # 아래(−t) 픽셀을 +t 쪽으로
_mv = cv2.warpAffine(RA, _M, (512, 512), flags=cv2.INTER_LINEAR)
ART['hammer'][..., :3][_hreg] = _mv[..., :3][_hreg]; ART['hammer'][..., 3][_hreg] = np.maximum(ART['hammer'][..., 3][_hreg], _mv[..., 3][_hreg])
# 먼 팔뚝: 재킷 밑으로 팔꿈치까지 이어 그림(살색) — 몸통이 위라 안 보임, 팔이 돌아도 틈 없게
_ext = np.zeros((512, 512), np.uint8); cv2.line(_ext, tuple(int(v) for v in EL_F - (WR_F - EL_F) / np.linalg.norm(WR_F - EL_F) * 6), (270, 302), 1, 20); _ext = _ext.astype(bool) & ~(ART['foreF'][..., 3] > 200)
ART['foreF'] = inpaint_into(ART['foreF'], _ext, own['foreF'] & (RA[..., 3] > 200) & (xx < 276))
# 허벅지: 반바지·천자락 밑으로 엉덩이까지(살색) — 서 있는 다리 그림이 움직여도 틈 없게
for sd, n in [('near', 'thighN'), ('far', 'thighF')]:
    _e = np.zeros((512, 512), np.uint8); h, k = LJ[sd]['h'], LJ[sd]['k']; cv2.line(_e, tuple(int(v) for v in h), tuple(int(v) for v in (h + k) / 2), 1, 30)
    _e = _e.astype(bool) & ~(ART[n][..., 3] > 200) & (own['hips'] | own['flapN'] | own['flapC']) & AL
    ART[n] = inpaint_into(ART[n], _e, own[n] & (RA[..., 3] > 200) & ~dil(~AL, 2))
THIGH_TOP_R = 338   # 먼 허벅지 다각형 오른쪽 위 끝 높이(x 270~290 에서 y 336~338)
# 먼 허벅지·부츠: 망치 자루·먼 주먹 밑 메움(자루가 움직이면 드러남, 10-19 공격)
for n in ('thighF', 'bootF'):
    _hz2 = dil(own[n], 6) & (own['hammer'] | own['fistF']) & mk[n] & ~(ART[n][..., 3] > 200)
    if n == 'thighF':   # (10-20 18:32 망치 = 다리 뒤) 대기에서 먼 허벅지가 자루 끝(쇠 마개) 앞 — 6px 띠가 아니라 허벅지 모양대로
        #   위 = 반바지 밑단(허벅지 다각형 위 끝, 반바지가 덮음) · 오른쪽 = 허벅지 바깥 선(엉덩이 옆 296 → 부츠 위 291, 원화 허벅지가 마개 밑에서 보이는 끝 294@356 에 맞춤)
        #   허벅지 칸에 붙은 자루 왼쪽 외곽선(어두운 px) 도 살로 — 바깥 선 밖은 허벅지에서 지움(자루 칸으로)
        _hzb = _old['hips'] & ~ABOVE_BELT; _hem = np.full(512, float(THIGH_TOP_R - 1)); _cols = _hzb.any(0)
        _hem[_cols] = 511 - _hzb[::-1].argmax(0)[_cols] - 3   # 반바지 밑단(다각형 아래 끝) 3px 위부터 — 허벅지 위 끝 외곽선이 반바지 밑에 숨게
        _hem[289:] = THIGH_TOP_R - 1                          # 반바지 모서리(288,336) 오른쪽 = 엉덩이 옆 허벅지 위 끝
        _cx = np.interp(yy, [330, 337, 342, 348, 354, 358, 362, 368], [288, 288, 293, 295, 294, 293, 291, 291])   # 허벅지 바깥 선: 반바지 모서리 → 조금 불룩 → 부츠 위(원화 294@356)
        _dark = own[n] & dil(own['hammer'], 5) & ~SKINC & (xx > 262)   # 살 아닌 px(자루 왼쪽 외곽선·점) — 자루가 앞일 땐 자루 외곽선으로 보였음
        _out = _dark & (xx > _cx); ART[n][..., 3][_out] = 0
        _hz2 = (own['hammer'] | (_dark & ~_out)) & (yy >= _hem[xx.astype(int)]) & (xx <= _cx) & (yy <= 368)   # 아래는 부츠 위 끝 밑까지(부츠가 덮음 — 틈·외곽선 안 보이게)
        ART[n][..., 3][_hz2] = 0
        _src = own[n] & SKINC & ~dil(LINE, 1) & ~dil(~AL, 2)
        ART[n] = outline_cut(inpaint_into(ART[n], _hz2, _src), _hz2)
        _aa = dil(_hz2, 2) & ~ero(ART[n][..., 3] > 128, 1); _sm = cv2.GaussianBlur(ART[n][..., 3].astype(np.float32), (0, 0), .8)   # 바깥 선 계단 → 알파만 살짝 부드럽게
        ART[n][..., 3][_aa] = np.minimum(ART[n][..., 3][_aa], _sm[_aa].astype(np.uint8))
        print('  먼 허벅지 = 자루 끝 앞 메움 px', int(_hz2.sum()), '· 바깥 자루 외곽선 지움', int(_out.sum()))
        continue
    if n == 'bootF':   # (10-20 18:32) 자루 마개 밑에 붙은 부츠 위 끝 뾰족한 외곽선(y ≤ 362) — 허벅지가 마개 앞이 되면 가시처럼 보임 → 지우고 메움에서도 뺌(3px 겹침도 위 오리기에서 뺌 — bootF 를 움직이는 칸 겹침 제외 목록에)
        _spk = (yy <= 362) & (xx >= 280) & (xx <= 294); ART[n][..., 3][_spk & own[n]] = 0; _hz2 = _hz2 & ~_spk
    if _hz2.any(): ART[n] = outline_cut(inpaint_into(ART[n], _hz2, own[n] & (RA[..., 3] > 200) & ~dil(~AL, 2)), _hz2)
# 가까운 팔: 팔꿈치 둥근 끝 — 윗팔 아래·팔뚝 위에 반원(살색 + 바깥 외곽선). 팔꿈치가 굽어도 잘린 면이 안 보임
_ax = (WR_N - SH_N) / np.linalg.norm(WR_N - SH_N); _R = 11.5
_disc = np.hypot(xx - EL_N[0], yy - EL_N[1]) <= _R
_skin = (lambda h: (h[..., 0] >= 5) & (h[..., 0] <= 25) & (h[..., 1] > 80) & (h[..., 2] > 140))(cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV)) & (RA[..., 3] > 200)
SKIN = np.median(RA[..., :3][_skin & (own['armU'] | own['armL'])], 0).astype(np.uint8)
for n, sgn, R_, ringOn in [('armU', 1, _R, True), ('armL', -1, _R - 3, False)]:   # 윗팔 = 외곽선 있는 둥근 끝(팔뚝 밑에 숨음) · 팔뚝 = 외곽선 안쪽 작은 반원(대기 때 윗팔 외곽선을 안 덮게)
    t_ = (xx - EL_N[0]) * _ax[0] + (yy - EL_N[1]) * _ax[1]; rr = np.hypot(xx - EL_N[0], yy - EL_N[1]); half = (rr <= R_) & (sgn * t_ >= -2)
    a = ART[n]; add = half & ~(a[..., 3] > 200); a[..., :3][add] = SKIN; a[..., 3][add] = 255
    if ringOn: ring = half & (rr > R_ - 2.2) & (sgn * t_ > 1); a[..., :3][ring] = (34, 26, 22); a[..., 3][ring] = 255
    ART[n] = a
#   (10-19 15:55 어깨갑 둘레 빈칸 메우기는 뺌 — 목 옆 흰 틈의 진짜 원인은 턱 아래가 머리 칸이던 것, 위 UNDER_JAW. 메운 머리카락이 달리기에서 검은 톱니로 보임)
O_ ={n: save_crop(a, n + 'Art') for n, a in ART.items()}
_gap = (RA[..., 3] > 200) & (COVER < 200); print('  gaps (원화 불투명인데 주인 없음):', int(_gap.sum()), 'px')
for n in ['bootN', 'bootF']: print('  stand sole', n, 'bottom y', int(O_[n][1] + np.nonzero((np.array(Image.open(os.path.join(W, n + 'Art.png')))[..., 3] > 128).any(1))[0].max()))

# ---------------- 서 있는 다리: 원화 부츠를 발목 선에서 정강이(위)·발(아래)로 나눔 ----------------
def split_boot(n, sd):
    a = np.array(Image.open(os.path.join(W, n + 'Art.png'))); o = O_[n]; k, an = LJ[sd]['k'], LJ[sd]['a']; d = (an - k) / np.linalg.norm(an - k)
    Y, X = np.mgrid[0:a.shape[0], 0:a.shape[1]]; t = (X + o[0] - an[0]) * d[0] + (Y + o[1] - an[1]) * d[1]
    sh = a.copy(); sh[..., 3] = np.where(t < 4, a[..., 3], 0); ft = a.copy(); ft[..., 3] = np.where(t > -4, a[..., 3], 0)
    Image.fromarray(sh).save(os.path.join(W, n + 'Shin.png')); Image.fromarray(ft).save(os.path.join(W, n + 'Foot.png'))
for n, sd in [('bootN', 'near'), ('bootF', 'far')]: split_boot(n, sd)

# ---------------- 부품 표 ----------------
L2 = lambda p: [round(float(p[0] - O[0]) * 2, 1), round(float(p[1] - O[1]) * 2, 1)]
pc = lambda p, o: [round(float(p[0] - o[0]), 1), round(float(p[1] - o[1]), 1)]
def_parts = {}
def part(name, src, pivot, scale=2.0, **kw):
    shutil.copy(src, os.path.join(OUT, 'parts', name + '.png')); def_parts[name] = dict(src=f'parts/{name}.png', pivot=pivot, scale=scale, **kw)
A = lambda n: os.path.join(W, n + 'Art.png')
part('pony', A('pony'), pc(PONY, O_['pony']))
part('head', A('head'), pc(NECK, O_['head']))
part('torso', A('torso'), pc(HIP, O_['torso'])); part('hips', A('hips'), pc(HIP, O_['hips'])); part('belt', A('belt'), pc(HIP, O_['belt'])); part('sideF', A('sideF'), pc(HIP, O_['sideF']))
part('flapC', A('flapC'), pc(np.array([210.0, 326]), O_['flapC'])); part('flapN', A('flapN'), pc(np.array([170.0, 314]), O_['flapN']))
part('pauldron', A('pauldron'), pc(SH_N, O_['pauldron']))
part('armU', A('armU'), pc(SH_N, O_['armU']), elbow=pc(EL_N, O_['armU']))
part('armL', A('armL'), pc(EL_N, O_['armL']), fist=pc(np.array([128.0, 327]), O_['armL']))
part('foreF', A('foreF'), pc(EL_F, O_['foreF']), elbow=pc(EL_F, O_['foreF']))
part('fistF', A('fistF'), pc(WR_F, O_['fistF']))
_hm = np.array(Image.open(A('hammer')))[..., 3] > 128; _hy = np.nonzero(_hm.any(1))[0]
TIP = G + HU * 170; BUTT = G - HU * 58
# 망치: 자루가 그림 세로(쇠 머리 위)가 되게 원화 오림을 돌려 2배 해상도로 저장(4배로 키워 돌린 뒤 줄임) — 엔진 두 손 쥐기(_swordRigid)는 무기 그림 위쪽 = 자루 방향을 씀.
#   대기는 뼈 각도(HTH)로 원래 자리 그대로. (10-19 14:00 내려찍기)
HTH = float(math.atan2(HU[0], -HU[1]))                                   # 그림 위쪽 → 자루 방향 (시계 방향 +)
_ha = Image.open(A('hammer')); _o = O_['hammer']; _S = 4
_big = _ha.resize((_ha.width * _S, _ha.height * _S), Image.LANCZOS); _pv = (G - _o) * _S
_pad = int(max(_big.size) * .8); _can = Image.new('RGBA', (_big.width + 2 * _pad, _big.height + 2 * _pad), (0, 0, 0, 0)); _can.paste(_big, (_pad, _pad)); _pv = _pv + _pad
_rot = _can.rotate(math.degrees(HTH), resample=Image.BICUBIC, center=tuple(_pv))   # PIL: + = 화면에서 반시계 → 기울어진 자루를 세움
_bb = _rot.getbbox(); _rot = _rot.crop(_bb); _pv = _pv - np.array(_bb[:2]); _rot = _rot.resize((_rot.width // 2, _rot.height // 2), Image.LANCZOS); _pv = _pv / 2
_rot.save(os.path.join(W, 'hammerUp.png'))
# (10-19 21:30 v6 망치 맨 앞 → 공격용 weaponA) 쇠 머리 왼쪽 아래 모서리: 원화에선 흰 앞머리가 덮어 모서리가 파이고 앞머리 외곽선 조각이 남아 있음 → 대기엔 머리가 덮어 안 보이지만
#   망치를 맨 앞에 그리면 홈·검은 초승달이 보임. 가장 큰 덩어리만 남기고(초승달·점 지움), 모서리는 바로 위 판(같은 x, 50 위)을 내려 채우고 아래 외곽선을 이음
def _fix_hammer(path):
    a = np.array(Image.open(path).convert('RGBA')); n_, lb_, st_, _ = cv2.connectedComponentsWithStats((a[..., 3] > 10).astype(np.uint8), 8)
    big = 1 + int(np.argmax(st_[1:, cv2.CC_STAT_AREA])); a[..., 3] = np.where(lb_ == big, a[..., 3], 0)
    m = Image.new('L', (a.shape[1], a.shape[0]), 0); ImageDraw.Draw(m).polygon([(9, 152), (9, 204), (60, 204), (60, 198), (48, 183), (30, 163), (18, 152)], fill=255)
    m = cv2.GaussianBlur((np.array(m) > 0).astype(np.float32), (7, 7), 0)          # 3px 섞임 — 위에서 내린 판과 원래 판 사이 이음이 안 보이게
    src = np.roll(a, 50, axis=0).astype(np.float32); out = a.astype(np.float32)
    k = m[..., None]; out[..., :3] = out[..., :3] * (1 - k) + src[..., :3] * k; out[..., 3] = np.maximum(out[..., 3], (m > .5) * 255)
    a = out.clip(0, 255).astype(np.uint8)
    a[150:210, 10:17, :3] = a[120, 10:17, :3]; a[150:210, 10:17, 3] = a[120, 10:17, 3]   # 왼쪽 외곽선 그대로 내림
    a[204:210, 10:62, :3] = (5, 3, 2); a[204:210, 10:62, 3] = 255; a[210, 12:62, :3] = (8, 5, 4); a[210, 12:62, 3] = 126   # 아래 외곽선(x 60 의 원화 외곽선 y 204~210 과 같은 굵기)
    Image.fromarray(a).save(path)
import shutil as _sh; _sh.copy(os.path.join(W, 'hammerUp.png'), os.path.join(W, 'hammerUpA.png')); _fix_hammer(os.path.join(W, 'hammerUpA.png'))   # 대기 망치는 원화 그대로(흰 앞머리가 홈에 들어감), 공격 중(weaponA, 맨 앞)만 고친 망치
_WP = [round(float(_pv[0]), 1), round(float(_pv[1]), 1)]; _up = lambda d: [_WP[0], round(_WP[1] - d * 2, 1)]
part('weapon', os.path.join(W, 'hammerUpA.png'), _WP, scale=1.0, tip=_up(170), pommel=_up(-58), tips=[[_WP[0] - 12, round(_WP[1] - 340, 1)], [_WP[0] + 12, round(_WP[1] - 340, 1)]], shaftDir=[0.0, -1.0])
part('weaponA', os.path.join(W, 'hammerUpA.png'), _WP, scale=1.0, tip=_up(170), pommel=_up(-58), tips=[[_WP[0] - 12, round(_WP[1] - 340, 1)], [_WP[0] + 12, round(_WP[1] - 340, 1)]], shaftDir=[0.0, -1.0])
for n in ['thighN', 'thighF']: part(n, A(n), [0, 0], scale=1.0)
for n in ['bootN', 'bootF']: part(n + 'Shin', os.path.join(W, n + 'Shin.png'), [0, 0], scale=1.0)
for n, sd in [('bootN', 'near'), ('bootF', 'far')]: part(n + 'Foot', os.path.join(W, n + 'Foot.png'), pc(LJ[sd]['a'], O_[n]))

# ---------------- 뼈 ----------------
bones = [dict(name='root', parent=None, pos=[0, 0]), dict(name='hip', parent='root', pos=L2(HIP))]
def bone(name, parent, at, parent_at, part_=None, rot=0.0):
    b = dict(name=name, parent=parent, pos=[round(float(at[0] - parent_at[0]) * 2, 1), round(float(at[1] - parent_at[1]) * 2, 1)])
    if rot: b['rot'] = round(rot, 4)
    if part_: b['part'] = part_
    bones.append(b)
bone('hips', 'hip', HIP, HIP, 'hips'); bone('belt', 'hips', HIP, HIP, 'belt'); bone('flapN', 'hips', np.array([170.0, 314]), HIP, 'flapN'); bone('flapC', 'hips', np.array([210.0, 326]), HIP, 'flapC')
bone('torso', 'hip', HIP, HIP, 'torso'); bone('sideF', 'torso', HIP, HIP, 'sideF'); bone('head', 'torso', NECK, HIP, 'head'); bone('pony', 'head', PONY, NECK, 'pony')
bone('armU', 'torso', SH_N, HIP, 'armU'); bone('armL', 'armU', EL_N, SH_N, 'armL', rot=0.3)   # 엔진 대기 팔꿈치 처짐(−0.3)만큼 미리 반대로 → 대기 = 원화
bone('pauldron', 'torso', SH_N, HIP, 'pauldron')
bone('armF', 'torso', SH_F, HIP); bone('foreF', 'armF', EL_F, SH_F, 'foreF'); bone('fistF', 'foreF', WR_F, EL_F, 'fistF')
bone('weapon', 'fistF', G, WR_F, 'weapon', rot=HTH)
for n in ['cape', 'scarf', 'pouch', 'skirt', 'skirtB', 'pauldronF']: bones.append(dict(name=n, parent='torso', pos=[0, -200]))   # 그림 없는 뼈: 엔진이 이름으로 찾음

# ---------------- 다리 — 서 있을 때 = 원화 다리(오림), 달릴 때 = 시트 허벅지(4번 시트) + 시트 부츠(1번 22칸, 앞코 오른쪽)를 발목에서 나눔 ----------------
LEG_HY = 334.0
def sole(n, ank):
    a = np.array(Image.open(os.path.join(W, n + 'Foot.png')))[..., 3] > 128; o = O_[n]; ys = np.nonzero(a.any(1))[0]; yb = ys.max(); out = []; dy = O[1] - (yb + o[1])
    for y in (yb - 4, yb):
        xs = np.nonzero(a[y])[0]; out += [[round(float(xs.min() + o[0] - ank[0]), 1), round(float(y + o[1] - ank[1] + dy), 1)], [round(float(xs.max() + o[0] - ank[0]), 1), round(float(y + o[1] - ank[1] + dy), 1)]]
    return out
seg = lambda n, o, p0, p1: {'part': n, 'a': pc(p0, o), 'b': pc(p1, o), 'w': 1.0}
ln = lambda sd, p0, p1: round(float(np.linalg.norm(LJ[sd][p1] - LJ[sd][p0])) * 2, 1)
def stand(sd, n):
    j = LJ[sd]; bn = 'boot' + n
    return {'fade': [0.05, 0.1], 'boot': {'part': bn + 'Foot', 'sole': sole(bn, j['a'])}, 'thighImg': seg('thigh' + n, O_['thigh' + n], j['h'], j['k']),
            'shinImg': seg(bn + 'Shin', O_[bn], j['k'], j['a']), 'kneeImg': None}
def sheet_copy(src, dst):
    a = np.array(Image.open(src).convert('RGBA')).astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None)
    a[..., 0] -= m; a[..., 2] -= m; Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(dst)
TH_R, SH_R = 140.0, 150.0                                         # 달리기 허벅지·정강이(무릎→발목) 길이(리그)
RS = 2.0 * 1.029                                                 # 시트 부츠 22칸 = 원화 1.03배(SIFT) → 리그 배율
_bf = np.array(Image.open(os.path.join(C, 'bootF.png')))
KNEE_S, ANK_S = np.array([44.0, 14.0]), np.array([40.0, 86.0])    # 시트 부츠: 무릎(목 위 끝 안쪽) · 발목(발등 시작 위)
_Y, _X = np.mgrid[0:_bf.shape[0], 0:_bf.shape[1]]
_sh = _bf.copy(); _sh[..., 3] = np.where(_Y < ANK_S[1] + 6, _bf[..., 3], 0); Image.fromarray(_sh).save(os.path.join(W, 'rshin.png'))
_ft = _bf.copy(); _ft[..., 3] = np.where(_Y > ANK_S[1] - 8, _bf[..., 3], 0); Image.fromarray(_ft).save(os.path.join(W, 'rboot.png'))
sheet_copy(os.path.join(W, 'rshin.png'), os.path.join(OUT, 'parts', 'rshin.png')); def_parts['rshin'] = dict(src='parts/rshin.png', pivot=[0, 0], scale=1.0)
sheet_copy(os.path.join(W, 'rboot.png'), os.path.join(OUT, 'parts', 'rboot.png')); def_parts['rboot'] = dict(src='parts/rboot.png', pivot=ANK_S.tolist(), scale=RS)
_sil = SH_R / RS; print('  run shin image len', round(float(np.linalg.norm(ANK_S - KNEE_S)), 1), 'want', round(_sil, 1))
def sole_sheet(a, ank):
    m = a[..., 3] > 128; ys = np.nonzero(m.any(1))[0]; yb = ys.max(); out = []
    for y in (yb - 6, yb - 3, yb):
        xs = np.nonzero(m[y])[0]; out += [[round(float(xs.min() - ank[0]), 1), round(float(y - ank[1]), 1)], [round(float(xs.max() - ank[0]), 1), round(float(y - ank[1]), 1)]]
    return out
rseg = {}
for n in ['thighN', 'thighF']:   # 4번 시트 허벅지: 위 = 반바지 속(곧게 잘림), 아래 = 둥근 무릎
    a = np.array(Image.open(os.path.join(C, n + '.png')).convert('RGBA')); m = a[..., 3] > 128; H = m.shape[0]
    _ys = np.nonzero(m.any(1))[0]; y0_, y1_ = _ys.min(), _ys.max(); ty, tx = np.nonzero(m[y0_:y0_ + 6]); top = [float(tx.mean()), float(ty.mean() + y0_)]
    kr = int(y0_ + (y1_ - y0_) * .80); kx = np.nonzero(m[kr])[0]; kn = [float(kx.mean()), float(kr)]
    il = math.hypot(kn[0] - top[0], kn[1] - top[1]); wid = float(m[int(y0_ + (y1_ - y0_) * .4)].sum())
    sheet_copy(os.path.join(C, n + '.png'), os.path.join(OUT, 'parts', 'r' + n + '.png')); def_parts['r' + n] = dict(src=f'parts/r{n}.png', pivot=[0, 0], scale=1.0)
    s_ = TH_R / il; rseg[n] = {'part': 'r' + n, 'a': [round(top[0], 1), round(top[1], 1)], 'b': [round(kn[0], 1), round(kn[1], 1)], 'w': round(64.0 / (wid * s_), 3)}   # 굵기 64 리그(원화 허벅지 32px)
kp = np.array(Image.open(os.path.join(C, 'kneeF.png'))); sheet_copy(os.path.join(C, 'kneeF.png'), os.path.join(OUT, 'parts', 'rknee.png'))
def_parts['rknee'] = dict(src='parts/rknee.png', pivot=[kp.shape[1] / 2, kp.shape[0] * .45], scale=RS)
legs = {'hip': [0, round((LEG_HY - HIP[1]) * 2, 1)], 'thigh': TH_R, 'shin': SH_R, 'thighFirst': True,
        'thighImg': rseg['thighF'], 'shinImg': {'part': 'rshin', 'a': KNEE_S.tolist(), 'b': ANK_S.tolist(), 'w': 1.0},
        'boot': {'part': 'rboot', 'sole': sole_sheet(_ft, ANK_S), 'ankleRange': [-0.35, 0.45], 'runLock': 0.0},   # runLock 0(엔진 opt-in): 달리기 다리 그림(시트 정강이·부츠)이면 발목 고정 — 부츠가 정강이와 한 줄, 발 구름 없음. DHL 10-21 12:35 '뛸 때 발이 2조각으로 나눠지면 이상 · 발 구르는 것 없이 뛰어도 좋으니 조각을 쪼개지 말아줘요'(서 있는 원화 다리 그림은 원래 범위)
        'near': {'x': round(float(LJ['near']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['near']['h'][0] - HIP[0]) * 2, 1), 'runX': -12, 'shade': 0,
                 'thigh': ln('near', 'h', 'k'), 'shin': ln('near', 'k', 'a'), 'thighImg': rseg['thighN'], 'stand': stand('near', 'N')},
        'far': {'x': round(float(LJ['far']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['far']['h'][0] - HIP[0]) * 2, 1), 'runX': 12, 'shade': 0.12,
                'thigh': ln('far', 'h', 'k'), 'shin': ln('far', 'k', 'a'), 'thighImg': rseg['thighF'], 'stand': stand('far', 'F')}}
print('  legs near', legs['near']['thigh'], legs['near']['shin'], 'far', legs['far']['thigh'], legs['far']['shin'], 'run thigh w', {k: v['w'] for k, v in rseg.items()})

# ---------------- 표정·깜빡임: 시트 25~32칸(머리 2칸과 같은 그림 자리) → 머리 맞춤(MH)으로 원화 얼굴에 ----------------
_hsv = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV); _skn = (_hsv[..., 0] >= 5) & (_hsv[..., 0] <= 25) & (_hsv[..., 1] > 80) & (_hsv[..., 2] > 140) & (RA[..., 3] > 200)
_fs = np.zeros((512, 512), bool); _fs[165:252, 200:335] = (_skn & own['head'])[165:252, 200:335]
_lb, _n = ndimage.label(_fs); _sz = ndimage.sum(_fs, _lb, range(1, _n + 1)); FACE = ndimage.binary_fill_holes(_lb == (int(np.argmax(_sz)) + 1))
_fm = np.clip(cv2.GaussianBlur(cv2.erode(FACE.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (5, 5), 1.0) * 1.15, 0, 1)
_omean = RA[..., :3][_skn & FACE].mean(0)
hb = np.array(Image.open(A('head'))); hx0, hy0 = int(O_['head'][0]), int(O_['head'][1]); hh, hw = hb.shape[:2]
def face_patch(cellname, out):
    a = np.array(Image.open(os.path.join(C, cellname + '.png')).convert('RGBA'))
    wf = cv2.warpAffine(a, MH, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
    h2 = cv2.cvtColor(wf[..., :3], cv2.COLOR_RGB2HSV); s3 = (h2[..., 0] >= 5) & (h2[..., 0] <= 25) & (h2[..., 1] > 80) & (h2[..., 2] > 140) & (wf[..., 3] > 200)
    if (s3 & FACE).sum() > 50: d = _omean - wf[..., :3][s3 & FACE].mean(0); wf = wf.copy(); wf[..., :3][s3] = np.clip(wf[..., :3][s3].astype(np.float32) + d, 0, 255).astype(np.uint8)
    al = _fm * (wf[..., 3] / 255.0); o2 = RA.astype(np.float32).copy(); o2[..., :3] = o2[..., :3] * (1 - al[..., None]) + wf[..., :3] * al[..., None]
    fc = o2.astype(np.uint8)[hy0:hy0 + hh, hx0:hx0 + hw].copy(); fc[..., 3] = np.where(FACE[hy0:hy0 + hh, hx0:hx0 + hw], hb[..., 3], 0)
    Image.fromarray(fc).save(os.path.join(W, out + '.png'))
FACE_N = ['neutral', 'happy', 'angry', 'focus', 'shout', 'effort']
for n in FACE_N: face_patch('face_' + n, 'face_' + n); part('face_' + n, os.path.join(W, 'face_' + n + '.png'), def_parts['head']['pivot'])
for n in ['half', 'closed']: face_patch('blink_' + n, 'blink_' + n); part('blink_' + n, os.path.join(W, 'blink_' + n + '.png'), def_parts['head']['pivot'])
FACES = {n: 'face_' + n for n in FACE_N if n != 'neutral'}; FACES['grimace'] = 'face_effort'; FACES['surprised'] = 'face_shout'

# ---------------- 내려찍기 (attack/smash.py) ----------------
# 10-19 21:36 DHL '전에 한 손으로 망치 치던 버전이 좋았는데 그걸로' → 한 손(3차, attack/smash_one.py)이 기본. 두 손 6차 = SMASH_FILE=smash.py
exec(open(os.path.join(HERE, 'attack', os.environ.get('SMASH_FILE', 'smash_one.py'))).read())

# ---------------- 그리는 순서 (뒤 → 앞) ----------------
# (10-20 06:10 DHL 06:05 '표시한 머리(포니테일)보다도 뒤로') 망치 = 포니테일·몸통·머리 뒤, 다리·골반 앞(자루 끝이 허리띠·허벅지 앞) — 대기·달리기에서 망치가 몸통과 안 겹쳐 그대로
draw = ['armF', 'foreF', 'weapon', 'fistF', 'legFar', 'legNear', 'hips', 'flapN', 'flapC', 'belt', 'pony', 'torso', 'head', 'armU', 'pauldron', 'armL']   # (10-20 18:32 DHL '같이 진행' = 12 v1.4 앞뒤 규칙) 먼 팔뚝·망치·주먹 = 다리·골반·포니테일·상체·머리 뒤 — 공격 drawA 와 같은 앞뒤. 대기에서 바뀌는 곳 = 자루 끝(쇠 마개)이 먼 허벅지·반바지 뒤
#   (전 v6.4: 다리·골반·천자락·허리띠 → 먼 팔뚝 → 망치 → 포니테일 → 상체 → 머리 → 주먹 → 가까운 팔)
_top = int(np.nonzero((own['head'] | own['pony']).any(1))[0].min())
rig = {'name': 'dulcinea-rust', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': def_parts, 'bones': bones, 'legs': legs, 'draw': draw, 'hidden': [], 'faces': FACES, 'blinkFaces': {'half': 'blink_half', 'closed': 'blink_closed'},
       'metrics': {'bodyHeight': round(2 * (O[1] - 120), 1), 'note': '리그 단위; 머리 위(포니테일 아래 머리카락 y120)~발바닥(485) ×2, 무기·포니테일 위 제외'},
       'armPhase': 0, 'gait': {'stance': 0.32, 'heelKick': 0.85, 'kneeLift': 0.95, 'strideBase': 70, 'strideK': 0.2, 'swingReach': 0.12, 'swingAng': 0.12, 'landAng': 0, 'hipBase': 6, 'bob': 16, 'lean': 0.2, 'strideFlex': [0.75, 1.5], 'headRun': 0.06, 'elbowRun': 1.2, 'armSwing': 0.55, 'armBias': 0.1},
       'ponySway': 0.6, 'carrySwing': 0.4, 'wristRange': 0.3, 'follow': [{'bone': 'pauldron', 'src': 'armU', 'k': 0.35}],
       'bounce': [{'bone': 'flapN', 'stiff': 170, 'damp': 7, 'y': 0.3, 'rot': -0.006, 'max': 10}, {'bone': 'flapC', 'stiff': 150, 'damp': 6, 'y': 0.35, 'rot': 0.008, 'max': 12}],
       'ui': {'attack': 'smash', 'touch': 'hop'},
       'gameRef': {'refOrigin': [round(float(O[0] - (HIP[0] - 248.9)), 1), float(O[1])], 'refScale': 2.0, 'refLift': 0,
                   'note': '게임 그림 char_0002.png(512) = 원화(md5 같음). x = 도감 칸(fitArt 중심 248.9, index.html measureBox 를 브라우저에서 같은 계산)에서 골반(hip x 232)이 가운데 (3·9·13·23 과 같은 규칙)'},
       'cutHold': 0.32,   # 10-20 06:40 스킬 컷인 = 망치를 머리 위로 높이 든 휘두름 시작(SW1) — 얼굴·망치 다 보임
       'note': '2 러스트 둘시네 (2026-10-19, v1 대기·달리기). 먼 손으로 큰 망치를 쥠(1시), 가까운 손 주먹. 보이는 곳은 원화를 오림, 달리는 다리는 시트.'}
rig.update(SMASH)
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(os.path.join(OUT, 'parts'))): _h.update(fn.encode()); _h.update(open(os.path.join(OUT, 'parts', fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_dulcinea.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['dulcinea-rust']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(def_parts), 'parts, version', rig['version'])
