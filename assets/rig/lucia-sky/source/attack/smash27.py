"""17 네온 루시아 — 한 손 도끼 내려찍기 (7 러스트 attack/smash7.py v1.5 구조 그대로 옮김). build_lucia17.py 가 exec.
같은 것: 시간표(들어 올림 .18 · 예비 .27 · 휘두름 .32·.36 · 타격 .40 · 버팀 .58 · 돌아옴 .68·.82)·얼굴(화남 → 외침 → 화남, 눈 뜸)·도끼 바꿈(weapon→weaponA)·공격 내내 한 순서(drawA)·farDx 10
바꾼 것: ①쥔 점·자루 각·골반·숙임 키 = attack/keys17.json(tools/genkeys17.py — 러스트 키를 네온 어깨·팔 길이로 옮겨 keyfit17 로 고침)
  ②먼 팔 조각: 윗팔 = upF(원화 회색 판·짙은 소매 + 어깨갑 밑 시트 13 소매 — 한 조각이라 러스트 upFs 바꿈 없음) · 팔뚝 afFart = 원화 크림 팔뚝 갑 + 회색 손목 고리 + 주먹 가운데(G)까지 고리 색 관 + 둥근 팔꿈치 끝
  ③먼 주먹 = 내내 원화 주먹(gFart·gFart2 — 러스트 v1.3) ④가까운 팔 = 방패 뒤 빈 뼈(방패는 상체 숙임 60% 되세움 — build follow)
입력 전역: def_parts, bones, O_, pc, HIP, SH_F, EL_F, WR_F, G, HU, OUT, W, HERE, json, np, os, cv2, Image, own, RA, LUM, TIPU, O, math, dil, ndimage, sheet_rgba, color_match, _uw(시트 윗팔 맞춘 것), xx, yy
출력: SMASH(rig 에 합칠 dict)"""
def unit(v): v = np.array(v, float); return [round(float(x), 4) for x in v / np.linalg.norm(v)]
def capsule(a, p0, p1, col, hwmax=None):   # 원화 좌표 p0→p1 을 a(512 캔버스) 안에 굵기 hw 로 이어 그림 — 이미 불투명한 곳은 그대로
    ax = (p1 - p0) / np.linalg.norm(p1 - p0); X, Y = xx, yy
    near0 = (np.abs((X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1]) < 4) & (a[..., 3] > 200)
    hw = max(6.0, float(np.abs((X - p0[0]) * -ax[1] + (Y - p0[1]) * ax[0])[near0].max()) - 1.5) if near0.any() else 8.0
    if hwmax: hw = min(hw, hwmax)
    t = (X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1]; d = np.abs((X - p0[0]) * -ax[1] + (Y - p0[1]) * ax[0])
    m = (t >= -2) & (t <= np.linalg.norm(p1 - p0) + 2) & (d <= hw) & ~(a[..., 3] > 200)
    a[..., :3][m] = col; a[..., 3][m] = 255; return a, round(hw, 1)
# 먼 팔뚝(공격): 원화 팔뚝 갑 + 회색 손목 고리(foreF) → 주먹 가운데(G)까지 고리 색 관(주먹 밑) — 대기 = 원화 그대로(이은 곳은 주먹 밑)
oF, oA = O_['fistF'], O_['foreF']
_fa = np.array(Image.open(os.path.join(W, 'foreFArt.png')).convert('RGBA')); _cv = np.zeros((512, 512, 4), np.uint8); _cv[int(oA[1]):int(oA[1]) + _fa.shape[0], int(oA[0]):int(oA[0]) + _fa.shape[1]] = _fa
_hsv_ = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV)
_cuff = own['foreF'] & (_hsv_[..., 1] < 50) & (LUM > 60) & (LUM < 170) & (np.hypot(xx - WR_F[0], yy - WR_F[1]) < 16)   # 회색 손목 고리
_CFC = np.median(RA[..., :3][_cuff], 0).astype(np.uint8) if _cuff.sum() > 10 else np.array([100, 100, 104], np.uint8)
_cv, _hwF = capsule(_cv, WR_F, G, _CFC, hwmax=float(os.environ.get('HW_WRIST', 12)))
_n_, _lb_, _st_, _ = cv2.connectedComponentsWithStats((_cv[..., 3] > 10).astype(np.uint8), 8)
_cv[..., 3] = np.where(_lb_ == 1 + int(np.argmax(_st_[1:, cv2.CC_STAT_AREA])), _cv[..., 3], 0)
# 팔꿈치 쪽 끝 다듬기(러스트 v1.2 — 각지지 않게): 팔꿈치 둘레 팔뚝 모양 볼록 껍질 + 둥근 끝(반지름 R_E)을 가까운 팔뚝 갑 색으로 채우고 새 가장자리에 외곽선
_fm = _cv[..., 3] > 10; _er = np.hypot(xx - EL_F[0], yy - EL_F[1]) < float(os.environ.get('ELBOW_ZONE', 26))
_RE = float(os.environ.get('ELBOW_R', 12.0)); _dsc = np.hypot(xx - EL_F[0], yy - EL_F[1]) <= _RE
_hp = cv2.convexHull(np.stack(np.nonzero((_fm & _er) | _dsc)[::-1], 1).astype(np.int32)); _hm = np.zeros((512, 512), np.uint8); cv2.fillPoly(_hm, [_hp], 1)
_add = (_hm > 0) & _er & ~_fm
_src_ = _fm & (_cv[..., :3].astype(np.float32).mean(-1) > 70); _ii2 = ndimage.distance_transform_edt(~_src_, return_distances=False, return_indices=True)
_cv[..., :3][_add] = _cv[..., :3][_ii2[0][_add], _ii2[1][_add]]; _cv[..., 3][_add] = 255
_full = _cv[..., 3] > 10; _edge = _full & ~ndimage.binary_erosion(_full, iterations=2) & dil(_add, 1)
_cv[..., :3][_edge] = np.array([30, 28, 30], np.uint8)
print('  smash 팔뚝 팔꿈치 끝 메움', int(_add.sum()), 'px · 손목 고리 관 반폭', _hwF, '· 고리 색', _CFC.tolist())
_ys, _xs = np.nonzero(_cv[..., 3] > 0); oA2 = np.array([_xs.min() - 2, _ys.min() - 2], float)
Image.fromarray(_cv[int(oA2[1]):_ys.max() + 3, int(oA2[0]):_xs.max() + 3]).save(os.path.join(OUT, 'parts', 'afFart.png'))
def_parts['gFart'] = dict(src='parts/fistF.png', pivot=pc(G, oF), scale=2.0, grip=pc(G, oF), wrist=pc(G, oF), elbow=pc(G, oF),
                          shaftDir=[round(float(HU[0]), 4), round(float(HU[1]), 4)], fore='afFart', foreBone='foreFf', foreDir=unit(EL_F - G))
def_parts['afFart'] = dict(src='parts/afFart.png', pivot=pc(G, oA2), scale=2.0, elbow=pc(EL_F, oA2))
# 공격 중(.05~.88) 팔뚝 afFart2 = 시트 14 팔뚝(옆에서 본 긴 크림 팔뚝 갑 + 회색 손목 고리) — 원화 팔뚝 갑은 앞을 향해 줄어 보인 덩어리라 들어 올리면 팔꿈치가 조각나 보였음(v1 시험)
#   시트 팔꿈치 원 가운데 (16,15) → EL_F · 손목 고리 가운데 (22,57) → WR_F 로 닮음 변환(배율 ≈ 1.13), 원화 팔뚝 갑 색으로 맞춤 + 주먹 가운데(G)까지 고리 색 관
_sf_ = sheet_rgba('foreF'); _e0, _c0 = (np.array([float(v) for v in os.environ.get('FE0', '16,9').split(',')]), np.array([float(v) for v in os.environ.get('FC0', '16,43').split(',')]))
_s2 = float(np.linalg.norm(WR_F - EL_F) / np.linalg.norm(_c0 - _e0)); _r2 = math.atan2(*(WR_F - EL_F)[::-1]) - math.atan2(*(_c0 - _e0)[::-1])
_M2 = np.array([[_s2 * math.cos(_r2), -_s2 * math.sin(_r2), 0], [_s2 * math.sin(_r2), _s2 * math.cos(_r2), 0]]); _M2[:, 2] = EL_F - _M2[:, :2] @ _e0
_fw = cv2.warpAffine(_sf_, _M2, (512, 512), flags=cv2.INTER_LINEAR)
_lt = lambda a: a[..., :3].astype(np.float32).mean(-1) > 185   # 크림 평균만 맞춤(평균·편차 맞춤은 회색 판·고리를 푸르게 바꿨음)
_selS = (_fw[..., 3] > 200) & _lt(_fw); _selA = own['foreF'] & (RA[..., 3] > 200) & _lt(RA)
if _selS.sum() > 30 and _selA.sum() > 30: _o_ = _fw[..., 3] > 0; _fw[..., :3][_o_] = np.clip(_fw[..., :3][_o_].astype(np.float32) + (RA[..., :3][_selA].astype(np.float32).mean(0) - _fw[..., :3][_selS].astype(np.float32).mean(0)), 0, 255).astype(np.uint8)
_cv2, _hw2 = capsule(_fw.copy(), WR_F, G, _CFC, hwmax=float(os.environ.get('HW_WRIST', 12)))
_ys, _xs = np.nonzero(_cv2[..., 3] > 0); oA3 = np.array([_xs.min() - 2, _ys.min() - 2], float)
Image.fromarray(_cv2[int(oA3[1]):_ys.max() + 3, int(oA3[0]):_xs.max() + 3]).save(os.path.join(OUT, 'parts', 'afFart2.png'))
def_parts['afFart2'] = dict(src='parts/afFart2.png', pivot=pc(G, oA3), scale=2.0, elbow=pc(EL_F, oA3))
def_parts['gFart2'] = dict(def_parts['gFart'], fore='afFart2')
bones.append(dict(name='foreFf', parent='torso', pos=[0, 0], part='afFart'))
print(f'  smash 팔뚝(공격) 시트 14 배율 {_s2:.3f} · 회전 {math.degrees(_r2):.1f}°')
# 공격 중(.05~.88) 윗팔 upFs = 시트 13 윗팔(곧은 짙은 소매 + 회색 네모 판·금색 줄)을 어깨 → 팔꿈치에 맞춘 것(build 의 _uw — 원화 색 맞춤) — armF 의 자식 뼈 armFs, 투명도 키로 바꿈(러스트 upFs 와 같은 방법)
_ys, _xs = np.nonzero(_uw[..., 3] > 0); _o_us = np.array([_xs.min() - 2, _ys.min() - 2], float)
Image.fromarray(_uw[int(_o_us[1]):_ys.max() + 3, int(_o_us[0]):_xs.max() + 3]).save(os.path.join(OUT, 'parts', 'upFs.png'))
def_parts['upFs'] = dict(src='parts/upFs.png', pivot=pc(SH_F, _o_us), scale=2.0, elbow=pc(EL_F, _o_us))
bones.append(dict(name='armFs', parent='armF', pos=[0, 0], part='upFs'))

# ---- 시간표 (애니 초) — 7·12·22 와 같음 ----
LIFT, WIND, SW1, SW2, HIT, HOLD, RET1, RET, END = .18, .27, .32, .36, .40, .58, .68, .82, 1.0
k = lambda *kv: [list(x) for x in kv]
UPS_T = [float(v) for v in os.environ.get('UPS_T', '0.05,0.88').split(',')]   # 시트 윗팔·팔뚝을 쓰는 구간 = 주먹 nPiece gFart2 와 같은 때
KF = json.load(open(os.environ.get('KEYS27') or os.path.join(HERE, 'attack', 'keys27.json')))
KEYS = KF['keys']   # [t, gx, gy(리그 px, 골반 기준), 자루 각(도), 숙임(rad), 골반 x, 골반 y, 쥔 손(키 표 확인용), 이음]
_g0 = (G - HIP) * 2; _a0 = math.atan2(HU[1], HU[0])
assert abs(KEYS[0][1] - _g0[0]) < 1 and abs(KEYS[0][2] - _g0[1]) < 1 and abs(math.radians(KEYS[0][3]) - _a0) < .01, ('keys27 0 키 = 대기 쥔 점·자루 각이어야 함', _g0, math.degrees(_a0))
EZ = lambda r: r[8] if len(r) > 8 and r[8] else None
PT = lambda i, f=lambda v: v: [[r[0], round(f(r[i]), 4)] + ([EZ(r)] if EZ(r) else []) for r in KEYS]
smash = {
    'kind': 'sword', 'rigid': True, 'orderAlways': True, 'dur': END, 'hitAt': HIT, 'hitStop': .12, 'cancelAt': .78, 'freeArm': True,
    'aDamp': 30, 'standStep': True,
    'ankleRange': [-.45, 1.1], 'legRun': k((0, 0)),   # v1.2(DHL 10-21 15:40 '이 타이밍에 다리를 틀지 말고 이전 다리 모양으로 공격을 완료하고 이동 전에 다리를 틀면'): 공격 내내 서 있는 원화 다리 —
    #   전엔 러스트처럼 휘두름 .31~.34 에 달리기 다리로, .87 에 다시 서 있는 다리로 바꿈(두 번 틀림). 달리다 공격하면 시작 .09 에 서 있는 다리로 한 번, 공격이 끝나 다시 달릴 때 한 번만 바뀜 · 골반 내림 0(genkeys17)
    'w': k((0, 0, 'io'), (.12, 1), (END - .03, 1, 'io'), (END, 0)),
    'reach': k((0, 0)), 'sN': k((0, 0)),
    'nPiece': k((0, 'gFart'), (.05, 'gFart2'), (.88, 'gFart')),   # 먼 손 = 내내 원화 주먹(러스트 v1.3)
    'armIK': k((0, 1)), 'ikSideK': {'N': [[0, 1]]},
    'gx': PT(1), 'gy': PT(2), 'sa': PT(3, math.radians), 'lean': PT(4), 'hipX': PT(5), 'hipY': PT(6),
    'fuA': k((0, 0)),   # 자유 팔 = 방패 뒤 빈 뼈
    'flA': k((0, 0)),
    'head': k((0, 0, 'io'), (LIFT, .05, 'io'), (WIND, .06, 'i'), (HIT, -.08, 'o'), (HOLD, -.06, 'io'), (RET + .08, 0)),
    'nearDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, 10), (HOLD, 9, 'io'), (RET + .06, 0)),
    'farDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, 10), (HOLD, 10, 'io'), (RET + .06, 0)),   # 러스트 v1.5(DHL 10-21 00:10) — 먼 다리가 손·도끼에 안 걸리게
    'farLift': k((0, 0), (SW1, 0, 'io'), (SW2, 11, 'io'), (HIT, 0), (HOLD, 0, 'io'), (HOLD + .06, 8, 'io'), (RET + .06, 0)),
    'shake': k((0, 0), (HIT, 0, 'lin'), (HIT + .01, 1), (HIT + .12, 0)),
    'face': [[0, 'angry'], [WIND, 'shout'], [HIT + .14, 'angry'], [RET + .08, None]],   # 공격 내내 눈 뜸(러스트 v1.4 DHL 23:58 '공격할때 눈 감지 않도록')
    'fade': {'weapon': k((0, 1), (.06, 1, 'lin'), (.061, 0), (.93, 0, 'lin'), (.931, 1)), 'weaponA': k((0, 0), (.06, 0, 'lin'), (.061, 1), (.93, 1, 'lin'), (.931, 0)),
             'armF': k((0, 1), (UPS_T[0], 1, 'lin'), (UPS_T[0] + .001, 0), (UPS_T[1], 0, 'lin'), (UPS_T[1] + .001, 1)),     # 윗팔: 원화(대기 그림) ↔ 시트 곧은 윗팔(공격 중)
             'armFs': k((0, 0), (UPS_T[0], 0, 'lin'), (UPS_T[0] + .001, 1), (UPS_T[1], 1, 'lin'), (UPS_T[1] + .001, 0)),
             'pauldronF': k((0, 1), (UPS_T[0], 1, 'lin'), (UPS_T[0] + .001, 0), (UPS_T[1], 0, 'lin'), (UPS_T[1] + .001, 1)),   # 어깨갑: 원화 ↔ 시트 12 위 원화(아래 테 온전)
             'pauldronFs': k((0, 0), (UPS_T[0], 0, 'lin'), (UPS_T[0] + .001, 1), (UPS_T[1], 1, 'lin'), (UPS_T[1] + .001, 0))},
    'order': [[0, 'drawA']],
}
for _k, _v in (KF.get('tracks') or {}).items(): smash[_k] = _v
_ov = os.environ.get('SMASH_KEYS')
if _ov: smash.update(json.load(open(_ov)))
# 그리는 순서(공격 내내 한 순서 — 대기 순서와 같은 규칙): 먼 팔뚝·도끼·쥔 주먹 = 다리·골반·머리 뒤 · 다리 = 상체·골반 뒤 · 윗팔 = 상체 앞 · 어깨갑 = 윗팔 앞 · 가리개 = 머리 앞 · 방패 맨 앞
DRAW_ATK = ['foreFf', 'weapon', 'weaponA', 'foreF', 'legFar', 'legNear', 'torso', 'armF', 'armFs', 'pauldronF', 'pauldronFs', 'hips', 'head', 'armU', 'armL', 'shield']
_hk = [r for r in KEYS if abs(r[0] - HIT) < 1e-6][0]; _Gy = (HIP[1] - O[1]) * 2 + _hk[6] + _hk[2]
TIPD = round(_Gy + math.sin(math.radians(_hk[3])) * TIPU * 2 + 6, 1)
SMASH = {'actions': {'smash': smash}, 'drawA': DRAW_ATK,
         'swordGrip': {'tipDepth': TIPD, 'near': {'upper': 'upF', 'carry': 'gFart'}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': 0}, 'stretchMax': 1.05, 'shoulderPush': 0},
         'hidden': ['weaponA', 'armFs', 'pauldronFs']}
bones.append(dict(name='weaponA', parent='weapon', pos=[0, 0], part='weaponA'))
print('  smash tipDepth', TIPD, '· 키', len(KEYS))
