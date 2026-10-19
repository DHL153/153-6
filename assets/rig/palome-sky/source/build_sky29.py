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
body = body & ~_frag; print('  shoulder fragments removed', int(_frag.sum()), 'px')
bflat2, fillO = flat_fill(body, (OCC | _frag) & (SHOULDER_R > 0))   # 그 밖의 앞 조각(칼 날밑·손잡이·먼 토시·수염) 밑도 시트가 못 덮는 곳은 남색 천 — 칼을 들면 날밑 자리에 배경 구멍·찢어진 조각이 보였음
_OK = (~_zone | (SHOULDER_R > 0)) & (YY < cut_y + OVL)
torso = under(under(under(art(body & (YY < cut_y + OVL)), stw, (OCC | _frag) & _OK), bflat, fillN & (YY < cut_y + OVL)), bflat2, fillO & (YY < cut_y + OVL))
o_torso = save('torso', torso)
# 치마: 주먹 밑(주머니 윗덮개·허리띠)은 시트 골반의 주머니를 원화 주머니 위 두 모서리에 맞춰(시트 10,10 → 138,355 · 90,12 → 198,357) — 시트 전체 맞춤은 3/4 휘어짐이 달라 안 맞음
shp = warp(col_match(sheet('hips'), body & (YY >= cut_y)), simil((10, 10), (90, 12), (138, 355), (198, 357)))
skirt = under(under(art(body & (YY >= cut_y)), shp, lab('foreN') & (YY >= cut_y)), bflat, fillN & (YY >= cut_y))
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
uw = arm_piece('upperN2', (22, 19), (22, 101), SH_N, EL_N)   # 가까운 윗팔(시트 2 4번): 둥근 끝 사이 82(원화 87) — 위 끝은 큰 어깨갑 밑
o_aU = save('armU', under(art(_nv | (lab('upperN') & (RA[..., :3].mean(-1) < 45))), uw, lab('pauldron') | lab('foreN') | lab('upperN')))
# 가까운 팔뚝+주먹(토시 + 쇠 장갑 주먹, 원화 그대로 — 맨 앞)
o_aL = save('armL', art(lab('foreN')))
# 먼 윗팔(남색 소매): 원화 보이는 곳 + 앞 조각(몸 어깨판·토시·칼) 밑은 시트 먼 윗팔(어깨 → 팔꿈치), 색 = 원화 먼 소매 × .9
ufw = arm_piece('upperF2', (26, 19), (26, 108), SH_F, EL_F)   # 먼 윗팔(시트 2 2번): 둥근 끝 사이 89(원화 80, 위 끝은 몸 띠 밑) · 아래 열린 소매 끝은 토시 밑
# 먼 어깨 덮개(pauldronF 뼈, 몸통에 붙음): 먼 소매 둘레의 몸 그림(가죽 띠·크림 판)을 먼 윗팔 위에 한 번 더 — 대기 = 원화, 팔이 돌면 소매가 띠 밑으로 들어감
huF = np.zeros((512, 512), np.uint8); cv2.fillConvexPoly(huF, cv2.convexHull(np.argwhere(lab('upperF'))[:, ::-1].astype(np.int32)), 1)
huF = dil(huF > 0, 8)
o_pF = save('pauldronF', art(body & huF & (YY < 330)))
o_aF = save('armF', under(art(lab('upperF')), ufw, (body & huF & (YY < 330)) | lab('foreF') | lab('sword') | lab('handF') | lab('head')))   # 몸 쪽 메움은 덮개 밑에서만
# 먼 팔뚝(토시): 원화 + 손·손잡이 밑은 껍질 안 inpaint
finp, ffill = hull_inpaint(lab('foreF'), lab('handF') | lab('sword'), 5)
o_fF = save('foreF', under(art(lab('foreF')), finp, ffill))
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
sw = art(lab('sword'))
D = 40.0
yT = lambda x: TOPL[0] * x + TOPL[1]; yB = lambda x: BOTL[0] * x + BOTL[1]
v = (YY - yT(XX)) / (yB(XX) - yT(XX))
# 머리카락 외곽선 조각(칼날 띠 밖)은 칼에서 뺌 — 칼을 돌리면 날 가장자리에 검은 점선으로 붙어 다녔음
sw[(XX >= 170) & (XX <= 340) & ((v < -0.12) | (v > 1.12))] = 0
hid = (XX >= 170) & (XX <= 372) & (v > -0.1) & (v < 1.1) & (sw[..., 3] < 250) & (RA[..., 3] > 40) & ~lab('handF') & ~lab('foreF')   # 띠 안 빈 곳은 라벨과 상관없이(머리카락 사이 틈까지) 메움 — 대기엔 머리가 덮음
# 띠 좌표 v 는 그대로, 날 길이 방향으로는 머리카락 왼쪽(x 168~174)의 단면 평균을 늘려 씀 → 홈·가장자리가 곧게 이어짐(왼쪽 D px 복사는 날이 좁아지며 홈이 계단처럼 어긋났음)
cols = []
for xr in range(168, 175):
    ys_r = yT(xr) + v * (yB(xr) - yT(xr)); cols.append(cv2.remap(sw.astype(np.float32), np.full_like(ys_r, xr, np.float32), ys_r.astype(np.float32), cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)))
src = np.mean(cols, 0); put = hid & (src[..., 3] > 200); sw[put] = np.clip(src[put], 0, 255).astype(np.uint8); hid &= ~put
print('  blade fill left', int(hid.sum()), 'px')
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
W_PIV = vpt(G); W_TIP = vpt(TIP); W_GUARD = vpt(HA0); W_POM = vpt(HA1)
print('  sword vertical: tip', np.round(W_TIP, 1), 'grip', np.round(W_PIV, 1), 'rot', round(rot_deg, 2))
# 다리: 서 있을 때 = 원화 다리(바짓단 아래 바지 + 부츠) 그대로 / 달릴 때 = 먼 부츠(앞코 오른쪽) + 바지 통(shinP)
o_lN = save('bootStandN', art(lab('legN'))); o_lF = save('bootStandF', art(lab('legF')))
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
P_('armF', SH_F, elbow=piv('armF', EL_F)); P_('foreF', EL_F); P_('fistF', WR_F); P_('pauldronF', SH_F)
CAPE_P = np.array([118.0, 300.0])   # 망토 뿌리(가까운 어깨 뒤, 팔·어깨갑에 가려짐) — 엔진 cape 뼈가 달리기 속도만큼 뒤로 젖히고 메시가 펄럭임
P_('cape', CAPE_P, mesh={'cols': 6, 'rows': 7})
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
         'armF': (SH_F, 0.0), 'foreF': (EL_F, 0.0), 'fistF': (WR_F, 0.0), 'weapon': (G, WEAPON_ANG), 'cape': (CAPE_P, 0.0), 'scarf': (NECK, 0.0), 'pouch': (HIP, 0.0), 'pauldronF': (SH_F, 0.0), 'foreFb': (WR_F, 0.0)}
BONES = [('root', None), ('hip', 'root'), ('skirt', 'hip'), ('torso', 'hip'), ('head', 'torso'), ('armF', 'torso'), ('foreF', 'armF'), ('fistF', 'foreF'), ('weapon', 'fistF'),
         ('armU', 'torso'), ('armL', 'armU'), ('pauldron', 'torso'), ('cape', 'torso'), ('scarf', 'torso'), ('pouch', 'hip'), ('pauldronF', 'torso'), ('foreFb', 'torso')]
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
hipY = SC * (LEG['near']['hip'][1] - HIP[1])
LEGL = float(np.linalg.norm(LEG['near']['ankle'] - LEG['near']['hip'])) * SC   # 엉덩이→발목(리그) — 짧은 드워프 다리: 허벅지·정강이 = 반씩 + 5%
legs = {'hip': [0, round(hipY, 1)], 'thigh': round(LEGL * .525, 1), 'shin': round(LEGL * .525, 1),
        'thighImg': {'part': 'shinP', 'a': [22, 0], 'b': [22, 46], 'w': 0.001}, 'shinImg': {'part': 'shinP', 'a': [22, 0], 'b': [22, 46], 'w': 0.001},
        'boot': {'part': 'bootFRun', 'sole': RB['far'][1], 'ankleRange': [-1.7, 1.7]},   # 발목 범위 넓게 — 짧은 다리라 정강이(통) 각이 크게 흔들려도 부츠는 땅과 거의 평평(좁으면 부츠가 통을 따라 돌아 발끝이 아래로 꺾임)
        'tube': {'part': 'shinP', 'a': [22, 0], 'b': [22, 46], 'k': 1.8, 'runBoot': True}}
for sd, nm, lm in [('near', 'bootStandN', lab('legN')), ('far', 'bootStandF', lab('legF'))]:
    legs[sd] = {'x': round(SC * (LEG[sd]['hip'][0] - HIP[0]), 1), 'shade': 0, 'thighImg': legs['thighImg'], 'shinImg': legs['shinImg'], 'runBoot': 'bootNRun' if sd == 'near' else 'bootFRun',
                'stand': {'fade': [0.12, 0.4], 'boot': {'part': nm, 'sole': sole_pts(lm, LEG[sd]['ankle'], O[1])}}}
idle = {sd: round(SC * (LEG[sd]['ankle'][0] - LEG[sd]['hip'][0]), 1) for sd in ('near', 'far')}
# 그리는 순서 (뒤 → 앞): 망토 · 먼 다리 · 가까운 다리 · 상체 · 치마 · 먼 윗팔(소매) · 먼 어깨 덮개(몸 띠) · 먼 팔뚝 · 칼(칼날은 머리 뒤) · 가까운 윗팔 · 어깨갑 · 머리+수염(+표정) · 먼 손 · 가까운 팔뚝+주먹(맨 앞 — 팔꿈치 레이어 > 어깨)
draw = ['cape', 'legFar', 'legNear', 'torso', 'skirt', 'armF', 'pauldronF', 'foreF', 'weapon', 'armU', 'pauldron', 'head', 'fistF', 'armL']
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
