"""22 스카이 둘시네 리그 조립 — 시험판 p1 (2026-10-20 15:3x — DHL 14:12 '모두 같은 모션으로': 12 네온 v1.4 동작·그리는 순서 + 2 러스트 포니테일 구조)
구조 = 12 네온 build_neon12.py 그대로(엔진 기본 길: 자유 팔 armU→armL = 가까운 팔·주먹, 무기 팔 armF→foreF→fistF→weapon = 먼 팔·망치) + 포니테일(pony 뼈, 러스트) + 먼 허리 천자락(flapF 뼈, 출렁임)
입력: ref512.png(새 원화 = 게임 char_0022, 프롬프트 0 14:35 합격) · polys22.json → seg22.py(POLYS) 부품 칸 · pieces/(시트 1장 25칸, 15:01 합격 — cut22.py)
출력: ../rig.json, ../rig.def.js, ../parts/*.png      실행: cd source && python3 -I build_sky22.py
12 와 다른 곳: ①먼 팔 = 접은 소매 끝(크림)·살 팔뚝 → 장갑(흰 보호대 없음) — 원화 먼 소매 위쪽 조각(어깨 옆)은 윗팔 뼈(armF) 그림 upF
  ②가까운 팔뚝(armL)은 접은 소매(armU) 뒤 — 팔뚝이 소매 속에서 나옴(원화 경계 외곽선 = 소매 것)
  ③망치 = 머리와 안 겹침(앞머리 밑 모서리 손질 없음) · 자루(먼 주먹 밑) = 시트 망치를 SIFT 로 원화 자리에 맞춰 채움(주먹 위 금 고리를 내려 붙이지 않음)
  ④천자락 = 원화에서 반바지·먼 다리·망치·주먹 뒤 → 그리는 순서 맨 뒤(대기 = 원화), 가려진 곳 메움 ⑤포니테일 = 머리 뒤, 망치 앞(러스트 06:10 규칙)
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

# ---------------- 원화 관절 (512 px, 10-20 15:1x 그리드 확대 review/grid_full·grid_mid·z_*.jpg 에서 잼) ----------------
O = np.array([238.0, 485.0])                                     # 뿌리: 두 발바닥 가운데(가까운 104~173 · 먼 299~376, y 479/475 줄) 땅
HIP = np.array([222.0, 333.0]); NECK = np.array([248.0, 256.0])   # 골반(허리띠 가운데) · 목(턱 밑 = 머리 회전 중심)
SH_N, EL_N, WR_N = np.array([172.0, 262.0]), np.array([155.0, 288.0]), np.array([139.0, 312.0])   # 가까운 팔: 어깨(어깨 판 밑) · 팔꿈치(접은 소매 끝 안) · 손목(장갑 입구)
FIST_N = np.array([135.0, 334.0])
HU = np.array([0.495, -0.869]); HU /= np.linalg.norm(HU)          # 망치 자루 방향(쥔 손 → 쇠 머리), 세로에서 오른쪽 30°
G = np.array([329.0, 314.0])                                      # 쥔 점: 자루 축 위, 먼 주먹이 덮는 축 구간 가운데
SH_F, EL_F, WR_F = np.array([266.0, 266.0]), np.array([274.2, 302.5]), np.array([305.0, 311.0])   # 먼 팔: 어깨·팔꿈치 = 조끼 뒤(안 보임, 12 네온과 같은 팔 길이 74.7·111.8 리그가 되게 팔꿈치를 풂) · 손목 = 살 → 장갑
LJ = {'near': dict(h=np.array([192.0, 347]), k=np.array([187.0, 386]), a=np.array([150.0, 452])),
      'far': dict(h=np.array([248.0, 347]), k=np.array([276.0, 387.5]), a=np.array([290.0, 452]))}   # 무릎 = 부츠 무릎 판 안(판이 허벅지 앞) · 엉덩이 y = LEG_HY(엔진은 두 다리 뿌리 높이 하나)
#   무릎을 다리 축(엉덩이→발목)에서 앞으로 9.5(가까운)·11.5(먼)px — 판 가운데(축에서 4~6px)로 두면 엉덩이→발목 거리 / 다리 길이 = .997·.993 > .99 라 엔진이 첫 프레임부터 골반을 1.6 리그 px 내림
#   (서 있는 다리는 다 펴지 않음 규칙) → 대기가 원화보다 아래로 밀리고 가까운 정강이가 돌았음(15:5x 대기 비교 IoU .966). 12 네온과 같은 비율(.985 · .979)로
LEG_HY = 347.0
PONY = np.array([176.0, 124.0])                                   # 포니테일 묶은 곳(리본 매듭)
FLAP_P = np.array([292.0, 338.0])                                 # 먼 허리 천자락 매단 곳(허리띠 오른쪽 끝)
print('  arm N', round(float(np.linalg.norm(EL_N - SH_N) + np.linalg.norm(FIST_N - EL_N)), 1), 'arm F(→G)', round(float(np.linalg.norm(EL_F - SH_F) + np.linalg.norm(G - EL_F)), 1),
      '(리그 L1 %.1f · L2 %.1f, 12 네온 74.7 · 111.8)' % (2 * np.linalg.norm(EL_F - SH_F), 2 * np.linalg.norm(G - EL_F)))

# ---------------- 원화 칸 나누기 (seg22.py POLYS — 씨앗 다각형 + 외곽선 watershed) ----------------
LBL = os.path.join(W, 'labels22.npy')
if not os.path.exists(LBL) or os.path.getmtime(LBL) < max(os.path.getmtime(os.path.join(HERE, f)) for f in ('polys22.json', 'ref512.png', 'seg22.py')):
    subprocess.run([sys.executable, '-I', os.path.join(HERE, 'seg22.py'), os.path.join(HERE, 'ref512.png')], env=dict(os.environ, POLYS='polys22.json'), check=True, stdout=subprocess.DEVNULL)
    shutil.copy(os.path.join(W, 'labels.npy'), LBL)
SL = np.load(LBL)
SEGN = ['head', 'pony', 'hammer', 'fistF', 'foreF', 'padN', 'upperN', 'foreN', 'torso', 'hips', 'flap', 'thighN', 'thighF', 'bootN', 'bootF']
RIGN = {'padN': 'pauldron', 'upperN': 'armU', 'foreN': 'armL', 'flap': 'flapF'}   # seg 이름 → 리그 이름(flap 은 엔진 rig.def.flap(코트 앞자락)과 이름이 겹쳐서 flapF)
own = {RIGN.get(n, n): (SL == i + 1) & AL for i, n in enumerate(SEGN)}
_hc_n, _hc_l, _hc_s, _ = cv2.connectedComponentsWithStats(own['hammer'].astype(np.uint8), 8)   # 망치 칸 중 머리에 붙은 떨어진 조각 → 머리(12 와 같음, 22 는 거의 없음)
_big = 1 + int(np.argmax(_hc_s[1:, cv2.CC_STAT_AREA])); _to_head = np.zeros((512, 512), bool)
for _i in range(1, _hc_n):
    if _i != _big and (dil(own['head'], 2) & (_hc_l == _i)).any(): _to_head |= _hc_l == _i
own['head'] |= _to_head; own['hammer'] &= ~_to_head
# 먼 소매 위쪽(어깨 옆 크림 소매·갈색 띠, y < 290.5 — 접은 소매 끝 윗선 위) = 윗팔 → armF 뼈 그림 upF (팔뚝과 같이 돌면 팔꿈치 위가 꺾여 보임)
own['upF'] = own['foreF'] & (yy < 290.5) & (xx < 300); own['foreF'] &= ~own['upF']
# 먼 팔뚝 칸에 붙은 조끼 오른쪽 가장자리(회청 띠 x 283~285 · 짙은 회색 선) → 상체로 — 공격에서 팔뚝과 같이 움직이면 소매 끝에 파란 세로줄이 붙어 다녔음(15:5x 확대)
_RAi = RA[..., :3].astype(int)
_vest = own['foreF'] & dil(own['torso'], 6) & (_RAi[..., 2] - _RAi[..., 0] >= -3) & (_RAi.mean(-1) > 40)
_vest |= own['foreF'] & dil(_vest, 2) & (LUM < 60)   # 띠 바깥 검은 외곽선도 조끼 것(팔이 떠나면 조끼 가장자리에 외곽선이 남게) — 소매 끝 왼쪽은 build 의 둥근 팔꿈치 끝 외곽선
_vest |= own['foreF'] & dil(own['torso'] | _vest, 3) & (LUM < 90)   # 조끼 쪽 3px 안 어두운 선 조각도(공격 팔꿈치 끝에 ㄴ자 검은 줄로 남았음)
own['torso'] |= _vest; own['foreF'] &= ~_vest
# 반바지 밑 허벅지 살(골반 칸에 들어가 있던 것) → 허벅지 칸: 달릴 때 골반과 같이 고정돼 반바지 왼쪽 아래에 살 초승달로 남았음(DHL 16:57 2·3 '표시한 살 부분')
_sk0 = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV); _skin0 = (_sk0[..., 0] >= 5) & (_sk0[..., 0] <= 22) & (_sk0[..., 1] > 90) & (_sk0[..., 2] > 140) & (RA[..., 3] > 200)
_hsk = own['hips'] & _skin0 & (yy > 340)
#   살 덩어리만(밝은 살 V ≥ 230 · 20px 이상) — 색 범위만 보면 허리띠 밑 금 D고리·주머니 고리·갈색 띠 끝(y 341~)도 '살'로 들어가 허벅지로 옮겨졌고,
#   달릴 때 허벅지가 그늘색 조각으로 바뀌니 골반 조각에 고리 아래가 빈칸으로 남았음(16:57 수정 확대 0.40)
_hn, _hl, _hs, _ = cv2.connectedComponentsWithStats(_hsk.astype(np.uint8), 8)
_hsk = np.isin(_hl, [i for i in range(1, _hn) if _hs[i, cv2.CC_STAT_AREA] >= 20 and RA[..., :3][_hl == i].max(-1).mean() >= 230])
_hsk = ndimage.binary_dilation(_hsk, iterations=1) & own['hips'] & (yy > 340) & ~(_sk0[..., 2] > 200) | _hsk   # 살 둘레 1px(외곽선 아닌 살 가장자리)
own['thighN'] |= _hsk & (xx < 232); own['thighF'] |= _hsk & (xx >= 232); own['hips'] &= ~_hsk
print('  hips 밑 허벅지 살 → 허벅지', int((_hsk & (xx < 232)).sum()), int((_hsk & (xx >= 232)).sum()))
print('  labels', {n: int(m.sum()) for n, m in own.items()}, '망치→머리', int(_to_head.sum()))

# ---------------- 조각 오리기: 주인 칸 + 앞 조각 밑 3px 겹침 + 가려진 곳 메우기 ----------------
#   원화 앞뒤(뒤 → 앞): 포니테일 · 먼 윗팔 · 천자락 · 먼 다리 · 가까운 다리 · 골반 · 먼 팔뚝 · 상체 · 망치 · 머리 · 먼 주먹 · 가까운 팔뚝 · 소매 · 어깨 판
DRAW_ART = ['pony', 'upF', 'flapF', 'thighF', 'bootF', 'thighN', 'bootN', 'hips', 'foreF', 'torso', 'hammer', 'head', 'fistF', 'armL', 'armU', 'pauldron']
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
MOVING = own['armL'] | own['armU'] | own['pauldron'] | own['foreF'] | own['fistF'] | own['hammer'] | own['upF']
ART = {}
for n in DRAW_ART:
    _ab = dil(own[n], 3) & above(n) & AL
    if n in ('torso', 'hips', 'thighN', 'thighF', 'flapF', 'bootF', 'bootN'): _ab &= ~MOVING   # 움직이는 팔·주먹·망치 밑 겹침은 안 가져옴(외곽선이 떠 보임) — 그 밑은 메우기
    if n == 'hammer': _ab &= ~own['head']
    if n in ('foreF', 'upF'): _ab &= ~(own['torso'] | own['hips'])   # 먼 팔은 조끼·골반 밑 겹침을 안 가져옴(팔이 몸에서 떨어지면 조끼 조각이 붙어 다님)
    if n == 'pony': _ab &= ~own['head']                                 # 포니테일 밑 머리(땋은 머리 외곽선)는 안 가져옴 — 흔들리면 줄이 떠 보임, 그 밑은 머리카락으로 메움
    if n == 'flapF': _ab &= ~(own['thighF'] | own['bootF'] | own['hips'])
    m = own[n] | _ab; a = RA.copy(); a[..., 3] = np.where(m, RA[..., 3], 0); ART[n] = a
_hsv = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV)
SKIN = (_hsv[..., 0] >= 5) & (_hsv[..., 0] <= 22) & (_hsv[..., 1] > 90) & (_hsv[..., 2] > 140) & (RA[..., 3] > 200)
CREAM = (_hsv[..., 1] < 70) & (_hsv[..., 2] > 175) & (RA[..., 3] > 200) & (RA[..., 0].astype(int) > RA[..., 2].astype(int) + 25)   # 셔츠·소매 크림색(따뜻한 색만 — 조끼 흰 테·회청은 빼기)
SKINC = np.median(RA[..., :3][SKIN & (own['torso'] | own['armL'] | own['foreF'])], 0).astype(np.uint8)
OPQ = lambda n: ART[n][..., 3] > 200
# 상체: 어깨 판·소매·가까운 팔 밑, 턱·옆머리 밑 메움 — 상체 테두리 다각형 안만
TORSO_HULL = pmask([[188, 256], [212, 250], [262, 250], [284, 262], [290, 300], [282, 324], [200, 326], [186, 300]])
_reg = TORSO_HULL & (own['pauldron'] | own['armU'] | own['armL'] | (own['head'] & dil(own['torso'], 8))) & ~OPQ('torso')
ART['torso'] = outline_cut(inpaint_into(ART['torso'], _reg, own['torso'] & (RA[..., 3] > 200) & ~dil(~AL, 2)), _reg)
print('  torso fill', int(_reg.sum()))
# 골반: 먼 주먹·망치 자루 끝·가까운 주먹 밑 — 먼 팔뚝(접은 소매 끝) 밑은 안 메움: v1.4 순서로 골반이 팔뚝 앞이라 메우면 대기에서 소매 끝 아래 말린 곳을 허리띠가 덮음(15:5x 확대)
HIPS_HULL = pmask([[178, 320], [288, 318], [291, 334], [290, 350], [286, 362], [250, 368], [215, 375], [178, 365], [170, 340]])   # 오른쪽 = 허리띠 끝(x 289) — 넘으면 자루 끝 옆 천자락 자리에 골반 색 쐐기(15:5x)
_reg = HIPS_HULL & (own['hammer'] | own['fistF'] | own['armL']) & ~OPQ('hips')
ART['hips'] = outline_cut(inpaint_into(ART['hips'], _reg, own['hips'] & (RA[..., 3] > 200) & ~dil(~AL, 2)), _reg & dil(~HIPS_HULL, 1))
print('  hips fill', int(_reg.sum()))
# 망치 자루(먼 주먹 밑): 주먹 위 가죽 감은 자루(축 t 37~90, 금 고리 t 25~31·97~ 사이)를 축 따라 64px 내려 채움 — 시트 망치를 맞춰 넣으면 시트의 고리·구리색 띠가 주먹 밑에 들어갔음(15:5x)
t_ax = (xx - G[0]) * HU[0] + (yy - G[1]) * HU[1]; n_ax = (xx - G[0]) * -HU[1] + (yy - G[1]) * HU[0]
SHAFT_HW = float(np.median([float(np.ptp(n_ax[own['hammer'] & (np.abs(t_ax - tt) < .8)])) for tt in range(44, 72, 3)])) / 2   # 원화 자루 반폭(외곽선 포함)
SHAFT_SHIFT = 64.0
_hreg = (np.abs(n_ax) <= SHAFT_HW + .5) & (t_ax > -28) & (t_ax < 26) & ~OPQ('hammer')
_mv = cv2.warpAffine(ART['hammer'], np.float32([[1, 0, -HU[0] * SHAFT_SHIFT], [0, 1, -HU[1] * SHAFT_SHIFT]]), (512, 512), flags=cv2.INTER_LINEAR)   # (+t 픽셀을 −t 쪽으로)
_okw = _hreg & (_mv[..., 3] > 128)
ART['hammer'][_okw] = _mv[_okw]
print('  shaft fill', int(_okw.sum()), '/', int(_hreg.sum()), 'px · 자루 반폭', round(SHAFT_HW, 1))
# 쇠 머리 왼쪽 끝 아래 모서리(원화에선 오른쪽 옆머리 끝과 맞닿아 외곽선이 머리 칸으로 감): 시트 망치(reg22 SIFT 닮음)를 원화 색으로 맞춰 채움 — 휘두르면 드러남
if not os.path.exists(os.path.join(HERE, 'pieces', 'index.json')):   # 시트 조각(pieces/ — git 에 안 올림)은 시트에서 다시 자름
    subprocess.run([sys.executable, '-I', os.path.join(HERE, 'cut22.py'), os.path.join(HERE, 'sheets', 'sheet1_v1.png')], check=True, stdout=subprocess.DEVNULL)
sys.path.insert(0, HERE); import reg22
PC = os.path.join(HERE, 'pieces')
def sheet_rgba(n):   # 시트 조각 + 자홍 테두리 빼기
    a = np.array(Image.open(os.path.join(PC, n + '.png')).convert('RGBA')).astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None)
    a[..., 0] -= m; a[..., 2] -= m; return np.clip(a, 0, 255).astype(np.uint8)
_rh = reg22.match('hammer', reg22.REG['hammer']); MHm = np.array(_rh['M'])
_hw = cv2.warpAffine(sheet_rgba('hammer'), MHm, (512, 512), flags=cv2.INTER_LINEAR)
_ov = (_hw[..., 3] > 200) & OPQ('hammer') & (t_ax > 110) & ~dil(own['head'], 3)
_mu_s, _sd_s = _hw[..., :3][_ov].astype(float).mean(0), _hw[..., :3][_ov].astype(float).std(0) + 1
_mu_a, _sd_a = RA[..., :3][_ov].astype(float).mean(0), RA[..., :3][_ov].astype(float).std(0) + 1
_fillH = (_hw[..., 3] > 128) & ~OPQ('hammer') & dil(own['head'], 3) & (t_ax > 90)
ART['hammer'][..., :3][_fillH] = np.clip((_hw[..., :3][_fillH] - _mu_s) / _sd_s * _sd_a + _mu_a, 0, 255).astype(np.uint8); ART['hammer'][..., 3][_fillH] = _hw[..., 3][_fillH]
print('  hammer sheet fill(옆머리 옆 모서리)', int(_fillH.sum()), 'px · sheet scale', _rh['scale'], 'rot', _rh['rot'], 'inl', _rh['inl'])
# 천자락: 망치 자루 끝·먼 주먹·먼 허벅지·무릎 판 밑(공격·달리기에서 드러남) — 천 테두리 다각형 안, 천 색으로 메우고 다각형 경계에 외곽선
#   (15:5x) 메우는 곳 = 자루 끝 금 고리·주먹 밑(천 위쪽 양옆이 보이는 구멍)만 — 허벅지·무릎 판 밑까지 다각형으로 메우면 회색 얼룩 천이 됐음. 다리 밑 잘린 가장자리는 외곽선만
FLAP_HULL = pmask([[287, 335], [297, 332], [321, 351], [316, 356], [300, 354], [289, 348]])   # 천 띠 위쪽 = 왼쪽 보이는 띠(x 288~300)와 오른쪽 위 선((318,352)→(335,365))을 허리띠 쪽(297,332)까지 이은 삼각 띠
_reg = FLAP_HULL & (own['hammer'] | own['fistF']) & ~OPQ('flapF') & AL
_fsrc = own['flapF'] & (RA[..., 3] > 200) & (LUM > 150) & ~dil(own['hammer'] | own['fistF'], 1)
ART['flapF'] = outline_cut(inpaint_into(ART['flapF'], _reg, _fsrc, r=4), _reg & dil(~FLAP_HULL, 1))
ART['flapF'] = outline_cut(ART['flapF'], own['thighF'] | own['bootF'] | own['hips'])   # 다리·허리띠에 가려 잘린 가장자리 = 외곽선(다리가 움직이면 드러남)
_fa_ = ART['flapF'][..., 3] > 10; _n_, _l_, _s_, _ = cv2.connectedComponentsWithStats(_fa_.astype(np.uint8), 8)
ART['flapF'][..., 3] = np.where(_l_ == 1 + int(np.argmax(_s_[1:, cv2.CC_STAT_AREA])), ART['flapF'][..., 3], 0)   # 떨어진 점 지움
_fin = ndimage.distance_transform_edt(ART['flapF'][..., 3] > 128) > 3.2; _fdk = _fin & (ART['flapF'][..., :3].astype(np.float32).mean(-1) < 110)   # 천 안쪽 검은 점(자루 끝 고리 밑 찌꺼기) → 둘레 천 색
_fmd = cv2.medianBlur(np.ascontiguousarray(ART['flapF'][..., :3]), 5); ART['flapF'][..., :3][_fdk] = _fmd[_fdk]
print('  flap fill', int(_reg.sum()))
# 포니테일: 머리(땋은 머리) 밑 띠 12px 를 포니테일 머리카락으로 — 흔들리면 드러남
_reg = dil(own['pony'], 12) & own['head'] & ~OPQ('pony')
ART['pony'] = inpaint_into(ART['pony'], _reg, own['pony'] & (RA[..., 3] > 200) & ~dil(~AL, 2))
print('  pony fill', int(_reg.sum()))
# 먼 팔뚝: 조끼 밑으로 팔꿈치까지 접은 소매(크림) 관 + 둥근 팔꿈치 끝(달리기·공격에서 팔이 돌면 조끼 가장자리에서 드러남)
_u = (WR_F - EL_F) / np.linalg.norm(WR_F - EL_F); _nn = np.array([-_u[1], _u[0]])
_tf = (xx - EL_F[0]) * _u[0] + (yy - EL_F[1]) * _u[1]; _df = (xx - EL_F[0]) * _nn[0] + (yy - EL_F[1]) * _nn[1]
_band = own['foreF'] & (_tf > 13) & (_tf < 17)
CUFF_D = (float(_df[_band].min()), float(_df[_band].max())); CUFF_DC = (CUFF_D[0] + CUFF_D[1]) / 2
CUFF_HW = min((CUFF_D[1] - CUFF_D[0]) / 2 - 1.2, 13.0)   # 접은 소매 끝은 아래 말린 곳까지 재면 반폭 17.6 — 팔꿈치 끝을 그만큼 그리면 공격에서 턱 밑에 큰 공처럼 보였음 → 팔 관 굵기 13
_c0 = EL_F + _nn * CUFF_DC
_ext = ((np.abs(_df - CUFF_DC) <= CUFF_HW) & (_tf >= 0) & (_tf <= 15)) | (np.hypot(xx - _c0[0], yy - _c0[1]) <= CUFF_HW)
_ext = _ext & ~OPQ('foreF')
ART['foreF'] = inpaint_into(ART['foreF'], _ext, own['foreF'] & CREAM)
ART['foreF'] = outline_cut(ART['foreF'], dil(_ext, 1) & ~own['foreF'])   # 이어 그린 소매 끝 둥근 테두리 = 외곽선
ART['foreF'] = outline_cut(ART['foreF'], own['hips'] | own['flapF'])   # 소매 끝 아래 말린 곳이 골반·천에 닿아 잘린 가장자리 = 외곽선(공격에서 팔이 떠나면 흰 톱니로 보였음)
_fin = ndimage.distance_transform_edt(ART['foreF'][..., 3] > 128) > 3.2; _fdk = _fin & dil(_ext, 3) & ~own['foreF'] | (_fin & _ext & (ART['foreF'][..., :3].astype(np.float32).mean(-1) < 170))   # 이어 그린 팔꿈치 끝 안 검은 점 → 둘레 색
_fmd = cv2.medianBlur(np.ascontiguousarray(ART['foreF'][..., :3]), 5); ART['foreF'][..., :3][_fdk] = _fmd[_fdk]
_m = ART['foreF'][..., 3] > 128; _m2 = ndimage.binary_fill_holes(cv2.morphologyEx(_m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0)   # 소매 끝 가장자리 구멍·톱니(칸 경계가 들쭉날쭉) 메움
_add = _m2 & ~_m; _dd, (_iy, _ix) = ndimage.distance_transform_edt(~_m, return_indices=True); ART['foreF'][..., :3][_add] = ART['foreF'][..., :3][_iy[_add], _ix[_add]]; ART['foreF'][..., 3] = np.where(_m2, 255, 0).astype(np.uint8)
ART['foreF'] = outline_cut(ART['foreF'], own['hips'] | own['flapF'])
print('  far cuff 반폭', round(CUFF_HW, 1), '가운데', round(CUFF_DC, 1), 'fill', int(_ext.sum()))
# 먼 윗팔(upF): 조끼 밑으로 어깨~팔꿈치 크림 소매(달릴 때 팔이 흔들리면 조끼 가장자리에서 드러남) — 조끼 칸 안만(대기 = 원화)
_ua = (EL_F - SH_F) / np.linalg.norm(EL_F - SH_F); _ut = (xx - SH_F[0]) * _ua[0] + (yy - SH_F[1]) * _ua[1]; _ud = np.abs((xx - SH_F[0]) * -_ua[1] + (yy - SH_F[1]) * _ua[0])
_ext = (((_ud <= CUFF_HW) & (_ut >= 0) & (_ut <= np.linalg.norm(EL_F - SH_F))) | (np.hypot(xx - SH_F[0], yy - SH_F[1]) <= CUFF_HW)) & own['torso'] & ~OPQ('upF')
ART['upF'] = inpaint_into(ART['upF'], _ext, own['upF'] & CREAM)
print('  far upper sleeve fill', int(_ext.sum()))
# 가까운 소매(armU): 어깨 판 밑으로 어깨까지 소매(크림) — 달릴 때 팔이 흔들리면 드러남
_na = (EL_N - SH_N) / np.linalg.norm(EL_N - SH_N); _nt = (xx - SH_N[0]) * _na[0] + (yy - SH_N[1]) * _na[1]; _nd = np.abs((xx - SH_N[0]) * -_na[1] + (yy - SH_N[1]) * _na[0])
_ext = (((_nd <= 13) & (_nt >= -4) & (_nt <= 20)) | (np.hypot(xx - SH_N[0], yy - SH_N[1]) <= 13)) & ~OPQ('armU') & (own['pauldron'] | dil(own['armU'], 2)) & ~own['armL']
ART['armU'] = inpaint_into(ART['armU'], _ext, own['armU'] & CREAM)
# 가까운 팔뚝(armL): 소매 속으로 팔꿈치 위까지 살 관(팔뚝이 소매 뒤 — 팔꿈치가 굽으면 소매 끝 밑에서 드러남)
_fa = (WR_N - EL_N) / np.linalg.norm(WR_N - EL_N); _ft = (xx - EL_N[0]) * _fa[0] + (yy - EL_N[1]) * _fa[1]; _fd = (xx - EL_N[0]) * -_fa[1] + (yy - EL_N[1]) * _fa[0]
_bandN = own['armL'] & SKIN & (_ft > 4) & (_ft < 14)
_d0, _d1 = (float(_fd[_bandN].min()), float(_fd[_bandN].max())) if _bandN.sum() > 10 else (-8.0, 8.0)
_ext = (_fd >= _d0) & (_fd <= _d1) & (_ft >= -8) & (_ft <= 10) & ~OPQ('armL') & own['armU']
ART['armL'] = inpaint_into(ART['armL'], _ext, own['armL'] & SKIN)
print('  near forearm 살 폭', round(_d1 - _d0, 1), 'fill', int(_ext.sum()))
# 허벅지: 반바지 밑으로 엉덩이 관절까지 살색
for sd, n in [('near', 'thighN'), ('far', 'thighF')]:
    _e = np.zeros((512, 512), np.uint8); h, k = LJ[sd]['h'], LJ[sd]['k']; cv2.line(_e, tuple(int(v) for v in h), tuple(int(v) for v in (h + k) / 2), 1, 28)
    _e = _e.astype(bool) & ~OPQ(n) & own['hips'] & AL
    ART[n] = inpaint_into(ART[n], _e, own[n] & SKIN)
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
part('head', A('head'), pc(NECK, O_['head'])); part('pony', A('pony'), pc(PONY, O_['pony']))
part('torso', A('torso'), pc(HIP, O_['torso'])); part('hips', A('hips'), pc(HIP, O_['hips'])); part('flapF', A('flapF'), pc(FLAP_P, O_['flapF']))
part('pauldron', A('pauldron'), pc(SH_N, O_['pauldron']))
part('armU', A('armU'), pc(SH_N, O_['armU']), elbow=pc(EL_N, O_['armU']))
part('armL', A('armL'), pc(EL_N, O_['armL']), fist=pc(FIST_N, O_['armL']))
part('upF', A('upF'), pc(SH_F, O_['upF']), elbow=pc(EL_F, O_['upF']))
part('foreF', A('foreF'), pc(EL_F, O_['foreF']), elbow=pc(EL_F, O_['foreF']))
part('fistF', A('fistF'), pc(WR_F, O_['fistF']))
# 망치: 자루가 그림 세로(쇠 머리 위)가 되게 원화 오림을 돌려 2배 해상도로 저장(엔진 _swordRigid 는 무기 그림 위쪽 = 자루 방향)
HTH = float(math.atan2(HU[0], -HU[1]))
_ha = Image.open(A('hammer')); _o = O_['hammer']; _S = 4
_big = _ha.resize((_ha.width * _S, _ha.height * _S), Image.LANCZOS); _pv = (G - _o) * _S
_pad = int(max(_big.size) * .8); _can = Image.new('RGBA', (_big.width + 2 * _pad, _big.height + 2 * _pad), (0, 0, 0, 0)); _can.paste(_big, (_pad, _pad)); _pv = _pv + _pad
_rot = _can.rotate(math.degrees(HTH), resample=Image.BICUBIC, center=tuple(_pv))
_bb = _rot.getbbox(); _rot = _rot.crop(_bb); _pv = _pv - np.array(_bb[:2]); _rot = _rot.resize((_rot.width // 2, _rot.height // 2), Image.LANCZOS); _pv = _pv / 2
_ra = np.array(_rot); _n, _lb, _st, _ = cv2.connectedComponentsWithStats((_ra[..., 3] > 10).astype(np.uint8), 8)
_ra[..., 3] = np.where(_lb == 1 + int(np.argmax(_st[1:, cv2.CC_STAT_AREA])), _ra[..., 3], 0)   # 큰 덩어리만(찌꺼기 지움)
Image.fromarray(_ra).save(os.path.join(W, 'hammerUp.png'))
TIPU = float(t_ax[own['hammer'] & (t_ax > 90)].mean()); BUTT = float(-t_ax[own['hammer'] | (ART['hammer'][..., 3] > 128)].min())
HEAD_HALF = float(np.percentile(np.abs(n_ax[own['hammer'] & (t_ax > 120)]), 99.5))   # 쇠 머리 반 길이(자루에 수직) — 타격 때 쇠 머리 아래 끝 = 땅
print('  hammer 쥔 점→쇠 머리 가운데', round(TIPU, 1), '→마개', round(BUTT, 1), '· 쇠 머리 반 길이', round(HEAD_HALF, 1), '(원화 px)')
_WP = [round(float(_pv[0]), 1), round(float(_pv[1]), 1)]; _up = lambda d: [_WP[0], round(_WP[1] - d * 2, 1)]
for nm in ('weapon', 'weaponA'):
    part(nm, os.path.join(W, 'hammerUp.png'), _WP, scale=1.0, tip=_up(TIPU), pommel=_up(-BUTT), tips=[[_WP[0] - 12, round(_WP[1] - TIPU * 2, 1)], [_WP[0] + 12, round(_WP[1] - TIPU * 2, 1)]], shaftDir=[0.0, -1.0])
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
bone('hips', 'hip', HIP, HIP, 'hips'); bone('flapF', 'hips', FLAP_P, HIP, 'flapF')
bone('torso', 'hip', HIP, HIP, 'torso'); bone('head', 'torso', NECK, HIP, 'head'); bone('pony', 'head', PONY, NECK, 'pony')
bone('armU', 'torso', SH_N, HIP, 'armU'); bone('armL', 'armU', EL_N, SH_N, 'armL', rot=0.3)   # 엔진 대기 팔꿈치 처짐(−0.3)만큼 미리 반대로 → 대기 = 원화
bone('pauldron', 'torso', SH_N, HIP, 'pauldron')
bone('armF', 'torso', SH_F, HIP, 'upF'); bone('foreF', 'armF', EL_F, SH_F, 'foreF'); bone('fistF', 'foreF', WR_F, EL_F, 'fistF')
bone('weapon', 'fistF', G, WR_F, 'weapon', rot=HTH)
for n in ['cape', 'scarf', 'pouch', 'skirt', 'skirtB', 'pauldronF']: bones.append(dict(name=n, parent='torso', pos=[0, -200]))

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
TH_R, SH_R = ln('far', 'h', 'k'), ln('far', 'k', 'a')
legs = {'hip': [0, round((LEG_HY - HIP[1]) * 2, 1)], 'thigh': TH_R, 'shin': SH_R, 'thighFirst': True,
        'thighImg': seg('thighF', O_['thighF'], LJ['far']['h'], LJ['far']['k']), 'shinImg': seg('bootFShin', O_['bootF'], LJ['far']['k'], LJ['far']['a']),
        'boot': {'part': 'bootFFoot', 'sole': sole('bootF', LJ['far']['a']), 'ankleRange': [-0.35, 0.45]},
        'near': {'x': round(float(LJ['near']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['near']['h'][0] - HIP[0]) * 2, 1), 'runX': -12, 'shade': 0,
                 'thigh': ln('near', 'h', 'k'), 'shin': ln('near', 'k', 'a'), 'thighImg': seg('thighN', O_['thighN'], LJ['near']['h'], LJ['near']['k']), 'stand': stand('near', 'N')},
        'far': {'x': round(float(LJ['far']['a'][0] - HIP[0]) * 2, 1), 'hipX': round(float(LJ['far']['h'][0] - HIP[0]) * 2, 1), 'runX': 12, 'shade': 0.12,
                'thigh': ln('far', 'h', 'k'), 'shin': ln('far', 'k', 'a'), 'stand': stand('far', 'F')}}
print('  legs near', legs['near']['thigh'], legs['near']['shin'], 'far', legs['far']['thigh'], legs['far']['shin'])

# ---------------- 달리기 다리 — 시트 20·21(허벅지) + 23(먼 부츠, 옆모습 앞코 오른쪽, 무릎 판 붙음)을 발목에서 나눔(12·러스트와 같은 방법) ----------------
RS = 2.0                                                         # 시트 = 원화 배율 → 리그 ×2
#   (10-20 DHL 16:57 ①타격 0.40 뒷다리 '길어지면서 얇아짐 — 두께는 비슷하게, 덜 뻗게' ②③달리기 '표시한 살 부분까지 없애야 자연스러움')
#   원인: 달리는 허벅지 = 먼 다리 서 있는 길이 49(원화 px)를 시트 허벅지(폭 34, 원화 허벅지 44~47 보다 가늚)로 1.45배 늘여 그림 → 길고 가는 살 다리,
#         달리는 부츠 = 시트 ×1(원화 가까운 부츠보다 약 15% 작음)이라 반바지 밑단~무릎 판 사이 살이 20~25px 보였음(12 네온은 무릎 보호대가 반바지 밑단 바로 밑)
#   v1.1(17:15): 부츠 ×1.19 + 짧은 그늘색 허벅지(살 안 보임) → (10-20 17:48 DHL '달릴 때·공격할 때 표시한 다리(반바지 밑~무릎 판 사이 허벅지 살)를 표현 · 전처럼 바지에 붙이지 말고 · 부츠를 살짝 내리거나 줄여서 보이게')
#   v1.2: 허벅지 = 살(시트 허벅지, 원화 허벅지 살 색에 맞춤) · 굵기 = 원화 대기 허벅지 굵기(가까운 44·먼 37 원화 px — 반바지 밑~무릎 판 사이에서 잼) · 길이 = 대기 가까운 허벅지(78.6)
#         부츠 = 시트 ×1.0(v1.1 ×1.19 에서 줄임) · 허벅지 96(대기 먼 허벅지 98.5 쯤) → 반바지 밑단(가까운 다리 뿌리 아래 14.5 원화 px)~무릎 판 위 끝 사이 살이 원화 대기처럼 보임
#         (비교 4안 17:5x: 부츠 ×1.05·허벅지 79 / ×1.05·90 / ×1.0·96 / ×1.0·104 — 79·90 은 달릴 때 살이 거의 안 보이고, 104 는 다리가 v1 보다 길어짐)
RSB = float(os.environ.get('RSB', 2.0))                          # 달리는 부츠 배율(리그) — 시트 ×1.0
RUN_TH = float(os.environ.get('RUN_TH', 96.0))                   # 달리는 허벅지 길이(리그) — 다리 전체 96 + 128.8 = 224.8(v1 227.7 · v1.1 203.2)
RUN_THW = {'thighN': float(os.environ.get('RUN_THWN', 86.0)), 'thighF': float(os.environ.get('RUN_THWF', 76.0))}   # 달리는 허벅지 굵기(리그) = 원화 대기 허벅지 굵기 ×2(가까운 44 · 먼 37 원화 px, 반바지 밑~무릎 판 사이 가운데)
_bf = sheet_rgba('bootF')
KNEE_S, ANK_S = np.array([44.0, 10.0]), np.array([37.0, 74.0])    # 시트 부츠: 무릎(무릎 판 가운데 위) · 발목(발등 띠 위, 뒤꿈치 위)
_Y, _X = np.mgrid[0:_bf.shape[0], 0:_bf.shape[1]]
_sh = _bf.copy(); _sh[..., 3] = np.where(_Y < ANK_S[1] + 6, _bf[..., 3], 0); Image.fromarray(_sh).save(os.path.join(OUT, 'parts', 'rshin.png')); def_parts['rshin'] = dict(src='parts/rshin.png', pivot=[0, 0], scale=1.0)
_ft = _bf.copy(); _ft[..., 3] = np.where(_Y > ANK_S[1] - 8, _bf[..., 3], 0); Image.fromarray(_ft).save(os.path.join(OUT, 'parts', 'rboot.png')); def_parts['rboot'] = dict(src='parts/rboot.png', pivot=ANK_S.tolist(), scale=RSB)
RUN_SH = round(float(np.linalg.norm(ANK_S - KNEE_S)) * RSB, 1)   # 정강이 그림(w 1 = 같은 배율로 가로·세로) → 부츠 전체 ×RSB
legs['thigh'], legs['shin'] = RUN_TH, RUN_SH
print('  run legs thigh', RUN_TH, 'shin', RUN_SH, '(합', round(RUN_TH + RUN_SH, 1), '· 전 98.2 + 129.5)')
def sole_sheet(a, ank):
    m = a[..., 3] > 128; ys = np.nonzero(m.any(1))[0]; yb = ys.max(); out = []
    for y in (yb - 6, yb - 3, yb):
        xs = np.nonzero(m[y])[0]; out += [[round(float(xs.min() - ank[0]), 1), round(float(y - ank[1]), 1)], [round(float(xs.max() - ank[0]), 1), round(float(y - ank[1]), 1)]]
    return out
rseg = {}
_skA = RA[..., :3][SKIN & (own['thighN'] | own['thighF'])].astype(float)   # 원화 허벅지 살 색(평균·편차) — 시트 살은 조금 밝고 노람
for n in ['thighN', 'thighF']:   # 시트 허벅지: 위 = 반바지 속(곧게 잘림), 아래 = 둥근 무릎
    a = sheet_rgba(n); m = a[..., 3] > 128
    _ys = np.nonzero(m.any(1))[0]; y0_, y1_ = _ys.min(), _ys.max(); ty, tx = np.nonzero(m[y0_:y0_ + 6]); top = [float(tx.mean()), float(ty.mean() + y0_)]
    kr = int(y0_ + (y1_ - y0_) * .80); kx = np.nonzero(m[kr])[0]; kn = [float(kx.mean()), float(kr)]
    il = math.hypot(kn[0] - top[0], kn[1] - top[1]); s_ = RUN_TH / il
    _wid = float(np.median([m[y].sum() for y in range(int(top[1]) + 4, kr)]))   # 시트 허벅지 폭(px)
    _dd = ndimage.distance_transform_edt(m); _in = m & (_dd > 1.8) & (a[..., :3].astype(int).mean(-1) > 90)   # 외곽선 안 살
    _sk = a[..., :3][_in].astype(float); _mu_s, _sd_s = _sk.mean(0), _sk.std(0) + 1
    a = a.copy(); a[..., :3][_in] = np.clip((a[..., :3][_in] - _mu_s) / _sd_s * _skA.std(0) + _skA.mean(0), 0, 255).astype(np.uint8)
    Image.fromarray(a).save(os.path.join(OUT, 'parts', 'r' + n + '.png')); def_parts['r' + n] = dict(src=f'parts/r{n}.png', pivot=[0, 0], scale=1.0)
    rseg[n] = {'part': 'r' + n, 'a': [round(top[0], 1), round(top[1], 1)], 'b': [round(kn[0], 1), round(kn[1], 1)], 'w': round(RUN_THW[n] / (_wid * s_), 3)}   # 굵기 = 원화 대기 허벅지
    print('  run', n, '시트 폭', _wid, '길이 배율', round(s_, 2), '→ 굵기', RUN_THW[n], '(가로 배율', round(RUN_THW[n] / _wid, 2), ')')
legs['thighImg'] = rseg['thighF']; legs['near']['thighImg'] = rseg['thighN']; legs['far']['thighImg'] = rseg['thighF']
legs['shinImg'] = {'part': 'rshin', 'a': KNEE_S.tolist(), 'b': ANK_S.tolist(), 'w': 1.0}
legs['boot'] = {'part': 'rboot', 'sole': sole_sheet(_ft, ANK_S), 'ankleRange': [-0.35, 0.6], 'runLock': 0.0}   # 발목 앞 굽힘 .45 → .6: 가까운 정강이가 세로에서 29° 누운 원화(12 는 23°) — .45 면 서 있을 때 발을 7° 돌려 맞춤(15:5x 대기 비교)
print('  run thigh', {k: (v['w']) for k, v in rseg.items()})

# ---------------- 표정·깜빡임: 시트 3~10칸(2칸 머리와 같은 그림 자리) → 머리 맞춤(MH)으로 원화 얼굴에 ----------------
_rhd = reg22.match('head', reg22.REG['head']); MH = np.array(_rhd['M']); print('  head sheet→원화 scale', _rhd['scale'], 'rot', _rhd['rot'], 'inl', _rhd['inl'])
# 얼굴 칸(22): 시트 표정 7장을 원화 자리에 놓고 서로 다른 곳(눈·눈썹·입·안경 알 안) + 둘레 5px — 12 처럼 '가장 큰 살색 덩어리'로 잡으면
#   앞머리·안경테가 얼굴 살을 여러 조각으로 나눠 왼쪽 뺨만 잡혔음(15:5x 표정이 하나도 안 바뀜)
_wfs = {n: cv2.warpAffine(sheet_rgba(n), MH, (512, 512), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)).astype(np.int16)
        for n in ['face_neutral', 'face_happy', 'face_angry', 'face_focus', 'face_shout', 'face_effort', 'blink_half', 'blink_closed']}
_dif = np.zeros((512, 512), bool)
for n, w_ in _wfs.items():
    if n != 'face_neutral': _dif |= (np.abs(w_[..., :3] - _wfs['face_neutral'][..., :3]).sum(-1) > 60) & (w_[..., 3] > 200)
_box = np.zeros((512, 512), bool); _box[165:270, 180:325] = True
_dif &= _box; _dif = ndimage.binary_opening(_dif, np.ones((2, 2)))
FACE = ndimage.binary_fill_holes(cv2.morphologyEx(dil(_dif, 5).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0) & own['head'] & _box
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

# ---------------- 내려찍기: 12 네온 v1.4 한 손(attack/smash22.py — 12 smash12.py 와 같은 시간표·순서, 쥔 점·어깨 키는 22 몸으로 옮김) ----------------
exec(open(os.path.join(HERE, 'attack', 'smash22.py')).read())

# ---------------- 그리는 순서 (뒤 → 앞) — 12 v1.4 규칙(10-20 12:18 DHL ①달리기·대기 = 손·망치가 다리 뒤) + 천자락 맨 뒤(원화) + 포니테일 = 망치 앞·머리 뒤 + 가까운 팔뚝 = 소매 뒤 ----------------
draw = ['flapF', 'armF', 'foreF', 'weapon', 'fistF', 'legFar', 'legNear', 'hips', 'pony', 'torso', 'head', 'armL', 'armU', 'pauldron']
_top = int(np.nonzero(own['head'][:, 265:326].any(1))[0].min())
rig = {'name': 'dulcinea-sky', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0] * 2), float(O[1] * 2)], 'refScale': 1.0, 'refLift': 0,
       'parts': def_parts, 'bones': bones, 'legs': legs, 'draw': draw, 'hidden': [], 'faces': FACES, 'blinkFaces': {'half': 'blink_half', 'closed': 'blink_closed'},
       'metrics': {'bodyHeight': round(2 * (O[1] - _top), 1), 'note': f'리그 단위; 땋은 머리 위(y{_top}, x 265~325 — 포니테일 빼고)~발바닥(485) ×2, 무기 제외'},
       'armPhase': 0, 'gait': {'stance': 0.32, 'heelKick': 0.85, 'kneeLift': 0.95, 'strideBase': 70, 'strideK': 0.2, 'swingReach': 0.12, 'swingAng': 0.12, 'landAng': 0, 'hipBase': 18, 'bob': 16, 'lean': 0.2, 'strideFlex': [0.75, 1.5], 'headRun': 0.06, 'elbowRun': 1.2, 'armSwing': 0.55, 'armBias': 0.1},
       'ponySway': 0.6, 'carrySwing': 0.4, 'wristRange': 0.3, 'follow': [{'bone': 'pauldron', 'src': 'armU', 'k': 0.35}],
       'bounce': [{'bone': 'flapF', 'stiff': 150, 'damp': 6, 'y': 0.35, 'rot': 0.008, 'max': 12}],
       'ui': {'attack': 'smash', 'touch': 'hop'},
       'gameRef': {'refOrigin': [round(float(O[0] - (HIP[0] - 282.4)), 1), float(O[1])], 'refScale': 2.0, 'refLift': 0,
                   'note': '게임 그림 char_0022.png(512) = 원화(md5 같음, source/ref512.png). x = 도감 칸(fitArt 중심 282.4, index.html measureBox 를 브라우저에서 같은 계산 — 2·12 값 248.9·269.5 로 확인)에서 골반(hip x 222)이 가운데 (2·12 와 같은 규칙)'},
       'cutHold': 0.32,   # 스킬 컷인 = 망치를 머리 위로 높이 든 휘두름 시작(2·12 와 같은 시각)
       'note': '22 스카이 둘시네 시험판 p1 (2026-10-20 — 원화 조각 + 시트 표정·자루·쥔 손·달리기 다리, 12 네온 v1.4 한 손 내려찍기·그리는 순서, 포니테일·천자락 흔들림)'}
rig.update(SMASH)
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(os.path.join(OUT, 'parts'))): _h.update(fn.encode()); _h.update(open(os.path.join(OUT, 'parts', fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_sky22.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['dulcinea-sky']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(def_parts), 'parts, version', rig['version'], 'bodyHeight', rig['metrics']['bodyHeight'])
