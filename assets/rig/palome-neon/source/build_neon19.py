"""19 네온 팔로메 리그 조립 (2026-10-20 19:5x~) — 9 러스트 팔로메 구조 그대로(같은 자세로 새 원화를 받음: 드워프 몸, 먼 팔이 칼을 어깨에 멤·칼날 머리 뒤, 망토 없음)
입력: ref512.png(새 원화 = 게임 char_0019) · work/labels.npy(seg19.py) · pieces/(조각 시트 21칸, cut19.py) · work/geom.json(reg19.py SIFT)
출력: ../rig.json · ../rig.def.js · ../parts/*.png
실행: cd source && python3 -I cut19.py && python3 -I seg19.py && python3 -I reg19.py && python3 -I build_neon19.py
원칙(DHL): 대기 = 원화 · 칼 크기 그대로 · 칼날은 원화처럼 머리 뒤 · 팔다리 길이 고정(늘이지 않음) · 공격 = 9 v1.1 한 손 내려찍기(지렛대 휘두르기) 키 — 19 팔에 맞춰 쥔 점만 옮김(tools/rekey19.py)
좌표: 원화 512px 로 적고, 리그 단위 = ×2 (조각 그림은 원화 px 그대로, part scale 2)
엔진 이름(9 와 같음): armF→foreF→fistF→weapon = 칼 메는 팔(몸 뒤 먼 팔) · armU→armL + pauldron = 자유 팔(가까운 팔, 큰 흰 어깨갑)
"""
import json, math, os, shutil, hashlib
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); PC = os.path.join(HERE, 'pieces'); W = os.path.join(HERE, 'work'); OUT = os.path.join(HERE, '..'); PARTS = os.path.join(OUT, 'parts')
if os.path.isdir(PARTS): shutil.rmtree(PARTS)
os.makedirs(PARTS); os.makedirs(W, exist_ok=True)
RA = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA'))
LAB = np.load(os.path.join(W, 'labels.npy'))
NAMES = json.load(open(os.path.join(W, 'label_names.json')))
LID = {n: i + 1 for i, n in enumerate(NAMES)}
lab = lambda n: LAB == LID[n] if n in LID else np.zeros((512, 512), bool)
GEO = json.load(open(os.path.join(W, 'geom.json')))
YY, XX = np.mgrid[0:512, 0:512]
LUM = RA[..., :3].astype(int).mean(-1)
# 라벨 손질(첫 렌더 공격 확대에서 봄):
#  ①가까운 소매(upperN)에 붙은 토시 윗 테(흰·밝은 1~3px) → 토시(foreN): 팔이 움직이면 소매와 토시가 따로 돌아 토시 위에 흰 실조각
#  ②토시·주먹 둘레 2px 어두운 외곽선이 몸(body)에 남은 것 → 토시: 팔이 비키면 몸 위에 검은 톱니 선(29 v1.7 RING_N 교훈)
LAB = LAB.copy(); _LI = {n: i + 1 for i, n in enumerate(json.load(open(os.path.join(W, 'label_names.json'))))}
_fn = LAB == _LI['foreN']
_rim = (LAB == _LI['upperN']) & (LUM > 110) & (cv2.dilate(_fn.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0); LAB[_rim] = _LI['foreN']
_ring = (LAB == _LI['body']) & (cv2.dilate(_fn.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))) > 0) & (LUM < 48); LAB[_ring] = _LI['foreN']
print('  label fix: vambrace rim from sleeve', int(_rim.sum()), '· outline ring from body', int(_ring.sum()))
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
def col_match(im, ref_m, k=1.0):   # 시트 조각 색을 원화 같은 부위 색(채널별 평균·편차)에 맞춤
    im = im.astype(np.float32); m = im[..., 3] > 200; R = RA[..., :3].astype(np.float32)[ref_m & (RA[..., 3] > 200)]
    for c in range(3):
        v = im[..., c][m]; im[..., c] = np.where(im[..., 3] > 0, (im[..., c] - v.mean()) / max(1.0, v.std()) * R[:, c].std() + R[:, c].mean(), im[..., c])
    im[..., :3] *= k; return np.clip(im, 0, 255).astype(np.uint8)
def hull_inpaint(m_src, where, r=4):   # m_src 볼록 껍질 안 + where 를 m_src 색으로 inpaint + 껍질 가장자리 외곽선 2px
    hull = np.zeros((512, 512), np.uint8); cv2.fillConvexPoly(hull, cv2.convexHull(np.argwhere(m_src)[:, ::-1].astype(np.int32)), 1)
    fill = (hull > 0) & where & ~m_src
    rgb = cv2.inpaint(np.ascontiguousarray(RA[..., :3]), (~m_src).astype(np.uint8), r, cv2.INPAINT_TELEA)
    out = np.zeros_like(RA); out[..., :3] = rgb; out[..., 3] = np.where(fill, 255, 0)
    edge = fill & (cv2.distanceTransform((hull > 0).astype(np.uint8), cv2.DIST_L2, 3) < 2.2); out[edge, :3] = (30, 28, 34)
    return out, fill

# ---------------- 원화 관절 (512 px, 격자 확대 j9_19·poly19*.png 에서 읽음 — 9 와 같은 자세라 9 값에서 비킨 곳만 고침) ----------------
O = np.array([280.0, 501.0])           # 뿌리: 두 발 가운데 땅(가까운 발바닥 501)
HIP = np.array([288.0, 405.0])         # 골반(허리띠 가운데 높이) — 9 와 같음
NECK = np.array([300.0, 305.0])        # 머리+수염 뼈(수염 속 목)
SH_N, EL_N, WR_N = np.array([172.0, 282.0]), np.array([146.0, 343.0]), np.array([170.0, 408.0])   # 가까운 팔(자유 팔): 9 와 같은 자리(토시·주먹이 9 와 겹침)
SH_F, EL_F, WR_F = np.array([352.0, 276.0]), np.array([408.0, 332.0]), np.array([405.0, 292.0])   # 먼 팔(칼 메는 팔): 어깨 = 주먹 뒤 먼 어깨갑 끝 안쪽, 팔꿈치 = 세로 토시 아래 둥근 끝, 손목 = 주먹 아래
HA0, HA1 = np.array([354.0, 233.5]), np.array([457.5, 312.0])     # 손잡이 축(날밑 = 금 고리에서 날 축으로 −4.5px → 폼멜 고리)
G = HA0 + (HA1 - HA0) * ((400.0 - HA0[0]) / (HA1[0] - HA0[0]))   # 쥔 점 = 손잡이 축 위 x 400 (손가락 가운데)
TOPL, BOTL = (0.7051, -40.6), (0.7051, 9.6)                       # 칼날 위·아래 가장자리 (y = a x + b — 날 폭 41, 고리→칼끝 선에서 +16 / −25)
MID = ((TOPL[0] + BOTL[0]) / 2, (TOPL[1] + BOTL[1]) / 2); UT = -np.array([1.0, MID[0]]) / math.hypot(1, MID[0])   # 칼끝 방향(날 가운데 선)
TIP = np.array([44.0, 10.0])
LEG = {'near': dict(hip=np.array([226.0, 438.0]), ankle=np.array([222.0, 483.0])), 'far': dict(hip=np.array([333.0, 438.0]), ankle=np.array([338.0, 482.0]))}
FIT_CX = 252.0   # 도감 fitArt 가운데(index.html measureBox 를 160px 로 흉내) — 칼날 뒤집은 char_0019(10-20 21:05, 원화 그대로였을 땐 253.6)

# ---------------- 상체·치마 ----------------
# 허리띠 윗변(큰 버클 위 389, 나머지 394)에서 나눔 — 치마 = 허리띠·아래 배 판, 상체 = 그 위 + 14px 겹침
CUT = np.array([[150, 394], [285, 394], [290, 389], [345, 389], [350, 394], [420, 394]], float)
cut_y = np.interp(XX, CUT[:, 0], CUT[:, 1]); OVL = 14
body = lab('body')
# 상체 메움: 시트 상체(SIFT) — 색 = 원화 몸통
stw = warp(col_match(sheet('torso'), body & (YY < 390)), GEO['torso']['M'])
OCC = lab('head') | lab('handF') | lab('foreF') | lab('upperF') | lab('sword') | lab('pauldron') | lab('upperN') | lab('foreN')
# 가까운 팔 밑 몸 가장자리: 몸 껍질 안 inpaint(시트 상체가 못 덮는 곳) — 프롬프트 2 '가까운 팔만 지운 원화'가 오면 그 그림으로 바꿈
binp, fillN = hull_inpaint(body, lab('foreN') | lab('upperN') | lab('pauldron'))
torso = under(under(art(body & (YY < cut_y + OVL)), stw, OCC & (YY < cut_y + OVL)), binp, fillN & (YY < cut_y + OVL))
# 가까운 팔만 지운 원화 (DHL 10-20 19:50, sheets/noarm_1950.png — 프롬프트 2 + 가이드 refs/ref_W19): 원화와 SIFT 803점 · 배율 1.0000 · 0.0px, 팔 밖 색 차이 0.06
#   → 팔(소매·토시·주먹 + 외곽선)이 가리던 곳(+1px)만 이 그림 그대로: 상체(나눔선 위) · 치마(나눔선 아래). 몸 밖(그림에서 투명)은 비움 — 시트 상체·inpaint 로 채웠던 곳(공격 때 흰 줄·톱니)
NOARM = np.array(Image.open(os.path.join(HERE, 'sheets', 'noarm_1950.png')).convert('RGBA'))
_ARMZ = dil(lab('foreN') | lab('upperN'), 1)
ARM_OCC = _ARMZ & (NOARM[..., 3] > 200); ARM_OUT = _ARMZ & (NOARM[..., 3] <= 200) & ~body
_tNA = ARM_OCC & (YY < cut_y); torso[_tNA] = NOARM[_tNA]; torso[ARM_OUT & (YY < cut_y + OVL)] = 0
#   상체 아래 겹침 띠(나눔선 아래 14px — 대기엔 치마가 덮고, 공격 때 상체가 기울면 보임): 그림 픽셀(허리띠·금 판)을 상체에 두면 치마 허리띠와 두 겹(48번) →
#   나눔선 바로 위 '천' 색(밝은 판·외곽선 빼고 σ4 정규화 흐림)을 아래로 늘임(29 v2.0)
_lumNA = NOARM[..., :3].astype(int).mean(-1)
_RN, _GN, _BN = (NOARM[..., c].astype(int) for c in range(3))
_clo = ((NOARM[..., 3] > 200) & (_lumNA >= 25) & (_lumNA <= 95) & ~((_RN - _BN >= 40) & (_GN - _BN >= 20))).astype(np.float32)   # 검은 누빔·버건디 천만(금 판·흰 판·외곽선 빼고 — 금색이 섞여 공격 때 주먹 밑에 금빛 번짐)
_cb = cv2.GaussianBlur(NOARM[..., :3].astype(np.float32) * _clo[..., None], (0, 0), 4) / np.maximum(cv2.GaussianBlur(_clo, (0, 0), 4)[..., None], 1e-3)
_srow = np.clip(np.floor(cut_y[0]).astype(int) - 3, 0, 511)
_nzt = np.clip(cv2.GaussianBlur(np.random.default_rng(4).normal(0, 1, (512, 512)).astype(np.float32), (0, 0), 3) * 10, -4, 4)[..., None]
_skc = cv2.erode(((NOARM[..., 3] > 200) & (YY >= cut_y - 4)).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0   # 치마(그림) 안쪽 4px — 가장자리까지 채우면 공격 때 상체가 기울며 띠가 치마 왼쪽 밖으로 삐져나옴
_ovNA = ARM_OCC & (YY >= cut_y) & (YY < cut_y + OVL) & _skc
torso[ARM_OCC & (YY >= cut_y) & (YY < cut_y + OVL) & ~_skc] = 0
torso[_ovNA, :3] = np.clip(_cb[_srow[XX], XX] + _nzt, 0, 255)[_ovNA].astype(np.uint8); torso[_ovNA, 3] = 255
# 칼·먼 주먹·먼 토시만 지운 원화 (DHL 10-20 20:19, sheets/nosword_2019.png — 프롬프트 3 + 가이드 refs/ref_X19): 원화와 SIFT 749점 · 배율 1.0000 · 0.0px, 지운 곳 밖 색 차이 0.48
#   → 칼·손·토시가 가리던 곳(+1px) 중 상체 몫(나눔선 위) = 이 그림 그대로: 먼 어깨갑(흰 판·금 테) · 몸 오른쪽 · 수염 오른쪽 아래 판. 그림에서 투명한 곳(칼이 있던 몸 밖)은 비움 —
#   시트 상체가 칼 자리까지 채워 공격 때 오른쪽 위에 흰 띠 조각이 떠 있었음(29 는 시트 3 + torsoM 으로 따로 메웠던 곳)
NOSW = np.array(Image.open(os.path.join(HERE, 'sheets', 'nosword_2019.png')).convert('RGBA'))
_hh = np.zeros((512, 512), np.uint8); cv2.fillConvexPoly(_hh, cv2.convexHull(np.argwhere(lab('head'))[:, ::-1].astype(np.int32)), 1); HEAD_HULL = _hh > 0
#   머리 껍질 안(머리카락·수염 사이로 칼날·날밑이 보이던 틈)은 상체가 아니라 머리 몫 → 공격 표정 조각에만 그림 머리카락으로 메움(아래 표정) — 상체에 두면 머리가 돌 때 머리카락 조각이 몸에 남음
HFILL = dil(lab('sword') | lab('handF') | lab('foreF'), 1) & HEAD_HULL & ~lab('head') & (NOSW[..., 3] > 200)
_SWZ = dil(lab('sword') | lab('handF') | lab('foreF'), 1) & ~lab('head') & ~HEAD_HULL
SW_OCC = _SWZ & (NOSW[..., 3] > 200) & (YY < cut_y); SW_OUT = _SWZ & (NOSW[..., 3] <= 200) & ~body
torso[SW_OCC] = NOSW[SW_OCC]; torso[SW_OUT & (YY < cut_y + OVL)] = 0
print('  torso behind sword/far hand <- no-sword art', int(SW_OCC.sum()), 'px · cleared', int((SW_OUT & (YY < cut_y + OVL)).sum()))
print('  torso behind near arm <- no-arm art', int(_tNA.sum()), 'px · overlap cloth', int(_ovNA.sum()), '· cleared outside body', int((ARM_OUT & (YY < cut_y + OVL)).sum()))
o_torso = save('torso', torso)
# 밑단(치마 아래 배 판의 아래 외곽선, 격자 hem19.png 에서 읽음): 그 아래 몸 픽셀(검은 바지·무릎 판 윗부분)은 서 있는 다리 조각으로 —
#   치마에 두면 숨쉬기·달리기로 치마가 움직일 때 무릎 판 위가 갈라져 찢긴 조각·검은 띠(29 v1.7 교훈, 첫 렌더에서도 보였음)
HEM = {'near': np.array([[186, 442], [200, 445], [220, 448], [240, 450], [266, 451]], float), 'far': np.array([[286, 451], [310, 451], [330, 449], [350, 447], [365, 444], [386, 439]], float)}
HEMX = {'near': (194, 254), 'far': (302, 376)}   # 다리 조각이 있는 칸만(넓게 잡으면 치마 아래 외곽선 끝줄이 다리 조각 위에 가는 검은 선으로 붙음)
hem_y = {sd: np.ceil(np.interp(XX, HEM[sd][:, 0], HEM[sd][:, 1]) + 0.5) for sd in HEM}   # 외곽선 한 줄은 치마 것, 그 아래부터 다리
legTop = {sd: body & (XX >= HEMX[sd][0]) & (XX <= HEMX[sd][1]) & (YY >= hem_y[sd]) & (YY < 475) for sd in HEM}
legTop = {sd: cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0 for sd, m in legTop.items()}   # 1~2줄 가는 조각(치마 외곽선 끝) 뺌
SKIRT_CUT = legTop['near'] | legTop['far']
print('  leg tops from body', {sd: int(legTop[sd].sum()) for sd in legTop})
shw = warp(col_match(sheet('hips'), body & (YY >= cut_y)), GEO['hips']['M'])
skirt = under(under(art(body & (YY >= cut_y) & ~SKIRT_CUT), shw, lab('foreN') & (YY >= cut_y)), binp, fillN & (YY >= cut_y))
_sNA = ARM_OCC & (YY >= cut_y) & ~SKIRT_CUT; skirt[_sNA] = NOARM[_sNA]; skirt[ARM_OUT & (YY >= cut_y)] = 0   # 주먹 밑 허리띠·금 판·아래 배 판 = 그림 그대로
print('  skirt under fist <- no-arm art', int(_sNA.sum()), 'px')
o_skirt = save('skirt', skirt)
# 머리+수염 (원화 그대로, 안경 포함)
o_head = save('head', art(lab('head')))
# 어깨갑: 원화 + 머리·귀 뒤는 시트 어깨갑(SIFT)
pw = warp(col_match(sheet('pauldron'), lab('pauldron')), GEO['pauldron']['M'])
o_pd = save('pauldron', under(art(lab('pauldron')), pw, lab('head')))
# 윗팔 조각: 시트 윗팔을 늘이지 않고(같은 배율 K) 아래 둥근 끝 가운데 = 팔꿈치, 위 = 어깨 방향 (29 v1.4 교훈)
def arm_piece(nm, top, bot, SH, EL, K, ref_m, k=1.0):
    a0, a1 = np.array(bot, float), np.array(top, float); u = (np.array(SH, float) - np.array(EL, float)); u /= np.linalg.norm(u)
    return warp(col_match(sheet(nm), ref_m, k), simil(a0, a1, EL, np.array(EL, float) + u * np.linalg.norm(a1 - a0) * K))
SLEEVE = lab('upperN') & (LUM < 80)   # 원화 가까운 소매(검은 누빔)
# 가까운 윗팔 = 시트 15번(44×102, 둥근 끝 가운데 (22,22)·(22,80)) ×1.075(시트 배율 .93 되돌림) → 둥근 끝 사이 62(9 리그 74 — 위 끝은 큰 어깨갑 밑)
uw = arm_piece('upperN', (22, 22), (22, 80), SH_N, EL_N, 1.075, SLEEVE)
o_aU = save('armU', under(art(lab('upperN')), uw, lab('pauldron') | lab('foreN') | lab('upperN')))
# 가까운 팔뚝+주먹(큰 흰 토시 + 쇠 장갑 주먹, 원화 그대로 — 맨 앞)
o_aL = save('armL', art(lab('foreN')))
# 먼 윗팔 = 시트 17번(36×96, 둥근 끝 가운데 (18,18)·(18,78)) ×1.4: 굵기 50(가까운 소매의 약 0.85 — 9 v1.1 '팔이 너무 얇아' 교훈) · 둥근 끝 사이 84(어깨~팔꿈치 79.2 — 남는 위 끝은 몸·수염 뒤)
K_AF = 1.4
o_aF = save('armF', arm_piece('upperF', (18, 18), (18, 78), SH_F, EL_F, K_AF, SLEEVE, 0.85))
# 먼 팔뚝(흰 토시): 원화 + 손·손잡이 밑은 껍질 안 inpaint
finp, ffill = hull_inpaint(lab('foreF'), lab('handF') | lab('sword'), 5)
o_fF = save('foreF', under(art(lab('foreF')), finp, ffill))
# 먼 손(칼 쥔 손, 원화 그대로)
o_fist = save('fistF', art(lab('handF')))
# ---------------- 칼 ----------------
# 움직이는 칼날(머리 뒤 ~ 날밑) = 머리 왼쪽 깨끗한 단면 하나(x 227~231: 아래 크림 반은 홈 사이 맨 칼날, 위 회색 반은 긴 홈)를 날 방향으로 이어 붙인 한 덩어리 —
#   가려진 곳만 메우면 원화 홈 무늬와 메운 띠가 엇갈려 '깨진 칼'(29 v1.5 교훈 40, 첫 렌더에서도 칼날 가운데 계단). 날 폭·길이 = 원화 그대로.
#   서 있을 땐 guardArt(바뀐 곳의 원화 칼 픽셀, 칼 뼈에 붙음)가 위에 그려 대기 = 원화
sw = art(lab('sword')); SW0 = sw.copy()
yT = lambda x: TOPL[0] * x + TOPL[1]; yB = lambda x: BOTL[0] * x + BOTL[1]
v = (YY - yT(XX)) / (yB(XX) - yT(XX))
_ax = (HA1 - HA0) / np.linalg.norm(HA1 - HA0); _al = (XX - HA0[0]) * _ax[0] + (YY - HA0[1]) * _ax[1]
X0B = 233   # 이은 날이 시작하는 칸(이 왼쪽은 원화 그대로)
REPL = (XX >= X0B) & (_al < -12) & (v > -0.12) & (v < 1.12)   # 날밑 앞까지 날 띠
sw[(XX >= X0B) & (XX <= 352) & ((v < -0.12) | (v > 1.12)) & (_al < -14)] = 0   # 날 띠 밖 조각(머리카락 외곽선 등)은 칼에서 뺌
cols = []
for xr in range(227, 232):
    ys_r = yT(xr) + v * (yB(xr) - yT(xr)); cols.append(cv2.remap(SW0.astype(np.float32), np.full_like(ys_r, xr, np.float32), ys_r.astype(np.float32), cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)))
src = np.mean(cols, 0)
sw[REPL] = 0; put = REPL & (src[..., 3] > 4); sw[put] = np.clip(src[put], 0, 255).astype(np.uint8)
print('  blade rebuilt from section x227~231:', int(put.sum()), 'px')
# 손잡이(주먹에 가려진 곳): 날밑과 주먹 사이 보이는 손잡이 단면(축 거리 14~20 평균)을 손잡이 축으로 이어 메움 — 메기 때 주먹이 칼을 따라 돌며 날밑~주먹 사이 손잡이 구멍이 흰 실금으로 보였음
_nh = np.array([-_ax[1], _ax[0]]); _lat = (XX - HA0[0]) * _nh[0] + (YY - HA0[1]) * _nh[1]
_hl = np.linalg.norm(HA1 - HA0); _HZ = (_al >= 12) & (_al <= _hl - 14) & (np.abs(_lat) <= 8.5) & (sw[..., 3] < 250)
_hc = []
for _a in range(14, 21):
    _px = HA0[0] + _a * _ax[0] + _lat * _nh[0]; _py = HA0[1] + _a * _ax[1] + _lat * _nh[1]
    _hc.append(cv2.remap(SW0.astype(np.float32), _px.astype(np.float32), _py.astype(np.float32), cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)))
_hsrc = np.mean(_hc, 0); _hput = _HZ & (_hsrc[..., 3] > 128)
sw[_hput] = np.clip(np.where(sw[_hput][:, 3:4] > 0, (sw[_hput].astype(np.float32) * sw[_hput][:, 3:4] / 255 + _hsrc[_hput] * (1 - sw[_hput][:, 3:4] / 255)), _hsrc[_hput]), 0, 255).astype(np.uint8); sw[_hput, 3] = 255
print('  handle under fist filled', int(_hput.sum()), 'px')
# 날밑 아래쪽(수염·머리카락에 가려진 반): 날밑 위쪽 반을 금 고리 가운데(356,230)에서 칼날 방향 축으로 거울 — 휘두를 때 날밑 아래가 톱니로 잘려 보였음(시트 칼은 SIFT 자리가 어긋나 못 씀)
_RC = np.array([356.0, 230.0]); _ga_ = (XX - _RC[0]) * UT[0] + (YY - _RC[1]) * UT[1]; _gb_ = (XX - _RC[0]) * -UT[1] + (YY - _RC[1]) * UT[0]
_mx_ = _RC[0] + _ga_ * UT[0] + (-_gb_) * -UT[1]; _my_ = _RC[1] + _ga_ * UT[1] + (-_gb_) * UT[0]
_gm_src = cv2.remap(SW0.astype(np.float32), _mx_.astype(np.float32), _my_.astype(np.float32), cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
_GZ = (np.abs(_ga_) <= 13) & (np.abs(_gb_) <= 38) & (sw[..., 3] < 128) & lab('head') & (_gm_src[..., 3] > 200)
sw[_GZ] = np.clip(_gm_src[_GZ], 0, 255).astype(np.uint8); print('  guard lower half mirrored', int(_GZ.sum()), 'px')
for _x in (215, 342):   # 머리 양쪽 원화 칼날 윗변 vs 맞춤 선(어긋나면 이은 날이 대기와 달라짐)
    _c = np.nonzero(lab('sword')[:, _x] & (np.abs(v[:, _x] - 0.5) < 0.8))[0]
    if len(_c): print(f'  blade top @x{_x}: art {_c.min()} vs line {yT(_x):.1f}')
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
# guardArt: 원화 칼 픽셀 중 움직이는 칼 그림에서 바뀐 곳 — 칼 뼈에 붙여 서 있을 때·달릴 때·공격 시작/끝만 칼 위에 그림 → 대기 = 원화
_gm = (SW0[..., 3] > 0) & ((np.abs(SW0.astype(int) - sw.astype(int)).max(-1) > 8) | dil(REPL, 3))
ga = np.zeros_like(SW0); ga[_gm] = SW0[_gm]
ga2 = cv2.resize(ga, None, fx=UPS, fy=UPS, interpolation=cv2.INTER_LANCZOS4); ga2[..., 3] = np.clip(cv2.resize(ga[..., 3], None, fx=UPS, fy=UPS, interpolation=cv2.INTER_LINEAR), 0, 255)
gav = cv2.warpAffine(ga2, Rm, (WS, HS), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))[y0:y0 + swv.shape[0], x0:x0 + swv.shape[1]]
# 칼날 좌우 반전(10-20 20:38 DHL '칼을 좌우반전 · 칼날이 뒤에 있어요'): 원화는 크림 날이 어깨 쪽(아래), 회색 등이 위 → 앞으로 내려찍으면 등이 앞장섬.
#   세운 칼 그림에서 날밑 위 칼날만 칼날 가운데 세로선(날밑 바로 위 칼날 폭 가운데)으로 거울 — 날밑·손잡이·폼멜은 그대로(주먹·쥔 점·칼 방향·길이 그대로).
#   날밑 오른쪽 위 뿔(x > 102)은 날밑 것이라 빼고, 날밑 윗선(y ≥ 748)부터는 그대로. guardArt(대기 원화 칼 픽셀)도 같은 거울 → 대기 = '원화 칼을 뒤집은 것'
FLIP_BLADE = True
if FLIP_BLADE:
    _al_ = swv[..., 3] > 40; _gy = int(round(W_GUARD[1])); _rows = [y for y in range(_gy - 40, _gy - 30) if _al_[y].any()]
    _bx = [np.nonzero(_al_[y])[0] for y in _rows]; BCX = float(np.median([(b.min() + b.max()) / 2 for b in _bx]))   # 날밑 바로 위 칼날 폭 가운데
    YCUT = _gy - 24; XL, XR = 3, int(2 * BCX) - 3
    def _mir(img):
        out = img.copy(); ys_ = slice(0, YCUT); xd = np.arange(XL, XR + 1); xs_ = np.round(2 * BCX - xd).astype(int)
        blk = img[ys_][:, xs_].copy(); out[ys_, XL:XR + 1] = blk; return out
    swv = _mir(swv); gav = _mir(gav)
    # 칼날 위 guardArt(원화 칼날 픽셀)는 뒤집으면 머리 외곽선에서 잘렸던 끝이 머리 밖으로 나와 칼날에 톱니·흰 조각(21:05 char_0019 만들며 찾음) → 칼날은 공격과 같은 이은 칼날, guardArt 는 날밑·손잡이만
    gav[:YCUT, XL:XR + 1] = 0
    W_TIP = np.array([2 * BCX - W_TIP[0], W_TIP[1]])
    Image.fromarray(swv).save(os.path.join(PARTS, 'weapon.png')); Image.fromarray(gav).save(os.path.join(PARTS, 'guardArt.png'))
    print('  blade flipped about x', BCX, 'rows <', YCUT, 'cols', XL, '~', XR)
TIPS_DX = (12, -28) if FLIP_BLADE else (-12, 28)   # 칼끝 두 모서리(날 쪽·등 쪽)도 같이 거울
# 게임 정지 그림(char_0019 — 카드·필살기 컷신) 칼날도 같게 뒤집으려고(tools/art_flip19.py): 대기 때 보이는 칼(원화 칼 픽셀 + 가려진 곳 이은 칼날, 원화 공간) + 세운 그림 변환
_q = (Rm[:, :2] @ np.stack([XX.ravel() * UPS, YY.ravel() * UPS]) + Rm[:, 2:3] - np.array([[x0], [y0]])).reshape(2, 512, 512)
_bladeA = (_q[1] < YCUT) & (_q[0] >= 3) & (_q[0] <= XR) if FLIP_BLADE else np.zeros((512, 512), bool)   # 원화 공간에서 거울하는 칼날 칸
_swi = sw.copy(); _gm2 = _gm & ~_bladeA; _swi[_gm2] = SW0[_gm2]; Image.fromarray(_swi).save(os.path.join(HERE, 'work', 'sword_idle_art.png'))
json.dump({'Rm': Rm.tolist(), 'x0': int(x0), 'y0': int(y0), 'UPS': UPS, 'BCX': BCX if FLIP_BLADE else None, 'YCUT': YCUT if FLIP_BLADE else None, 'XL': 3, 'XR': (XR if FLIP_BLADE else None)},
          open(os.path.join(HERE, 'work', 'sword_flip.json'), 'w'))
Image.fromarray(gav).save(os.path.join(PARTS, 'guardArt.png')); print('  guardArt', int(_gm.sum()), 'px')
print('  sword vertical: tip', np.round(W_TIP, 1), 'grip', np.round(W_PIV, 1), 'rot', round(rot_deg, 2))
# ---------------- 다리 ----------------
def stand_leg(sd, lm):   # 서 있는 다리 = 원화 다리 + 밑단 아래 몸 픽셀 + 밑단 위 6px 검은 바지(치마 밑에 숨음 — 숨쉬기로 치마가 올라가도 틈 없음)
    m = lm | legTop[sd]; a = art(m); hy = hem_y[sd]
    _legc = (m & (YY >= hy) & (YY <= hy + 4)).any(0)
    ext = (YY >= hy - 6) & (YY < hy) & _legc[None, :] & body & (RA[..., 3] > 200) & (XX >= HEMX[sd][0]) & (XX <= HEMX[sd][1])
    f = np.zeros_like(RA); f[..., :3] = np.clip(TR_COL[None, None] + np.random.default_rng(5).normal(0, 2.0, (512, 512, 1)), 0, 255).astype(np.uint8); f[..., 3] = np.where(ext, 255, 0)
    return under(a, f, ext)
_c0 = RA[body & (YY >= 446) & (YY <= 452) & (RA[..., 3] > 200)][:, :3].astype(int); TR_COL = np.median(_c0[(_c0.mean(1) > 25) & (_c0.mean(1) < 80)], 0).astype(np.float32)
o_lN = save('bootStandN', stand_leg('near', lab('legN'))); o_lF = save('bootStandF', stand_leg('far', lab('legF')))
def run_boot(nm, lm):   # 달리는 부츠 = 시트 부츠 그대로(늘이지 않음, 원화 부츠 크기로 ×1.07) · 색 = 원화 부츠, 발목 점 = 목 가운데·밑창 위 18px
    b = col_match(sheet(nm), lm & (YY >= 460)); H_, W_ = b.shape[:2]; b = cv2.resize(b, (int(round(W_ * 1.07)), int(round(H_ * 1.07))), interpolation=cv2.INTER_LANCZOS4)
    ys, xs = np.nonzero(b[..., 3] > 128); piv = (float(xs.min() + (xs.max() - xs.min()) * 0.32), ys.max() - 18.0)
    Image.fromarray(b).save(os.path.join(PARTS, f'{nm}Run.png'))
    bot = {x: ys[xs == x].max() for x in range(xs.min(), xs.max() + 1) if (xs == x).any()}; xl, xr = min(bot), max(bot)
    cols_ = sorted(set(int(round(xl + (xr - xl) * f)) for f in (0.03, 0.25, 0.5, 0.75, 0.97)))
    return piv, [[round(float(x - piv[0]), 1), round(float(bot[x] - piv[1]), 1)] for x in cols_]
RB = {'near': run_boot('bootN', lab('legN')), 'far': run_boot('bootF', lab('legF'))}
def sole_pts(m, ankle, ground=None):
    ys, xs = np.nonzero(m); xl, xr = xs.min(), xs.max(); bot = {x: ys[xs == x].max() for x in range(xl, xr + 1) if (xs == x).any()}
    xlow = max(bot, key=lambda x: bot[x]); cols_ = sorted(set([int(round(xl + (xr - xl) * f)) for f in (0.02, 0.2, 0.8, 0.98)] + [xlow]))
    lift = 0.0 if ground is None else float(ground - bot[xlow])
    return [[float(x - ankle[0]), float(bot[x] - ankle[1] + lift)] for x in cols_ if x in bot]
_c = RA[(lab('legN') | lab('legF') | body) & (YY >= 444) & (YY <= 456) & (RA[..., 3] > 200)][:, :3].astype(int); _l = _c.mean(1)
tr_col = np.median(_c[(_l > 30) & (_l < 95)], 0)   # 치마 밑 검은 바지
print('  trouser colour', tr_col)
TW, TH = 44, 50; xs_ = (np.arange(TW) + .5) / TW
edge = np.clip(1 - np.minimum(xs_, 1 - xs_) / .2, 0, 1) ** 1.5; hl = np.exp(-((xs_ - .36) / .1) ** 2) * .6
base = tr_col.astype(np.float32); col = base[None] * (1 - edge[:, None]) + base[None] * .72 * edge[:, None]; col = col * (1 - hl[:, None]) + base[None] * 1.18 * hl[:, None]
tub = np.zeros((TH, TW, 4), np.float32); tub[..., :3] = col[None] + np.random.default_rng(9).normal(0, 2.0, (TH, TW, 1))
olm = (np.arange(TW) < 2) | (np.arange(TW) >= TW - 2); tub[:, olm, :3] = (24, 24, 30)
yy2 = np.arange(TH)[:, None]; tub[..., 3] = 255 * np.clip((yy2 - 1) / 5, 0, 1) * np.clip((TH - 1 - yy2) / 4, 0, 1)
Image.fromarray(np.clip(tub, 0, 255).astype(np.uint8)).save(os.path.join(PARTS, 'shinP.png'))

# ---------------- 표정·깜빡임 (시트 표정 = 무표정과 다른 곳 + 5px 만 원화 얼굴 자리로, 색 = 원화에 맞춤) ----------------
FACE_N = ['happy', 'angry', 'focus', 'shout', 'effort']; BLINK_N = ['half', 'closed']
SRC = {**{n: f'face_{n}' for n in FACE_N}, 'half': 'blink_half', 'closed': 'blink_closed'}
neu = sheet('face_neutral').astype(np.int16); U_ = np.zeros(neu.shape[:2], bool)
for n in FACE_N + BLINK_N: U_ |= np.abs(sheet(SRC[n]).astype(np.int16) - neu).max(2) > 40
reg = cv2.dilate(U_.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
MF = np.array(GEO['face_neutral']['M'], np.float32)
face = (cv2.warpAffine(reg, MF, (512, 512), flags=cv2.INTER_NEAREST) > 0) & lab('head')
fm = np.clip(cv2.GaussianBlur(cv2.erode(face.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (5, 5), 1.0) * 1.15, 0, 1)
hb = np.array(Image.open(os.path.join(PARTS, 'head.png'))); hx0, hy0 = OFF['head']; hh, hw = hb.shape[:2]
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
    if n in FACE_N:   # 공격 표정: 칼날·날밑이 보이던 머리카락 틈 = 칼 지운 원화 머리카락(대기 머리·깜빡임은 원화 그대로)
        _hf = HFILL[hy0:hy0 + hh, hx0:hx0 + hw] & (fc[..., 3] < 250); fc[_hf] = NOSW[hy0:hy0 + hh, hx0:hx0 + hw][_hf]
    Image.fromarray(fc).save(os.path.join(PARTS, f'face_{n}.png'))
print('  face patch px', int(face.sum()), '· hair gap fill (attack faces)', int(HFILL.sum()))

# ---------------- 뼈·조각 정의 ----------------
SC = 2.0
def piv(name, p): o = np.array(OFF[name], float); q = np.array(p, float) - o; return [round(float(q[0]), 1), round(float(q[1]), 1)]
parts = {}
def P_(name, at, **kw): parts[name] = dict({'src': f'parts/{name}.png', 'pivot': piv(name, at), 'scale': SC}, **kw)
P_('torso', HIP); P_('skirt', HIP, mesh={'cols': 8, 'rows': 6}); P_('head', NECK)
P_('pauldron', SH_N); P_('armU', SH_N, elbow=piv('armU', EL_N)); P_('armL', EL_N, fist=piv('armL', WR_N + (WR_N - EL_N) * .2))
P_('armF', SH_F, elbow=piv('armF', EL_F)); P_('foreF', EL_F); P_('fistF', WR_F)
parts['weapon'] = {'src': 'parts/weapon.png', 'pivot': [round(float(W_PIV[0]), 1), round(float(W_PIV[1]), 1)], 'scale': SC / UPS,
                   'tip': [round(float(W_TIP[0]), 1), round(float(W_TIP[1]), 1)], 'tips': [[round(float(W_TIP[0]) + TIPS_DX[0], 1), round(float(W_TIP[1]) + 10 * UPS, 1)], [round(float(W_TIP[0]) + TIPS_DX[1], 1), round(float(W_TIP[1]) + 10 * UPS, 1)]],
                   'guard': [round(float(W_GUARD[0]), 1), round(float(W_GUARD[1]), 1)], 'pommel': [round(float(W_POM[0]), 1), round(float(W_POM[1]), 1)]}
parts['guardArt'] = {'src': 'parts/guardArt.png', 'pivot': [round(float(W_PIV[0]), 1), round(float(W_PIV[1]), 1)], 'scale': SC / UPS}
for n in FACE_N + BLINK_N: parts[f'face_{n}'] = {'src': f'parts/face_{n}.png', 'pivot': parts['head']['pivot'], 'scale': SC}
for nm, sd in [('bootStandN', 'near'), ('bootStandF', 'far')]: P_(nm, LEG[sd]['ankle'])
for _sd, _nm in (('near', 'bootNRun'), ('far', 'bootFRun')): parts[_nm] = {'src': f'parts/{_nm}.png', 'pivot': [round(RB[_sd][0][0], 1), round(RB[_sd][0][1], 1)], 'scale': SC}
parts['shinP'] = {'src': 'parts/shinP.png', 'pivot': [0, 0], 'scale': 1}
WEAPON_ANG = math.atan2(UT[1], UT[0]) + math.pi / 2
ARML_REST = 0.3   # 엔진이 서 있을 때 자유 팔뚝을 −0.3 rad 굽힘(armL.ar) → 뼈 rot 에 +0.3 을 넣어 대기 = 원화
world = {'root': (O, 0.0), 'hip': (HIP, 0.0), 'skirt': (HIP, 0.0), 'torso': (HIP, 0.0), 'head': (NECK, 0.0), 'pauldron': (SH_N, 0.0), 'armU': (SH_N, 0.0), 'armL': (EL_N, ARML_REST),
         'armF': (SH_F, 0.0), 'foreF': (EL_F, 0.0), 'fistF': (WR_F, 0.0), 'weapon': (G, WEAPON_ANG), 'cape': (NECK, 0.0), 'scarf': (NECK, 0.0), 'pouch': (HIP, 0.0), 'pauldronF': (SH_F, 0.0), 'foreFb': (WR_F, 0.0), 'guardArt': (G, WEAPON_ANG)}
BONES = [('root', None), ('hip', 'root'), ('skirt', 'hip'), ('torso', 'hip'), ('head', 'torso'), ('armF', 'torso'), ('foreF', 'armF'), ('fistF', 'foreF'), ('weapon', 'fistF'),
         ('armU', 'torso'), ('armL', 'armU'), ('pauldron', 'torso'), ('cape', 'torso'), ('scarf', 'torso'), ('pouch', 'hip'), ('pauldronF', 'torso'), ('foreFb', 'torso'), ('guardArt', 'weapon')]
bones = []
for name, parent in BONES:
    if parent is None: bones.append({'name': 'root', 'parent': None, 'pos': [0, 0]}); continue
    (pw_, pa), (cw_, ca) = world[parent], world[name]; dv = (np.array(cw_) - np.array(pw_)) * SC; c, s = math.cos(-pa), math.sin(-pa)
    b = {'name': name, 'parent': parent, 'pos': [round(c * dv[0] - s * dv[1], 1), round(s * dv[0] + c * dv[1], 1)]}
    if abs(ca - pa) > 1e-4: b['rot'] = round(ca - pa, 4)
    if name in parts: b['part'] = name
    bones.append(b)

# ---------------- 다리 (카르덴식: 바지 통 + 부츠, 서 있을 땐 원화 다리) ----------------
hipY = SC * (LEG['near']['hip'][1] - HIP[1])
legs = {'hip': [0, round(hipY, 1)], 'thigh': 48, 'shin': 48,
        'thighImg': {'part': 'shinP', 'a': [22, 0], 'b': [22, 46], 'w': 0.001}, 'shinImg': {'part': 'shinP', 'a': [22, 0], 'b': [22, 46], 'w': 0.001},
        'boot': {'part': 'bootFRun', 'sole': RB['far'][1], 'ankleRange': [-1.7, 1.7]},
        'tube': {'part': 'shinP', 'a': [22, 0], 'b': [22, 46], 'k': 1.2, 'runBoot': True}}   # 바지 통 굵기 1.2(29 v1.7 — 서 있을 때 원화 밖으로 삐져나오지 않게)
for sd, nm, lm in [('near', 'bootStandN', lab('legN') | legTop['near']), ('far', 'bootStandF', lab('legF') | legTop['far'])]:
    legs[sd] = {'x': round(SC * (LEG[sd]['hip'][0] - HIP[0]), 1), 'shade': 0, 'thighImg': legs['thighImg'], 'shinImg': legs['shinImg'], 'runBoot': 'bootNRun' if sd == 'near' else 'bootFRun',
                'stand': {'fade': [0.12, 0.4], 'boot': {'part': nm, 'sole': sole_pts(lm, LEG[sd]['ankle'], O[1])}}}
idle = {sd: round(SC * (LEG[sd]['ankle'][0] - LEG[sd]['hip'][0]), 1) for sd in ('near', 'far')}
# 그리는 순서 (뒤 → 앞): 먼 다리 · 가까운 다리 · 상체 · 치마 · 먼 팔뚝 · 칼(칼날은 머리 뒤) · 가까운 윗팔 · 가까운 팔뚝+주먹 · 어깨갑 · 머리+수염(+표정) · 먼 손
draw = ['legFar', 'legNear', 'torso', 'skirt', 'foreF', 'weapon', 'guardArt', 'armU', 'armL', 'pauldron', 'head', 'fistF']
rig = {'name': 'palome-neon', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': parts, 'bones': bones, 'legs': legs, 'draw': draw, 'hidden': [], 'faces': {n: f'face_{n}' for n in FACE_N},
       'blinkFaces': {'half': 'face_half', 'closed': 'face_closed'}, 'idleStance': idle,
       'gait': {'stance': 0.18, 'strideBase': 14, 'strideK': 0.06, 'hipBase': 0, 'bob': 6, 'lean': 0.06, 'waddle': 0.02, 'headBob': 3, 'kneeLift': 0.2, 'heelKick': 0.03, 'dropCap': 12,
                'swingReach': 0.05, 'landAng': -0.04, 'angK': 0.2, 'elbowRun': 0.22, 'armSwing': 0.16, 'armBias': 0.0, 'headRun': 0.06},
       'hemRun': {'lift': 8, 'knee': 0.5, 'heel': 0.3, 'reach': 0.2}, 'hemLimit': {'up': 0.25, 'x': 0.3}, 'hemGain': 0.15, 'footReach': 0.97,
       'follow': [{'bone': 'pauldron', 'src': 'armU', 'k': 0.3}], 'skirtFollow': 0.7, 'carrySwing': 0.15, 'wristRange': 0.2, 'dropLift': 10,
       'bounce': [], 'metrics': {'bodyHeight': round(2 * (501 - 159)), 'note': 'rig units; 머리카락 위(y159)~발바닥(501) ×2, 칼 제외'},
       'ui': {'attack': 'smash', 'touch': 'hop'},
       'gameRef': {'refOrigin': [round(float(O[0] - (HIP[0] - FIT_CX)), 1), float(O[1])], 'refScale': 2.0, 'refLift': 0,
                   'note': f'게임 그림 char_0019.png(512) = 새 원화(ref512)에서 칼날만 좌우 반전(tools/art_flip19.py, v1.3). x = 도감 칸(fitArt 중심 {FIT_CX}, index.html measureBox 와 같은 계산)에서 골반(hip x 288)이 가운데 (9·29 팔로메와 같은 규칙)'},
       'note': '19 네온 팔로메 v1(대기·달리기·한 손 내려찍기). 9 러스트 팔로메 구조(드워프 몸, 먼 팔이 칼을 어깨에 멤, 칼날 머리 뒤). 조각 = 원화를 부품별로 나눔(seg19.py) + 가려진 곳만 시트·inpaint 로 메움'}
exec(open(os.path.join(HERE, 'attack_neon19.py'), encoding='utf-8').read())   # 한 손 내려찍기(9 v1.1 지렛대)
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(PARTS)): _h.update(fn.encode()); _h.update(open(os.path.join(PARTS, fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_neon19.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['palome-neon']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(parts), 'parts, version', rig['version'], 'idle', idle, 'legs x', legs['near']['x'], legs['far']['x'], 'hipY', legs['hip'])
