"""29 스카이아크 팔로메 리그 조립 (2026-10-20~) — 9 러스트 팔로메 v1.1 구조 그대로(몸 = 6 카르덴식 드워프, 칼 = 먼 팔이 어깨에 멤·칼날 머리 뒤) + 망토(cape 뼈·메시)·먼 비늘 대신 남색 소매 윗팔
입력: ref512.png(원화 = 게임 char_0029) · work/labels.npy(seg29.py) · pieces/(조각 시트 22칸, cut29.py) · work/geom.json(reg29.py SIFT: 머리·표정·수염만 씀)
출력: ../rig.json · ../rig.def.js · ../parts/*.png
실행: cd source && python3 -I cut29.py && python3 -I seg29.py && python3 -I reg29.py && python3 -I build_sky29.py
원칙(DHL): 대기 = 원화 · 칼 크기 그대로 · 칼날은 원화처럼 머리 뒤 · 팔다리 길이 고정 · 공격 = 9 v1.1 과 같은 한 손 내려찍기(전투 칸 위로 칼끝이 안 나가게)
좌표: 원화 512px 로 적고, 리그 단위 = ×2 (조각 그림은 원화 px 그대로, part scale 2)
엔진 이름(21 알론소와 같음): armF→foreF→fistF→weapon = 칼 메는 팔(여기선 몸 뒤 먼 팔, 왼손) · armU→armL + pauldron = 자유 팔(가까운 팔, 큰 어깨갑)
"""
import json, math, os, shutil, hashlib
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); PC = os.path.join(HERE, 'pieces'); W = os.path.join(HERE, 'work'); OUT = os.path.join(HERE, '..'); PARTS = os.path.join(OUT, 'parts')
if os.path.isdir(PARTS): shutil.rmtree(PARTS)
os.makedirs(PARTS); os.makedirs(W, exist_ok=True)
RA = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA'))
LAB = np.load(os.path.join(W, 'labels.npy'))
NAMES = ['head', 'sword', 'handF', 'foreF', 'upperF', 'pauldron', 'upperN', 'foreN', 'cape', 'legN', 'legF', 'body']
PO_ = json.load(open(os.path.join(HERE, 'polys29.json')))
def poly_(pts):
    from PIL import ImageDraw as _D
    m = Image.new('L', (512, 512), 0); _D.Draw(m).polygon([tuple(map(float, q)) for q in pts], fill=255); return np.array(m) > 0
LID = {n: i + 1 for i, n in enumerate(NAMES)}
lab = lambda n: LAB == LID[n]
GEO = json.load(open(os.path.join(W, 'geom.json')))
YY, XX = np.mgrid[0:512, 0:512]
def desp(a):   # 자홍 배경 번짐 지움
    a = a.astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None); a[..., 0] -= m; a[..., 2] -= m; return np.clip(a, 0, 255).astype(np.uint8)
def sheet(n): return desp(np.array(Image.open(os.path.join(PC, n + '.png')).convert('RGBA')))
def warp(img, M): return cv2.warpAffine(img, np.array(M, np.float32), (512, 512), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
def simil(a0, a1, b0, b1):   # 두 점 a → b 닮음 (2×3)
    a0, a1, b0, b1 = map(lambda v: np.array(v, float), (a0, a1, b0, b1)); va, vb = a1 - a0, b1 - b0; s = np.linalg.norm(vb) / np.linalg.norm(va)
    th = math.atan2(vb[1], vb[0]) - math.atan2(va[1], va[0]); R = s * np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]]); return np.c_[R, b0 - R @ a0]
def art(mask):   # 원화에서 mask 만
    a = RA.copy(); a[..., 3] = np.where(mask, a[..., 3], 0); return a
def under(a, b, where):   # a(원화 조각) 밑에 b(채움)를 where 에서만
    out = a.copy(); w = where & (b[..., 3] > 0) & (a[..., 3] < 250)
    fa = a[..., 3:4] / 255.0; fb = b[..., 3:4] / 255.0
    col = a[..., :3] * fa + b[..., :3] * fb * (1 - fa); al = fa + fb * (1 - fa)
    out[w, :3] = np.clip(col[w] / np.maximum(al[w], 1e-3), 0, 255).astype(np.uint8); out[w, 3] = np.clip(al[w, 0] * 255, 0, 255).astype(np.uint8); return out
OFF = {}
def save(name, a, pad=2):   # 512 캔버스 → 잘라 저장, 반환 = 왼쪽 위(원화 px)
    ys, xs = np.nonzero(a[..., 3] > 0); x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad); x1, y1 = min(512, xs.max() + 1 + pad), min(512, ys.max() + 1 + pad)
    Image.fromarray(a[y0:y1, x0:x1]).save(os.path.join(PARTS, name + '.png')); OFF[name] = (x0, y0); return np.array([x0, y0], float)
def dil(m, r): return cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0

# ---------------- 원화 관절 (512 px, review/z_*.png 격자에서 읽음) ----------------
O = np.array([263.0, 478.0])           # 뿌리: 두 발 가운데 땅(발바닥 y 478)
HIP = np.array([268.0, 392.0])         # 골반(허리띠 가운데 높이) — 상체·치마 뼈
NECK = np.array([282.0, 248.0])        # 머리+수염 뼈(수염 속 목)
SH_N, EL_N, WR_N = np.array([160.0, 245.0]), np.array([98.0, 306.0]), np.array([170.0, 335.0])   # 가까운 팔(자유 팔): 어깨(어깨갑 속)·팔꿈치(토시 왼쪽 끝)·손목(장갑 시작)
SH_F, EL_F, WR_F = np.array([362.0, 262.0]), np.array([424.0, 312.0]), np.array([410.0, 246.0])   # 먼 팔(칼 메는 팔): 어깨(어깨판 뒤)·팔꿈치(토시 아래)·손목(손 밑)
HA0, HA1 = np.array([372.0, 197.0]), np.array([478.0, 257.0])     # 손잡이 축(날밑 → 폼멜)
G = HA0 + (HA1 - HA0) * ((412.0 - HA0[0]) / (HA1[0] - HA0[0]))   # 쥔 점 = 손잡이 축 위 x 412 (손가락 가운데)
TOPL, BOTL = (0.3812, 18.1714), (0.462, 58.7347)                   # 칼날 위·아래 가장자리 (원화 맞춤 선 y = a x + b, 날 끝 비스듬한 곳 빼고)
MID = ((TOPL[0] + BOTL[0]) / 2, (TOPL[1] + BOTL[1]) / 2); UT = -np.array([1.0, MID[0]]) / math.hypot(1, MID[0])   # 칼끝 방향(날 가운데 선)
TIP = np.array([26.0, 51.0])
LEG = {'near': dict(hip=np.array([182.0, 430.0]), ankle=np.array([176.0, 458.0])), 'far': dict(hip=np.array([330.0, 430.0]), ankle=np.array([331.0, 458.0]))}
R2 = lambda p: [round(float(2 * (p[0] - O[0])), 1), round(float(2 * (p[1] - O[1])), 1)]   # 원화 → 리그(뿌리 기준)

# ---------------- 조각 그림 ----------------
def col_match(im, ref_m, k=1.0):   # 시트 조각 색을 원화 같은 부위 색(채널별 평균·편차)에 맞춤 (9 v1.1 교훈: 시트 색이 원화와 다름)
    im = im.astype(np.float32); m = im[..., 3] > 200; R = RA[..., :3].astype(np.float32)[ref_m & (RA[..., 3] > 200)]
    for c in range(3):
        v = im[..., c][m]; im[..., c] = np.where(im[..., 3] > 0, (im[..., c] - v.mean()) / max(1.0, v.std()) * R[:, c].std() + R[:, c].mean(), im[..., c])
    im[..., :3] *= k; return np.clip(im, 0, 255).astype(np.uint8)
def hull_inpaint(m_src, where, r=4):   # m_src 볼록 껍질 안 + where 를 m_src 색으로 inpaint (그 밖은 모르는 값) — 가려진 가장자리 메움
    hull = np.zeros((512, 512), np.uint8); cv2.fillConvexPoly(hull, cv2.convexHull(np.argwhere(m_src)[:, ::-1].astype(np.int32)), 1)
    fill = (hull > 0) & where & ~m_src
    rgb = cv2.inpaint(np.ascontiguousarray(RA[..., :3]), (~m_src).astype(np.uint8), r, cv2.INPAINT_TELEA)
    out = np.zeros_like(RA); out[..., :3] = rgb; out[..., 3] = np.where(fill, 255, 0)
    edge = fill & (cv2.distanceTransform((hull > 0).astype(np.uint8), cv2.DIST_L2, 3) < 2.2); out[edge, :3] = (30, 28, 34)   # 껍질 가장자리 = 외곽선 2px
    return out, fill
NAVY = np.array([46.0, 45.0, 54.0])   # 원화 남색 천(바지·소매) 가운데 값
def flat_fill(m_src, where, col=NAVY):   # m_src 볼록 껍질 안 + where 를 납작한 천 색으로(번진 inpaint 대신) + 껍질 가장자리 외곽선 2px
    hull = np.zeros((512, 512), np.uint8); cv2.fillConvexPoly(hull, cv2.convexHull(np.argwhere(m_src)[:, ::-1].astype(np.int32)), 1)
    fill = (hull > 0) & where & ~m_src; out = np.zeros_like(RA)
    sh = np.clip(cv2.GaussianBlur(np.random.default_rng(3).normal(0, 1, (512, 512)).astype(np.float32), (0, 0), 6) * 25, -8, 8)
    out[..., :3] = np.clip(col[None, None] + sh[..., None], 0, 255).astype(np.uint8); out[..., 3] = np.where(fill, 255, 0)
    edge = fill & (cv2.distanceTransform((hull > 0).astype(np.uint8), cv2.DIST_L2, 3) < 2.2); out[edge, :3] = (24, 24, 30)
    return out, fill
def sleeve(p0, p1, r, col=NAVY):   # 소매 관(둥근 끝 캡슐): 가로 음영 + 외곽선 2px — 원화에서 거의 안 보이는 윗팔을 팔이 움직일 때만 보이게
    p0, p1 = np.array(p0, float), np.array(p1, float); u = (p1 - p0) / np.linalg.norm(p1 - p0); n = np.array([-u[1], u[0]])
    P = np.stack([XX, YY], -1).astype(float) - p0; t = np.clip(P @ u, 0, np.linalg.norm(p1 - p0)); q = P - t[..., None] * u[None, None]; d = np.linalg.norm(q, axis=-1)
    side = (P @ n) / r; out = np.zeros_like(RA); inside = d <= r
    shade = 1.0 + 0.18 * np.exp(-((side + .35) / .3) ** 2) - 0.28 * np.clip(np.abs(side), 0, 1) ** 2
    out[..., :3] = np.clip(col[None, None] * shade[..., None], 0, 255).astype(np.uint8); out[..., 3] = np.where(inside, 255, 0)
    out[inside & (d > r - 2), :3] = (24, 24, 30); return out
# 상체·치마: 몸(body)을 허리띠 위 선에서 나눔 (치마 = 허리띠·주머니·남색 아랫자락, 상체 = 그 위 + 14px 겹침)
CUT = np.array([[110, 352], [205, 356], [215, 370], [250, 377], [300, 382], [350, 381], [410, 375]], float)
cut_y = np.interp(XX, CUT[:, 0], CUT[:, 1]); OVL = 14
body = lab('body')
# 상체 메움: 시트 상체 → 가슴 버클(시트 110,75 → 원화 289,291)·먼 어깨 금 단추(172,40 → 351,247) 두 점 닮음
st = sheet('torso'); MT = simil((110, 75), (172, 40), (289, 291), (351, 247)); stw = warp(col_match(st, lab('body') & (YY < 380)), MT)   # 색 = 원화 몸통(시트 크림이 더 밝고 노람)
OCC = lab('head') | lab('handF') | lab('foreF') | lab('upperF') | lab('sword') | lab('pauldron') | lab('upperN') | lab('foreN')
bflat, fillN = flat_fill(body, lab('foreN') | lab('upperN') | lab('pauldron'))   # 가까운 팔 밑 몸 가장자리: 시트 상체가 못 덮는 곳은 남색 천(번진 inpaint 는 달리기 확대에서 얼룩으로 보였음)
# 몸 오른쪽 위(칼 날밑·손·먼 토시 밑): 몸 껍질이 칼 쪽까지 부풀어 남색 삼각형이 생겼음 → 몸 어깨 윤곽(SHOULDER_R) 안만 채움,
#   그 칸의 작은 원화 몸 조각(날밑·손 사이로 보이던 끈 토막 < 150px)은 몸에서 빼고 채움 — 칼·팔이 떠나면 찢긴 조각으로 보였음 (10-20 07:57 확대)
SHOULDER_R = np.zeros((512, 512), np.uint8); cv2.fillPoly(SHOULDER_R, [np.array([(296, 232), (330, 236), (352, 246), (372, 262), (390, 284), (402, 312), (406, 345), (300, 345)], np.int32)], 1)
_zone = (XX > 318) & (YY < 330); _bz = (body & _zone).astype(np.uint8); _k, _cc, _st, _ = cv2.connectedComponentsWithStats(_bz, connectivity=8)
_frag = np.zeros((512, 512), bool)
for _j in range(1, _k):
    if _st[_j, 4] < 150: _frag |= _cc == _j
_sh3a = cv2.warpAffine((np.array(Image.open(os.path.join(PC, 'p3_shoulderF3.png')).convert('RGBA'))[..., 3] > 100).astype(np.uint8), np.array(GEO['p3_shoulderF3']['M'], np.float32), (512, 512), flags=cv2.INTER_NEAREST) > 0
body = body & ~_frag; print('  shoulder fragments removed', int(_frag.sum()), 'px')
# 다리 윗부분 (10-20 13:47 DHL '알파가 잘 안 따진 곳 · 필요 없는 부분' — 부츠 위 두 곳): 치마 밑단 아래 무릎 토시·끈·바지가 원화 라벨에서 몸(body)으로 가 치마 조각에 붙어 있었음
#   → 대기 숨쉬기로 치마가 ±2px 오르내리면 토시 위(치마)·아래(서 있는 다리)가 갈라져 찢긴 조각·파란 틈으로 보였음.
#   밑단 선(토시 윗 외곽선) 아래 몸 픽셀 = 서 있는 다리 조각(토시 통째), 치마는 그 선에서 끝남(선 한 줄은 두 조각 모두 — 대기 = 원화)
HEM = {'near': np.array([[146, 431], [212, 431], [215, 436], [232, 437]], float), 'far': np.array([[294, 437], [339, 437], [347, 428], [364, 429], [376, 433]], float)}   # 먼 쪽: 치마 판 아래 외곽선 → 판 오른쪽 아래 모서리 사선 → 토시 윗 외곽선
HEMX = {'near': (146, 232), 'far': (294, 376)}
hem_y = {sd: np.ceil(np.interp(XX, HEM[sd][:, 0], HEM[sd][:, 1]) - 1e-6) for sd in HEM}   # 칸마다 다리 첫 줄(정수)
legTop = {sd: body & (XX >= HEMX[sd][0]) & (XX <= HEMX[sd][1]) & (YY >= hem_y[sd]) & (YY < 470) for sd in HEM}
LEGTOP_ALL = legTop['near'] | legTop['far']
SKIRT_CUT = (legTop['near'] & (YY > hem_y['near'])) | (legTop['far'] & (YY > hem_y['far']))   # 치마에서 뺄 곳(밑단 선 한 줄은 치마에도 남김)
print('  leg tops from body', {sd: int(legTop[sd].sum()) for sd in legTop})
# 가까운 주먹 둘레 (DHL 같은 지적 — 주먹 오른쪽): 대기 숨쉬기 팔 흔들림(윗팔 ±.03 + 팔뚝 ±.04 rad → 주먹 ±6~7px)으로 주먹이 비키면 그 밑 상체 메움(시트 상체 크림)이
#   둘레 원화(밤색 천)와 달라 톱니 크림 조각으로 보였고, 주먹 외곽선 바깥 1~2px(라벨에서 몸으로 간 어두운 선)이 상체에 남아 실금처럼 보였음
#   → ①주먹 둘레 2px 어두운 선 + 토시 끝 작은 크림 조각(몸 라벨로 간 것)은 주먹 조각으로 ②주먹 밑 12px 띠 = 재질별 납작한 색(아래 _MAT, 경계 1px 외곽선)
#     ③주먹 오른쪽 아래 크림 배 판은 보이는 두 외곽선을 주먹 밑으로 이어 판 모서리를 그림(아래 PLATE_H)
#   대기 그대로: ①은 주먹이 같은 자리에 그리고 ②③은 주먹 밑(대기 중 주먹이 비키는 만큼만 보임)
from scipy import ndimage as _ndi
FN = lab('foreN'); _lumA = RA[..., :3].astype(int).mean(-1)
RING_N = body & dil(FN, 2) & ~FN & (_lumA < 70)
_cr = body & ~FN & (_lumA > 140) & dil(FN, 4); _ccn, _ccl, _ccs, _ = cv2.connectedComponentsWithStats(_cr.astype(np.uint8), connectivity=8)
for _j in range(1, _ccn):   # 주먹 토시 끝이 몸 라벨로 간 작은 크림 조각(< 60px, 주먹에 닿음) → 주먹 조각으로
    if _ccs[_j, 4] < 60 and (dil(FN, 1) & (_ccl == _j)).any(): RING_N |= _ccl == _j
# 재질(밤색 천·남색 천·쇠 버클)을 색 규칙으로 나눠, 띠의 각 점 = 가장 가까운 재질의 납작한 가운데 색 — 원화 색을 그대로 이으면 줄무늬·톱니,
#   k-평균은 판 가장자리 안티에일리어스를 재질로 잡아 얼룩(10-20 확대 비교: 그대로 이음·TELEA·섞기·k-평균 모두 얼룩)
_R, _G, _B = (RA[..., c].astype(int) for c in range(3))
_MAT = [(_R - _B >= 18) & (_R - _G >= 12) & (_lumA >= 45) & (_lumA <= 140),   # 밤색 천(가운데 띠)
        (_B - _R >= 4) & (_lumA >= 25) & (_lumA <= 95),                       # 남색 천(위)
        (np.abs(_R - _B) < 14) & (_lumA >= 95) & (_lumA <= 175)]              # 쇠 버클(아래)
_srcN = body & ~FN & ~RING_N & (RA[..., 3] > 200) & dil(FN, 16)
_kmap = np.full((512, 512), -1, int)
for _j, _m in enumerate(_MAT): _kmap[_srcN & _m & (_kmap < 0)] = _j
_srcN &= _kmap >= 0
_kmed = np.array([np.median(RA[_srcN & (_kmap == j)][:, :3], 0) for j in range(len(_MAT))])
_dN, _iN = _ndi.distance_transform_edt(~_srcN, return_indices=True)
BAND_N = (FN | RING_N) & (_ndi.distance_transform_edt(~(body & ~FN & ~RING_N)) <= 12)   # 띠 = 몸 경계에서 12px
_kfill = _kmap[_iN[0], _iN[1]]
_dm = _ndi.distance_transform_edt(~(_srcN & (_kmap == 2))); _cl = _srcN & (_kmap < 2)
_dc, _ic = _ndi.distance_transform_edt(~_cl, return_indices=True)
_kfill = np.where((_kfill == 2) & (_dm > 4), _kmap[_ic[0], _ic[1]], _kfill)   # 쇠 버클은 4px 까지만 이음(버클 테 굵기) — 더 이으면 회색 덩어리
_oh = np.stack([cv2.blur((_kfill == j).astype(np.float32), (7, 7)) for j in range(len(_MAT))], -1)
_kfill = np.where(FN | RING_N, np.argmax(_oh, -1), _kfill)   # 재질 경계를 7px 다수결로 매끈하게(작은 섬·톱니 없앰)
EXT_N = RA.copy(); EXT_N[..., :3] = np.clip(_kmed[_kfill] + np.clip(cv2.GaussianBlur(np.random.default_rng(4).normal(0, 1, (512, 512)).astype(np.float32), (0, 0), 3) * 12, -5, 5)[..., None], 0, 255).astype(np.uint8); EXT_N[..., 3] = 255
print('  fist fill materials', [tuple(int(v) for v in c) for c in _kmed], [int((_srcN & (_kmap == j)).sum()) for j in range(len(_MAT))])
_kd = np.zeros((512, 512), bool)
for _sy, _sx in ((0, 1), (1, 0)): _kd |= _kfill != np.roll(_kfill, (-_sy, -_sx), (0, 1))
EXT_N[BAND_N & _kd, :3] = (34, 30, 34)   # 채운 띠 안에서 재질이 바뀌는 곳 = 외곽선 1px(원화처럼 판·천 경계에 선)
# 주먹 오른쪽 아래 크림 배 판: 원화에선 판 왼쪽 위 외곽선(236,336 → 227,347)과 왼쪽 아래 외곽선(224,369 → 228,373)만 보이고 그 사이 판 가장자리는
#   주먹 외곽선이 겸함 → 주먹이 비키면 판이 외곽선 없이 톱니로 끝나 '흰 조각'(DHL 동그라미 1). 두 선을 주먹 밑으로 이어(만나는 점 ≈ 216,361) 판을 그리고 안쪽 2px 외곽선,
#   선 밖은 위 재질 채움(밤색 천). 판 색 = 가장 가까운 원화 판 픽셀
_d1 = (XX - (227 - 0.8 * (YY - 347))) / math.hypot(1, 0.8); _d2 = (XX - (224 + (YY - 369))) / math.sqrt(2)
_plate = body & (_lumA > 150) & (XX >= 214) & (XX <= 245) & (YY >= 330) & (YY <= 380) & ~FN & ~RING_N
PLATE_H = (FN | RING_N) & (_d1 > 0) & (_d2 > 0) & (YY >= 340) & (YY <= 375)
_dp, _ip = _ndi.distance_transform_edt(~_plate, return_indices=True)
_o = np.clip(2.3 - np.minimum(_d1, _d2), 0, 1)[..., None]
EXT_N[PLATE_H, :3] = np.clip(RA[_ip[0], _ip[1], :3] * (1 - _o) + np.array([34, 30, 34]) * _o, 0, 255)[PLATE_H].astype(np.uint8)
BAND_N |= PLATE_H
print('  fist ring', int(RING_N.sum()), 'band', int(BAND_N.sum()), 'hidden plate', int(PLATE_H.sum()))
bflat2, fillO = flat_fill(body, (OCC | _frag) & (SHOULDER_R > 0))
fillO &= ~(_zone & ~(stw[..., 3] > 100))   # 오른쪽 위(칼·먼 팔 자리)는 시트 상체 윤곽 안만 — 밖을 남색으로 채우면 팔이 떠난 뒤 남색 깃발처럼 보였음(10-20 09:00)   # 그 밖의 앞 조각(칼 날밑·손잡이·먼 토시·수염) 밑도 시트가 못 덮는 곳은 남색 천 — 칼을 들면 날밑 자리에 배경 구멍·찢어진 조각이 보였음
_OK = (~_zone | (SHOULDER_R > 0)) & (YY < cut_y + OVL)
# 먼 어깨(시트 3 2번, 10-20 08:23 — 수염 오른쪽 세로 크림 판·금 단추·가죽 끈·남색 어깨 천): 칼 날밑·손·토시에 가려졌던 어깨를 이 조각으로 먼저 메움(SIFT 맞춤)
sh3 = cv2.warpAffine(desp(np.array(Image.open(os.path.join(PC, 'p3_shoulderF3.png')).convert('RGBA'))), np.array(GEO['p3_shoulderF3']['M'], np.float32), (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
# 날밑·손·토시 경계 4px 띠(어깨 쪽): 원화 몸 픽셀은 톱니 외곽선 조각 → 시트 어깨로 바꿈(시트 어깨가 없는 곳은 지움). 대기엔 날밑·손이 거의 덮음
_ring = _zone & (cv2.dilate((lab('sword') | lab('handF') | lab('foreF')).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))) > 0) & body
_sh3s = sh3[..., 3] > 200
_Zrep = _zone & body & _sh3s & (YY < 300)   # 시트 어깨가 있는 곳 = 시트 어깨로 통째(어깨 판 위 끝이 날밑 뒤에서 톱니로 잘려 있었음)
_Zcut = _zone & body & (SHOULDER_R == 0) & ~(cv2.dilate(_sh3s.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & (YY < 300)   # 어깨 윤곽·시트 어깨 밖으로 삐죽 나온 조각
_ring = _ring | _Zrep | _Zcut
SEAM = _ring.copy()   # 대기 그대로를 위해 원화 경계 픽셀은 seamF(서 있을 때만 그림)로 따로 남김
_t0 = art(body & (YY < cut_y + OVL)); _t0[_ring & (sh3[..., 3] > 200)] = sh3[_ring & (sh3[..., 3] > 200)]; _t0[_ring & (sh3[..., 3] <= 200), 3] = 0
print('  shoulder ring', int(_ring.sum()), 'px')
torso = under(under(under(under(_t0, sh3, (OCC | _frag) & (SHOULDER_R > 0) & (YY < cut_y + OVL)), stw, (OCC | _frag) & _OK), bflat, fillN & (YY < cut_y + OVL)), bflat2, fillO & (YY < cut_y + OVL))
_bt = BAND_N & (YY < cut_y + OVL); torso[_bt] = EXT_N[_bt]   # 주먹 밑 띠 = 둘레 원화 몸 색 이음(위 '가까운 주먹 둘레')
o_torso = save('torso', torso)
# 공격용 상체 torsoM (10-20 10:41 DHL '29 타격 때 어깨 위치를 무시하고 팔이 너무 아래로' → 손을 올리니 먼 어깨 둘레가 더 보임):
#   먼 어깨 둘레 원화 부스러기(칼·손·토시 경계에서 라벨이 갈라진 크림 왕관·검은 뾰족 조각)는 빼고, 시트 3 먼 어깨(sh3)를 자기 알파로 통째 덮고,
#   경계 띠에서 비운 구멍(날밑 자리 크림 판 홈)은 둘레 상체 색으로 메움. 공격 0.04~0.85 동안만(tPiece) — 서 있기·달리기 = 원화 상체(torso + seamF)
tm = torso.copy(); _z2 = (XX > 318) & (YY < 345)
_deb = _z2 & (tm[..., 3] > 0) & (SHOULDER_R == 0) & ~(sh3[..., 3] > 60); tm[_deb] = 0
_cl = cv2.morphologyEx((tm[..., 3] > 128).astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))) > 0
_hole = (sh3[..., 3] <= 200) & _cl & (tm[..., 3] < 128) & _z2 & (YY > 280)
_inp = cv2.inpaint(np.ascontiguousarray(tm[..., :3]), _hole.astype(np.uint8) * 255, 5, cv2.INPAINT_TELEA); tm[_hole, :3] = _inp[_hole]; tm[_hole, 3] = 255
_hedge = _hole & (cv2.dilate((tm[..., 3] < 128).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0); tm[_hedge, :3] = (34, 30, 34)   # 메운 곳 바깥 가장자리 = 외곽선
_ga3 = sh3[..., 3:4].astype(np.float32) / 255; _ta3 = tm[..., 3:4].astype(np.float32) / 255; _oa3 = _ga3 + _ta3 * (1 - _ga3)
_rgb3 = (sh3[..., :3] * _ga3 + tm[..., :3] * _ta3 * (1 - _ga3)) / np.maximum(_oa3, 1e-6); _m3 = sh3[..., 3] > 0
tm[_m3, :3] = np.clip(_rgb3[_m3], 0, 255).astype(np.uint8); tm[_m3, 3] = np.clip(_oa3[_m3, 0] * 255, 0, 255).astype(np.uint8)
o_tm = save('torsoM', tm); print('  torsoM: debris', int(_deb.sum()), 'hole', int(_hole.sum()), 'shoulder', int(_m3.sum()))
# 치마: 주먹 밑(주머니 윗덮개·허리띠)은 시트 골반의 주머니를 원화 주머니 위 두 모서리에 맞춰(시트 10,10 → 138,355 · 90,12 → 198,357) — 시트 전체 맞춤은 3/4 휘어짐이 달라 안 맞음
shp = warp(col_match(sheet('hips'), body & (YY >= cut_y)), simil((10, 10), (90, 12), (138, 355), (198, 357)))
skirt = under(under(art(body & (YY >= cut_y) & ~SKIRT_CUT), shp, lab('foreN') & (YY >= cut_y)), bflat, fillN & (YY >= cut_y))   # 밑단 아래 토시·끈은 서 있는 다리로
_bs = BAND_N & (YY >= cut_y); skirt[_bs] = EXT_N[_bs]
o_skirt = save('skirt', skirt)
# 머리+수염 (원화 그대로, 꽁지머리·귀·안경 포함)
o_head = save('head', art(lab('head')))
# 어깨갑: 원화 + 수염(머리) 뒤 가장자리는 껍질 안 inpaint
pinp, pfill = hull_inpaint(lab('pauldron'), lab('head'))
o_pd = save('pauldron', under(art(lab('pauldron')), pinp, pfill))
# 가까운 윗팔(남색 소매): 원화 보이는 곳 + 어깨갑·토시 밑은 시트 윗팔(어깨 → 팔꿈치 축, 색 = 원화 소매)
_nv = lab('upperN') & (np.abs(RA[..., :3].astype(int) - NAVY).max(-1) < 60)   # 원화 소매 조각 중 남색·외곽선만(토시 윗선 밝은 점·띠 조각 뺌)
def arm_piece(nm, top, bot, SH, EL):   # 시트 2 윗팔 조각을 늘이지 않고(배율 1) 아래 둥근 끝 가운데 = 팔꿈치, 위쪽 = 어깨 방향으로 놓음 (10-20 DHL '늘어나는 것 없이 보이는 리소스로')
    a0, a1 = np.array(bot, float), np.array(top, float); u = (np.array(SH, float) - np.array(EL, float)); u /= np.linalg.norm(u)
    return warp(desp(np.array(Image.open(os.path.join(PC, f'p2_{nm}.png')).convert('RGBA'))), simil(a0, a1, EL, np.array(EL, float) + u * np.linalg.norm(a1 - a0)))
uw = arm_piece('upperN2', (24, 19), (24, 101), SH_N, EL_N)   # 가까운 윗팔 = 스카이 시트 2(09:00) 4번: 둥근 끝 사이 82(원화 87) — 위 끝은 큰 어깨갑 밑, 늘이지 않음
o_aU = save('armU', under(art(_nv | (lab('upperN') & (RA[..., :3].mean(-1) < 45))), uw, lab('pauldron') | lab('foreN') | lab('upperN')))
# 가까운 팔뚝+주먹(토시 + 쇠 장갑 주먹, 원화 그대로 — 맨 앞)
o_aL = save('armL', art(lab('foreN') | RING_N))   # 주먹 둘레 어두운 외곽선 2px 포함(움직이면 같이 감)
# 먼 윗팔(남색 소매): 원화 보이는 곳 + 앞 조각(몸 어깨판·토시·칼) 밑은 시트 먼 윗팔(어깨 → 팔꿈치), 색 = 원화 먼 소매 × .9
ufw = arm_piece('upperF2', (24, 21), (24, 107), SH_F, EL_F)   # 먼 윗팔 = 스카이 시트 2 2번: 둥근 끝 사이 86(원화 80, 위 끝은 몸 띠 밑), 늘이지 않음
# 먼 어깨 덮개(pauldronF 뼈, 몸통에 붙음): 먼 소매 둘레의 몸 그림(가죽 띠·크림 판)을 먼 윗팔 위에 한 번 더 — 대기 = 원화, 팔이 돌면 소매가 띠 밑으로 들어감
huF = np.zeros((512, 512), np.uint8); cv2.fillConvexPoly(huF, cv2.convexHull(np.argwhere(lab('upperF'))[:, ::-1].astype(np.int32)), 1)
huF = dil(huF > 0, 8)
o_pF = save('pauldronF', art(body & huF & (YY < 330) & ~SEAM))   # SEAM(날밑·어깨 경계 원화)은 seamF 가 서 있을 때만
o_aF = save('armF', under(art(lab('upperF')), ufw, (body & huF & (YY < 330)) | lab('foreF') | lab('sword') | lab('handF') | lab('head')))   # 몸 쪽 메움은 덮개 밑에서만
# 공격용 먼 윗팔 armFc (nUpper 0.04~0.85): 원화 라벨에 붙어 있던 검은 깃발·가죽 끈 줄·크림·금 조각이 팔과 같이 돌아 찢겨 보였음 → 스카이 시트 2 윗팔만(늘이지 않음)
o_aFc = save('armFc', ufw)   # 시트 윗팔 그대로(원화 조각을 위에 남기면 남색 쐐기·검은 점이 이음매로 보였음)
# 먼 팔뚝(토시): 원화 + 손·손잡이 밑은 껍질 안 inpaint
finp, ffill = hull_inpaint(lab('foreF'), lab('handF') | lab('sword'), 5)
o_fF = save('foreF', under(art(lab('foreF')), finp, ffill))
# 공격용 먼 팔뚝 foreFc(gF 의 fore): 떨어진 작은 조각(손·날밑 경계 크림 줄 — 타격 때 팔뚝 옆에 떠 보였음) 뺌. 대기 foreF 는 원화 그대로
_ff = under(art(lab('foreF')), finp, ffill); _nc, _cc2, _st2, _ = cv2.connectedComponentsWithStats((_ff[..., 3] > 20).astype(np.uint8), connectivity=8)
_big = np.argmax(_st2[1:, 4]) + 1; _ff[(_cc2 != _big) & (_ff[..., 3] > 0)] = 0
OFF['foreFc'] = OFF['foreF']; Image.fromarray(_ff[OFF['foreF'][1]:OFF['foreF'][1] + np.array(Image.open(os.path.join(PARTS, 'foreF.png'))).shape[0], OFF['foreF'][0]:OFF['foreF'][0] + np.array(Image.open(os.path.join(PARTS, 'foreF.png'))).shape[1]]).save(os.path.join(PARTS, 'foreFc.png'))
print('  foreFc: removed', int(sum(_st2[i, 4] for i in range(1, _nc) if i != _big)), 'px in', _nc - 2, 'bits')
# 먼 손(칼 쥔 손, 원화 그대로)
o_fist = save('fistF', art(lab('handF')))
# 망토: 원화 + 몸·팔 밑(가려진 위쪽)은 시트 망토(왼쪽 말린 끝 5,125 → 33,362 · 아래 가운데 100,190 → 100,415)
MC = simil((5, 125), (100, 190), (33, 362), (100, 415)); cw = warp(col_match(sheet('cape'), lab('cape')), MC)
cape = under(art(lab('cape')), cw, body | lab('foreN') | lab('upperN') | lab('pauldron') | lab('legN'))
# 망토 위쪽(팔꿈치·어깨갑 뒤): 시트 망토가 못 덮는 곳은 남색 천 — 팔을 흔들면 팔꿈치 뒤로 배경이 보였음
CB = np.zeros((512, 512), np.uint8); cv2.fillPoly(CB, [np.array([(62, 262), (150, 270), (168, 330), (140, 362), (36, 352)], np.int32)], 1)
cfl, _ = flat_fill(lab('cape') | (CB > 0), (CB > 0) & (lab('foreN') | lab('upperN') | lab('pauldron')))
cape = under(cape, cfl, (CB > 0) & (lab('foreN') | lab('upperN') | lab('pauldron')))
o_cape = save('cape', cape)
# 칼: 원화 + 머리 뒤 칼날은 칼날 띠 좌표(가장자리 맞춤 선 사이 0~1)로 왼쪽 D px 칼날을 옮겨 메움 (무늬 없는 날 — 홈·가장자리 선이 이어짐)
sw = art(lab('sword')); SW0 = sw.copy()   # SW0 = 원화 칼 픽셀(바뀐 곳은 guardArt 로 서 있을 때만 다시 그림)
D = 40.0
yT = lambda x: TOPL[0] * x + TOPL[1]; yB = lambda x: BOTL[0] * x + BOTL[1]
v = (YY - yT(XX)) / (yB(XX) - yT(XX))
# 머리카락 외곽선 조각(칼날 띠 밖)은 칼에서 뺌 — 칼을 돌리면 날 가장자리에 검은 점선으로 붙어 다녔음
gd3 = cv2.warpAffine(desp(np.array(Image.open(os.path.join(PC, 'p3_guard3.png')).convert('RGBA'))), np.array(GEO['p3_guard3']['M'], np.float32), (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
_gsil = cv2.dilate((gd3[..., 3] > 100).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))) > 0
sw[(XX >= 170) & (XX <= 372) & ((v < -0.08) | (v > 1.08)) & ~_gsil] = 0   # 날 띠 밖 조각(머리카락 외곽선·어깨 판 크림 조각)은 칼에서 뺌 — 날밑 둘레까지
hid = (XX >= 170) & (XX <= 372) & (v > -0.1) & (v < 1.1) & (sw[..., 3] < 250) & (RA[..., 3] > 40) & ~lab('handF') & ~lab('foreF')   # 띠 안 빈 곳은 라벨과 상관없이(머리카락 사이 틈까지) 메움 — 대기엔 머리가 덮음
# 띠 좌표 v 는 그대로, 날 길이 방향으로는 머리카락 왼쪽(x 168~174)의 단면 평균을 늘려 씀 → 홈·가장자리가 곧게 이어짐(왼쪽 D px 복사는 날이 좁아지며 홈이 계단처럼 어긋났음)
cols = []; swc = sw.copy()   # 단면 뽑을 원본(아래 칼날 다시 그릴 때도 같은 단면)
for xr in range(168, 175):
    ys_r = yT(xr) + v * (yB(xr) - yT(xr)); cols.append(cv2.remap(sw.astype(np.float32), np.full_like(ys_r, xr, np.float32), ys_r.astype(np.float32), cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)))
src = np.mean(cols, 0); put = hid & (src[..., 3] > 200); sw[put] = np.clip(src[put], 0, 255).astype(np.uint8); hid &= ~put
print('  blade fill left', int(hid.sum()), 'px')
# 날밑(시트 3 3번 — 원화와 같은 각도로 다시 그린 날밑, SIFT 맞춤): ①날밑 둘레에서 칼 띠(날·손잡이·폼멜)·날밑 모양 밖의 원화 '칼' 픽셀은 몸 판·끈 조각 → 칼에서 뺌
#   ②날밑 모양 안인데 원화에서 손·어깨 판에 가려 빈 곳은 시트 날밑으로 — 칼을 휘두르면 날밑 왼쪽 아래가 찢겨 보였음(10-20 08:03)
_band = (v > -0.12) & (v < 1.12) & (XX < 372)
_ax = (HA1 - HA0) / np.linalg.norm(HA1 - HA0); _al = (XX - HA0[0]) * _ax[0] + (YY - HA0[1]) * _ax[1]; _lat = (XX - HA0[0]) * -_ax[1] + (YY - HA0[1]) * _ax[0]
_hband = (_al > 0) & (np.abs(_lat) < 12)
_near = cv2.dilate(_gsil.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))) > 0
_gcut = _near & ~_gsil & ~_band & ~_hband & ~poly_(PO_['pommel']) & (sw[..., 3] > 0); sw[_gcut] = 0
# seamF: 원화의 날밑·어깨 경계 픽셀(위에서 바꾸거나 뺀 곳) — 서 있을 때·달릴 때만 칼 위에 그려 대기 = 원화, 공격(칼이 움직임) 땐 안 그림
_sm = (SEAM | _gcut) & (RA[..., 3] > 40); o_seam = save('seamF', art(_sm)); print('  seamF', int(_sm.sum()), 'px')
_gfill = (gd3[..., 3] > 200) & (_gsil & ~_band | (sw[..., 3] < 200)) & (cv2.dilate((RA[..., 3] > 40).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0); sw[_gfill] = gd3[_gfill]   # 날밑 = 시트 날밑 통째(움직일 때 깨끗) — 서 있을 땐 guardArt(원화)가 위에
# 칼날(머리 오른쪽 ~ 날밑): 움직일 때 쓰는 칼 그림은 머리 왼쪽 깨끗한 단면(x168~174 평균)을 날 방향으로 그대로 이어 붙인 날 하나로 — 원화 조각(머리·날밑 사이)·시트 칼 뿌리를
#   섞으면 홈 위치·폭이 달라 '깨진 칼'로 보였음(10-20 09:15 DHL). 서 있을 땐 guardArt 가 원화 칼날을 위에 그림 (칼 길이·폭 = 원화 그대로)
# 원화 칼날은 머리 오른쪽 부분이 머리 왼쪽보다 6.5~11px 아래로 어긋나 그려져 있음(머리에 가려 안 보이던 이음매) → 움직일 땐 그 어긋남이 '깨진 칼'
#   → 윗날 선을 머리 뒤(x170~260)에서 아주 완만히 휘어(최대 4°) 오른쪽 원화 윗날(x310~366)보다 살짝 안쪽으로 지나가게 → 날 하나로 매끈, 대기엔 원화(guardArt)가 덮음
K_TOP, W_TOP = 0.0726, 90.0
_off = np.where(XX < 170, 0.0, np.where(XX < 170 + W_TOP, K_TOP * (XX - 170.0) ** 2 / (2 * W_TOP), K_TOP * (XX - 170.0 - W_TOP / 2)))
yT2 = yT(XX) + _off; v2 = (YY - yT2) / (yB(XX) - yT2)
cols2 = []
for xr in range(168, 175):
    ys_r = yT(xr) + v2 * (yB(xr) - yT(xr)); cols2.append(cv2.remap(swc.astype(np.float32), np.full_like(ys_r, xr, np.float32), ys_r.astype(np.float32), cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)))
src2 = np.mean(cols2, 0)
_gcore = gd3[..., 3] > 200
_root = (XX >= 170) & (_al < -1) & ~_gcore & (((v > -0.12) & (v < 1.12)) | ((v2 > -0.12) & (v2 < 1.12)))
sw[_root] = 0; _rp = _root & (v2 > -0.12) & (v2 < 1.12) & (src2[..., 3] > 4); sw[_rp] = np.clip(src2[_rp], 0, 255).astype(np.uint8)
# 날밑 마무리: 날밑 둘레 고리(_gsil 안, 날밑 본체 밖)에 남은 원화 조각(금색·크림 부스러기 — 휘두를 때 날밑 아래가 찢겨 보였음) 지우고
#   시트 날밑을 자기 알파 그대로 칼날 위에 덮어 그림(날이 날밑 홈으로 들어가는 모양) — 원화 실루엣 밖(배경) 날밑은 예전처럼 뺌
_gring = _gsil & ~_gcore & ~_hband & ~poly_(PO_['pommel']) & ~_rp
sw[_gring] = 0
_ga = gd3[..., 3:4].astype(np.float32) / 255 * (cv2.dilate((RA[..., 3] > 40).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)[..., None]
_sa = sw[..., 3:4].astype(np.float32) / 255; _oa = _ga + _sa * (1 - _ga)
_rgb = (gd3[..., :3] * _ga + sw[..., :3] * _sa * (1 - _ga)) / np.maximum(_oa, 1e-6)
_gc = _gsil & (gd3[..., 3] > 0); sw[_gc, :3] = np.clip(_rgb[_gc], 0, 255).astype(np.uint8); sw[_gc, 3] = np.clip(_oa[_gc, 0] * 255, 0, 255).astype(np.uint8)
print('  guard: cut', int(_gcut.sum()), 'filled', int(_gfill.sum()), 'ring', int(_gring.sum()), 'blade', int(_root.sum()))
o_sw_art = save('_sword_art', sw); os.remove(os.path.join(PARTS, '_sword_art.png'))
ang_tip = math.atan2(UT[1], UT[0]); rot_deg = math.degrees(-math.pi / 2 - ang_tip)
UPS = 2
sw2 = cv2.resize(sw, None, fx=UPS, fy=UPS, interpolation=cv2.INTER_LANCZOS4); sw2[..., 3] = np.clip(cv2.resize(sw[..., 3], None, fx=UPS, fy=UPS, interpolation=cv2.INTER_LINEAR), 0, 255)
Rm = cv2.getRotationMatrix2D((float(G[0] * UPS), float(G[1] * UPS)), -rot_deg, 1.0)
WS, HS = 800, 2000; Rm[0, 2] += WS / 2 - G[0] * UPS; Rm[1, 2] += 1640 - G[1] * UPS
swv = cv2.warpAffine(sw2, Rm, (WS, HS), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
ys, xs = np.nonzero(swv[..., 3] > 0); x0, y0 = max(0, xs.min() - 2), max(0, ys.min() - 2); assert xs.min() > 0 and ys.min() > 0 and xs.max() < WS - 1 and ys.max() < HS - 1, '칼 그림이 캔버스 밖'; swv = swv[y0:ys.max() + 3, x0:xs.max() + 3]
Image.fromarray(swv).save(os.path.join(PARTS, 'weapon.png'))
vpt = lambda p: (Rm[:, :2] @ (np.array(p, float) * UPS) + Rm[:, 2]) - np.array([x0, y0])
# guardArt: 원화 칼 픽셀 중 칼 그림에서 바뀐 곳(날밑·경계 조각) — 칼 뼈에 붙여 서 있을 때·달릴 때만 칼 위에 그림 → 대기 = 원화, 휘두를 땐 깨끗한 시트 날밑
_gm = (SW0[..., 3] > 0) & ((np.abs(SW0.astype(int) - sw.astype(int)).max(-1) > 8) | (cv2.dilate((_root | _gsil | _gcut).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0))   # 바뀐 곳 + 날밑·뿌리 둘레 통째(점점이 겹치면 줄무늬)
ga = np.zeros_like(SW0); ga[_gm] = SW0[_gm]
ga2 = cv2.resize(ga, None, fx=UPS, fy=UPS, interpolation=cv2.INTER_LANCZOS4); ga2[..., 3] = np.clip(cv2.resize(ga[..., 3], None, fx=UPS, fy=UPS, interpolation=cv2.INTER_LINEAR), 0, 255)
gav = cv2.warpAffine(ga2, Rm, (WS, HS), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))[y0:y0 + swv.shape[0], x0:x0 + swv.shape[1]]
Image.fromarray(gav).save(os.path.join(PARTS, 'guardArt.png')); print('  guardArt', int(_gm.sum()), 'px')
W_PIV = vpt(G); W_TIP = vpt(TIP); W_GUARD = vpt(HA0); W_POM = vpt(HA1)
print('  sword vertical: tip', np.round(W_TIP, 1), 'grip', np.round(W_PIV, 1), 'rot', round(rot_deg, 2))
# 다리: 서 있을 때 = 원화 다리(바짓단 아래 바지 + 부츠) 그대로 / 달릴 때 = 먼 부츠(앞코 오른쪽) + 바지 통(shinP)
def stand_leg(sd, lm):   # 서 있는 다리 = 원화 다리 + 밑단 아래 몸 픽셀(토시 통째) + 밑단 위 6px 남색 바지(치마 밑에 숨음 — 숨쉬기로 치마가 올라가도 틈 없음)
    m = lm | legTop[sd]; a = art(m); hy = hem_y[sd]
    _legc = (m & (YY >= hy) & (YY <= hy + 4)).any(0)   # 다리 조각 윗부분이 있는 칸
    ext = (YY >= hy - 6) & (YY < hy) & _legc[None, :] & body & ~SKIRT_CUT & (RA[..., 3] > 200) & (XX >= HEMX[sd][0]) & (XX <= HEMX[sd][1])   # 그 칸의 치마 밑(치마가 덮는 곳만)
    f = np.zeros_like(RA); f[..., :3] = np.clip(NAVY[None, None] + np.random.default_rng(5).normal(0, 2.0, (512, 512, 1)), 0, 255).astype(np.uint8); f[..., 3] = np.where(ext, 255, 0)
    return under(a, f, ext)
o_lN = save('bootStandN', stand_leg('near', lab('legN'))); o_lF = save('bootStandF', stand_leg('far', lab('legF')))
# 달리는 부츠 = 시트 먼 부츠(깨끗한 한 장, 앞코 오른쪽, 남색 목까지) → 원화 먼 부츠 바닥 양 끝에 맞춤(시트 0,48 → 303,471 · 69,48 → 382,471, 1.15배) · 색 = 원화 부츠
#   (원화 다리를 밑단 아래에서 잘라 쓰면 목의 금 장식이 잘려 찢어진 조각처럼 보였음)
# 달리는 부츠(쪽별) = 시트 부츠 그대로 그림 크기 1.1배(늘이지 않음, 원화 부츠 길이에 맞춤) · 색 = 원화 부츠. 발목 점 = 정강이 판 아래(시트 x 26, 밑창 위 20px)
#   엔진 opt-in legs.tube.runBoot 으로 달릴 때만(서 있을 땐 원화 다리) — 10-20 07:25 DHL '달리기 자세 어색': 원화 다리를 잘라 만든 부츠가 돌며 찢긴 장식·아래로 꺾인 발끝
RBK = 1.1
def run_boot(nm, lm):
    b = col_match(sheet(nm), lm & (YY >= 446)); H_, W_ = b.shape[:2]; b = cv2.resize(b, (int(round(W_ * RBK)), int(round(H_ * RBK))), interpolation=cv2.INTER_LANCZOS4)
    ys, xs = np.nonzero(b[..., 3] > 128); sole = ys.max(); piv = (26 * RBK, sole - 20.0)
    Image.fromarray(b).save(os.path.join(PARTS, f'{nm}Run.png'))
    bot = {x: ys[xs == x].max() for x in range(xs.min(), xs.max() + 1) if (xs == x).any()}; xl, xr = min(bot), max(bot)
    cols = sorted(set(int(round(xl + (xr - xl) * f)) for f in (0.03, 0.25, 0.5, 0.75, 0.97)))
    return piv, [[round(float(x - piv[0]), 1), round(float(bot[x] - piv[1]), 1)] for x in cols]
RB = {'near': run_boot('bootN', lab('legN')), 'far': run_boot('bootF', lab('legF'))}
bf = art(lab('legF') & (YY >= 446))   # (옛 bootRun — 쓰지 않음, 밑창 점 계산용)
def sole_pts(m, ankle, ground=None):
    ys, xs = np.nonzero(m); xl, xr = xs.min(), xs.max(); bot = {x: ys[xs == x].max() for x in range(xl, xr + 1) if (xs == x).any()}
    xlow = max(bot, key=lambda x: bot[x]); cols = sorted(set([int(round(xl + (xr - xl) * f)) for f in (0.02, 0.2, 0.8, 0.98)] + [xlow]))
    lift = 0.0 if ground is None else float(ground - bot[xlow])
    return [[float(x - ankle[0]), float(bot[x] - ankle[1] + lift)] for x in cols if x in bot]
_c = RA[(lab('legN') | lab('legF') | lab('body')) & (YY >= 425) & (YY <= 450) & (RA[..., 3] > 200)][:, :3].astype(int); _l = _c.mean(1)
tr_col = np.median(_c[(_c[:, 2] > _c[:, 0] + 4) & (_l > 35) & (_l < 110)], 0)   # 바짓단 밑 남색 바지(부츠 목이 밑단까지 와서 보이는 바지는 아주 조금)
print('  trouser colour', tr_col)
TW, TH = 44, 50; xs_ = (np.arange(TW) + .5) / TW
edge = np.clip(1 - np.minimum(xs_, 1 - xs_) / .2, 0, 1) ** 1.5; hl = np.exp(-((xs_ - .36) / .1) ** 2) * .6
base = tr_col.astype(np.float32); col = base[None] * (1 - edge[:, None]) + base[None] * .72 * edge[:, None]; col = col * (1 - hl[:, None]) + base[None] * 1.18 * hl[:, None]
tub = np.zeros((TH, TW, 4), np.float32); tub[..., :3] = col[None] + np.random.default_rng(9).normal(0, 2.0, (TH, TW, 1))
olm = (np.arange(TW) < 2) | (np.arange(TW) >= TW - 2); tub[:, olm, :3] = (24, 24, 32)
yy2 = np.arange(TH)[:, None]; tub[..., 3] = 255 * np.clip((yy2 - 1) / 5, 0, 1) * np.clip((TH - 1 - yy2) / 4, 0, 1)
Image.fromarray(np.clip(tub, 0, 255).astype(np.uint8)).save(os.path.join(PARTS, 'shinP.png'))

# ---------------- 표정·깜빡임 (23 faces 방식: 시트 표정 = 무표정과 다른 곳 + 5px 만 원화 얼굴 자리로) ----------------
FACE_N = ['happy', 'angry', 'focus', 'shout', 'effort']; BLINK_N = ['half', 'closed']
SRC = {**{n: f'face_{n}' for n in FACE_N}, 'half': 'blink_half', 'closed': 'blink_closed'}
neu = sheet('face_neutral').astype(np.int16); U_ = np.zeros(neu.shape[:2], bool)
for n in FACE_N + BLINK_N: U_ |= np.abs(sheet(SRC[n]).astype(np.int16) - neu).max(2) > 40
reg = cv2.dilate(U_.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
MF = np.array(GEO['face_neutral']['M'], np.float32)
face = (cv2.warpAffine(reg, MF, (512, 512), flags=cv2.INTER_NEAREST) > 0) & lab('head')
fm = np.clip(cv2.GaussianBlur(cv2.erode(face.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (5, 5), 1.0) * 1.15, 0, 1)
hb = np.array(Image.open(os.path.join(PARTS, 'head.png'))); hx0, hy0 = OFF['head']; hh, hw = hb.shape[:2]
# 색 맞춤: 시트 무표정 얼굴(원화 자리로 옮긴 것)과 원화를 얼굴 덧댐 자리에서 채널별 평균·편차로 맞춤 — 시트 피부가 원화보다 주황(덧댐이 얼룩으로 보였음)
wn = cv2.warpAffine(sheet('face_neutral'), MF, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0)).astype(np.float32); cm = face & (wn[..., 3] > 200) & (RA[..., 3] > 200)
CA = [(RA[..., c][cm].astype(np.float32).std() / max(1.0, wn[..., c][cm].std()), 0.0) for c in range(3)]
CA = [(a, float(RA[..., c][cm].mean() - a * wn[..., c][cm].mean())) for c, (a, _) in enumerate(CA)]
print('  face colour fit', [(round(a, 3), round(b, 1)) for a, b in CA])
for n in FACE_N + BLINK_N:
    wf = cv2.warpAffine(sheet(SRC[n]), MF, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0)).astype(np.float32)
    for c in range(3): wf[..., c] = np.clip(wf[..., c] * CA[c][0] + CA[c][1], 0, 255)
    al = fm * (wf[..., 3] / 255.0)
    o_ = RA.astype(np.float32).copy(); o_[..., :3] = o_[..., :3] * (1 - al[..., None]) + wf[..., :3] * al[..., None]
    fc = o_[hy0:hy0 + hh, hx0:hx0 + hw].astype(np.uint8); fc[..., 3] = hb[..., 3]
    fc[..., :3] = np.where((face[hy0:hy0 + hh, hx0:hx0 + hw] == 0)[..., None], hb[..., :3], fc[..., :3])
    Image.fromarray(fc).save(os.path.join(PARTS, f'face_{n}.png'))
print('  face patch px', int(face.sum()))

# ---------------- 뼈·조각 정의 ----------------
SC = 2.0
def piv(name, p): o = np.array(OFF[name], float); q = np.array(p, float) - o; return [round(float(q[0]), 1), round(float(q[1]), 1)]
parts = {}
def P_(name, at, **kw): parts[name] = dict({'src': f'parts/{name}.png', 'pivot': piv(name, at), 'scale': SC}, **kw)
P_('torso', HIP); P_('skirt', HIP, mesh={'cols': 8, 'rows': 6}); P_('head', NECK)
P_('pauldron', SH_N); P_('armU', SH_N, elbow=piv('armU', EL_N)); P_('armL', EL_N, fist=piv('armL', WR_N + (WR_N - EL_N) * .2))
P_('armF', SH_F, elbow=piv('armF', EL_F)); P_('armFc', SH_F, elbow=piv('armFc', EL_F)); P_('torsoM', HIP); P_('foreF', EL_F); P_('fistF', WR_F); P_('pauldronF', SH_F); P_('seamF', HIP)
CAPE_P = np.array([118.0, 300.0])   # 망토 뿌리(가까운 어깨 뒤, 팔·어깨갑에 가려짐) — 엔진 cape 뼈가 달리기 속도만큼 뒤로 젖히고 메시가 펄럭임
P_('cape', CAPE_P, mesh={'cols': 6, 'rows': 7})
parts['guardArt'] = {'src': 'parts/guardArt.png', 'pivot': [round(float(W_PIV[0]), 1), round(float(W_PIV[1]), 1)], 'scale': SC / UPS}
parts['weapon'] = {'src': 'parts/weapon.png', 'pivot': [round(float(W_PIV[0]), 1), round(float(W_PIV[1]), 1)], 'scale': SC / UPS,
                   'tip': [round(float(W_TIP[0]), 1), round(float(W_TIP[1]), 1)], 'tips': [[round(float(W_TIP[0]) - 6 * UPS, 1), round(float(W_TIP[1]) + 10 * UPS, 1)], [round(float(W_TIP[0]) + 14 * UPS, 1), round(float(W_TIP[1]) + 10 * UPS, 1)]],
                   'guard': [round(float(W_GUARD[0]), 1), round(float(W_GUARD[1]), 1)], 'pommel': [round(float(W_POM[0]), 1), round(float(W_POM[1]), 1)]}
for n in FACE_N + BLINK_N: parts[f'face_{n}'] = {'src': f'parts/face_{n}.png', 'pivot': parts['head']['pivot'], 'scale': SC}
for nm, sd in [('bootStandN', 'near'), ('bootStandF', 'far')]: P_(nm, LEG[sd]['ankle'])
for _sd, _nm in (('near', 'bootNRun'), ('far', 'bootFRun')): parts[_nm] = {'src': f'parts/{_nm}.png', 'pivot': [round(RB[_sd][0][0], 1), round(RB[_sd][0][1], 1)], 'scale': SC}
parts['shinP'] = {'src': 'parts/shinP.png', 'pivot': [0, 0], 'scale': 1}
WEAPON_ANG = math.atan2(UT[1], UT[0]) + math.pi / 2   # 세로 칼 그림 뼈의 세계 각(그림 위쪽 → 칼끝)
ARML_REST = 0.3   # 엔진이 서 있을 때 자유 팔뚝을 −0.3 rad 굽힘(armL.ar) → 뼈 rot 에 +0.3 을 넣어 대기 = 원화
world = {'root': (O, 0.0), 'hip': (HIP, 0.0), 'skirt': (HIP, 0.0), 'torso': (HIP, 0.0), 'head': (NECK, 0.0), 'pauldron': (SH_N, 0.0), 'armU': (SH_N, 0.0), 'armL': (EL_N, ARML_REST),
         'armF': (SH_F, 0.0), 'foreF': (EL_F, 0.0), 'fistF': (WR_F, 0.0), 'weapon': (G, WEAPON_ANG), 'cape': (CAPE_P, 0.0), 'scarf': (NECK, 0.0), 'pouch': (HIP, 0.0), 'pauldronF': (SH_F, 0.0), 'foreFb': (WR_F, 0.0), 'seamF': (HIP, 0.0), 'guardArt': (G, WEAPON_ANG)}
BONES = [('root', None), ('hip', 'root'), ('skirt', 'hip'), ('torso', 'hip'), ('head', 'torso'), ('armF', 'torso'), ('foreF', 'armF'), ('fistF', 'foreF'), ('weapon', 'fistF'),
         ('armU', 'torso'), ('armL', 'armU'), ('pauldron', 'torso'), ('cape', 'torso'), ('scarf', 'torso'), ('pouch', 'hip'), ('pauldronF', 'torso'), ('foreFb', 'torso'), ('seamF', 'torso'), ('guardArt', 'weapon')]
bones = []
for name, parent in BONES:
    if parent is None: bones.append({'name': 'root', 'parent': None, 'pos': [0, 0]}); continue
    (pw_, pa), (cw_, ca) = world[parent], world[name]; dv = (np.array(cw_) - np.array(pw_)) * SC; c, s = math.cos(-pa), math.sin(-pa)
    b = {'name': name, 'parent': parent, 'pos': [round(c * dv[0] - s * dv[1], 1), round(s * dv[0] + c * dv[1], 1)]}
    if abs(ca - pa) > 1e-4: b['rot'] = round(ca - pa, 4)
    if name in parts: b['part'] = name
    bones.append(b)
# armL: 뼈 rot +0.3 과 엔진 대기 굽힘 −0.3 이 상쇄 → 그림은 원화 방향 그대로 저장

# ---------------- 다리 (카르덴식: 바지 통 + 부츠, 서 있을 땐 원화 다리) ----------------
TUBE_K = 1.2   # 바지 통 굵기 1.8 → 1.2 (10-20 13:47): 서 있을 때 가까운 다리 통이 원화 끈·부츠 사이 홈(배경)으로 삐져나와 어두운 쐐기로 보였음(원화 밖 픽셀 119 → 16) — 달릴 땐 달리기 부츠가 거의 다 덮어 차이 없음(1.8·1.5·1.2 비교)
hipY = SC * (LEG['near']['hip'][1] - HIP[1])
LEGL = float(np.linalg.norm(LEG['near']['ankle'] - LEG['near']['hip'])) * SC   # 엉덩이→발목(리그) — 짧은 드워프 다리: 허벅지·정강이 = 반씩 + 5%
legs = {'hip': [0, round(hipY, 1)], 'thigh': round(LEGL * .525, 1), 'shin': round(LEGL * .525, 1),
        'thighImg': {'part': 'shinP', 'a': [22, 0], 'b': [22, 46], 'w': 0.001}, 'shinImg': {'part': 'shinP', 'a': [22, 0], 'b': [22, 46], 'w': 0.001},
        'boot': {'part': 'bootFRun', 'sole': RB['far'][1], 'ankleRange': [-1.7, 1.7]},   # 발목 범위 넓게 — 짧은 다리라 정강이(통) 각이 크게 흔들려도 부츠는 땅과 거의 평평(좁으면 부츠가 통을 따라 돌아 발끝이 아래로 꺾임)
        'tube': {'part': 'shinP', 'a': [22, 0], 'b': [22, 46], 'k': TUBE_K, 'runBoot': True}}
for sd, nm, lm in [('near', 'bootStandN', lab('legN')), ('far', 'bootStandF', lab('legF'))]:
    legs[sd] = {'x': round(SC * (LEG[sd]['hip'][0] - HIP[0]), 1), 'shade': 0, 'thighImg': legs['thighImg'], 'shinImg': legs['shinImg'], 'runBoot': 'bootNRun' if sd == 'near' else 'bootFRun',
                'stand': {'fade': [0.12, 0.4], 'boot': {'part': nm, 'sole': sole_pts(lm, LEG[sd]['ankle'], O[1])}}}
idle = {sd: round(SC * (LEG[sd]['ankle'][0] - LEG[sd]['hip'][0]), 1) for sd in ('near', 'far')}
# 그리는 순서 (뒤 → 앞): 망토 · 먼 다리 · 가까운 다리 · 상체 · 치마 · 먼 윗팔(소매) · 먼 어깨 덮개(몸 띠) · 먼 팔뚝 · 칼(칼날은 머리 뒤) · 가까운 윗팔 · 어깨갑 · 머리+수염(+표정) · 먼 손 · 가까운 팔뚝+주먹(맨 앞 — 팔꿈치 레이어 > 어깨)
draw = ['cape', 'legFar', 'legNear', 'torso', 'skirt', 'armF', 'pauldronF', 'foreF', 'weapon', 'guardArt', 'seamF', 'armU', 'pauldron', 'head', 'fistF', 'armL']
rig = {'name': 'palome-sky', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': parts, 'bones': bones, 'legs': legs, 'draw': draw, 'hidden': [], 'faces': {n: f'face_{n}' for n in FACE_N},
       'blinkFaces': {'half': 'face_half', 'closed': 'face_closed'}, 'idleStance': idle,
       'gait': {'stance': 0.18, 'strideBase': 14, 'strideK': 0.06, 'hipBase': 0, 'bob': 6, 'lean': 0.06, 'waddle': 0.02, 'headBob': 3, 'kneeLift': 0.2, 'heelKick': 0.03, 'dropCap': 12,
                'swingReach': 0.05, 'landAng': -0.04, 'angK': 0.2, 'elbowRun': 0.3, 'foreRun': 0.3, 'armSwing': 0.08, 'armBias': 0.0, 'headRun': 0.06},   # 가까운 팔은 배 앞을 가로지름 → 조금만 흔듦(배·주머니가 덜 드러남) · elbowRun .3 = 엔진 대기 팔뚝 굽힘(−.3)과 같아 달려도 팔뚝 각이 대기 그대로
       'hemRun': {'lift': 8, 'knee': 0.5, 'heel': 0.3, 'reach': 0.2}, 'hemLimit': {'up': 0.25, 'x': 0.3}, 'hemGain': 0.15, 'footReach': 0.97,
       'follow': [{'bone': 'pauldron', 'src': 'armU', 'k': 0.3}], 'skirtFollow': 0.7, 'carrySwing': 0.15, 'wristRange': 0.2, 'dropLift': 10,
       'bounce': [], 'metrics': {'bodyHeight': round(2 * (478 - 111)), 'note': 'rig units; 머리카락 위(y111)~발바닥(478) ×2, 칼 제외'},
       'ui': {'attack': 'smash', 'touch': 'hop'},   # 트레일 기본(위 → 아래) = 내려찍기
       'gameRef': {'refOrigin': [round(float(O[0] - (HIP[0] - 251.5)), 1), float(O[1])], 'refScale': 2.0, 'refLift': 0,
                   'note': '게임 그림 char_0029.png(512) = 원화(md5 같음). x = 도감 칸(fitArt 중심 251.5, index.html measureBox 와 같은 계산)에서 골반(hip x 268)이 가운데 (9 팔로메와 같은 규칙)'},
       'note': '29 스카이아크 팔로메 v1(대기·달리기·한 손 내려찍기). 9 러스트 팔로메 v1.1 구조(드워프 몸, 먼 팔이 칼을 어깨에 멤, 칼날 머리 뒤) + 망토. 조각 = 원화를 부품별로 나눔(seg29.py) + 가려진 곳만 시트·inpaint 로 메움'}
if os.path.exists(os.path.join(HERE, 'attack_sky29.py')): exec(open(os.path.join(HERE, 'attack_sky29.py'), encoding='utf-8').read())   # 한 손 내려찍기(9 v1.1 지렛대)
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(PARTS)): _h.update(fn.encode()); _h.update(open(os.path.join(PARTS, fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_sky29.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['palome-sky']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(parts), 'parts, version', rig['version'], 'idle', idle, 'legs x', legs['near']['x'], legs['far']['x'], 'hipY', legs['hip'])
