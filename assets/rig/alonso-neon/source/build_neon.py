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
def crop(mask, name, grow=0, cut=None):
    """원화에서 mask 부분만 오려 work/name.png 로. 반환: 오린 칸 왼쪽 위(원화 px).
    grow: 위에 그리는 조각은 2px 넓혀 밑 조각과 겹치게 — 맞닿은 가장자리의 반투명 줄(틈)이 안 보이게"""
    if grow: mask = cv2.dilate(mask.astype(np.uint8), np.ones((2 * grow + 1, 2 * grow + 1), np.uint8)).astype(bool)
    if cut is not None: mask = mask & ~cut
    ys, xs = np.nonzero(mask & (RA[..., 3] > 0)); x0, y0, x1, y1 = xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3
    a = RA.copy(); a[..., 3] = np.where(mask, a[..., 3], 0); a = islands(a, name); Image.fromarray(a[y0:y1, x0:x1]).save(os.path.join(W, name + '.png')); return np.array([x0, y0], float)

# ---------------- 원화 관절 (512 px) ----------------
O = np.array([208.0, 486.0])          # 뿌리: 두 발목 가운데 땅(부츠 바닥)
HIP = np.array([192.0, 398.0]); NECK = np.array([205.0, 312.0])
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
# 손잡이: 시트 칼(83×282)의 손잡이 y 204~262만 → 0.9배, 날밑 바로 밑(V0+46)부터. 폼멜은 원화 것 하나만
ss = img(os.path.join(PC, 'sword.png')); gp = ss.crop((22, 204, 62, 252));   # 시트 손잡이 끝·폼멜 고리(252~)는 뺌 — 원화 폼멜과 두 개로 겹쳐 보였음(10-18 달리기 확인). 끝(V0+89)은 아래 주먹 속 gp = gp.resize((round(gp.width * .9), round(gp.height * .9)), Image.LANCZOS)
swI = Image.fromarray(sw); gl = Image.new('RGBA', swI.size, (0, 0, 0, 0)); gl.alpha_composite(gp, (int(U0 - 20 * .9), V0 + 46)); gl.alpha_composite(swI); swI = gl
# 폼멜: 원화 폼멜(아래 주먹 밑으로 보이는 흰 고리·금색)을 시트 폼멜 위에 — 대기 자세와 똑같게
_pm = up.copy(); _vv, _uu = np.mgrid[0:470, 0:200]; _pmk = (_vv >= V0 + 96) & (_vv <= V0 + 128) & (np.abs(_uu - U0) <= 15) & ~_srcU
_br = cv2.dilate((_pm[..., :3].max(-1) > 150).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0   # 흰 고리·금색 + 둘레 1px 선만 (뒤 바지는 빼기)
_pm[..., 3] = np.where(_pmk & _br, _pm[..., 3], 0); swI.alpha_composite(Image.fromarray(_pm))
swI.save(os.path.join(W, 'sword.png'))
SW = dict(tip=(U0, V0 - 324), pivot=(U0, V0 - tOf((262, 370))), guard=(U0, V0 + 30), pommel=(U0, V0 + 123))

# ---------------- 원화에서 오리는 조각 ----------------
mk = {n: pmask(n) for n in ['head', 'pauldronN', 'pauldronF', 'nUp', 'nArt', 'fArt', 'torso', 'hips']}
# 칼 띠(원화에서 칼이 있는 곳) — 몸통에서 빼기
yy, xx = np.mgrid[0:512, 0:512]; tt = (xx - B[0]) * U[0] + (yy - B[1]) * U[1]; nn = (xx - B[0]) * NRM[0] + (yy - B[1]) * NRM[1]
mk['sword'] = ((tt > -40) & (np.abs(nn) < 42)) | ((tt > -120) & (np.abs(nn) < 14))   # 칼날·날밑(넓게) + 손잡이·폼멜(좁게)
o_head = crop(mk['head'] & ~mk['sword'], 'headArt', 2)
o_pN = crop(mk['pauldronN'], 'pauldronNArt', 2); o_pF = crop(mk['pauldronF'] & ~mk['sword'], 'pauldronFArt', 2)
o_nUp = crop(mk['nUp'] & ~mk['pauldronN'], 'nUpArt', 2)
o_nArt = crop(mk['nArt'], 'nArt', 2, cut=outline_cut('nArt', 11, 21, [[238, 392], [280, 375], [280, 420], [225, 420], [225, 400]])); o_fArt = crop(mk['fArt'] & ~mk['nArt'], 'fArt', 2)
o_hips = crop(mk['hips'] & ~mk['nArt'] & ~mk['sword'], 'hipsArt')
# 몸통: 시트 몸통(3점 아핀으로 원화 자리에) 위에 원화 몸통(머리·어깨갑·팔·주먹·칼 뺀 곳)
ex = mk['head'] | mk['pauldronN'] | mk['pauldronF'] | mk['nUp'] | mk['nArt'] | mk['fArt'] | mk['sword']
tm = mk['torso'] & ~ex   # 가장자리 틈 없이(넓히지 않음) — 틈이 있으면 밑 시트 몸통의 흰색이 선으로 보임
TA = cv2.getAffineTransform(np.float32([[45, 53], [120, 52], [88, 148]]), np.float32([[168, 332], [220, 334], [198, 401]]))
st = cv2.warpAffine(np.array(img(os.path.join(PC, 'torso.png'))), TA, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
st[..., 3] = np.where(mk['torso'] & (RA[..., 3] > 0), st[..., 3], 0)   # 시트 몸통은 원화 몸통 자리 안에서만(밑으로 삐져나온 허리 장식 지움)
ov = RA.copy(); ov[..., 3] = np.where(tm, ov[..., 3], 0)
tc = Image.fromarray(st); tc.alpha_composite(Image.fromarray(ov)); tca = islands(slivers(np.array(tc), 9), 'torsoArt')
ys, xs = np.nonzero(tca[..., 3] > 0); o_torso = np.array([xs.min() - 2, ys.min() - 2], float)
Image.fromarray(tca[ys.min() - 2:ys.max() + 3, xs.min() - 2:xs.max() + 3]).save(os.path.join(W, 'torsoArt.png'))
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
bone('hips', 'hip', HIP, HIP, 'hips'); bone('torso', 'hip', HIP, HIP, 'torso'); bone('head', 'torso', NECK, HIP, 'head')
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
o_lg = {n: crop(pmask(n), n + 'Art') for n in ['thighN', 'thighF', 'shinN', 'shinF', 'bootN', 'bootF']}
for n in o_lg: shutil.copy(os.path.join(W, n + 'Art.png'), os.path.join(OUT, 'parts', n + '.png')); def_parts[n] = dict(src=f'parts/{n}.png', pivot=[0, 0], scale=1.0)
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
draw = ['legFar', 'legNear', 'hips', 'armF', 'torso', 'pauldronF', 'head', 'weapon', 'foreF', 'armU', 'pauldron', 'armL']
GX, GY = (G_U - HIP) * 2
guard = {'gx': round(float(GX), 1), 'gy': round(float(GY), 1), 'sa': round(ang(U), 4), 'sN': 0, 'sF': round(S_LOW, 1),
         'nPiece': 'foreF', 'fPiece': 'armL', 'nUpper': 'armF', 'fUpper': 'armU', 'order': 'drawA',
         'run': {'gx': [6, 0.15], 'gy': [7, 0.1], 'sa': [0.04, 0.35]}, 'runAt': {'gx': 12, 'gy': -22, 'sa': -0.05}, 'breath': {'gy': 3, 'sa': 0.01}}
rig = {'name': 'alonso-neon', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': def_parts, 'bones': bones, 'legs': legs, 'draw': draw, 'drawA': draw, 'hidden': [], 'faces': {n: f'face_{n}' for n in FACE_N if n not in ('half', 'closed')}, 'blinkFaces': {'half': 'face_half', 'closed': 'face_closed'},
       'metrics': {'bodyHeight': 2 * (482 - 95), 'note': 'rig units; 머리카락 가운데(y95)~발바닥(482) ×2, 무기 제외'},
       'armPhase': 0.5, 'gait': {'heelKick': 0.5, 'kneeLift': 0.35, 'strideBase': 80, 'strideK': 0.2, 'swingReach': -0.05, 'swingAng': 0.15, 'landAng': 0, 'hipBase': -44, 'bob': 10, 'lean': 0.1},
       'carrySwing': 0.25, 'wristRange': 0.2,
       'swordGrip': {'tipDepth': 6, 'near': {'upper': 'armF', 'carry': 'foreF'}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': round(S_LOW, 1)}, 'guard': guard},
       'ui': {'attack': 'smash', 'touch': 'hop'},
       'gameRef': {'refOrigin': [float(O[0]), float(O[1])], 'refScale': 2.0, 'refLift': 0, 'note': '게임 그림 char_0011.png(512) = 원화'},
       'note': '11 네온 알론소 (2026-10-18, v1 대기·달리기). 두 손으로 칼을 몸 앞에 쥠(swordGrip.guard), 손·팔뚝·머리·어깨갑은 원화를 그대로 오려 씀.'}
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(os.path.join(OUT, 'parts'))): _h.update(fn.encode()); _h.update(open(os.path.join(OUT, 'parts', fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_neon.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['alonso-neon']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(def_parts), 'parts, version', rig['version'], 'guard', guard['gx'], guard['gy'], guard['sa'], 'sF', guard['sF'])
