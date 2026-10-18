# 11 머리 위 키트(20:38 DHL 시트 v1 전체 자세) → 리그 조각·키 (attack_neon.py 끝에서 exec)
#  · 키트 전체 자세 머리를 원화 머리에 SIFT 로 맞춘 닮음 변환(geom.json head)으로 키트 좌표 → 상체 뼈 좌표
#  · torsoOH(정면 상체·두 어깨갑)·uFOH(먼 윗팔 보이는 부분) = 상체 뼈에 고정, 키트 자리 그대로
#  · gN_OH(가까운 팔뚝, 은색 토시) · gF_OH(먼 팔뚝) = 칼에 붙는 쥔 팔 조각(따로 그린 조각, 키트 전체 자세에 SIFT 로 맞춘 자리·각도)
#  · uN_OH(가까운 윗팔) = 키트 전체 자세에서 오림, 엔진이 어깨→팔꿈치로 돌림(늘임 ≈ 1)
#  · 손 순서: 원화는 은색 토시 손이 폼멜 쪽 → 가까운 주먹은 키트 자리 그대로, 먼 주먹은 날 쪽으로(가까운 팔뚝 뒤) — 키트 그림은 손 순서가 반대였음
import shutil
KH = os.path.join(HERE, 'kitoh'); KO = os.path.join(KH, 'out')
GEO = json.load(open(os.path.join(KH, 'geom.json'))); MET = json.load(open(os.path.join(KO, 'meta.json'))); OHC = ATK.get('overheadKit', {})
Mh = np.array(GEO['head']['M']); s_h = GEO['head']['scale']; th = math.radians(GEO['head']['rotDeg']); SR = 2 * s_h
TA = np.array(rig['refOrigin']) / 2 + np.array(next(b for b in bones if b['name'] == 'hip')['pos']) / 2   # 상체 뼈 원점(원화 px)
def k2t(p): a = Mh @ np.array([p[0], p[1], 1.0]); return 2 * (a - TA)
K0 = np.linalg.solve(Mh[:, :2], TA - Mh[:, 2])   # 상체 원점에 오는 키트 점
r1 = lambda v: [round(float(v[0]), 2), round(float(v[1]), 2)]
def put(name, file):
    shutil.copy(os.path.join(KO, file), os.path.join(OUT, 'parts', name + '.png')); return name
for name, file, key_ in [('torsoOH', 'torsoOH.png', 'torso')]:
    put(name, file); off = np.array(MET[key_]['off'])
    def_parts[name] = {'src': f'parts/{name}.png', 'pivot': r1(K0 - off), 'scale': round(SR, 5)}
    bones.append(dict(name=name, parent='torso', pos=[0, 0], rot=round(th, 5), part=name))
Uk = OHC.get('swordKitDeg', 126.5)   # 키트 칼날 방향(키트 px, 화면 각도) — 칼날 가운데 선에서 잼
def fore_piece(name, file, mk, rot_deg, sc):
    put(name, file); m = MET[mk]; sd = math.radians(Uk - rot_deg)
    def_parts[name] = {'src': f'parts/{name}.png', 'pivot': list(m['elbow']), 'elbow': list(m['elbow']), 'grip': list(m['grip']), 'wrist': list(m['grip']),
                       'shaftDir': [round(math.cos(sd), 5), round(math.sin(sd), 5)], 'scale': round(SR * sc, 5)}
AK = OHC.get('armK', 1.0)   # 머리 위 팔 크기(21:18 DHL '팔이 너무 길어요') — 어깨를 중심으로 팔 전체(팔뚝·윗팔·주먹)를 줄임
fore_piece('gN_OH', 'gN.png', 'gN', GEO['armN']['rotDeg'], GEO['armN']['scale'] * AK)
gF = MET['gF']; aF = math.degrees(math.atan2(gF['elbow'][1] - gF['grip'][1], gF['elbow'][0] - gF['grip'][0]))
fore_piece('gF_OH', 'gF.png', 'gF', OHC.get('farForeDeg', 30) - aF, GEO['armN']['scale'] * OHC.get('farFistK', 1.0) * AK)
put('uN_OH', 'uN.png'); off = np.array(MET['uN']['off'])
def_parts['uN_OH'] = {'src': 'parts/uN_OH.png', 'pivot': r1(np.array(MET['uN']['shoulder']) - off), 'elbow': r1(np.array(MET['uN']['elbowTop']) - off), 'scale': round(SR * AK, 5)}
# 먼 팔(보이는 윗팔): 상체 고정 조각 — 어깨 공을 먼 어깨갑 밑(키트 자리)에, 팔꿈치가 머리 오른쪽, 팔뚝 끝은 머리카락 뒤
put('farArmOH', 'fArm.png'); _fa = MET['fArm']; _at = k2t(OHC.get('farArmAt', [640, 668]))
def_parts['farArmOH'] = {'src': 'parts/farArmOH.png', 'pivot': list(_fa['shoulder']), 'scale': round(SR * GEO['armN']['scale'] * OHC.get('farArmK', 1.0), 5)}
bones.append(dict(name='farArmOH', parent='torso', pos=r1(_at), rot=round(th + math.radians(OHC.get('farArmRot', -15)), 5), part='farArmOH'))
rig.setdefault('overlays', {})['farFistOv'] = {'bone': 'foreF', 'rect': MET['gF']['fistRect']}
rig['drawOH2'] = ['legFar', 'legNear', 'hips', 'foreF', 'farArmOH', 'torsoOH', 'head', 'weapon', 'weaponA', 'farFistOv', 'armU', 'armL']   # 먼 팔: 주먹만(팔뚝은 머리 뒤) — 큰 머리 3/4 보기에서 먼 팔은 머리에 가려짐
# --- 머리 위 키: 가까운 주먹 = 키트 자리, 칼 방향 = 키트 칼날, 먼 주먹(G) = 날 쪽으로 |sF|
MN = np.array(GEO['armN']['M']); Nk = MN @ np.array(MET['gN']['grip'] + [1.0]); Nt = k2t(Nk)
S_t = k2t(MET['uN']['shoulder']); Nt = S_t + AK * (Nt - S_t)   # 팔을 줄이면 주먹도 어깨 쪽으로(팔 모양 그대로 작게)
ua = math.radians(Uk + math.degrees(th)); u = np.array([math.cos(ua), math.sin(ua)]); sF = -ATK['action']['sF'][0][1] if ATK['action'].get('sF') else 56.8
G = Nt + u * abs(ATK['action']['sF'][0][1]); sa0 = ua - 2 * math.pi   # 들어 올림은 각도가 줄어드는 쪽(칼끝 위→뒤로), 휘두름은 늘어나는 쪽
S_t = k2t(MET['uN']['shoulder']); armU0 = np.array(next(b for b in bones if b['name'] == 'armU')['pos']); shO = S_t - armU0
H = OHC.get('hold', [[0.1002, -0.08, 'o'], [0.16, 0.0, 'io'], [0.27, 0.0, 'io'], [0.33, -0.06, 'io'], [0.36, -0.06, 'lin']])   # [t, 칼 각도 더함(rad), ease] — 처음 넘침 → 자리 → 뒤로 한 번 더(예비)
gk = [g for g in act['gx']]; T_ = [g[0] for g in gk]
def keep(t): return not (0.1001 < t <= 0.3600001)
for k_ in ('gx', 'gy', 'sa'): act[k_] = [g for g in act[k_] if keep(g[0])]
for t, da, e in H:
    a_ = sa0 + da; Gx = Nt + np.array([math.cos(a_), math.sin(a_)]) * abs(ATK['action']['sF'][0][1])   # 가까운 주먹 자리는 그대로, 칼이 그 둘레로 돎
    act['gx'].append([t, round(float(Gx[0]), 2), e]); act['gy'].append([t, round(float(Gx[1]), 2), e]); act['sa'].append([t, round(a_, 4), e])
for k_ in ('gx', 'gy', 'sa'): act[k_].sort(key=lambda g: g[0])
act['shNx'] = [[0, 0], [0.1, 0, 'lin'], [0.1001, round(float(shO[0]), 2)], [0.36, round(float(shO[0]), 2), 'lin'], [0.3601, 0]]
act['shNy'] = [[0, 0], [0.1, 0, 'lin'], [0.1001, round(float(shO[1]), 2)], [0.36, round(float(shO[1]), 2), 'lin'], [0.3601, 0]]
print('  overhead kit: near fist', r1(Nt), 'G', r1(G), 'sa0 %.3f' % sa0, 'shoulder', r1(S_t), 'offset', r1(shO), 'K0', r1(K0), 'SR %.4f' % SR)
# --- 휘두름·런지 팔(20:48 시트 v2): 가까운 토시 팔뚝+주먹(칼에 붙음, 팔뚝이 칼 줄기를 따라 어깨 쪽) · 윗팔(엔진이 어깨→팔꿈치) · 먼 주먹만(먼 팔은 몸 뒤)
STK = OHC.get('strikeScale', 0.9)
for name, file, mk in [('gN_ST', 'gNst.png', 'gNst'), ('gF_ST', 'gFst.png', 'gFst')]:
    put(name, file); m = MET[mk]
    def_parts[name] = {'src': f'parts/{name}.png', 'pivot': list(m['elbow']), 'elbow': list(m['elbow']), 'grip': list(m['grip']), 'wrist': list(m['grip']), 'shaftDir': list(m['shaftDir']), 'scale': STK}
put('uN_ST', 'uNst.png')
def _clean_uNst(path):   # (21:59 IK 로 윗팔이 더 숙으면 어깨갑 밖으로 나오는 위 끝 정리) 지운 파란 패드의 회색 찌꺼기·구멍·가는 외곽선 꼬리
    from scipy import ndimage as _nd
    a = np.array(Image.open(path).convert('RGBA')).astype(np.int32); H_, W_ = a.shape[:2]; yy_, xx_ = np.mgrid[0:H_, 0:W_]; al_ = a[..., 3]
    light = (al_ > 0) & (a[..., :3].min(2) > 150) & ((a[..., :3].max(2) - a[..., :3].min(2)) < 45) & (xx_ < 130); al_ = np.where(light, 0, al_)
    m_ = al_ > 40; m2 = np.where((xx_ < 85) | ((xx_ < 135) & (yy_ < 45)) | ((xx_ < 135) & (yy_ < 70)), _nd.binary_opening(m_, structure=np.ones((7, 7))), m_)
    lab_, n_ = _nd.label(m2); keep = lab_ == (1 + int(np.argmax(_nd.sum(m2, lab_, range(1, n_ + 1))))); hole = _nd.binary_fill_holes(keep) & ~keep
    a[..., 3] = np.where(keep, al_, 0); _sk = (a[..., 3] > 200) & (a[..., 0] > 200) & (a[..., 1] > 140) & (a[..., 1] < 210) & (a[..., 2] < 130); a[hole] = list(np.median(a[_sk][:, :3], 0).astype(int)) + [255]
    Image.fromarray(a.astype(np.uint8), 'RGBA').save(path)   # 구멍 = 패드 밑 윗팔 살 → 살색
_clean_uNst(os.path.join(OUT, 'parts', 'uN_ST.png')); def_parts['uN_ST'] = {'src': 'parts/uN_ST.png', 'pivot': list(MET['uNst']['shoulder']), 'elbow': list(MET['uNst']['elbow']), 'scale': STK}
