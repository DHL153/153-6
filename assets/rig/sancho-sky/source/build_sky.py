"""23 스카이아크 산초 리그 조립 — 13 네온 산초 build_neon.py 를 옮겨 온 틀 (2026-10-19 18:40, 새 원화·조각 시트 오기 전에 준비).
  ★ 표시 = 새 원화(char_0023 러스트 자세)에서 다시 잴 값 — 지금은 13 값이 들어 있음(그대로 돌리면 안 됨)
  13 과 다른 곳: 목도리 꼬리 두 갈래(streamers tailA·tailB, 21 스카이 알론소 방식) · 포니테일(pony 뼈, ponySway — 2 둘시네 방식) ·
                 가까운 어깨 은색 어깨갑(padN — 13 의 먼 어깨판 자리 없음) · 입 보임(faces23 = neutral 과 다른 곳이라 입 저절로) ·
                 달리기 다리 굵기 = 원화 다리 굵기 × LEG_T(13 v1.1 DHL '너무 얇음' → 처음부터 원화에서 잼)
입력: ref512.png(새 원화 = 게임 char_0023) · pieces/(조각 시트 1, cut23.py) · polys.json(원화에서 오릴 다각형) · joints.json(관절) · geom.json(reg23.py: 시트 조각 → 원화)
출력: ../rig.json, ../rig.def.js, ../parts/*.png
실행: cd source && python3 -I cut23.py && python3 -I reg23.py && python3 -I build_sky.py
원칙(DHL): 대기 자세 = 원화. 두 손은 처음부터 끝까지 칼을 쥠(swordGrip.guard, frame torso). 손은 원화 손 그대로(오려 씀). 손 뒤집기 금지. 칼 크기 그대로·칼은 늘 머리 앞.
손 순서(원화): 날밑 쪽 위 주먹 = 오른손 = 가까운 팔(흰·자주 팔뚝 보호대가 화면 왼쪽 아래 팔꿈치에서 올라옴) · 폼멜 쪽 아래 주먹 = 왼손 = 먼 팔(흰 팔뚝이 가슴 앞을 지나 화면 오른쪽 먼 어깨)
엔진 이름: near(armF→foreF, 칼 쥔 점 G) = 가까운 팔(위 주먹) · far(armU→armL, G + U·sF) = 먼 팔(아래 주먹) + 먼 어깨 보호대(pauldron)  — 러스트 산초와 같음
러스트와 다른 곳: 가까운 어깨가 아래 주먹 뒤(시트 상체 조각 어깨 구멍) → 대기 팔꿈치 쪽이 반대(ikSideK, 키에서 팔이 접힌 순간에 바꿈) · 칼 그림 축 = 손잡이(원화 날이 4° 더 기움)
좌표: 원화 512px로 적고 ×2 = 리그 단위.
"""
import json, math, os, shutil, hashlib
import numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); PC = os.path.join(HERE, 'pieces'); W = os.path.join(HERE, 'work'); OUT = os.path.join(HERE, '..')
os.makedirs(os.path.join(OUT, 'parts'), exist_ok=True); os.makedirs(W, exist_ok=True)
for f in os.listdir(os.path.join(OUT, 'parts')): os.remove(os.path.join(OUT, 'parts', f))
img = lambda p: Image.open(p).convert('RGBA')
RA = np.array(img(os.path.join(HERE, 'ref512.png'))); AL = RA[..., 3] > 0
POLY = json.load(open(os.path.join(HERE, 'polys.json'))); GEO = json.load(open(os.path.join(HERE, 'geom.json'))); JT = json.load(open(os.path.join(HERE, 'joints.json'), encoding='utf-8'))
def pmask(name_or_pts, size=(512, 512)):
    m = Image.new('L', size, 0); ImageDraw.Draw(m).polygon([tuple(p) for p in (POLY[name_or_pts] if isinstance(name_or_pts, str) else name_or_pts)], fill=255); return np.array(m) > 0
def dil(m, r): return cv2.dilate(m.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0
def ero(m, r): return cv2.erode(m.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0
def slivers(a, k=5):
    """가늘게 삐져나온 띠(폭 < k px — 이웃 조각을 뺀 경계에 남은 외곽선 조각) 지움 (11)"""
    on = (a[..., 3] > 40).astype(np.uint8); op = cv2.morphologyEx(on, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    km = cv2.dilate(op, np.ones((3, 3), np.uint8)).astype(bool); a = a.copy(); a[..., 3] = np.where(km, a[..., 3], 0); return a
def islands(a, name, frac=0.03):
    """오린 조각에서 떨어진 작은 섬(다른 부품 가장자리 부스러기) 지움 — 대기 땐 안 보이다가 달리기·공격에서 떠 보임 (11 v1)"""
    on = (a[..., 3] > 40).astype(np.uint8); n, lab, stt, _ = cv2.connectedComponentsWithStats(on, connectivity=8)
    if n <= 2: return a
    big = stt[1:, cv2.CC_STAT_AREA].max(); keep = np.zeros(n, bool); keep[1:] = stt[1:, cv2.CC_STAT_AREA] >= max(40, frac * big)
    km = cv2.dilate(keep[lab].astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    rm = int((~keep[1:]).sum())
    if rm: print('  islands', name, 'removed', rm, 'areas', sorted(int(v) for v in stt[1:, cv2.CC_STAT_AREA][~keep[1:]])[-5:])
    a = a.copy(); a[..., 3] = np.where(km, a[..., 3], 0); return a
COVER = np.zeros((512, 512), np.uint8)   # 오린 조각 알파 합(대기 자리) — 원화에 있는데 아무 조각도 안 덮는 틈 찾기
def save_crop(a, name, sl=0, keep=False):
    """a(512×512 RGBA, 원화 좌표) → work/name.png, 반환 = 칸 왼쪽 위(원화 px). keep: 떨어진 작은 덩어리도 둠(위 주먹 옆 흰 반짝임)"""
    a = (slivers(a, sl) if sl else a) if keep else islands(slivers(a, sl) if sl else a, name); COVER[:] = np.maximum(COVER, a[..., 3]); ys, xs = np.nonzero(a[..., 3] > 0)
    if not len(xs):   # 원화에서 다 가려진 조각(23 가까운 윗팔 — 주먹 뒤) → 4×4 투명, 칸 = 다각형 자리
        print('  empty crop', name); Image.fromarray(np.zeros((4, 4, 4), np.uint8)).save(os.path.join(W, name + '.png')); return np.array([256.0, 256.0])
    x0, y0 = xs.min() - 2, ys.min() - 2; Image.fromarray(a[y0:ys.max() + 3, x0:xs.max() + 3]).save(os.path.join(W, name + '.png')); return np.array([x0, y0], float)
def crop(mask, name, grow=0, cut=None, src=None, sl=0, keep=False):
    if grow: mask = dil(mask, grow)
    if cut is not None: mask = mask & ~cut
    a = (RA if src is None else src).copy(); a[..., 3] = np.where(mask, a[..., 3], 0); return save_crop(a, name, sl, keep)
def desp(a):
    """자홍 배경 번짐(외곽선이 보라색) 지움: min(R,B) − G 만큼 R·B 를 뺌"""
    a = a.astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None); a[..., 0] -= m; a[..., 2] -= m; return np.clip(a, 0, 255).astype(np.uint8), m
def sheet_copy(n, dst):
    a, m = desp(np.array(img(os.path.join(PC, n + '.png')))); Image.fromarray(a).save(dst); return int((m > 4).sum())
# ---------------- 원화 관절 (512 px, joints.json) ----------------
P_ = lambda k: np.array(JT[k], float)
O = P_('O'); HIP = P_('HIP'); NECK = P_('NECK')
SH_N, EL_N = P_('SH_N'), P_('EL_N')   # 가까운 팔(엔진 armF→foreF): 어깨(아래 주먹 뒤 — 시트 상체 어깨 구멍) · 팔꿈치(흰·자주 팔뚝 보호대 왼쪽 아래 끝)
SH_F, EL_F = P_('SH_F'), P_('EL_F')   # 먼 팔(엔진 armU→armL): 어깨(먼 어깨 보호대 안) · 팔꿈치(흰 팔뚝 판 오른쪽 끝, 검은 마디)
# 칼: 손잡이 축 = 날밑 금고리 → 폼멜 금띠 (원화·시트 같은 점) — 시트 → 원화 닮음(손잡이) MS. 원화 날은 이 축보다 4° 더 기움 → 날은 원화 그림 그대로
HJ = JT['handle']; RING_A, POM_A = np.array(HJ['collar'], float), np.array(HJ['pommel'], float)
RING_S, POM_S = np.array([40.0, 289.0]), np.array([39.4, 382.1])     # 시트 칼 그림의 같은 두 점(날밑 가운데 금 동그라미 · 폼멜 금 무게중심) — 시트 손잡이가 원화보다 짧아 1.18배(금고리 · 폼멜 큰 금띠 금색 무게중심)
def simil(a0, a1, b0, b1):   # a(시트) → b(원화) 닮음
    va, vb = a1 - a0, b1 - b0; s = np.linalg.norm(vb) / np.linalg.norm(va); th = math.atan2(vb[1], vb[0]) - math.atan2(va[1], va[0])
    R = s * np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]]); return np.c_[R, b0 - R @ a0]
MS = simil(RING_S, POM_S, RING_A, POM_A); R2 = MS[:, :2]; SMS = float(np.hypot(*R2[:, 0]))   # 시트 칼 px 당 원화 px (1.05)
HD = (POM_A - RING_A) / np.linalg.norm(POM_A - RING_A); U = -R2[:, 1] / np.linalg.norm(R2[:, 1])   # 칼끝 방향(원화) = 칼 그림 위쪽(−v) 을 MS 로 옮긴 것 — 원화 두 점 선(HD)과 0.2° 다르면 칼끝에서 1px 어긋났음(엔진은 그림 위쪽을 U 로 돌림)
on_handle = lambda y: RING_A + HD * ((y - RING_A[1]) / HD[1])
G_U = on_handle(float(HJ['G_U_y'])); G_L = on_handle(float(HJ['G_L_y']))     # 쥔 점: 위 주먹(가까운 손) · 아래 주먹(먼 손)
S_LOW = -float(np.dot(G_L - G_U, -U)) * 2
print('  MS scale', round(float(np.hypot(*R2[:, 0])), 4), 'U', np.round(U, 4).tolist(), 'G_U', np.round(G_U, 1).tolist(), 'G_L', np.round(G_L, 1).tolist(), 'S_LOW', round(S_LOW, 1))

# ---------------- 칼 그림 틀: 시트 칼 그림 크기 + 여백(원화 날이 이 틀에서 4° 기울어 칼끝 쪽이 왼쪽으로 18px 나감) ----------------
sw0 = np.array(img(os.path.join(PC, 'sword.png'))); sw0, _ = desp(sw0); H0, W0 = sw0.shape[:2]; HROW = 305   # 시트 칼 날밑 아래 = 손잡이 첫 줄   # 날밑 아래 = 손잡이 첫 줄(시트 칼)
PX, PY = 30, 8; CW, CH = W0 + 2 * PX, H0 + PY
swA = np.zeros((CH, CW, 4), np.uint8); swA[HROW:H0, PX:PX + W0] = sw0[HROW:]        # 시트에서 쓰는 곳 = 손잡이·폼멜만(주먹에 가린 곳 메움). 날·날밑은 원화
MW = MS.copy(); MW[:, 2] = MS[:, 2] - R2 @ np.array([PX, 0.0])   # 칼 그림(여백 포함) → 원화
toImg = lambda p: np.linalg.solve(R2, np.array(p, float) - MW[:, 2])
# 원화 칼 자리 SWM: 날 = 원화 알파 가장자리 직선(joints blade) + 칼끝(원화 알파 첫 덩어리) · 날밑·손잡이 = 시트 날밑·손잡이(줄 262~)를 MS 로
BL = JT['blade']; la, lk, _ = BL['left']; ra_, rk, _ = BL['right']
SWM = np.zeros((512, 512), bool)
GT = JT['guardTop']; _g0, _g1 = np.array(GT['p0'], float), np.array(GT['p1'], float)
gtop = lambda x: _g0[1] + (x - _g0[0]) * (_g1[1] - _g0[1]) / (_g1[0] - _g0[0])          # 날밑 가로대 윗선(원화)
for y in range(0, 280):
    xs = np.nonzero(RA[y, 40:300, 3] > 100)[0] + 40   # 칼끝 둘레 반투명 점(알파 1~100)은 덩어리를 끊음 → 진한 점으로 찾고 ±3px
    if not len(xs): continue
    if y < 40:   # 칼끝: 첫 덩어리(2px 틈까지 이어 봄)
        e = xs[0]
        for x in xs[1:]:
            if x > e + 3: break
            e = x
        x0_, x1_ = xs[0] - 3, e + 3
    else: x0_, x1_ = int(math.floor(la + lk * y)), int(math.ceil(ra_ + rk * y))
    for x in range(x0_, x1_ + 1):
        if 0 <= x < 512 and y < gtop(x) + 4: SWM[y, x] = True
_r, _g, _b = [RA[..., i].astype(int) for i in range(3)]
GOLD = (RA[..., 3] > 150) & (_r > 150) & (_g > 100) & (_b < 120) & (_r - _b > 70) & (_r >= _g)
_yy, _xx = np.mgrid[0:512, 0:512]
_gbox = (_xx > 180) & (_xx < 266) & (_yy > 236) & (_yy < 302); _pbox = (_xx > 244) & (_xx < 283) & (_yy > 354) & (_yy < 385)
SWM |= dil(GOLD & (_gbox | _pbox), 3)                                                    # 날밑·폼멜 = 원화 금색 + 외곽선 3px (시트 날밑은 원화와 모양이 달라 안 씀)
_gh = np.zeros((CH, CW), np.uint8); _gh[HROW:H0, PX:PX + W0] = (sw0[HROW:, :, 3] > 90)
SWM |= cv2.warpAffine(_gh, MW.astype(np.float32), (512, 512), flags=cv2.INTER_NEAREST) > 0   # 손잡이(주먹 사이·밑) = 시트 손잡이
SWM &= AL
SW_TIP_A = np.array(JT['blade']['tip'], float)
SW_PIV = toImg(G_U); SW_TIP = toImg(SW_TIP_A); SW_POM = toImg(POM_A + HD * 24); SW_GRD = toImg(np.array(BL['guardC'], float))
print('  sword img', CW, CH, 'pivot', np.round(SW_PIV, 1).tolist(), 'tip', np.round(SW_TIP, 1).tolist(), 'pommel', np.round(SW_POM, 1).tolist(), 'G_L → img', np.round(toImg(G_L), 1).tolist(), 'SWM px', int(SWM.sum()))

# ---------------- 원화에서 오리는 조각 ----------------
mk = {n: pmask(n) for n in ['head', 'nearUp', 'nearFore', 'farFore', 'farUp', 'pauldron', 'torso', 'hips', 'thighN', 'shinN', 'bootN', 'thighF', 'shinF', 'bootF', 'pony', 'tail']}
# 손·팔: 앞에 그리는 조각이 겹친 픽셀을 가짐 — 아래 주먹·먼 팔뚝(armL) > 위 주먹·가까운 팔뚝(foreF) > 가까운 윗팔(armF) / 어깨 보호대 > 먼 윗팔(armU)
und = lambda m, *tops: m & ~np.logical_or.reduce([ero(t, 3) for t in tops])
A_farFore = mk['farFore']; A_nearFore = und(mk['nearFore'], A_farFore); A_nearUp = und(mk['nearUp'], mk['nearFore'], A_farFore)
A_pd = und(mk['pauldron'], A_farFore); A_farUp = und(mk['farUp'], mk['pauldron'], A_farFore)
ARMS = A_farFore | A_nearFore | A_nearUp | A_pd | A_farUp
SWin = dil(SWM, 1)   # 칼 자리 + 1px — 칼 외곽선을 머리·몸통에 남기지 않음
# 머리: 다각형 − 칼(칼이 머리 앞) − 주먹. 칼·주먹 뒤에 가려진 머리카락은 시트 머리(같은 크기, reg13 SIFT)로 메움
A_head = mk['head'] & ~SWin & ~ARMS & AL & ~mk['pony'] & ~mk['tail'] & ~pmask('tailB')
Mh = np.array(GEO['head']['M'], np.float32)
_sh = cv2.warpAffine(desp(np.array(img(os.path.join(PC, 'head.png'))))[0], Mh, (512, 512), flags=cv2.INTER_LANCZOS4)
# 칼·주먹 둘레 4px 안에서는 시트 머리 실루엣 밖 원화 점을 뺌 — 칼·주먹 외곽선 부스러기가 머리에 남아 공격 때 귀 왼쪽에 검은 점으로 떴음(10-19 렌더 0.53)
_near = dil(ARMS, 4) | dil(SWin, 2); A_head &= ~(_near & ~(_sh[..., 3] > 64))   # 칼 쪽은 2px 만(더 넓히면 칼날 옆 머리카락 외곽선이 머리에서 빠져 칼 그림에 붙었음)
HEADA = RA.copy(); HEADA[..., 3] = np.where(A_head, RA[..., 3], 0)
_fill = (_sh[..., 3] > 128) & (SWin | ARMS | _near) & mk['head'] & ~A_head & dil(RA[..., 3] > 128, 2)
HEADA[_fill] = _sh[_fill]; HEADA[..., 3][_fill] = 255; print('  head hair fill (behind sword/fist) px', int(_fill.sum()))
_ha = HEADA[..., 3] > 128; _hole = ndimage.binary_fill_holes(_ha) & ~_ha   # 메운 머리카락 안 작은 구멍(시트·원화 둘 다 없는 곳) → 둘레 색
if _hole.any():
    _c = cv2.inpaint(np.ascontiguousarray(HEADA[..., :3]), _hole.astype(np.uint8) * 255, 3, cv2.INPAINT_TELEA); HEADA[..., :3][_hole] = _c[_hole]; HEADA[..., 3][_hole] = 255
print('  head holes filled px', int(_hole.sum()))
# 23 뒷머리: 시트 머리는 뒷머리가 짧고 매듭(크림 천)이 귀 바로 뒤 — 원화 매듭(포니테일 뿌리, 칼날 왼쪽)과 두 개가 됨 → 시트 매듭은 머리카락으로 지움,
#  칼날 뒤 원화 매듭 ~ 시트 뒷머리 사이(BRIDGE)는 머리 그림을 왼쪽으로 옮겨 붙인 머리카락 + 남은 틈 메움 — 칼이 비켜도 포니테일이 머리에 붙어 보이게
HAIR = np.array([44, 58, 92], np.uint8)   # 원화 남색 머리카락 중간색
_c3 = HEADA[..., :3].astype(int); _tieS = _fill & (_xx > 212) & (_xx < 254) & (_yy > 258) & (_yy < 304) & (_c3.min(2) > 135)
if _tieS.any():
    _ti = dil(_tieS, 2) & (HEADA[..., 3] > 128); _s0 = np.ascontiguousarray(HEADA[..., :3].copy()); _s0[HEADA[..., 3] < 128] = HAIR
    HEADA[..., :3][_ti] = cv2.inpaint(_s0, _ti.astype(np.uint8) * 255, 5, cv2.INPAINT_TELEA)[_ti]
BRIDGE = pmask([[178, 258], [194, 238], [222, 234], [236, 258], [238, 292], [224, 302], [200, 302], [186, 296]])
_pv = mk['pony'] & AL & ~SWin
_sh_ = np.zeros_like(HEADA); _sh_[:, :-30] = HEADA[:, 30:]   # 머리 그림 30px 왼쪽
_br = BRIDGE & SWin & ~(HEADA[..., 3] > 128) & ~_pv   # 칼 뒤만(칼 밖 빈 곳은 대기 때 보이니 그대로 비움)
_bs = _br & (_sh_[..., 3] > 128) & (_sh_[..., :3].astype(int).min(2) < 135)
HEADA[_bs] = _sh_[_bs]; _rest = _br & ~_bs
if _rest.any():
    _src = np.ascontiguousarray(HEADA[..., :3].copy()); _src[HEADA[..., 3] < 128] = HAIR   # 머리 밖(칼·손잡이 색)을 끌어오지 않게
    HEADA[..., :3][_rest] = cv2.inpaint(_src, _rest.astype(np.uint8) * 255, 4, cv2.INPAINT_TELEA)[_rest]; HEADA[..., 3][_rest] = 255
_hb = HEADA[..., 3] > 128; _bd = ndimage.distance_transform_edt(_hb | _pv); _be = _br & (_bd <= 2.2); HEADA[..., :3][_be] = (22, 24, 36)   # 메운 뒷머리 바깥 가장자리 외곽선
print('  sheet tie → hair px', int(_tieS.sum()), 'back-hair bridge px', int(_br.sum()), '(shifted hair', int(_bs.sum()), ')')
HEADA = slivers(HEADA, 3)
_armsIn = ero(mk['nearFore'] | mk['farFore'], 3)
_others = mk['torso'] | mk['hips'] | ARMS | mk['thighN'] | mk['thighF'] | mk['shinN'] | mk['shinF'] | mk['bootN'] | mk['bootF'] | mk['pony'] | mk['tail'] | pmask('tailB')
SW_FRINGE = dil(SWM, 9) & AL & ~_others & ~SWin & ~(HEADA[..., 3] > 128) & ~(mk['head'] & ~dil(SWM, 3) & (_sh[..., 3] > 64))   # 머리 다각형 안에선 시트 머리카락 자리면 칼 둘레 3px 까지만(머리카락 외곽선이 칼에 붙어 같이 움직였음)
SWART = ((SWin & ~_armsIn) | SW_FRINGE | (dil(SWM, 3) & ARMS & ~_armsIn)) & AL
_ov = dil(HEADA[..., 3] > 128, 3) & SW_FRINGE
HEADA[..., :3][_ov] = RA[..., :3][_ov]; HEADA[..., 3][_ov] = RA[..., 3][_ov]
o_head = save_crop(HEADA, 'headArt')
# 몸통: 다각형 − 머리 안쪽 − 팔·칼 → 뺀 자리 = 시트 상체(팔·어깨 보호대 없는 가슴)를 두 금장식 닮음으로 원화 자리에 깐 것 + 못 덮는 곳은 둘레 검은 옷색 inpaint
_hin = ero(mk['head'] & AL, 4)
_tor = mk['torso'] & ~_hin & AL
_hole = _tor & (ARMS | SWin)
_rgb = np.ascontiguousarray(RA[..., :3].copy()); _rgb[~AL] = (40, 38, 42)
_inp = cv2.inpaint(_rgb, (_hole.astype(np.uint8) * 255), 6, cv2.INPAINT_TELEA)
_inner = ero((RA[..., 3] > 200) & mk['torso'], 2)
TORSOA = RA.copy(); TORSOA[..., :3][_hole] = _inp[_hole]; TORSOA[..., 3] = np.where(_tor, np.where(_hole & _inner, 255, RA[..., 3]), 0)
TS = simil(np.array([8.0, 21.0]), np.array([89.0, 25.0]), np.array([246.0, 334.0]), np.array([358.0, 338.0]))   # 시트 상체 두 어깨 끝(둥근 소매 자리) → 원화 가까운·먼 어깨
_st, _ = desp(np.array(img(os.path.join(PC, 'torso.png'))))
_sw = cv2.warpAffine(_st, TS.astype(np.float32), (512, 512), flags=cv2.INTER_LANCZOS4)
_use = _hole & (_sw[..., 3] > 200); TORSOA[..., :3][_use] = _sw[..., :3][_use]
print('  torso fill px', int(_hole.sum()), 'from sheet torso', int(_use.sum()), 'sheet scale', round(float(np.hypot(*TS[:, 0])), 3))
_red = _hole & ~_use
SHIRT = np.array([226, 214, 190], np.uint8)   # 메우는 천 색 = 크림 상의
_src = np.ascontiguousarray(TORSOA[..., :3].copy()); _src[dil(_red, 8) & ~_red & ~_use & (_src.max(2) < 90)] = SHIRT   # 둘레 어두운 외곽선·장갑 색이 번지지 않게
TORSOA[..., :3][_red] = cv2.inpaint(_src, _red.astype(np.uint8) * 255, 5, cv2.INPAINT_TELEA)[_red]
_out = _red & ~(_sw[..., 3] > 40); TORSOA[..., 3][_out] = 0   # 23: 시트 상체 밖(팔·주먹 뒤라 원화에도 없는 곳)은 메우지 않고 비움 — 메우면 회색·검은 얼룩(가까운 어깨 왼쪽)
print('  torso: outside sheet torso → transparent px', int(_out.sum()))
_A = TORSOA[..., 3] > 128; _d = ndimage.distance_transform_edt(_A); _cutE = _A & dil(_hole, 1) & (_d <= 2.6)
_w = np.clip(2.8 - _d, 0, 1)[_cutE][:, None]; OUTL = np.array([30, 28, 30], np.float32)
TORSOA[..., :3][_cutE] = (TORSOA[..., :3][_cutE] * (1 - _w) + OUTL * _w).astype(np.uint8)
print('  torso: inpaint-only px', int(_red.sum()), 'cut-edge outline px', int(_cutE.sum()))
o_torso = save_crop(TORSOA, 'torsoArt', sl=5)
o_hips = crop(mk['hips'] & AL, 'hipsArt', sl=3)
o_nUp = crop(A_nearUp, 'nUpArt'); o_nF = crop(A_nearFore, 'nForeArt', keep=True); o_fF = crop(A_farFore, 'fForeArt'); o_fUp = crop(A_farUp, 'fUpArt'); o_pd = crop(A_pd, 'pauldronArt')
o_lg = {n: crop(mk[n] & AL, n + 'Art') for n in ['thighN', 'thighF', 'shinN', 'shinF', 'bootN', 'bootF']}
# ---------------- 칼 그림 최종: 원화 칼(보이는 곳) + 시트 손잡이(주먹에 가린 곳) — 2배 해상도 ----------------
K2 = 2; M2 = MW.copy(); M2[:, :2] = MW[:, :2] / K2
_artW = cv2.warpAffine(RA, M2.astype(np.float32), (CW * K2, CH * K2), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderValue=(0, 0, 0, 0))
_mW = cv2.warpAffine(SWART.astype(np.float32), M2.astype(np.float32), (CW * K2, CH * K2), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
_sh2 = cv2.resize(swA, (CW * K2, CH * K2), interpolation=cv2.INTER_LANCZOS4)
_aA = _artW[..., 3:].astype(np.float32) / 255 * _mW[..., None]; _aS = _sh2[..., 3:].astype(np.float32) / 255 * (1 - _mW[..., None])
_a = np.clip(_aA + _aS, 0, 1)
swF = np.zeros_like(_sh2); swF[..., :3] = np.clip((_artW[..., :3] * _aA + _sh2[..., :3] * _aS) / np.maximum(_a, 1e-4), 0, 255).astype(np.uint8); swF[..., 3] = (_a[..., 0] * 255).astype(np.uint8)
Image.fromarray(swF).save(os.path.join(W, 'sword.png'))
print('  sword: art px', int(SWART.sum()), 'fringe px', int(SW_FRINGE.sum()))
COVER[:] = np.maximum(COVER, (SWART * 255).astype(np.uint8))
COVER[:] = np.maximum(COVER, cv2.warpAffine(swA[..., 3], MW.astype(np.float32), (512, 512), flags=cv2.INTER_LINEAR))

# ---------------- 부품 표 ----------------
L2 = lambda p: [round(float(p[0]) * 2 - O[0] * 2, 1), round(float(p[1]) * 2 - O[1] * 2, 1)]
pc = lambda p, o: [round(float(p[0] - o[0]), 1), round(float(p[1] - o[1]), 1)]
r1 = lambda p: [round(float(p[0]), 1), round(float(p[1]), 1)]
def_parts = {}
def part(name, src, pivot, scale=2.0, **kw):
    shutil.copy(src, os.path.join(OUT, 'parts', name + '.png')); def_parts[name] = dict(src=f'parts/{name}.png', pivot=pivot, scale=scale, **kw)
part('head', os.path.join(W, 'headArt.png'), pc(NECK, o_head))
part('torso', os.path.join(W, 'torsoArt.png'), pc(HIP, o_torso))
part('hips', os.path.join(W, 'hipsArt.png'), pc(HIP, o_hips))
part('pauldron', os.path.join(W, 'pauldronArt.png'), pc(SH_F, o_pd))
SD = [float(U[0]), float(U[1])]
part('armF', os.path.join(W, 'nUpArt.png'), pc(SH_N, o_nUp), elbow=pc(EL_N, o_nUp))
part('foreF', os.path.join(W, 'nForeArt.png'), pc(EL_N, o_nF), elbow=pc(EL_N, o_nF), grip=pc(G_U, o_nF), wrist=pc(G_U, o_nF), shaftDir=SD)
part('armU', os.path.join(W, 'fUpArt.png'), pc(SH_F, o_fUp), elbow=pc(EL_F, o_fUp))
# 먼 쥔 팔 = 주먹(armL, 손잡이에 붙음) + 팔뚝(armLf, 손목 마디에서 돎 — 엔진 wristArm). 손목 점 WR_F = 장갑 끝(아래 주먹 오른쪽, 흰 팔뚝 판이 들어오는 곳)
WR_F = P_('WR_F'); _fa = np.array(Image.open(os.path.join(W, 'fForeArt.png'))).astype(np.float32); _wi = WR_F - o_fF; _ei = EL_F - o_fF
_ax = (_ei - _wi) / np.linalg.norm(_ei - _wi); _yy, _xx = np.mgrid[0:_fa.shape[0], 0:_fa.shape[1]]; _t = (_xx - _wi[0]) * _ax[0] + (_yy - _wi[1]) * _ax[1]
_fist = _fa.copy(); _fist[..., 3] *= np.clip((4 - _t) / 2, 0, 1); _fore = _fa.copy(); _fore[..., 3] *= np.clip((_t + 6) / 2, 0, 1) * np.clip((np.hypot(_xx - _wi[0], _yy - _wi[1]) - 2) / 2 + (_t > 0), 0, 1)
Image.fromarray(_fist.astype(np.uint8)).save(os.path.join(W, 'fFistArt.png')); Image.fromarray(_fore.astype(np.uint8)).save(os.path.join(W, 'fForeOnly.png'))
part('armL', os.path.join(W, 'fFistArt.png'), pc(EL_F, o_fF), elbow=pc(WR_F, o_fF), grip=pc(G_L, o_fF), wrist=pc(G_L, o_fF), shaftDir=SD, fore='armLf', foreBone='armLf', foreDir=[round(float(_ax[0]), 5), round(float(_ax[1]), 5)])
part('armLf', os.path.join(W, 'fForeOnly.png'), pc(WR_F, o_fF), elbow=pc(EL_F, o_fF))
# 칼 = 날+날밑(weapon) · 손잡이·폼멜(weaponH, weapon 의 자식 = 늘 같은 자리) 두 그림. 칼 크기 그대로(DHL 10-19 09:12 무조건)
_wf = np.array(Image.open(os.path.join(W, 'sword.png'))); _wid = (_wf[..., 3] > 128).sum(1); _piv = int(SW_PIV[1] * K2)
GROW = int(max(r for r in range(_piv - 140, _piv) if _wid[r] > 100)) + 1   # 날밑 아래 끝 다음 줄(2배 그림)
_wb = _wf.copy(); _wb[GROW:, :, 3] = 0; _wh = _wf.copy(); _wh[:GROW - 10, :, 3] = 0
Image.fromarray(_wb).save(os.path.join(W, 'swordBlade.png')); Image.fromarray(_wh).save(os.path.join(W, 'swordHandle.png'))
print('  sword split row', GROW, 'grip→guard', round(float(_piv - GROW) * SMS, 1), 'part scale', round(2.0 * SMS / K2, 4))
part('weapon', os.path.join(W, 'swordBlade.png'), r1(SW_PIV * K2), scale=round(2.0 * SMS / K2, 4),   # 칼 그림 px = 시트 칼 px/K2 → 원화 SMS/K2 px → 리그 ×2
      tip=r1(SW_TIP * K2), tips=[[round(SW_TIP[0] * K2 - 16, 1), round(SW_TIP[1] * K2 + 20, 1)], [round(SW_TIP[0] * K2 + 16, 1), round(SW_TIP[1] * K2 + 20, 1)]], guard=r1(SW_GRD * K2), pommel=r1(SW_POM * K2))
part('weaponH', os.path.join(W, 'swordHandle.png'), r1(SW_PIV * K2), scale=round(2.0 * SMS / K2, 4))
# ---------------- 표정·깜빡임 (faces13.py) ----------------
exec(open(os.path.join(HERE, 'faces23.py'), encoding='utf-8').read())
for n in FACE_N + BLINK_N: part(f'face_{n}', os.path.join(W, f'face_{n}.png'), def_parts['head']['pivot'])
# ---------------- 뼈 ----------------
ang = lambda v: math.atan2(v[1], v[0])
bones = [dict(name='root', parent=None, pos=[0, 0]), dict(name='hip', parent='root', pos=L2(HIP))]
def bone(name, parent, at, parent_at, part_=None, rot=0.0):
    b = dict(name=name, parent=parent, pos=[round(float(at[0] - parent_at[0]) * 2, 1), round(float(at[1] - parent_at[1]) * 2, 1)])
    if rot: b['rot'] = round(rot, 4)
    if part_: b['part'] = part_
    bones.append(b)
bone('hips', 'hip', HIP, HIP, 'hips'); bone('torso', 'hip', HIP, HIP, 'torso'); bone('head', 'torso', NECK, HIP, 'head')
bone('armF', 'torso', SH_N, HIP, 'armF'); bone('foreF', 'armF', EL_N, SH_N, 'foreF'); bone('fistF', 'foreF', G_U, EL_N)
bones.append(dict(name='weapon', parent='fistF', pos=[0, 0], rot=round(ang(U) + math.pi / 2, 4), part='weapon'))
bones.append(dict(name='weaponH', parent='weapon', pos=[0, 0], part='weaponH'))
bone('armU', 'torso', SH_F, HIP, 'armU'); bone('armL', 'armU', EL_F, SH_F, 'armL'); bone('fistN', 'armL', G_L, EL_F); bone('armLf', 'armU', EL_F, SH_F, 'armLf')
bone('pauldron', 'torso', SH_F, HIP, 'pauldron')
for n in ['cape', 'scarf', 'pouch', 'skirt', 'skirtB', 'pauldronF']: bones.append(dict(name=n, parent='torso', pos=[0, -200]))   # 그림 없는 뼈: 엔진이 이름으로 찾음
# ---------------- 다리 — 서 있을 때 = 원화 다리(오림), 달릴 때 = 조각 시트 곧은 다리 ----------------
LGJ = JT['legs']; LEG_HY = HIP[1] + LGJ['hipY_off']
LJ = {sd: {k: np.array([LGJ[sd][k][0], LEG_HY if k == 'h' else LGJ[sd][k][1]], float) for k in ('h', 'k', 'a')} for sd in ('near', 'far')}
for n in o_lg: shutil.copy(os.path.join(W, n + 'Art.png'), os.path.join(OUT, 'parts', n + '.png')); def_parts[n] = dict(src=f'parts/{n}.png', pivot=[0, 0], scale=1.0)
for _sn, _bn in [('shinN', 'bootN'), ('shinF', 'bootF')]:   # 정강이 조각에서 부츠 윗선 + 3px 아래는 지움(부츠가 그 자리를 그림)
    _s = np.array(Image.open(os.path.join(OUT, 'parts', _sn + '.png'))); _b = np.array(Image.open(os.path.join(OUT, 'parts', _bn + '.png')))[..., 3] > 128
    _so, _bo = o_lg[_sn].astype(int), o_lg[_bn].astype(int)
    for _x in range(_s.shape[1]):
        _gx = _x + _so[0] - _bo[0]
        if 0 <= _gx < _b.shape[1] and _b[:, _gx].any():
            _top = int(np.nonzero(_b[:, _gx])[0].min()) + _bo[1] - _so[1]; _s[max(0, _top + 3):, _x, 3] = 0
    Image.fromarray(_s).save(os.path.join(OUT, 'parts', _sn + '.png'))
def sole(n, ank):   # 부츠 그림 바닥 점(발목 기준): 맨 아래 줄 양 끝 + 그 위 4px 양 끝 — 밑창을 (O − 밑창)만큼 옮겨 발목이 원화 자리에(대기 = 원화)
    a = np.array(Image.open(os.path.join(W, n + 'Art.png')))[..., 3] > 128; o = o_lg[n]; ys = np.nonzero(a.any(1))[0]; yb = ys.max(); out = []; dy = O[1] - (yb + o[1])
    for y in (yb - 4, yb):
        xs = np.nonzero(a[y])[0]; out += [[round(float(xs.min() + o[0] - ank[0]), 1), round(float(y + o[1] - ank[1] + dy), 1)], [round(float(xs.max() + o[0] - ank[0]), 1), round(float(y + o[1] - ank[1] + dy), 1)]]
    print('  stand sole', n, 'bottom', int(yb + o[1]), 'dy', dy)
    return out
for n, sd in [('bootN', 'near'), ('bootF', 'far')]: def_parts[n].update(pivot=pc(LJ[sd]['a'], o_lg[n]), scale=2.0)
seg = lambda n, sd, p0, p1: {'part': n, 'a': pc(LJ[sd][p0], o_lg[n]), 'b': pc(LJ[sd][p1], o_lg[n]), 'w': 1.0}
ln = lambda sd, p0, p1: round(float(np.linalg.norm(LJ[sd][p1] - LJ[sd][p0])) * 2, 1)
# 달리기 다리 = 조각 시트 다리(허벅지·무릎 보호대·정강이·부츠). 시트 다리 ≈ 원화 0.95~1.0배(허벅지 폭 36 = 원화 36) → 시트 px 당 1.9 리그(조금 날씬하게)

def sheet_pts(n, top, bot):
    a = np.array(Image.open(os.path.join(PC, n + '.png')))[..., 3] > 128; H = a.shape[0]
    ty, tx = np.nonzero(a[:top]); by, bx = np.nonzero(a[H - bot:])
    return [round(float(tx.mean()), 1), round(float(ty.mean()), 1)], [round(float(bx.mean()), 1), round(float(by.mean() + H - bot), 1)]
TH_R, SH_R = 100.0, 64.0   # 달리기 허벅지·정강이 길이(리그) — 원화 가까운 117·63, 먼 92·61(평균 104·62, 합 166) → 무릎 보호대가 앞자락 밑단에 걸쳐 보이게
# 달리기 다리 굵기 = 원화 서 있는 다리 굵기 × LEG_T (13 v1.1: DHL '달리는 다리 너무 얇음, 살짝만 두껍게' 뒤 받아들인 굵기로 맞춘 비율 — 23 은 처음부터 원화에서 잼)
#  13 v1.1 에 맞춰 봄(이 식으로 13 을 다시 재면): 허벅지 0.80 · 정강이 0.70 · 부츠 0.91 → 13 v1.1 굵기(72·70 / 54·51 · 부츠 2.05)와 ±5%
#  가까운·먼 쪽은 같은 배율(시트가 그린 앞뒤 굵기 차이 그대로) — 쪽마다 원화에 맞추면 원화 조각에 섞인 무릎 보호대·부츠 목 때문에 한쪽만 굵어짐
LEG_T = {'thigh': 0.80, 'shin': 0.70, 'boot': 0.91}
def _wid(mask, a, b, f0=.1, f1=.9):
    """mask(조각 알파) 의 a→b 축에 수직인 폭 중앙값(같은 px)"""
    a, b = np.array(a, float), np.array(b, float); ax = b - a; L = np.linalg.norm(ax); u = ax / L; n_ = np.array([-u[1], u[0]])
    ys, xs = np.nonzero(mask); P = np.stack([xs + .5, ys + .5], 1) - a; t = P @ u; s_ = P @ n_; out = []
    for f in np.linspace(f0, f1, 17):   # 다각형이 뼈보다 짧으면(23 정강이 = 무릎 보호대 밑 감개만) 조각이 있는 줄만
        sel = np.abs(t - f * L) < 1.0
        if sel.sum() > 3: out.append(s_[sel].max() - s_[sel].min())
    return float(np.median(out))
RWK = {}   # 조각마다 가로 배율(리그/시트 px)
for _ty, _pp in [('thigh', ('h', 'k')), ('shin', ('k', 'a'))]:
    _wa = np.mean([_wid(mk[_ty + _s] & AL, LJ[_sd][_pp[0]], LJ[_sd][_pp[1]]) * 2 for _s, _sd in (('N', 'near'), ('F', 'far'))])   # 원화 굵기(리그 px) 두 쪽 평균
    _ws = np.mean([_wid(np.array(Image.open(os.path.join(PC, _ty + _s + '.png')))[..., 3] > 128, *sheet_pts(_ty + _s, 6, 6)) for _s in 'NF'])   # 시트 굵기(시트 px) 두 쪽 평균
    for _s in 'NF': RWK[_ty + _s] = round(LEG_T[_ty] * _wa / _ws, 3)
    print('  run leg', _ty, 'art w', round(_wa, 1), 'sheet w', round(_ws, 1), '→ k', RWK[_ty + 'N'], '(run w', round(RWK[_ty + 'N'] * _ws, 1), ')')
_bA = np.array(Image.open(os.path.join(W, 'bootFArt.png')))[..., 3] > 128; _bS = np.array(Image.open(os.path.join(PC, 'bootF.png')))[..., 3] > 128
RB = round(LEG_T['boot'] * 2 * _bA.any(0).sum() / _bS.any(0).sum(), 3)   # 부츠: 원화 먼 부츠 가로 × LEG_T
RKN = round(RWK['thighN'] * 0.84, 3)   # 무릎 보호대: 13 v1.1 비율(무릎 1.95 / 허벅지 2.32)
print('  run boot k', RB, 'knee k', RKN)
rseg = {}
for n in ['thighN', 'thighF', 'shinN', 'shinF']:
    a_, b_ = sheet_pts(n, 6, 6); il = math.hypot(b_[0] - a_[0], b_[1] - a_[1]); wl = TH_R if n.startswith('thigh') else SH_R
    sheet_copy(n, os.path.join(OUT, 'parts', 'r' + n + '.png')); def_parts['r' + n] = dict(src=f'parts/r{n}.png', pivot=[0, 0], scale=1.0)
    rseg[n] = {'part': 'r' + n, 'a': a_, 'b': b_, 'w': round(RWK[n] * il / wl, 3)}
for n in ['kneeN', 'kneeF']:
    a = np.array(Image.open(os.path.join(PC, n + '.png'))); sheet_copy(n, os.path.join(OUT, 'parts', 'r' + n + '.png'))
    def_parts['r' + n] = dict(src=f'parts/r{n}.png', pivot=[a.shape[1] / 2, a.shape[0] / 2], scale=RKN)
sheet_copy('bootF', os.path.join(OUT, 'parts', 'rboot.png'))   # 발끝 오른쪽(앞) 부츠
_rb = np.array(Image.open(os.path.join(PC, 'bootF.png')))[..., 3] > 128; _ty = int(np.nonzero(_rb.any(1))[0].min()); _tx = np.nonzero(_rb[_ty + 2])[0]
RBA = (round(float(_tx.min() + _tx.max()) / 2, 1), float(_ty + 4))   # 부츠 목 위 끝 가운데 조금 아래 = 발목
def_parts['rboot'] = dict(src='parts/rboot.png', pivot=list(RBA), scale=RB)
def sole_sheet(n, ank):
    a = np.array(Image.open(os.path.join(PC, n + '.png')))[..., 3] > 128; ys = np.nonzero(a.any(1))[0]; yb = ys.max(); out = []
    for y in (yb - 6, yb - 3, yb):
        xs = np.nonzero(a[y])[0]; out += [[round(float(xs.min() - ank[0]), 1), round(float(y - ank[1]), 1)], [round(float(xs.max() - ank[0]), 1), round(float(y - ank[1]), 1)]]
    return out
stand = lambda sd, bn: {'fade': [0.05, 0.1], 'boot': {'part': bn, 'sole': sole(bn, LJ[sd]['a'])}, 'thighImg': seg('thigh' + sd[0].upper(), sd, 'h', 'k'), 'shinImg': seg('shin' + sd[0].upper(), sd, 'k', 'a'), 'kneeImg': None}
legs = {'hip': [0, round(float(LGJ['hipY_off']) * 2, 1)], 'thigh': TH_R, 'shin': SH_R,
        'thighImg': rseg['thighF'], 'shinImg': rseg['shinF'], 'thighFirst': False,
        'boot': {'part': 'rboot', 'sole': sole_sheet('bootF', RBA), 'ankleRange': [-0.45, 0.75], 'runLock': 0.0},   # runLock 0(엔진 opt-in): 달리기 다리 그림(시트 정강이·부츠)이면 발목 고정 — 부츠가 정강이와 한 줄, 발 구름 없음. DHL 10-21 12:35 '뛸 때 발이 2조각으로 나눠지면 이상 · 발 구르는 것 없이 뛰어도 좋으니 조각을 쪼개지 말아줘요'(서 있는 원화 다리 그림은 원래 범위)
        'near': {'x': round(float(LJ['near']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['near']['h'][0] - HIP[0]) * 2, 1), 'runX': -10, 'shade': 0, 'kneeOut': 1,
                 'thigh': ln('near', 'h', 'k'), 'shin': ln('near', 'k', 'a'), 'thighImg': rseg['thighN'], 'shinImg': rseg['shinN'],
                 'kneeImg': {'part': 'rkneeN', 'mix': 0.5}, 'stand': stand('near', 'bootN')},
        'far': {'x': round(float(LJ['far']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['far']['h'][0] - HIP[0]) * 2, 1), 'runX': 10, 'shade': 0,
                'thigh': ln('far', 'h', 'k'), 'shin': ln('far', 'k', 'a'), 'thighImg': rseg['thighF'], 'shinImg': rseg['shinF'],
                'kneeImg': {'part': 'rkneeF', 'mix': 0.5}, 'stand': stand('far', 'bootF')}}
print('  legs near', legs['near']['thigh'], legs['near']['shin'], 'far', legs['far']['thigh'], legs['far']['shin'], 'run w', {k: v['w'] for k, v in rseg.items()}, 'rboot', RBA)
# ---------------- 목도리 꼬리 두 갈래(streamers — 21 스카이 알론소와 같은 엔진 opt-in) · 포니테일(pony — 2 둘시네) ----------------
#  꼬리: 그림 오른쪽 끝(뿌리, 목 고리 뒤)이 pivot, 왼쪽(뒤)으로 날림. 서 있어도 바람(wind), 달릴수록 펴짐(droop·sag 줄어듦), 몸이 오르내리면 늦게 따라옴(lag)
#  ★ 뿌리 자리 TAIL_ROOT·PONY_ROOT 와 시트 → 원화 배율은 새 원화·reg23 에서. 원화에서 오린 꼬리가 시트 꼬리보다 원화와 딱 맞으면 원화 쪽(26 스카이 땋은 수염 교훈)
TJ = JT['tail']
# 목도리 꼬리 두 갈래 = 원화 꼬리를 갈래 사이 선으로 나눈 것(보이는 곳) + 팔·주먹 뒤에 숨은 뿌리 쪽 = 시트 꼬리(닮음)로 이음 → 공격 때 주먹이 비켜도 목 뒤까지 이어짐
TSL = {'A': simil(np.array(TJ['A']['p1S'], float), np.array(TJ['A']['p2S'], float), np.array(TJ['A']['p1A'], float), np.array(TJ['A']['p2A'], float))}
_R = TSL['A'][:, :2]; TSL['B'] = np.c_[_R, np.array(TJ['B']['p1A'], float) - _R @ np.array(TJ['B']['p1S'], float)]   # 아래 꼬리 = 위 꼬리와 같은 배율·회전, 끝점 맞춤
STREAMERS = []
_XX = np.mgrid[0:512, 0:512][1]
for _k, _n, _poly in [('A', 'tailA', 'tail'), ('B', 'tailB', 'tailB')]:
    _ts, _ = desp(np.array(img(os.path.join(PC, _n + '.png')))); _tw = cv2.warpAffine(_ts, TSL[_k].astype(np.float32), (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
    _other = pmask('tailB' if _k == 'A' else 'tail'); _tA = (pmask(_poly) | (dil(pmask(_poly), 2) & (mk['tail'] | pmask('tailB')) if _k == 'A' else pmask(_poly))) & AL & ~ARMS & ~SWin   # 위 꼬리는 갈래 사이 선을 2px 넘어 아래 꼬리 위에 겹침(따로 움직일 때 틈 없게)
    TAILA = RA.copy(); TAILA[..., 3] = np.where(_tA, RA[..., 3], 0)
    _ext = (_tw[..., 3] > 128) & ~dil(_tA, 1) & (_XX > 205) & (~_other if _k == 'A' else True) & (np.mgrid[0:512, 0:512][0] >= 299)   # 숨은 곳(팔·주먹 뒤 + 뿌리 쪽)만, 다른 갈래 자리는 안 덮음, 몸통 위 끝 아래만 — 위로 나오면 칼이 비킬 때 머리 옆에 곧은 띠
    TAILA[_ext] = _tw[_ext]; print('  tail', _n, 'art px', int(_tA.sum()), 'sheet root px', int(_ext.sum()), 'sheet→art', round(float(np.hypot(*TSL[_k][:, 0])), 3))
    _o = save_crop(TAILA, _n + 'Art')
    _ta = np.array(Image.open(os.path.join(W, _n + 'Art.png')))[..., 3] > 40; _xs = np.where(_ta.any(0))[0]; _x1 = int(_xs.max()); _ys = np.where(_ta[:, _x1 - 12:_x1 + 1].any(1))[0]
    _root = np.array([_o[0] + _x1 - 6, _o[1] + (_ys.min() + _ys.max()) / 2])   # 그림 오른쪽 끝 = 뿌리(엔진 streamers)
    part(_n, os.path.join(W, _n + 'Art.png'), pc(_root, _o), mesh={'cols': 8, 'rows': 2})
    bone(_n, 'torso', _root, HIP, _n)
    STREAMERS.append({'bone': _n, 'part': _n, 'len': round(float(_x1 - _xs.min()) * 2, 1), 'amp': 6 if _k == 'A' else 8, 'freq': 6.5 if _k == 'A' else 5.9, 'phase': 0 if _k == 'A' else 1.9,
                      'droop': 0.0, 'sag': 4, 'wind': 0.6 if _k == 'A' else 0.55, 'lag': 0.35 if _k == 'A' else 0.45})   # 원화 꼬리 그대로라 쉴 때 처짐 0(대기 = 원화), 두 갈래 박자 다르게(21 스카이 알론소)
# 포니테일 = 원화에서 칼날 왼쪽에 보이는 머리 다발(다각형 − 칼), 뿌리 = 크림 매듭(joints pony.root) — 칼 뒤 매듭은 머리 메움(시트 머리)이 그림
PONY_ROOT = np.array(JT['pony']['root'], float)
_pv = mk['pony'] & AL & ~SWin; PONYA = RA.copy(); PONYA[..., 3] = np.where(_pv, RA[..., 3], 0)   # 포니테일 = 원화에서 보이는 머리 다발 + 매듭(뿌리는 머리 쪽 뒷머리가 덮음)
o_pony = save_crop(PONYA, 'ponyArt')
part('pony', os.path.join(W, 'ponyArt.png'), pc(PONY_ROOT, o_pony))
bone('pony', 'head', PONY_ROOT, NECK, 'pony')
# ---------------- 그리는 순서 (뒤 → 앞) ----------------
# 원화: 다리 < 몸통 < 허리띠·앞판 < 먼 윗팔 < 먼 어깨 보호대 < 가까운 윗팔 < 머리 < 칼(머리카락 앞) < 위 주먹·가까운 팔뚝 < 아래 주먹·먼 팔뚝(가슴 앞)
draw = ['tailB', 'tailA', 'pony', 'legFar', 'legNear', 'torso', 'hips', 'armU', 'pauldron', 'armF', 'head', 'weaponH', 'weapon', 'armLf', 'foreF', 'armL']   # ★ 꼬리·포니테일 맨 뒤(칼 늘 머리 앞), 주먹 둘이 맨 앞 — 가까운 어깨갑(padN) 자리는 조립 때
GX, GY = (G_U - HIP) * 2
guard = {'gx': round(float(GX), 1), 'gy': round(float(GY), 1), 'sa': round(ang(U), 4), 'sN': 0, 'sF': round(S_LOW, 1),
         'nPiece': 'foreF', 'fPiece': 'armL', 'nUpper': 'armF', 'fUpper': 'armU', 'order': 'drawA', 'frame': 'torso'}
_top = int(np.nonzero((mk['head'] & AL).any(1))[0].min())
rig = {'name': 'sancho-sky', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': def_parts, 'bones': bones, 'legs': legs, 'draw': draw, 'drawA': draw, 'hidden': [], 'faces': FACES,
       'metrics': {'bodyHeight': round(2 * (O[1] - _top), 1), 'note': f'rig units; 머리카락 끝(원화 y{_top})~발바닥({int(O[1])}) ×2, 무기 제외'},
       'armPhase': 0.5, 'gait': {'heelKick': 0.5, 'kneeLift': 0.35, 'strideBase': 80, 'strideK': 0.2, 'swingReach': -0.05, 'swingAng': 0.15, 'landAng': 0, 'hipBase': -24, 'bob': 10, 'lean': 0.1, 'headRun': 0.04},
       'carrySwing': 0.25, 'wristRange': 0.2,
       'swordGrip': {'tipDepth': 6, 'near': {'upper': 'armF', 'carry': 'foreF'}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': round(S_LOW, 1)}, 'guard': guard},
       'ui': {'attack': None, 'touch': 'hop', 'trail': 'up'},   # trail up = 게임 공격 트레일 아래 → 위(올려베기)
       'gameRef': {'refOrigin': [236.4, float(O[1])], 'refScale': 2.0, 'refLift': 0, 'note': '게임 그림 char_0023.png(512) 발 높이 = 원화. x 236.4 = 도감 칸(fitArt 중심 248.4, index.html measureBox 와 같은 계산 — 칼이 왼쪽으로 커서 그림 중심이 몸보다 왼쪽)에서 골반(hip x 297)이 가운데 (3·13 산초와 같은 규칙)'},
       'note': '23 스카이아크 산초 (2026-10-19, 3 러스트 산초 v3.1 · 13 네온 산초 v1.1 구조). 두 손으로 큰 칼을 쥠(swordGrip.guard, 칼날 11시), 손·팔·머리·어깨갑·다리는 원화를 그대로 오려 씀. 목도리 꼬리 두 갈래(streamers)·포니테일(pony).'}
rig['blinkFaces'] = BLINK
if any(S_.get('len') for S_ in STREAMERS): rig['streamers'] = [S_ for S_ in STREAMERS if S_.get('len')]
if 'pony' in def_parts: rig['ponySway'] = 0.6   # 2 둘시네 값에서 시작
exec(open(os.path.join(HERE, 'attack_sky.py'), encoding='utf-8').read())   # 올려베기 (attack_keys.json — tools/gen_keys.py)
_gap = (RA[..., 3] > 200) & (COVER < 200); _gap[480:] = False
print('  gaps (원화 불투명인데 조각이 안 덮음):', int(_gap.sum()), 'px')
_v = RA.copy(); _v[_gap] = (255, 0, 255, 255); Image.fromarray(_v).save(os.path.join(W, '_gaps.png'))
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(os.path.join(OUT, 'parts'))): _h.update(fn.encode()); _h.update(open(os.path.join(OUT, 'parts', fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_sky.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['sancho-sky']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(def_parts), 'parts, version', rig['version'], 'guard', guard)
