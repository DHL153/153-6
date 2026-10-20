# 29 스카이 팔로메 한 손 내려찍기 (9 러스트 v1.1 과 같은 지렛대 휘두르기) — build_sky29.py 안에서 exec
#   엔진 _swordRigid(칼 키 gx·gy·sa) + 손목 마디(wristArm, 3 산초): 원화 손(gF)은 칼에 붙어 같이 돌고, 팔뚝(foreFa)·윗팔(armF)은 길이 고정 두 관절 IK
#   자유 팔(가까운 큰 토시 팔)은 칼을 안 쥠(reach 0) — freeArm 키(fuA·flA)로 균형만
#   키 원본 = attack_keys.json (원화 px·도, tools/presim2.py 로 검사: 손목 꺾임 ±40° · 닿음 · 칼끝 칸 안 · 땅 위)
AK = json.load(open(os.path.join(HERE, 'attack_keys.json'), encoding='utf-8'))
fo_off = np.array(OFF['foreF'], float); fi_off = np.array(OFF['fistF'], float)
ipt = lambda off, p: [round(float(p[0] - off[0]), 1), round(float(p[1] - off[1]), 1)]
ud = (EL_F - WR_F) / np.linalg.norm(EL_F - WR_F)
parts['gF'] = {'src': 'parts/fistF.png', 'pivot': ipt(fi_off, WR_F), 'grip': ipt(fi_off, G), 'elbow': ipt(fi_off, WR_F), 'wrist': ipt(fi_off, WR_F), 'scale': SC,
               'shaftDir': [round(float(UT[0]), 4), round(float(UT[1]), 4)], 'fore': 'foreFa', 'foreBone': 'foreFb', 'foreDir': [round(float(ud[0]), 4), round(float(ud[1]), 4)]}
parts['foreFa'] = {'src': 'parts/foreFc.png', 'pivot': ipt(fo_off, WR_F), 'elbow': ipt(fo_off, EL_F), 'scale': SC}
rig['swordGrip'] = {'tipDepth': 6, 'near': {'upper': 'armF', 'carry': 'gF', 'pieces': []}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': 0}, 'stretchMax': 1.05, 'shoulderPush': 0}
# 그리는 순서: 칼날이 머리 뒤(메기·젖힘·돌아옴) → 머리 위를 넘어 앞으로 오면 칼·먼 팔이 몸 앞(타격)
BASE = ['legFar', 'legNear']
BASE = ['cape'] + BASE
_dA = BASE + ['armF', 'torso', 'skirt', 'pauldronF', 'foreFb', 'weapon', 'armU', 'pauldron', 'head', 'foreF', 'armL']   # 가까운 팔뚝+주먹 맨 앞
rig['drawA0'] = [x for y in [[n] + (['guardArt', 'seamF'] if n == 'weapon' else []) for n in _dA] for x in y]   # 공격 시작·끝(원화 상체·윗팔 + 원화 덧그림)
# 0.04~0.85: 상체 = torsoM(깨끗한 먼 어깨), 먼 윗팔 = armFc(시트) — 윗팔이 상체 뒤라 pauldronF(원화 띠 덧그림)는 안 그림(원화 부스러기를 다시 얹었음, 10-20 10:41)
rig['drawA'] = [n for n in _dA if n != 'pauldronF']
rig['drawStrike'] = BASE + ['armF', 'torso', 'skirt', 'foreFb', 'armU', 'pauldron', 'head', 'weapon', 'foreF', 'armL']
K = AK['keys']
def trk(i, f=lambda v, k: v):   # 키 i 번째 값 → 엔진 트랙 [[t, v, easing]]
    return [[k[0], round(f(k[i], k), 4), k[6] if len(k) > 6 else 'io'] for k in K]
act = {'kind': 'sword', 'rigid': True, 'orderAlways': True, 'dur': 0.9, 'hitAt': 0.45, 'hitStop': 0.07, 'cancelAt': 0.66,
       'w': [[0, 1]], 'reach': [[0, 0]], 'nPiece': [[0, 'gF']], 'nUpper': [[0, 'armF'], [0.04, 'armFc'], [0.85, 'armF']], 'tPiece': [[0, None], [0.04, 'torsoM'], [0.85, None]], 'armIK': [[0, 1]], 'ikSideK': {'N': [[0, 1]]},
       'gx': trk(1, lambda v, k: SC * v), 'gy': trk(2, lambda v, k: SC * (v - k[5])), 'sa': trk(3, lambda v, k: math.radians(v)),
       'lean': trk(4, lambda v, k: math.radians(v)), 'hipY': trk(5, lambda v, k: SC * v),
       'head': [[0, 0], [0.28, -0.06, 'io'], [0.45, 0.05, 'io'], [0.6, 0.04, 'io'], [0.86, 0]],
       'freeArm': True, 'fuA': [[0, 0], [0.28, -0.12, 'io'], [0.45, 0.3, 'o'], [0.6, 0.26, 'io'], [0.86, 0]], 'flA': [[0, 0], [0.28, -0.08, 'io'], [0.45, 0.18, 'o'], [0.6, 0.15, 'io'], [0.86, 0]],
       'face': [[0, 'angry'], [0.12, 'effort'], [0.4, 'shout'], [0.62, 'focus'], [0.82, None]],
       'order': [[0, 'drawA0'], [0.04, 'drawA'], [0.375, 'drawStrike'], [0.72, 'drawA'], [0.85, 'drawA0']]}   # drawA0 = drawA + seamF(원화 날밑·어깨 경계, 칼이 대기 자리일 때만)
rig['actions'] = {'smash': act}
rig['cutHold'] = 0.25   # 스킬 컷인: 칼을 어깨 뒤로 눕혀 멘 힘줌 자세(9 v1.1 과 같은 시각)
