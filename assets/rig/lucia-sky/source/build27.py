"""27 스카이 루시아 리그 조립 v1 — build_lucia17(17 네온 v1.2) 을 옮김. 다른 점: 목 가리개 없음(스카프 = 상체, 투구 가리개 = 머리) · 가까운 주먹 fistN = 방패 자식(7 러스트)
17 네온 루시아 리그 조립 v1 (2026-10-21 — DHL 06:46 '네온 루시아 작업 진행해요~' · 0번 원화 09:54 · 시트 11:03 · 지운 원화 11:32·11:36 합격)
구조 = 7 러스트 루시아 v1.5(build_lucia7.py · attack/smash7.py) 그대로 + 네온만의 것:
  ①방패 = 가까운 어깨(SH_N)에 붙은 뼈 'shield'(상체 자식, follow 상체 −0.6 + 출렁임) — 가까운 손은 방패 뒤라 안 보임(DHL 09:43). 가까운 주먹 조각 없음(러스트 fistN 뺌)
  ②목 가리개 = 'collar'(상체 자식 뼈, 머리 앞) — 머리가 돌아도 가리개 아래 끝이 가슴 판에 붙어 있게. 머리 조각은 가리개 밑 턱을 시트 2 머리로 채움
  ③먼 팔(갑옷): 큰 크림 어깨갑 = 'pauldronF'(먼 팔 30% 따라 돎) · 윗팔 upF = 원화 회색 네모 판·짙은 소매 + 어깨갑 밑 = 시트 13 윗팔을 뼈 따라 맞춤 · 팔뚝 foreF = 원화 크림 팔뚝 갑 + 회색 손목 고리 · 주먹 = 원화
  ④가려진 곳 = 지운 원화 두 장(seg17 의 work/body.png — 방패·먼 팔 없는 몸) → 몸 조각은 메움이 거의 없음
입력: ref512.png(= 게임 char_0017) · work/body.png · work/labels.npy · work/labels_body.npy(seg27.py) · pieces/(시트 19칸, cut27.py) · measure27.json
출력: ../rig.json, ../rig.def.js, ../parts/*.png      실행: cd source && python3 -I build27.py
원칙: 대기 = 원화(보이는 곳은 원화를 오림), 가려진 곳만 지운 원화·시트·inpaint. 손 조각 뒤집기 금지. 팔다리 길이 고정. 좌표: 원화 512px 로 적고 ×2 = 리그 단위."""
import json, math, os, shutil, hashlib, sys, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work'); OUT = os.path.join(HERE, '..')
os.makedirs(os.path.join(OUT, 'parts'), exist_ok=True); os.makedirs(W, exist_ok=True)
img = lambda p: np.array(Image.open(p).convert('RGBA'))
RA = img(os.path.join(HERE, 'ref512.png')); AL = RA[..., 3] > 8
def pmask(pts):
    m = Image.new('L', (512, 512), 0); ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255); return np.array(m) > 0
def dil(m, r): return cv2.dilate(m.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0
def ero(m, r): return cv2.erode(m.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0
yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)
LUM = RA[..., :3].astype(np.float32).mean(-1)
unitv = lambda v: np.array(v, float) / np.linalg.norm(v)
MS = json.load(open(os.path.join(HERE, 'measure27.json')))

# ---------------- 원화 관절 (512 px, measure27.json — grid17.py 격자 확대에서 잼) ----------------
O = np.array([281.0, 450.0])                                      # 뿌리: 두 발 가운데(가까운 밑창 170~234 · 먼 352~391 → 바깥 끝 가운데 280.5) 땅(발바닥 450)
HIP = np.array(MS['HIP'], float); NECK = np.array(MS['NECK'], float)   # 골반(버클 가운데) · 목(가리개 안 = 머리 회전 중심)
SH_N = np.array(MS['SH_N'], float); FIST_N = np.array(MS['FIST_N'], float)                                  # 가까운 어깨(방패 뒤 — noshield 의 가까운 큰 어깨갑 가운데 밑)
SH_F, EL_F, WR_F = (np.array(MS['far'][k], float) for k in ('SH', 'EL', 'WR'))
_ax0, _ax1 = np.array(MS['axe']['shaftTop'], float), np.array(MS['axe']['shaftLow'], float)
HU = unitv(_ax0 - _ax1)                                           # 자루 방향(쥔 손 → 날), 세로에서 뒤로 13.9°
G = _ax1 + HU * float(np.dot(np.array(MS['far']['G']) - _ax1, HU))  # 쥔 점: 자루 축 위, 주먹 가운데 높이(y 289)
LJ = {sd: {k[0]: np.array(v, float) for k, v in MS['legs'][sd].items() if k != 'len'} for sd in ('near', 'far')}   # h k a
LEG_HY = float((LJ['near']['h'][1] + LJ['far']['h'][1]) / 2)
for sd in ('near', 'far'):   # 서 있는 다리는 다 펴지 않음(≤ .985 — 22 교훈)
    j = LJ[sd]; ha = np.linalg.norm(j['a'] - j['h']); L_ = np.linalg.norm(j['k'] - j['h']) + np.linalg.norm(j['a'] - j['k'])
    if ha / L_ > .985:
        u_ = (j['a'] - j['h']) / ha; n_ = np.array([-u_[1], u_[0]]); n_ = n_ if n_[0] > 0 else -n_; k0 = j['k'].copy()
        for s_ in np.arange(0, 12, .1):
            j['k'] = k0 + n_ * s_
            if ha / (np.linalg.norm(j['k'] - j['h']) + np.linalg.norm(j['a'] - j['k'])) <= .985: break
        print(f'  {sd} 무릎 앞으로 {s_:.1f}px → {j["k"].round(1).tolist()}')
    print(f'  {sd} 다리 펴짐', round(float(ha / (np.linalg.norm(j['k'] - j['h']) + np.linalg.norm(j['a'] - j['k']))), 3))
print('  far arm 리그 L1 %.1f · L2 %.1f · 손목→쥔 점 %.1f · 쥔 점→팔꿈치 %.1f' % (2 * np.linalg.norm(EL_F - SH_F), 2 * np.linalg.norm(WR_F - EL_F), 2 * np.linalg.norm(G - WR_F), 2 * np.linalg.norm(G - EL_F)), '· G', G.round(1).tolist())

# ---------------- 칸 (seg27.py) ----------------
LBL = os.path.join(W, 'labels.npy')
if not os.path.exists(LBL) or os.path.getmtime(LBL) < max(os.path.getmtime(os.path.join(HERE, f)) for f in ('ref512.png', 'seg27.py', 'sheets/noshield_1921.png', 'sheets/nofar_1921.png')):
    subprocess.run([sys.executable, '-I', os.path.join(HERE, 'seg27.py')], check=True, stdout=subprocess.DEVNULL)
SL, SLB = np.load(LBL), np.load(os.path.join(W, 'labels_body.npy')); SEGN = json.load(open(os.path.join(W, 'label_names.json')))
BODY = img(os.path.join(W, 'body.png')); BL = BODY[..., 3] > 8
own = {n: (SL == i + 1) & AL for i, n in enumerate(SEGN)}               # 원화 칸
ownB = {n: (SLB == i + 1) & BL for i, n in enumerate(SEGN) if (SLB == i + 1).any()}   # 몸 그림 칸
_hsvB = cv2.cvtColor(BODY[..., :3], cv2.COLOR_RGB2HSV)
GREYB = (_hsvB[..., 1] < 55) & (_hsvB[..., 2] > 70) & (BODY[..., 3] > 200)
SKIN = lambda A: ((lambda h: (h[..., 0] >= 5) & (h[..., 0] <= 22) & (h[..., 1] > 90) & (h[..., 2] > 140))(cv2.cvtColor(A[..., :3], cv2.COLOR_RGB2HSV))) & (A[..., 3] > 200)
# 다리: 허벅지 = 다리 칸 중 무릎판(짙은 회색 네모 + 금색 관절, 무릎 둘레 22px)이 아니고 엉덩이→무릎 축에서 무릎보다 위 · 나머지(무릎판·정강이·부츠) = boot
#   무릎 보호대(짙은 회색 네모 + 금색 둥근 관절 — 다리 안쪽) = 정강이 쪽(러스트 무릎 쇠판과 같음) — 격자 확대(grid17 body 4배)에서 읽은 다각형
KNEE_ARMOR = {'near': pmask([[192, 372], [225, 367], [244, 377], [244, 409], [199, 413]]),
              'far': pmask([[325, 384], [350, 377], [369, 383], [369, 411], [329, 414]])}
for sd, ln, tn, bn in (('near', 'legN', 'thighN', 'bootN'), ('far', 'legF', 'thighF', 'bootF')):
    h, k = LJ[sd]['h'], LJ[sd]['k']; u_ = unitv(k - h); t_ = (xx - h[0]) * u_[0] + (yy - h[1]) * u_[1]
    plate = dil(KNEE_ARMOR[sd], 1) & ownB[ln]
    ownB[tn] = ownB[ln] & ~plate & (t_ < np.linalg.norm(k - h) - 2) & (yy < k[1] + 6); ownB[bn] = ownB[ln] & ~ownB[tn]   # 먼 다리는 비스듬해 축만 보면 부츠 뒤꿈치가 허벅지로 들어감 → 무릎 높이 + 6 까지만
    del ownB[ln]
for n in ('legN', 'legF'): own.pop(n, None)
print('  몸 칸', {n: int(m.sum()) for n, m in ownB.items()}, '· 원화 앞 칸', {n: int(own[n].sum()) for n in ('shield', 'pauldron', 'upF', 'foreF', 'axe', 'fistF')})

# ---------------- 조각 오리기 ----------------
#   몸(BODY 그림): 뒤 → 앞 = 먼 다리 · 가까운 다리 · 상체 · 골반 · 머리 · 목 가리개 — 앞 조각 밑 3px 겹침
#   앞(원화 그림): 어깨갑 · 윗팔 · 팔뚝 · 도끼 · 주먹 · 방패 — 서로만 3px 겹침(몸 조각 밑으로는 안 들어감: 팔이 움직이면 몸 조각이 붙어 다님)
DRAW_B = ['thighF', 'bootF', 'thighN', 'bootN', 'torso', 'hips', 'head']
DRAW_F = ['pauldron', 'upF', 'foreF', 'axe', 'fistF', 'shield']   # v1.1(DHL 20:33 '표시한 손 삭제') 가까운 주먹 뺌 — 주먹 자리 = 방패+주먹 지운 원화의 몸(허리띠 끝·남색 상의)
def inpaint_into(a, region, src_ok, r=5):
    rgb = np.ascontiguousarray(a[..., :3].copy()); d, (iy, ix) = ndimage.distance_transform_edt(~src_ok, return_indices=True)
    rgb[~src_ok] = rgb[iy[~src_ok], ix[~src_ok]]
    out = cv2.inpaint(rgb, region.astype(np.uint8) * 255, r, cv2.INPAINT_TELEA); a = a.copy(); a[..., :3][region] = out[region]; a[..., 3][region] = 255; return a
def outline_cut(a, cutmask, w=2.4):
    A = a[..., 3] > 128; d = ndimage.distance_transform_edt(A); e = A & dil(cutmask, 1) & (d <= w + .2)
    k = np.clip(w + .4 - d, 0, 1)[e][:, None]; a = a.copy(); a[..., :3][e] = (a[..., :3][e] * (1 - k) + np.array([28, 26, 28]) * k).astype(np.uint8); return a
def save_crop(a, name):
    ys, xs = np.nonzero(a[..., 3] > 0); x0, y0 = xs.min() - 2, ys.min() - 2
    Image.fromarray(a[y0:ys.max() + 3, x0:xs.max() + 3]).save(os.path.join(W, name + 'Art.png')); return np.array([x0, y0], float)
def largest(a):
    n_, l_, s_, _ = cv2.connectedComponentsWithStats((a[..., 3] > 10).astype(np.uint8), 8); a = a.copy(); a[..., 3] = np.where(l_ == 1 + int(np.argmax(s_[1:, cv2.CC_STAT_AREA])), a[..., 3], 0); return a
ART = {}
for order, SRC, OWN, AMASK in ((DRAW_B, BODY, ownB, BL), (DRAW_F, RA, own, AL)):
    for i, n in enumerate(order):
        ab = dil(OWN[n], 3) & np.logical_or.reduce([OWN[m] for m in order[i + 1:]] + [np.zeros((512, 512), bool)]) & AMASK
        if n in ('upF', 'foreF'): ab &= ~own['pauldron']            # 팔은 어깨갑 밑 겹침 안 가져옴(어깨갑은 30% 만 따라 돎)
        if n == 'upF': ab &= ~own['foreF']                           # 윗팔(상체 뒤 순서)이 팔뚝 갑 끝을 덮지 않게
        if n == 'axe': ab &= ~(own['foreF'] | own['upF'])
        m = OWN[n] | ab; a = SRC.copy(); a[..., 3] = np.where(m, SRC[..., 3], 0); ART[n] = a
for n in DRAW_B:   # 원화에서 이 몸 조각 칸인 곳 = 원화 픽셀(대기에 보이는 그대로) — 지운 원화가 다시 그린 상체 옆 짙은 띠·금색 줄(nofar 의 둥근 어깨와 다름) 등
    _ob = own.get(n, np.zeros((512, 512), bool)) if n not in ('thighN', 'thighF', 'bootN', 'bootF') else (ownB[n] & AL & ((SL == 0) | (SL == SEGN.index('leg' + n[-1]) + 1)))   # 다리 칸(원화에 보이는 다리 — 방패 오른쪽 테에서 몸으로 돌린 띠 포함)
    _ch = _ob & (np.abs(ART[n].astype(int) - RA.astype(int)).max(-1) > 0)
    ART[n][_ch] = RA[_ch]
    if _ch.any(): print(f'  {n} 원화 픽셀로', int(_ch.sum()))
for n in ('head',):   # 원화에서 상체 칸인 곳(어깨갑 왼쪽 짙은 띠)은 머리·가리개가 덮지 않게 — 몸 그림(nofar)에선 머리 칸으로 들어간 곳
    _k = own['torso'] & (ART[n][..., 3] > 0); ART[n][..., 3][_k] = 0
    if _k.any(): print(f'  {n} 상체 칸 뺌', int(_k.sum()))
#   방패 뒤(원화 방패 칸) 몸 조각의 가는 부스러기 — 지운 원화가 방패 밑에 그린 골반 왼쪽 끝 가는 선(왼쪽으로 뾰족) 등. 달리면 방패가 출렁여 틈으로 보였음(DHL 12:27 '방패쪽 지저분한 것')
#   + 원화 실루엣 밖(원화는 빈 곳인데 지운 원화가 그린 곳 — 방패 오른쪽 테와 허벅지 사이 틈의 골반 끝 가는 선) 뺌
_hid = dil(own['shield'], 1)
for n in DRAW_B:
    _a = ART[n][..., 3] > 0; _op = cv2.morphologyEx(_a.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))) > 0
    _rm = _a & ((~dil(_op, 1) & _hid) | ~dil(AL, 1)); ART[n][..., 3][_rm] = 0
    if _rm.any(): print(f'  {n} 방패 뒤 가는 부스러기·원화 밖 뺌', int(_rm.sum()))
#   골반 왼쪽 아래 가는 꼬리(방패 테 ↔ 가까운 허벅지 사이 비스듬한 외곽선 아래 끝, 원화 칸 없음) → 서 있는 가까운 허벅지 조각으로 옮김:
#   대기 모습은 그대로, 달리면(서 있는 다리 그림이 옅어짐) 같이 사라짐 — 골반에 붙어 있으면 다리가 움직여도 허공에 남은 선으로 보였음
_a = ART['hips'][..., 3] > 0; _op = cv2.morphologyEx(_a.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))) > 0
_tail = _a & ~dil(_op, 1) & (yy > 345) & (xx < 232)
ART['thighN'][_tail] = ART['hips'][_tail]; ART['hips'][..., 3][_tail] = 0; print('  골반 왼쪽 아래 꼬리 → 가까운 허벅지(서 있는)', int(_tail.sum()))
OPQ = lambda n: ART[n][..., 3] > 200
#   v1.1 가까운 주먹 뺌(DHL 20:33): 주먹 자리(+2px) 중 몸 조각이 덮지 않은 곳 = 몸 그림(방패+주먹 지운 원화) 픽셀로 상체에 채움 — 빈 틈 없게
_fz = dil(own['fistN'], 2) & BL & ~np.logical_or.reduce([ART[n][..., 3] > 128 for n in DRAW_B])
ART['torso'][_fz] = BODY[_fz]; print('  가까운 주먹 자리 상체 메움', int(_fz.sum()))
_cov = np.logical_or.reduce([ART[n][..., 3] > 200 for n in DRAW_B + DRAW_F if n != 'fistN'])
_gap = AL & (RA[..., 3] > 200) & ~_cov & (xx > 200) & (xx < 242) & (yy > 288) & (yy < 386)   # 방패 테 ↔ 몸 사이 원화에서 주먹·띠가 있던 1~6px 틈
if _gap.any(): ART['torso'] = inpaint_into(ART['torso'], _gap, (ART['torso'][..., 3] > 200) & ~dil(LUM < 40, 0), r=3)
print('  방패 ↔ 몸 틈 메움', int(_gap.sum()))

# ---- 시트 조각 (cut27.py) ----
if not os.path.exists(os.path.join(HERE, 'pieces', 'index.json')):
    subprocess.run([sys.executable, '-I', os.path.join(HERE, 'cut27.py'), os.path.join(HERE, 'sheets', 'parts1_1930.png')], check=True, stdout=subprocess.DEVNULL)
PC = os.path.join(HERE, 'pieces')
def sheet_rgba(n):   # 시트 조각 + 자홍 테두리 빼기
    a = np.array(Image.open(os.path.join(PC, n + '.png')).convert('RGBA')).astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None)
    a[..., 0] -= m; a[..., 2] -= m; return np.clip(a, 0, 255).astype(np.uint8)
def color_match(src, sel_src, ref, sel_ref):   # 시트 색 → 원화 색(평균·편차)
    mu_s, sd_s = src[..., :3][sel_src].astype(float).mean(0), src[..., :3][sel_src].astype(float).std(0) + 1
    mu_a, sd_a = ref[..., :3][sel_ref].astype(float).mean(0), ref[..., :3][sel_ref].astype(float).std(0) + 1
    out = src.copy(); out[..., :3] = np.clip((src[..., :3].astype(float) - mu_s) / sd_s * sd_a + mu_a, 0, 255).astype(np.uint8); return out
_sf = cv2.SIFT_create(4000)
def sift_to(piece, ref, refmask):
    g = lambda a: cv2.cvtColor(np.ascontiguousarray(a[..., :3]), cv2.COLOR_RGB2GRAY)
    k1, d1 = _sf.detectAndCompute(g(piece), (piece[..., 3] > 128).astype(np.uint8) * 255); k2, d2 = _sf.detectAndCompute(g(ref), refmask.astype(np.uint8) * 255)
    m = [p for p, q in cv2.BFMatcher().knnMatch(d1, d2, k=2) if p.distance < .75 * q.distance]
    A, inl = cv2.estimateAffinePartial2D(np.float32([k1[x.queryIdx].pt for x in m]), np.float32([k2[x.trainIdx].pt for x in m]), ransacReprojThreshold=2.5)
    return A, int(inl.sum()), len(m)

# 머리: 가리개 밑(턱·목) = 시트 2칸 머리(목 가리개 없이 그림 — SIFT 배율 ≈ .84)를 원화 색으로 맞춰 채움 — 가리개는 머리 앞 조각이라 대기엔 안 보임
_hd = sheet_rgba('head'); MH, _hin, _hm = sift_to(_hd, BODY, ownB['head'] & (yy < 262))
_hw = cv2.warpAffine(_hd, MH, (512, 512), flags=cv2.INTER_LINEAR)
_ov = (_hw[..., 3] > 200) & OPQ('head') & ~dil(~ownB['head'], 3)
_hw = color_match(_hw, _ov, BODY, _ov)
_fillH = np.zeros((512, 512), bool)
ART['head'] = largest(ART['head'])
print('  head 가리개 밑 시트 메움', int(_fillH.sum()), 'px · 배율', round(math.hypot(MH[0, 0], MH[1, 0]), 4), '회전', round(math.degrees(math.atan2(MH[1, 0], MH[0, 0])), 2), '· SIFT', _hin, '/', _hm)
# 상체: 머리카락 밑(가까운 큰 어깨갑 위)·골반(허리띠) 밑 — 상체 테두리 안 inpaint (숙이면 허리띠 위로 드러남, 머리가 돌면 머리카락 밑이 드러남)
_tb = ownB['torso']; _ys, _xs = np.nonzero(_tb)
TORSO_HULL = pmask([[186, 252], [205, 244], [240, 240], [262, 262], [300, 285], [338, 262], [356, 270], [358, 300], [352, 345], [340, 368], [250, 368], [222, 350], [190, 300]])
_reg = TORSO_HULL & (ownB['head'] & dil(_tb, 14)) & ~OPQ('torso')
_LUMB = BODY[..., :3].astype(np.float32).mean(-1)
ART['torso'] = inpaint_into(ART['torso'], _reg, _tb & (BODY[..., 3] > 200) & ~dil(~BL, 2) & ~dil(_LUMB < 60, 1))
_regH = TORSO_HULL & ownB['hips'] & (yy < 368) & ~OPQ('torso')   # 허리띠 밑 = 짙은 회색 속옷(금색 줄·크림 판을 끌어오지 않게 어두운 속옷 픽셀만 재료)
_dk = _tb & (BODY[..., 3] > 200) & (_LUMB > 40) & (_LUMB < 95) & (_hsvB[..., 1] < 60)
ART['torso'] = outline_cut(inpaint_into(ART['torso'], _regH, _dk), (_reg | _regH) & dil(~TORSO_HULL, 1))
print('  torso fill', int(_reg.sum()), '+ 허리띠 밑', int(_regH.sum()))
# 허벅지: 허리 판(골반) 밑으로 엉덩이 관절까지 — 짙은 회색 허벅지 색
for sd, n in [('near', 'thighN'), ('far', 'thighF')]:
    _e = np.zeros((512, 512), np.uint8); h, k = LJ[sd]['h'], LJ[sd]['k']; cv2.line(_e, tuple(int(v) for v in h - (k - h) * .35), tuple(int(v) for v in (h + k) / 2), 1, 24)
    _e = _e.astype(bool) & ~OPQ(n) & ownB['hips']
    ART[n] = inpaint_into(ART[n], _e, ownB[n] & (BODY[..., 3] > 200) & (LUM > 30))
    print(f'  {n} fill', int(_e.sum()))
# 도끼 자루(먼 주먹 밑): 주먹 위 자루(축 t 33~70)를 축 따라 주기로 내려 채움(러스트 7 과 같은 방법)
WRAP0, WRAP1 = float(os.environ.get('WRAP0', 42)), float(os.environ.get('WRAP1', 68))
t_ax = (xx - G[0]) * HU[0] + (yy - G[1]) * HU[1]; n_ax = (xx - G[0]) * -HU[1] + (yy - G[1]) * HU[0]
_sh = own['axe'] & (t_ax > WRAP0) & (t_ax < WRAP1) & (np.abs(n_ax) < 20)
SHAFT_HW = float(np.median([float(np.ptp(n_ax[own['axe'] & (np.abs(t_ax - tt) < .8) & (np.abs(n_ax) < 20)])) for tt in range(int(WRAP0) + 2, int(WRAP1) - 2, 3)])) / 2
_lowT = float(t_ax[own['axe'] & (t_ax < 0)].max()) if (own['axe'] & (t_ax < 0)).any() else -30.0   # 주먹 아래로 보이는 자루 위 끝
_hreg = (np.abs(n_ax) <= SHAFT_HW + .5) & (t_ax > -40) & (t_ax < WRAP0) & ~OPQ('axe') & dil(own['fistF'] | own['foreF'], 2)
_tsrc = WRAP0 + np.mod(t_ax - WRAP0, WRAP1 - WRAP0)
_sx_ = np.clip(np.round(G[0] + HU[0] * _tsrc - HU[1] * n_ax), 0, 511).astype(int); _sy_ = np.clip(np.round(G[1] + HU[1] * _tsrc + HU[0] * n_ax), 0, 511).astype(int)
_ok = _hreg & own['axe'][_sy_, _sx_]
ART['axe'][..., :3][_ok] = RA[..., :3][_sy_[_ok], _sx_[_ok]]; ART['axe'][..., 3][_ok] = 255
_hole = _hreg & ~_ok; ART['axe'] = inpaint_into(ART['axe'], _hole, OPQ('axe') & (np.abs(n_ax) <= SHAFT_HW), r=3) if _hole.any() else ART['axe']
ART['axe'] = largest(ART['axe'])
print('  axe shaft fill', int(_ok.sum()), '+ inpaint', int(_hole.sum()), 'px · 자루 반폭', round(SHAFT_HW, 1))
# 먼 어깨갑: 윗팔 판·팔뚝 갑에 가려진 아래쪽 = 볼록 껍질 안 크림 inpaint + 외곽선(어깨갑은 팔의 30% 만 돌아 판이 비키면 드러남)
_pm = own['pauldron'] & (RA[..., 3] > 200); _hp = cv2.convexHull(np.stack(np.nonzero(_pm)[::-1], 1).astype(np.int32)); _hm_ = np.zeros((512, 512), np.uint8); cv2.fillPoly(_hm_, [_hp], 1)
#   (v1 시험: 껍질 안 inpaint 는 공격 때 아래 끝이 톱니·흰 점으로 보임) → 시트 12 어깨갑(완전한 둥근 판)을 원화 어깨갑 칸에 맞춰(배율·회전·이동 격자 찾기 — 칸 덮음 최대, 칸 밖 벌점) 밑에 깔고 원화가 위
#   깔 곳 = 원화에서 윗팔 판·팔뚝 갑에 가려진 곳 + 어깨갑 왼쪽 짙은 띠 중 시트 테두리(어두운 곳) — 원화 실루엣 밖으로는 안 나감
_ps = sheet_rgba('pauldron'); _pmk = (_ps[..., 3] > 128).astype(np.uint8); _ys, _xs = np.nonzero(own['pauldron']); _pcen = np.array([_xs.mean(), _ys.mean()]); _pc0 = np.array([_pmk.shape[1] / 2, _pmk.shape[0] / 2])
_allowP = own['pauldron'] | own['upF'] | own['foreF'] | own['torso']; _best = None
def _pM(s_, r_, dx_, dy_):
    a_ = math.radians(r_); M_ = np.array([[s_ * math.cos(a_), -s_ * math.sin(a_), 0], [s_ * math.sin(a_), s_ * math.cos(a_), 0]]); M_[:, 2] = _pcen + np.array([dx_, dy_]) - M_[:, :2] @ _pc0; return M_
for s_ in np.arange(.80, 1.30, .03):
    for r_ in range(-90, 91, 3):
        for dx_ in range(-8, 9, 2):
            for dy_ in range(2, 15, 2):
                w_ = cv2.warpAffine(_pmk, _pM(s_, r_, dx_, dy_), (512, 512)) > 0
                sc_ = (w_ & own['pauldron']).sum() / own['pauldron'].sum() - ((w_ & ~_allowP).sum() + 2 * (w_ & ~AL).sum()) / own['pauldron'].sum()
                if _best is None or sc_ > _best[0]: _best = (sc_, s_, r_, dx_, dy_)
_pw = cv2.warpAffine(_ps, _pM(*_best[1:]), (512, 512), flags=cv2.INTER_LINEAR)
_crS = (_pw[..., 3] > 200) & (_pw[..., :3].astype(np.float32).mean(-1) > 190); _crA = own['pauldron'] & (RA[..., 3] > 200) & (LUM > 190)
if _crS.sum() > 30 and _crA.sum() > 30: _pw[..., :3][_pw[..., 3] > 0] = np.clip(_pw[..., :3][_pw[..., 3] > 0].astype(np.float32) + (RA[..., :3][_crA].astype(np.float32).mean(0) - _pw[..., :3][_crS].astype(np.float32).mean(0)), 0, 255).astype(np.uint8)   # 크림 색만 평균 맞춤(회색이 푸르게 변하지 않게)
#   대기·달리기 = 원화 어깨갑 + 껍질 안 가려진 곳만 inpaint(대기 = 원화) · 공격 중(.05~.88) = pauldronFs(시트 어깨갑 위에 원화 — 아래 테가 온전, smash17 투명도 키로 바꿈)
_preg = (_hm_ > 0) & ~OPQ('pauldron') & (own['upF'] | own['foreF'])
PAUL_S = _pw.copy(); _po = own['pauldron'] & (RA[..., 3] > 200); PAUL_S[_po] = RA[_po]
ART['pauldron'] = outline_cut(inpaint_into(ART['pauldron'], _preg, _pm & (LUM > 120)), _preg & ~ero(_hm_ > 0, 2))
print('  pauldron fill', int(_preg.sum()), '· 공격용 시트 어깨갑 맞춤 배율·회전·이동', [round(float(v), 2) for v in _best[1:]], '· 점수', round(float(_best[0]), 3))
# 먼 윗팔: 어깨갑 밑 = 시트 13 윗팔(곧은 소매 + 회색 판)을 뼈(어깨 → 팔꿈치)에 맞춰 원화 아래에 깔고, 원화 판·소매가 위
_ua = sheet_rgba('upF'); _m = _ua[..., 3] > 128; _ys, _xs = np.nonzero(_m); _w = float(np.median([_m[y].sum() for y in range(_ys.min() + 10, _ys.max() - 10)]))
_top = np.array([float(np.nonzero(_m[_ys.min() + int(_w / 2)])[0].mean()), _ys.min() + _w / 2]); _bot = np.array([float(np.nonzero(_m[_ys.max() - int(_w / 2)])[0].mean()), _ys.max() - _w / 2])
_sU = float(np.linalg.norm(EL_F - SH_F) / np.linalg.norm(_bot - _top)); _angS = math.atan2(*(_bot - _top)[::-1]); _angB = math.atan2(*(EL_F - SH_F)[::-1]); _r = _angB - _angS
_Mu = np.array([[_sU * math.cos(_r), -_sU * math.sin(_r), 0], [_sU * math.sin(_r), _sU * math.cos(_r), 0]]); _Mu[:, 2] = SH_F - _Mu[:, :2] @ _top
_uw = cv2.warpAffine(_ua, _Mu, (512, 512), flags=cv2.INTER_LINEAR)
#   (시트 윗팔 색은 원화와 가까워 맞추지 않음 — 평균·편차 맞춤은 회색을 푸르게 바꿨음)
_fu = (_uw[..., 3] > 128) & ~OPQ('upF') & (own['pauldron'] | own['upF']) & (_hm_ > 0)   # 어깨갑 껍질 안만(어깨갑이 앞 순서라 대기엔 안 보임 — 밖까지 깔면 상체 옆을 덮음)
ART['upF'][..., :3][_fu] = _uw[..., :3][_fu]; ART['upF'][..., 3][_fu] = _uw[..., 3][_fu]
print('  upF 시트 윗팔 깔기', int(_fu.sum()), 'px · 배율', round(_sU, 3), '· 굵기(원화 px)', round(_w * _sU, 1))
O_ = {n: save_crop(a, n) for n, a in ART.items()}
O_['pauldronS'] = save_crop(PAUL_S, 'pauldronS')
json.dump({n: o.tolist() for n, o in O_.items()}, open(os.path.join(W, 'offsets.json'), 'w'))
if __name__ == 'idlecomp': raise SystemExit   # tools/idlecomp17 용 — 아래부터 ../parts 를 새로 씀
for f in os.listdir(os.path.join(OUT, 'parts')): os.remove(os.path.join(OUT, 'parts', f))

# ---------------- 서 있는 다리: 부츠를 발목 선에서 정강이·발로 나눔 ----------------
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
_empty = os.path.join(W, 'empty.png'); Image.new('RGBA', (2, 2), (0, 0, 0, 0)).save(_empty)   # 가까운 팔 뼈(armU·armL) 빈 그림 — 팔은 방패 뒤
part('head', A('head'), pc(NECK, O_['head']))
part('torso', A('torso'), pc(HIP, O_['torso'])); part('hips', A('hips'), pc(HIP, O_['hips']))
part('pauldronF', A('pauldron'), pc(SH_F, O_['pauldron'])); part('pauldronFs', A('pauldronS'), pc(SH_F, O_['pauldronS']))
part('shield', A('shield'), pc(SH_N, O_['shield']))
part('armU', _empty, [1, 1], elbow=[1, 1 + 26]); part('armL', _empty, [1, 1], fist=[1, 1 + 30])
part('upF', A('upF'), pc(SH_F, O_['upF']), elbow=pc(EL_F, O_['upF']))
part('foreF', A('foreF'), pc(EL_F, O_['foreF']), elbow=pc(EL_F, O_['foreF']))
part('fistF', A('fistF'), pc(WR_F, O_['fistF']))
# 도끼: 자루가 그림 세로(날 위)가 되게 원화 오림을 돌려 2배 해상도로 저장(엔진 _swordRigid 는 무기 그림 위쪽 = 자루 방향)
HTH = float(math.atan2(HU[0], -HU[1]))
_ha = Image.open(A('axe')); _o = O_['axe']; _S = 4
_big = _ha.resize((_ha.width * _S, _ha.height * _S), Image.LANCZOS); _pv = (G - _o) * _S
_pad = int(max(_big.size) * .8); _can = Image.new('RGBA', (_big.width + 2 * _pad, _big.height + 2 * _pad), (0, 0, 0, 0)); _can.paste(_big, (_pad, _pad)); _pv = _pv + _pad
_rot = _can.rotate(math.degrees(HTH), resample=Image.BICUBIC, center=tuple(_pv))
_bb = _rot.getbbox(); _rot = _rot.crop(_bb); _pv = _pv - np.array(_bb[:2]); _rot = _rot.resize((_rot.width // 2, _rot.height // 2), Image.LANCZOS); _pv = _pv / 2
_ra = largest(np.array(_rot)); Image.fromarray(_ra).save(os.path.join(W, 'axeUp.png'))
_axm = own['axe'] | (ART['axe'][..., 3] > 128)
TIPU = float(t_ax[_axm & (t_ax > 120)].mean()); BUTT = float(-t_ax[_axm].min())
BLADE_LO = float(np.percentile(n_ax[_axm & (t_ax > 110)], 99.5))
print('  axe 쥔 점→날 가운데', round(TIPU, 1), '→마개', round(BUTT, 1), '· 날 끝(자루에서)', round(BLADE_LO, 1), '(원화 px)')
_WP = [round(float(_pv[0]), 1), round(float(_pv[1]), 1)]; _up = lambda d: [_WP[0], round(_WP[1] - d * 2, 1)]
for nm in ('weapon', 'weaponA'):
    part(nm, os.path.join(W, 'axeUp.png'), _WP, scale=1.0, tip=_up(TIPU), pommel=_up(-BUTT), tips=[[_WP[0] - 12, round(_WP[1] - TIPU * 2, 1)], [_WP[0] + 12, round(_WP[1] - TIPU * 2, 1)]], shaftDir=[0.0, -1.0])
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
bone('hips', 'hip', HIP, HIP, 'hips')
bone('torso', 'hip', HIP, HIP, 'torso'); bone('head', 'torso', NECK, HIP, 'head')
bone('armU', 'torso', SH_N, HIP, 'armU'); bone('armL', 'armU', SH_N + np.array([0, 13.0]), SH_N, 'armL', rot=0.3)
bone('shield', 'torso', SH_N, HIP, 'shield')
bone('pauldronF', 'torso', SH_F, HIP, 'pauldronF'); bones.append(dict(name='pauldronFs', parent='pauldronF', pos=[0, 0], part='pauldronFs'))
bone('armF', 'torso', SH_F, HIP, 'upF'); bone('foreF', 'armF', EL_F, SH_F, 'foreF'); bone('fistF', 'foreF', WR_F, EL_F, 'fistF')
bone('weapon', 'fistF', G, WR_F, 'weapon', rot=HTH)
for n in ['cape', 'scarf', 'pouch', 'skirt', 'skirtB', 'pauldron']: bones.append(dict(name=n, parent='torso', pos=[0, -200]))

# ---------------- 다리 — 서 있을 때 = 원화 다리 ----------------
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
legs = {'hip': [0, round((LEG_HY - HIP[1]) * 2, 1)], 'thighFirst': True,
        'near': {'x': round(float(LJ['near']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['near']['h'][0] - HIP[0]) * 2, 1), 'runX': round(float(LJ['near']['h'][0] - HIP[0]) * 2, 1), 'shade': 0,
                 'thigh': ln('near', 'h', 'k'), 'shin': ln('near', 'k', 'a'), 'stand': stand('near', 'N')},
        'far': {'x': round(float(LJ['far']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['far']['h'][0] - HIP[0]) * 2, 1), 'runX': round(float(LJ['far']['h'][0] - HIP[0]) * 2, 1), 'shade': 0.12,
                'thigh': ln('far', 'h', 'k'), 'shin': ln('far', 'k', 'a'), 'stand': stand('far', 'F')}}
print('  legs near', legs['near']['thigh'], legs['near']['shin'], 'far', legs['far']['thigh'], legs['far']['shin'])

# ---------------- 달리기 다리 — 시트 15·16(허벅지) + 17·18(정강이 + 부츠, 옆모습 앞코 오른쪽) + 19(무릎 보호대) ----------------
#   크기: 달리는 다리(허벅지 + 정강이) = 서 있는 원화 다리 뿌리~발목 높이에 맞춤(러스트 v1.1 교훈 — 시트 길이 그대로면 다리가 길어 디딘 다리도 굽음)
RUN_TH = float(os.environ.get('RUN_TH', 0))
_runH = float(np.mean([LJ[sd]['a'][1] - LJ[sd]['h'][1] for sd in ('near', 'far')]))   # 서 있는 엉덩이 → 발목 높이(원화 px)
_RS0 = {}
for sd, bn in (('near', 'bootN'), ('far', 'bootF')):
    _b = sheet_rgba(bn); _m = _b[..., 3] > 128; _ys = np.nonzero(_m.any(1))[0]
    _top = np.nonzero(_m[_ys.min() + 3])[0]; KNEE_S = np.array([float(_top.mean()), float(_ys.min() + 3)])
    _ay = int(_ys.max() - (_ys.max() - _ys.min()) * .40); _ar = np.nonzero(_m[_ay])[0]; ANK_S = np.array([float(_ar.min() + (_ar.max() - _ar.min()) * .45), float(_ay)])
    _RS0[sd] = (KNEE_S, ANK_S, _b, _m)
_thF = sheet_rgba('thighF'); _mt = _thF[..., 3] > 128; _ty = np.nonzero(_mt.any(1))[0]
_thL = (_ty.max() - _ty.min()) * .80 - 3                                    # 허벅지 위 끝 → 무릎(아래에서 20%)
_shL = float(np.linalg.norm(_RS0['far'][1] - _RS0['far'][0]))
RS = 2.0                                                                   # 시트 → 리그 배율(시트 1번 = 원화 1:1 — 부츠·무릎 보호대 크기 = 원화)
RUN_THL = round(.96 * 2.0 * _runH - _shL * RS, 1)                          # 달리는 허벅지(리그) = 엉덩이~발목 높이 × .96 − 시트 정강이 (드워프 짧은 다리 — 시트 허벅지는 원화보다 길게 그려짐)
print('  달리기 다리: 시트 허벅지', round(_thL, 1), '+ 정강이', round(_shL, 1), 'px · 원화 엉덩이~발목', round(_runH, 1), '→ 허벅지', RUN_THL, '(시트 허벅지 아래쪽만 씀)')
for sd, bn in (('near', 'bootN'), ('far', 'bootF')):
    KNEE_S, ANK_S, _b, _m = _RS0[sd]; _Y, _X = np.mgrid[0:_b.shape[0], 0:_b.shape[1]]
    _sh = _b.copy(); _sh[..., 3] = np.where(_Y < ANK_S[1] + float(os.environ.get('SH_EXT', 6)), _b[..., 3], 0); Image.fromarray(_sh).save(os.path.join(OUT, 'parts', 'rshin' + sd[0].upper() + '.png'))
    def_parts['rshin' + sd[0].upper()] = dict(src=f'parts/rshin{sd[0].upper()}.png', pivot=[0, 0], scale=1.0)
    _ft = _b.copy(); _ft[..., 3] = np.where(_Y > ANK_S[1] - float(os.environ.get('BT_EXT', 8)), _b[..., 3], 0); Image.fromarray(_ft).save(os.path.join(OUT, 'parts', 'rboot' + sd[0].upper() + '.png'))
    def_parts['rboot' + sd[0].upper()] = dict(src=f'parts/rboot{sd[0].upper()}.png', pivot=ANK_S.tolist(), scale=RS)
    if sd == 'far': KNEE_F, ANK_F, FT_F = KNEE_S, ANK_S, _ft
    else: KNEE_Nn, ANK_Nn, FT_N = KNEE_S, ANK_S, _ft
RUN_SH = round(float(np.linalg.norm(ANK_F - KNEE_F)) * RS, 1)
legs['shin'] = RUN_SH
def sole_sheet(a, ank):
    m = a[..., 3] > 128; ys = np.nonzero(m.any(1))[0]; yb = ys.max(); out = []
    for y in (yb - 6, yb - 3, yb):
        xs = np.nonzero(m[y])[0]; out += [[round(float(xs.min() - ank[0]), 1), round(float(y - ank[1]), 1)], [round(float(xs.max() - ank[0]), 1), round(float(y - ank[1]), 1)]]
    return out
rseg = {}
for n in ['thighN', 'thighF']:   # 시트 허벅지: 위 = 허리 판 밑, 아래 = 둥근 무릎
    a = sheet_rgba(n); m = a[..., 3] > 128
    _ys = np.nonzero(m.any(1))[0]; y0_, y1_ = _ys.min(), _ys.max(); ty, tx = np.nonzero(m[y0_:y0_ + 6]); top = [float(tx.mean()), float(ty.mean() + y0_)]
    kr = int(y0_ + (y1_ - y0_) * .80); kx = np.nonzero(m[kr])[0]; kn = [float(kx.mean()), float(kr)]
    #   허벅지 그림 = 무릎에서 RUN_THL/2 위(a)까지 + 위로 8px 만(그 위는 자름 — 다 쓰면 허벅지가 1.8배 길어 달릴 때 다리가 길어짐)
    _ay = kn[1] - RUN_THL / RS; _axr = np.nonzero(m[int(round(_ay))])[0]; top = [float(_axr.mean()), float(_ay)]
    a = a.copy(); a[:max(0, int(_ay) - 8), :, 3] = 0
    Image.fromarray(a).save(os.path.join(OUT, 'parts', 'r' + n + '.png')); def_parts['r' + n] = dict(src=f'parts/r{n}.png', pivot=[0, 0], scale=1.0)
    rseg[n] = {'part': 'r' + n, 'a': [round(top[0], 1), round(top[1], 1)], 'b': [round(kn[0], 1), round(kn[1], 1)], 'w': 1.0}
legs['thighImg'] = rseg['thighF']; legs['near']['thighImg'] = rseg['thighN']; legs['far']['thighImg'] = rseg['thighF']
_tA, _tB = np.array(rseg['thighF']['a']), np.array(rseg['thighF']['b'])
legs['thigh'] = RUN_TH if 'RUN_TH' in os.environ else round(float(np.linalg.norm(_tB - _tA)) * RS, 1)   # = RUN_THL
print('  run legs thigh', legs['thigh'], 'shin', RUN_SH, '· 무릎', KNEE_F.tolist(), '발목', ANK_F.tolist())
legs['shinImg'] = {'part': 'rshinF', 'a': KNEE_F.tolist(), 'b': ANK_F.tolist(), 'w': 1.0}
legs['near']['shinImg'] = {'part': 'rshinN', 'a': KNEE_Nn.tolist(), 'b': ANK_Nn.tolist(), 'w': 1.0}
#   발목 범위 위 끝 .6 → .8 (DHL 12:27 '다리 걸음이 삐그덕'): 디딘 발이 뜨는 첫 프레임에 정강이가 .6 을 넘으면 엔진이 부츠를 돌려 맞추는데,
#   긴 부츠(시트 1:1 ×2)는 돌리면 발끝이 내려가 발목이 48px 들림 → 다리가 짧아져 더 굽음 → 또 돌림(6번) — 한 프레임에 무릎 22° → 96°.
#   .8 이면 부츠가 거의 평평하게 뜨고 굽힘이 22→32→46→60→71→79→82° 로 이어짐(legprobe17 DBG=near)
legs['boot'] = {'part': 'rbootF', 'sole': sole_sheet(FT_F, ANK_F), 'ankleRange': [-0.35, 0.8]}
legs['near']['boot'] = {'part': 'rbootN', 'sole': sole_sheet(FT_N, ANK_Nn), 'ankleRange': [-0.35, 0.8]}
#   무릎 보호대 = 두 다리 모두 kneeF(네모 판이 앞 = 오른쪽, 금색 관절이 뒤) — DHL 12:27 '무릎이 갑자기 반대편으로 돌아갑니다, 무릎은 동일하게 움직여요':
#   시트 19칸 왼쪽(kneeN)은 좌우가 거꾸로 그려진 짝이라 가까운 다리 무릎만 뒤를 보는 것처럼 보였음 → 한 그림을 두 다리에(먼 다리는 shade 로 어둡게)
for n in ('kneeF',):
    a = sheet_rgba(n); m = a[..., 3] > 128; ys_, xs_ = np.nonzero(m)
    Image.fromarray(a).save(os.path.join(OUT, 'parts', n + '.png')); def_parts[n] = dict(src=f'parts/{n}.png', pivot=[round(float(xs_.mean()), 1), round(float(ys_.mean()), 1)], scale=RS)
legs['near']['kneeImg'] = {'part': 'kneeF'}; legs['far']['kneeImg'] = {'part': 'kneeF'}; legs['kneeImg'] = {'part': 'kneeF'}

# ---------------- 표정·깜빡임: 시트 3~10칸(2칸 머리와 같은 그림 자리) → 머리 맞춤(MH)으로 원화 얼굴에 ----------------
_NEU = sheet_rgba('face_neutral')
def _ecc_to_neutral(a):   # 칸마다 그림 자리가 조금씩 달라(안경 테 겹쳐 보임) — 투구·안경 테로 기본 얼굴 칸에 ECC affine 맞춤
    g = lambda x: cv2.GaussianBlur(cv2.cvtColor(np.ascontiguousarray(x[..., :3]), cv2.COLOR_RGB2GRAY).astype(np.float32), (3, 3), 0)
    h_, w_ = _NEU.shape[:2]; a = a[:h_, :w_] if a.shape[0] >= h_ and a.shape[1] >= w_ else cv2.copyMakeBorder(a, 0, max(0, h_ - a.shape[0]), 0, max(0, w_ - a.shape[1]), cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))[:h_, :w_]
    m = ((_NEU[..., 3] > 200) & (a[..., 3] > 200)).astype(np.uint8)
    Wm = np.eye(2, 3, dtype=np.float32)
    try: _, Wm = cv2.findTransformECC(g(_NEU), g(a), Wm, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), m, 3)
    except cv2.error as e: print('  ECC 실패', e); return a
    print('  얼굴 칸 ECC 이동', Wm[:, 2].round(2).tolist())
    return cv2.warpAffine(a, Wm, (w_, h_), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderValue=(0, 0, 0, 0))
_AL = {n: (sheet_rgba(n) if n == 'face_neutral' else _ecc_to_neutral(sheet_rgba(n))) for n in ['face_neutral', 'face_happy', 'face_angry', 'face_focus', 'face_shout', 'face_effort', 'blink_half', 'blink_closed']}
_wfs = {n: cv2.warpAffine(_AL[n], MH, (512, 512), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)).astype(np.int16)
        for n in ['face_neutral', 'face_happy', 'face_angry', 'face_focus', 'face_shout', 'face_effort', 'blink_half', 'blink_closed']}
_dif = np.zeros((512, 512), bool)
for n, w_ in _wfs.items():
    if n != 'face_neutral': _dif |= (np.abs(w_[..., :3] - _wfs['face_neutral'][..., :3]).sum(-1) > 60) & (w_[..., 3] > 200)
_box = np.zeros((512, 512), bool); _box[226:266, 262:352] = True   # 눈썹·눈(가리개 위 — 27 은 입이 가리개 밑)
_dif &= _box; _dif = ndimage.binary_opening(_dif, np.ones((2, 2)))
FACE = ndimage.binary_fill_holes(cv2.morphologyEx(dil(_dif, 4).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0) & (ART['head'][..., 3] > 200) & _box
_fm = np.clip(cv2.GaussianBlur(cv2.erode(FACE.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (5, 5), 1.0) * 1.15, 0, 1)
_SK = SKIN(ART['head'])
_omean = ART['head'][..., :3][_SK & FACE].mean(0) if (_SK & FACE).sum() > 20 else ART['head'][..., :3][_SK].mean(0)
hb = np.array(Image.open(A('head'))); hx0, hy0 = int(O_['head'][0]), int(O_['head'][1]); hh, hw = hb.shape[:2]
def face_patch(cellname, out):
    a = _AL[cellname]
    wf = cv2.warpAffine(a, MH, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
    s3 = SKIN(wf)
    if (s3 & FACE).sum() > 50: d = _omean - wf[..., :3][s3 & FACE].mean(0); wf = wf.copy(); wf[..., :3][s3] = np.clip(wf[..., :3][s3].astype(np.float32) + d, 0, 255).astype(np.uint8)
    al = _fm * (wf[..., 3] / 255.0); o2 = ART['head'].astype(np.float32).copy(); o2[..., :3] = o2[..., :3] * (1 - al[..., None]) + wf[..., :3] * al[..., None]
    fc = o2.astype(np.uint8)[hy0:hy0 + hh, hx0:hx0 + hw].copy(); fc[..., 3] = np.where(FACE[hy0:hy0 + hh, hx0:hx0 + hw], hb[..., 3], 0)
    Image.fromarray(fc).save(os.path.join(W, out + '.png'))
FACE_N = ['neutral', 'happy', 'angry', 'focus', 'shout', 'effort']
for n in FACE_N: face_patch('face_' + n, 'face_' + n); part('face_' + n, os.path.join(W, 'face_' + n + '.png'), def_parts['head']['pivot'])
for n in ['half', 'closed']: face_patch('blink_' + n, 'blink_' + n); part('blink_' + n, os.path.join(W, 'blink_' + n + '.png'), def_parts['head']['pivot'])
FACES = {n: 'face_' + n for n in FACE_N if n != 'neutral'}; FACES['grimace'] = 'face_effort'; FACES['surprised'] = 'face_shout'
print('  face px', int(FACE.sum()))

# ---------------- 내려찍기: 7 러스트 smash7 구조(attack/smash27.py — 키는 네온 몸·팔·도끼로 attack/keys17.json) ----------------
exec(open(os.path.join(HERE, 'attack', 'smash27.py')).read())

# ---------------- 그리는 순서 (뒤 → 앞) ----------------
#   7 러스트 v1.5 규칙: 먼 팔뚝·도끼·쥔 주먹 = 다리·골반·머리 뒤 · 다리 = 상체·골반 뒤 · 윗팔 = 상체 앞
#   네온: 먼 어깨갑은 윗팔 판 뒤(원화 — 회색 판이 어깨갑 아래 끝 위) · 목 가리개 = 머리 앞 · 방패 = 맨 앞
#   먼 어깨갑 = 윗팔 앞(윗팔이 어깨갑 밑에서 나옴 — 러스트와 같음). 원화는 회색 판 위 끝·팔뚝 갑 모서리가 어깨갑 테 위에 조금 걸침(131+63px) → 대기에선 어깨갑 테가 그만큼 덮음
draw = ['foreF', 'weapon', 'fistF', 'legFar', 'legNear', 'torso', 'armF', 'pauldronF', 'hips', 'head', 'armU', 'armL', 'shield']
_top = MS['hatTop'][1]
_a = np.array(Image.open(os.path.join(HERE, '..', '..', '..', 'art', 'characters', 'char_0027.png')).convert('RGBA').resize((160, 160), Image.BOX))[..., 3]
_ys, _xs = np.nonzero(_a > 40); FIT_CX = round(float(((_xs.min() + _xs.max() + 1) / 2 + _xs.mean() + .5) / 2 / 160 * 512), 1)
rig = {'name': 'lucia-sky', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': def_parts, 'bones': bones, 'legs': legs, 'draw': draw, 'hidden': [], 'faces': FACES, 'blinkFaces': {'half': 'blink_half', 'closed': 'blink_closed'},
       'metrics': {'bodyHeight': round(2 * (O[1] - _top), 1), 'note': f'리그 단위; 모자 꼭대기(y{_top})~발바닥({O[1]:.0f}) ×2, 무기 제외'},
       'armPhase': 0,
       # 7 러스트 v1.1 드워프 종종걸음 그대로
       'gait': {'stance': 0.26, 'strideBase': 26, 'strideK': 0.08, 'hipBase': 4, 'bob': 4, 'lean': 0.12, 'waddle': 0.03, 'headBob': 3, 'kneeLift': 0.2, 'heelKick': 0.05, 'dropCap': 8,
                'swingReach': 0.05, 'swingAng': 0, 'landAng': -0.04, 'angK': 0.12, 'strideFlex': [0.75, 1.15], 'headRun': 0.05, 'elbowRun': 0, 'armSwing': 0.5, 'armBias': 0.0},
       'carrySwing': 0.35, 'wristRange': 0.3,
       'follow': [{'bone': 'pauldronF', 'src': 'armF', 'k': float(os.environ.get('PAUL_K', 1.0)), 'world': True}, {'bone': 'shield', 'src': 'torso', 'k': -0.6}],
       'bounce': [{'bone': 'shield', 'stiff': 170, 'damp': 9, 'y': 0.25, 'rot': 0.004, 'max': 8}],
       'ui': {'attack': 'smash', 'touch': 'hop'},
       'gameRef': {'refOrigin': [round(float(O[0] - (HIP[0] - FIT_CX)), 1), float(O[1])], 'refScale': 2.0, 'refLift': 0,
                   'note': f'게임 그림 char_0027.png(512) = 원화(source/ref512.png). x = 도감 칸(fitArt 중심 {FIT_CX}, index.html measureBox 와 같은 계산 — 20 build_bruno20 과 같음)에서 골반(hip x {HIP[0]:.0f})이 가운데'},
       'cutHold': float(os.environ.get('CUTHOLD', 0.36)),   # 스킬 컷인 = 도끼를 앞으로 휘둘러 내리는 중(외침 얼굴). 7 러스트 .34 는 네온 도끼(위 끝 52, 러스트 57)가 칸 위로 PC 혼자 3·둘 13 · 폰 2·4px 잘림 → .36 PC 12·11 · 폰 18·16px 안(tools/cutpair17.py HOLD7)
       'note': '27 스카이 루시아 v1.1 (2026-10-21 — 17 네온 v1.2 구조, 가까운 주먹 없음(DHL 20:33 — 방패 뒤), 한 손 도끼 내려찍기, 드워프 종종걸음 · 가려진 곳 = 지운 원화 2장 + 시트 19칸)'}
rig.update(SMASH)
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(os.path.join(OUT, 'parts'))): _h.update(fn.encode()); _h.update(open(os.path.join(OUT, 'parts', fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build27.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['lucia-sky']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(def_parts), 'parts, version', rig['version'], 'bodyHeight', rig['metrics']['bodyHeight'])
