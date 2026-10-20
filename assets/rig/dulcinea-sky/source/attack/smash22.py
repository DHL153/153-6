"""22 스카이 둘시네 — 한 손 내려찍기 (12 네온 v1.4 attack/smash12.py 를 옮김, 10-20 15:3x 시험판 p1). build_sky22.py 가 exec.
같은 것: 시간표·자루 각(sa)·몸(골반·숙임·머리·다리)·가까운 팔 흔들기·얼굴·망치 바꿈(weapon→weaponA)·그리는 순서(공격 내내 drawA 하나 = 손·망치가 다리·머리 뒤)
바꾼 것: ①쥔 점·먼 어깨 키 = 12 키를 22 몸으로 옮김(tools/keys22.py — 12 팔과 22 팔 길이가 같게 팔꿈치를 풀어 둠: 같은 팔 모양 = 펴짐·손목 꺾임 같음)
  ②먼 팔 조각: 팔뚝 = 원화 접은 소매 끝(크림)·살 팔뚝 + 장갑 색 공 손목(주먹 밑), 팔꿈치 끝은 build 에서 이어 그린 둥근 소매 끝 그대로(12 의 살색 팔꿈치 덮개 없음)
     윗팔 auFart = 크림 소매 관(12 는 남색 소매 + 살) ③gFh = 시트 19칸(tools/gfh22.py) ④천자락·포니테일을 그리는 순서에 더함 ⑤tipDepth = 쇠 머리 크기로(12 와 같은 여유)
입력 전역: def_parts, bones, O_, pc, HIP, SH_N, EL_N, SH_F, EL_F, WR_F, G, HU, OUT, W, HERE, json, np, os, cv2, Image, ImageDraw, own, CREAM, CUFF_HW, HEAD_HALF
출력: SMASH(rig 에 합칠 dict)"""
def unit(v): v = np.array(v, float); return [round(float(x), 4) for x in v / np.linalg.norm(v)]
def capsule(a, o, p0, p1, col, hwmax=None):   # 원화 좌표 p0→p1 을 a(틀 o) 안에 팔뚝 굵기로 이어 그림 — 이미 불투명한 곳은 그대로
    ax = (p1 - p0) / np.linalg.norm(p1 - p0); hh, ww = a.shape[:2]; yy, xx = np.mgrid[0:hh, 0:ww]; X, Y = xx + o[0], yy + o[1]
    near0 = (np.abs((X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1]) < 4) & (a[..., 3] > 200)
    hw = max(6.0, float(np.abs((X - p0[0]) * -ax[1] + (Y - p0[1]) * ax[0])[near0].max()) - 1.5)
    if hwmax: hw = min(hw, hwmax)
    t = (X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1]; d = np.abs((X - p0[0]) * -ax[1] + (Y - p0[1]) * ax[0])
    m = (t >= -2) & (t <= np.linalg.norm(p1 - p0) + 2) & (d <= hw) & ~(a[..., 3] > 200)
    a[..., :3][m] = col; a[..., 3][m] = 255; return a, round(hw, 1)
# 먼 팔: 원화 주먹(fistF, 망치를 쥔 그대로) · 원화 팔뚝(foreF: 접은 소매 끝 + 살 팔뚝)을 주먹 가운데(G)까지 장갑 색으로 이어 그린 것 — 대기 = 원화 그대로(이은 곳은 주먹·자루 밑)
oF, oA = O_['fistF'], O_['foreF']
_fa = np.array(Image.open(os.path.join(W, 'foreFArt.png')).convert('RGBA')); _cv = np.zeros((512, 512, 4), np.uint8); _cv[int(oA[1]):int(oA[1]) + _fa.shape[0], int(oA[0]):int(oA[0]) + _fa.shape[1]] = _fa
_gl = own['fistF'] & ~SKIN & (LUM > 45) & (LUM < 150)   # 장갑 가죽 갈색
_GLC = np.median(RA[..., :3][_gl], 0).astype(np.uint8)
_cv, _hwF = capsule(_cv, np.zeros(2), WR_F, G, _GLC, hwmax=float(os.environ.get('HW_WRIST', 10)))
_n_, _lb_, _st_, _ = cv2.connectedComponentsWithStats((_cv[..., 3] > 10).astype(np.uint8), 8)
_cv[..., 3] = np.where(_lb_ == 1 + int(np.argmax(_st_[1:, cv2.CC_STAT_AREA])), _cv[..., 3], 0)   # 큰 덩어리만
_ys, _xs = np.nonzero(_cv[..., 3] > 0); oA2 = np.array([_xs.min() - 2, _ys.min() - 2], float)
Image.fromarray(_cv[int(oA2[1]):_ys.max() + 3, int(oA2[0]):_xs.max() + 3]).save(os.path.join(OUT, 'parts', 'afFart.png'))
def_parts['gFart'] = dict(src='parts/fistF.png', pivot=pc(G, oF), scale=2.0, grip=pc(G, oF), wrist=pc(G, oF), elbow=pc(G, oF),
                          shaftDir=[round(float(HU[0]), 4), round(float(HU[1]), 4)], fore='afFart', foreBone='foreFf', foreDir=unit(EL_F - G))
def_parts['afFart'] = dict(src='parts/afFart.png', pivot=pc(G, oA2), scale=2.0, elbow=pc(EL_F, oA2))
def_parts['afFart2'] = dict(def_parts['afFart'])                     # 22: 팔꿈치 끝은 이미 둥근 소매 끝(build) — 공격용 팔뚝 = 같은 그림(엔진 nPiece 이름만 12 와 같게)
def_parts['gFart2'] = dict(def_parts['gFart'], fore='afFart2')
# 먼 윗팔 auFart: 원화에선 조끼 뒤라 그림이 없음 → 크림 소매 관(둥근 두 끝 + 원화 굵기 외곽선 + 아래 그늘), 길이 = 원화 어깨→팔꿈치, 굵기 = 먼 소매 끝과 같게
_LU = float(np.linalg.norm(EL_F - SH_F)); _r = 12.0; _Wd, _Hd = int(_LU + 2 * _r + 6), int(2 * _r + 6)   # 소매 관 반지름 12(가까운 소매 윗팔 굵기)
_uy, _ux = np.mgrid[0:_Hd, 0:_Wd].astype(np.float32); _p0 = np.array([_r + 3, _r + 3]); _p1 = _p0 + np.array([_LU, 0])
_tt = np.clip((_ux - _p0[0]) / _LU, 0, 1); _dd = np.hypot(_ux - (_p0[0] + _tt * _LU), _uy - _p0[1])
_au = np.zeros((_Hd, _Wd, 4), np.uint8); _in = _dd <= _r
_CRC = np.median(RA[..., :3][(own['foreF'] | own['upF'] | own['armU']) & CREAM], 0).astype(np.uint8)
_au[..., :3][_in] = _CRC; _au[..., 3][_in] = 255
_sh = _in & (_uy > _p0[1] + _r * .35); _au[..., :3][_sh] = (_au[..., :3][_sh] * np.array([.9, .84, .8])).astype(np.uint8)   # 아래 그늘(따뜻한 색)
_au[..., :3][_in & (_dd > _r - 1.8)] = np.array([34, 26, 22], np.uint8)
Image.fromarray(_au).save(os.path.join(OUT, 'parts', 'auFart.png'))
def_parts['auFart'] = dict(src='parts/auFart.png', pivot=[round(float(_p0[0]), 1), round(float(_p0[1]), 1)], scale=2.0, elbow=[round(float(_p1[0]), 1), round(float(_p1[1]), 1)])
bones.append(dict(name='foreFf', parent='torso', pos=[0, 0], part='afFart'))
print('  smash 공 손목 굵기 반(원화 px)', _hwF, '· 장갑 색', _GLC.tolist(), '· 소매 색', _CRC.tolist(), '· 윗팔 관 반지름', round(_r, 1))
_L = lambda *p: round(float(sum(np.linalg.norm(p[i + 1] - p[i]) for i in range(len(p) - 1)) * 2), 1)
print('  smash 원화 먼 팔 길이(리그, 어깨→팔꿈치→주먹 가운데):', _L(SH_F, EL_F, G))
# 휘두름~버팀 먼 손 = 시트 19칸 '자루 따라 쥔 손'(gFh, tools/gfh22.py)
AD = os.environ.get('GFH_DIR') or os.path.join(HERE, 'attack'); AP = json.load(open(os.path.join(AD, 'pieces.json'))); import shutil as _shu
_j = AP['gFh']; _shu.copy(os.path.join(AD, 'pieces', 'gFh.png'), os.path.join(OUT, 'parts', 'gFh.png')); _g = [round(float(_j['grip'][0]), 1), round(float(_j['grip'][1]), 1)]
def_parts['gFh'] = dict(src='parts/gFh.png', pivot=_g, scale=_j['scale'], grip=_g, wrist=_g, elbow=_g, shaftDir=[float(v) for v in _j['shaftDir']],
                        fore='afFart2', foreBone='foreFf', foreDir=unit(np.array(_j['wrist']) - np.array(_j['grip'])))

# ---- 시간표 (애니 초) — 12 와 같음 ----
LIFT, WIND, SW1, SW2, HIT, HOLD, RET1, RET, END = .18, .27, .32, .36, .40, .58, .68, .82, 1.0
k = lambda *kv: [list(x) for x in kv]
_g0 = (G - HIP) * 2; _a0 = math.atan2(HU[1], HU[0]); _g0x, _g0y = round(float(_g0[0]), 1), round(float(_g0[1]), 1); _a0 = round(_a0, 3)   # 22 대기 쥔 점·자루 각
POSE = [(0, _g0x, _g0y, _a0, 'io'), (LIFT, 190, -268, -2.6, 'io'), (WIND, 186, -272, -2.65, 'i'), (SW1, 260, -212, -1.8, None), (SW2, 328, -132, -1.1, 'o'),
        (HIT, 216, 0, .4, 'o'), (HOLD, 214, 2, .42, 'io'), (RET1, 313, -23, -.2, 'io'), (RET, 175, -60, -.5, 'io'), (END - .03, _g0x, _g0y, _a0, None)]
SH0 = [round(float(v), 1) for v in (SH_F - HIP) * 2]                 # 대기 먼 어깨(상체 기준, 리그) — 22 (88,−134) · 12 (54,−114)
_KB = os.path.join(HERE, 'attack', 'keys22b.json')
if os.path.exists(_KB) and not os.environ.get('K12RAW'):
    K22B = json.load(open(_KB))['keys']; print('  smash keys22b.json 어깨·쥔 점', len(K22B), '키')
else:   # 처음 한 번: 12 v1.4 keys12b 를 대기 어깨 차이만큼 그대로 옮김(상체 회전 무시 근사) — tools/keys22.py 가 엔진에서 재서 keys22b.json 을 만듦
    _k12 = json.load(open(os.path.join(HERE, '..', '..', 'dulcinea-neon', 'source', 'attack', 'keys12b.json')))['keys']; _d = (SH0[0] - 54.0, SH0[1] + 114.0)
    K22B = {t: {'shL': [v['shL'][0] + _d[0], v['shL'][1] + _d[1]], 'G': [v['G'][0] + _d[0], v['G'][1] + _d[1]]} for t, v in _k12.items()}
    print('  smash 12 keys12b 근사 옮김(어깨 차이', _d, ')')
POSE = [(p[0], *K22B[f'{p[0]:.2f}']['G'], p[3], p[4]) if f'{p[0]:.2f}' in K22B else p for p in POSE]
# 돌아옴(RET1·RET, 원화 주먹 gFart2) 자루 각 −10°: 22 원화 주먹은 팔뚝↔자루 각이 12 보다 10° 작음(−107.8° vs −117.8°) → 12 와 같은 팔·자루 각이면 손목이 −54°(기준 ±47, 12 는 −44)
SA_RET = float(os.environ.get('SA_RET', -0.175)); POSE = [(p[0], p[1], p[2], round(p[3] + SA_RET, 3), p[4]) if p[0] in (RET1, RET) else p for p in POSE]
PT = lambda i: [[p[0], p[i]] + ([p[4]] if p[4] else []) for p in POSE]
def _shk(j):   # keys22b 의 어깨(상체 기준) → shFx·shFy 키(POSE 와 같은 시각·같은 보간)
    return [[p[0], (round(K22B[f'{p[0]:.2f}']['shL'][j] - SH0[j], 1) if f'{p[0]:.2f}' in K22B else 0)] + ([p[4]] if p[4] else []) for p in POSE]
smash = {
    'kind': 'sword', 'rigid': True, 'orderAlways': True, 'dur': END, 'hitAt': HIT, 'hitStop': .12, 'cancelAt': .78, 'freeArm': True,
    'aDamp': 30, 'standStep': True,
    'ankleRange': [-.45, 1.1], 'legRun': k((0, 0), (SW1 - .01, 0, 'lin'), (SW1 + .02, 1), (HOLD + .04, 1, 'io'), (RET + .045, .12, 'lin'), (RET + .055, 0)),
    'w': k((0, 0, 'io'), (.12, 1), (END - .03, 1, 'io'), (END, 0)),
    'reach': k((0, 0)), 'sN': k((0, 0)),
    'nPiece': k((0, 'gFart'), (.05, 'gFart2'), (SW2, 'gFh'), (RET1, 'gFart2'), (.88, 'gFart')),
    'armIK': k((0, 1)), 'ikSideK': {'N': [[0, 1]]},
    'gx': PT(1), 'gy': PT(2), 'sa': PT(3), 'shFx': _shk(0), 'shFy': _shk(1),
    'fuA': k((0, 0, 'io'), (LIFT, -.5, 'io'), (WIND, -.55, 'i'), (SW2, .1, 'o'), (HIT, .5, 'o'), (HOLD, .45, 'io'), (RET + .08, 0)),
    'flA': k((0, 0, 'io'), (LIFT, -.6, 'io'), (WIND, -.65, 'i'), (SW2, -.1, 'o'), (HIT, .15, 'o'), (HOLD, .12, 'io'), (RET + .08, 0)),
    'hipX': k((0, 0, 'io'), (LIFT, -10, 'io'), (WIND, -12, 'i'), (SW2, 25, 'o'), (HIT, 56, 'o'), (HOLD, 60, 'io'), (RET + .08, 0)),
    'hipY': k((0, 0, 'io'), (LIFT, 10, 'io'), (WIND, 14, 'i'), (SW2, 24, 'o'), (HIT, 40, 'o'), (HIT + .05, 46, 'io'), (HOLD, 44, 'io'), (RET + .08, 0)),
    'lean': k((0, 0, 'io'), (LIFT, -.12, 'io'), (WIND, -.13, 'i'), (SW1, -.02), (SW2, .14, 'o'), (HIT, .30, 'o'), (HOLD, .32, 'io'), (RET + .08, 0)),
    'head': k((0, 0, 'io'), (LIFT, .05, 'io'), (WIND, .06, 'i'), (HIT, -.08, 'o'), (HOLD, -.06, 'io'), (RET + .08, 0)),
    'nearDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, 15), (HOLD, 13, 'io'), (RET + .06, 0)),   # (DHL 16:57 ① 뒷다리 덜 뻗게) 12 −80 · −82 → v1.1 −50 · −52 → v1.2 +15 · +13: 타격 때 골반이 앞으로 56 나가고 hipY 40 이라 −50 도 뒷다리가 다 펴졌음(엉덩이→발목 = 다리 길이 .99, 엔진이 골반을 내려 맞춤) — 뒷발을 15 앞으로 디뎌 무릎이 조금 굽음(펴짐 약 .92)
    'farDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, 85), (HOLD, 85, 'io'), (RET + .06, 0)),
    'farLift': k((0, 0), (SW1, 0, 'io'), (SW2, 14, 'io'), (HIT, 0), (HOLD, 0, 'io'), (HOLD + .06, 10, 'io'), (RET + .06, 0)),
    'shake': k((0, 0), (HIT, 0, 'lin'), (HIT + .01, 1), (HIT + .12, 0)),
    'face': [[0, 'focus'], [.08, 'effort'], [WIND, 'shout'], [HIT + .14, 'focus'], [RET + .08, None]],
    'fade': {'weapon': k((0, 1), (.06, 1, 'lin'), (.061, 0), (.93, 0, 'lin'), (.931, 1)), 'weaponA': k((0, 0), (.06, 0, 'lin'), (.061, 1), (.93, 1, 'lin'), (.931, 0))},
    'order': [[0, 'drawA']],
}
_ov = os.environ.get('SMASH_KEYS')
if _ov: smash.update(json.load(open(_ov)))
# 그리는 순서(12 v1.4 규칙 ②③ 공격 = 손·망치가 머리·다리 뒤, 공격 내내 한 순서): 천자락 맨 뒤 · 먼 윗팔·팔뚝·망치·쥔 주먹 = 다리·골반·상체·머리 뒤 · 포니테일 = 망치 앞 · 가까운 팔뚝 = 소매 뒤
DRAW_ATK = ['flapF', 'armF', 'foreFf', 'weapon', 'weaponA', 'foreF', 'legFar', 'legNear', 'hips', 'pony', 'torso', 'head', 'armL', 'armU', 'pauldron']
TIPD = -round(2 * HEAD_HALF * math.cos(.4) + 32)                     # 12: 쇠 머리 반 길이 94 → −205(같은 여유 32)
SMASH = {'actions': {'smash': smash}, 'drawA': DRAW_ATK,
         'swordGrip': {'tipDepth': TIPD, 'near': {'upper': 'auFart', 'carry': 'gFart'}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': 0}, 'stretchMax': 1.05, 'shoulderPush': 0},
         'hidden': ['weaponA']}
bones.append(dict(name='weaponA', parent='weapon', pos=[0, 0], part='weaponA'))
print('  smash tipDepth', TIPD)
