# 19 네온 팔로메 한 손 내려찍기 = 9 러스트 v1.1 과 같은 지렛대 휘두르기·그리는 순서(9 attack_palome.py 복사) — build_neon19.py 안에서 exec
#   엔진 _swordRigid(칼 키 gx·gy·sa) + 손목 마디(wristArm, 3 산초): 원화 손(gF)은 칼에 붙어 같이 돌고, 팔뚝(foreFa)·윗팔(armF)은 길이 고정 두 관절 IK
#   자유 팔(가까운 큰 토시 팔)은 칼을 안 쥠(reach 0) — freeArm 키(fuA·flA)로 균형만
#   키 원본 = attack_keys.json (원화 px·도, tools/presim2.py 로 검사: 손목 꺾임 ±40° · 닿음 · 칼끝 칸 안 · 땅 위)
AK = json.load(open(os.path.join(HERE, 'attack_keys.json'), encoding='utf-8'))
fo_off = np.array(OFF['foreF'], float); fi_off = np.array(OFF['fistF'], float)
ipt = lambda off, p: [round(float(p[0] - off[0]), 1), round(float(p[1] - off[1]), 1)]
ud = (EL_F - WR_F) / np.linalg.norm(EL_F - WR_F)
parts['gF'] = {'src': 'parts/fistF.png', 'pivot': ipt(fi_off, WR_F), 'grip': ipt(fi_off, G), 'elbow': ipt(fi_off, WR_F), 'wrist': ipt(fi_off, WR_F), 'scale': SC,
               'shaftDir': [round(float(UT[0]), 4), round(float(UT[1]), 4)], 'fore': 'foreFa', 'foreBone': 'foreFb', 'foreDir': [round(float(ud[0]), 4), round(float(ud[1]), 4)]}
parts['foreFa'] = {'src': 'parts/foreF.png', 'pivot': ipt(fo_off, WR_F), 'elbow': ipt(fo_off, EL_F), 'scale': SC}
rig['swordGrip'] = {'tipDepth': 6, 'near': {'upper': 'armF', 'carry': 'gF', 'pieces': []}, 'far': {'upper': 'armU', 'pieces': ['armL'], 'sPref': 0}, 'stretchMax': 1.05, 'shoulderPush': 0}
# 그리는 순서: 칼날이 머리 뒤(메기·젖힘·돌아옴) → 머리 위를 넘어 앞으로 오면 칼·먼 팔이 몸 앞(타격)
BASE = ['legFar', 'legNear']
rig['drawA'] = BASE + ['armF', 'torso', 'skirt', 'foreFb', 'weapon', 'armU', 'armL', 'pauldron', 'head', 'foreF']
rig['drawStrike'] = BASE + ['armF', 'torso', 'skirt', 'foreFb', 'armU', 'armL', 'pauldron', 'head', 'weapon', 'foreF']
rig['drawR'] = [n for n in rig['drawA'] if n != 'armF']
# 먼 팔 몸 뒤(10-20 12:12 DHL 0.37 '표시한 팔 레이어를 몸 뒤로 — 몸 뒤에서 움직입니다'): 손이 어깨 아래(배 옆)로 내려와 있는 동안 먼 팔뚝·주먹·칼을 몸통 뒤에
rig['drawB'] = BASE + ['armF', 'foreFb', 'weapon', 'foreF', 'torso', 'skirt', 'armU', 'armL', 'pauldron', 'head']   # 윗팔도 같이 몸 뒤(12:55 DHL '여기에 팔은 있어야지요' — 타격 때 몸과 팔뚝 사이 윗팔)
rig['drawB0'] = [n for n in rig['drawB'] if n != 'armF']   # 0.31~0.35: 손은 어깨 높이·팔꿈치만 배 옆으로 접힌 순간 — 윗팔 끝이 손 밑 덩어리로 보여(11:50) 안 그림, 0.35 부터는 팔꿈치가 배 뒤라 같이 그려도 안 튐   # 0.72~ 칼을 다시 멜 때: 먼 윗팔은 대기처럼 안 그림 — 팔꿈치가 배 옆으로 나와 비늘 윗팔 끝이 손 밑에 덩어리로 보였음(10-20 11:50 DHL '표시 저 부분이 어색')
K = AK['keys']
def trk(i, f=lambda v, k: v):   # 키 i 번째 값 → 엔진 트랙 [[t, v, easing]]
    return [[k[0], round(f(k[i], k), 4), k[6] if len(k) > 6 else 'io'] for k in K]
act = {'kind': 'sword', 'rigid': True, 'orderAlways': True, 'dur': 0.9, 'hitAt': 0.45, 'hitStop': 0.07, 'cancelAt': 0.66,
       'w': [[0, 1]], 'reach': [[0, 0]], 'nPiece': [[0, 'gF']], 'nUpper': [[0, 'armF']], 'armIK': [[0, 1]], 'ikSideK': {'N': [[0, 1]]},
       'gx': trk(1, lambda v, k: SC * v), 'gy': trk(2, lambda v, k: SC * (v - k[5])), 'sa': trk(3, lambda v, k: math.radians(v)),
       'lean': trk(4, lambda v, k: math.radians(v)), 'hipY': trk(5, lambda v, k: SC * v),
       'head': [[0, 0], [0.28, -0.06, 'io'], [0.45, 0.05, 'io'], [0.6, 0.04, 'io'], [0.86, 0]],
       'freeArm': True, 'fuA': [[0, 0], [0.28, -0.12, 'io'], [0.45, 0.3, 'o'], [0.6, 0.26, 'io'], [0.86, 0]], 'flA': [[0, 0], [0.28, -0.08, 'io'], [0.45, 0.18, 'o'], [0.6, 0.15, 'io'], [0.86, 0]],
       'face': [[0, 'angry'], [0.12, 'effort'], [0.4, 'shout'], [0.62, 'focus'], [0.82, None]],
       'order': [[0, 'drawA0'], [0.04, 'drawA'], [0.31, 'drawB0'], [0.35, 'drawB'], [0.73, 'drawR'], [0.85, 'drawR0']]}   # drawA0·drawR0 = 칼이 대기 자리 근처일 때 guardArt(원화 칼날) 덧그림   # 0.31~0.73: 손이 어깨 아래(배 옆) — 먼 팔뚝·주먹·칼 = 몸통 뒤(DHL 12:12), 먼 윗팔 안 그림 · 0.73~: 다시 멜 때 대기처럼 팔뚝·주먹 앞(몸과 가장 덜 겹치는 순간에 바꿈), 먼 윗팔 안 그림
_ga = lambda L: [x for y in [[n] + (['guardArt'] if n == 'weapon' else []) for n in L] for x in y]
rig['drawA0'] = _ga(rig['drawA']); rig['drawR0'] = _ga(rig['drawR'])
rig['actions'] = {'smash': act}
rig['cutHold'] = 0.25   # 스킬 컷인: 칼을 어깨 뒤로 눕혀 멘 힘줌 자세(메기 꼭대기 .28 직전, 게임은 한 프레임 더 가서 약 .27~.29) — 낮은 버팀(.45~.6)은 11 네온 알론소 때 DHL '쪼그려 앉은 듯', v1.1 휘두르는 순간(.37~.41)은 손이 배 앞이라 컷인으로 약함
