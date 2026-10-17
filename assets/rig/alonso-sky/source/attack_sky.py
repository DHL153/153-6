# 21 스카이아크 알론소 내려찍기 (2026-10-18) — 1 러스트 알론소 v4의 rigid 방식(칼 먼저, 쥔 팔뚝 그림이 칼에 붙음)
#  build_sky.py 안에서 exec 됨 (rig, def_parts, parts, world, W, PC, OUT, P2, O, img, unit, np, math, Image 사용)
#  · 엔진 이름: near(armF→foreF) = 칼 메는 팔(여기선 몸 뒤 먼 팔) · far(armU→armL) = 자유 팔(여기선 몸 앞 가까운 팔)
#  · 쥔 팔 조각 = 시트 쥔 주먹(4손가락) + 팔뚝 그림을 합성. 팔뚝 방향은 칼 축 기준으로 고정(rigid) → 구간마다 조각을 바꿈
R2 = 2.0   # 합성 그림 해상도: 리그 1단위 = 2px
FIST_S = 1.24
# 주먹 조각 (DHL 10/18 00:39 "다른 쪽 손 모양"): 메는 손 = 먼 팔 = 왼손 → 원화 메는 손(cArt)·시트 메는 손(cFist)·먼 손(gFv·gF45)만,
#  자유 손 = 가까운 팔 = 오른손 → gNv·gNh만. 좌우 뒤집기 금지(뒤집으면 반대 손이 됨)
#  grip·wrist: 그림 px · sd: 칼끝 방향(엄지 쪽) · k: 그림 px → 리그 단위 · c: 자연스러운 손목→팔꿈치 각도(칼끝 기준, 시계 +) — 손목 꺾임은 c ±40° 안에서만
FISTS = {
    'cArt': dict(file=os.path.join(W, 'carryArt.png'), grip=(37.0, 37.0), wrist=(25.0, 86.0), sd=(float(-UAX[0]), float(-UAX[1])), k=2.0, c=-102),
    'cFist': dict(file=os.path.join(W, 'carryFist.png'), grip=(205.0, 80.0), wrist=(180.0, 82.0), sd=(-0.49, -0.87), k=FIST_S, c=-61),
    'gNv': dict(grip=(60.0, 80.0), sd=(0.0, -1.0), wrist=(10.0, 88.0), k=FIST_S, c=-90),
    'gNh': dict(grip=(85.0, 52.0), sd=(-1.0, 0.0), wrist=(175.0, 48.0), k=FIST_S, c=180),
    'gFv': dict(grip=(46.0, 80.0), sd=(0.0, -1.0), wrist=(116.0, 90.0), k=FIST_S, c=90),
    'gF45': dict(grip=(68.0, 68.0), sd=(-0.707, -0.707), wrist=(122.0, 72.0), k=FIST_S, c=145),
}
FORES = {   # 팔뚝: 팔꿈치·손목 점(그림 좌표)
    'near': dict(file=os.path.join(W, 'nearFore.png'), el=(30.0, 22.0), wr=(70.0, 122.0)),
    'carry': dict(file=os.path.join(W, 'carryFore.png'), el=(35.0, 60.0), wr=(176.0, 72.0)),
}
# 손을 뗐다 잡는 자유 손 주먹: 위아래로 삐져나온 손잡이 토막을 지움 — 열마다 주먹 테두리(어두운 선)까지만
#  ('top', x0, x1, y): y 아래 처음 나오는 테두리 위를 지움 / ('bot', x0, x1, y): y 위 마지막 테두리 아래를 지움 / ('left', y0, y1, x): x 왼쪽 지움
NOSTUB = {'gNv': [('top', 38, 86, 34), ('bot', 36, 86, 124)], 'gNh': [('left', 28, 78, 40)],
          'gFv': [('top', 26, 70, 43), ('bot', 24, 68, 127)]}
def unstub(im, spec):
    a = np.array(im).copy(); dark = (a[..., 3] > 128) & (a[..., :3].sum(-1) < 120)
    for kind, p0, p1, q in spec:
        for c in range(p0, p1 + 1):
            if kind == 'top':
                ys = [y for y in range(q, q + 8) if dark[y, c]]; a[:(ys[0] if ys else q), c, 3] = 0
            elif kind == 'bot':
                ys = [y for y in range(q - 8, q + 1) if dark[y, c]]; a[(ys[-1] + 1 if ys else q):, c, 3] = 0
            else:
                xs = [x for x in range(q, q + 10) if dark[c, x]]; a[c, :(xs[0] if xs else q), 3] = 0
    from scipy import ndimage   # 지우고 남은 가는 부스러기 제거: 가장 큰 덩어리만
    lab, n = ndimage.label(a[..., 3] > 0)
    if n > 1: big = 1 + int(np.argmax(ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)))); a[..., 3] = np.where(lab == big, a[..., 3], 0)
    return Image.fromarray(a)
def sim_pts(p1, p2, q1, q2):
    p1, p2, q1, q2 = map(lambda v: np.array(v, float), (p1, p2, q1, q2)); vp, vq = p2 - p1, q2 - q1
    s = np.linalg.norm(vq) / np.linalg.norm(vp); a = math.atan2(vq[1], vq[0]) - math.atan2(vp[1], vp[0]); c, sn = math.cos(a) * s, math.sin(a) * s
    A = np.array([[c, -sn], [sn, c]]); return A, q1 - A @ p1
def compose(name, fist, fore, rel_deg, L=95.0, inset=10.0):
    """쥔 팔 조각 만들기: 주먹 그림 + 팔뚝. rel_deg = 손목→팔꿈치 방향(칼끝 방향 기준, 화면 각도·시계 방향 +)."""
    F, Fo = FISTS[fist], FORES[fore]; oim = img(Fo['file'])
    fim = unstub(img(F.get('file') or os.path.join(PC, fist + '.png')), NOSTUB.get(fist, []))
    k = F['k'] * R2; sd = unit(F['sd']); a_sd = math.atan2(sd[1], sd[0]); d = (math.cos(a_sd + math.radians(rel_deg)), math.sin(a_sd + math.radians(rel_deg)))
    Wc = np.array(F['wrist']) * k; Wi = Wc - np.array(d) * inset * R2; Ec = Wi + np.array(d) * L * R2   # 팔뚝 손목 끝은 토시 안으로 inset만큼
    A, t = sim_pts(Fo['wr'], Fo['el'], Wi, Ec)
    cs = [A @ np.array(c, float) + t for c in [(0, 0), (oim.width, 0), (0, oim.height), (oim.width, oim.height)]] + [np.array([0, 0]), np.array([fim.width * k, fim.height * k])]
    mn = np.floor(np.min(cs, 0)) - 4; mx = np.ceil(np.max(cs, 0)) + 4; size = tuple((mx - mn).astype(int))
    Ai = np.linalg.inv(A); bi = -Ai @ (t - mn)   # 캔버스 → 팔뚝 그림
    canvas = oim.transform(size, Image.AFFINE, (Ai[0, 0], Ai[0, 1], bi[0], Ai[1, 0], Ai[1, 1], bi[1]), resample=Image.BICUBIC)
    fs = fim.resize((round(fim.width * k), round(fim.height * k)), Image.LANCZOS); canvas.alpha_composite(fs, (int(-mn[0]), int(-mn[1])))
    canvas.save(os.path.join(OUT, 'parts', name + '.png'))
    g = np.array(F['grip']) * k - mn; e = Ec - mn
    def_parts[name] = {'src': f'parts/{name}.png', 'pivot': [round(float(e[0]), 1), round(float(e[1]), 1)], 'elbow': [round(float(e[0]), 1), round(float(e[1]), 1)],
                       'grip': [round(float(g[0]), 1), round(float(g[1]), 1)], 'wrist': [round(float(g[0]), 1), round(float(g[1]), 1)], 'shaftDir': [float(sd[0]), float(sd[1])], 'scale': 1 / R2}
# 구간별 쥔 팔 (손목→팔꿈치 방향, 칼끝 방향 기준 각도): 머리 위(칼끝이 뒤쪽 192°) / 휘두름(0°) / 타격(25°)
ATK = json.load(open(os.path.join(HERE, 'attack_keys.json'), encoding='utf-8'))
# 원화 메는 손(cArt): 서 있을 때 그림(fistF = 원화 오림) 그대로 쥔 팔 조각으로 — 공격 시작·끝이 서 있는 그림과 똑같이 이어짐 (팔꿈치 = 원화 팔꿈치 EL_F)
_o = np.array(P2(405, 225), float); _px = lambda p: [round(float(v), 1) for v in (np.array(p, float) - _o) / 2.0]
def_parts['cArt'] = {'src': 'parts/fistF.png', 'pivot': _px(EL_F), 'elbow': _px(EL_F), 'grip': _px(GRIP), 'wrist': _px(GRIP), 'shaftDir': [float(-UAX[0]), float(-UAX[1])], 'scale': 2.0}
for nm, (fist, fore, rel, *Lx) in ATK['pieces'].items(): compose(nm, fist, fore, rel, *(Lx[:1] or []))
# 팔 = '팔꿈치까지 그림을 늘려서' (DHL 01:54): 조각을 여러 장 잇지 않음
#  · 가까운 팔: 소매를 밑단에서 자른 armUs(어깨→팔꿈치, 늘임) + 쥔 팔뚝 조각(팔꿈치 살은 소매 안으로 — 그리는 순서 armL 다음 armU)
#  · 먼 팔(칼 메는 팔): 처음 그림(원화 손 cArt) 그대로 + 내린 소매 armF 통째(어깨→소매→팔뚝 살→손목 띠)를 늘여 원화 손 토시 안까지
exec(open(os.path.join(HERE, 'sleeve_crop.py'), encoding='utf-8').read().split("if __name__")[0])
crop_hem(os.path.join(PC, 'armNdown.png'), os.path.join(OUT, 'parts', 'armUs.png'))
def_parts['armUs'] = {'src': 'parts/armUs.png', 'pivot': [50.0, 22.0], 'elbow': [48.0, 104.0], 'scale': def_parts['armU']['scale']}
def_parts['armFw'] = {'src': def_parts['armF']['src'], 'pivot': [48.0, 20.0], 'elbow': [48.0, 138.0], 'scale': def_parts['armF']['scale']}
def_parts['cArt']['elbow'] = [float(v) for v in ATK.get('cArtCuff', [18, 78])]   # 원화 손 토시 구멍(팔뚝이 들어가는 곳) — 먼 소매 끝이 여기 닿음
# 칼 폼멜: 공격 때만(메는 손 원화 그림이 없을 때) 그림 — 칼 그림의 잘린 아래쪽
_full = img(os.path.join(W, 'sword_full.png')); _top = 515 + EXT; _full.crop((0, _top, _full.width, _full.height)).save(os.path.join(OUT, 'parts', 'pommel.png'))
_wp = def_parts['weapon']; def_parts['pommel'] = {'src': 'parts/pommel.png', 'pivot': [_wp['pivot'][0], _wp['pivot'][1] - _top], 'scale': _wp['scale']}
rig['bones'].append({'name': 'pommel', 'parent': 'weapon', 'pos': [0, 0], 'part': 'pommel'})
rig['hidden'] = []
rig['swordGrip'] = {'tipDepth': 6, 'near': {'upper': 'armF', 'carry': ATK['carry0']}, 'far': {'upper': 'armU', 'pieces': [ATK['far0']], 'sPref': ATK['sF']},
                   'shoulderN': ATK['shoulderN'], 'shoulderF': ATK['shoulderF'], 'pauldronFollow': ATK.get('pauldronFollow', 1)}
if ATK.get('reachBulge'): rig['swordGrip']['far']['reachBulge'] = ATK['reachBulge']
for _k in ('stretchMax', 'shoulderPush'):
    if _k in ATK: rig['swordGrip'][_k] = ATK[_k]
D0 = rig['draw']
for k, L in ATK['orders'].items(): rig[k] = L if 'hiltW' in L else [x for n in L for x in (['hiltW', n] if n == 'weapon' else [n])]
act = dict(ATK['action']); act.update({'kind': 'sword', 'rigid': True, 'reachIK': True, 'hiltSlide': ['hiltW', 'pommel'], 'orderAlways': True})   # 자유 손 잡기·놓기 = 두 관절 IK(원래 팔 그림, 팔꿈치 위/아래는 reachUp 키) → 손에 닿은 뒤 쥔 팔 조각
# 키: 칼 손잡이 자리는 '세계(발 기준)' 좌표로 적고 골반 이동(hipX·hipY)을 빼서 gx·gy로 (엔진은 골반 기준)
from bisect import bisect
EASE = {'lin': lambda u: u, 'io': lambda u: u * u * (3 - 2 * u), 'o': lambda u: 1 - (1 - u) ** 2, 'i': lambda u: u * u, 'o3': lambda u: 1 - (1 - u) ** 3, 'o5': lambda u: 1 - (1 - u) ** 5,
        's': lambda u: 1 - (1 - ((u * u / 0.4 if u < .2 else u - .1) / .9)) ** 3}
def samp(K, t):   # 엔진 track()과 같은 보간 (키 끝 문자 = 다음 키까지 easing)
    if t <= K[0][0]: return K[0][1]
    for i in range(len(K) - 1):
        if t <= K[i + 1][0]: u = (t - K[i][0]) / max(1e-6, K[i + 1][0] - K[i][0]); return K[i][1] + (K[i + 1][1] - K[i][1]) * EASE[K[i][2] if len(K[i]) > 2 else 'io'](u)
    return K[-1][1]
HIP0 = next(b for b in rig['bones'] if b['name'] == 'hip')['pos']
gx, gy, sa = [], [], []
FIX = ATK.get('gripFix', {})   # 키별 보정(tools/calib.py가 채움): 다리 IK 등으로 골반이 키와 다르게 움직인 만큼
for t, X, Y, A, *e in ATK['grip']:
    ee = e[0] if e else 'io'; fx = FIX.get(str(t), [0, 0]); X, Y = X + fx[0], Y + fx[1]
    gx.append([t, round(X - HIP0[0] - samp(act.get('hipX', [[0, 0]]), t), 1), ee]); gy.append([t, round(Y - HIP0[1] - samp(act.get('hipY', [[0, 0]]), t), 1), ee]); sa.append([t, A, ee])
act.update({'gx': gx, 'gy': gy, 'sa': sa})
rig['actions'] = {'smash': act}
rig['cutHold'] = ATK.get('cutHold', .55)   # 스킬 컷인: 내려찍은 자세(런지, 칼 앞 아래)로 멈춤 — 손을 놓기(0.62) 전
