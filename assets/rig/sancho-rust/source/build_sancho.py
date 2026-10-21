"""3 러스트 산초 리그 조립 (2026-10-19, 11 네온 알론소 v5.4 구조 기준 — 수치·조각·손·순서는 전부 이 캐릭터에서 새로 잼).
입력: ref512.png(손 고친 원화 = 게임 char_0003) · pieces/(조각 시트 1, cut3.py) · polys.json(원화에서 오릴 다각형) · geom.json(시트 조각 → 원화)
출력: ../rig.json, ../rig.def.js, ../parts/*.png
실행: cd source && python3 -I build_sancho.py
원칙(DHL): 대기 자세 = 원화. 두 손은 처음부터 끝까지 칼을 쥠(swordGrip.guard, frame torso). 손은 원화 손 그대로(오려 씀). 손 뒤집기 금지.
손 순서(원화): 날밑 쪽 위 주먹 = 오른손 = 가까운 팔(화면 왼쪽, 녹색 소매) · 폼멜 쪽 아래 주먹 = 왼손 = 먼 팔(팔뚝이 가슴 앞을 지나 화면 오른쪽 먼 어깨, 쇠 어깨갑)
엔진 이름: near(armF→foreF, 칼 쥔 점 G) = 가까운 팔(위 주먹) · far(armU→armL, G + U·sF) = 먼 팔(아래 주먹) + 어깨갑(pauldron)  ← 11 과 반대(11 은 위 주먹이 먼 팔)
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
POLY = json.load(open(os.path.join(HERE, 'polys.json'))); GEO = json.load(open(os.path.join(HERE, 'geom.json')))
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
def save_crop(a, name, sl=0):
    """a(512×512 RGBA, 원화 좌표) → work/name.png, 반환 = 칸 왼쪽 위(원화 px)"""
    a = islands(slivers(a, sl) if sl else a, name); COVER[:] = np.maximum(COVER, a[..., 3]); ys, xs = np.nonzero(a[..., 3] > 0)
    x0, y0 = xs.min() - 2, ys.min() - 2; Image.fromarray(a[y0:ys.max() + 3, x0:xs.max() + 3]).save(os.path.join(W, name + '.png')); return np.array([x0, y0], float)
def crop(mask, name, grow=0, cut=None, src=None, sl=0):
    if grow: mask = dil(mask, grow)
    if cut is not None: mask = mask & ~cut
    a = (RA if src is None else src).copy(); a[..., 3] = np.where(mask, a[..., 3], 0); return save_crop(a, name, sl)

def sheet_copy(n, dst):
    """시트 조각을 parts 로 — 자홍 배경 번짐(외곽선이 보라색, 10-19 달리기 확대) 지움: min(R,B) − G 만큼 R·B 를 뺌(녹·갈·회색은 그대로)"""
    a = np.array(img(os.path.join(PC, n + '.png'))).astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None)
    a[..., 0] -= m; a[..., 2] -= m; Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(dst)
    return int((m > 4).sum())
# ---------------- 원화 관절 (512 px) ----------------
O = np.array([279.0, 494.0])                                     # 뿌리: 두 발 가운데 땅(부츠 바닥)
HIP = np.array([283.0, 402.0]); NECK = np.array([300.0, 326.0])   # 골반(벨트 버클) · 목(턱 끝 밑 = 머리 회전 중심)
SH_N, EL_N = np.array([229.0, 323.0]), np.array([212.0, 352.0])  # 가까운 팔(엔진 armF→foreF): 어깨(위 주먹 뒤, 안 보임) · 팔꿈치(녹색 소매 끝)
SH_F, EL_F = np.array([336.0, 340.0]), np.array([311.0, 366.0])  # 먼 팔(엔진 armU→armL): 어깨(어깨갑 안) · 팔꿈치(살색 팔뚝 끝, 녹색 소매 밑)
# 칼: 조각 시트 칼 = 원화 칼을 세운 것(SIFT 1.0006배, −21.4°, 덮음 0.994). 원화 손잡이는 칼날 축에서 오른쪽으로 약 9px 평행이동되어 그려져 있음
#   (측정: 손잡이 축 y290 x226 · y370 x258.5) → 칼 그림의 손잡이·폼멜을 같은 만큼 옮겨 원화 손잡이 자리에 맞춤(두 주먹이 손잡이를 쥐게)
MS = np.array(GEO['sword']['M'], float); R2 = MS[:, :2]
SHIFT = np.linalg.solve(R2, np.array([9.0, 0.0]))                 # 원화 (+9, 0) → 칼 그림 좌표 이동 ≈ (8.4, 3.3)
U = -R2 @ np.array([0.0, 1.0]); U /= np.linalg.norm(U)            # 칼끝 방향(원화) = 칼 그림 위쪽(−v)
HA = np.array([226.0, 290.0]); HB = np.array([258.5, 370.0])      # 원화 손잡이 축 두 점
on_handle = lambda y: HA + (HB - HA) * ((y - HA[1]) / (HB[1] - HA[1]))
G_U = on_handle(318.0); G_L = on_handle(347.0)                    # 쥔 점: 위 주먹(가까운 손) · 아래 주먹(먼 손)
S_LOW = -float(np.linalg.norm(G_L - G_U)) * 2                     # 아래 주먹 = 위 주먹에서 칼끝 반대로 (리그 단위, 음수)
print('  U', np.round(U, 4).tolist(), 'handle dir', np.round((HA - HB) / np.linalg.norm(HA - HB), 4).tolist(), 'G_U', np.round(G_U, 1).tolist(), 'G_L', np.round(G_L, 1).tolist(), 'S_LOW', round(S_LOW, 1))

# ---------------- 칼 그림: 시트 칼(날·날밑) + 옮긴 손잡이·폼멜 ----------------
sw0 = np.array(img(os.path.join(PC, 'sword.png'))); H0, W0 = sw0.shape[:2]; HROW = 309   # 날밑 아래 = 손잡이 첫 줄(시트 칼)
PX, PY = 12, 8; CW, CH = W0 + 2 * PX, H0 + PY
blade = np.zeros((CH, CW, 4), np.uint8); blade[:HROW, PX:PX + W0] = sw0[:HROW]
hnd = np.zeros((CH, CW, 4), np.uint8); hnd[HROW:H0, PX:PX + W0] = sw0[HROW:]
for r in range(HROW - 6, HROW): hnd[r, PX:PX + W0] = sw0[HROW]   # 손잡이 첫 줄을 위로 6줄 늘림 → 옮긴 뒤 날밑 밑 틈(3줄) 없음, 늘린 곳은 날밑 밑에 숨음
hnd = cv2.warpAffine(hnd, np.float32([[1, 0, SHIFT[0]], [0, 1, SHIFT[1]]]), (CW, CH), flags=cv2.INTER_LINEAR)
swI = Image.fromarray(hnd); swI.alpha_composite(Image.fromarray(blade)); swA = np.array(swI)   # 날밑이 손잡이 위
Image.fromarray(swA).save(os.path.join(W, 'sword.png'))
MW = MS.copy(); MW[:, 2] = MS[:, 2] - R2 @ np.array([PX, 0.0])   # 칼 그림(여백 포함) → 원화
toImg = lambda p: np.linalg.solve(R2, np.array(p, float) - MW[:, 2])
SWM = cv2.warpAffine((swA[..., 3] > 90).astype(np.uint8), MW.astype(np.float32), (512, 512), flags=cv2.INTER_NEAREST) > 0   # 칼 자리(원화)
_al = swA[..., 3] > 128; _ys = np.nonzero(_al.any(1))[0]
SW_TIP = np.array([np.nonzero(_al[_ys[0] + 3])[0].mean(), float(_ys[0])]); SW_POM = np.array([np.nonzero(_al[_ys[-1] - 3])[0].mean(), float(_ys[-1])])
SW_GRD = np.array([SW_TIP[0], HROW - 8.0]); SW_PIV = toImg(G_U)
print('  sword img', CW, CH, 'pivot', np.round(SW_PIV, 1).tolist(), 'tip', np.round(SW_TIP, 1).tolist(), 'pommel', np.round(SW_POM, 1).tolist(),
      'grip check: G_L → img', np.round(toImg(G_L), 1).tolist())

# ---------------- 원화에서 오리는 조각 ----------------
mk = {n: pmask(n) for n in ['head', 'nearUp', 'nearFore', 'farFore', 'farUp', 'pauldron', 'torso', 'hips', 'thighN', 'shinN', 'bootN', 'thighF', 'shinF', 'bootF']}
# 손·팔: 앞에 그리는 조각이 겹친 픽셀을 가짐 — 아래 주먹·먼 팔뚝(armL) > 위 주먹·가까운 팔뚝(foreF) > 가까운 소매(armF) / 어깨갑 > 먼 윗팔(armU)
#   밑 조각은 위 조각 경계 안쪽 3px 까지 가짐(겹침) — 맞닿은 잘린 가장자리가 그릴 때 반투명이 되어 회색 줄(이음매)로 보였음(10-19 대기 확대, 11 교훈 grow 와 같은 뜻)
und = lambda m, *tops: m & ~np.logical_or.reduce([ero(t, 3) for t in tops])
A_farFore = mk['farFore']; A_nearFore = und(mk['nearFore'], A_farFore); A_nearUp = und(mk['nearUp'], mk['nearFore'], A_farFore)
A_pd = und(mk['pauldron'], A_farFore); A_farUp = und(mk['farUp'], mk['pauldron'], A_farFore)
ARMS = A_farFore | A_nearFore | A_nearUp | A_pd | A_farUp
SWin = dil(SWM, 1)   # 칼 자리 + 1px — 칼 외곽선을 머리·몸통에 남기지 않음(11 교훈: 공격 때 칼이 떠나면 검은 줄)
# 머리: 다각형(머리카락·얼굴·귀, 아래 = 턱선) − 칼(칼이 머리 앞) − 주먹. 칼·주먹 뒤에 가려진 머리카락은 시트 머리(같은 얼굴 크기)로 메움 — 공격에서 칼·주먹이 떠나면 보임
A_head = mk['head'] & ~SWin & ~ARMS & AL
Mh = np.array(GEO['headSheet']['M'], np.float32)
_sh = cv2.warpAffine(np.array(img(os.path.join(PC, 'head.png'))), Mh, (512, 512), flags=cv2.INTER_LANCZOS4)
HEADA = RA.copy(); HEADA[..., 3] = np.where(A_head, RA[..., 3], 0)
_fill = (_sh[..., 3] > 128) & (SWin | ARMS) & mk['head'] & ~A_head & (RA[..., 3] > 128)   # 원화에서 가려진(불투명) 곳만 — 주먹 다각형 안 빈틈(배경)에 시트 머리카락 점이 보였음
HEADA[_fill] = _sh[_fill]; HEADA[..., 3][_fill] = 255; print('  head hair fill (behind sword/fist) px', int(_fill.sum()))
HEADA = slivers(HEADA, 3)   # 칼날 오른쪽 외곽선 띠(2~3px)는 머리에서 빠짐 → 아래 칼 둘레(SW_FRINGE)가 가져감
# 칼로 가져올 원화 곳(SWART): 칼 자리(주먹 경계 안 3px 까지 — 주먹 가장자리 밑 이음매 없게) + 다른 조각 밖 칼 둘레(외곽선 톱니) + 주먹 다각형 띠 중 칼 3px 안(손잡이 외곽선)
_armsIn = ero(mk['nearFore'] | mk['farFore'], 3)
_others = mk['torso'] | mk['hips'] | ARMS | mk['thighN'] | mk['thighF'] | mk['shinN'] | mk['shinF'] | mk['bootN'] | mk['bootF']
SW_FRINGE = dil(SWM, 9) & AL & ~_others & ~SWin & ~(HEADA[..., 3] > 128)
SWART = ((SWin & ~_armsIn) | SW_FRINGE | (dil(SWM, 3) & ARMS & ~_armsIn)) & AL
_ov = dil(HEADA[..., 3] > 128, 3) & SW_FRINGE   # 머리 가장자리가 칼 둘레 외곽선 밑으로 3px 들어감(겹침 — 이음매 없게)
HEADA[..., :3][_ov] = RA[..., :3][_ov]; HEADA[..., 3][_ov] = RA[..., 3][_ov]
o_head = save_crop(HEADA, 'headArt')
# 몸통: 다각형 − 머리 안쪽 − 팔·어깨갑·칼 → 뺀 자리는 둘레 몸통 색으로 메움(inpaint). 대기·달리기에선 팔·칼이 위(frame torso 로 같이 움직임)라 안 보임
#   머리 가장자리 4px 띠는 몸통에도 남김: 달리기에 머리가 1~3px 움직여도 턱 밑에 흰 줄(배경)이 안 보이게(11 교훈)
_hin = ero(mk['head'] & AL, 4)
_tor = mk['torso'] & ~_hin & AL
_hole = _tor & (ARMS | SWin)
_rgb = np.ascontiguousarray(RA[..., :3].copy()); _rgb[~AL] = (40, 38, 30)
_inp = cv2.inpaint(_rgb, (_hole.astype(np.uint8) * 255), 6, cv2.INPAINT_TELEA)
_inner = ero((RA[..., 3] > 200) & mk['torso'], 2)   # 메운 자리 불투명은 몸 안쪽만 — 실루엣 가장자리(어깨갑·소매 끝 반투명)에 진한 테두리가 생겼었음(10-19 대기 비교)
TORSOA = RA.copy(); TORSOA[..., :3][_hole] = _inp[_hole]; TORSOA[..., 3] = np.where(_tor, np.where(_hole & _inner, 255, RA[..., 3]), 0)
# (10-19 올려베기) 팔이 가슴에서 떠나면 메운 자리가 흐린 얼룩으로 보였음 → 메운 자리는 조각 시트 상체(팔 없는 깨끗한 가슴)를 3점 아핀으로 원화 몸통 자리에 깐 것
#   (목깃 위 끝·버클·왼쪽 가슴 끝: 시트 (50,8)(57,70)(5,30) → 원화 (296,320)(291,398)(232,340)). 시트 목 구멍(분홍)은 목 그늘색. 시트가 안 덮는 곳만 위 inpaint
TA = cv2.getAffineTransform(np.float32([[50, 8], [57, 70], [5, 30]]), np.float32([[296, 320], [291, 398], [232, 340]]))
_st = np.array(img(os.path.join(PC, 'torso.png'))).astype(np.int16); _m = np.clip(np.minimum(_st[..., 0], _st[..., 2]) - _st[..., 1], 0, None); _st[..., 0] -= _m; _st[..., 2] -= _m
_hs = cv2.cvtColor(np.clip(_st[..., :3], 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV); _pink = (_hs[..., 0] > 150) | ((_hs[..., 0] < 8) & (_hs[..., 1] > 90) & (np.arange(_st.shape[0])[:, None] < 16))
_st[..., :3][_pink] = (120, 72, 46)
_sw = cv2.warpAffine(np.clip(_st, 0, 255).astype(np.uint8), TA, (512, 512), flags=cv2.INTER_LANCZOS4)
_use = _hole & (_sw[..., 3] > 200); TORSOA[..., :3][_use] = _sw[..., :3][_use]
print('  torso fill px', int(_hole.sum()), 'from sheet torso', int(_use.sum()))
# (10-19 올려베기 v2) 시트가 못 덮는 메운 자리(가까운 어깨 위·먼 어깨 밑)는 머리카락·외곽선 색을 끌어와 갈색 얼룩이었음
#   → 둘레 원화를 셔츠 녹색으로 바꾼 뒤 inpaint(시트 셔츠에서만 색을 끌어옴). 잘린 실루엣 가장자리(팔이 덮던 곳)엔 원화 같은 외곽선 2px
_red = _hole & ~_use
_hsv = cv2.cvtColor(np.ascontiguousarray(_sw[..., :3]), cv2.COLOR_RGB2HSV); _grn = _use & (_hsv[..., 0] >= 22) & (_hsv[..., 0] <= 45) & (_hsv[..., 1] > 60)
SHIRT = np.median(TORSOA[..., :3][_grn], 0).astype(np.uint8) if _grn.sum() > 50 else np.array([92, 92, 50], np.uint8)
_src = np.ascontiguousarray(TORSOA[..., :3].copy()); _src[dil(_red, 8) & ~_red & (~_use | (_src.max(2) < 90))] = SHIRT   # 시트 셔츠 가장자리 외곽선(어두운 점)도 셔츠색으로
TORSOA[..., :3][_red] = cv2.inpaint(_src, _red.astype(np.uint8) * 255, 5, cv2.INPAINT_TELEA)[_red]
_A = TORSOA[..., 3] > 128; _d = ndimage.distance_transform_edt(_A); _cutE = _A & dil(_hole, 1) & (_d <= 2.6)
_w = np.clip(2.8 - _d, 0, 1)[_cutE][:, None]; OUTL = np.array([38, 32, 26], np.float32)
TORSOA[..., :3][_cutE] = (TORSOA[..., :3][_cutE] * (1 - _w) + OUTL * _w).astype(np.uint8)
print('  torso: shirt', SHIRT.tolist(), 'inpaint-only px', int(_red.sum()), 'cut-edge outline px', int(_cutE.sum()))
o_torso = save_crop(TORSOA, 'torsoArt', sl=5)
o_hips = crop(mk['hips'] & AL, 'hipsArt', sl=3)
o_nUp = crop(A_nearUp, 'nUpArt'); o_nF = crop(A_nearFore, 'nForeArt'); o_fF = crop(A_farFore, 'fForeArt'); o_fUp = crop(A_farUp, 'fUpArt'); o_pd = crop(A_pd, 'pauldronArt')
o_lg = {n: crop(mk[n] & AL, n + 'Art') for n in ['thighN', 'thighF', 'shinN', 'shinF', 'bootN', 'bootF']}
# ---------------- 칼 그림 최종: 원화 칼(보이는 곳) + 시트 칼(주먹에 가린 손잡이) — 2배 해상도 ----------------
#   시트 칼은 날 오른쪽 톱니 외곽선(원화 y30~135)·날밑 왼쪽 아래·손잡이 둘레 외곽선이 원화보다 좁음(틈 1,700px) → 대기 자리 = 원화 그대로가 되게 원화를 세워 씀(11 방식)
#   2배 해상도로 세움(부품 scale 1.0): 세울 때·게임에서 돌릴 때 두 번 다시 그리는 흐림을 반으로
K2 = 2; M2 = MW.copy(); M2[:, :2] = MW[:, :2] / K2                 # 칼 그림(2배) → 원화
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
# 먼 쥔 팔 = 주먹(armL, 손잡이에 붙음) + 팔뚝(armLf, 손목 마디에서 돎 — 엔진 wristArm). 손목 점 WR_F = 장갑 끝·붕대 손목 가운데(원화)
#   (10-19 올려베기) 칼이 한 바퀴 도는 동안 원화 팔뚝 각도 그대로면 손목 꺾임이 ±100° 넘어 조각을 바꿔야 했음(바꿀 때 주먹이 튐) → 팔뚝만 손목 둘레로 돌게
WR_F = np.array([275.0, 351.0]); _fa = np.array(Image.open(os.path.join(W, 'fForeArt.png'))).astype(np.float32); _wi = WR_F - o_fF; _ei = EL_F - o_fF
_ax = (_ei - _wi) / np.linalg.norm(_ei - _wi); _yy, _xx = np.mgrid[0:_fa.shape[0], 0:_fa.shape[1]]; _t = (_xx - _wi[0]) * _ax[0] + (_yy - _wi[1]) * _ax[1]
_fist = _fa.copy(); _fist[..., 3] *= np.clip((4 - _t) / 2, 0, 1); _fore = _fa.copy(); _fore[..., 3] *= np.clip((_t + 6) / 2, 0, 1) * np.clip((np.hypot(_xx - _wi[0], _yy - _wi[1]) - 2) / 2 + (_t > 0), 0, 1)
Image.fromarray(_fist.astype(np.uint8)).save(os.path.join(W, 'fFistArt.png')); Image.fromarray(_fore.astype(np.uint8)).save(os.path.join(W, 'fForeOnly.png'))
part('armL', os.path.join(W, 'fFistArt.png'), pc(EL_F, o_fF), elbow=pc(WR_F, o_fF), grip=pc(G_L, o_fF), wrist=pc(G_L, o_fF), shaftDir=SD, fore='armLf', foreBone='armLf', foreDir=[round(float(_ax[0]), 5), round(float(_ax[1]), 5)])
part('armLf', os.path.join(W, 'fForeOnly.png'), pc(WR_F, o_fF), elbow=pc(EL_F, o_fF))
# 칼 = 날+날밑(weapon) · 손잡이·폼멜(weaponH, weapon 의 자식 = 늘 같은 자리) 두 그림. (v1 groundShorten 날 줄이기는 DHL 10-19 09:12 '칼 크기 변경 없음(무조건)'으로 뺌 — 칼끝은 키로 땅 위에)
_wf = np.array(Image.open(os.path.join(W, 'sword.png'))); _wid = (_wf[..., 3] > 128).sum(1); _piv = int(SW_PIV[1] * K2)
GROW = int(max(r for r in range(_piv - 140, _piv) if _wid[r] > 100)) + 1   # 날밑 아래 끝 다음 줄(2배 그림, 날밑 폭 150 · 손잡이 40~80)
_wb = _wf.copy(); _wb[GROW:, :, 3] = 0; _wh = _wf.copy(); _wh[:GROW - 10, :, 3] = 0   # 손잡이 그림은 날밑 밑으로 10줄 겹침(먼저 그림)
Image.fromarray(_wb).save(os.path.join(W, 'swordBlade.png')); Image.fromarray(_wh).save(os.path.join(W, 'swordHandle.png'))
GUARD_D = round(float(_piv - GROW) * (2.0 / K2) / 1, 1)   # 쥔 점 → 날밑 아래 끝(리그)
print('  sword split row', GROW, 'grip→guard', GUARD_D)
part('weapon', os.path.join(W, 'swordBlade.png'), r1(SW_PIV * K2), scale=2.0 / K2, tip=r1(SW_TIP * K2), tips=[[round(SW_TIP[0] * K2 - 16, 1), round(SW_TIP[1] * K2 + 20, 1)], [round(SW_TIP[0] * K2 + 16, 1), round(SW_TIP[1] * K2 + 20, 1)]], guard=r1(SW_GRD * K2), pommel=r1(SW_POM * K2))
part('weaponH', os.path.join(W, 'swordHandle.png'), r1(SW_PIV * K2), scale=2.0 / K2)
# ---------------- 표정 (faces3.py) ----------------
exec(open(os.path.join(HERE, 'faces3.py'), encoding='utf-8').read())
for n in FACE_N: part(f'face_{n}', os.path.join(W, f'face_{n}.png'), def_parts['head']['pivot'])
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
bone('armU', 'torso', SH_F, HIP, 'armU'); bone('armL', 'armU', EL_F, SH_F, 'armL'); bone('fistN', 'armL', G_L, EL_F); bone('armLf', 'armU', EL_F, SH_F, 'armLf')   # armLf 자리는 엔진이 손목에 놓음
bone('pauldron', 'torso', SH_F, HIP, 'pauldron')
for n in ['cape', 'scarf', 'pouch', 'skirt', 'skirtB', 'pauldronF']: bones.append(dict(name=n, parent='torso', pos=[0, -200]))   # 그림 없는 뼈: 엔진이 이름으로 찾음
# ---------------- 다리 — 서 있을 때 = 원화 다리(오림), 달릴 때 = 조각 시트 곧은 다리 ----------------
# 원화 관절: 가까운 엉덩이(246,405)·무릎(216,430, 바깥=뒤로 굽음 → kneeOut)·발목(214,465) / 먼 엉덩이(312,410)·무릎(352,437)·발목(348,467)
#   엉덩이 y 는 두 쪽 같게(엔진: 골반 + legs.hip[1] = HIP.y + 5) — 쪽마다 다르면(405·410) 무릎 IK 가 원화 무릎에서 벗어나 무릎 보호대가 돌아 보였음(10-19 대기 비교)
LEG_HY = HIP[1] + 5
LJ = {'near': dict(h=np.array([246.0, LEG_HY]), k=np.array([216.0, 430]), a=np.array([214.0, 465])),
      'far': dict(h=np.array([312.0, LEG_HY]), k=np.array([352.0, 437]), a=np.array([348.0, 467]))}
for n in o_lg: shutil.copy(os.path.join(W, n + 'Art.png'), os.path.join(OUT, 'parts', n + '.png')); def_parts[n] = dict(src=f'parts/{n}.png', pivot=[0, 0], scale=1.0)
for _sn, _bn in [('shinN', 'bootN'), ('shinF', 'bootF')]:   # 정강이 조각에서 부츠 윗선 + 3px 아래는 지움(부츠가 그 자리를 그림) — 무릎이 굽으면 부츠 목이 두 겹으로 보였음(11 교훈)
    _s = np.array(Image.open(os.path.join(OUT, 'parts', _sn + '.png'))); _b = np.array(Image.open(os.path.join(OUT, 'parts', _bn + '.png')))[..., 3] > 128
    _so, _bo = o_lg[_sn].astype(int), o_lg[_bn].astype(int)
    for _x in range(_s.shape[1]):
        _gx = _x + _so[0] - _bo[0]
        if 0 <= _gx < _b.shape[1] and _b[:, _gx].any():
            _top = int(np.nonzero(_b[:, _gx])[0].min()) + _bo[1] - _so[1]; _s[max(0, _top + 3):, _x, 3] = 0
    Image.fromarray(_s).save(os.path.join(OUT, 'parts', _sn + '.png'))
def sole(n, ank):   # 부츠 그림 바닥 점(발목 기준, 원화 px): 맨 아래 줄 양 끝 + 그 위 4px 양 끝
    #   원화 두 부츠 밑창 높이가 다름(가까운 491 · 먼 496, 땅 O=494) — 엔진은 밑창 가장 낮은 점을 땅(O)에 놓음 → 밑창 점을 (O − 밑창)만큼 옮겨 발목이 원화 자리에 오게(대기 = 원화)
    a = np.array(Image.open(os.path.join(W, n + 'Art.png')))[..., 3] > 128; o = o_lg[n]; ys = np.nonzero(a.any(1))[0]; yb = ys.max(); out = []; dy = O[1] - (yb + o[1])
    for y in (yb - 4, yb):
        xs = np.nonzero(a[y])[0]; out += [[round(float(xs.min() + o[0] - ank[0]), 1), round(float(y + o[1] - ank[1] + dy), 1)], [round(float(xs.max() + o[0] - ank[0]), 1), round(float(y + o[1] - ank[1] + dy), 1)]]
    print('  stand sole', n, 'bottom', int(yb + o[1]), 'dy', dy)
    return out
for n, sd in [('bootN', 'near'), ('bootF', 'far')]: def_parts[n].update(pivot=pc(LJ[sd]['a'], o_lg[n]), scale=2.0)
seg = lambda n, sd, p0, p1: {'part': n, 'a': pc(LJ[sd][p0], o_lg[n]), 'b': pc(LJ[sd][p1], o_lg[n]), 'w': 1.0}
ln = lambda sd, p0, p1: round(float(np.linalg.norm(LJ[sd][p1] - LJ[sd][p0])) * 2, 1)
# 달리기 다리 = 조각 시트 다리(허벅지·무릎 보호대·붕대 정강이·부츠). 시트 다리는 원화의 약 0.74배 → 시트 px 당 2.55 리그(조금 날씬하게)
RK, RB, RKN = 2.55, 2.6, 2.5
def sheet_pts(n, top, bot):   # 시트 조각 위·아래 관절 점: 위 top 줄·아래 bot 줄 알파 무게중심
    a = np.array(Image.open(os.path.join(PC, n + '.png')))[..., 3] > 128; H = a.shape[0]
    ty, tx = np.nonzero(a[:top]); by, bx = np.nonzero(a[H - bot:])
    return [round(float(tx.mean()), 1), round(float(ty.mean()), 1)], [round(float(bx.mean()), 1), round(float(by.mean() + H - bot), 1)]
TH_R, SH_R = 84.0, 66.0   # 달리기 허벅지·정강이 길이(리그) — 원화 가까운 78·70, 먼 97·61
rseg = {}
for n in ['thighN', 'thighF', 'shinN', 'shinF']:
    a_, b_ = sheet_pts(n, 6, 6); il = math.hypot(b_[0] - a_[0], b_[1] - a_[1]); wl = TH_R if n.startswith('thigh') else SH_R
    sheet_copy(n, os.path.join(OUT, 'parts', 'r' + n + '.png')); def_parts['r' + n] = dict(src=f'parts/r{n}.png', pivot=[0, 0], scale=1.0)
    rseg[n] = {'part': 'r' + n, 'a': a_, 'b': b_, 'w': round(RK * il / wl, 3)}
for n in ['kneeN', 'kneeF']:
    a = np.array(Image.open(os.path.join(PC, n + '.png'))); sheet_copy(n, os.path.join(OUT, 'parts', 'r' + n + '.png'))
    def_parts['r' + n] = dict(src=f'parts/r{n}.png', pivot=[a.shape[1] / 2, a.shape[0] / 2], scale=RKN)
sheet_copy('bootF', os.path.join(OUT, 'parts', 'rboot.png'))   # 발끝 오른쪽(앞) 부츠 — bootN 은 발끝이 바깥(왼쪽)
_rb = np.array(Image.open(os.path.join(PC, 'bootF.png')))[..., 3] > 128; _ty = int(np.nonzero(_rb.any(1))[0].min()); _tx = np.nonzero(_rb[_ty + 2])[0]
RBA = (round(float(_tx.min() + _tx.max()) / 2, 1), float(_ty + 4))   # 부츠 목 위 끝 가운데 조금 아래 = 발목
def_parts['rboot'] = dict(src='parts/rboot.png', pivot=list(RBA), scale=RB)
def sole_sheet(n, ank):
    a = np.array(Image.open(os.path.join(PC, n + '.png')))[..., 3] > 128; ys = np.nonzero(a.any(1))[0]; yb = ys.max(); out = []
    for y in (yb - 6, yb - 3, yb):
        xs = np.nonzero(a[y])[0]; out += [[round(float(xs.min() - ank[0]), 1), round(float(y - ank[1]), 1)], [round(float(xs.max() - ank[0]), 1), round(float(y - ank[1]), 1)]]
    return out
stand = lambda sd, bn: {'fade': [0.05, 0.1], 'boot': {'part': bn, 'sole': sole(bn, LJ[sd]['a'])}, 'thighImg': seg('thigh' + sd[0].upper(), sd, 'h', 'k'), 'shinImg': seg('shin' + sd[0].upper(), sd, 'k', 'a'), 'kneeImg': None}
legs = {'hip': [0, 10], 'thigh': TH_R, 'shin': SH_R,
        'thighImg': rseg['thighF'], 'shinImg': rseg['shinF'], 'thighFirst': False,
        'boot': {'part': 'rboot', 'sole': sole_sheet('bootF', RBA), 'ankleRange': [-0.45, 0.75], 'runLock': 0.0},   # runLock 0(엔진 opt-in): 달리기 다리 그림(시트 정강이·부츠)이면 발목 고정 — 부츠가 정강이와 한 줄, 발 구름 없음. DHL 10-21 12:35 '뛸 때 발이 2조각으로 나눠지면 이상 · 발 구르는 것 없이 뛰어도 좋으니 조각을 쪼개지 말아줘요'(서 있는 원화 다리 그림은 원래 범위)
        'near': {'x': round(float(LJ['near']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['near']['h'][0] - HIP[0]) * 2, 1), 'runX': -10, 'shade': 0, 'kneeOut': 1,
                 'thigh': ln('near', 'h', 'k'), 'shin': ln('near', 'k', 'a'), 'thighImg': rseg['thighN'], 'shinImg': rseg['shinN'],
                 'kneeImg': {'part': 'rkneeN', 'mix': 0.5}, 'stand': stand('near', 'bootN')},
        'far': {'x': round(float(LJ['far']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['far']['h'][0] - HIP[0]) * 2, 1), 'runX': 10, 'shade': 0,
                'thigh': ln('far', 'h', 'k'), 'shin': ln('far', 'k', 'a'), 'thighImg': rseg['thighF'], 'shinImg': rseg['shinF'],
                'kneeImg': {'part': 'rkneeF', 'mix': 0.5}, 'stand': stand('far', 'bootF')}}
print('  legs near', legs['near']['thigh'], legs['near']['shin'], 'far', legs['far']['thigh'], legs['far']['shin'], 'run w', {k: v['w'] for k, v in rseg.items()}, 'rboot', RBA)
# ---------------- 그리는 순서 (뒤 → 앞) ----------------
# 원화: 다리 < 몸통 < 벨트·앞자락 < 먼 윗팔 < 어깨갑 < 가까운 소매 < 머리 < 칼(머리카락 앞) < 위 주먹·가까운 팔뚝 < 아래 주먹·먼 팔뚝(가슴 앞)
draw = ['legFar', 'legNear', 'torso', 'hips', 'armU', 'pauldron', 'armF', 'head', 'weaponH', 'weapon', 'armLf', 'foreF', 'armL']   # 주먹 둘이 맨 앞(DHL 10-19 08:12)
GX, GY = (G_U - HIP) * 2
guard = {'gx': round(float(GX), 1), 'gy': round(float(GY), 1), 'sa': round(ang(U), 4), 'sN': 0, 'sF': round(S_LOW, 1),
         'nPiece': 'foreF', 'fPiece': 'armL', 'nUpper': 'armF', 'fUpper': 'armU', 'order': 'drawA', 'frame': 'torso'}   # 11 교훈: 칼·두 팔을 상체에 붙여 한 덩어리
_top = int(np.nonzero((mk['head'] & AL).any(1))[0].min())
rig = {'name': 'sancho-rust', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': def_parts, 'bones': bones, 'legs': legs, 'draw': draw, 'drawA': draw, 'hidden': [], 'faces': FACES,
       'metrics': {'bodyHeight': round(2 * (O[1] - _top), 1), 'note': f'rig units; 머리카락 끝(원화 y{_top})~발바닥(494) ×2, 무기 제외'},
       'armPhase': 0.5, 'gait': {'heelKick': 0.5, 'kneeLift': 0.35, 'strideBase': 80, 'strideK': 0.2, 'swingReach': -0.05, 'swingAng': 0.15, 'landAng': 0, 'hipBase': -24, 'bob': 10, 'lean': 0.1, 'headRun': 0.04},
       'carrySwing': 0.25, 'wristRange': 0.2,
       'swordGrip': {'tipDepth': 6, 'near': {'upper': 'armF', 'carry': 'foreF'}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': round(S_LOW, 1)}, 'guard': guard},
       'ui': {'attack': None, 'touch': 'hop', 'trail': 'up'},   # trail up = 게임 공격 트레일 아래 → 위(올려베기)
       'gameRef': {'refOrigin': [241.3, float(O[1])], 'refScale': 2.0, 'refLift': 0, 'note': '게임 그림 char_0003.png(512) 발 높이 = 원화. x 241.3 = 도감 칸(fitArt 중심 245.3, index.html measureBox 와 같은 계산 — 칼이 왼쪽으로 커서 그림 중심이 몸보다 왼쪽)에서 골반(hip x +8 → +4px)이 가운데 (13 네온 산초·알론소들과 같은 규칙)'},
       'note': '3 러스트 산초 (2026-10-19, v1 대기·달리기). 두 손으로 큰 칼을 쥠(swordGrip.guard, 칼날 11시), 손·팔·머리·어깨갑·다리는 원화를 그대로 오려 씀.'}
if BLINK: rig['blinkFaces'] = BLINK
exec(open(os.path.join(HERE, 'attack_sancho.py'), encoding='utf-8').read())   # 올려베기 (attack_keys.json)
_gap = (RA[..., 3] > 200) & (COVER < 200); _gap[480:] = False
print('  gaps (원화 불투명인데 조각이 안 덮음):', int(_gap.sum()), 'px')
_v = RA.copy(); _v[_gap] = (255, 0, 255, 255); Image.fromarray(_v).save(os.path.join(W, '_gaps.png'))
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(os.path.join(OUT, 'parts'))): _h.update(fn.encode()); _h.update(open(os.path.join(OUT, 'parts', fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_sancho.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['sancho-rust']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(def_parts), 'parts, version', rig['version'], 'guard', guard)
