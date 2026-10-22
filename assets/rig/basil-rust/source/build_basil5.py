"""5 러스트 바실 리그 조립 v2 — 대기 · 달리기 · 뒷손 펀치(v1 = 두 주먹 내려찍기)
입력: ref512.png(원화 = 게임 char_0005) · sheets/nonear_2052.png·nofar_2105.png(팔·건틀릿만 지운 원화, 프롬프트 2·3) · work/body512.png·labels.npy(seg5.py)
      pieces/(조각 시트 21칸, cut5.py) · measure5.json
출력: ../rig.json · ../rig.def.js · ../parts/*.png · review/keys5.json
실행: cd source && python3 -I cut5.py && python3 -I seg5.py && python3 -I build_basil5.py
원칙(DHL): 대기 = 원화 · 건틀릿 크기 그대로 · 팔다리 길이 고정 · 공격 중 눈 뜸 · 달릴 때 발목 고정
구조: 무기 없음 — 엔진 sword 동작(swordGrip)을 그대로 씀: 먼 건틀릿 = 쥔 팔 조각(gF, 주먹 자리 gx·gy 를 키로, 먼 팔 길이 고정 IK),
      가까운 건틀릿 = freeArm(윗팔 fuA·건틀릿 flA 각 키). weapon 뼈 = 먼 주먹 자리의 보이지 않는 점(맞는 자리 = 먼 주먹)
      가까운 건틀릿은 원화에서 조끼 자락 뒤 → 대기·예비는 상체 뒤(drawA), 머리 위로 든 뒤부터 몸 앞(drawB)
좌표: 원화 512px 로 적고, 리그 단위 = ×2
"""
import json, math, os, shutil, hashlib
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); PC = os.path.join(HERE, 'pieces'); W = os.path.join(HERE, 'work'); OUT = os.path.join(HERE, '..'); PARTS = os.path.join(OUT, 'parts')
if os.path.isdir(PARTS): shutil.rmtree(PARTS)
os.makedirs(PARTS); os.makedirs(os.path.join(HERE, 'review'), exist_ok=True)
RA = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA'))
BODY = np.array(Image.open(os.path.join(W, 'body512.png')).convert('RGBA'))
LAB = np.load(os.path.join(W, 'labels.npy')); NAMES = json.load(open(os.path.join(W, 'label_names.json'))); LID = {n: i + 1 for i, n in enumerate(NAMES)}
lab = lambda *ns: np.logical_or.reduce([LAB == LID[n] for n in ns])
M = json.load(open(os.path.join(HERE, 'measure5.json')))
YY, XX = np.mgrid[0:512, 0:512]
V = lambda p: np.array(p, float)
SC = 2.0
def dil(m, r): return cv2.dilate(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))) > 0
def desp(a):
    a = a.astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None); a[..., 0] -= m; a[..., 2] -= m; return np.clip(a, 0, 255).astype(np.uint8)
def sheet(n): return desp(np.array(Image.open(os.path.join(PC, n + '.png')).convert('RGBA')))
def under(a, b, where):
    out = a.copy(); w = where & (b[..., 3] > 0) & (a[..., 3] < 250); fa = a[..., 3:4] / 255.0; fb = b[..., 3:4] / 255.0
    col = a[..., :3] * fa + b[..., :3] * fb * (1 - fa); al = fa + fb * (1 - fa)
    out[w, :3] = np.clip(col[w] / np.maximum(al[w], 1e-3), 0, 255).astype(np.uint8); out[w, 3] = np.clip(al[w, 0] * 255, 0, 255).astype(np.uint8); return out
def despeck(a, minpx=14):
    n, cc, st, _ = cv2.connectedComponentsWithStats((a[..., 3] > 0).astype(np.uint8), 8); a = a.copy()
    for i in range(1, n):
        if st[i, 4] < minpx: a[cc == i] = 0
    return a
OFF = {}
def save(name, a, pad=2):
    d_ = despeck(a, 40 if name in ('armL', 'foreF', 'armF') else 14); a = d_ if (d_[..., 3] > 0).any() else a
    ys, xs = np.nonzero(a[..., 3] > 0); x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad); x1, y1 = min(a.shape[1], xs.max() + 1 + pad), min(a.shape[0], ys.max() + 1 + pad)
    Image.fromarray(a[y0:y1, x0:x1]).save(os.path.join(PARTS, name + '.png')); OFF[name] = (x0, y0)
# ---------------- 관절(지운 원화로 다시 잼 — 가까운 어깨 = 조끼 소매 구멍 가운데, 팔꿈치 = 시트 건틀릿 소매 입구를 원화 자리로 옮긴 곳) ----------------
SOLE = float(M['sole_y']); HIP = V(M['hip']); NECK = V(M['neck']); PONY = V(M['pony'])
LEG = {sd: {k: V(v) for k, v in M['legs'][sd].items() if k != 'len'} for sd in ('near', 'far')}
O = V([(LEG['near']['ankle'][0] + LEG['far']['ankle'][0]) / 2, SOLE])
SH_N, EL_N, FI_N = V([167, 243]), V([196, 250]), V([148, 338])
SH_F, EL_F, FI_F = V([306, 218]), V([338, 234]), V([440, 272])
# ---------------- 팔 = 원화 − 지운 원화 ----------------
NONEAR = np.array(Image.open(os.path.join(HERE, 'sheets', 'nonear_2052.png')).convert('RGBA')); NOFAR = np.array(Image.open(os.path.join(HERE, 'sheets', 'nofar_2105.png')).convert('RGBA'))
def poly(pts): m = np.zeros((512, 512), np.uint8); cv2.fillPoly(m, [np.array(pts, np.int32)], 1); return m > 0
def capm(p, q, r):
    p, q = V(p), V(q); d = q - p; L2 = max(d @ d, 1e-9); t = np.clip(((XX - p[0]) * d[0] + (YY - p[1]) * d[1]) / L2, 0, 1)
    return (XX - (p[0] + t * d[0])) ** 2 + (YY - (p[1] + t * d[1])) ** 2 <= r * r
def changed(IMG, sd):
    s = M[sd]; area = dil(poly(s['gaunt']) | capm(s['SH'], s['EL'], 30), 12)
    ch = (np.abs(RA.astype(int) - IMG.astype(int)).max(-1) > 24) & (RA[..., 3] > 0) & area
    ch = cv2.morphologyEx(ch.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
    return ch & (RA[..., 3] > 0) & area
ARM_N, ARM_F = changed(NONEAR, 'near'), changed(NOFAR, 'far')
_sift = cv2.SIFT_create(4000)
def _gr(a): al_ = a[..., 3:4] / 255.0; return cv2.cvtColor((a[..., :3] * al_ + 128 * (1 - al_)).astype(np.uint8), cv2.COLOR_RGB2GRAY)
def fit_sheet(nm, region):   # 시트 조각 → 원화(닮음 변환, SIFT)
    SM = sheet(nm); k1, d1 = _sift.detectAndCompute(_gr(SM), ((SM[..., 3] > 128) * 255).astype(np.uint8)); k2, d2 = _sift.detectAndCompute(_gr(RA), (region * 255).astype(np.uint8))
    mm = [a for a, b in cv2.BFMatcher().knnMatch(d1, d2, k=2) if a.distance < .75 * b.distance]
    T, inl = cv2.estimateAffinePartial2D(np.float32([k1[a.queryIdx].pt for a in mm]), np.float32([k2[a.trainIdx].pt for a in mm]), ransacReprojThreshold=2.0)
    ws = cv2.warpAffine(SM, T, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
    print(f'  {nm}: 시트 SIFT {int(inl.sum())}점 ×{np.hypot(T[0, 0], T[1, 0]):.3f} 회전 {math.degrees(math.atan2(T[1, 0], T[0, 0])):+.1f}°')
    return ws
GW_N = fit_sheet('gauntN', ARM_N); GW_F = fit_sheet('gauntF', ARM_F)
GM_N = dil(GW_N[..., 3] > 100, 2); GM_F = dil(GW_F[..., 3] > 100, 2)
#   가까운 팔 = 시트 건틀릿 실루엣 안 + 왼쪽 위 주황 맨살(건틀릿 뒤 팔) — 그 밖에서 바뀐 픽셀(지운 원화가 다시 그린 조끼 자락·허리 가죽끈)은 몸 몫
_drop = ARM_N & ~(dil(GM_N, 3) | ((XX < 150) & (YY < 300))); ARM_N = ARM_N & ~_drop; _rgb = RA[..., :3].astype(int); _green = (np.abs(_rgb[..., 0] - _rgb[..., 1]) < 18) & (_rgb[..., 1] - _rgb[..., 2] > 22) & (_rgb[..., 0] < 175) & (XX > 140)   # 조끼 국방색 자락
_green = dil(_green, 1) & ~(GW_N[..., 3] > 0) | _green; _green |= dil(_green, 4) & (_rgb.mean(-1) < 70) & (XX > 140) & (YY < 300); _drop |= ARM_N & _green; ARM_N = ARM_N & ~_green   # + 자락 외곽선
BODY[_drop] = RA[_drop]; print('  가까운 팔에서 뺀 몸 픽셀(몸 조각엔 원화 그대로)', int(_drop.sum()))
def place_limb(nm, S, E):   # 시트 윗팔(곧게 선 그림) → 어깨 S 에서 팔꿈치 E 쪽으로(배율 1 — 늘이지 않음), 위 둥근 끝 가운데 = 어깨
    p = sheet(nm); ys, xs = np.nonzero(p[..., 3] > 128); cx = (xs.min() + xs.max()) / 2; wtop = (p[ys.min() + 6, :, 3] > 128).sum(); a = np.array([cx, ys.min() + wtop / 2])
    d = (E - S) / np.linalg.norm(E - S); th = math.atan2(d[1], d[0]) - math.pi / 2; c, s = math.cos(th), math.sin(th)
    T = np.array([[c, -s, S[0] - (c * a[0] - s * a[1])], [s, c, S[1] - (s * a[0] + c * a[1])]], np.float32)
    return cv2.warpAffine(p, T, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
def art(m): a = RA.copy(); a[..., 3] = np.where(m, a[..., 3], 0); return a
# 가까운 건틀릿(armL) = 원화 가까운 팔 전부 + 가려진 곳(조끼 자락 뒤 소매 입구) = 시트 건틀릿
_holes = (cv2.morphologyEx(ARM_N.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))) > 0) & ~ARM_N
armL = under(art(ARM_N), GW_N, GM_N & _holes)   # v3.2: 건틀릿이 늘 맨 앞(DHL 09:49) — 조끼 자락 뒤 소매 입구(시트 주황 통)는 안 채움(턱 앞에 주황 통이 보였음), 실루엣 안 구멍만 시트로   # 원화에서 다른 것(조끼 자락)에 가려진 곳만 — 실루엣 밖은 안 채움(대기 = 원화)
# 가까운 윗팔(armU) = 시트 윗팔(대기엔 조끼·건틀릿 뒤라 안 보임)
armU = place_limb('upperN', SH_N, EL_N)
# 먼 팔: 원화 − 지운 원화 = 윗팔 맨살 + 건틀릿 → 시트 건틀릿 자리로 나눔
UPF_m = ARM_F & ~GM_F; GAF_m = ARM_F & GM_F
def biggest(m):   # 가장 큰 덩어리만(건틀릿 둘레에 떨어진 부스러기 — 공격 때 먼 윗팔을 따라 허공에 점으로 떴음)
    n, cc, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8); return (cc == 1 + int(np.argmax(st[1:, 4]))) if n > 1 else m
_isl = UPF_m & ~biggest(UPF_m); UPF_m = UPF_m & ~_isl; GAF_m = GAF_m | _isl
# v3.5 (DHL 12:17 '팔은 뒤로 젖히면서 깨지는 것 같다'): 원인 = 원화 먼 윗팔 살 대부분이 시트 건틀릿 모양(GM_F) 안이라 '건틀릿 조각'에 붙어 있었음
#   → 팔이 돌면 살 띠가 건틀릿을 따라가고 윗팔 조각(240px)은 시트 팔과 섞여 갈라져 보임
#   고침: 원화 '바뀐 곳'에서 살색 덩어리(어깨~건틀릿 소매 테) = 먼 윗팔, 나머지 = 건틀릿. 윗팔 둘레 외곽선은 원화 선, 턱과 맞닿은 쪽은 원화 외곽선 색 2px(턱선은 머리 조각이 가짐)
_r, _g, _b = (RA[..., c].astype(int) for c in range(3)); _lumR = RA[..., :3].astype(int).mean(-1)
_sk = ARM_F & (_r > 165) & (_g > 95) & (_r - _b > 55) & (_lumR > 120)
_sk = biggest(_sk); _sk = cv2.morphologyEx(_sk.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))) > 0
_sk = (_sk | (ARM_F & (cv2.morphologyEx(_sk.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0))) & (RA[..., 3] > 0)   # 살 안 흉터·점
_jl = dil(lab('head'), 4) & (_lumR < 120) & (RA[..., 3] > 0)
JAW_OUT = _jl & dil(_sk, 3)                                   # 턱 외곽선 → 머리 조각
_line = dil(_sk, 2) & ARM_F & (_lumR < 70) & ~_sk & ~_jl & (XX < 340)   # 윗팔 위·아래 원화 외곽선(소매 테 쪽은 건틀릿 몫)
UPF_m = _sk | _line; GAF_m = ARM_F & ~UPF_m
_gop = biggest(cv2.morphologyEx(GAF_m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0); _str = GAF_m & ~dil(_gop, 1)   # 건틀릿 밖 가는 선 토막(윗팔 위 외곽선 끝) → 윗팔
UPF_m = UPF_m | (_str & dil(_sk, 6)); GAF_m = GAF_m & ~_str
armF = art(UPF_m)
_ring = dil(_sk, 2) & ~_sk & ~_line & _jl                     # 턱과 맞닿던 쪽 = 윗팔 자기 외곽선
_oc = np.array([28, 16, 12], np.uint8); armF[_ring, :3] = _oc; armF[_ring, 3] = 255
print('  먼 윗팔 = 원화 살', int(_sk.sum()), '+ 외곽선', int(_line.sum() + _ring.sum()), 'px · 건틀릿', int(GAF_m.sum()))
# v3.7 (DHL 15:14 '팔이 비어 있어요'): 원화에 보이는 윗팔 살은 턱·건틀릿 사이 가는 쐐기뿐 → 팔을 들면 건틀릿 소매 입구까지 빈 곳
#   → 어깨~소매 입구 안쪽까지 둥근 팔 통(반지름 ARM_R)을 원화 살색으로 깔고 외곽선, 원화 살·선은 그 위 그대로. 대기엔 머리·건틀릿이 덮음
ARM_R = float(os.environ.get('ARM_R', 16)); _ud = (EL_F - SH_F) / np.linalg.norm(EL_F - SH_F)
_tubeA = capm(SH_F, EL_F + _ud * 16, ARM_R)   # 공격용 통(전부)
_tube = _tubeA & (RA[..., 3] > 200) & ~(lab('torso') & ~dil(_sk, 3))   # 대기용: 원화 실루엣 안·조끼 밖만(대기에 삐져나오지 않게)
_skc = np.median(RA[_sk & (_lumR > 150)][:, :3], 0).astype(np.uint8)
_tin = _tube & ~(cv2.erode(_tube.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)
_tb = np.zeros_like(RA); _tb[_tube, :3] = _skc; _tb[_tube, 3] = 255; _tb[_tin, :3] = _oc
_ys2 = (YY - SH_F[1]).astype(float); _shade = _tube & (((XX - SH_F[0]) * -_ud[1] + (YY - SH_F[1]) * _ud[0]) > ARM_R * .35)   # 아래쪽 그늘
_tb[_shade & ~_tin, :3] = (_skc.astype(float) * .82).astype(np.uint8)
_tbA = np.zeros_like(RA); _tbA[_tubeA, :3] = _skc; _tbA[_tubeA, 3] = 255
_tinA = _tubeA & ~(cv2.erode(_tubeA.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0); _tbA[_shade & ~_tinA, :3] = (_skc.astype(float) * .82).astype(np.uint8); _tbA[_tinA, :3] = _oc
_shadeA = _tubeA & (((XX - SH_F[0]) * -_ud[1] + (YY - SH_F[1]) * _ud[0]) > ARM_R * .35); _tbA[_shadeA & ~_tinA, :3] = (_skc.astype(float) * .82).astype(np.uint8)
# v3.8 (DHL 15:32 '표시한 부분 이상 — 통으로 어깨부터 연결된 이미지로, 앞 팔처럼'): 공격용 윗팔 = 둥근 팔 통 하나(외곽선 = 통 가장자리)
#   원화 살 쐐기의 뾰족한 외곽선을 위에 얹지 않음 — 통 안쪽에만 원화 살 무늬(밝은 살·흉터, 어두운 선 뺌)를 옮겨 그림
#   v3.8b: 통 대신 시트 14번 먼 윗팔(근육·음영 그린 팔)을 어깨→팔꿈치 방향으로(배율 1.1 — 굵기 = 원화 팔), 원화 살색으로 색 맞춤
_sp = place_limb('upperF', SH_F, EL_F)
_sp = cv2.warpAffine(_sp, cv2.getRotationMatrix2D((float(SH_F[0]), float(SH_F[1])), 0, float(os.environ.get('UPF_K', 1.25))), (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
_m = _sp[..., 3] > 200; _ref = RA[_sk & (_lumR > 120)][:, :3].astype(float)
_spf = _sp.astype(float)
for c in range(3):
    v = _spf[..., c][_m]; _spf[..., c] = np.where(_sp[..., 3] > 0, (_spf[..., c] - v.mean()) / max(1.0, v.std()) * _ref[:, c].std() + _ref[:, c].mean(), _spf[..., c])
_dark = (_sp[..., :3].astype(int).mean(-1) < 70); _spf[_dark, :3] = _sp[_dark, :3]   # 외곽선은 시트 선 그대로
armFA = np.clip(_spf, 0, 255).astype(np.uint8)
armF = under(armF, _tb, _tube & (armF[..., 3] < 250))
print('  먼 윗팔 통 깔기', int((_tube & ~UPF_m).sum()), 'px · 반지름', ARM_R)
foreF = art(GAF_m)   # 먼 건틀릿은 맨 앞 — 가려진 곳 없음(시트 ×1.055 라 채우면 둘레에 테가 생김)
print('  팔 px: 가까운', int(ARM_N.sum()), '(건틀릿 + 시트 보탬', int(((armL[..., 3] > 0) & ~ARM_N).sum()), ') · 먼 윗팔', int(UPF_m.sum()), '· 먼 건틀릿', int(GAF_m.sum()))
# ---------------- 몸: 합친 몸 그림(팔 없음)을 라벨로 — 대기에 팔보다 앞에 그리는 조각(상체·머리·상투)의 팔 밑 픽셀은 뒤 조각(…B)으로 ----------------
DRAW_IDLE = ['legFar', 'legNear', 'skirt', 'belt', 'torsoB', 'armU', 'armL', 'armLp', 'torso', 'headB', 'armF', 'foreF', 'head', 'pony']
ARM_OF = {'near': ('armL', ARM_N), 'far': ('armF', ARM_F)}
BONE_OF = {'head': 'head', 'pony': 'pony', 'torso': 'torso', 'belt': 'belt', 'hips': 'skirt', 'legN': 'legNear', 'legF': 'legFar'}
def body(n): a = BODY.copy(); a[..., 3] = np.where(LAB == LID[n], a[..., 3], 0); return a
PIECE, BACKP = {}, {}
for n in NAMES:
    a = body(n); back = np.zeros((512, 512), bool)
    for sd, (ab, am) in ARM_OF.items():
        if DRAW_IDLE.index(BONE_OF[n]) > DRAW_IDLE.index(ab): back |= am & (LAB == LID[n])
    if back.any():
        b_ = a.copy(); b_[~back, 3] = 0; a[back, 3] = 0; BACKP[n] = b_
    PIECE[n] = a
print('  뒤 조각 px', {k: int((v[..., 3] > 0).sum()) for k, v in BACKP.items()})
def underlay(a, back_m, front_m, r=4):   # 이음 밑 덧칠: 뒤 조각에 앞 조각 경계 r px 를 원화로(앞 조각이 움직여도 틈 대신 원화)
    band = front_m & dil(back_m, r) & (BODY[..., 3] >= 250) & (a[..., 3] == 0); a = a.copy(); a[band] = BODY[band]; return a, int(band.sum())
PIECE['torso'], _u1 = underlay(PIECE['torso'], lab('torso'), lab('head', 'pony'), 5)
PIECE['belt'], _u2 = underlay(PIECE['belt'], lab('belt'), lab('torso'), 5)
PIECE['hips'], _u3 = underlay(PIECE['hips'], lab('hips'), lab('belt'), 8)
PIECE['head'], _u4 = underlay(PIECE['head'], lab('head'), lab('pony'), 4)
PIECE['head'] = PIECE['head'].copy(); PIECE['head'][JAW_OUT] = RA[JAW_OUT]; print('  턱 외곽선(먼 팔 몫이던 것) → 머리 조각', int(JAW_OUT.sum()), 'px')
print('  이음 밑 덧칠 px 상체←머리', _u1, '· 허리띠←상체', _u2, '· 바지←허리띠', _u3, '· 머리←상투', _u4)
for n, nm in (('head', 'head'), ('pony', 'pony'), ('torso', 'torso'), ('belt', 'belt'), ('hips', 'hips')): save(nm, PIECE[n])
for n, b_ in BACKP.items(): save(n + 'B', b_)
save('armU', armU); save('armL', armL); save('armF', armF); save('armFA', armFA); save('foreF', foreF)
Image.fromarray(np.zeros((4, 4, 4), np.uint8)).save(os.path.join(PARTS, 'weapon.png'))
# ---------------- 다리: 서 있을 땐 원화 다리(발목 핀), 달리면 시트 허벅지·정강이·샌들 ----------------
def sole_pts(m, ankle, ground=None):
    ys, xs = np.nonzero(m); xl, xr = xs.min(), xs.max(); bot = {x: ys[xs == x].max() for x in range(xl, xr + 1) if (xs == x).any()}
    xlow = max(bot, key=lambda x: bot[x]); cols_ = sorted(set([int(round(xl + (xr - xl) * f)) for f in (0.02, 0.2, 0.8, 0.98)] + [xlow]))
    lift = 0.0 if ground is None else float(ground - bot[xlow]); return [[float(x - ankle[0]), float(bot[x] - ankle[1] + lift)] for x in cols_ if x in bot]
save('bootStandN', PIECE['legN']); save('bootStandF', PIECE['legF'])
def run_boot(nm, sd):
    up = SOLE - LEG[sd]['ankle'][1]; b = sheet(nm); ys, xs = np.nonzero(b[..., 3] > 128); piv = (float(xs.min() + (xs.max() - xs.min()) * 0.32), ys.max() - up)
    Image.fromarray(b).save(os.path.join(PARTS, f'{nm}Run.png')); bot = {x: ys[xs == x].max() for x in range(xs.min(), xs.max() + 1) if (xs == x).any()}; xl, xr = min(bot), max(bot)
    return piv, [[round(float(x - piv[0]), 1), round(float(bot[x] - piv[1]), 1)] for x in sorted(set(int(round(xl + (xr - xl) * f)) for f in (0.03, 0.25, 0.5, 0.75, 0.97)))]
RB = {'near': run_boot('sandalN', 'near'), 'far': run_boot('sandalF', 'far')}
L_TH = float(max(np.linalg.norm(LEG[s]['knee'] - LEG[s]['hip']) for s in LEG)); L_SH = float(max(np.linalg.norm(LEG[s]['ankle'] - LEG[s]['knee']) for s in LEG))
# 달리는 다리 길이(DHL 10-22 09:36 '달릴 때 너무 구부린 다리, 살짝 펴 주세요'): 원화 다리는 옆으로 벌린 길이(허벅지 59.9)라 옆모습 달리기엔 엉덩이~발목 높이(63)보다 훨씬 김 → 늘 무릎이 107~180° 접힘
#   → 엉덩이~무릎(바짓단) 세로 · 무릎~발목 세로로: 허벅지 36 · 정강이 30(합 66 ≈ 엉덩이~발목 63 + 걸음 여유) — 시트 조각은 길이만 줄여 그림(굵기 w 따로)
STAND_K = float(os.environ.get('STAND_K', 0.95))   # v3.6: 서 있는 다리 뼈 = 원화 길이 ×.95 — 다리 뿌리를 안쪽으로 옮기니 ×1 이면 서 있는 원화 다리가 발목에서 끌려 대기가 원화와 달라짐(차 > 60 px 878)
L_TH0, L_SH0 = L_TH * STAND_K, L_SH * STAND_K   # 서 있을 때(원화 다리 그림) 다리 길이 — 엔진 legs.near/far.thigh·shin(A 0) → 달리기(A 1) legs.thigh·shin 으로 섞임
L_TH = float(os.environ.get('RUN_TH', 33)); L_SH = float(os.environ.get('RUN_SH', 28))
def limb_piece(nm, L):   # 관절 점 a·b = 위·아래 끝에서 같은 만큼 안쪽 — a-b = 뼈 길이(배율 ≈ 1, 늘이지 않음)
    p = sheet(nm); Image.fromarray(p).save(os.path.join(PARTS, nm + '.png'))
    ys, xs = np.nonzero(p[..., 3] > 128); cx = float((xs.min() + xs.max()) / 2)
    if nm.startswith('thigh'): b = float(ys.max() - 10); a = b - L   # 무릎(아래 둥근 끝 가운데) = b, 위로 남는 바지는 반바지 밑에 숨음
    else: a = float(ys.min() + 10); b = a + L                       # 무릎(위 둥근 끝 가운데) = a, 아래 남는 붕대는 샌들 쪽
    return {'part': nm, 'a': [round(cx, 1), round(a, 1)], 'b': [round(cx, 1), round(b, 1)], 'w': 1.0}
TH = {'near': limb_piece('thighN', L_TH), 'far': limb_piece('thighF', L_TH)}
SHN = {'near': limb_piece('shinN', L_SH), 'far': limb_piece('shinF', L_SH)}
SHIN_W = float(os.environ.get('SHIN_W', 0.72))   # 시트 정강이 48px(무릎 공 포함) → 원화 종아리 굵기 ≈ 34
for _d in SHN.values(): _d['w'] = SHIN_W
for _d in TH.values(): _d['w'] = float(os.environ.get('THIGH_W', 0.75))   # 바지 다리 — 반바지 밑단 밖으로 불룩 나오지 않게
print('  다리 길이 허벅지', round(L_TH, 1), '정강이', round(L_SH, 1), '· 시트 a-b', {k: round(v['b'][1] - v['a'][1], 1) for k, v in {**{'th_' + s: TH[s] for s in TH}, **{'sh_' + s: SHN[s] for s in SHN}}.items()})
# ---------------- 표정·깜빡임: 시트 머리 → 원화 머리 자리(SIFT), 무표정과 다른 곳(눈·눈썹·입 둘레 타원 안)만 ----------------
head_m = lab('head')
sift = cv2.SIFT_create()
def gray(a): al = a[..., 3:4] / 255.0; return cv2.cvtColor((a[..., :3] * al + 128 * (1 - al)).astype(np.uint8), cv2.COLOR_RGB2GRAY)
def up(a, k): return cv2.resize(a, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
kA, dA = sift.detectAndCompute(up(gray(RA), 2), (up((head_m * 255).astype(np.uint8), 2) > 0).astype(np.uint8) * 255)
neu_s = sheet('face_neutral'); kS, dS = sift.detectAndCompute(up(gray(neu_s), 2), (up(neu_s[..., 3], 2) > 20).astype(np.uint8) * 255)
good = [a for a, b in cv2.BFMatcher().knnMatch(dS, dA, k=2) if a.distance < .75 * b.distance]
MF, inl = cv2.estimateAffinePartial2D(np.float32([kS[a.queryIdx].pt for a in good]) / 2, np.float32([kA[a.trainIdx].pt for a in good]) / 2, ransacReprojThreshold=2.0)
print('  face SIFT', int(inl.sum()), 'scale', round(float(np.hypot(MF[0, 0], MF[1, 0])), 4), 'rot', round(math.degrees(math.atan2(MF[1, 0], MF[0, 0])), 2))
FACE_N = ['happy', 'angry', 'focus', 'shout', 'effort']; BLINK_N = ['half', 'closed']
SRCF = {'happy': 'face_happy', 'angry': 'face_angry', 'focus': 'face_focus', 'shout': 'face_shout', 'effort': 'face_effort', 'half': 'blink_half', 'closed': 'blink_closed'}
neu = neu_s.astype(np.int16); U_ = np.zeros(neu.shape[:2], bool)
for n in FACE_N + BLINK_N:
    s_ = sheet(SRCF[n]).astype(np.int16)
    if s_.shape != neu.shape: s_ = cv2.resize(s_.astype(np.uint8), (neu.shape[1], neu.shape[0]), interpolation=cv2.INTER_AREA).astype(np.int16)
    U_ |= np.abs(s_ - neu).max(2) > 40
reg = cv2.dilate(U_.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
FACE_EL = (((XX - 270) / 46.0) ** 2 + ((YY - 208) / 44.0) ** 2) <= 1   # 눈·눈썹·입 둘레(머리숱·반창고 밖)
face = (cv2.warpAffine(reg, MF, (512, 512), flags=cv2.INTER_NEAREST) > 0) & head_m & FACE_EL
fm = np.clip(cv2.GaussianBlur(cv2.erode(face.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (5, 5), 1.0) * 1.15, 0, 1)
hb = np.array(Image.open(os.path.join(PARTS, 'head.png'))); hx0, hy0 = OFF['head']; hh, hw = hb.shape[:2]
wn = cv2.warpAffine(neu_s, MF, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0)).astype(np.float32); cm = face & (wn[..., 3] > 200) & (RA[..., 3] > 200)
CA = [(RA[..., c][cm].astype(np.float32).std() / max(1.0, wn[..., c][cm].std()), 0.0) for c in range(3)]
CA = [(a, float(RA[..., c][cm].mean() - a * wn[..., c][cm].mean())) for c, (a, _) in enumerate(CA)]
for n in FACE_N + BLINK_N:
    sp = sheet(SRCF[n]); k2, d2 = sift.detectAndCompute(up(gray(sp), 2), (up(sp[..., 3], 2) > 20).astype(np.uint8) * 255)
    mm = [a for a, b in cv2.BFMatcher().knnMatch(d2, dS, k=2) if a.distance < .7 * b.distance]; Mrel = None
    if len(mm) >= 12: Mrel, _ = cv2.estimateAffinePartial2D(np.float32([k2[a.queryIdx].pt for a in mm]) / 2, np.float32([kS[a.trainIdx].pt for a in mm]) / 2, ransacReprojThreshold=1.5)
    Mn = MF if Mrel is None else (np.vstack([MF, [0, 0, 1]]) @ np.vstack([Mrel, [0, 0, 1]]))[:2]
    wf = cv2.warpAffine(sp, Mn, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0)).astype(np.float32)
    for c in range(3): wf[..., c] = np.clip(wf[..., c] * CA[c][0] + CA[c][1], 0, 255)
    al = fm * (wf[..., 3] / 255.0); o_ = np.zeros((512, 512, 4), np.float32); o_[hy0:hy0 + hh, hx0:hx0 + hw] = hb
    o_[..., :3] = o_[..., :3] * (1 - al[..., None]) + wf[..., :3] * al[..., None]
    fc = o_[hy0:hy0 + hh, hx0:hx0 + hw].astype(np.uint8); fc[..., 3] = hb[..., 3]
    Image.fromarray(fc).save(os.path.join(PARTS, f'face_{n}.png'))
print('  face patch px', int(face.sum()))
# ---------------- 뼈·조각 ----------------
def piv(name, p): o = np.array(OFF[name], float); q = np.array(p, float) - o; return [round(float(q[0]), 1), round(float(q[1]), 1)]
parts = {}
def P_(name, at, **kw): parts[name] = dict({'src': f'parts/{name}.png', 'pivot': piv(name, at), 'scale': SC}, **kw)
P_('torso', HIP); P_('hips', HIP); P_('belt', HIP); P_('head', NECK); P_('pony', PONY)
BACKB = {}
for n in BACKP:
    nm = n + 'B'; pt = {'torso': HIP, 'head': NECK, 'pony': PONY, 'belt': HIP, 'hips': HIP}[n]; P_(nm, pt); BACKB[nm] = ({'hips': 'skirt'}.get(n, n), pt)
P_('armU', SH_N, elbow=piv('armU', EL_N)); P_('armF', SH_F, elbow=piv('armF', EL_F)); P_('armFA', SH_F, elbow=piv('armFA', EL_F))
P_('armL', EL_N, fist=piv('armL', FI_N)); P_('foreF', EL_F)
# 펀치 건틀릿(armLp): 가까운 건틀릿 그림은 소매 입구가 오른쪽 위·주먹 마디가 아래라 앞으로 곧게 내지르면 마디가 아래·뒤를 봄(v2 첫 렌더) →
#   공격 동안만 먼 건틀릿 그림(소매 입구 왼쪽 · 주먹 마디 오른쪽 = 원화의 앞으로 내지른 주먹)을 가까운 팔꿈치에 붙여 씀(크기 = 가까운 건틀릿만큼).
#   대기 자리에서 소매 입구→건틀릿 가운데 방향·거리를 가까운 건틀릿과 같게 놓아, 처음·끝에 제자리에서 겹쳐 바꿈(fade)
def _cen(a): ys, xs = np.nonzero(a[..., 3] > 100); return np.array([xs.mean(), ys.mean()])
C_N, C_F = _cen(armL), _cen(foreF)
A_CN, A_CF = math.degrees(math.atan2(*(C_N - EL_N)[::-1])), math.degrees(math.atan2(*(C_F - EL_F)[::-1]))
K_P = float(np.linalg.norm(C_N - EL_N) / np.linalg.norm(C_F - EL_F))
R_P = math.radians(A_CN - A_CF)
shutil.copy(os.path.join(PARTS, 'foreF.png'), os.path.join(PARTS, 'armLp.png')); OFF['armLp'] = OFF['foreF']
parts['armLp'] = {'src': 'parts/armLp.png', 'pivot': piv('foreF', EL_F), 'scale': round(SC * K_P, 4)}
print(f'  펀치 건틀릿: 가까운 가운데 방향 {A_CN:.1f}° · 먼 {A_CF:.1f}° → 돌림 {math.degrees(R_P):.1f}° · 크기 ×{K_P:.3f}')
UF = (FI_F - EL_F) / np.linalg.norm(FI_F - EL_F)
parts['gF'] = {'src': 'parts/foreF.png', 'pivot': piv('foreF', EL_F), 'grip': piv('foreF', FI_F), 'elbow': piv('foreF', EL_F), 'scale': SC, 'shaftDir': [round(float(UF[0]), 4), round(float(UF[1]), 4)]}
parts['weapon'] = {'src': 'parts/weapon.png', 'pivot': [2, 2], 'scale': SC, 'tip': [2, 0], 'tips': [[2, 2], [2, 2]], 'pommel': [2, 4]}
for n in FACE_N + BLINK_N: parts[f'face_{n}'] = {'src': f'parts/face_{n}.png', 'pivot': parts['head']['pivot'], 'scale': SC}
for nm, sd in [('bootStandN', 'near'), ('bootStandF', 'far')]: P_(nm, LEG[sd]['ankle'])
for _sd, _nm in (('near', 'sandalNRun'), ('far', 'sandalFRun')): parts[_nm] = {'src': f'parts/{_nm}.png', 'pivot': [round(RB[_sd][0][0], 1), round(RB[_sd][0][1], 1)], 'scale': SC}
for nm in ('thighN', 'thighF', 'shinN', 'shinF'): parts[nm] = {'src': f'parts/{nm}.png', 'pivot': [0, 0], 'scale': 1}
WEAPON_ANG = math.atan2(UF[1], UF[0]) + math.pi / 2
ARML_REST = 0.3   # 엔진이 서 있을 때 자유 팔뚝을 −0.3 rad 굽힘 → 뼈 rot +0.3 → 대기 = 원화(10·20·30 브루노와 같음)
world = {'root': (O, 0.0), 'hip': (HIP, 0.0), 'skirt': (HIP, 0.0), 'cape': (NECK, 0.0), 'scarf': (NECK, 0.0), 'pouch': (HIP, 0.0), 'pauldron': (SH_N, 0.0), 'pauldronF': (SH_F, 0.0),
         'torso': (HIP, 0.0), 'head': (NECK, 0.0), 'pony': (PONY, 0.0), 'belt': (HIP, 0.0),
         'armU': (SH_N, 0.0), 'armL': (EL_N, ARML_REST), 'fistN': (FI_N, ARML_REST),
         'armF': (SH_F, 0.0), 'foreF': (EL_F, 0.0), 'fistF': (FI_F, 0.0), 'weapon': (FI_F, WEAPON_ANG), 'foreFb': (FI_F, 0.0)}
for _nm, (_par, _pt) in BACKB.items(): world[_nm] = (_pt, 0.0)
world['armLp'] = (EL_N, 0.0)
BONES = [('root', None), ('hip', 'root'), ('skirt', 'hip'), ('torso', 'hip'), ('head', 'torso'), ('pony', 'head'), ('armF', 'torso'), ('foreF', 'armF'), ('fistF', 'foreF'), ('weapon', 'fistF'),
         ('armU', 'torso'), ('armL', 'armU'), ('fistN', 'armL'), ('foreFb', 'torso'), ('cape', 'torso'), ('scarf', 'torso'), ('pouch', 'hip'), ('pauldron', 'torso'), ('pauldronF', 'torso'), ('belt', 'torso')]
BONES += [(_nm, _par) for _nm, (_par, _pt) in BACKB.items()]
BONES += [('armLp', 'armL')]
WANG = {'armL': ARML_REST, 'fistN': ARML_REST, 'weapon': WEAPON_ANG}
bones = []
for name, parent in BONES:
    if parent is None: bones.append({'name': 'root', 'parent': None, 'pos': [0, 0]}); continue
    pw_, pa, cw_, ca = world[parent][0], WANG.get(parent, 0.0), world[name][0], WANG.get(name, 0.0)
    if parent == 'armL': pa, ca = 0.0, 0.0
    dv = (cw_ - pw_) * SC; c, s = math.cos(-pa), math.sin(-pa)
    b = {'name': name, 'parent': parent, 'pos': [round(c * dv[0] - s * dv[1], 1), round(s * dv[0] + c * dv[1], 1)]}
    if abs(ca - pa) > 1e-4: b['rot'] = round(ca - pa, 4)
    if name in parts and name != 'weapon': b['part'] = name
    if name == 'weapon': b['part'] = 'weapon'
    if name == 'skirt': b['part'] = 'hips'
    if name == 'armLp': b['pos'] = [0, 0]; b['rot'] = round(R_P, 4)
    bones.append(b)
# ---------------- 다리 정의(30 브루노와 같은 틀) ----------------
legs = {'hip': [0, round(SC * (float(np.mean([LEG[s]['hip'][1] for s in LEG])) - HIP[1]), 1)], 'thigh': round(SC * L_TH, 1), 'shin': round(SC * L_SH, 1),
        'thighImg': TH['near'], 'shinImg': SHN['near'], 'boot': {'part': 'sandalNRun', 'sole': RB['near'][1], 'ankleRange': [-1.2, 1.4], 'runLock': 0.0}, 'lenByStand': True}
RUNX = {'near': -148.0, 'far': 16.0}; ROOTX = {'near': -160.0, 'far': 46.0}   # v3.6 DHL 14:24 '다리 사이 조금 좁게, 루시아 참고 걸음' — 뿌리 간격 266 → 206(몸 키의 .23, 7 루시아 .23)   # DHL 09:49 '다리는 바지 다리 구멍 안에서' — 다리 뿌리 = 반바지 밑단 구멍 가운데 위(원화 x 167 · 300), 발 줄은 그보다 조금 뒤
#   # 달리는 발 줄(리그 px, 골반 기준) — DHL 09:36 '다리를 뒤로': legprobe 로 두 다리 기울기 평균이 발이 조금 뒤(+5~+12°)가 되게 고름(먼 다리는 뿌리보다 +16 이어야 같은 기울기)
for sd, nm, lm in [('near', 'bootStandN', lab('legN')), ('far', 'bootStandF', lab('legF'))]:
    hide = {'part': TH[sd]['part'], 'a': TH[sd]['a'], 'b': TH[sd]['b'], 'w': 0.001}
    _root = round(SC * (LEG[sd]['hip'][0] - HIP[0]), 1); _rest = round(SC * (LEG[sd]['ankle'][0] - HIP[0]), 1)
    legs[sd] = {'x': _rest, 'hipX': ROOTX[sd], 'runX': RUNX[sd], 'shade': 0, 'thighImg': TH[sd], 'shinImg': SHN[sd], 'runBoot': 'sandalNRun' if sd == 'near' else 'sandalFRun', 'thigh': round(SC * L_TH0, 1), 'shin': round(SC * L_SH0, 1),
                'stand': {'fade': [0.05, 0.1], 'thighImg': hide, 'shinImg': dict(hide, part=SHN[sd]['part'], a=SHN[sd]['a'], b=SHN[sd]['b']), 'boot': {'part': nm, 'sole': sole_pts(lm, LEG[sd]['ankle'], SOLE)}}}
# ---------------- 그리는 순서 ----------------
def order(lst): return [x for x in lst if x not in ('torsoB', 'headB', 'ponyB', 'beltB', 'hipsB') or x in BACKB]
draw = order(['legFar', 'legNear', 'skirt', 'belt', 'torsoB', 'armU', 'torso', 'headB', 'armF', 'foreF', 'head', 'pony', 'armL', 'armLp'])   # DHL 09:49 '주먹이 옷 레이어보다 위로' — 가까운 건틀릿 늘 맨 앞(대기 포함, 원화의 조끼 자락이 건틀릿을 덮던 곳은 건틀릿이 덮음)
rig = {'name': 'basil-rust', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': parts, 'bones': bones, 'legs': legs, 'draw': draw, 'hidden': ['armLp'], 'faces': {n: f'face_{n}' for n in FACE_N},
       'blinkFaces': {'half': 'face_half', 'closed': 'face_closed'},
       'gait': {'stance': 0.26, 'strideBase': 26, 'strideK': 0.08, 'hipBase': -18, 'bob': 4, 'lean': 0.12, 'waddle': 0.03, 'headBob': 3, 'kneeLift': 0.2, 'heelKick': 0.05, 'dropCap': 8, 'angK': 0.12, 'strideFlex': [0.75, 1.15],   # 7 러스트 루시아 종종걸음(드워프)
                'swingReach': 0.05, 'landAng': -0.04, 'elbowRun': 0.12, 'armSwing': 0.06, 'armBias': 0.0, 'headRun': 0.05},
       'carrySwing': 0.15, 'wristRange': 0.2, 'dropLift': 8, 'ponySway': 0.8, 'bounce': [],
       'metrics': {'bodyHeight': round(2 * (SOLE - M['hairTop'][1])), 'note': f"rig units; 상투 위(y{M['hairTop'][1]})~발바닥({SOLE:.0f}) ×2"},
       'ui': {'attack': 'smash', 'touch': 'hop'}}
# ---------------- 공격: 뒷손 펀치(DHL 10-22 05:42 '앞으로 펀치 — 주먹이 길어지지 않고 뒤에서 앞으로') — v1 두 주먹 내려찍기 키는 SLAM_KEYS(안 씀) ----------------
#   키(원화 좌표·도, 0° = 오른쪽, 90° = 아래): 몸 기울기 lean(rad, + = 앞으로) · 가까운 (윗팔 각, 건틀릿 각) · 먼 (주먹 자리, 건틀릿 각) · 가까운 어깨 앞으로(shNx, 원화 px — 몸을 트는 것)
#   가까운(화면 왼쪽 = 뒷손) 건틀릿: 뒤로 젖혔다가 가슴 높이로 앞으로 곧게 — 팔 길이·건틀릿 크기 그대로(윗팔 30 + 건틀릿 100), 어깨를 앞으로 내밀어 닿는 거리
#   먼(앞손) 건틀릿: 처음엔 조금 앞으로 겨눴다가 칠 때 턱 옆으로 당겨 막음(머리 뒤)
def rot_about0(p, th): c, s_ = math.cos(th), math.sin(th); q = V(p) - HIP; return HIP + np.array([c * q[0] - s_ * q[1], s_ * q[0] + c * q[1]])
u0N = math.degrees(math.atan2(*(EL_N - SH_N)[::-1])); f0N = math.degrees(math.atan2(*(FI_N - EL_N)[::-1])); a0F = math.degrees(math.atan2(*(FI_F - EL_F)[::-1]))
SLAM_KEYS = [[0.10, -0.04, -40, 40, 400, 190, -30], [0.20, -0.07, -118, -105, 335, 90, -95], [0.28, -0.08, -122, -112, 325, 84, -105], [0.38, 0.30, 32, 74, 420, 352, 74], [0.52, 0.28, 34, 76, 412, 348, 76]]
#   가까운 건틀릿 각 = 소매 입구→건틀릿 가운데 방향 φ(펀치 건틀릿 armLp 기준, 대기 = A_CN) — 아래에서 엔진 팔뚝 각(소매→주먹 마디, 대기 f0N)으로 바꿈
PUNCH_V2_KEYS = [[0.16, -0.12, 150, 185, 414, 258, 12, -12], [0.23, 0.03, 80, 40, 410, 250, -20, 8], [0.30, 0.24, 45, 8, 340, 236, -95, 30]]   # v2(안 씀 — DHL 06:00 '팔이 돌면 안 돼요')
# v3 (DHL 10-22 06:00 '팔이 돌지 않고 뒤로만 살짝 갔다가 앞으로'): 앞손(먼 건틀릿 — 원화에서 이미 앞으로 내지른 주먹) 곧게 치기.
#   팔은 돌리지 않음 — 먼 어깨를 주먹과 같은 만큼 옮겨(shFx·shFy, 몸을 트는 것) 어깨→팔꿈치→주먹이 대기 모양 그대로 미끄러짐(IK 각 변화 0)
#   뒷손(가까운 건틀릿)도 세상 각 그대로(몸 기울기만큼 되돌림), 그림 바꾸기·순서 바꾸기 없음
# v3.5 (DHL 12:17 '팔은 뒤로 젖히면서 깨지는 것 같다 · 팔을 올리고 몸이 살짝 뒤로 갔다가 앞으로 · 다리도 이상 — 연구한 것 중심으로'):
#   ① 골반은 안 움직임(hipX·hipY 0 — 66번: 서 있는 원화 다리는 발목에 고정된 한 장이라 골반이 움직이면 바지 밑단이 다리 위로 미끄러짐)
#   ② 어깨는 상체에 붙은 채(shFx·shFy 0 — 어깨를 옮기면 윗팔 뿌리가 턱·조끼 밖으로 나와 깨져 보였음)
#   ③ 먼 팔 = 윗팔만 어깨 둘레로 돎(길이 그대로), 건틀릿은 세상 각 그대로 평행 이동 — 주먹 = 어깨 + 윗팔(u) + (원화 팔꿈치→주먹)
#   키: 몸 기울기 lean, 윗팔 세상 각 u(도, 0 = 오른쪽, 음수 = 위)
JAB = json.loads(os.environ.get('JAB', 'null')) or [
  # t,    lean,  u
  [0.00, 0.00, None],
  [0.18, -0.08, -30],      # ① 팔을 올림 — 윗팔을 위로 세워 건틀릿이 어깨 위로, 몸은 살짝 뒤로
  [0.30, 0.16, 18],         # ② 앞으로 — 윗팔을 앞으로 눕히며 몸을 앞으로 숙임(타격)
  [0.46, 0.14, 20],         # ③ 뻗은 채 버팀
  [0.78, 0.02, None],      # ④ 돌아옴
  [1.00, 0.00, None]]
def _rot(v, th): c, s_ = math.cos(th), math.sin(th); return np.array([c * v[0] - s_ * v[1], s_ * v[0] + c * v[1]])
_L1F = float(np.linalg.norm(EL_F - SH_F)); _u0F = math.degrees(math.atan2(*(EL_F - SH_F)[::-1])); _EF = FI_F - EL_F
KEYS, SHF, HX = [], [], []
for t_, ln, u in JAB:
    S_ = rot_about0(SH_F, ln); uu = _u0F + math.degrees(ln) if u is None else u   # None = 대기 팔(상체와 같이 기욺)
    E_ = S_ + _L1F * np.array([math.cos(math.radians(uu)), math.sin(math.radians(uu))]); G_ = E_ + _EF
    KEYS.append([t_, ln, u0N, A_CN, float(G_[0]), float(G_[1]), a0F, 0]); SHF.append([t_, 0.0, 0.0]); HX.append([t_, 0.0])
print('  먼 주먹 자리(원화 px)', [(k[0], round(k[4], 1), round(k[5], 1)) for k in KEYS])
for _k in KEYS: _k[3] = _k[3] + (f0N - A_CN)
HIT_T = float(os.environ.get('HIT_T', 0.30))
def wrap(d): return (d + 180) % 360 - 180
KU = [KEYS[0][:]]
for k in KEYS[1:]: KU.append([k[0], k[1], KU[-1][2] + wrap(k[2] - KU[-1][2]), KU[-1][3] + wrap(k[3] - KU[-1][3]), k[4], k[5], KU[-1][6] + wrap(k[6] - KU[-1][6]), k[7]])
def rot_about(p, th): c, s = math.cos(th), math.sin(th); q = V(p) - HIP; return HIP + np.array([c * q[0] - s * q[1], s * q[0] + c * q[1]])
L1N, L2N = np.linalg.norm(EL_N - SH_N), np.linalg.norm(FI_N - EL_N); L1F, L2F = np.linalg.norm(EL_F - SH_F), np.linalg.norm(FI_F - EL_F)
chk = []
for k in KU:
    t, th = k[0], k[1]; S = rot_about(SH_N + [k[7], 0], th); E = S + L1N * np.array([math.cos(math.radians(k[2])), math.sin(math.radians(k[2]))]); F = E + L2N * np.array([math.cos(math.radians(k[3])), math.sin(math.radians(k[3]))])
    SF = V(k[4:6]) - (FI_F - SH_F) if True else rot_about(SH_F, th); d = np.linalg.norm(V(k[4:6]) - SF) / (L1F + L2F)
    chk.append(dict(t=t, nearFist=[round(float(F[0]), 1), round(float(F[1]), 1)], farReach=round(float(d), 3)))
print('  키 검사', chk)
assert all(c['farReach'] <= 1.0 for c in chk), '먼 팔이 닿지 않음'
ORDER_T = None
rig['drawA'] = draw
rig['drawB'] = draw
EA = 'io'
trk = lambda f: [[k[0], round(f(k), 4), EA] for k in KU]
act = {'kind': 'sword', 'rigid': True, 'orderAlways': True, 'dur': float(os.environ.get('DUR', 0.8)), 'hitAt': HIT_T, 'hitStop': 0.07, 'cancelAt': 0.8,
       'w': [[0, 1]], 'reach': [[0, 0]], 'nPiece': [[0, 'gF']], 'nUpper': [[0, 'armF'], [0.06, 'armFA'], [0.9, 'armF']], 'armIK': [[0, 1]],
       'gx': trk(lambda k: SC * (k[4] - HIP[0])), 'gy': trk(lambda k: SC * (k[5] - HIP[1])), 'sa': trk(lambda k: math.radians(k[6])),
       'lean': trk(lambda k: k[1]), 'hipY': [[0, 0]], 'hipX': [[0, 0]],
       'head': [[0, 0], [0.18, 0.02, 'io'], [0.3, -0.03, 'io'], [0.46, -0.02, 'io'], [0.78, 0]],
       'freeArm': True, 'fuA': trk(lambda k: math.radians(k[2] - u0N) - k[1]), 'flA': trk(lambda k: math.radians((k[3] - k[2]) - (f0N - u0N))),
       'face': [[0, 'angry'], [0.12, 'effort'], [0.26, 'shout'], [0.5, 'angry'], [0.85, None]],
       'order': [[0, 'drawA']],
       'shake': [[0, 0]],
       'nearLift': [[0, 0]], 'farLift': [[0, 0]], 'aDamp': 40, 'standStep': True}
rig['swordGrip'] = {'tipDepth': 2000, 'near': {'upper': 'armF', 'carry': 'gF', 'pieces': []}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': 0}, 'stretchMax': 1.05, 'shoulderPush': 0}
rig['actions'] = {'smash': act}
rig['cutHold'] = float(os.environ.get('CUT', 0.18))
_a = np.array(Image.open(os.path.join(HERE, '..', '..', '..', 'art', 'characters', 'char_0005.png')).convert('RGBA').resize((160, 160), Image.BOX))[..., 3]
_ys, _xs = np.nonzero(_a > 40); FIT_CX = round(float(((_xs.min() + _xs.max() + 1) / 2 + _xs.mean() + .5) / 2 / 160 * 512), 1)
rig['gameRef'] = {'refOrigin': [round(float(O[0] - (HIP[0] - FIT_CX)), 1), float(O[1])], 'refScale': 2.0, 'refLift': 0,
                  'note': f'게임 그림 char_0005.png(512) = 원화(ref512). x = 도감 칸(fitArt 중심 {FIT_CX}, index.html measureBox 와 같은 계산)에서 골반(hip x {HIP[0]:.0f})이 가운데'}
rig['note'] = '5 러스트 바실 v3(대기·달리기·앞손 곧게 치기). 조각 = 팔·건틀릿만 지운 원화 2장으로 몸을 드러내 부품별로 나눔(seg5.py) + 팔 = 원화 − 지운 원화(가려진 곳 = 시트 건틀릿), 시트 = 표정·깜빡임·윗팔·달리는 다리·샌들'
json.dump(dict(keys=KU, check=chk, order=ORDER_T, hit=HIT_T), open(os.path.join(HERE, 'review', 'keys5.json'), 'w'), ensure_ascii=False, indent=1)
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(PARTS)): _h.update(fn.encode()); _h.update(open(os.path.join(PARTS, fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_basil5.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};window.MR_RIG_DEFS['basil-rust']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(parts), 'parts, version', rig['version'], 'draw', draw, 'FIT_CX', FIT_CX)
