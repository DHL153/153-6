"""7 러스트 루시아 — 한 손 도끼 내려찍기 (22 스카이 둘시네 attack/smash22.py = 12 네온 v1.4 구조를 옮김, 10-20 21:xx v1). build_lucia7.py 가 exec.
같은 것: 시간표(들어 올림 .18 · 예비 .27 · 휘두름 .32·.36 · 타격 .40 · 버팀 .58 · 돌아옴 .68·.82)·얼굴·도끼 바꿈(weapon→weaponA)·공격 내내 한 순서(drawA)
바꾼 것: ①쥔 점·자루 각·골반·숙임 키 = attack/keys7.json(tools/keyfit7.py 로 잼 — 루시아 팔: 주먹 = 쥔 점, 팔뚝 = 쥔 점→팔꿈치)
  — 타격·버팀: 날 앞 끝이 땅에 닿게(도끼가 몸 키보다 커서 12 키 그대로면 날이 땅속으로 들어감 — 연구 10-20 20:3x), 손목 꺾임 ±40° 안
  ②먼 팔 조각: 윗팔 auFart = 원화 걷은 갈색 소매(upF, 보호대 밑까지 이어 그림) · 팔뚝 afFart = 원화 살 팔뚝 + 손목 띠 + 주먹 가운데(G)까지 띠 색 관
  ③gFh = 시트 19칸(tools/gfh7.py, ×1.3 — 시트 주먹이 원화보다 작음) ④가까운 팔 = 방패(자유 팔 fuA 를 follow 로 12% 따라 돎)
입력 전역: def_parts, bones, O_, pc, HIP, SH_F, EL_F, WR_F, G, HU, OUT, W, HERE, json, np, os, cv2, Image, own, RA, LUM, SKIN, BLADE_LO, TIPU
출력: SMASH(rig 에 합칠 dict)"""
def unit(v): v = np.array(v, float); return [round(float(x), 4) for x in v / np.linalg.norm(v)]
def capsule(a, o, p0, p1, col, hwmax=None):   # 원화 좌표 p0→p1 을 a(틀 o) 안에 팔뚝 굵기로 이어 그림 — 이미 불투명한 곳은 그대로
    ax = (p1 - p0) / np.linalg.norm(p1 - p0); hh, ww = a.shape[:2]; yy_, xx_ = np.mgrid[0:hh, 0:ww]; X, Y = xx_ + o[0], yy_ + o[1]
    near0 = (np.abs((X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1]) < 4) & (a[..., 3] > 200)
    hw = max(6.0, float(np.abs((X - p0[0]) * -ax[1] + (Y - p0[1]) * ax[0])[near0].max()) - 1.5) if near0.any() else 8.0
    if hwmax: hw = min(hw, hwmax)
    t = (X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1]; d = np.abs((X - p0[0]) * -ax[1] + (Y - p0[1]) * ax[0])
    m = (t >= -2) & (t <= np.linalg.norm(p1 - p0) + 2) & (d <= hw) & ~(a[..., 3] > 200)
    a[..., :3][m] = col; a[..., 3][m] = 255; return a, round(hw, 1)
# 먼 팔: 원화 주먹(fistF, 도끼 자루를 쥔 그대로) · 원화 팔뚝(foreF: 살 + 갈색 손목 띠)을 주먹 가운데(G)까지 띠 색으로 이어 그린 것 — 대기 = 원화 그대로(이은 곳은 주먹 밑)
oF, oA = O_['fistF'], O_['foreF']
_fa = np.array(Image.open(os.path.join(W, 'foreFArt.png')).convert('RGBA')); _cv = np.zeros((512, 512, 4), np.uint8); _cv[int(oA[1]):int(oA[1]) + _fa.shape[0], int(oA[0]):int(oA[0]) + _fa.shape[1]] = _fa
_bd = own['foreF'] & ~SKIN & (LUM > 45) & (LUM < 150) & (np.hypot(xx - WR_F[0], yy - WR_F[1]) < 22) & ((xx - WR_F[0]) * (G - WR_F)[0] + (yy - WR_F[1]) * (G - WR_F)[1] > 0)   # 손목 띠 갈색(손목 → 주먹 쪽)
_BDC = np.median(RA[..., :3][_bd], 0).astype(np.uint8) if _bd.sum() > 10 else np.array([110, 60, 40], np.uint8)
_cv, _hwF = capsule(_cv, np.zeros(2), WR_F, G, _BDC, hwmax=float(os.environ.get('HW_WRIST', 11)))
_n_, _lb_, _st_, _ = cv2.connectedComponentsWithStats((_cv[..., 3] > 10).astype(np.uint8), 8)
_cv[..., 3] = np.where(_lb_ == 1 + int(np.argmax(_st_[1:, cv2.CC_STAT_AREA])), _cv[..., 3], 0)
_ys, _xs = np.nonzero(_cv[..., 3] > 0); oA2 = np.array([_xs.min() - 2, _ys.min() - 2], float)
Image.fromarray(_cv[int(oA2[1]):_ys.max() + 3, int(oA2[0]):_xs.max() + 3]).save(os.path.join(OUT, 'parts', 'afFart.png'))
def_parts['gFart'] = dict(src='parts/fistF.png', pivot=pc(G, oF), scale=2.0, grip=pc(G, oF), wrist=pc(G, oF), elbow=pc(G, oF),
                          shaftDir=[round(float(HU[0]), 4), round(float(HU[1]), 4)], fore='afFart', foreBone='foreFf', foreDir=unit(EL_F - G))
def_parts['afFart'] = dict(src='parts/afFart.png', pivot=pc(G, oA2), scale=2.0, elbow=pc(EL_F, oA2))
def_parts['afFart2'] = dict(def_parts['afFart'])
def_parts['gFart2'] = dict(def_parts['gFart'], fore='afFart2')
# 먼 윗팔 auFart = 갈색 소매 관(둥근 두 끝 + 외곽선 + 아래 그늘 + 팔꿈치 쪽 걷은 주름 2줄) — 원화 걷은 소매(upF)는 아래로 처진 모양이라
#   머리 위로 들면 보호대 밑에 갈색 천 덩어리가 매달려 보였음(21:5x v1 시험) → 22 크림 소매 관과 같은 방법. 길이 = 원화 어깨→팔꿈치, 굵기 = 소매 반폭
_LU = float(np.linalg.norm(EL_F - SH_F)); _r = float(os.environ.get('UP_R', 12.5)); _Wd, _Hd = int(_LU + 2 * _r + 6), int(2 * _r + 6)
_uy, _ux = np.mgrid[0:_Hd, 0:_Wd].astype(np.float32); _p0 = np.array([_r + 3, _r + 3]); _p1 = _p0 + np.array([_LU, 0])
_tt = np.clip((_ux - _p0[0]) / _LU, 0, 1); _dd = np.hypot(_ux - (_p0[0] + _tt * _LU), _uy - _p0[1])
_au = np.zeros((_Hd, _Wd, 4), np.uint8); _in = _dd <= _r
_slv = own['upF'] & ~SKIN & (LUM > 55) & (LUM < 160)
_SLC = np.median(RA[..., :3][_slv], 0).astype(np.uint8)
_au[..., :3][_in] = _SLC; _au[..., 3][_in] = 255
_sh = _in & (_uy > _p0[1] + _r * .3); _au[..., :3][_sh] = (_au[..., :3][_sh] * np.array([.82, .78, .76])).astype(np.uint8)   # 아래 그늘
_hl = _in & (_uy < _p0[1] - _r * .45); _au[..., :3][_hl] = np.clip(_au[..., :3][_hl] * 1.12, 0, 255).astype(np.uint8)          # 위 밝은 띠
for _fx in (_p1[0] - 13, _p1[0] - 22): _au[..., :3][_in & (np.abs(_ux - _fx - (_uy - _p0[1]) * .35) < 1.0)] = (_SLC * .55).astype(np.uint8)   # 걷은 주름
_au[..., :3][_in & (_dd > _r - 2.2)] = np.array([30, 22, 20], np.uint8)
Image.fromarray(_au).save(os.path.join(OUT, 'parts', 'auFart.png'))
def_parts['auFart'] = dict(src='parts/auFart.png', pivot=[round(float(_p0[0]), 1), round(float(_p0[1]), 1)], scale=2.0, elbow=[round(float(_p1[0]), 1), round(float(_p1[1]), 1)])
print('  smash 윗팔 관 반지름', _r, '· 소매 색', _SLC.tolist())
bones.append(dict(name='foreFf', parent='torso', pos=[0, 0], part='afFart'))
print('  smash 손목 띠 관 굵기 반(원화 px)', _hwF, '· 띠 색', _BDC.tolist())
# 휘두름~버팀 먼 손 = 시트 19칸 '자루 따라 쥔 손'(gFh, tools/gfh7.py)
AD = os.environ.get('GFH_DIR') or os.path.join(HERE, 'attack'); AP = json.load(open(os.path.join(AD, 'pieces.json')))
_j = AP['gFh']; shutil.copy(os.path.join(AD, 'pieces', 'gFh.png'), os.path.join(OUT, 'parts', 'gFh.png')); _g = [round(float(_j['grip'][0]), 1), round(float(_j['grip'][1]), 1)]
def_parts['gFh'] = dict(src='parts/gFh.png', pivot=_g, scale=_j['scale'], grip=_g, wrist=_g, elbow=_g, shaftDir=[float(v) for v in _j['shaftDir']],
                        fore='afFart2', foreBone='foreFf', foreDir=unit(np.array(_j['wrist']) - np.array(_j['grip'])))

# ---- 시간표 (애니 초) — 12·22 와 같음 ----
LIFT, WIND, SW1, SW2, HIT, HOLD, RET1, RET, END = .18, .27, .32, .36, .40, .58, .68, .82, 1.0
k = lambda *kv: [list(x) for x in kv]
KF = json.load(open(os.environ.get('KEYS7') or os.path.join(HERE, 'attack', 'keys7.json')))
KEYS = KF['keys']   # [t, gx, gy(리그 px, 골반 기준), 자루 각(도), 숙임(rad), 골반 x, 골반 y, 쥔 손(키 표 확인용), 이음]
_g0 = (G - HIP) * 2; _a0 = math.atan2(HU[1], HU[0])
assert abs(KEYS[0][1] - _g0[0]) < 1 and abs(KEYS[0][2] - _g0[1]) < 1 and abs(math.radians(KEYS[0][3]) - _a0) < .01, ('keys7 0 키 = 대기 쥔 점·자루 각이어야 함', _g0, math.degrees(_a0))
EZ = lambda r: r[8] if len(r) > 8 and r[8] else None
PT = lambda i, f=lambda v: v: [[r[0], round(f(r[i]), 4)] + ([EZ(r)] if EZ(r) else []) for r in KEYS]
smash = {
    'kind': 'sword', 'rigid': True, 'orderAlways': True, 'dur': END, 'hitAt': HIT, 'hitStop': .12, 'cancelAt': .78, 'freeArm': True,
    'aDamp': 30, 'standStep': True,
    'ankleRange': [-.45, 1.1], 'legRun': k((0, 0), (SW1 - .01, 0, 'lin'), (SW1 + .02, 1), (HOLD + .04, 1, 'io'), (RET + .045, .12, 'lin'), (RET + .055, 0)),
    'w': k((0, 0, 'io'), (.12, 1), (END - .03, 1, 'io'), (END, 0)),
    'reach': k((0, 0)), 'sN': k((0, 0)),
    'nPiece': k((0, 'gFart'), (.05, 'gFart2'), (SW2, 'gFh'), (KF.get('artBack', RET1), 'gFart2'), (.88, 'gFart')),
    'armIK': k((0, 1)), 'ikSideK': {'N': [[0, 1]]},
    'gx': PT(1), 'gy': PT(2), 'sa': PT(3, math.radians), 'lean': PT(4), 'hipX': PT(5), 'hipY': PT(6),
    'fuA': k((0, 0)),   # 자유 팔 = 방패 뒤 빈 뼈(방패는 상체 숙임을 60% 되돌려 세움 — build follow)
    'flA': k((0, 0)),
    'head': k((0, 0, 'io'), (LIFT, .05, 'io'), (WIND, .06, 'i'), (HIT, -.08, 'o'), (HOLD, -.06, 'io'), (RET + .08, 0)),
    'nearDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, 10), (HOLD, 9, 'io'), (RET + .06, 0)),
    'farDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, 64), (HOLD, 64, 'io'), (RET + .06, 0)),
    'farLift': k((0, 0), (SW1, 0, 'io'), (SW2, 11, 'io'), (HIT, 0), (HOLD, 0, 'io'), (HOLD + .06, 8, 'io'), (RET + .06, 0)),
    'shake': k((0, 0), (HIT, 0, 'lin'), (HIT + .01, 1), (HIT + .12, 0)),
    'face': [[0, 'focus'], [.08, 'effort'], [WIND, 'shout'], [HIT + .14, 'focus'], [RET + .08, None]],
    'fade': {'weapon': k((0, 1), (.06, 1, 'lin'), (.061, 0), (.93, 0, 'lin'), (.931, 1)), 'weaponA': k((0, 0), (.06, 0, 'lin'), (.061, 1), (.93, 1, 'lin'), (.931, 0))},
    'order': [[0, 'drawA']],
}
for _k, _v in (KF.get('tracks') or {}).items(): smash[_k] = _v   # keys7.json 'tracks' = 트랙 통째로 바꿈(시험)
_ov = os.environ.get('SMASH_KEYS')
if _ov: smash.update(json.load(open(_ov)))
# 그리는 순서(공격 내내 한 순서): 먼 팔뚝·도끼·쥔 주먹 = 다리·골반·머리 뒤(12 v1.4) · 다리 = 상체·골반 뒤(v1.1 DHL 21:44 '다리를 옷 뒤로' — 대기 순서와 같은 규칙)
#   먼 윗팔(소매) = 상체 앞(원화: 소매가 튜닉 앞) · 보호대 · 방패 · 가까운 주먹
DRAW_ATK = ['foreFf', 'weapon', 'weaponA', 'foreF', 'legFar', 'legNear', 'torso', 'armF', 'hips', 'head', 'pauldronF', 'armU', 'armL', 'shield', 'fistN']
# 땅 막기(엔진: 날 가운데 점 y > tipDepth 면 자루를 세움): 타격 키 자세의 날 가운데 높이 + 여유 6 — 키대로면 안 걸림, 보간이 넘칠 때만
_hk = [r for r in KEYS if abs(r[0] - HIT) < 1e-6][0]; _Gy = (HIP[1] - O[1]) * 2 + _hk[6] + _hk[2]
TIPD = round(_Gy + math.sin(math.radians(_hk[3])) * TIPU * 2 + 6, 1)
SMASH = {'actions': {'smash': smash}, 'drawA': DRAW_ATK,
         'swordGrip': {'tipDepth': TIPD, 'near': {'upper': 'auFart', 'carry': 'gFart'}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': 0}, 'stretchMax': 1.05, 'shoulderPush': 0},
         'hidden': ['weaponA']}
bones.append(dict(name='weaponA', parent='weapon', pos=[0, 0], part='weaponA'))
print('  smash tipDepth', TIPD, '· 키', len(KEYS))
