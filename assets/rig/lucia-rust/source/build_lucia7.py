"""7 러스트 루시아 리그 조립 v1 (2026-10-20 21:xx — DHL 19:41 '진행해 보시죠!' · 20:44 조각 시트 25칸 → 합격)
구조 = 22 스카이 둘시네 build_sky22.py(12 네온 v1.4 동작·그리는 순서) 그대로 + 루시아만의 것:
  ①방패 = 가까운 어깨(SH_N)에 붙은 뼈 'shield'(상체 자식) — 가까운 팔(armU·armL)은 방패 뒤라 안 보임(엔진용 빈 조각). 방패는 엔진 자유 팔(armU)을 follow 로 조금 따라 돎(달리기 흔들림·공격 fuA)
  ②가까운 주먹 = 방패 뼈 자식 'fistN'(방패 손잡이 쥔 채 같이 움직임)
  ③먼 어깨 보호대 = 'pauldronF'(먼 팔 armF 를 follow) — 엔진 'pauldron'(가까운 어깨갑) 뼈는 빈 뼈
  ④무기 = 원화 도끼(날이 자루 축에서 약 6° 돈 그림 그대로 — 시트 도끼는 곧음) + 먼 주먹 밑 자루 = 시트 도끼 자루를 축 맞춰 채움
  ⑤먼 팔: 갈색 걷은 소매 = 윗팔(upF, 어깨 보호대 밑까지 이어 그림) · 살 팔뚝 + 갈색 손목 띠 = foreF · 주먹 = fistF
입력: ref512.png(새 원화 = 게임 char_0007, 20:20 합격) · work/labels.npy(seg7.py) · pieces/(시트 25칸, cut7.py) · reg7.py(시트→원화 맞춤)
출력: ../rig.json, ../rig.def.js, ../parts/*.png      실행: cd source && python3 -I build_lucia7.py
원칙: 대기 = 원화(보이는 곳은 원화를 오림), 가려진 곳만 시트·inpaint. 손 조각 뒤집기 금지. 팔다리 길이 고정. 좌표: 원화 512px 로 적고 ×2 = 리그 단위."""
import json, math, os, shutil, hashlib, sys, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work'); OUT = os.path.join(HERE, '..')
os.makedirs(os.path.join(OUT, 'parts'), exist_ok=True); os.makedirs(W, exist_ok=True)
for f in os.listdir(os.path.join(OUT, 'parts')): os.remove(os.path.join(OUT, 'parts', f))
img = lambda p: np.array(Image.open(p).convert('RGBA'))
RA = img(os.path.join(HERE, 'ref512.png')); AL = RA[..., 3] > 8
def pmask(pts):
    m = Image.new('L', (512, 512), 0); ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255); return np.array(m) > 0
def dil(m, r): return cv2.dilate(m.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0
def ero(m, r): return cv2.erode(m.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0
yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)
LUM = RA[..., :3].astype(np.float32).mean(-1)
unitv = lambda v: np.array(v, float) / np.linalg.norm(v)

# ---------------- 원화 관절 (512 px, 10-20 20:5x 격자 확대 tools/gridzoom.py 에서 잼) ----------------
O = np.array([273.0, 448.0])                                      # 뿌리: 두 발 가운데(가까운 172~250 · 먼 304~372) 땅(발바닥 448)
HIP = np.array([280.0, 351.0]); NECK = np.array([288.0, 290.0])   # 골반(허리띠 가운데, 버클 (281,352)) · 목(쇠 가리개 밑 = 머리 회전 중심)
SH_N, FIST_N = np.array([238.0, 285.0]), np.array([210.0, 340.0])   # 가까운 어깨(방패 뒤, 안 보임) · 가까운 주먹(방패 오른쪽 가장자리 배 높이)
SH_F, EL_F, WR_F = np.array([355.0, 290.0]), np.array([389.0, 337.0]), np.array([411.0, 311.0])   # 먼 팔: 어깨(보호대 밑) · 팔꿈치(걷은 소매 끝 → 살) · 손목(살 → 갈색 띠)
POMMEL, COLLAR = np.array([448.0, 342.0]), np.array([412.0, 215.0])   # 도끼 자루 끝 마개 가운데 · 쇠 목 아래
HU = unitv(COLLAR - POMMEL)                                        # 자루 방향(쥔 손 → 날), 세로에서 뒤로 약 16°
G = POMMEL + HU * float(np.dot(np.array([434.3, 294.0]) - POMMEL, HU))   # 쥔 점: 자루 축 위, 먼 주먹 가운데 높이(y 294)
LJ = {'near': dict(h=np.array([245.0, 362]), k=np.array([231.0, 393]), a=np.array([207.0, 430])),
      'far': dict(h=np.array([310.0, 362]), k=np.array([349.0, 392]), a=np.array([342.0, 430]))}   # 무릎 = 무릎 쇠판 가운데 · 발목 = 정강이 끈 아래(부츠 목)
LEG_HY = 362.0
#   서 있는 다리는 다 펴지 않음(엉덩이→발목 / 다리 길이 ≤ .985 — 22 교훈): 넘으면 무릎을 다리 축에서 앞(+x 쪽)으로 밀어 맞춤
for sd in ('near', 'far'):
    j = LJ[sd]; ha = np.linalg.norm(j['a'] - j['h']); L_ = np.linalg.norm(j['k'] - j['h']) + np.linalg.norm(j['a'] - j['k'])
    if ha / L_ > .985:
        u_ = (j['a'] - j['h']) / ha; n_ = np.array([-u_[1], u_[0]]); n_ = n_ if n_[0] > 0 else -n_; k0 = j['k'].copy()
        for s_ in np.arange(0, 12, .1):
            j['k'] = k0 + n_ * s_
            if ha / (np.linalg.norm(j['k'] - j['h']) + np.linalg.norm(j['a'] - j['k'])) <= .985: break
        print(f'  {sd} 무릎 앞으로 {s_:.1f}px → {j["k"].round(1).tolist()}')
    print(f'  {sd} 다리 펴짐', round(float(ha / (np.linalg.norm(j['k'] - j['h']) + np.linalg.norm(j['a'] - j['k']))), 3))
print('  far arm 리그 L1 %.1f · L2 %.1f · 손목→쥔 점 %.1f' % (2 * np.linalg.norm(EL_F - SH_F), 2 * np.linalg.norm(WR_F - EL_F), 2 * np.linalg.norm(G - WR_F)), '· G', G.round(1).tolist())

# ---------------- 원화 칸 나누기 (seg7.py — 씨앗 다각형 + 외곽선 watershed) → 리그 부품 ----------------
LBL = os.path.join(W, 'labels.npy')
if not os.path.exists(LBL) or os.path.getmtime(LBL) < max(os.path.getmtime(os.path.join(HERE, f)) for f in ('polys7.json', 'ref512.png', 'seg7.py')):
    subprocess.run([sys.executable, '-I', os.path.join(HERE, 'seg7.py'), os.path.join(HERE, 'ref512.png')], check=True, stdout=subprocess.DEVNULL)
SL = np.load(LBL); SEGN = json.load(open(os.path.join(W, 'label_names.json')))
RIGN = {'handN': 'fistN', 'handF': 'fistF', 'body': 'torso'}
own = {RIGN.get(n, n): (SL == i + 1) & AL for i, n in enumerate(SEGN)}
_hsv = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV)
CREAM = (_hsv[..., 1] < 80) & (_hsv[..., 2] > 170) & (RA[..., 0].astype(int) > RA[..., 2].astype(int) + 20) & (RA[..., 3] > 200)   # 목도리 크림색
SKIN = (_hsv[..., 0] >= 5) & (_hsv[..., 0] <= 22) & (_hsv[..., 1] > 90) & (_hsv[..., 2] > 140) & (RA[..., 3] > 200)
GREY = (_hsv[..., 1] < 55) & (_hsv[..., 2] > 110) & (RA[..., 3] > 200)   # 쇠(무릎 판·투구·도끼 날)
# 가리개 밑 목도리(크림)가 머리 칸에 들어가 있음 → 상체로(머리가 돌면 목도리 조각이 붙어 다님)
#   가리개 아래 외곽선 = (245,262) → (300,291) 직선(격자 확대 21:2x), 선 굵기 3px 까지 머리
_scarf = own['head'] & (yy > 262 + (xx - 245) * 0.527 + 3.5) & (xx >= 238) & (xx < 304)
own['torso'] |= _scarf; own['head'] &= ~_scarf; print('  head 목도리 → 상체', int(_scarf.sum()))
# 먼 팔: 걷은 갈색 소매 끝 선((381,318) → (397,350)) 왼쪽 = 윗팔 upF, 오른쪽 = 살 팔뚝 + 손목 띠 foreF
_p1, _p2 = np.array([381.0, 318.0]), np.array([397.0, 350.0]); _nv = unitv([(_p2 - _p1)[1], -(_p2 - _p1)[0]])   # 오른쪽(+x) 법선
_side = (xx - _p1[0]) * _nv[0] + (yy - _p1[1]) * _nv[1]
own['upF'] = own['foreF'] & (_side < 0); own['foreF'] &= ~own['upF']
# 다리: 허벅지 = 다리 칸 중 무릎 쇠판이 아니고 엉덩이→무릎 축에서 무릎보다 위 · 나머지(무릎 판·정강이 끈·부츠) = boot
for sd, ln, tn, bn in (('near', 'legN', 'thighN', 'bootN'), ('far', 'legF', 'thighF', 'bootF')):
    h, k = LJ[sd]['h'], LJ[sd]['k']; u_ = unitv(k - h); t_ = (xx - h[0]) * u_[0] + (yy - h[1]) * u_[1]
    plate = dil(GREY & own[ln], 2) & own[ln]
    own[tn] = own[ln] & ~plate & (t_ < np.linalg.norm(k - h) - 2); own[bn] = own[ln] & ~own[tn]
    del own[ln]
print('  labels', {n: int(m.sum()) for n, m in own.items()})

# ---------------- 조각 오리기: 주인 칸 + 앞 조각 밑 3px 겹침 + 가려진 곳 메우기 ----------------
#   원화 앞뒤(뒤 → 앞): 먼 다리 · 가까운 다리 · 상체 · 골반(허리띠가 튜닉 앞) · 머리 · 먼 윗팔(소매 — 상체·허리띠 끝 앞) · 먼 팔뚝 · 도끼 · 먼 주먹 · 어깨 보호대 · 방패 · 가까운 주먹
DRAW_ART = ['thighF', 'bootF', 'thighN', 'bootN', 'torso', 'hips', 'head', 'upF', 'foreF', 'axe', 'fistF', 'pauldron', 'shield', 'fistN']
def above(n):
    i = DRAW_ART.index(n); return np.logical_or.reduce([own[m] for m in DRAW_ART[i + 1:] if m in own] + [np.zeros((512, 512), bool)])
def inpaint_into(a, region, src_ok, r=5):
    rgb = np.ascontiguousarray(a[..., :3].copy()); d, (iy, ix) = ndimage.distance_transform_edt(~src_ok, return_indices=True)
    rgb[~src_ok] = rgb[iy[~src_ok], ix[~src_ok]]
    out = cv2.inpaint(rgb, region.astype(np.uint8) * 255, r, cv2.INPAINT_TELEA); a = a.copy(); a[..., :3][region] = out[region]; a[..., 3][region] = 255; return a
def outline_cut(a, cutmask, w=2.4):
    A = a[..., 3] > 128; d = ndimage.distance_transform_edt(A); e = A & dil(cutmask, 1) & (d <= w + .2)
    k = np.clip(w + .4 - d, 0, 1)[e][:, None]; a = a.copy(); a[..., :3][e] = (a[..., :3][e] * (1 - k) + np.array([28, 24, 22]) * k).astype(np.uint8); return a
def save_crop(a, name):
    ys, xs = np.nonzero(a[..., 3] > 0); x0, y0 = xs.min() - 2, ys.min() - 2
    Image.fromarray(a[y0:ys.max() + 3, x0:xs.max() + 3]).save(os.path.join(W, name + 'Art.png')); return np.array([x0, y0], float)
def largest(a):   # 큰 덩어리만(찌꺼기 지움)
    n_, l_, s_, _ = cv2.connectedComponentsWithStats((a[..., 3] > 10).astype(np.uint8), 8); a = a.copy(); a[..., 3] = np.where(l_ == 1 + int(np.argmax(s_[1:, cv2.CC_STAT_AREA])), a[..., 3], 0); return a
MOVING = own['upF'] | own['foreF'] | own['fistF'] | own['axe'] | own['pauldron']
FRONTS = own['shield'] | own['fistN']                                  # 방패·가까운 주먹(상체에 붙어 있지만 follow·출렁임으로 조금 움직임)
ART = {}
for n in DRAW_ART:
    _ab = dil(own[n], 3) & above(n) & AL
    if n in ('torso', 'hips', 'thighN', 'thighF', 'bootN', 'bootF', 'head'): _ab &= ~(MOVING | FRONTS)   # 움직이는 팔·도끼·방패 밑 겹침은 안 가져옴(외곽선이 떠 보임) — 그 밑은 메우기
    if n in ('upF', 'foreF', 'fistF'): _ab &= ~(own['torso'] | own['hips'] | own['pauldron'])           # 먼 팔은 상체·골반·보호대 밑 겹침을 안 가져옴(팔이 떠나면 그 조각이 붙어 다님)
    if n == 'axe': _ab &= ~(own['head'] | own['pauldron'])
    if n == 'shield': _ab &= ~(own['head'] | own['torso'] | own['hips'] | own['bootN'] | own['thighN'])   # 방패 둘레에 몸 조각이 붙어 다니지 않게(방패는 맨 앞)
    m = own[n] | _ab; a = RA.copy(); a[..., 3] = np.where(m, RA[..., 3], 0); ART[n] = a
OPQ = lambda n: ART[n][..., 3] > 200

# ---- 시트 조각 (cut7.py) + 시트→원화 맞춤(reg7.py SIFT) ----
if not os.path.exists(os.path.join(HERE, 'pieces', 'index.json')):   # 시트 조각(pieces/ — git 에 안 올림)은 시트에서 다시 자름
    subprocess.run([sys.executable, '-I', os.path.join(HERE, 'cut7.py'), os.path.join(HERE, 'sheets', 'sheet1.png')], check=True, stdout=subprocess.DEVNULL)
sys.path.insert(0, HERE); import reg7
PC = os.path.join(HERE, 'pieces')
def sheet_rgba(n):   # 시트 조각 + 자홍 테두리 빼기
    a = np.array(Image.open(os.path.join(PC, n + '.png')).convert('RGBA')).astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None)
    a[..., 0] -= m; a[..., 2] -= m; return np.clip(a, 0, 255).astype(np.uint8)
def color_match(src, sel_src, sel_ref):   # 시트 색 → 원화 색(평균·편차)
    mu_s, sd_s = src[..., :3][sel_src].astype(float).mean(0), src[..., :3][sel_src].astype(float).std(0) + 1
    mu_a, sd_a = RA[..., :3][sel_ref].astype(float).mean(0), RA[..., :3][sel_ref].astype(float).std(0) + 1
    out = src.copy(); out[..., :3] = np.clip((src[..., :3].astype(float) - mu_s) / sd_s * sd_a + mu_a, 0, 255).astype(np.uint8); return out

# 머리: 방패·어깨 보호대에 가려진 투구·볏·머리카락 = 시트 2칸 머리(SIFT 닮음, 배율 .99)를 원화 색으로 맞춰 채움 — 머리가 돌면 방패 가장자리에서 드러남
_rhd = reg7.match('head', reg7.REG['head']); MH = np.array(_rhd['M'])
_hw = cv2.warpAffine(sheet_rgba('head'), MH, (512, 512), flags=cv2.INTER_LINEAR)
_ov = (_hw[..., 3] > 200) & OPQ('head') & ~dil(~own['head'], 3)
_hw = color_match(_hw, _ov, _ov)
_fillH = (_hw[..., 3] > 128) & ~OPQ('head') & (own['shield'] | own['fistN'] | own['pauldron'])   # 방패·보호대 칸 안만(밖으로 나가면 대기에서 보임)
ART['head'][..., :3][_fillH] = _hw[..., :3][_fillH]; ART['head'][..., 3][_fillH] = _hw[..., 3][_fillH]
ART['head'] = largest(ART['head'])
print('  head sheet fill', int(_fillH.sum()), 'px · scale', _rhd['scale'], 'rot', _rhd['rot'], 'inl', _rhd['inl'])
# 상체: 방패 가장자리 띠(28px)·어깨 보호대·먼 소매 밑·턱(가리개) 밑 — 상체 테두리 다각형 안, inpaint
TORSO_HULL = pmask([[222, 262], [240, 252], [262, 262], [300, 286], [330, 276], [352, 286], [360, 312], [352, 340], [300, 342], [225, 342], [214, 318], [216, 285]])
_reg = TORSO_HULL & ((own['shield'] & dil(own['torso'], 28)) | own['fistN'] | own['pauldron'] | own['upF'] | (own['head'] & dil(own['torso'], 10))) & ~OPQ('torso')
#   (21:5x) 오른쪽(먼 소매·보호대 밑) = 시트 13칸 상체(tools/torsofit7.py — 배율 1.31·회전 −8°, 시트 상체도 원화보다 작게 그려짐)를 원화 색으로 — 팔을 들면 튜닉 오른쪽 가장자리·외곽선이 시트대로 보임
#   (inpaint 만으로는 소매 자리가 옅은 크림 얼룩 + 톱니 가장자리였음). 시트가 안 덮는 곳은 상체 밖(빈칸 = 실루엣)
_tf = json.load(open(os.path.join(HERE, 'torso_fit7.json'))) if os.path.exists(os.path.join(HERE, 'torso_fit7.json')) else None
_regR = TORSO_HULL & (own['pauldron'] | own['upF']) & ~OPQ('torso')
if _tf:
    _tw = cv2.warpAffine(sheet_rgba('torso'), np.array(_tf['M']), (512, 512), flags=cv2.INTER_LINEAR)
    _ovt = (_tw[..., 3] > 200) & OPQ('torso') & own['torso'] & ~dil(~own['torso'], 3); _tw = color_match(_tw, _ovt, _ovt)
    _fr = _regR & (_tw[..., 3] > 128)
    ART['torso'][..., :3][_fr] = _tw[..., :3][_fr]; ART['torso'][..., 3][_fr] = _tw[..., 3][_fr]
    _reg &= ~_regR
    print('  torso sheet fill(오른쪽)', int(_fr.sum()), 'px')
ART['torso'] = outline_cut(inpaint_into(ART['torso'], _reg, own['torso'] & (RA[..., 3] > 200) & ~dil(~AL, 2) & ~dil(LUM < 60, 1)), _reg & dil(~TORSO_HULL, 1))   # 외곽선(어두운 선)은 메움 재료에서 뺌 — 보호대 밑 검은 번짐
print('  torso fill', int(_reg.sum()))
# 골반: 방패·가까운 주먹 밑(허리띠 왼쪽 끝·튜닉 자락) — 골반 다각형 안
HIPS_HULL = pmask([[212, 338], [240, 334], [280, 338], [330, 335], [342, 345], [348, 370], [345, 396], [300, 402], [245, 404], [212, 392], [206, 362]])
_reg = HIPS_HULL & ((own['shield'] & dil(own['hips'], 22)) | own['fistN']) & ~OPQ('hips')   # 먼 소매 밑은 안 메움: 리그 순서에서 골반이 소매 앞이라 메우면 대기에서 소매 끝을 덮음
ART['hips'] = outline_cut(inpaint_into(ART['hips'], _reg, own['hips'] & (RA[..., 3] > 200) & ~dil(~AL, 2)), _reg & dil(~HIPS_HULL, 1))
print('  hips fill', int(_reg.sum()))
# 도끼 자루(먼 주먹 밑): 주먹 위 감은 자루(축 t 42~78, 고리 t 27~41 과 쇠 목 t 82 사이)를 축 따라 36px 주기로 내려 채움(22 망치와 같은 방법)
#   — 시트 도끼를 맞춰 넣으면(21:1x 첫 시도) 원화 색 맞춤에서 고리 아래 청록 줄·옅은 얼룩이 생겼음
t_ax = (xx - G[0]) * HU[0] + (yy - G[1]) * HU[1]; n_ax = (xx - G[0]) * -HU[1] + (yy - G[1]) * HU[0]
SHAFT_HW = float(np.median([float(np.ptp(n_ax[own['axe'] & (np.abs(t_ax - tt) < .8) & (np.abs(n_ax) < 18)])) for tt in range(46, 72, 3)])) / 2   # 원화 자루 반폭(외곽선 포함, 주먹 위 감은 곳)
WRAP0, WRAP1 = 42.0, 78.0
_hreg = (np.abs(n_ax) <= SHAFT_HW + .5) & (t_ax > -34) & (t_ax < WRAP0) & ~OPQ('axe') & (own['fistF'] | own['foreF'])   # 주먹·손목 밑만(밖은 대기에서 보임)
_tsrc = WRAP0 + np.mod(t_ax - WRAP0, WRAP1 - WRAP0)
_sx_ = np.clip(np.round(G[0] + HU[0] * _tsrc - HU[1] * n_ax), 0, 511).astype(int); _sy_ = np.clip(np.round(G[1] + HU[1] * _tsrc + HU[0] * n_ax), 0, 511).astype(int)
_ok = _hreg & own['axe'][_sy_, _sx_]
ART['axe'][..., :3][_ok] = RA[..., :3][_sy_[_ok], _sx_[_ok]]; ART['axe'][..., 3][_ok] = 255
_fistz = (np.abs(n_ax) <= SHAFT_HW + .5) & (t_ax > -34) & (t_ax < WRAP0) & dil(own['fistF'] | own['foreF'], 1) & own['axe']   # 주먹 외곽선에 붙은 원화 조각(살·밝은 점)도 자루 무늬로
_ok2 = _fistz & own['axe'][_sy_, _sx_]; ART['axe'][..., :3][_ok2] = RA[..., :3][_sy_[_ok2], _sx_[_ok2]]
_junk = (t_ax > -34) & (t_ax < WRAP0 - 2) & (np.abs(n_ax) > SHAFT_HW + 1) & (ART['axe'][..., 3] > 0) & ~dil(own['axe'] & (np.abs(n_ax) > SHAFT_HW + 4) & (t_ax < -30), 2)   # 자루 띠 밖 주먹 외곽선 부스러기
ART['axe'][..., 3][_junk] = 0
_hole = _hreg & ~_ok; ART['axe'] = inpaint_into(ART['axe'], _hole, OPQ('axe') & (np.abs(n_ax) <= SHAFT_HW), r=3) if _hole.any() else ART['axe']
print('  axe shaft fill', int(_ok.sum()), '+ inpaint', int(_hole.sum()), 'px · 자루 반폭', round(SHAFT_HW, 1))
# 먼 윗팔(upF): 어깨 보호대·상체 밑으로 어깨(SH_F)까지 갈색 소매 관 — 팔이 돌면 드러남
_ua = unitv(EL_F - SH_F); _ut = (xx - SH_F[0]) * _ua[0] + (yy - SH_F[1]) * _ua[1]; _ud = (xx - SH_F[0]) * -_ua[1] + (yy - SH_F[1]) * _ua[0]
_band = own['upF'] & (np.abs(_ut - (np.linalg.norm(EL_F - SH_F) - 16)) < 3)
UP_D = (float(_ud[_band].min()), float(_ud[_band].max())); UP_HW = min((UP_D[1] - UP_D[0]) / 2 - 1.0, 15.0); UP_DC = (UP_D[0] + UP_D[1]) / 2
_ext = ((((np.abs(_ud - UP_DC) <= UP_HW) & (_ut >= 0) & (_ut <= np.linalg.norm(EL_F - SH_F))) | (np.hypot(xx - SH_F[0] - (-_ua[1]) * UP_DC, yy - SH_F[1] - _ua[0] * UP_DC) <= UP_HW))
        & ~OPQ('upF') & own['pauldron'])   # 보호대 밑만 — 리그 순서에서 소매가 상체 앞이라 상체 칸까지 메우면 대기에서 튜닉을 덮음
_src = own['upF'] & (RA[..., 3] > 200) & ~SKIN & (LUM > 45)
ART['upF'] = inpaint_into(ART['upF'], _ext, _src)
ART['upF'] = outline_cut(ART['upF'], dil(_ext, 1) & ~own['upF'] & ~(own['pauldron']))
ART['upF'] = outline_cut(ART['upF'], own['torso'] | own['hips'])
print('  far upper sleeve 반폭', round(UP_HW, 1), '가운데', round(UP_DC, 1), 'fill', int(_ext.sum()))
# 허벅지: 튜닉 자락(골반) 밑으로 엉덩이 관절까지 바지색
for sd, n in [('near', 'thighN'), ('far', 'thighF')]:
    _e = np.zeros((512, 512), np.uint8); h, k = LJ[sd]['h'], LJ[sd]['k']; cv2.line(_e, tuple(int(v) for v in h), tuple(int(v) for v in (h + k) / 2), 1, 26)
    _e = _e.astype(bool) & ~OPQ(n) & (own['hips'] | (own['shield'] if sd == 'near' else False)) & AL
    ART[n] = inpaint_into(ART[n], _e, own[n] & (RA[..., 3] > 200) & (LUM > 40))
    print(f'  {n} fill', int(_e.sum()))
O_ = {n: save_crop(a, n) for n, a in ART.items()}
json.dump({n: o.tolist() for n, o in O_.items()}, open(os.path.join(W, 'offsets.json'), 'w'))
if __name__ == 'idlecomp': raise SystemExit   # tools/idlecomp7.py: 오린 조각까지만

# ---------------- 서 있는 다리: 원화 부츠를 발목 선에서 정강이·발로 나눔 ----------------
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
_empty = os.path.join(W, 'empty.png'); Image.new('RGBA', (2, 2), (0, 0, 0, 0)).save(_empty)   # 엔진이 쓰는 가까운 팔 뼈(armU·armL)의 빈 그림 — 팔은 방패 뒤
part('head', A('head'), pc(NECK, O_['head']))
part('torso', A('torso'), pc(HIP, O_['torso'])); part('hips', A('hips'), pc(HIP, O_['hips']))
part('pauldronF', A('pauldron'), pc(SH_F, O_['pauldron']))
part('shield', A('shield'), pc(SH_N, O_['shield'])); part('fistN', A('fistN'), pc(FIST_N, O_['fistN']))
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
TIPU = float(t_ax[_axm & (t_ax > 90)].mean()); BUTT = float(-t_ax[_axm].min())
BLADE_LO = float(np.percentile(n_ax[_axm & (t_ax > 85)], 99.5))   # 날 앞(+n) 끝 = 타격 때 땅에 닿는 날 끝(자루에 수직 거리)
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
bone('armU', 'torso', SH_N, HIP, 'armU'); bone('armL', 'armU', SH_N + np.array([0, 13.0]), SH_N, 'armL', rot=0.3)   # 엔진 자유 팔(빈 그림) — 대기 팔꿈치 처짐(−0.3)만큼 미리 반대로
bone('shield', 'torso', SH_N, HIP, 'shield'); bone('fistN', 'shield', FIST_N, SH_N, 'fistN')
bone('pauldronF', 'torso', SH_F, HIP, 'pauldronF')
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
# v1.1 (DHL 21:44 '다리가 너무 구부러짐 — 다른 모델 참고'): 달릴 때 발이 지나가는 줄(runX) = 다리 뿌리(hipX) 바로 밑 — 팔로메·카르덴처럼 3/4 몸의 두 다리가 각자 제자리에서 걸음.
#   v1 은 ±12(몸 가운데)라 뿌리(−70 · +60)에서 발까지 다리가 X 자로 최대 65° 기울어 무릎이 많이 꺾였음
legs = {'hip': [0, round((LEG_HY - HIP[1]) * 2, 1)], 'thighFirst': True,
        'near': {'x': round(float(LJ['near']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['near']['h'][0] - HIP[0]) * 2, 1), 'runX': round(float(LJ['near']['h'][0] - HIP[0]) * 2, 1), 'shade': 0,
                 'thigh': ln('near', 'h', 'k'), 'shin': ln('near', 'k', 'a'), 'stand': stand('near', 'N')},
        'far': {'x': round(float(LJ['far']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['far']['h'][0] - HIP[0]) * 2, 1), 'runX': round(float(LJ['far']['h'][0] - HIP[0]) * 2, 1), 'shade': 0.12,
                'thigh': ln('far', 'h', 'k'), 'shin': ln('far', 'k', 'a'), 'stand': stand('far', 'F')}}
print('  legs near', legs['near']['thigh'], legs['near']['shin'], 'far', legs['far']['thigh'], legs['far']['shin'])

# ---------------- 달리기 다리 — 시트 21·22(허벅지) + 23·24(정강이 + 부츠, 옆모습 앞코 오른쪽) + 25(무릎 쇠판) ----------------
RS = 2.0                                                         # 시트 = 원화 배율 → 리그 ×2
RUN_TH = float(os.environ.get('RUN_TH', 0))                     # 달리는 허벅지 길이(리그) 시험용 — 없으면 시트 허벅지 길이 × RS (v1.1)
for sd, bn in (('near', 'bootN'), ('far', 'bootF')):
    _b = sheet_rgba(bn); _m = _b[..., 3] > 128; _ys = np.nonzero(_m.any(1))[0]
    # 시트 정강이+부츠: 무릎 = 위 끝 가운데, 발목 = 쇠 앞코 위(부츠 목) — 아래에서 30% 높이의 뒤꿈치 쪽 가운데
    _top = np.nonzero(_m[_ys.min() + 3])[0]; KNEE_S = np.array([float(_top.mean()), float(_ys.min() + 3)])
    _ay = int(_ys.max() - (_ys.max() - _ys.min()) * .36); _ar = np.nonzero(_m[_ay])[0]; ANK_S = np.array([float(_ar.min() + (_ar.max() - _ar.min()) * .4), float(_ay)])
    _Y, _X = np.mgrid[0:_b.shape[0], 0:_b.shape[1]]
    _sh = _b.copy(); _sh[..., 3] = np.where(_Y < ANK_S[1] + 6, _b[..., 3], 0); Image.fromarray(_sh).save(os.path.join(OUT, 'parts', 'rshin' + sd[0].upper() + '.png'))
    def_parts['rshin' + sd[0].upper()] = dict(src=f'parts/rshin{sd[0].upper()}.png', pivot=[0, 0], scale=1.0)
    _ft = _b.copy(); _ft[..., 3] = np.where(_Y > ANK_S[1] - 8, _b[..., 3], 0); Image.fromarray(_ft).save(os.path.join(OUT, 'parts', 'rboot' + sd[0].upper() + '.png'))
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
for n in ['thighN', 'thighF']:   # 시트 허벅지: 위 = 튜닉 자락 밑(곧게 잘림), 아래 = 둥근 무릎
    a = sheet_rgba(n); m = a[..., 3] > 128
    _ys = np.nonzero(m.any(1))[0]; y0_, y1_ = _ys.min(), _ys.max(); ty, tx = np.nonzero(m[y0_:y0_ + 6]); top = [float(tx.mean()), float(ty.mean() + y0_)]
    kr = int(y0_ + (y1_ - y0_) * .80); kx = np.nonzero(m[kr])[0]; kn = [float(kx.mean()), float(kr)]
    Image.fromarray(a).save(os.path.join(OUT, 'parts', 'r' + n + '.png')); def_parts['r' + n] = dict(src=f'parts/r{n}.png', pivot=[0, 0], scale=1.0)
    rseg[n] = {'part': 'r' + n, 'a': [round(top[0], 1), round(top[1], 1)], 'b': [round(kn[0], 1), round(kn[1], 1)], 'w': 1.0}
legs['thighImg'] = rseg['thighF']; legs['near']['thighImg'] = rseg['thighN']; legs['far']['thighImg'] = rseg['thighF']
# v1.1: 달리는 허벅지 = 시트 그림 그대로의 배율(RS) 길이 — v1 은 80(시트 25px 를 ×3.2 로 늘림)이라 다리 전체 152.7 > 엉덩이 높이 128 → 서 있는 다리도 무릎이 꺾였음
#   지금 허벅지 50.2 + 정강이 72.7 = 122.9 ≈ 엉덩이(다리 뿌리)~발목 높이 128 − hipBase 4 → 디딘 다리가 거의 곧음(펴짐 .95~1)
_tA, _tB = np.array(rseg['thighF']['a']), np.array(rseg['thighF']['b'])
legs['thigh'] = RUN_TH if 'RUN_TH' in os.environ else round(float(np.linalg.norm(_tB - _tA)) * RS, 1)
print('  run legs thigh', legs['thigh'], 'shin', RUN_SH, '· 무릎', KNEE_F.tolist(), '발목', ANK_F.tolist())
legs['shinImg'] = {'part': 'rshinF', 'a': KNEE_F.tolist(), 'b': ANK_F.tolist(), 'w': 1.0}
legs['near']['shinImg'] = {'part': 'rshinN', 'a': KNEE_Nn.tolist(), 'b': ANK_Nn.tolist(), 'w': 1.0}
legs['boot'] = {'part': 'rbootF', 'sole': sole_sheet(FT_F, ANK_F), 'ankleRange': [-0.35, 0.6], 'runLock': 0.0}   # runLock 0(엔진 opt-in): 달리기 다리 그림(시트 정강이·부츠)이면 발목 고정 — 부츠가 정강이와 한 줄, 발 구름 없음. DHL 10-21 12:35 '뛸 때 발이 2조각으로 나눠지면 이상 · 발 구르는 것 없이 뛰어도 좋으니 조각을 쪼개지 말아줘요'(서 있는 원화 다리 그림은 원래 범위)
legs['near']['boot'] = {'part': 'rbootN', 'sole': sole_sheet(FT_N, ANK_Nn), 'ankleRange': [-0.35, 0.6]}
# 무릎 쇠판(시트 25칸): 무릎 위 — 허벅지·정강이 가운데 각도(엔진 kneeImg)
for n, sd in (('kneeN', 'near'), ('kneeF', 'far')):
    a = sheet_rgba(n); m = a[..., 3] > 128; ys_, xs_ = np.nonzero(m)
    Image.fromarray(a).save(os.path.join(OUT, 'parts', n + '.png')); def_parts[n] = dict(src=f'parts/{n}.png', pivot=[round(float(xs_.mean()), 1), round(float(ys_.mean()), 1)], scale=RS)
legs['near']['kneeImg'] = {'part': 'kneeN'}; legs['far']['kneeImg'] = {'part': 'kneeF'}; legs['kneeImg'] = {'part': 'kneeF'}

# ---------------- 표정·깜빡임: 시트 3~10칸(2칸 머리와 같은 그림 자리) → 머리 맞춤(MH)으로 원화 얼굴에 (22 와 같은 방법) ----------------
_wfs = {n: cv2.warpAffine(sheet_rgba(n), MH, (512, 512), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)).astype(np.int16)
        for n in ['face_neutral', 'face_happy', 'face_angry', 'face_focus', 'face_shout', 'face_effort', 'blink_half', 'blink_closed']}
_dif = np.zeros((512, 512), bool)
for n, w_ in _wfs.items():
    if n != 'face_neutral': _dif |= (np.abs(w_[..., :3] - _wfs['face_neutral'][..., :3]).sum(-1) > 60) & (w_[..., 3] > 200)
_box = np.zeros((512, 512), bool); _box[200:275, 255:345] = True   # 눈·눈썹·안경(가리개 위)
_dif &= _box; _dif = ndimage.binary_opening(_dif, np.ones((2, 2)))
FACE = ndimage.binary_fill_holes(cv2.morphologyEx(dil(_dif, 4).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0) & own['head'] & _box
_fm = np.clip(cv2.GaussianBlur(cv2.erode(FACE.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (5, 5), 1.0) * 1.15, 0, 1)
_omean = RA[..., :3][SKIN & FACE].mean(0) if (SKIN & FACE).sum() > 20 else RA[..., :3][SKIN & own['head']].mean(0)
hb = np.array(Image.open(A('head'))); hx0, hy0 = int(O_['head'][0]), int(O_['head'][1]); hh, hw = hb.shape[:2]
def face_patch(cellname, out):
    a = sheet_rgba(cellname)
    wf = cv2.warpAffine(a, MH, (512, 512), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0))
    h2 = cv2.cvtColor(wf[..., :3], cv2.COLOR_RGB2HSV); s3 = (h2[..., 0] >= 5) & (h2[..., 0] <= 22) & (h2[..., 1] > 90) & (h2[..., 2] > 140) & (wf[..., 3] > 200)
    if (s3 & FACE).sum() > 50: d = _omean - wf[..., :3][s3 & FACE].mean(0); wf = wf.copy(); wf[..., :3][s3] = np.clip(wf[..., :3][s3].astype(np.float32) + d, 0, 255).astype(np.uint8)
    al = _fm * (wf[..., 3] / 255.0); o2 = RA.astype(np.float32).copy(); o2[..., :3] = o2[..., :3] * (1 - al[..., None]) + wf[..., :3] * al[..., None]
    fc = o2.astype(np.uint8)[hy0:hy0 + hh, hx0:hx0 + hw].copy(); fc[..., 3] = np.where(FACE[hy0:hy0 + hh, hx0:hx0 + hw], hb[..., 3], 0)
    Image.fromarray(fc).save(os.path.join(W, out + '.png'))
FACE_N = ['neutral', 'happy', 'angry', 'focus', 'shout', 'effort']
for n in FACE_N: face_patch('face_' + n, 'face_' + n); part('face_' + n, os.path.join(W, 'face_' + n + '.png'), def_parts['head']['pivot'])
for n in ['half', 'closed']: face_patch('blink_' + n, 'blink_' + n); part('blink_' + n, os.path.join(W, 'blink_' + n + '.png'), def_parts['head']['pivot'])
FACES = {n: 'face_' + n for n in FACE_N if n != 'neutral'}; FACES['grimace'] = 'face_effort'; FACES['surprised'] = 'face_shout'
print('  face px', int(FACE.sum()))

# ---------------- 내려찍기: 12 네온 v1.4 한 손(attack/smash7.py — 22 smash22.py 와 같은 시간표·구조, 키는 루시아 몸·도끼로) ----------------
exec(open(os.path.join(HERE, 'attack', 'smash7.py')).read())

# ---------------- 그리는 순서 (뒤 → 앞) ----------------
#   12 v1.4 규칙(먼 팔·도끼·쥔 주먹 = 다리·골반·머리 뒤) + 루시아 원화: 먼 소매가 상체(튜닉) 앞
#   v1.1 (DHL 10-20 21:44 '다리 레이어가 옷 뒤로'): 다리 = 상체(튜닉)·골반(허리띠 + 치맛단) 뒤 — 달릴 때 무릎이 튜닉 위로 올라와 보이던 것.
#     팔뚝·도끼·쥔 주먹은 다리보다 더 뒤(12 규칙), 윗팔 소매만 상체 앞(원화). 대기 원화 겹침 차이 = v1 과 같은 762 px (tools/ordercheck7.py)
#   방패·가까운 주먹 = 맨 앞, 먼 어깨 보호대 = 머리 앞·방패 뒤
draw = ['foreF', 'weapon', 'fistF', 'legFar', 'legNear', 'torso', 'armF', 'armFs', 'hips', 'head', 'pauldronF', 'armU', 'armL', 'shield', 'fistN']
_top = 170
rig = {'name': 'lucia-rust', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': def_parts, 'bones': bones, 'legs': legs, 'draw': draw, 'hidden': [], 'faces': FACES, 'blinkFaces': {'half': 'blink_half', 'closed': 'blink_closed'},
       'metrics': {'bodyHeight': round(2 * (O[1] - _top), 1), 'note': f'리그 단위; 투구 둥근 꼭대기(y{_top} — 볏 빼고)~발바닥({O[1]:.0f}) ×2, 무기 제외'},
       'armPhase': 0,
       # v1.1 걸음(DHL 21:44 '너무 구부러짐'): 팔로메(9·29)·카르덴(6) 드워프 종종걸음 쪽 — 작은 보폭·낮은 무릎·뒤꿈치 거의 안 참·골반 덜 내림·발목 덜 꺾음(긴 쇠 앞코 부츠가 꺾이면 발목이 들려 무릎이 접힘)
       #   v1: 보폭 60+.18v · 무릎 .85 · 뒤꿈치 .7 · 골반 14 · 출렁 14 → 무릎 굽힘 최대 163°(평균 50~63) / v1.1: 최대 ~83°(그네 다리), 디딘 다리 5~37° (tools/legprobe7.py, 게임 걸음 2.22/s)
       'gait': {'stance': 0.26, 'strideBase': 26, 'strideK': 0.08, 'hipBase': 4, 'bob': 4, 'lean': 0.12, 'waddle': 0.03, 'headBob': 3, 'kneeLift': 0.2, 'heelKick': 0.05, 'dropCap': 8,
                'swingReach': 0.05, 'swingAng': 0, 'landAng': -0.04, 'angK': 0.12, 'strideFlex': [0.75, 1.15], 'headRun': 0.05, 'elbowRun': 0, 'armSwing': 0.5, 'armBias': 0.0},
       'carrySwing': 0.35, 'wristRange': 0.3,
       'follow': [{'bone': 'pauldronF', 'src': 'armF', 'k': 0.3}, {'bone': 'shield', 'src': 'torso', 'k': -0.6}],   # 방패 = 상체 숙임의 60% 만큼 되돌려 세움(타격 때 상체 17° 숙이면 방패가 머리 쪽으로 넘어갔음 21:5x)
       'bounce': [{'bone': 'shield', 'stiff': 170, 'damp': 9, 'y': 0.25, 'rot': 0.004, 'max': 8}],
       'ui': {'attack': 'smash', 'touch': 'hop'},
       'gameRef': {'refOrigin': [round(float(O[0] - (HIP[0] - 254.4)), 1), float(O[1])], 'refScale': 2.0, 'refLift': 0,
                   'note': '게임 그림 char_0007.png(512) = 원화(md5 같음, source/ref512.png). x = 도감 칸(fitArt 중심 254.4 — index.html measureBox 를 파이썬 같은 계산, 22·12 값 282.4·269.4 로 확인)에서 골반(hip x 280)이 가운데 (2·12·22 와 같은 규칙)'},
       'cutHold': 0.34,   # 스킬 컷인 = 도끼를 앞에 세운 채 내려치는 중(10-21 06:16 DHL '추천으로' — .32 는 머리 위 도끼·방패가 칸 위로 17px 잘림, .34 는 PC·폰 모두 칸 안 · tools/cutpair7.py HOLD7)
       'note': '7 러스트 루시아 v1.1 (2026-10-20 — 원화 조각 + 시트 표정·자루·쥔 손·달리기 다리·무릎 쇠판, 12 네온 v1.4 한 손 내려찍기·그리는 순서, 방패 = 가까운 어깨에 붙음 · v1.1 다리 = 옷 뒤 + 드워프 종종걸음)'}
rig.update(SMASH)
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(os.path.join(OUT, 'parts'))): _h.update(fn.encode()); _h.update(open(os.path.join(OUT, 'parts', fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_lucia7.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['lucia-rust']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(def_parts), 'parts, version', rig['version'], 'bodyHeight', rig['metrics']['bodyHeight'])
