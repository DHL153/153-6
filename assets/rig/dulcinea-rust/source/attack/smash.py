"""2 러스트 둘시네 — 두 손 내려찍기 v2 (2026-10-19, build_dulcinea.py 가 exec)
DHL 14:24 '팔이 꼬임(1·4) · 팔이 늘어남(2~4) — 절대 안 됨, 기존의 팔이 움직이도록' → 원화 팔만 씀(시트 팔·늘인 팔 없음), 길이 = 원화 길이 고정.
구조(엔진 _swordRigid 키 방식 + 손목 마디 = 3 러스트 산초 방식):
  엔진 'near' 쪽 = 둘시네 먼 팔(왼팔): 원화 주먹(fistF 그림 = gFart, 망치를 쥔 그대로) · 원화 팔뚝(foreF 그림 = afFart, 뼈 foreFf) · 윗팔(재킷 밑, 원화 길이 auFart)
  엔진 'far'  쪽 = 둘시네 가까운 팔(오른팔): 원화 팔(armL 그림)을 같은 틀로 주먹(gNart)·팔뚝(afNart, 뼈 armLf)으로 나눔 + 원화 윗팔(armU)
  주먹은 자루에 붙고, 팔뚝은 손목 둘레로 돌아 팔꿈치를 가리킴. 어깨→팔꿈치→손목 2관절 IK, 길이 원화 고정.
  손은 팔이 닿는 곳까지만 — 손이 안 닿으면 망치 자리를 팔이 닿는 곳으로(11 네온 알론소 24번 규칙). 원화 팔이 짧아 머리 위로 높이 들지 않고 귀 옆에서 감아올림.
  잡기·놓기 = 엔진 opt-in reachW(주먹 자리·각도가 원화 → 자루로; 같은 틀이라 reach 0 = 원화 그대로).
  손 순서(10-19): 자루 끝 쪽 = 먼 손(G), 쇠 머리 쪽 = 가까운 손(sF > 0).
  엔진 어깨 키: shNx·shNy = 가까운 어깨(armU+어깨갑), shFx·shFy = 먼 어깨(armF, 몸 뒤라 안 보임).
입력 전역: def_parts, bones, O_, pc, HIP, SH_N, EL_N, SH_F, EL_F, WR_F, G, HU, OUT, W, HERE, json, np, os, cv2, Image, ImageDraw
출력: SMASH(rig 에 합칠 dict)"""
def unit(v): v = np.array(v, float); return [round(float(x), 4) for x in v / np.linalg.norm(v)]
# ---- 공 손목(3 러스트 산초 v2 '공 손목 관 팔' 방식): 주먹 = 장갑만, 손목 키 = 쥔 점(주먹 가운데) — 팔뚝 끝을 장갑 밑 가운데까지 이어 그려서
#      팔뚝이 어느 각도로 들어와도 장갑 밑으로 들어감(손목이 꺾인 '팔 없는' 모양이 안 생김). 팔 길이 = 원화 어깨→팔꿈치→주먹 가운데 그대로.
def capsule(a, o, p0, p1, col):   # 원화 좌표 p0→p1 을 a(틀 o) 안에 팔뚝 굵기로 이어 그림 — 이미 불투명한 곳은 그대로
    ax = (p1 - p0) / np.linalg.norm(p1 - p0); hh, ww = a.shape[:2]; yy, xx = np.mgrid[0:hh, 0:ww]; X, Y = xx + o[0], yy + o[1]
    near0 = (np.abs((X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1]) < 4) & (a[..., 3] > 200)
    hw = max(6.0, float(np.abs((X - p0[0]) * -ax[1] + (Y - p0[1]) * ax[0])[near0].max()) - 1.5)   # 손목 굵기의 반(외곽선 안쪽)
    t = (X - p0[0]) * ax[0] + (Y - p0[1]) * ax[1]; d = np.abs((X - p0[0]) * -ax[1] + (Y - p0[1]) * ax[0])
    m = (t >= -2) & (t <= np.linalg.norm(p1 - p0) + 2) & (d <= hw) & ~(a[..., 3] > 200)
    a[..., :3][m] = col; a[..., 3][m] = 255; return a, round(hw, 1)
# 가까운 팔: 원화 armL 그림을 같은 틀(같은 크기·같은 자리)로 장갑 주먹(gNart)·팔뚝(afNart) 둘로 — 같은 틀이라 reachW 잡기 시작(reach 0) = 원화 그대로
_A = np.array(Image.open(os.path.join(W, 'armLArt.png')).convert('RGBA')); oL = O_['armL']; _h, _w = _A.shape[:2]
_pm = Image.new('L', (_w, _h), 0)
ImageDraw.Draw(_pm).polygon([(x - oL[0], y - oL[1]) for x, y in [(98, 297), (126, 297), (130, 306), (138, 314), (150, 311), (160, 318), (162, 345), (150, 360), (120, 364), (98, 350)]], fill=255)
_hv = cv2.cvtColor(np.ascontiguousarray(_A[..., :3]), cv2.COLOR_RGB2HSV); _band = (_hv[..., 1] < 70) & (_hv[..., 2] > 140)   # 손목 붕대(크림) = 팔뚝 쪽
_fist = (np.array(_pm) > 0) & ~_band & (_A[..., 3] > 0)
_n, _lb, _st, _ = cv2.connectedComponentsWithStats(_fist.astype(np.uint8), 8); _fist = _lb == (1 + int(np.argmax(_st[1:, cv2.CC_STAT_AREA])))   # 장갑 덩어리 하나만(붕대 부스러기 빼기)
_fore = (_A[..., 3] > 0) & ~_fist
WR2 = np.array([133.0, 309.0]); GRIP_N = np.array([130.0, 332.0])   # 손목(붕대·장갑 사이) · 쥔 점(주먹 가운데 = 공 손목)
_F = _A.copy(); _F[..., 3] = np.where(_fist, _A[..., 3], 0)
_R = _A.copy(); _R[..., 3] = np.where(_fore, _A[..., 3], 0)
_R, _hwN = capsule(_R, oL, WR2, GRIP_N, np.median(_A[..., :3][_band & _fore], 0).astype(np.uint8))
Image.fromarray(_F).save(os.path.join(OUT, 'parts', 'gNart.png')); Image.fromarray(_R).save(os.path.join(OUT, 'parts', 'afNart.png'))
def_parts['gNart'] = dict(src='parts/gNart.png', pivot=pc(GRIP_N, oL), scale=2.0, grip=pc(GRIP_N, oL), wrist=pc(GRIP_N, oL), elbow=pc(GRIP_N, oL),
                          shaftDir=unit([-(EL_N - WR2)[1], (EL_N - WR2)[0]]), fore='afNart', foreBone='armLf', foreDir=unit(EL_N - GRIP_N))   # 자루 = 손목→팔꿈치 방향을 시계 방향 90°
def_parts['afNart'] = dict(src='parts/afNart.png', pivot=pc(GRIP_N, oL), scale=2.0, elbow=pc(EL_N, oL))
# 먼 팔: 원화 주먹(fistF, 망치를 쥔 그대로) · 원화 팔뚝(foreF)을 주먹 가운데(G)까지 이어 그린 것 — 대기 = 원화 그대로(이은 곳은 주먹·자루 밑)
oF, oA = O_['fistF'], O_['foreF']
_fa = np.array(Image.open(os.path.join(W, 'foreFArt.png')).convert('RGBA')); _cv = np.zeros((512, 512, 4), np.uint8); _cv[int(oA[1]):int(oA[1]) + _fa.shape[0], int(oA[0]):int(oA[0]) + _fa.shape[1]] = _fa
_wr = (np.hypot(*(np.mgrid[0:512, 0:512][::-1] - WR_F[:, None, None])) < 7) & (_cv[..., 3] > 200)
_cv, _hwF = capsule(_cv, np.zeros(2), WR_F, G, np.median(_cv[..., :3][_wr], 0).astype(np.uint8))
_ys, _xs = np.nonzero(_cv[..., 3] > 0); oA2 = np.array([_xs.min() - 2, _ys.min() - 2], float)
Image.fromarray(_cv[int(oA2[1]):_ys.max() + 3, int(oA2[0]):_xs.max() + 3]).save(os.path.join(OUT, 'parts', 'afFart.png'))
def_parts['gFart'] = dict(src='parts/fistF.png', pivot=pc(G, oF), scale=2.0, grip=pc(G, oF), wrist=pc(G, oF), elbow=pc(G, oF),
                          shaftDir=[round(float(HU[0]), 4), round(float(HU[1]), 4)], fore='afFart', foreBone='foreFf', foreDir=unit(EL_F - G))
def_parts['afFart'] = dict(src='parts/afFart.png', pivot=pc(G, oA2), scale=2.0, elbow=pc(EL_F, oA2))
_ua = def_parts['armU']; _lu = float(np.hypot(_ua['elbow'][0] - _ua['pivot'][0], _ua['elbow'][1] - _ua['pivot'][1]))
def_parts['auFart'] = dict(src='parts/armU.png', pivot=_ua['pivot'], scale=round(float(np.linalg.norm(EL_F - SH_F)) / _lu * 2, 4), elbow=_ua['elbow'])   # 먼 윗팔(몸 뒤, 안 보임) — 원화 길이
bones.append(dict(name='foreFf', parent='torso', pos=[0, 0], part='afFart')); bones.append(dict(name='armLf', parent='torso', pos=[0, 0], part='afNart'))
print('  smash 공 손목 팔뚝 굵기 반(원화 px): near', _hwN, 'far', _hwF)
_L = lambda *p: round(float(sum(np.linalg.norm(p[i + 1] - p[i]) for i in range(len(p) - 1)) * 2), 1)
print('  smash 원화 팔 길이(리그, 어깨→팔꿈치→주먹 가운데): near', _L(SH_N, EL_N, GRIP_N), 'far', _L(SH_F, EL_F, G))

# ---- 시간표 (애니 초) ----
#   먼 손 혼자 망치를 얼굴 오른쪽으로 들어 올리며 쇠 머리를 머리 위로 넘김 → 가까운 손이 올라와 머리 위에서 자루를 잡음(감아올림, 멈칫)
#   → 손이 앞으로 넘어오며 망치가 머리 위를 지나 휘두름(손이 얼굴 앞을 지나는 건 2프레임) → 타격(손 배 앞, 쇠 머리 땅) → 버팀 → 가까운 손 놓음 → 먼 손이 대기 자리로
#   자세(G·각도)는 원화 팔 길이·공 손목·팔꿈치 방향(굽힘)으로 풀어서 고름(팔 늘임 1.00, 손목에 팔뚝이 들어가는 각 ±47° 안)
LIFT, GRAB0, GRAB, WIND1, SW1, SW2, HIT, HOLD, REL0, REL, END = .09, .05, .17, .28, .325, .355, .40, .60, .63, .74, 1.0
k = lambda *kv: [list(x) for x in kv]
#        이름:  (시각, gx, gy, 각도, sF(가까운 손 = 먼 손에서 쇠 머리 쪽으로), 보간)
POSE = [(0, 164.6, -10, -.96, 82, 'io'), (LIFT, 164, -264, -2.4, 82, 'io'), (GRAB, -52, -324, -3.1, 50, 'io'), (WIND1, -52, -328, -3.15, 50, 'i'),
        (SW1, 0, -316, -3.0, 48, None), (SW2, 48, -28, -1.0, 36, 'o'), (HIT, 40, -6, .4, 26, 'o'), (HOLD, 40, -4, .42, 26, 'io'), (REL, 70, -30, -.2, 26, 'io'), (END - .03, 164.6, -10, -.96, 82, None)]
PT = lambda i: [[p[0], p[i]] + ([p[5]] if p[5] else []) for p in POSE]
smash = {
    'kind': 'sword', 'rigid': True, 'orderAlways': True, 'dur': END, 'hitAt': HIT, 'hitStop': .12, 'cancelAt': .76, 'reachW': True,
    'ankleRange': [-.45, 1.1], 'legRun': k((0, 0), (SW1 - .01, 0, 'lin'), (SW1 + .02, 1), (HOLD + .04, 1, 'io'), (REL + .045, .12, 'lin'), (REL + .055, 0)),   # 서 있는 원화 다리 ↔ 시트 다리 바뀜(fade .05~.1)은 한 프레임에
    'w': k((0, 0, 'io'), (LIFT, 1), (END - .03, 1, 'io'), (END, 0)),
    'reach': k((0, 0), (GRAB0, 0, 'io'), (GRAB, 1), (REL0, 1, 'io'), (REL, 0)),
    'sN': k((0, 0)), 'sF': PT(4),
    'nPiece': k((0, 'gFart')), 'nUpper': k((0, 'auFart')), 'fPiece': k((0, 'gNart')), 'fUpper': k((0, 'armU')),
    'armIK': k((0, 1)), 'ikSideK': {'N': [[0, 0]], 'F': [[0, 0]]},
    'gx': PT(1), 'gy': PT(2), 'sa': PT(3),   # 망치: 먼 손 쥔 점 G(골반 기준 리그 px) · 자루 각도(쇠 머리 방향, 라디안: −π/2 = 위)
    'shNx': k((0, 0, 'io'), (WIND1, 0, 'io'), (SW1, 10, 'io'), (SW2, 25, 'o'), (HIT, 40, 'o'), (HOLD, 40, 'io'), (REL + .06, 0)),   # 가까운 어깨(armU+어깨갑) — 몸을 앞으로 틂
    'shNy': k((0, 0, 'io'), (GRAB, -24), (WIND1, -26, 'io'), (SW2, -12, 'io'), (HIT, 0), (END, 0)),
    'shFx': k((0, 0, 'io'), (LIFT, -20, 'io'), (GRAB, -45), (WIND1, -48, 'io'), (SW2, -10, 'io'), (HIT, 0), (END, 0)),   # 먼 어깨(armF, 몸 뒤라 안 보임)
    'shFy': k((0, 0, 'io'), (LIFT, -15, 'io'), (GRAB, -25), (WIND1, -26, 'io'), (SW2, -8, 'io'), (HIT, 0), (END, 0)),
    'hipX': k((0, 0, 'io'), (GRAB, -10, 'io'), (WIND1, -12, 'i'), (SW2, 25, 'o'), (HIT, 56, 'o'), (HOLD, 60, 'io'), (REL + .08, 0)),
    'hipY': k((0, 0, 'io'), (GRAB, 14, 'io'), (WIND1, 18, 'i'), (SW2, 26, 'o'), (HIT, 40, 'o'), (HIT + .05, 46, 'io'), (HOLD, 44, 'io'), (REL + .08, 0)),
    'lean': k((0, 0, 'io'), (GRAB, -.08, 'io'), (WIND1, -.10, 'i'), (SW1, -.02), (SW2, .14, 'o'), (HIT, .32, 'o'), (HOLD, .34, 'io'), (REL + .08, 0)),
    'head': k((0, 0, 'io'), (GRAB, .04, 'io'), (WIND1, .05, 'i'), (HIT, -.08, 'o'), (HOLD, -.06, 'io'), (REL + .08, 0)),
    'nearDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, -80), (HOLD, -82, 'io'), (REL + .06, 0)),
    'farDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, 85), (HOLD, 85, 'io'), (REL + .06, 0)),
    'farLift': k((0, 0), (SW1, 0, 'io'), (SW2, 14, 'io'), (HIT, 0), (HOLD, 0, 'io'), (HOLD + .06, 10, 'io'), (REL + .06, 0)),
    'shake': k((0, 0), (HIT, 0, 'lin'), (HIT + .01, 1), (HIT + .12, 0)),
    'face': [[0, 'focus'], [LIFT, 'effort'], [WIND1, 'shout'], [HIT + .14, 'focus'], [REL + .08, None]],
    'fade': {'armLf': k((0, 0), (GRAB0, 0, 'lin'), (GRAB0 + .001, 1), (REL - .001, 1, 'lin'), (REL, 0))},
    # 그리는 순서: 대기(먼 팔뚝 몸 뒤) → 공격 동안(먼 팔뚝 몸 앞·머리 뒤 — 휘두를 때 먼 팔꿈치가 볼 앞에 오지 않게) → 돌아옴(대기 순서) — 바꾸는 순간은 움직일 때
    'order': [[0, 'drawA'], [.03, 'drawL'], [.70, 'drawA']],
}
_ov = os.environ.get('SMASH_KEYS')   # 맞추기용: 키 덮어쓰기 JSON
if _ov: smash.update(json.load(open(_ov)))
# sideF(재킷 오른쪽 자락을 20px 늘인 조각)는 먼 팔이 올라가면 몸 옆에 네모 덩어리로 떠 보여서(10-19 15:20) 공격 순서에서 뺌
DRAW_ATK = ['pony', 'legFar', 'legNear', 'hips', 'flapN', 'flapC', 'belt', 'armF', 'foreFf', 'torso', 'head', 'weapon', 'foreF', 'armU', 'pauldron', 'armLf', 'armL']
DRAW_LIFT = ['pony', 'legFar', 'legNear', 'hips', 'flapN', 'flapC', 'belt', 'armF', 'torso', 'foreFf', 'head', 'weapon', 'foreF', 'armU', 'pauldron', 'armLf', 'armL']   # 들어 올림·머리 위: 먼 팔뚝이 몸 앞, 머리 뒤
SMASH = {'actions': {'smash': smash}, 'drawA': DRAW_ATK, 'drawL': DRAW_LIFT,
         'swordGrip': {'tipDepth': -205, 'near': {'upper': 'auFart', 'carry': 'gFart'}, 'far': {'upper': 'armU', 'pieces': ['gNart'], 'sPref': 82}, 'stretchMax': 1.05, 'shoulderPush': 0},
         'swapReset': ['armL']}
