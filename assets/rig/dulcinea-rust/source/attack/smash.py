"""2 러스트 둘시네 — 두 손 내려찍기 (2026-10-19 13:40~, build_dulcinea.py 가 exec)
구조(엔진 _swordRigid, rigid 키 방식 · 산초 손목 마디(wristArm) 방식):
  엔진 'near' 쪽 = 둘시네 먼 팔(망치 쥔 팔: armF 윗팔 · foreF 뼈 = 쥔 주먹 · foreFf 뼈 = 팔뚝) — 처음부터 끝까지 망치를 쥠
  엔진 'far'  쪽 = 둘시네 가까운 팔(armU 윗팔 · armL 뼈 = 쥔 주먹 · armLf 뼈 = 팔뚝) — reach 로 자루를 잡고(0~GRAB) 놓음(REL~)
  주먹은 자루에 그대로 붙고(그림 속 자루 = 망치 자루), 팔뚝은 손목 둘레로 돌아 팔꿈치를 가리킴. 윗팔·팔뚝 길이 고정(2관절 IK) — 늘이지 않음.
  손 순서(10-19 규칙): 자루 끝 쪽 = 먼 손, 쇠 머리 쪽 = 가까운 손(sF > 0).
  시작·끝: 먼 팔은 원화 주먹·원화 팔뚝(gFart·afFart)으로 대기와 같은 자리에서 시작 → 잡는 순간(가장 빠른 때) 시트 손·팔로 바꿈.
입력 전역: def_parts, bones, O_, pc, HIP, SH_N, SH_F, EL_F, WR_F, G, HU, OUT, HERE, shutil, json, np, os
출력: SMASH(rig 에 합칠 dict)"""
AD = os.path.join(HERE, 'attack'); AP = json.load(open(os.path.join(AD, 'pieces.json')))
def apart(n, pivot, scale, **kw):
    shutil.copy(os.path.join(AD, 'pieces', n + '.png'), os.path.join(OUT, 'parts', n + '.png'))
    def_parts[n] = dict(src=f'parts/{n}.png', pivot=[round(float(pivot[0]), 1), round(float(pivot[1]), 1)], scale=scale, **kw)
def unit(v): v = np.array(v, float); return [round(float(x), 4) for x in v / np.linalg.norm(v)]
r1 = lambda p: [round(float(p[0]), 1), round(float(p[1]), 1)]
# ---- 조각 ----
for n in ('auN', 'auF'): j = AP[n]; apart(n, j['top'], j['scale'], elbow=r1(j['bot']))          # 윗팔: pivot = 어깨, elbow = 팔꿈치
for n in ('afN', 'afF'): j = AP[n]; apart(n, j['bot'], j['scale'], elbow=r1(j['top']))          # 팔뚝: pivot = 손목, elbow = 팔꿈치
FD = {'gNv': (-1, 0), 'gNh': (-1, .05), 'gFv': (1, .15), 'gFh': (-.7, -.7)}                       # 쥔 손 그림에서 팔뚝이 나가는 방향(손목 꺾임 0)
for n in ('gNv', 'gNh', 'gFv', 'gFh'):
    j = AP[n]; near = n[1] == 'N'
    apart(n, j['grip'], j['scale'], grip=r1(j['grip']), wrist=r1(j['wrist']), elbow=r1(j['wrist']), shaftDir=[float(v) for v in j['shaftDir']],
          fore='afN' if near else 'afF', foreBone='armLf' if near else 'foreFf', foreDir=unit(FD[n]))
# 먼 팔 시작·끝 = 원화(대기와 같은 그림·같은 자리): 원화 주먹(fistF)을 쥔 손으로, 원화 팔뚝(foreF)을 손목 마디 팔뚝으로, 윗팔은 원화 길이(재킷 밑, 안 보임)
oF, oA = O_['fistF'], O_['foreF']
def_parts['gFart'] = dict(src='parts/fistF.png', pivot=pc(G, oF), scale=2.0, grip=pc(G, oF), wrist=pc(WR_F, oF), elbow=pc(WR_F, oF),
                          shaftDir=[round(float(HU[0]), 4), round(float(HU[1]), 4)], fore='afFart', foreBone='foreFf', foreDir=unit(EL_F - WR_F))
def_parts['afFart'] = dict(src='parts/foreF.png', pivot=pc(WR_F, oA), scale=2.0, elbow=pc(EL_F, oA))
_ju = AP['auF']; _lu = float(np.hypot(_ju['bot'][0] - _ju['top'][0], _ju['bot'][1] - _ju['top'][1]))
def_parts['auFart'] = dict(src='parts/auF.png', pivot=r1(_ju['top']), scale=round(float(np.linalg.norm(EL_F - SH_F)) * 2 / _lu, 4), elbow=r1(_ju['bot']))
# 가까운 팔 잡기·놓기 구간 = 원화 팔(armU 윗팔 + armL 팔뚝·주먹 한 장)을 자루에 붙임 — 주먹 가운데로 자루가 지나감, 자루 방향 = 팔뚝 방향을 시계 방향 90°(쥔 손 시트 1칸과 같은 관계)
_FN = np.array([128.0, 327]); _fd = (EL_N - _FN) / np.linalg.norm(EL_N - _FN)
def_parts['gNart'] = dict(src='parts/armL.png', pivot=pc(EL_N, O_['armL']), scale=2.0, grip=pc(_FN, O_['armL']), wrist=pc(_FN, O_['armL']), elbow=pc(EL_N, O_['armL']),
                          shaftDir=[round(float(-_fd[1]), 4), round(float(_fd[0]), 4)])
bones.append(dict(name='foreFf', parent='torso', pos=[0, 0], part='afF')); bones.append(dict(name='armLf', parent='torso', pos=[0, 0], part='afN'))

# ---- 시간표 (애니 초) ----
GRAB, SWP1, LIFT, WIND0, WIND1, SW1, SW2, HIT, HOLD, REC, SWP2, PRE, REL, END = .08, .105, .13, .22, .30, .335, .365, .40, .62, .70, .80, .84, .87, 1.0   # PRE = 놓기 직전(망치를 몸 앞에 세움 — 잡을 때와 같은 자리)
k = lambda *kv: [list(x) for x in kv]
smash = {
    'kind': 'sword', 'rigid': True, 'orderAlways': True, 'dur': END, 'hitAt': HIT, 'hitStop': .12, 'cancelAt': .74,
    'ankleRange': [-.45, 1.1], 'legRun': k((0, 0), (SW1 - .01, 0, 'lin'), (SW1 + .02, 1), (REC + .04, 1, 'io'), (PRE, 0)),
    'w': k((0, 0, 'io'), (GRAB, 1), (REL, 1, 'io'), (END, 0)),
    'reach': k((0, 0, 'o'), (GRAB - .005, .98, 'lin'), (GRAB, 1), (REL - .005, 1, 'lin'), (REL, .98, 'io'), (END - .02, 0)),
    'sN': k((0, 0)), 'sF': k((0, 82)),
    # 조각: 잡기~SWP1·SWP2~놓기 = 원화 팔(짧음, 대기와 같은 그림) / SWP1~SWP2 = 시트 팔(김) — 바꾸는 순간 = 들어 올림·일어섬 중 가장 빠른 때
    'nPiece': k((0, 'gFart'), (SWP1, 'gFv'), (SW2, 'gFh'), (SWP2, 'gFart')), 'nUpper': k((0, 'auFart'), (SWP1, 'auF'), (SWP2, 'auFart')),
    'fPiece': k((0, 'gNart'), (SWP1, 'gNh'), (SWP2, 'gNart')), 'fUpper': k((0, 'armU'), (SWP1, 'auN'), (SWP2, 'armU')),
    'armIK': k((0, 1)), 'ikSideK': {'N': [[0, 0], [SWP1, 1], [SWP2, 0]], 'F': [[0, 0], [SWP1, 1], [SWP2, 0]]},   # 0 = 쥔 그림의 곧은 팔뚝에 가까운 쪽(원화 팔), 1 = 시계 방향 쪽(머리 위·휘두를 때 팔꿈치 바깥·아래)
    # 망치(먼 손 쥔 점 G, 골반 기준 리그 px)·각도(쇠 머리 방향, 라디안: −π/2 = 위)
    'gx': k((0, 164.6, 'io'), (GRAB, 30), (LIFT, 70, 'io'), (WIND0, -110, 'io'), (WIND1, -120, 'i'), (SW1, 80, 'o'), (SW2, 150), (HIT, 0, 'o'), (HOLD, 0, 'io'), (REC, 10, 'io'), (PRE, 40, 'io'), (REL, 42, 'io'), (END, 164.6)),
    'gy': k((0, -10, 'io'), (GRAB, -40), (LIFT, -400, 'io'), (WIND0, -385, 'io'), (WIND1, -390, 'i'), (SW1, -380, 'o'), (SW2, -210), (HIT, 10, 'o'), (HOLD, 14, 'io'), (REC, 0, 'io'), (PRE, -30, 'io'), (REL, -28, 'io'), (END, -10)),
    'sa': k((0, -.96, 'io'), (GRAB, -.75), (LIFT, -1.66, 'io'), (WIND0, -2.25, 'io'), (WIND1, -2.3, 'i'), (SW1, -1.15, 'o'), (SW2, -.64), (HIT, .4, 'o'), (HOLD, .42, 'io'), (REC, .3, 'io'), (PRE, -.75, 'io'), (REL, -.76, 'io'), (END, -.96)),
    'shNx': k((0, 0, 'io'), (GRAB, 25, 'io'), (LIFT, 0, 'io'), (WIND1, 0, 'io'), (SW1, 40, 'o'), (SW2, 80), (HIT, 70, 'o'), (HOLD, 70, 'io'), (PRE, 25, 'io'), (REL, 25, 'io'), (END, 0)),
    'shNy': k((0, 0, 'io'), (LIFT, -30), (WIND1, -32, 'io'), (SW2, -15, 'io'), (HIT, 0), (PRE, 0)),
    'shFx': k((0, 0)),
    'shFy': k((0, 0, 'io'), (LIFT, -25), (WIND1, -26, 'io'), (SW2, -8, 'io'), (HIT, 0), (PRE, 0)),
    'hipX': k((0, 0, 'io'), (WIND0, -10, 'io'), (WIND1, -12, 'i'), (SW2, 25, 'o'), (HIT, 56, 'o'), (HOLD, 60, 'io'), (PRE, 0)),
    'hipY': k((0, 0, 'io'), (GRAB, 6, 'io'), (WIND0, 14, 'io'), (WIND1, 18, 'i'), (SW2, 30, 'o'), (HIT, 54, 'o'), (HIT + .05, 60, 'io'), (HOLD, 57, 'io'), (PRE, 0)),
    'lean': k((0, 0, 'io'), (WIND0, -.08, 'io'), (WIND1, -.09, 'i'), (SW2, .14, 'o'), (HIT, .32, 'o'), (HOLD, .34, 'io'), (PRE, 0)),
    'head': k((0, 0, 'io'), (WIND0, .04, 'io'), (WIND1, .05, 'i'), (HIT, -.08, 'o'), (HOLD, -.06, 'io'), (PRE, 0)),
    'nearDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, -80), (HOLD, -82, 'io'), (PRE, 0)),
    'farDx': k((0, 0, 'io'), (SW1, 0, 'io'), (HIT, 85), (HOLD, 85, 'io'), (PRE, 0)),
    'farLift': k((0, 0), (SW1, 0, 'io'), (SW2, 14, 'io'), (HIT, 0), (REC, 0, 'io'), (REC + .06, 10, 'io'), (PRE, 0)),
    'shake': k((0, 0), (HIT, 0, 'lin'), (HIT + .01, 1), (HIT + .12, 0)),
    'face': [[0, 'focus'], [GRAB, 'effort'], [WIND1, 'shout'], [HIT + .14, 'focus'], [PRE, None]],
    'fade': {'armLf': k((0, 0), (SWP1 - .001, 0, 'lin'), (SWP1, 1), (SWP2 - .001, 1, 'lin'), (SWP2, 0))},
    'order': [[0, 'drawA']],
}
DRAW_ATK = ['pony', 'legFar', 'legNear', 'hips', 'flapN', 'flapC', 'belt', 'armF', 'foreFf', 'sideF', 'torso', 'head', 'weapon', 'foreF', 'armU', 'pauldron', 'armLf', 'armL']
SMASH = {'actions': {'smash': smash}, 'drawA': DRAW_ATK,
         'swordGrip': {'tipDepth': -150, 'near': {'upper': 'auFart', 'carry': 'gFart'}, 'far': {'upper': 'armU', 'pieces': ['gNart'], 'sPref': 82}, 'stretchMax': 1.05, 'shoulderPush': 0},
         'swapReset': ['armL']}
print('  smash: parts', [n for n in def_parts if n[:2] in ('au', 'af', 'gN', 'gF')], 'temp arms', [n for n in ('auN', 'auF', 'afN', 'afF') if AP[n].get('temp')])
