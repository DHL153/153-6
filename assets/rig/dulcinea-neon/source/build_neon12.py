"""12 네온 둘시네 리그 조립 — 시험판 p2 (2026-10-20 — p1 원화 조각만(DHL 08:26 그동안 준비) → p2 시트 1장(DHL 08:35), 08:43 기록) 표정·망치·쥔 손·달리기 다리)
구조 = 2 러스트 둘시네 v6.4(build_dulcinea.py) 그대로: 엔진 기본 길(자유 팔 armU→armL = 가까운 팔·주먹, 무기 팔 armF→foreF→fistF→weapon = 먼 팔·망치)
입력: ref512.png(새 원화 = 게임 char_0012) · polys12.json → seg12.py(POLYS) 부품 칸 · (시트 오면) cut/
출력: ../rig.json, ../rig.def.js, ../parts/*.png      실행: cd source && python3 -I build_neon12.py
시험판에서 빠진 것(시트 기다림): 표정·깜빡임(2~10칸), 달리기 다리(22~27칸 — 지금은 원화 다리를 그대로 돌림), 상체·골반 가려진 곳(12·14칸 — 지금은 inpaint),
  망치 쇠 머리 머리카락 밑 모서리(11칸), 휘두를 때 먼 손(21칸 — 지금은 러스트 gFh 그림을 자리만 빌림, 색 다름). 게임·편집 툴에는 아직 안 넣음.
원칙: 대기 = 원화(보이는 곳은 원화를 오림), 가려진 곳만 시트·inpaint. 손 조각 뒤집기 금지. 팔다리 길이 고정. 좌표: 원화 512px 로 적고 ×2 = 리그 단위."""
import json, math, os, shutil, hashlib, sys, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work'); OUT = os.path.join(HERE, '..')
RUST = os.path.abspath(os.path.join(HERE, '..', '..', 'dulcinea-rust', 'source'))
os.makedirs(os.path.join(OUT, 'parts'), exist_ok=True); os.makedirs(W, exist_ok=True)
for f in os.listdir(os.path.join(OUT, 'parts')): os.remove(os.path.join(OUT, 'parts', f))
img = lambda p: np.array(Image.open(p).convert('RGBA'))
RA = img(os.path.join(HERE, 'ref512.png')); AL = RA[..., 3] > 8
def pmask(pts):
    m = Image.new('L', (512, 512), 0); ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255); return np.array(m) > 0
def dil(m, r): return cv2.dilate(m.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0
def ero(m, r): return cv2.erode(m.astype(np.uint8), np.ones((2 * r + 1, 2 * r + 1), np.uint8)) > 0
yy, xx = np.mgrid[0:512, 0:512].astype(np.float32)

# ---------------- 원화 관절 (512 px, 10-20 08:43 기록 — 새 원화에서 잼) ----------------
O = np.array([221.0, 486.0])                                     # 뿌리: 두 발바닥 가운데(가까운 104~163 · 먼 277~342) 땅
HIP = np.array([223.0, 332.0]); NECK = np.array([240.0, 262.0])   # 골반(허리띠 주황 버클) · 목(턱 밑 = 머리 회전 중심)
SH_N, EL_N, WR_N = np.array([160.0, 271.0]), np.array([138.0, 302.0]), np.array([121.0, 333.0])   # 가까운 팔: 어깨(어깨 보호대 가운데) · 팔꿈치(살 윗팔 아래 끝) · 손목(토시 끝 = 장갑 시작)
FIST_N = np.array([118.0, 352.0])
HU = np.array([0.6, -0.8]); HU /= np.linalg.norm(HU)              # 망치 자루 방향(쥔 손 → 쇠 머리), 세로에서 오른쪽 37° — 주먹 위·아래 자루 가운데 선(x = 313 − .75(y − 296))
G = np.array([295.2, 319.8])                                      # 쥔 점: 자루 축 위, 먼 주먹이 덮는 축 구간 가운데
SH_F, EL_F, WR_F = np.array([250.0, 275.0]), np.array([240.0, 311.0]), np.array([284.0, 318.0])   # 먼 팔: 어깨·팔꿈치 = 상체 뒤(안 보임) · 손목 = 흰 손목 보호대 끝(장갑 시작)
# 무릎 = 다리 축(엉덩이→발목 선)에서 앞(+x)으로 약 9px — 원화 다리가 거의 곧아서(축에서 2px) 숨쉬기로 골반이 1~2px 내려가도 무릎이 5~8px 튀어나왔음(08:43 대기 비교).
#   대기에선 그 자리 그대로(그림 안 돌아감), 조금 굽혀 둔 무릎이라 골반이 움직여도 무릎이 덜 움직임(러스트 무릎은 축에서 11px)
LJ = {'near': dict(h=np.array([182.0, 345]), k=np.array([179.0, 385]), a=np.array([150.0, 452])),
      'far': dict(h=np.array([242.0, 345]), k=np.array([269.0, 392]), a=np.array([284.0, 452]))}
LEG_HY = 345.0
print('  arm N', round(float(np.linalg.norm(EL_N - SH_N) + np.linalg.norm(FIST_N - EL_N)), 1), 'arm F(→G)', round(float(np.linalg.norm(EL_F - SH_F) + np.linalg.norm(G - EL_F)), 1))

# ---------------- 원화 칸 나누기 (seg12.py POLYS — 씨앗 다각형 + 외곽선 watershed) ----------------
LBL = os.path.join(W, 'labels12.npy')
if not os.path.exists(LBL) or os.path.getmtime(LBL) < max(os.path.getmtime(os.path.join(HERE, f)) for f in ('polys12.json', 'ref512.png', 'seg12.py')):
    subprocess.run([sys.executable, '-I', os.path.join(HERE, 'seg12.py'), os.path.join(HERE, 'ref512.png')], env=dict(os.environ, POLYS='polys12.json'), check=True, stdout=subprocess.DEVNULL)
    shutil.copy(os.path.join(W, 'labels.npy'), LBL)
SL = np.load(LBL)
SEGN = ['head', 'hammer', 'fistF', 'foreF', 'padN', 'upperN', 'foreN', 'torso', 'hips', 'thighN', 'thighF', 'bootN', 'bootF']
RIGN = {'padN': 'pauldron', 'upperN': 'armU', 'foreN': 'armL'}            # seg 이름 → 리그 이름(러스트와 같은 뼈 이름)
own = {RIGN.get(n, n): (SL == i + 1) & AL for i, n in enumerate(SEGN)}
# (러스트 06:00 와 같음) 망치 = 머리 뒤: 망치 칸 중 머리에 붙은 떨어진 조각 → 머리
_hc_n, _hc_l, _hc_s, _ = cv2.connectedComponentsWithStats(own['hammer'].astype(np.uint8), 8)
_big = 1 + int(np.argmax(_hc_s[1:, cv2.CC_STAT_AREA])); _to_head = np.zeros((512, 512), bool)
for _i in range(1, _hc_n):
    if _i != _big and (dil(own['head'], 2) & (_hc_l == _i)).any(): _to_head |= _hc_l == _i
own['head'] |= _to_head; own['hammer'] &= ~_to_head
print('  labels', {n: int(m.sum()) for n, m in own.items()}, '망치→머리', int(_to_head.sum()))

# ---------------- 조각 오리기: 주인 칸 + 앞 조각 밑 3px 겹침 + 가려진 곳 메우기 ----------------
DRAW_ART = ['armF', 'thighF', 'bootF', 'thighN', 'bootN', 'hips', 'foreF', 'torso', 'hammer', 'head', 'fistF', 'armU', 'pauldron', 'armL']
def above(n):
    i = DRAW_ART.index(n); return np.logical_or.reduce([own[m] for m in DRAW_ART[i + 1:] if m in own] + [np.zeros((512, 512), bool)])
def inpaint_into(a, region, src_ok, r=5):
    rgb = np.ascontiguousarray(a[..., :3].copy()); d, (iy, ix) = ndimage.distance_transform_edt(~src_ok, return_indices=True)
    rgb[~src_ok] = rgb[iy[~src_ok], ix[~src_ok]]
    out = cv2.inpaint(rgb, region.astype(np.uint8) * 255, r, cv2.INPAINT_TELEA); a = a.copy(); a[..., :3][region] = out[region]; a[..., 3][region] = 255; return a
def outline_cut(a, cutmask, w=2.4):
    A = a[..., 3] > 128; d = ndimage.distance_transform_edt(A); e = A & dil(cutmask, 1) & (d <= w + .2)
    k = np.clip(w + .4 - d, 0, 1)[e][:, None]; a = a.copy(); a[..., :3][e] = (a[..., :3][e] * (1 - k) + np.array([28, 26, 30]) * k).astype(np.uint8); return a
def save_crop(a, name):
    ys, xs = np.nonzero(a[..., 3] > 0); x0, y0 = xs.min() - 2, ys.min() - 2
    Image.fromarray(a[y0:ys.max() + 3, x0:xs.max() + 3]).save(os.path.join(W, name + 'Art.png')); return np.array([x0, y0], float)
MOVING = own['armL'] | own['armU'] | own['pauldron'] | own['foreF'] | own['fistF'] | own['hammer']
ART = {}
for n in DRAW_ART:
    if n == 'armF': continue
    _ab = dil(own[n], 3) & above(n) & AL
    if n in ('torso', 'hips', 'thighN', 'thighF'): _ab &= ~MOVING          # 움직이는 팔·주먹·망치 밑 겹침은 안 가져옴(외곽선이 떠 보임) — 그 밑은 메우기
    if n == 'hammer': _ab &= ~own['head']                                 # 머리 밑 겹침은 머리카락 — 안 가져옴
    if n == 'foreF': _ab &= ~(own['torso'] | own['hips'])                # 먼 팔뚝은 상체·골반 밑 겹침을 안 가져옴 — 팔이 몸에서 떨어지면 크롭 탑 조각이 팔뚝에 붙어 다녔음
    m = own[n] | _ab; a = RA.copy(); a[..., 3] = np.where(m, RA[..., 3], 0); ART[n] = a
_hsv = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV)
SKIN = (_hsv[..., 0] >= 5) & (_hsv[..., 0] <= 22) & (_hsv[..., 1] > 90) & (_hsv[..., 2] > 140) & (RA[..., 3] > 200)
SKINC = np.median(RA[..., :3][SKIN & (own['torso'] | own['armU'] | own['foreF'])], 0).astype(np.uint8)
# 상체: 어깨 보호대·윗팔·팔·먼 팔뚝·주먹·턱 밑 메움(시트 12칸 오면 그것으로) — 상체 테두리 다각형 안만
TORSO_HULL = pmask([[166, 262], [205, 256], [246, 260], [264, 272], [266, 300], [258, 322], [180, 324], [168, 300]])
_reg = TORSO_HULL & (own['pauldron'] | own['armU'] | own['armL'] | (own['head'] & dil(own['torso'], 8))) & ~(ART['torso'][..., 3] > 200)   # 먼 팔뚝·주먹 자리는 상체 밖(허리 옆) — 메우면 상체 뒤 팔뚝을 덮음(08:43 대기 비교에서 찾음)
ART['torso'] = outline_cut(inpaint_into(ART['torso'], _reg, own['torso'] & (RA[..., 3] > 200) & ~dil(~AL, 2)), _reg)
print('  torso fill', int(_reg.sum()))
ART['torso'] = outline_cut(ART['torso'], own['foreF'] | own['fistF'])   # 먼 팔뚝이 덮던 상체 오른쪽 끝(허리 옆): 팔이 떠나면 외곽선 없는 잘린 면 → 원화 같은 외곽선
# 골반: 망치 자루 끝·먼 주먹 밑(시트 14칸 오면 그것으로)
HIPS_HULL = pmask([[158, 316], [255, 316], [259, 330], [259, 353], [240, 358], [214, 366], [204, 358], [150, 362], [152, 330]])   # 오른쪽 = 반바지 옆 회색 판 끝(x 259) — 넘으면 자루 끝 밑 메움이 반바지 밖으로 삐져 찢긴 모양(08:5x 공격 확대)
_reg = HIPS_HULL & (own['hammer'] | own['fistF'] | own['armL']) & ~(ART['hips'][..., 3] > 200)
ART['hips'] = outline_cut(inpaint_into(ART['hips'], _reg, own['hips'] & (RA[..., 3] > 200) & ~dil(~AL, 2)), _reg & dil(~HIPS_HULL, 1))
print('  hips fill', int(_reg.sum()))
# 망치 자루: 먼 주먹 밑 — 주먹 위 자루(홈 손잡이)를 축 따라 44px 내려 채움
t_ax = (xx - G[0]) * HU[0] + (yy - G[1]) * HU[1]; n_ax = (xx - G[0]) * -HU[1] + (yy - G[1]) * HU[0]
_hreg = (np.abs(n_ax) <= 11) & (t_ax > -30) & (t_ax < 23) & ~(ART['hammer'][..., 3] > 200)
_mv = cv2.warpAffine(RA, np.float32([[1, 0, -HU[0] * 44], [0, 1, -HU[1] * 44]]), (512, 512), flags=cv2.INTER_LINEAR)   # (+t 픽셀을 −t 쪽으로)
ART['hammer'][_hreg] = _mv[_hreg]
print('  shaft fill', int(_hreg.sum()))
# 망치 쇠 머리 중 머리카락 밑(원화에선 앞머리가 덮어 그림 없음): 시트 11칸 망치(reg12 SIFT 닮음, ×1.00)를 원화 색으로 맞춰 채움 — 휘두르면 드러남
if not os.path.exists(os.path.join(HERE, 'pieces', 'index.json')):   # 시트 조각(pieces/ — git 에 안 올림)은 시트에서 다시 자름
    subprocess.run([sys.executable, '-I', os.path.join(HERE, 'cut12.py'), os.path.join(HERE, 'sheets', 'sheet1_v1.png')], check=True, stdout=subprocess.DEVNULL)
sys.path.insert(0, HERE); import reg12
PC = os.path.join(HERE, 'pieces')
def sheet_rgba(n):   # 시트 조각 + 자홍 테두리 빼기
    a = np.array(Image.open(os.path.join(PC, n + '.png')).convert('RGBA')).astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None)
    a[..., 0] -= m; a[..., 2] -= m; return np.clip(a, 0, 255).astype(np.uint8)
_rh = reg12.match('hammer', reg12.REG['hammer']); MHm = np.array(_rh['M'])
_hw = cv2.warpAffine(sheet_rgba('hammer'), MHm, (512, 512), flags=cv2.INTER_LINEAR)
_ov = (_hw[..., 3] > 200) & (ART['hammer'][..., 3] > 200) & (t_ax > 60) & ~dil(own['head'], 3)
_mu_s, _sd_s = _hw[..., :3][_ov].astype(float).mean(0), _hw[..., :3][_ov].astype(float).std(0) + 1
_mu_a, _sd_a = RA[..., :3][_ov].astype(float).mean(0), RA[..., :3][_ov].astype(float).std(0) + 1
_fillH = (_hw[..., 3] > 128) & ~(ART['hammer'][..., 3] > 200) & dil(own['head'], 1) & (t_ax > 60)
ART['hammer'][..., :3][_fillH] = np.clip((_hw[..., :3][_fillH] - _mu_s) / _sd_s * _sd_a + _mu_a, 0, 255).astype(np.uint8); ART['hammer'][..., 3][_fillH] = _hw[..., 3][_fillH]
print('  hammer sheet fill(머리카락 밑)', int(_fillH.sum()), 'px · sheet scale', _rh['scale'], 'rot', _rh['rot'], 'inl', _rh['inl'])
# 먼 팔뚝: 상체 밑으로 팔꿈치까지 살색 이어 그림(공격에서 팔이 돌면 드러남)
_ext = np.zeros((512, 512), np.uint8); cv2.line(_ext, tuple(int(v) for v in EL_F - (WR_F - EL_F) / np.linalg.norm(WR_F - EL_F) * 4), (252, 314), 1, 20)   # 굵기 = 원화 먼 팔뚝 살 폭(약 20, 외곽선 포함 24)
cv2.circle(_ext, tuple(int(round(v)) for v in EL_F - (WR_F - EL_F) / np.linalg.norm(WR_F - EL_F) * 4), 10, 1, -1)   # 팔꿈치 끝 둥글게(네모 끝이 휘두를 때 상체 옆에 네모 덩어리로 보였음)
_ext = _ext.astype(bool) & ~(ART['foreF'][..., 3] > 200)
ART['foreF'] = inpaint_into(ART['foreF'], _ext, own['foreF'] & SKIN)
ART['foreF'] = outline_cut(ART['foreF'], dil(_ext, 1) | own['torso'] | own['hips'])   # 이어 그린 살·몸에 붙어 있던 위아래 끝에도 원화 같은 외곽선
# 가까운 윗팔: 어깨 보호대 밑으로 어깨까지 살색(달릴 때 팔이 흔들리면 드러남) + 팔꿈치 둥근 끝(윗팔 아래·팔뚝 위)
_ext = np.zeros((512, 512), np.uint8); cv2.line(_ext, tuple(int(v) for v in SH_N), tuple(int(v) for v in EL_N), 1, 18)
_ext = _ext.astype(bool) & ~(ART['armU'][..., 3] > 200) & (own['pauldron'] | dil(own['armU'], 2)) & ~own['armL']
ART['armU'] = inpaint_into(ART['armU'], _ext, own['armU'] & SKIN)
_ax = (WR_N - SH_N) / np.linalg.norm(WR_N - SH_N); _R = 9.5
for n, sgn, R_, ringOn in [('armU', 1, _R, True)]:
    t_ = (xx - EL_N[0]) * _ax[0] + (yy - EL_N[1]) * _ax[1]; rr = np.hypot(xx - EL_N[0], yy - EL_N[1]); half = (rr <= R_) & (sgn * t_ >= -2)
    a = ART[n]; add = half & ~(a[..., 3] > 200); a[..., :3][add] = SKINC; a[..., 3][add] = 255
    if ringOn: ring = half & (rr > R_ - 2.2) & (sgn * t_ > 1) & add; a[..., :3][ring] = (28, 26, 30); a[..., 3][ring] = 255
    ART[n] = a
# 허벅지: 반바지 밑으로 엉덩이 관절까지 살색
for sd, n in [('near', 'thighN'), ('far', 'thighF')]:
    _e = np.zeros((512, 512), np.uint8); h, k = LJ[sd]['h'], LJ[sd]['k']; cv2.line(_e, tuple(int(v) for v in h), tuple(int(v) for v in (h + k) / 2), 1, 28)
    _e = _e.astype(bool) & ~(ART[n][..., 3] > 200) & own['hips'] & AL
    ART[n] = inpaint_into(ART[n], _e, own[n] & SKIN)
# 먼 허벅지·무릎 보호대: 자루 끝 마개 밑(08:5x 공격 확대에서 마개가 떠나면 무릎 보호대 위 끝이 외곽선 없이 하얗게 찢겨 보였음)
#   허벅지 = 마개 밑으로 허벅지 오른쪽 끝 선(x 271~276)까지 살색으로 잇고 외곽선, 무릎 보호대 = 메우지 않고 마개와 붙어 있던 위 끝에 외곽선만
THF_UNDER = pmask([[255, 357], [262, 357], [273, 366], [276, 373], [255, 376]])   # 위 끝 = 반바지 밑단(y 357), 오른쪽 위는 허벅지 둥근 선
_hz = THF_UNDER & own['hammer'] & ~(ART['thighF'][..., 3] > 200)
ART['thighF'] = outline_cut(inpaint_into(ART['thighF'], _hz, own['thighF'] & SKIN), own['hammer'] & ~THF_UNDER)
ART['bootF'] = outline_cut(ART['bootF'], own['hammer'] | own['thighF'])
O_ = {n: save_crop(a, n) for n, a in ART.items()}

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
part('head', A('head'), pc(NECK, O_['head']))
part('torso', A('torso'), pc(HIP, O_['torso'])); part('hips', A('hips'), pc(HIP, O_['hips']))
part('pauldron', A('pauldron'), pc(SH_N, O_['pauldron']))
part('armU', A('armU'), pc(SH_N, O_['armU']), elbow=pc(EL_N, O_['armU']))
part('armL', A('armL'), pc(EL_N, O_['armL']), fist=pc(FIST_N, O_['armL']))
part('foreF', A('foreF'), pc(EL_F, O_['foreF']), elbow=pc(EL_F, O_['foreF']))
part('fistF', A('fistF'), pc(WR_F, O_['fistF']))
# 망치: 자루가 그림 세로(쇠 머리 위)가 되게 원화 오림을 돌려 2배 해상도로 저장(엔진 _swordRigid 는 무기 그림 위쪽 = 자루 방향)
HTH = float(math.atan2(HU[0], -HU[1]))
_ha = Image.open(A('hammer')); _o = O_['hammer']; _S = 4
_big = _ha.resize((_ha.width * _S, _ha.height * _S), Image.LANCZOS); _pv = (G - _o) * _S
_pad = int(max(_big.size) * .8); _can = Image.new('RGBA', (_big.width + 2 * _pad, _big.height + 2 * _pad), (0, 0, 0, 0)); _can.paste(_big, (_pad, _pad)); _pv = _pv + _pad
_rot = _can.rotate(math.degrees(HTH), resample=Image.BICUBIC, center=tuple(_pv))
_bb = _rot.getbbox(); _rot = _rot.crop(_bb); _pv = _pv - np.array(_bb[:2]); _rot = _rot.resize((_rot.width // 2, _rot.height // 2), Image.LANCZOS); _pv = _pv / 2
_rot.save(os.path.join(W, 'hammerUp.png'))
# 쇠 머리 가운데(쥔 점에서 자루 따라): 원화 망치 칸 중 쇠 머리(t > 80) 무게중심의 축 위치
TIPU = float(t_ax[own['hammer'] & (t_ax > 80)].mean()); BUTT = float(-t_ax[own['hammer'] | (ART['hammer'][..., 3] > 128)].min())
print('  hammer 쥔 점→쇠 머리 가운데', round(TIPU, 1), '→마개', round(BUTT, 1), '(원화 px; 러스트 170 · 58)')
_WP = [round(float(_pv[0]), 1), round(float(_pv[1]), 1)]; _up = lambda d: [_WP[0], round(_WP[1] - d * 2, 1)]
# 쇠 머리 왼쪽 아래 모서리(원화에선 오른쪽 옆머리가 덮음): 시트로 채운 곳이 들쭉날쭉하고 외곽선이 끊김 → 모서리 다각형(왼쪽 선 → 아래 비스듬한 면)으로 다시 그림
#   (러스트 _fix_hammer 와 같은 생각, 10-20 08:43 기록) 좌표 = 세운 망치 그림(hammerUp, 원화 ×2) — 그림이 바뀌면 다시 잴 것
def _fix_hammer12(src, dst):
    a = np.array(Image.open(src).convert('RGBA')); n_, lb_, st_, _ = cv2.connectedComponentsWithStats((a[..., 3] > 10).astype(np.uint8), 8)
    a[..., 3] = np.where(lb_ == 1 + int(np.argmax(st_[1:, cv2.CC_STAT_AREA])), a[..., 3], 0)
    Q = [(6, 146), (6, 176), (38, 214), (62, 214), (62, 146)]
    qm = Image.new('L', (a.shape[1], a.shape[0]), 0); ImageDraw.Draw(qm).polygon(Q, fill=255); qm = np.array(qm) > 0
    box = np.zeros(qm.shape, bool); box[146:220, 0:62] = True
    lum = a[..., :3].astype(int).mean(-1)
    stray = np.zeros(qm.shape, bool); stray[146:171, 10:31] = True; stray &= qm
    a[..., :3][stray] = a[..., :3][np.nonzero(stray)[0], 33]; a[..., 3][stray] = 255   # 흰 판 아래 왼쪽(머리카락 끝·찌꺼기) → 같은 줄 판 색
    hole = qm & (a[..., 3] < 200); ok = qm & (a[..., 3] >= 200) & ~stray
    if hole.any():
        d, (iy, ix) = ndimage.distance_transform_edt(~ok, return_indices=True); a[..., :3][hole] = a[..., :3][iy[hole], ix[hole]]; a[..., 3][hole] = 255
    a[..., 3][box & ~qm] = 0
    ol = Image.new('L', (a.shape[1], a.shape[0]), 0); ImageDraw.Draw(ol).line([(7, 146), (7, 176), (38, 213), (66, 213)], fill=255, width=5); ol = np.array(ol) > 0
    a[..., :3][ol & box] = (5, 4, 4); a[..., 3][ol & box] = 255
    Image.fromarray(a).save(dst)
_fix_hammer12(os.path.join(W, 'hammerUp.png'), os.path.join(W, 'hammerUpA.png'))
for nm in ('weapon', 'weaponA'):
    part(nm, os.path.join(W, 'hammerUpA.png'), _WP, scale=1.0, tip=_up(TIPU), pommel=_up(-BUTT), tips=[[_WP[0] - 12, round(_WP[1] - TIPU * 2, 1)], [_WP[0] + 12, round(_WP[1] - TIPU * 2, 1)]], shaftDir=[0.0, -1.0])
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
bone('armU', 'torso', SH_N, HIP, 'armU'); bone('armL', 'armU', EL_N, SH_N, 'armL', rot=0.3)   # 엔진 대기 팔꿈치 처짐(−0.3)만큼 미리 반대로 → 대기 = 원화
bone('pauldron', 'torso', SH_N, HIP, 'pauldron')
bone('armF', 'torso', SH_F, HIP); bone('foreF', 'armF', EL_F, SH_F, 'foreF'); bone('fistF', 'foreF', WR_F, EL_F, 'fistF')
bone('weapon', 'fistF', G, WR_F, 'weapon', rot=HTH)
for n in ['cape', 'scarf', 'pouch', 'skirt', 'skirtB', 'pauldronF']: bones.append(dict(name=n, parent='torso', pos=[0, -200]))

# ---------------- 다리 — 서 있을 때 = 원화 다리. 달릴 때(시험판) = 같은 원화 다리 그림(시트 22~25 오면 옆모습 허벅지·부츠) ----------------
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
TH_R, SH_R = ln('far', 'h', 'k'), ln('far', 'k', 'a')
legs = {'hip': [0, round((LEG_HY - HIP[1]) * 2, 1)], 'thigh': TH_R, 'shin': SH_R, 'thighFirst': True,
        'thighImg': seg('thighF', O_['thighF'], LJ['far']['h'], LJ['far']['k']), 'shinImg': seg('bootFShin', O_['bootF'], LJ['far']['k'], LJ['far']['a']),
        'boot': {'part': 'bootFFoot', 'sole': sole('bootF', LJ['far']['a']), 'ankleRange': [-0.35, 0.45]},
        'near': {'x': round(float(LJ['near']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['near']['h'][0] - HIP[0]) * 2, 1), 'runX': -12, 'shade': 0,
                 'thigh': ln('near', 'h', 'k'), 'shin': ln('near', 'k', 'a'), 'thighImg': seg('thighN', O_['thighN'], LJ['near']['h'], LJ['near']['k']), 'stand': stand('near', 'N')},
        'far': {'x': round(float(LJ['far']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['far']['h'][0] - HIP[0]) * 2, 1), 'runX': 12, 'shade': 0.12,
                'thigh': ln('far', 'h', 'k'), 'shin': ln('far', 'k', 'a'), 'stand': stand('far', 'F')}}
print('  legs near', legs['near']['thigh'], legs['near']['shin'], 'far', legs['far']['thigh'], legs['far']['shin'])

# ---------------- 달리기 다리 — 시트 22~25칸(허벅지 + 옆모습 부츠, 앞코 오른쪽 · 무릎 보호대 그려져 있음)을 발목에서 나눔(러스트와 같은 방법) ----------------
def sheet_copy(src_a, dst):
    Image.fromarray(src_a).save(dst)
RS = 2.0                                                         # 시트 = 원화 배율(1번 칸 ×1.00, 부츠 높이 108 ≈ 원화 106) → 리그 ×2
_bf = sheet_rgba('bootF')
KNEE_S, ANK_S = np.array([45.0, 16.0]), np.array([37.0, 74.0])    # 시트 부츠: 무릎(무릎 보호대 가운데 위) · 발목(발등 시작 위)
_Y, _X = np.mgrid[0:_bf.shape[0], 0:_bf.shape[1]]
_sh = _bf.copy(); _sh[..., 3] = np.where(_Y < ANK_S[1] + 6, _bf[..., 3], 0); sheet_copy(_sh, os.path.join(OUT, 'parts', 'rshin.png')); def_parts['rshin'] = dict(src='parts/rshin.png', pivot=[0, 0], scale=1.0)
_ft = _bf.copy(); _ft[..., 3] = np.where(_Y > ANK_S[1] - 8, _bf[..., 3], 0); sheet_copy(_ft, os.path.join(OUT, 'parts', 'rboot.png')); def_parts['rboot'] = dict(src='parts/rboot.png', pivot=ANK_S.tolist(), scale=RS)
print('  run shin image len', round(float(np.linalg.norm(ANK_S - KNEE_S)), 1), 'want', round(SH_R / RS, 1))
def sole_sheet(a, ank):
    m = a[..., 3] > 128; ys = np.nonzero(m.any(1))[0]; yb = ys.max(); out = []
    for y in (yb - 6, yb - 3, yb):
        xs = np.nonzero(m[y])[0]; out += [[round(float(xs.min() - ank[0]), 1), round(float(y - ank[1]), 1)], [round(float(xs.max() - ank[0]), 1), round(float(y - ank[1]), 1)]]
    return out
rseg = {}
for n in ['thighN', 'thighF']:   # 시트 허벅지: 위 = 반바지 속(곧게 잘림), 아래 = 둥근 무릎
    a = sheet_rgba(n); m = a[..., 3] > 128
    _ys = np.nonzero(m.any(1))[0]; y0_, y1_ = _ys.min(), _ys.max(); ty, tx = np.nonzero(m[y0_:y0_ + 6]); top = [float(tx.mean()), float(ty.mean() + y0_)]
    kr = int(y0_ + (y1_ - y0_) * .80); kx = np.nonzero(m[kr])[0]; kn = [float(kx.mean()), float(kr)]
    il = math.hypot(kn[0] - top[0], kn[1] - top[1]); s_ = TH_R / il
    sheet_copy(a, os.path.join(OUT, 'parts', 'r' + n + '.png')); def_parts['r' + n] = dict(src=f'parts/r{n}.png', pivot=[0, 0], scale=1.0)
    rseg[n] = {'part': 'r' + n, 'a': [round(top[0], 1), round(top[1], 1)], 'b': [round(kn[0], 1), round(kn[1], 1)], 'w': round(RS / s_, 3)}   # 굵기 = 시트 그대로(×2)
legs['thighImg'] = rseg['thighF']; legs['near']['thighImg'] = rseg['thighN']; legs['far']['thighImg'] = rseg['thighF']
legs['shinImg'] = {'part': 'rshin', 'a': KNEE_S.tolist(), 'b': ANK_S.tolist(), 'w': 1.0}
legs['boot'] = {'part': 'rboot', 'sole': sole_sheet(_ft, ANK_S), 'ankleRange': [-0.35, 0.45], 'runLock': 0.0}   # runLock 0(엔진 opt-in): 달리기 다리 그림(시트 정강이·부츠)이면 발목 고정 — 부츠가 정강이와 한 줄, 발 구름 없음. DHL 10-21 12:35 '뛸 때 발이 2조각으로 나눠지면 이상 · 발 구르는 것 없이 뛰어도 좋으니 조각을 쪼개지 말아줘요'(서 있는 원화 다리 그림은 원래 범위)
print('  run thigh', {k: (v['w']) for k, v in rseg.items()})

# ---------------- 표정·깜빡임: 시트 3~10칸(2칸 머리와 같은 그림 자리) → 머리 맞춤(MH)으로 원화 얼굴에 ----------------
_rhd = reg12.match('head', reg12.REG['head']); MH = np.array(_rhd['M']); print('  head sheet→원화 scale', _rhd['scale'], 'rot', _rhd['rot'], 'inl', _rhd['inl'])
_fs = np.zeros((512, 512), bool); _fs[165:266, 195:305] = (SKIN & own['head'])[165:266, 195:305]
_lb, _n = ndimage.label(_fs); _sz = ndimage.sum(_fs, _lb, range(1, _n + 1)); FACE = ndimage.binary_fill_holes(_lb == (int(np.argmax(_sz)) + 1))
_fm = np.clip(cv2.GaussianBlur(cv2.erode(FACE.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (5, 5), 1.0) * 1.15, 0, 1)
_omean = RA[..., :3][SKIN & FACE].mean(0)
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

# ---------------- 내려찍기: 러스트 v6.4 한 손(attack/smash12.py — 러스트 smash_one.py 와 같은 키, 대기 자리만 네온) ----------------
exec(open(os.path.join(HERE, 'attack', 'smash12.py')).read())

# ---------------- 그리는 순서 (뒤 → 앞) — 러스트 v6.4 대기와 같음(망치 = 몸통·머리 뒤, 다리·골반 앞), 포니테일·천자락·허리띠 없음 ----------------
draw = ['armF', 'foreF', 'weapon', 'fistF', 'legFar', 'legNear', 'hips', 'torso', 'head', 'armU', 'pauldron', 'armL']   # (10-20 12:18 DHL ①달리기·대기 = 손·망치가 다리 뒤) 먼 팔뚝·망치·주먹 = 다리·골반·상체·머리 뒤 — 공격 drawA 와 같은 앞뒤. 대기에서 바뀌는 곳 = 자루 끝 마개 아래가 먼 허벅지 뒤(원화는 마개가 앞), 팔뚝∩골반·주먹∩상체는 원화 같은 픽셀이라 그대로   # (전) 먼 팔뚝 = 상체 뒤, 망치 = 다리·골반 앞, 주먹 맨 앞
rig = {'name': 'dulcinea-neon', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': def_parts, 'bones': bones, 'legs': legs, 'draw': draw, 'hidden': [], 'faces': FACES, 'blinkFaces': {'half': 'blink_half', 'closed': 'blink_closed'},
       'metrics': {'bodyHeight': round(2 * (O[1] - 119), 1), 'note': '리그 단위; 머리카락 위(y119)~발바닥(486) ×2, 무기 제외'},
       'armPhase': 0, 'gait': {'stance': 0.32, 'heelKick': 0.85, 'kneeLift': 0.95, 'strideBase': 70, 'strideK': 0.2, 'swingReach': 0.12, 'swingAng': 0.12, 'landAng': 0, 'hipBase': 6, 'bob': 16, 'lean': 0.2, 'strideFlex': [0.75, 1.5], 'headRun': 0.06, 'elbowRun': 1.2, 'armSwing': 0.55, 'armBias': 0.1},
       'carrySwing': 0.4, 'wristRange': 0.3, 'follow': [{'bone': 'pauldron', 'src': 'armU', 'k': 0.35}],
       'ui': {'attack': 'smash', 'touch': 'hop'},
       'gameRef': {'refOrigin': [round(float(O[0] - (HIP[0] - 269.5)), 1), float(O[1])], 'refScale': 2.0, 'refLift': 0,
                   'note': '게임 그림 char_0012.png(512) = 원화(md5 같음, source/ref512.png). x = 도감 칸(fitArt 중심 269.5, index.html measureBox 를 브라우저에서 같은 계산 — 2·9·29 값 248.9·253.1·251.5 로 맞는지 확인)에서 골반(hip x 223)이 가운데 (2 러스트 둘시네와 같은 규칙)'},
       'cutHold': 0.32,   # 10-20 13:53 스킬 컷인 = 망치를 머리 위로 높이 든 휘두름 시작(2 러스트와 같은 시각) — 외침 얼굴·망치 다 보임(.20~.34 후보 비교)
       'note': '12 네온 둘시네 v1.4 (2026-10-20 — 원화 조각 + 시트 표정·망치·쥔 손·달리기 다리, 러스트 v6.4 한 손 내려찍기 키를 네온 팔·몸 안 어깨에 맞춤, 손·망치 = 다리·머리 뒤). 13:53 게임 반영(REGISTRY 12).'}
rig.update(SMASH)
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(os.path.join(OUT, 'parts'))): _h.update(fn.encode()); _h.update(open(os.path.join(OUT, 'parts', fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_neon12.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['dulcinea-neon']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(def_parts), 'parts, version', rig['version'])
