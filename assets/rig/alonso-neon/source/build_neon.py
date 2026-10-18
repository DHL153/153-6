"""11 네온 알론소 리그 조립 (2026-10-18, 21 스카이아크 알론소 구조 기준 — 수치·조각은 전부 이 캐릭터에서 새로 잼).
입력: ref512.png(손 고친 원화 = 게임 char_0011) · pieces/(조각 시트, cut11.py) · polys.json(원화에서 오릴 다각형)
출력: ../rig.json, ../rig.def.js, ../parts/*.png
실행: cd source && python3 -I build_neon.py
원칙(DHL): 대기 자세 = 원화. 두 손은 처음부터 끝까지 칼을 쥠(swordGrip.guard). 손은 원화 손 그대로(오려 씀).
엔진 이름(21과 같음): near(armF→foreF) = 칼날 쪽 위 주먹 = 먼 팔(화면 오른쪽, 살색 팔뚝)
                    far(armU→armL) = 폼멜 쪽 아래 주먹 = 가까운 팔(화면 왼쪽, 은색 토시) + 어깨갑(pauldron)
좌표: 원화 512px로 적고 ×2 = 리그 단위.
"""
import json, math, os, shutil, hashlib
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); PC = os.path.join(HERE, 'pieces'); W = os.path.join(HERE, 'work'); OUT = os.path.join(HERE, '..')
os.makedirs(os.path.join(OUT, 'parts'), exist_ok=True); os.makedirs(W, exist_ok=True)
for f in os.listdir(os.path.join(OUT, 'parts')): os.remove(os.path.join(OUT, 'parts', f))
img = lambda p: Image.open(p).convert('RGBA')
REF = img(os.path.join(HERE, 'ref512.png')); RA = np.array(REF)
POLY = json.load(open(os.path.join(HERE, 'polys.json')))
def pmask(name_or_pts, size=(512, 512)):
    m = Image.new('L', size, 0); ImageDraw.Draw(m).polygon([tuple(p) for p in (POLY[name_or_pts] if isinstance(name_or_pts, str) else name_or_pts)], fill=255); return np.array(m) > 0
def slivers(a, k=5):
    """가늘게 삐져나온 띠(폭 < k px — 이웃 조각을 뺀 경계에 남은 외곽선 조각) 지움: 알파 열림(opening) + 1px 여유"""
    on = (a[..., 3] > 40).astype(np.uint8); op = cv2.morphologyEx(on, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    km = cv2.dilate(op, np.ones((3, 3), np.uint8)).astype(bool); a = a.copy(); a[..., 3] = np.where(km, a[..., 3], 0); return a
def islands(a, name, frac=0.03):
    """오린 조각에서 떨어진 작은 섬(다른 부품 가장자리 부스러기) 지움 — 대기 땐 다른 조각 뒤라 안 보이다가 달리기·공격에서 떠 보임 (11 v1 몸통 오른쪽 아래 검은 점)"""
    on = (a[..., 3] > 40).astype(np.uint8); n, lab, stt, _ = cv2.connectedComponentsWithStats(on, connectivity=8)
    if n <= 2: return a
    big = stt[1:, cv2.CC_STAT_AREA].max(); keep = np.zeros(n, bool); keep[1:] = stt[1:, cv2.CC_STAT_AREA] >= max(60, frac * big)
    km = cv2.dilate(keep[lab].astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    rm = int((~keep[1:]).sum())
    if rm: print('  islands', name, 'removed', rm, 'areas', sorted(int(v) for v in stt[1:, cv2.CC_STAT_AREA][~keep[1:]])[-5:])
    a = a.copy(); a[..., 3] = np.where(km, a[..., 3], 0); return a
def outline_cut(name, i0, i1, lim, thr=40):
    """다각형 name 의 변 i0..i1 안쪽에서 시작해, 검은 외곽선(밝기 < thr)에 막힐 때까지 번지는 곳(lim 안) = 외곽선 밖 이웃 그림(바지·폼멜 고리).
    대기 땐 같은 자리 밑그림과 겹쳐 안 보이지만 달리기·공격에서 주먹 밑에 회색 띠·톱니로 보였음(10-18) → 오릴 때 뺌"""
    P = POLY[name]; m = cv2.dilate(pmask(name).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0; line = (RA[..., :3].max(-1) < thr) | (RA[..., 3] < 60)
    free = (m & ~line & pmask(lim)).astype(np.uint8); seeds = np.zeros_like(free)
    for i in range(i0, i1):
        a = np.array(P[i], float); b = np.array(P[(i + 1) % len(P)], float)
        for t in np.linspace(0, 1, 40):
            x, y = a + (b - a) * t
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    xi, yi = int(round(x + dx)), int(round(y + dy))
                    if free[yi, xi]: seeds[yi, xi] = 1
    n, lab = cv2.connectedComponents(free, connectivity=4); ids = np.unique(lab[seeds > 0]); ids = ids[ids > 0]; rem = np.isin(lab, ids)
    keep_in = cv2.dilate((m & ~line & ~rem).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0   # 외곽선은 남은 안쪽에서 2px 안만 (떨어진 선 부스러기 지움)
    return rem | (m & line & pmask(lim) & ~keep_in)
COVER = np.zeros((512, 512), np.uint8)   # 오린 조각들의 알파 합(대기 자리) — 원화에 있는데 아무 조각도 안 덮는 틈 찾기
def crop(mask, name, grow=0, cut=None, src=None):
    """원화에서 mask 부분만 오려 work/name.png 로. 반환: 오린 칸 왼쪽 위(원화 px).
    grow: 위에 그리는 조각은 2px 넓혀 밑 조각과 겹치게 — 맞닿은 가장자리의 반투명 줄(틈)이 안 보이게"""
    if grow: mask = cv2.dilate(mask.astype(np.uint8), np.ones((2 * grow + 1, 2 * grow + 1), np.uint8)).astype(bool)
    if cut is not None: mask = mask & ~cut
    ys, xs = np.nonzero(mask & ((RA if src is None else src)[..., 3] > 0)); x0, y0, x1, y1 = xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3
    a = (RA if src is None else src).copy(); a[..., 3] = np.where(mask, a[..., 3], 0); a = islands(a, name); COVER[:] = np.maximum(COVER, a[..., 3]); Image.fromarray(a[y0:y1, x0:x1]).save(os.path.join(W, name + '.png')); return np.array([x0, y0], float)

# ---------------- 원화 관절 (512 px) ----------------
O = np.array([208.0, 486.0])          # 뿌리: 두 발목 가운데 땅(부츠 바닥)
HIP = np.array([192.0, 398.0]); NECK = np.array([205.0, 312.0])
HEAD_K = 0.75   # 머리·표정 배율(목 중심) — 10-19 게임 쪽 요청 0.85, 06:00 DHL "좀더 줄여" → 0.75. 아래 끝(HEAD_K 적용)·몸통 목 띠 참고
SH_N, EL_N = np.array([150.0, 342.0]), np.array([166.0, 368.0])     # 가까운 팔(엔진 armU→armL): 어깨(어깨갑 안)·팔꿈치(검은 팔꿈치 덮개)
SH_F, EL_F = np.array([247.0, 336.0]), np.array([233.0, 376.0])     # 먼 팔(엔진 armF→foreF): 어깨(먼 어깨갑 안)·팔꿈치(가까운 토시 뒤, 안 보임)
B = np.array([304.0, 331.0]); U = np.array([0.605, -0.796]); U /= np.linalg.norm(U); NRM = np.array([-U[1], U[0]])   # 칼날 아래 끝·칼끝 방향(-52.8°)
tOf = lambda p: float((np.array(p) - B) @ U)
G_U = B + U * tOf((262, 370)); G_L = B + U * tOf((248, 395))         # 쥔 점: 위 주먹(먼 손) · 아래 주먹(가까운 손) — 칼 축 위
S_LOW = (tOf((248, 395)) - tOf((262, 370))) * 2                      # 아래 주먹 = 위 주먹에서 칼끝 반대로 (리그 단위, 음수)

# ---------------- 칼: 원화 칼날·날밑을 세워서 + 시트 칼 손잡이·폼멜 ----------------
# 세운 그림 좌표 (u, v): u0 = 100 = 칼 축, v = 300 - t(원화 칼 축 거리) → 칼끝이 위
U0, V0 = 100, 340
M = np.zeros((2, 3)); M[:, 0] = NRM; M[:, 1] = -U; M[:, 2] = B - U0 * NRM + V0 * U
up = cv2.warpAffine(RA, M, (200, 470), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderValue=(0, 0, 0, 0))
sm = Image.new("L", (200, 470), 0); ImageDraw.Draw(sm).polygon([(99, 6), (112, 16), (146, 56), (146, 312), (142, 315), (142, V0 + 60), (62, V0 + 60), (62, V0 + 14), (58, V0 + 12), (58, 315), (54, 312), (54, 56), (86, 16)], fill=255)   # 날밑 막대 왼쪽 끝 u 62(그 밖은 먼 어깨갑)
sw = up.copy(); sw[..., 3] = np.where(np.array(sm) > 0, sw[..., 3], 0)
# 원화에서 칼 위에 겹친 것(머리카락·먼 어깨갑·두 주먹)은 칼에서 뺌 — 세운 그림 픽셀마다 원화 자리를 찾아 그 다각형 안이면 지움
_yy, _xx = np.mgrid[0:512, 0:512]; _nn = (_xx - B[0]) * NRM[0] + (_yy - B[1]) * NRM[1]
_src = ((pmask('head') & (np.abs(_nn) > 38)) | pmask('fArt') | pmask('nArt')).astype(np.uint8) * 255   # 머리카락은 칼날 바깥만 (날밑은 먼 어깨갑 앞이라 빼지 않음)
_srcU = cv2.warpAffine(_src, M, (200, 470), flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP, borderValue=0) > 0
sw[..., 3] = np.where(_srcU, 0, sw[..., 3])
# 날밑 아래 막대 왼쪽 반은 위 주먹·먼 어깨갑에 가려 있음 → 오른쪽 반을 좌우로 뒤집어 채움(날밑은 좌우 대칭)
_poly = np.array(sm) > 0
for v in range(V0, V0 + 53):   # 주먹에 가려진 곳만 채움: ① 거울 자리(칼 축 반대쪽)가 보이면 뒤집어 씀 ② 아니면 바로 위 칸을 아래로 늘임
    for u in range(50, 151):
        if _srcU[v, u] and _poly[v, u]:
            m = 2 * U0 - u
            if 0 <= m < 200 and sw[v, m, 3] >= 200 and not _srcU[v, m]: sw[v, u] = sw[v, m]
            elif sw[v - 1, u, 3] >= 200 and v < V0 + 48: sw[v, u] = sw[v - 1, u]
sw[V0 + 53:, :, 3] = 0
# 칼날 왼쪽(머리 쪽) 외곽선은 곧은 선 — 줄마다 왼쪽 끝을 재서 곧은 선(중앙값 맞춤) 밖으로 튀어나온 것(외곽선이 붙은 머리카락 끝, v≈270) 지움
_al = sw[..., 3] > 60; _vs = np.arange(90, 331); _le = np.array([np.nonzero(_al[v])[0].min() if _al[v].any() else U0 for v in _vs], float)
_A = np.vstack([_vs, np.ones_like(_vs)]).T; _ok = np.ones(len(_vs), bool)
for _it in range(3):
    _cf = np.linalg.lstsq(_A[_ok], _le[_ok], rcond=None)[0]; _ok = np.abs(_A @ _cf - _le) < 2.5
for v in range(80, V0 - 4):
    _cut = int(np.floor(_cf[0] * v + _cf[1] - 1.5))
    if _cut > 0: sw[v, :_cut, 3] = 0
print('  blade left edge', np.round(_cf, 4).tolist(), 'outliers', int((~_ok).sum()))
# 칼날·날밑에 붙어 온 머리카락 끝(떨어진 섬) 지움 — 달릴 때 칼과 함께 움직여 '부서진 머리카락'으로 보였음(DHL 10-18 12:03)
_on = (sw[..., 3] > 60).astype(np.uint8); _n, _lab, _st, _ct = cv2.connectedComponentsWithStats(_on, connectivity=8)
_big = 1 + int(np.argmax(_st[1:, cv2.CC_STAT_AREA])); _keep = np.zeros(_n, bool); _keep[_big] = True
for _k in range(1, _n):
    if _k != _big and _ct[_k][1] > V0 + 10: _keep[_k] = True   # 날밑 아래(손잡이 쪽)는 남김
sw[..., 3] = np.where(cv2.dilate(_keep[_lab].astype(np.uint8), np.ones((3, 3), np.uint8)) > 0, sw[..., 3], 0)
print('  sword islands removed', int((~_keep[1:]).sum()))
BLADE_O = cv2.warpAffine((sw[..., 3] > 60).astype(np.uint8), M, (512, 512), flags=cv2.INTER_NEAREST) > 0   # 칼날·날밑 자리(원화 좌표) — 머리는 이 자리만 뺌
# 손잡이: 시트 칼(83×282)의 손잡이 y 204~262만 → 0.9배, 날밑 바로 밑(V0+46)부터. 폼멜은 원화 것 하나만
ss = img(os.path.join(PC, 'sword.png')); gp = ss.crop((22, 204, 62, 252)); gp = gp.resize((round(gp.width * .9), round(gp.height * .9)), Image.LANCZOS)   # 시트 손잡이 끝·폼멜 고리(252~)는 뺌 — 원화 폼멜과 두 개로 겹쳐 보였음(10-18 달리기 확인). 끝(V0+89)은 아래 주먹 속
swI = Image.fromarray(sw); gl = Image.new('RGBA', swI.size, (0, 0, 0, 0)); gl.alpha_composite(gp, (int(U0 - 20 * .9), V0 + 46)); gl.alpha_composite(swI); swI = gl
# 폼멜: 원화 폼멜(아래 주먹 밑으로 보이는 흰 고리·금색)을 시트 폼멜 위에 — 대기 자세와 똑같게
#   원화 좌표 다각형(은색 목 + 금색 고리 + 검은 외곽선) 안에서, 바깥 변에서 번지는 바지 색(회색·어두움)만 뺌 → 외곽선이 닫힌 깨끗한 폼멜
#   (전: 밝은 픽셀만 + 1px — 외곽선·그늘이 빠져 달릴 때 톱니처럼 깨지고 주먹과 떨어져 보였음, DHL 10-18 12:03)
POMMEL = [(226, 395), (235, 394), (242, 399), (243, 406), (240, 413), (237, 421), (232, 426), (223, 426), (218, 420), (218, 412), (222, 404)]
_pmO = pmask(POMMEL); _hsv = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV); _lum = RA[..., :3].max(-1)
_pants = _pmO & (_lum >= 38) & (_lum < 125) & (_hsv[..., 1] < 90)   # 바지·손잡이 회색
_n2, _lab2 = cv2.connectedComponents(_pants.astype(np.uint8), connectivity=4); _edge = _pmO & ~(cv2.erode(_pmO.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)
_ids = np.unique(_lab2[_edge & _pants]); _ids = _ids[_ids > 0]; _rem = np.isin(_lab2, _ids)
_kin = cv2.dilate((_pmO & ~_rem & (_lum >= 38)).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
_pmO = _pmO & ~_rem & (_kin | (_lum >= 38))
_pmU = cv2.warpAffine(_pmO.astype(np.uint8), M, (200, 470), flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP) > 0
_pm = up.copy(); _pm[..., 3] = np.where(_pmU, _pm[..., 3], 0); swI.alpha_composite(Image.fromarray(_pm))
swI.save(os.path.join(W, 'sword.png'))
COVER[:] = np.maximum(COVER, cv2.warpAffine(np.array(swI)[..., 3], M, (512, 512), flags=cv2.INTER_LINEAR))
SW = dict(tip=(U0, V0 - 324), pivot=(U0, V0 - tOf((262, 370))), guard=(U0, V0 + 30), pommel=(U0, V0 + 123))

# ---------------- 원화에서 오리는 조각 ----------------
mk = {n: pmask(n) for n in ['head', 'pauldronN', 'pauldronF', 'nUp', 'nArt', 'fArt', 'torso', 'hips']}
# 칼 띠(원화에서 칼이 있는 곳) — 몸통에서 빼기
yy, xx = np.mgrid[0:512, 0:512]; tt = (xx - B[0]) * U[0] + (yy - B[1]) * U[1]; nn = (xx - B[0]) * NRM[0] + (yy - B[1]) * NRM[1]
mk['sword'] = ((tt > -40) & (np.abs(nn) < 42)) | ((tt > -120) & (np.abs(nn) < 14))   # 칼날·날밑(넓게) + 손잡이·폼멜(좁게)
# 겹침(밑에 그리는 조각이 위 조각 밑으로 몇 px 더 들어감) — 숨쉬기·달리기에서 조각끼리 1~3px 움직여도 경계에 배경(흰 줄)이 안 비치게 (DHL 10-18 12:03)
#   머리 → 가까운 어깨갑(위) 밑으로 5px · 먼 어깨갑 → 머리(위) 밑으로 5px · 머리·먼 어깨갑은 칼날 외곽선 2px 밑까지(칼이 위)
_d11 = np.ones((11, 11), np.uint8); _bladeIn = cv2.dilate(BLADE_O.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0   # 칼날 자리 + 1px — 칼 외곽선을 머리·어깨갑에 남기지 않음(공격 때 칼이 떠나면 검은 줄로 보였음, 10-18 15:30). 서 있을 땐 칼이 위라 경계 안 보임
o_head = crop(mk['head'] | ((cv2.dilate(mk['head'].astype(np.uint8), _d11) > 0) & mk['pauldronN']), 'headArt', 2, cut=_bladeIn)   # 칼날 자리만 뺌(전: 칼 띠 |n|<42 → 칼날 옆 머리카락 끝이 칼 그림으로 감)
o_pN = crop(mk['pauldronN'], 'pauldronNArt', 2); o_pF = crop(mk['pauldronF'] | (((cv2.dilate(mk['pauldronF'].astype(np.uint8), _d11) > 0) & mk['head']) if HEAD_K >= 1 else False), 'pauldronFArt', 2, cut=_bladeIn)   # (10-19) 머리를 줄이면 머리 밑으로 넣던 턱 살 띠가 드러나서 뺌
o_nUp = crop(mk['nUp'] & ~mk['pauldronN'], 'nUpArt', 2)
o_nArt = crop(mk['nArt'], 'nArt', 2, cut=outline_cut('nArt', 11, 21, [[238, 392], [280, 375], [280, 420], [225, 420], [225, 400]])); o_fArt = crop(mk['fArt'] & ~mk['nArt'], 'fArt', 2)
# 공격용 깨끗한 몸(10-18 15:30): 원화에서 두 주먹·토시·손잡이·폼멜이 덮던 골반·허벅지 자리를 바지로 메움(inpaint) — 서 있을 땐 팔·칼이 위에 있어 안 보이고,
#   공격에서 팔·칼이 떠나도 주먹 부스러기(먼 허벅지 조각 속 아래 주먹·폼멜)가 남지 않음
_occ = mk['nArt'] | mk['fArt'] | pmask(POMMEL) | (mk['sword'] & (tt < -30))
_occ = cv2.dilate(_occ.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
_body = mk['hips'] | pmask('thighF') | pmask('thighN')
_fill = _occ & _body
_rgb = RA[..., :3].copy(); _rgb[RA[..., 3] < 100] = (58, 58, 66)
_ring = (cv2.dilate(_fill.astype(np.uint8), np.ones((11, 11), np.uint8)) > 0) & ~_fill
_hsv2 = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV); _pants = _ring & (_hsv2[..., 1] < 60) & (_hsv2[..., 2] > 35) & (_hsv2[..., 2] < 120)
_pc = np.median(RA[..., :3][_pants], 0).astype(np.uint8) if _pants.any() else np.array([58, 58, 66], np.uint8)
_rgb[_ring & ~_pants] = _pc   # 둘레의 금색·파랑·검은 선은 바지색으로 바꾼 뒤 메움(노란 번짐 없게)
_inp = cv2.inpaint(np.ascontiguousarray(_rgb), _fill.astype(np.uint8) * 255, 7, cv2.INPAINT_TELEA)
RA_body = RA.copy(); RA_body[..., :3][_fill] = _inp[_fill]; RA_body[..., 3][_fill] = 255
print('  body fill px', int(_fill.sum()))
o_hips = crop(mk['hips'], 'hipsArt', src=RA_body)
# 몸통: 시트 몸통(3점 아핀으로 원화 자리에) 위에 원화 몸통(머리·어깨갑·팔·주먹·칼 뺀 곳)
ex = mk['head'] | mk['pauldronN'] | mk['pauldronF'] | mk['nUp'] | mk['nArt'] | mk['fArt'] | mk['sword']
_hin = cv2.erode(mk['head'].astype(np.uint8), np.ones((9, 9), np.uint8)) > 0   # 머리 가장자리 4px 띠는 몸통에도 남김: 숨쉬기·달리기에 머리가 1~3px 움직여도 머리 밑 경계에 흰 줄(배경)이 안 보이게(DHL 10-18 12:03 목 왼쪽 흰 선)
tm = mk['torso'] & ~((ex & ~mk['head']) | _hin) if HEAD_K >= 1 else mk['torso'] & ~ex   # (10-19) 머리를 줄이면 원화 머리 가장자리 4px 띠(턱 외곽선)가 턱 밑에 유령 선으로 남음 → 띠 없이, 그 자리는 밑의 시트 몸통 목깃   # 가장자리 틈 없이(넓히지 않음) — 틈이 있으면 밑 시트 몸통의 흰색이 선으로 보임
TA = cv2.getAffineTransform(np.float32([[45, 53], [120, 52], [88, 148]]), np.float32([[168, 332], [220, 334], [198, 401]]))
st = cv2.warpAffine(np.array(img(os.path.join(PC, 'torso.png'))), TA, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
st[..., 3] = np.where(mk['torso'] & (RA[..., 3] > 0), st[..., 3], 0)   # 시트 몸통은 원화 몸통 자리 안에서만(밑으로 삐져나온 허리 장식 지움)
ov = RA.copy(); ov[..., 3] = np.where(tm, ov[..., 3], 0)
tc = Image.fromarray(st); tc.alpha_composite(Image.fromarray(ov))
if HEAD_K < 1:   # (10-19) 머리를 줄이면 원화 머리 자리 중 새 턱 아래(목·목깃·먼 어깨 위)가 드러남 → 몸통에 목깃으로 메움(주변 몸통 색 inpaint)
    _Hs = cv2.warpAffine(mk['head'].astype(np.uint8), np.float32([[HEAD_K, 0, NECK[0] * (1 - HEAD_K)], [0, HEAD_K, NECK[1] * (1 - HEAD_K)]]), (512, 512), flags=cv2.INTER_NEAREST) > 0   # 줄인 머리 자리
    _yb = np.where(_Hs.any(0), 511 - np.argmax(_Hs[::-1], 0), 9999)   # 열마다 줄인 머리 아래 끝
    REVEAL = mk['head'] & ~_Hs & (np.arange(512)[:, None] > _yb[None, :] - 3)   # 원화 머리 자리 중 줄인 머리 아래 (3px 겹침)
    _tcn = np.array(tc); _m = (REVEAL | (mk['head'] & mk['torso'] & (_tcn[..., 3] < 250)))
    _rgb3 = np.ascontiguousarray(_tcn[..., :3]); _rgb3[_tcn[..., 3] < 128] = (24, 23, 29)
    _inp3 = cv2.inpaint(_rgb3, _m.astype(np.uint8) * 255, 5, cv2.INPAINT_TELEA)
    _tcn[..., :3][_m] = _inp3[_m]; _tcn[..., 3][_m] = 255; tc = Image.fromarray(_tcn); print('  neck fill px', int(_m.sum()))
else: REVEAL = np.zeros((512, 512), bool)
tca = islands(slivers(np.array(tc), 9), 'torsoArt'); COVER[:] = np.maximum(COVER, tca[..., 3])
ys, xs = np.nonzero(tca[..., 3] > 0); o_torso = np.array([xs.min() - 2, ys.min() - 2], float)
Image.fromarray(tca[ys.min() - 2:ys.max() + 3, xs.min() - 2:xs.max() + 3]).save(os.path.join(W, 'torsoArt.png'))
# 공격용 몸통 torsoS = 시트 몸통 통째(위와 같은 3점 아핀): 팔을 들면 원화 몸통의 팔 자리(오린 자리)가 드러나므로 공격 동안 이 그림으로 바꿈(겹쳐 바뀜)
_tsa = cv2.warpAffine(np.array(img(os.path.join(PC, 'torso.png'))), TA, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
#   (10-18 내려찍기 v2) 원화 몸통 밑에 깔고(그리는 순서 torsoS < torso) 원화 몸통이 옅어지며 바뀜 → 배경이 비치지 않게:
#   · 원화 몸통에만 있는 곳(가까운 허리)은 원화 몸통 그림으로 채움  · 원화 몸통 밖으로 나온 허리 밑단(벨트 위로 겹침)은 지움
_tin = (_tsa[..., 3] < 200) & (tca[..., 3] > 128) & (np.arange(512)[None, :] < 200); _tsa[_tin] = tca[_tin]   # 가까운 쪽만(먼 쪽 옆구리 원화는 팔·칼을 오린 톱니 경계가 남아 있음)
_tsa[(tca[..., 3] == 0) & (np.arange(512)[:, None] > 392)] = 0
ys, xs = np.nonzero(_tsa[..., 3] > 0); o_torsoS = np.array([xs.min() - 2, ys.min() - 2], float)
Image.fromarray(_tsa[ys.min() - 2:ys.max() + 3, xs.min() - 2:xs.max() + 3]).save(os.path.join(W, 'torsoSArt.png'))
# 먼 윗팔(엔진 armF): 대기·달리기에선 몸통 뒤로 안 보임 → 시트 armFdown을 어깨→팔꿈치 길이에 맞춰
# 가까운 윗팔: 원화 살색 부분(어깨갑 밑~팔꿈치 덮개)

# ---------------- 부품 표 (원화 px 원점 o, 배율 2 = 원화 1px → 리그 2) ----------------
L2 = lambda p: [round(float(p[0]) * 2 - O[0] * 2, 1), round(float(p[1]) * 2 - O[1] * 2, 1)]
pc = lambda p, o: [round(float(p[0] - o[0]), 1), round(float(p[1] - o[1]), 1)]
def_parts = {}
def part(name, src, pivot, scale=2.0, **kw):
    shutil.copy(src, os.path.join(OUT, 'parts', name + '.png')); def_parts[name] = dict(src=f'parts/{name}.png', pivot=pivot, scale=scale, **kw)
part('head', os.path.join(W, 'headArt.png'), pc(NECK, o_head))
part('torso', os.path.join(W, 'torsoArt.png'), pc(HIP, o_torso))
part('torsoS', os.path.join(W, 'torsoSArt.png'), pc(HIP, o_torsoS))
part('hips', os.path.join(W, 'hipsArt.png'), pc(HIP, o_hips))
part('pauldron', os.path.join(W, 'pauldronNArt.png'), pc(SH_N, o_pN))
part('pauldronF', os.path.join(W, 'pauldronFArt.png'), pc(SH_F, o_pF))
part('armU', os.path.join(W, 'nUpArt.png'), pc(SH_N, o_nUp), elbow=pc(EL_N, o_nUp))
part('armL', os.path.join(W, 'nArt.png'), pc(EL_N, o_nArt), elbow=pc(EL_N, o_nArt), grip=pc(G_L, o_nArt), wrist=pc(G_L, o_nArt), shaftDir=[float(U[0]), float(U[1])])
part('foreF', os.path.join(W, 'fArt.png'), pc(EL_F, o_fArt), elbow=pc(EL_F, o_fArt), grip=pc(G_U, o_fArt), wrist=pc(G_U, o_fArt), shaftDir=[float(U[0]), float(U[1])])
# 먼 윗팔: 시트 armFdown (위 끝 검은 덮개 가운데 → 아래 덮개 가운데) 를 어깨→팔꿈치에
_lenF = float(np.linalg.norm(EL_F - SH_F)) * 2; _sF = _lenF / 120.0
part('armF', os.path.join(PC, 'armFdown.png'), [36, 25], scale=round(_sF, 4), elbow=[38, 145])
part('weapon', os.path.join(W, 'sword.png'), list(SW['pivot']), tip=list(SW['tip']), tips=[[U0 - 8, 10], [U0 + 8, 10]], guard=list(SW['guard']), pommel=list(SW['pommel']))
# ---------------- 표정 (머리 그림과 같은 칸 — 눈·눈썹·입만 시트 얼굴에서, faces11.py) ----------------
exec(open(os.path.join(HERE, 'faces11.py'), encoding='utf-8').read())
for n in FACE_N: part(f'face_{n}', os.path.join(W, f'face_{n}.png'), def_parts['head']['pivot'])
# ---------------- 뼈 ----------------
ang = lambda v: math.atan2(v[1], v[0])
bones = [dict(name='root', parent=None, pos=[0, 0]), dict(name='hip', parent='root', pos=L2(HIP))]
def bone(name, parent, at, parent_at, part_=None, rot=0.0):
    b = dict(name=name, parent=parent, pos=[round(float(at[0] - parent_at[0]) * 2, 1), round(float(at[1] - parent_at[1]) * 2, 1)])
    if rot: b['rot'] = round(rot, 4)
    if part_: b['part'] = part_
    bones.append(b)
bone('hips', 'hip', HIP, HIP, 'hips'); bone('torso', 'hip', HIP, HIP, 'torso'); bones.append(dict(name='torsoS', parent='torso', pos=[0, 0], part='torsoS')); bone('head', 'torso', NECK, HIP, 'head')
# 먼 팔: armF는 그림 축(아래로)과 어깨→팔꿈치 각도 차만큼 돎
rF = ang(EL_F - SH_F) - ang(np.array([38 - 36, 145 - 25.0]))
bone('armF', 'torso', SH_F, HIP, 'armF', rF)
bones.append(dict(name='foreF', parent='armF', pos=[round(_lenF * math.cos(ang(np.array([2, 120.0]))), 1), round(_lenF * math.sin(ang(np.array([2, 120.0]))), 1)], rot=round(-rF, 4), part='foreF'))
bones.append(dict(name='fistF', parent='foreF', pos=[round(float(G_U[0] - EL_F[0]) * 2, 1), round(float(G_U[1] - EL_F[1]) * 2, 1)]))
bones.append(dict(name='weapon', parent='fistF', pos=[0, 0], rot=round(ang(U) + math.pi / 2, 4), part='weapon'))
bone('armU', 'torso', SH_N, HIP, 'armU')
bones.append(dict(name='armL', parent='armU', pos=[round(float(EL_N[0] - SH_N[0]) * 2, 1), round(float(EL_N[1] - SH_N[1]) * 2, 1)], part='armL'))
bones.append(dict(name='fistN', parent='armL', pos=[round(float(G_L[0] - EL_N[0]) * 2, 1), round(float(G_L[1] - EL_N[1]) * 2, 1)]))
bone('pauldron', 'torso', SH_N, HIP, 'pauldron'); bone('pauldronF', 'torso', SH_F, HIP, 'pauldronF')
for n in ['cape', 'scarf', 'pouch', 'skirt', 'skirtB']: bones.append(dict(name=n, parent='torso', pos=[0, -200]))   # 그림 없는 뼈: 엔진이 이름으로 찾음
# ---------------- 다리 (IK) — 원화 바지·무릎 보호대·부츠를 그대로 오려 씀 ----------------
# 원화 관절: 가까운 엉덩이(172,402)·무릎(150,426)·발목(144,454) / 먼 엉덩이(214,404)·무릎(268,428)·발목(271,464)
LJ = {'near': dict(h=np.array([172.0, 402]), k=np.array([150.0, 426]), a=np.array([144.0, 454])),
      'far': dict(h=np.array([214.0, 404]), k=np.array([268.0, 428]), a=np.array([271.0, 464]))}
# 먼 허벅지 윗선(10-18 내려찍기): 원화에선 아래 주먹·폼멜이 덮어 윗선이 없음 → 메운 자리 위가 평평하게 잘려 보였음(머리 위로 칼을 들 때).
#   벨트 끝(226,404) → 원화에 남아 있는 허벅지 윗선 시작(266,401)까지 곡선 위는 지우고, 그 선을 검은 외곽선으로 그림
RA_tF = RA_body.copy(); _tc = [(222, 405.5), (232, 404.2), (244, 403.0), (255, 402.0), (266, 401.0)]
_ss = 4; _lm = Image.new('L', (512 * _ss, 512 * _ss), 0); ImageDraw.Draw(_lm).line([(x * _ss, (y + 1.0) * _ss) for x, y in _tc], fill=255, width=int(2.3 * _ss))
_lc = np.array(_lm.resize((512, 512), Image.LANCZOS)).astype(float) / 255
_up = Image.new('L', (512, 512), 0); ImageDraw.Draw(_up).polygon([(222, 380), (282, 380), (282, 400.2), (266, 400.2)] + _tc[::-1], fill=255); _upm = np.array(_up) > 0
for c_ in range(3): RA_tF[..., c_] = (RA_tF[..., c_] * (1 - _lc) + 26 * _lc).astype(np.uint8)
RA_tF[..., 3] = np.where(_upm, 0, np.maximum(RA_tF[..., 3], (_lc * 255).astype(np.uint8)))
o_lg = {n: crop(pmask(n), n + 'Art', src=(RA_tF if n == 'thighF' else RA_body) if n.startswith('thigh') else None) for n in ['thighN', 'thighF', 'shinN', 'shinF', 'bootN', 'bootF']}
for n in o_lg: shutil.copy(os.path.join(W, n + 'Art.png'), os.path.join(OUT, 'parts', n + '.png')); def_parts[n] = dict(src=f'parts/{n}.png', pivot=[0, 0], scale=1.0)
for _sn, _bn in [('shinN', 'bootN'), ('shinF', 'bootF')]:   # (10-18 16:58 DHL '발 중복 없이') 서 있는 정강이 조각 아래쪽이 부츠 목·버클(원화에서 부츠와 같은 자리)까지 들고 있어,
    #   내려찍기에서 무릎이 굽어 정강이가 돌면 부츠 목·노란 버클이 두 겹으로 보였음 → 부츠 윗선 + 3px 아래 정강이 픽셀은 지움(부츠가 그 자리를 그림)
    _s = np.array(Image.open(os.path.join(OUT, 'parts', _sn + '.png'))); _b = np.array(Image.open(os.path.join(OUT, 'parts', _bn + '.png')))[..., 3] > 128
    _so, _bo = o_lg[_sn].astype(int), o_lg[_bn].astype(int)
    for _x in range(_s.shape[1]):
        _gx = _x + _so[0] - _bo[0]
        if 0 <= _gx < _b.shape[1] and _b[:, _gx].any():
            _top = int(np.nonzero(_b[:, _gx])[0].min()) + _bo[1] - _so[1]; _s[max(0, _top + 3):, _x, 3] = 0
    Image.fromarray(_s).save(os.path.join(OUT, 'parts', _sn + '.png'))
def sole(n, ank):   # 부츠 그림의 바닥 점(발목 기준, 원화 px): 맨 아래 줄 양 끝 + 그 위 4px 양 끝
    a = np.array(Image.open(os.path.join(W, n + 'Art.png')))[..., 3] > 128; o = o_lg[n]; ys = np.nonzero(a.any(1))[0]; yb = ys.max(); out = []
    for y in (yb - 4, yb):
        xs = np.nonzero(a[y])[0]; out += [[round(float(xs.min() + o[0] - ank[0]), 1), round(float(y + o[1] - ank[1]), 1)], [round(float(xs.max() + o[0] - ank[0]), 1), round(float(y + o[1] - ank[1]), 1)]]
    return out
for n, sd in [('bootN', 'near'), ('bootF', 'far')]: def_parts[n].update(pivot=pc(LJ[sd]['a'], o_lg[n]), scale=2.0)
seg = lambda n, sd, p0, p1: {'part': n, 'a': pc(LJ[sd][p0], o_lg[n]), 'b': pc(LJ[sd][p1], o_lg[n]), 'w': 1.0}
ln = lambda sd, p0, p1: round(float(np.linalg.norm(LJ[sd][p1] - LJ[sd][p0])) * 2, 1)
# 달리기 다리 = 조각 시트의 곧은 다리(허벅지·정강이·무릎 덮개·부츠) — 원화의 벌린 다리 조각은 옆으로 누운 모양이라 달리기에 못 씀
#   크기: 바지 굵기 원화 ≈ 50px(허벅지)·37px(정강이) → 시트 px 당 1.15 리그 단위(조금 날씬하게), 부츠 길이 원화 74px → 1.12
RK, RB, RKN = 1.15, 1.12, 0.8
def sheet_pts(n, top, bot):   # 시트 조각의 위·아래 관절 점: 위 top 줄·아래 bot 줄 알파 무게중심
    a = np.array(Image.open(os.path.join(PC, n + '.png')))[..., 3] > 128; H = a.shape[0]
    ty, tx = np.nonzero(a[:top]); by, bx = np.nonzero(a[H - bot:])
    return [round(float(tx.mean()), 1), round(float(ty.mean()), 1)], [round(float(bx.mean()), 1), round(float(by.mean() + H - bot), 1)]
TH_R, SH_R = 108.0, 78.0   # 달리기 허벅지·정강이 길이(리그). 원화 먼 허벅지 118 — 다리가 몸 밑으로 모이면 골반이 올라감(gait.hipBase −)
rseg = {}
for n in ['thighN', 'thighF', 'shinN', 'shinF']:
    a_, b_ = sheet_pts(n, 40, 40); il = math.hypot(b_[0] - a_[0], b_[1] - a_[1]); wl = TH_R if n.startswith('thigh') else SH_R
    shutil.copy(os.path.join(PC, n + '.png'), os.path.join(OUT, 'parts', 'r' + n + '.png')); def_parts['r' + n] = dict(src=f'parts/r{n}.png', pivot=[0, 0], scale=1.0)
    rseg[n] = {'part': 'r' + n, 'a': a_, 'b': b_, 'w': round(RK * il / wl, 3)}
for n in ['kneeN', 'kneeF']:
    shutil.copy(os.path.join(PC, n + '.png'), os.path.join(OUT, 'parts', 'r' + n + '.png')); def_parts['r' + n] = dict(src=f'parts/r{n}.png', pivot=[49.5, 50.5], scale=RKN)
shutil.copy(os.path.join(PC, 'boot.png'), os.path.join(OUT, 'parts', 'rboot.png')); RBA = (46.0, 30.0)
def_parts['rboot'] = dict(src='parts/rboot.png', pivot=list(RBA), scale=RB)
def sole_sheet(n, ank):
    a = np.array(Image.open(os.path.join(PC, n + '.png')))[..., 3] > 128; ys = np.nonzero(a.any(1))[0]; yb = ys.max(); out = []
    for y in (yb - 14, yb - 7, yb):   # 둥근 밑창: 세 줄 양 끝
        xs = np.nonzero(a[y])[0]; out += [[round(float(xs.min() - ank[0]), 1), round(float(y - ank[1]), 1)], [round(float(xs.max() - ank[0]), 1), round(float(y - ank[1]), 1)]]
    return out
stand = lambda sd, bn: {'fade': [0.05, 0.1], 'boot': {'part': bn, 'sole': sole(bn, LJ[sd]['a'])}, 'thighImg': seg('thigh' + sd[0].upper(), sd, 'h', 'k'), 'shinImg': seg('shin' + sd[0].upper(), sd, 'k', 'a'), 'kneeImg': None}
legs = {'hip': [0, 10], 'thigh': TH_R, 'shin': SH_R,   # 달리기(두 다리 같은 길이) — 서 있을 때는 near/far.thigh·shin(원화 길이)로 A 따라 섞임
        'thighImg': rseg['thighF'], 'shinImg': rseg['shinF'], 'thighFirst': False,
        'boot': {'part': 'rboot', 'sole': sole_sheet('boot', RBA), 'ankleRange': [-0.45, 0.75]},
        'near': {'x': round(float(LJ['near']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['near']['h'][0] - HIP[0]) * 2, 1), 'runX': -10, 'shade': 0, 'kneeOut': 1,
                 'thigh': ln('near', 'h', 'k'), 'shin': ln('near', 'k', 'a'), 'thighImg': rseg['thighN'], 'shinImg': rseg['shinN'],
                 'kneeImg': {'part': 'rkneeN', 'mix': 0.5}, 'stand': stand('near', 'bootN')},
        'far': {'x': round(float(LJ['far']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['far']['h'][0] - HIP[0]) * 2, 1), 'runX': 10, 'shade': 0,
                'thigh': ln('far', 'h', 'k'), 'shin': ln('far', 'k', 'a'), 'thighImg': rseg['thighF'], 'shinImg': rseg['shinF'],
                'kneeImg': {'part': 'rkneeF', 'mix': 0.5}, 'stand': stand('far', 'bootF')}}
print('legs near', legs['near']['thigh'], legs['near']['shin'], 'far', legs['far']['thigh'], legs['far']['shin'], 'run', rseg, 'soleR', legs['boot']['sole'])
# ---------------- 그리는 순서 (뒤 → 앞) ----------------
# 원화: 다리 < 바지 위 < 먼 윗팔(몸 뒤) < 몸통 < 먼 어깨갑 < 머리 < 칼(위 주먹 뒤) < 위 주먹·먼 팔뚝 < 가까운 윗팔 < 가까운 어깨갑 < 가까운 토시·아래 주먹
draw = ['legFar', 'legNear', 'hips', 'armF', 'torsoS', 'torso', 'pauldronF', 'head', 'weapon', 'foreF', 'armU', 'pauldron', 'armL']   # torsoS(공격용 몸통)는 원화 몸통 밑 — 원화 몸통이 옅어지며 드러남
GX, GY = (G_U - HIP) * 2
guard = {'gx': round(float(GX), 1), 'gy': round(float(GY), 1), 'sa': round(ang(U), 4), 'sN': 0, 'sF': round(S_LOW, 1),
         'nPiece': 'foreF', 'fPiece': 'armL', 'nUpper': 'armF', 'fUpper': 'armU', 'order': 'drawA',
         'frame': 'torso'}   # 팔뚝 고정(DHL 13:25): 칼·두 팔을 상체에 붙여 한 덩어리로 — 달릴 때 팔이 상체와 따로 흔들리면 오린 팔꿈치·어깨 경계가 벌어져 깨져 보였음. 움직임은 상체 기울기·오르내림·숨쉬기가 줌
rig = {'name': 'alonso-neon', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': def_parts, 'bones': bones, 'legs': legs, 'draw': draw, 'drawA': draw, 'hidden': ['torsoS'], 'faces': {n: f'face_{n}' for n in FACE_N if n not in ('half', 'closed')}, 'blinkFaces': {'half': 'face_half', 'closed': 'face_closed'},
       'metrics': {'bodyHeight': 2 * (482 - 95), 'note': 'rig units; 머리카락 가운데(y95)~발바닥(482) ×2, 무기 제외'},
       'armPhase': 0.5, 'gait': {'heelKick': 0.5, 'kneeLift': 0.35, 'strideBase': 80, 'strideK': 0.2, 'swingReach': -0.05, 'swingAng': 0.15, 'landAng': 0, 'hipBase': -44, 'bob': 10, 'lean': 0.1, 'headRun': 0.04},
       'carrySwing': 0.25, 'wristRange': 0.2,
       'swordGrip': {'tipDepth': 6, 'near': {'upper': 'armF', 'carry': 'foreF'}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': round(S_LOW, 1)}, 'guard': guard},
       'ui': {'attack': None, 'touch': 'hop'},   # attack = 'smash' 는 attack_neon.py 가 넣음(actions.smash)
       'gameRef': {'refOrigin': [281.7, float(O[1])], 'refScale': 2.0, 'refLift': 0, 'note': '게임 그림 char_0011.png(512) 발 높이 = 원화. x 281.7 = 도감 칸(fitArt 중심 265.7, index.html measureBox 와 같은 계산)에서 골반(hip x −32 → −16px)이 가운데 (21 알론소와 같은 규칙, 2026-10-18 02:20 DHL "도감 위치 가운데")'},
       'note': '11 네온 알론소 (2026-10-18, v1 대기·달리기). 두 손으로 칼을 몸 앞에 쥠(swordGrip.guard), 손·팔뚝·머리·어깨갑은 원화를 그대로 오려 씀.'}
_gap = (RA[..., 3] > 200) & (COVER < 200); _gap[440:] = False   # 다리 아래(부츠 자리)는 달리기 조각이라 뺌
print('  gaps (원화 불투명인데 조각이 안 덮음):', int(_gap.sum()), 'px')
if _gap.any():
    _v = RA.copy(); _v[_gap] = (255, 0, 255, 255); Image.fromarray(_v).save(os.path.join(W, '_gaps.png'))
exec(open(os.path.join(HERE, 'attack_neon.py'), encoding='utf-8').read())   # 내려찍기 (키: attack_keys.json)
# (10-19 DHL 03:09 게임 쪽 요청 '머리 85~90%로 — 1 러스트·21 스카이 알론소와 등신 맞추기') 머리·표정·깜빡임을 목(NECK = 머리 pivot) 중심으로 HEAD_K 배.
#   대기 자세 머리/키: 러스트 0.40 · 스카이 0.45 · 네온 0.59(1.70등신) → 0.85 에서 0.53. bodyHeight(머리카락 가운데~발바닥)도 다시 재서 게임 키를 다른 알론소와 같게
for _n in def_parts:
    if _n == 'head' or _n.startswith('face_'): def_parts[_n]['scale'] = round(def_parts[_n]['scale'] * HEAD_K, 5)
rig['metrics'] = {'bodyHeight': round(2 * ((482 - NECK[1]) + HEAD_K * (NECK[1] - 95)), 1), 'note': f'rig units; 머리카락 가운데(원화 y95)~발바닥(482) ×2, 머리 {HEAD_K}배(목 y{NECK[1]:.0f} 중심), 무기 제외'}
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(os.path.join(OUT, 'parts'))): _h.update(fn.encode()); _h.update(open(os.path.join(OUT, 'parts', fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_neon.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['alonso-neon']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(def_parts), 'parts, version', rig['version'], 'guard', guard['gx'], guard['gy'], guard['sa'], 'sF', guard['sF'])
