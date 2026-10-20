"""9 러스트 팔로메 리그 조립 (2026-10-19 22:10~) — 몸 = 6 카르덴(드워프: 튜닉·바지 고정, 바짓단 아래만 걸음, 바지 통 다리) · 칼 = 21 스카이 알론소(먼 팔이 어깨에 멤, 칼날 머리 뒤)
입력: ref512.png(원화 = 게임 char_0009) · work/labels.npy(seg9.py — 원화를 부품별로 나눔) · pieces/(조각 시트 27칸, cut9.py) · work/geom.json(reg9.py SIFT: 시트 조각 → 원화)
출력: ../rig.json · ../rig.def.js · ../parts/*.png
실행: cd source && python3 -I cut9.py && python3 -I seg9.py && python3 -I reg9.py && python3 -I build_palome.py
원칙(DHL): 대기 = 원화 · 칼 크기 그대로 · 칼날은 원화처럼 머리 뒤 · 팔다리 길이 고정 · 공격 = 한 손 내려찍기 A(원화 손 하나로 끝까지, 21:39)
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
NAMES = ['head', 'sword', 'handF', 'foreF', 'pauldron', 'upperN', 'foreN', 'legN', 'legF', 'body']
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

# ---------------- 원화 관절 (512 px) ----------------
O = np.array([281.5, 501.0])           # 뿌리: 두 발 가운데 땅(가까운 발바닥)
HIP = np.array([288.0, 405.0])         # 골반(허리띠 가운데) — 상체·치마 뼈
NECK = np.array([300.0, 305.0])        # 머리+수염 뼈(수염 속 목)
SH_N, EL_N, WR_N = np.array([172.0, 282.0]), np.array([146.0, 343.0]), np.array([170.0, 408.0])   # 가까운 팔(자유 팔): 어깨(어깨갑 속)·팔꿈치(토시 위 왼쪽)·손목
SH_F, EL_F, WR_F = np.array([358.0, 303.0]), np.array([424.0, 336.0]), np.array([404.0, 288.0])   # 먼 팔(칼 메는 팔): 어깨(수염 뒤)·팔꿈치(둥근 토시 아래)·손목(손 밑)
HA0, HA1 = np.array([366.0, 232.0]), np.array([452.0, 311.0])     # 손잡이 축(날밑 → 폼멜)
G = HA0 + (HA1 - HA0) * ((398.0 - HA0[0]) / (HA1[0] - HA0[0]))   # 쥔 점 = 손잡이 축 위 x 398 (손가락 가운데)
TOPL, BOTL = (0.6475, -32.93), (0.6951, 7.24)                      # 칼날 위·아래 가장자리 (원화 맞춤 선 y = a x + b)
MID = ((TOPL[0] + BOTL[0]) / 2, (TOPL[1] + BOTL[1]) / 2); UT = -np.array([1.0, MID[0]]) / math.hypot(1, MID[0])   # 칼끝 방향(날 가운데 선)
TIP = np.array([44.0, 9.0])
LEG = {'near': dict(hip=np.array([226.0, 438.0]), ankle=np.array([225.0, 483.0])), 'far': dict(hip=np.array([333.0, 438.0]), ankle=np.array([338.0, 481.0]))}
R2 = lambda p: [round(float(2 * (p[0] - O[0])), 1), round(float(2 * (p[1] - O[1])), 1)]   # 원화 → 리그(뿌리 기준)

# ---------------- 조각 그림 ----------------
# 상체·치마: 몸(body)을 허리띠 위 선에서 나눔 (치마 = 허리띠·튜닉 아랫자락·가랑이 바지, 상체 = 그 위 + 8px 겹침)
CUT = np.array([[180, 394], [270, 394], [278, 384], [357, 383], [362, 392], [410, 392]], float)
cut_y = np.interp(XX, CUT[:, 0], CUT[:, 1]); OVL = 14   # 상체가 치마 밑으로 들어가는 겹침(기울어도 틈 없게)
body = lab('body')
# 상체 메움: 시트 상체(가까운 어깨 소매 구멍은 먼 어깨를 좌우 뒤집어 덮음) → 원화 배 너비에 맞춘 닮음(배 왼쪽 끝·오른쪽 끝)
st = sheet('torso'); st[:80, :46] = np.where(st[:80, 144:190][:, ::-1][..., 3:4] > 0, st[:80, 144:190][:, ::-1], st[:80, :46])
MT = simil((3, 95), (186, 92), (197, 360), (392, 350)); stw = warp(st, MT)
OCC = lab('head') | lab('handF') | lab('foreF') | lab('sword') | lab('pauldron') | lab('upperN') | lab('foreN')
# 가까운 팔(어깨갑·윗팔·토시) 밑 몸 가장자리: 몸 볼록 껍질 안을 몸 색으로 inpaint(몸 아닌 곳은 모두 모르는 값 → 몸 색만 번짐). 팔을 흔들면 보이는 배 왼쪽 테두리
hull_b = np.zeros((512, 512), np.uint8); cv2.fillConvexPoly(hull_b, cv2.convexHull(np.argwhere(body)[:, ::-1].astype(np.int32)), 1)
fillN = (hull_b > 0) & (lab('foreN') | lab('upperN') | lab('pauldron')) & ~body
bi = cv2.inpaint(np.ascontiguousarray(RA[..., :3]), (~body).astype(np.uint8), 4, cv2.INPAINT_TELEA)
binp = np.zeros_like(RA); binp[..., :3] = bi; binp[..., 3] = np.where(fillN, 255, 0)
_edge = fillN & (cv2.distanceTransform((hull_b > 0).astype(np.uint8), cv2.DIST_L2, 3) < 2.2); binp[_edge, :3] = (30, 24, 20)   # 껍질 가장자리 = 원화 외곽선 색 2px
torso = under(under(art(body & (YY < cut_y + OVL)), binp, fillN & (YY < cut_y + OVL)), stw, OCC & (YY < cut_y + OVL))
o_torso = save('torso', torso)
sh_ = sheet('hips'); MH = simil((2, 30), (183, 25), (196, 410), (395, 405)); shw = warp(sh_, MH)
skirt = under(under(art(body & (YY >= cut_y)), binp, fillN & (YY >= cut_y)), shw, lab('foreN') & (YY >= cut_y))
o_skirt = save('skirt', skirt)
# 머리+수염 (원화 그대로)
o_head = save('head', art(lab('head')))
# 어깨갑: 원화 + 머리·귀·수염 뒤는 시트 어깨갑(SIFT)
pw = warp(sheet('pauldron'), GEO['pauldron']['M'])
o_pd = save('pauldron', under(art(lab('pauldron')), pw, lab('head')))   # 앞에 있는 머리 뒤만 메움(몸은 어깨갑 뒤라 메우면 대기가 바뀜)
# 가까운 윗팔(비늘): 원화 보이는 곳 + 어깨갑·토시 밑은 시트 윗팔(어깨 → 팔꿈치 축에 맞춤)
def col_match(im, ref_m, k=1.0):   # 시트 조각 색을 원화 비늘 윗팔 색(채널별 평균·편차)에 맞춤 — 시트 비늘이 원화보다 노랗고 밝음(10-20 05:58 컷인 후보에서 봄)
    im = im.astype(np.float32); m = im[..., 3] > 200; R = RA[..., :3].astype(np.float32)[ref_m & (RA[..., 3] > 200)]
    for c in range(3):
        v = im[..., c][m]; im[..., c] = np.where(im[..., 3] > 0, (im[..., c] - v.mean()) / max(1.0, v.std()) * R[:, c].std() + R[:, c].mean(), im[..., c])
    im[..., :3] *= k; return np.clip(im, 0, 255).astype(np.uint8)
MU = simil((24, 3), (24, 53), SH_N, EL_N); uw = warp(col_match(sheet('upperN'), lab('upperN')), MU)
o_aU = save('armU', under(art(lab('upperN')), uw, lab('pauldron') | lab('foreN')))   # 앞에 있는 어깨갑·토시 밑만
# 가까운 팔뚝+주먹(큰 토시, 원화 그대로 — 맨 앞이라 가린 곳 없음)
o_aL = save('armL', art(lab('foreN')))
# 먼 윗팔: 원화에서는 수염·몸 뒤(안 보임) → 시트 먼 윗팔(어깨 → 팔꿈치)
# 먼 윗팔 = 시트 2 의 2번(10-20 08:28 — 원화 팔 길이에 맞춘 비늘 윗팔, 비늘 크기 = 가까운 팔): 늘이지 않고(배율 1) 아래 둥근 끝 가운데 = 팔꿈치, 위 = 어깨 방향.
#   둥근 끝 사이 89(원화 어깨~팔꿈치 74) — 남는 위 끝 15px 는 몸·수염 뒤. 색 = 원화 가까운 비늘 × .85(먼 쪽). 예전: 시트 1 upperF(42×51)를 1.6배 키워 씀(비늘이 커 보임)
_u2 = col_match(desp(np.array(Image.open(os.path.join(PC, 'p2_upperF2.png')).convert('RGBA'))), lab('upperN'), 0.85)
_ud = (SH_F - EL_F) / np.linalg.norm(SH_F - EL_F)
K_AF = 1.3   # 10-20 11:50 DHL '팔이 너무 얇아서 이상 — 반대편 팔과 두께를 맞춰야': 시트 2 윗팔 굵기 43 → 56(가까운 윗팔 60~80 의 약 0.8, 먼 팔). 아래 둥근 끝 = 팔꿈치 그대로, 길게 늘어난 위 끝은 어깨 너머 몸·수염 뒤(관절 길이 = 어깨~팔꿈치 74 그대로 — 늘이지 않음, 같은 배율로 키움)
o_aF = save('armF', warp(_u2, simil((23.5, 110), (23.5, 21), EL_F, EL_F + _ud * 89 * K_AF)))
# 먼 팔뚝(둥근 토시): 원화 + 손·손잡이 밑은 둘레 안을 inpaint
ff = art(lab('foreF')); hull = np.zeros((512, 512), np.uint8); cv2.fillConvexPoly(hull, cv2.convexHull(np.argwhere(lab('foreF'))[:, ::-1].astype(np.int32)), 1)
hole = (hull > 0) & (lab('handF') | lab('sword')) & (ff[..., 3] < 128)
if hole.any():
    rgb = cv2.inpaint(np.ascontiguousarray(ff[..., :3]), hole.astype(np.uint8), 5, cv2.INPAINT_TELEA); ff[hole, :3] = rgb[hole]; ff[hole, 3] = 255
o_fF = save('foreF', ff)
# 먼 손(칼 쥔 손, 원화 그대로)
o_fist = save('fistF', art(lab('handF')))
# 칼: 원화 + 머리 뒤 칼날은 칼날 띠 좌표(가장자리 맞춤 선 사이 0~1)로 왼쪽 D px 칼날을 옮겨 메움 (가죽 띠 간격 ≈ D 라 무늬가 이어짐)
sw = art(lab('sword'))
D = 67.0
yT = lambda x: TOPL[0] * x + TOPL[1]; yB = lambda x: BOTL[0] * x + BOTL[1]
v = (YY - yT(XX)) / (yB(XX) - yT(XX))
hid = (XX >= 240) & (XX <= 352) & (v > -0.14) & (v < 1.14) & lab('head')
for _ in range(3):   # 옮겨 온 곳도 가려졌으면 한 번 더 왼쪽에서
    xs_ = XX - D; ys_ = yT(xs_) + v * (yB(xs_) - yT(xs_))
    src = cv2.remap(sw, xs_.astype(np.float32), ys_.astype(np.float32), cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    put = hid & (src[..., 3] > 0) & (sw[..., 3] == 0); sw[put] = src[put]; hid &= ~put
    if not hid.any(): break
print('  blade fill left', int(hid.sum()), 'px')
o_sw_art = save('_sword_art', sw); os.remove(os.path.join(PARTS, '_sword_art.png'))
# 칼 그림을 세로(칼끝 위)로 돌림: 엔진 칼 뼈는 그림 위쪽(−y)이 칼끝 방향
ang_tip = math.atan2(UT[1], UT[0]); rot_deg = math.degrees(-math.pi / 2 - ang_tip)   # UT → (0,−1) 로 돌리는 각
UPS = 2   # 원화 2배(= 리그 단위)에서 돌림 → part scale 1
sw2 = cv2.resize(sw, None, fx=UPS, fy=UPS, interpolation=cv2.INTER_LANCZOS4); sw2[..., 3] = np.clip(cv2.resize(sw[..., 3], None, fx=UPS, fy=UPS, interpolation=cv2.INTER_LINEAR), 0, 255)
Rm = cv2.getRotationMatrix2D((float(G[0] * UPS), float(G[1] * UPS)), -rot_deg, 1.0)
WS, HS = 800, 2000; Rm[0, 2] += WS / 2 - G[0] * UPS; Rm[1, 2] += 1640 - G[1] * UPS   # 쥔 점을 캔버스 아래쪽에(칼끝이 위로 868px)
swv = cv2.warpAffine(sw2, Rm, (WS, HS), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
ys, xs = np.nonzero(swv[..., 3] > 0); x0, y0 = max(0, xs.min() - 2), max(0, ys.min() - 2); assert xs.min() > 0 and ys.min() > 0 and xs.max() < WS - 1 and ys.max() < HS - 1, '칼 그림이 캔버스 밖'; swv = swv[y0:ys.max() + 3, x0:xs.max() + 3]
Image.fromarray(swv).save(os.path.join(PARTS, 'weapon.png'))
vpt = lambda p: (Rm[:, :2] @ (np.array(p, float) * UPS) + Rm[:, 2]) - np.array([x0, y0])   # 원화 점 → 세로 칼 그림 px
W_PIV = vpt(G); W_TIP = vpt(TIP); W_GUARD = vpt(HA0); W_POM = vpt(HA1)
print('  sword vertical: tip', np.round(W_TIP, 1), 'grip', np.round(W_PIV, 1), 'rot', round(rot_deg, 2))
# 다리: 서 있을 때 = 원화 다리(바짓단 아래 바지 + 부츠) 그대로 / 달릴 때 = 먼 부츠(앞코 오른쪽) + 바지 통(shinP)
o_lN = save('bootStandN', art(lab('legN'))); o_lF = save('bootStandF', art(lab('legF')))
bf = art(lab('legF') & (YY >= 455)); bf[..., 3] = (bf[..., 3] * np.clip((YY - 455) / 4, 0, 1)).astype(np.uint8); o_bR = save('bootRun', bf)
# 달리는 부츠(쪽별) = 시트 부츠 그대로(배율 1, 늘이지 않음, 색 원화) — 10-20 29 교훈(DHL 07:25 '달리기 자세 어색'): 발목을 평평하게 두면 짧은 원화 부츠 목 옆으로 바지 통이
#   비스듬히 삐져나옴 → 목이 긴 시트 부츠가 통을 덮음. 엔진 opt-in legs.tube.runBoot(서 있을 땐 원화 다리, 달리면 한 프레임에 바꿈). 발목 점 = 목 가운데(x 20), 밑창 위 18px
def run_boot(nm, lm):
    b = col_match(sheet(nm), lm & (YY >= 455)); ys, xs = np.nonzero(b[..., 3] > 128); piv = (20.0, ys.max() - 18.0)
    Image.fromarray(b).save(os.path.join(PARTS, f'{nm}Run.png'))
    bot = {x: ys[xs == x].max() for x in range(xs.min(), xs.max() + 1) if (xs == x).any()}; xl, xr = min(bot), max(bot)
    cols = sorted(set(int(round(xl + (xr - xl) * f)) for f in (0.03, 0.25, 0.5, 0.75, 0.97)))
    return piv, [[round(float(x - piv[0]), 1), round(float(bot[x] - piv[1]), 1)] for x in cols]
RB = {'near': run_boot('bootN', lab('legN')), 'far': run_boot('bootF', lab('legF'))}
def sole_pts(m, ankle, ground=None):   # 부츠 바닥 점(발목 기준, 원화 px): 양 끝·가장 낮은 곳 포함. ground 를 주면 가장 낮은 점이 그 높이에 오게(먼 발은 원화에서 땅보다 위 — 깊이)
    ys, xs = np.nonzero(m); xl, xr = xs.min(), xs.max(); bot = {x: ys[xs == x].max() for x in range(xl, xr + 1) if (xs == x).any()}
    xlow = max(bot, key=lambda x: bot[x]); cols = sorted(set([int(round(xl + (xr - xl) * f)) for f in (0.02, 0.2, 0.8, 0.98)] + [xlow]))
    lift = 0.0 if ground is None else float(ground - bot[xlow])
    return [[float(x - ankle[0]), float(bot[x] - ankle[1] + lift)] for x in cols if x in bot]
tr_col = np.median(RA[(lab('legN') | lab('legF')) & (YY >= 449) & (YY <= 456) & (RA[..., :3].mean(-1) > 40)][:, :3], 0)
TW, TH = 44, 50; xs_ = (np.arange(TW) + .5) / TW
edge = np.clip(1 - np.minimum(xs_, 1 - xs_) / .2, 0, 1) ** 1.5; hl = np.exp(-((xs_ - .36) / .1) ** 2) * .6
base = tr_col.astype(np.float32); col = base[None] * (1 - edge[:, None]) + base[None] * .72 * edge[:, None]; col = col * (1 - hl[:, None]) + base[None] * 1.18 * hl[:, None]
tub = np.zeros((TH, TW, 4), np.float32); tub[..., :3] = col[None] + np.random.default_rng(9).normal(0, 2.0, (TH, TW, 1))
olm = (np.arange(TW) < 2) | (np.arange(TW) >= TW - 2); tub[:, olm, :3] = (26, 21, 21)
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
for n in FACE_N + BLINK_N:
    wf = cv2.warpAffine(sheet(SRC[n]), MF, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0)); al = fm * (wf[..., 3] / 255.0)
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
P_('armF', SH_F, elbow=piv('armF', EL_F)); P_('foreF', EL_F); P_('fistF', WR_F)
parts['weapon'] = {'src': 'parts/weapon.png', 'pivot': [round(float(W_PIV[0]), 1), round(float(W_PIV[1]), 1)], 'scale': SC / UPS,
                   'tip': [round(float(W_TIP[0]), 1), round(float(W_TIP[1]), 1)], 'tips': [[round(float(W_TIP[0]) - 6 * UPS, 1), round(float(W_TIP[1]) + 10 * UPS, 1)], [round(float(W_TIP[0]) + 14 * UPS, 1), round(float(W_TIP[1]) + 10 * UPS, 1)]],
                   'guard': [round(float(W_GUARD[0]), 1), round(float(W_GUARD[1]), 1)], 'pommel': [round(float(W_POM[0]), 1), round(float(W_POM[1]), 1)]}
for n in FACE_N + BLINK_N: parts[f'face_{n}'] = {'src': f'parts/face_{n}.png', 'pivot': parts['head']['pivot'], 'scale': SC}
for nm, sd in [('bootStandN', 'near'), ('bootStandF', 'far')]: P_(nm, LEG[sd]['ankle'])
P_('bootRun', LEG['far']['ankle'])
for _sd, _nm in (('near', 'bootNRun'), ('far', 'bootFRun')): parts[_nm] = {'src': f'parts/{_nm}.png', 'pivot': [round(RB[_sd][0][0], 1), round(RB[_sd][0][1], 1)], 'scale': SC}
parts['shinP'] = {'src': 'parts/shinP.png', 'pivot': [0, 0], 'scale': 1}
WEAPON_ANG = math.atan2(UT[1], UT[0]) + math.pi / 2   # 세로 칼 그림 뼈의 세계 각(그림 위쪽 → 칼끝)
ARML_REST = 0.3   # 엔진이 서 있을 때 자유 팔뚝을 −0.3 rad 굽힘(armL.ar) → 뼈 rot 에 +0.3 을 넣어 대기 = 원화
world = {'root': (O, 0.0), 'hip': (HIP, 0.0), 'skirt': (HIP, 0.0), 'torso': (HIP, 0.0), 'head': (NECK, 0.0), 'pauldron': (SH_N, 0.0), 'armU': (SH_N, 0.0), 'armL': (EL_N, ARML_REST),
         'armF': (SH_F, 0.0), 'foreF': (EL_F, 0.0), 'fistF': (WR_F, 0.0), 'weapon': (G, WEAPON_ANG), 'cape': (NECK, 0.0), 'scarf': (NECK, 0.0), 'pouch': (HIP, 0.0), 'pauldronF': (SH_F, 0.0), 'foreFb': (WR_F, 0.0)}
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
legs = {'hip': [0, round(hipY, 1)], 'thigh': 48, 'shin': 48,
        'thighImg': {'part': 'shinP', 'a': [22, 0], 'b': [22, 46], 'w': 0.001}, 'shinImg': {'part': 'shinP', 'a': [22, 0], 'b': [22, 46], 'w': 0.001},
        'boot': {'part': 'bootFRun', 'sole': RB['far'][1], 'ankleRange': [-1.7, 1.7]},   # 10-20 29 교훈: 짧은 다리라 정강이(통) 각이 크게 흔들려 좁은 범위면 부츠가 통을 따라 돌아 발끝이 아래로 꺾임 → 넓게(부츠는 거의 평평)
        'tube': {'part': 'shinP', 'a': [22, 0], 'b': [22, 46], 'k': 1.8, 'runBoot': True}}
for sd, nm, lm in [('near', 'bootStandN', lab('legN')), ('far', 'bootStandF', lab('legF'))]:
    legs[sd] = {'x': round(SC * (LEG[sd]['hip'][0] - HIP[0]), 1), 'shade': 0, 'thighImg': legs['thighImg'], 'shinImg': legs['shinImg'], 'runBoot': 'bootNRun' if sd == 'near' else 'bootFRun',
                'stand': {'fade': [0.12, 0.4], 'boot': {'part': nm, 'sole': sole_pts(lm, LEG[sd]['ankle'], O[1])}}}
idle = {sd: round(SC * (LEG[sd]['ankle'][0] - LEG[sd]['hip'][0]), 1) for sd in ('near', 'far')}
# 그리는 순서 (뒤 → 앞): 먼 다리 · 가까운 다리 · 상체 · 치마 · 먼 팔뚝 · 칼(칼날은 머리 뒤) · 가까운 윗팔 · 가까운 팔뚝+주먹 · 어깨갑 · 머리+수염(+표정) · 먼 손
draw = ['legFar', 'legNear', 'torso', 'skirt', 'foreF', 'weapon', 'armU', 'armL', 'pauldron', 'head', 'fistF']   # 귀·수염이 어깨갑 앞
rig = {'name': 'palome-rust', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': parts, 'bones': bones, 'legs': legs, 'draw': draw, 'hidden': [], 'faces': {n: f'face_{n}' for n in FACE_N},
       'blinkFaces': {'half': 'face_half', 'closed': 'face_closed'}, 'idleStance': idle,
       'gait': {'stance': 0.18, 'strideBase': 14, 'strideK': 0.06, 'hipBase': 0, 'bob': 6, 'lean': 0.06, 'waddle': 0.02, 'headBob': 3, 'kneeLift': 0.2, 'heelKick': 0.03, 'dropCap': 12,
                'swingReach': 0.05, 'landAng': -0.04, 'angK': 0.2, 'elbowRun': 0.22, 'armSwing': 0.16, 'armBias': 0.0, 'headRun': 0.06},
       'hemRun': {'lift': 8, 'knee': 0.5, 'heel': 0.3, 'reach': 0.2}, 'hemLimit': {'up': 0.25, 'x': 0.3}, 'hemGain': 0.15, 'footReach': 0.97,
       'follow': [{'bone': 'pauldron', 'src': 'armU', 'k': 0.3}], 'skirtFollow': 0.7, 'carrySwing': 0.15, 'wristRange': 0.2, 'dropLift': 10,
       'bounce': [], 'metrics': {'bodyHeight': round(2 * (501 - 167)), 'note': 'rig units; 머리카락 위(y167)~발바닥(501) ×2, 칼 제외'},
       'ui': {'attack': 'smash', 'touch': 'hop'},   # 트레일 기본(위 → 아래) = 내려찍기
       'gameRef': {'refOrigin': [round(float(O[0] - (HIP[0] - 253.1)), 1), float(O[1])], 'refScale': 2.0, 'refLift': 0,
                   'note': '게임 그림 char_0009.png(512) = 원화(md5 같음). x = 도감 칸(fitArt 중심 253.1, index.html measureBox 와 같은 계산)에서 골반(hip x 288)이 가운데 (3·13·23 산초·알론소들과 같은 규칙)'},
       'note': '9 러스트 팔로메 v1(대기·달리기). 몸 = 6 카르덴(드워프), 칼 = 21 스카이 알론소(먼 팔이 어깨에 멤, 칼날 머리 뒤). 조각 = 원화를 부품별로 나눔(seg9.py) + 가려진 곳만 시트로 메움'}
exec(open(os.path.join(HERE, 'attack_palome.py'), encoding='utf-8').read())   # 한 손 내려찍기 A
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(PARTS)): _h.update(fn.encode()); _h.update(open(os.path.join(PARTS, fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_palome.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['palome-rust']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(parts), 'parts, version', rig['version'], 'idle', idle, 'legs x', legs['near']['x'], legs['far']['x'], 'hipY', legs['hip'])
