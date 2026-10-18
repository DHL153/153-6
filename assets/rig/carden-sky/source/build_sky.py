"""26 스카이아크 카르덴 리그 조립 (2026-10-18 22:27) — 16 네온 build_carden.py 복사. 다른 점: 땋은 수염 두 갈래(braid·braid2 뼈, 무표정 얼굴 조각에서 오림 — tune.braids),
  찌르기 소매 = 조각 시트 33·34칸(sleeveSheet.fromCut), 원화 자리·다각형은 스카이 원화로 다시 잼
16 네온 카르덴 리그 조립 (2026-10-18) — 6 러스트 카르덴 v10 build_carden.py 복사. 다른 점: 조각 배율이 조각마다 다름(머리·수염 1.84, 몸통 2.34, 얼굴·봉 2.04)이라
  자리 = 원화에 맞춘 변환(fix_result.json: fixmatch 범위 맞춤 + place_manual 두 점), 땋은 수염(braid 뼈, 수염 아래), 오른 옆머리 없음(skip), 인사 없음, 봉 갈고리 얼룩 지움(weaponClean)
6 카르덴(러스트 드워프 기술자) 리그 조립 — 8 러스트 니콜(rust-fork-girl v15) 뼈대 구조, 수치는 전부 6 에서 새로 잼 (2026-10-17)
입력: cut/*.png(조각 시트 1장, 31칸), parts_work/(손 다듬기 결과, hands.py), sift_result.json·fix_result.json(조각→기준 그림 배치),
      measure/joints_ref.json(원화 512 관절점), tune.json(걸음·찌르기·조정값)
출력: ../rig.json, ../parts/*.png, ../rig.def.js
단위: 기준 그림 ref1024(= 원화 char_0006 512 의 2배) 픽셀 = 리그 단위. 뿌리(root) = 두 발 가운데 땅.
배율: 조각은 모두 시트에서 같은 배율 K=2.05(머리·얼굴·봉이 SIFT 로 2.04~2.07) — 조각마다 따로 맞추지 않음(맞춤 점수가 작은 배율로 쏠림, 21:58 확인)
먼 주먹(fistF)만 원화에서 오림: 시트 주먹은 손 좌우가 원화와 반대(hands.py 설명)
실행: cd source && python3 -I build_carden.py
"""
import json, math, os, shutil, hashlib
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); PK = os.path.join(HERE, '..'); PARTS = os.path.join(PK, 'parts')
if os.path.isdir(PARTS): shutil.rmtree(PARTS)
os.makedirs(PARTS)
S = json.load(open(os.path.join(HERE, 'sift_result.json'))); F = json.load(open(os.path.join(HERE, 'fix_result.json')))
J5 = json.load(open(os.path.join(HERE, 'measure', 'joints_ref.json'))); HJ = json.load(open(os.path.join(HERE, 'hands.json')))
TUNE = json.load(open(os.path.join(HERE, 'tune.json'))) if os.path.exists(os.path.join(HERE, 'tune.json')) else {}
T = lambda n, d: TUNE.get(n, d)
A = lambda v: np.array(v, float)
J = {k: A(v) * 2 for k, v in J5.items() if isinstance(v, list)}                     # 원화 관절점 → ref1024
ap = lambda m, p: m[:, :2] @ A(p) + m[:, 2]
inv = lambda m, r: np.linalg.solve(m[:, :2], A(r) - m[:, 2])
def info(m): return math.hypot(m[0, 0], m[1, 0]), math.atan2(m[1, 0], m[0, 0])
def simT(s, phi, src, dst):
    c, sn = math.cos(phi) * s, math.sin(phi) * s; m = A([[c, -sn, 0], [sn, c, 0]]); m[:, 2] = A(dst) - m[:, :2] @ A(src); return m
def seg(s, a, b, P, Q):                                      # 조각 선분 a→b 를 P→Q 방향으로, a→P (배율 s 고정)
    phi = math.atan2(Q[1] - P[1], Q[0] - P[0]) - math.atan2(b[1] - a[1], b[0] - a[0]); return simT(s, phi, a, P)
K = T('K', 2.05)
GROUND = 1000.0; ROOT = A([(J['nearSole'][0] + J['farSole'][0]) / 2, GROUND])
WAIST = J['waist']; NECK = J['neck'] + A(T('neckOff', [0, 0]))
sz = lambda n: Image.open(os.path.join(HERE, 'cut', n + '.png')).size
M_ = lambda n: A((F.get(n) or S.get(n) or {'M': [[1, 0, 0], [0, 1, 0]]})['M'])   # 스카이: 맞추지 않은 조각(tuftR 등 skip)은 단위 변환
SKIP = set(T('skip', []))

# ---- 조각 관절점 (조각 그림 px, 시트 격자 확대로 읽음 — review/c_*.png)
PT = {'armU': ([22, 3], [22, 48]), 'armL': ([57, 3], [52, 42]), 'armLF': ([34, 3], [33, 45]), 'armF': ([19, 2], [19, 50]), 'foreF': ([17, 2], [17, 52]),
      'thighN': ([40, 4], [36, 55]), 'thighF': ([37, 4], [40, 55]), 'shinN': ([19, 3], [18, 43]), 'shinF': ([19, 3], [19, 43])}
PT.update(T('pts', {}))

P = {}
P['torso'] = dict(file='cut/torso.png', M=M_('torso'), at=WAIST)
P['hips'] = dict(file='cut/hips.png', M=M_('hips')); w_, h_ = sz('hips'); P['hips']['at'] = ap(P['hips']['M'], (w_ / 2, h_ * .3))
P['pouch'] = dict(file='cut/pouch.png', M=M_('pouch')); w_, h_ = sz('pouch'); P['pouch']['at'] = ap(P['pouch']['M'], (w_ / 2, 4))
P['head'] = dict(file='cut/head.png', M=M_('head'), at=NECK)
HF = T('headFace', None)
if HF:   # 머리 = 표정 시트 무표정 얼굴 통째(모자·옆머리·귀·고글·수염) — 원화에 SIFT 로 딱 맞음(2.03, 점 198개). 시트 머리 조각엔 귀 둘레 옆머리가 없어 원화와 달랐음 (16 네온 10-18 13:05)
    _f = np.asarray(Image.open(os.path.join(HERE, 'cut/face_neutral.png')).convert('RGBA')).copy()
    for x0_, y0_, x1_, y1_ in HF.get('erase', []): _f[y0_:y1_, x0_:x1_, 3] = 0   # 땋은 끝(따로 braid 뼈)
    os.makedirs(os.path.join(HERE, 'parts_work'), exist_ok=True); Image.fromarray(_f, 'RGBA').save(os.path.join(HERE, 'parts_work/head_face.png'))
    P['head'] = dict(file='parts_work/head_face.png', M=A(S['face_neutral']['M']), at=NECK)
BRS = T('braids', None)
if BRS and HF:   # 땋은 수염 두 갈래(스카이): 무표정 얼굴 조각의 끈 아래(cutY~)를 오려 따로 뼈 — 머리 그림에선 지움(끈 아래 fade 줄은 겹쳐 이음매 안 보임) (26 스카이 10-18 22:27)
    _f = np.asarray(Image.open(os.path.join(HERE, 'parts_work/head_face.png')).convert('RGBA')).copy(); _yy = np.arange(_f.shape[0])[:, None]; cy_ = BRS['cutY']; fd_ = BRS.get('fade', 3)
    MFACE = A(S['face_neutral']['M'])
    for bn_, side_ in [('braid', 'L'), ('braid2', 'R')]:
        x0_, x1_ = BRS[side_]['x']; _b = _f.copy(); _b[:, :x0_, 3] = 0; _b[:, x1_:, 3] = 0
        _b[..., 3] = (_b[..., 3] * np.clip((_yy - cy_ + fd_) / fd_, 0, 1)).astype(np.uint8)   # 끈 아래부터(위 fd 줄 흐리게 — 머리 그림의 끈 밑으로 들어감)
        ys_, xs_ = np.nonzero(_b[..., 3] > 2); ox_, oy_ = int(xs_.min()), int(ys_.min()); _b = _b[oy_:ys_.max() + 1, ox_:xs_.max() + 1]
        Image.fromarray(_b, 'RGBA').save(os.path.join(HERE, f'parts_work/{bn_}.png'))
        Mb_ = MFACE.copy(); Mb_[:, 2] = MFACE[:, 2] + MFACE[:, :2] @ A([ox_, oy_])
        P[bn_] = dict(file=f'parts_work/{bn_}.png', M=Mb_, at=ap(MFACE, BRS[side_]['root']))
        _m = (_yy >= cy_) & (np.arange(_f.shape[1])[None, :] >= x0_) & (np.arange(_f.shape[1])[None, :] < x1_)
        _f[..., 3] = np.where(_m, 0, _f[..., 3])
    Image.fromarray(_f, 'RGBA').save(os.path.join(HERE, 'parts_work/head_face.png'))
w_, h_ = sz('tuftL'); P['tuftL'] = dict(file='cut/tuftL.png', M=M_('tuftL'), at=ap(M_('tuftL'), T('tuftLroot', (w_ * .88, h_ * .62))))
w_, h_ = sz('tuftR'); P['tuftR'] = dict(file='cut/tuftR.png', M=M_('tuftR'), at=ap(M_('tuftR'), T('tuftRroot', (w_ * .12, h_ * .62))))
w_, h_ = sz('beard'); P['beard'] = dict(file='cut/beard.png', M=M_('beard'), at=ap(M_('beard'), (w_ / 2, 12)))
PO = T('pouchRef', None)
if PO:   # 가까운 주머니 = 원화(ref1024)에서 다각형으로 오림 — 시트 주머니는 원화보다 작고 모양이 달라서, 바지(원화 오림)에 들어간 주머니 아래쪽과 딱 이어짐 (26 스카이 10-18 22:27)
    from PIL import ImageDraw as _D
    _R = Image.open(os.path.join(HERE, 'ref1024.png')).convert('RGBA'); _m = Image.new('L', (4096, 4096), 0); _D.Draw(_m).polygon([(x * 4, y * 4) for x, y in PO['poly']], fill=255)
    _m = np.asarray(_m.resize((1024, 1024), Image.LANCZOS)).astype(np.float32) / 255; _a = np.asarray(_R).copy(); _a[..., 3] = (_a[..., 3] * _m).astype(np.uint8)
    _ys, _xs = np.nonzero(_a[..., 3] > 2); _ox, _oy = int(_xs.min()), int(_ys.min()); _a = _a[_oy:_ys.max() + 1, _ox:_xs.max() + 1]
    os.makedirs(os.path.join(HERE, 'parts_work'), exist_ok=True); Image.fromarray(_a, 'RGBA').save(os.path.join(HERE, 'parts_work/pouch.png'))
    P['pouch'] = dict(file='parts_work/pouch.png', M=A([[1, 0, _ox], [0, 1, _oy]]), at=A([_ox + _a.shape[1] / 2, _oy + 4]))
SN = J['nearShoulder'] + A(T('SNoff', [0, 0]))
P['pauldron'] = dict(file='cut/pauldron.png', M=M_('pauldron'), at=SN)
PR = T('pauldronRef', None)
if PR:   # 어깨갑 = 원화(ref1024)에서 다각형으로 오림 — 시트 어깨갑은 노란 줄 모양이 원화(Y자)와 달라서 (16 네온 10-18 13:15)
    from PIL import ImageDraw as _D
    _R = Image.open(os.path.join(HERE, 'ref1024.png')).convert('RGBA'); _m = Image.new('L', (4096, 4096), 0); _D.Draw(_m).polygon([(x * 4, y * 4) for x, y in PR['poly']], fill=255)
    _m = np.asarray(_m.resize((1024, 1024), Image.LANCZOS)).astype(np.float32) / 255; _a = np.asarray(_R).copy(); _a[..., 3] = (_a[..., 3] * _m).astype(np.uint8)
    _ys, _xs = np.nonzero(_a[..., 3] > 2); _ox, _oy = int(_xs.min()), int(_ys.min()); _a = _a[_oy:_ys.max() + 1, _ox:_xs.max() + 1]
    Image.fromarray(_a, 'RGBA').save(os.path.join(HERE, 'parts_work/pauldron.png'))
    P['pauldron'] = dict(file='parts_work/pauldron.png', M=A([[1, 0, _ox], [0, 1, _oy]]), at=SN)
# 가까운 팔: 팔뚝+편 손(armL) = 원화 손 자리에 맞춘 배치(fix, -20°), 팔꿈치 = 그 그림의 소매 위 끝. 윗팔은 어깨→팔꿈치
ML = M_('armL'); EN = ap(ML, PT['armL'][0])
NA = T('nearArm', None)   # DHL 23:51 '가까운 팔이 너무 짧음': 윗팔 뼈를 먼 팔만큼 길게(upper), 팔꿈치는 어깨·손(원화 손바닥 가운데) 두 원의 바깥 교점 → 서 있을 땐 손이 원화 자리
if NA:
    HN = A(NA['hand']); a_, b_ = A(NA['elbowImg']), A(NA['handImg']); LU_ = NA['upper']; LF_ = np.linalg.norm(b_ - a_) * K
    dv = HN - SN; dd = np.linalg.norm(dv); ca = np.clip((LU_ ** 2 + dd ** 2 - LF_ ** 2) / (2 * LU_ * dd), -1, 1); ang0 = math.atan2(dv[1], dv[0]); al_ = math.acos(ca)
    c1 = SN + LU_ * A([math.cos(ang0 + al_), math.sin(ang0 + al_)]); c2 = SN + LU_ * A([math.cos(ang0 - al_), math.sin(ang0 - al_)]); EN = c1 if c1[0] < c2[0] else c2
    ML = seg(K, a_, b_, EN, HN); PT['armL'] = (list(a_), list(b_))
NR = T('nearArmRef', None)
if NR:   # 가까운 팔(어깨갑 아래 소매 + 편 장갑) = 원화(ref1024)에서 다각형으로 통째 오림 — 원화 팔은 앞으로 뻗어 짧아 보이는(원근) 모양이라 시트 조각(곧은 팔뚝)으론 안 맞음 (16 네온 10-18 13:30)
    from PIL import ImageDraw as _D
    _R = Image.open(os.path.join(HERE, 'ref1024.png')).convert('RGBA'); _m = Image.new('L', (4096, 4096), 0); _D.Draw(_m).polygon([(x * 4, y * 4) for x, y in NR['poly']], fill=255)
    _m = np.asarray(_m.resize((1024, 1024), Image.LANCZOS)).astype(np.float32) / 255; _a = np.asarray(_R).copy(); _a[..., 3] = (_a[..., 3] * _m).astype(np.uint8)
    from scipy import ndimage as _nd
    _k = _a[..., 3] > 20; _lb, _n = _nd.label(_k); _sz = _nd.sum(_k, _lb, range(1, _n + 1)); _a[..., 3] = np.where(_lb == 1 + int(np.argmax(_sz)), _a[..., 3], 0)
    if NR.get('padCut') and T('pauldronRef', None) is not None:   # 어깨갑은 따로(pauldron 뼈) — 팔 그림에선 어깨갑 다각형을 PC px 줄여서 뺌(어깨갑 밑으로 팔이 조금 들어가 이음 안 비침). 달릴 때 팔이 흔들려도 어깨갑이 두 겹으로 안 보임 (16 네온 DHL 10-18 12:45)
        _pm = Image.new('L', (4096, 4096), 0); _D.Draw(_pm).polygon([(x * 4, y * 4) for x, y in T('pauldronRef', None)['poly']], fill=255)
        _pm = np.asarray(_pm.resize((1024, 1024), Image.LANCZOS)).astype(np.float32) / 255
        _pm = _nd.grey_erosion(_pm, size=(2 * NR['padCut'] + 1, 2 * NR['padCut'] + 1)); _a[..., 3] = (_a[..., 3] * (1 - _pm)).astype(np.uint8)
    _ys, _xs = np.nonzero(_a[..., 3] > 2); _ox, _oy = int(_xs.min()), int(_ys.min()); _a = _a[_oy:_ys.max() + 1, _ox:_xs.max() + 1]
    Image.fromarray(_a, 'RGBA').save(os.path.join(HERE, 'parts_work/armL_ref.png'))
    EN = A(NR['elbow']); ML = A([[1, 0, _ox], [0, 1, _oy]]); PT['armL'] = ([NR['elbow'][0] - _ox, NR['elbow'][1] - _oy], [NR['hand'][0] - _ox, NR['hand'][1] - _oy])
P['armU'] = dict(file='cut/armU.png', M=seg(K, *PT['armU'], SN, EN), at=SN)
P['armL'] = dict(file='parts_work/armL_ref.png' if NR else 'cut/armL.png', M=ML, at=EN)
LB = T('armLbind', 0)
if LB:   # 엔진 대기에서 팔뚝을 −0.3 rad(팔이 처짐) 돌림 → 원화 그대로 오린 팔은 그만큼 미리 반대로 돌려 둠(대기 = 원화). 달리기 주먹(armLF)은 그림을 −LB 돌려 저장해 달릴 때 자세는 그대로 (16 네온 10-18 13:40)
    _c, _s = math.cos(LB), math.sin(LB); _Rt = A([[_c, -_s], [_s, _c]]); _M = P['armL']['M'].copy(); P['armL']['M'] = np.c_[_Rt @ _M[:, :2], _Rt @ (_M[:, 2] - EN) + EN]
# 먼 팔: 어깨 → 손목(원화 주먹의 소매 테 가운데) 두 관절 IK. 팔꿈치는 몸 쪽(수염·몸통 뒤로 숨는 쪽)
fo = HJ['fistF']; MF = A([[1, 0, fo['origin'][0]], [0, 1, fo['origin'][1]]]) @ np.eye(3)[:, :3] if False else A([[1, 0, fo['origin'][0]], [0, 1, fo['origin'][1]]])
WF = A(fo['wristRef']) + A(T('WFoff', [0, 0])); G = A(fo['gripRef'])
SF = J['farShoulder'] + A(T('SFoff', [0, 0]))
L1 = np.linalg.norm(A(PT['armF'][1]) - PT['armF'][0]) * K; L2 = np.linalg.norm(A(PT['foreF'][1]) - PT['foreF'][0]) * K
d = np.linalg.norm(WF - SF); dd = min(d, (L1 + L2) * .995); base = math.atan2(WF[1] - SF[1], WF[0] - SF[0])
al = math.acos(np.clip((L1 * L1 + dd * dd - L2 * L2) / (2 * L1 * dd), -1, 1))
E1 = SF + L1 * A([math.cos(base + al), math.sin(base + al)]); E2 = SF + L1 * A([math.cos(base - al), math.sin(base - al)])
EF = E1 if E1[1] > E2[1] else E2                            # 팔꿈치 아래 (8 니콜과 같은 쪽)
P['armF'] = dict(file='cut/armF.png', M=seg(K, *PT['armF'], SF, EF), at=SF)
P['foreF'] = dict(file='cut/foreF.png', M=seg(K, *PT['foreF'], EF, WF), at=EF)
P['fistF'] = dict(file=fo['file'], M=MF, at=WF)
# 봉: 시트 봉(배율 K). weaponRaise = 손 안에서 위로 올림(리그 단위) — 달리기·찌르기에서 집게가 땅에 닿지 않게 (대역 리그 연구 21:30)
MW = M_('weapon').copy(); MW[1, 2] -= T('weaponRaise', 16)
P['weapon'] = dict(file='cut/weapon.png', M=MW, at=G)
WC = T('weaponClean', None)
if WC:   # 시트 봉 아래 마디 옆 갈고리 얼룩(조각 px 상자들) 지움 (16 네온 10-18 12:30)
    _w = np.asarray(Image.open(os.path.join(HERE, 'cut/weapon.png')).convert('RGBA')).copy()
    for x0_, y0_, x1_, y1_ in WC: _w[y0_:y1_, x0_:x1_, 3] = 0
    os.makedirs(os.path.join(HERE, 'parts_work'), exist_ok=True); Image.fromarray(_w, 'RGBA').save(os.path.join(HERE, 'parts_work/weapon.png')); P['weapon']['file'] = 'parts_work/weapon.png'
BR = T('braid', None)
if BR:   # 땋은 수염 끝(조각 시트 waveHand 칸) — 수염 뼈 아래 매달려 출렁임. rootImg = 끈 위 가운데(조각 px)
    P['braid'] = dict(file='cut/waveHand.png', M=M_('waveHand'), at=ap(M_('waveHand'), BR['rootImg']))
for n_ in SKIP: P.pop(n_, None)

if T('closeArmhole', False):   # 몸통 가까운 소매 구멍(어두운 안쪽) → 소매 윗면 올리브로 메움: 봉 찌르기에서 어깨가 앞으로 나가면 구멍이 보임(시트 10~13엔 없음)
    from scipy import ndimage as _nd
    _a = np.asarray(Image.open(os.path.join(HERE, 'cut/torso.png')).convert('RGBA')).astype(float); _l = _a[..., :3].mean(-1)
    _m = (_a[..., 3] > 128) & (_l < 70); _m[:, 22:] = False; _m[:30] = False; _m[88:] = False
    _lb, _n = _nd.label(_m); _sz = _nd.sum(_m, _lb, range(1, _n + 1)); _m = _lb == (1 + int(np.argmax(_sz)))
    _edge = (_a[..., 3] > 128) & ~_nd.binary_erosion(_a[..., 3] > 128, iterations=4)   # 바깥 외곽선은 남김
    _f = _m & ~_edge; _ol = _a[50:62, 26:40, :3].reshape(-1, 3).mean(0) * .8
    _fs = _nd.gaussian_filter(_f.astype(float), 1.2); _a[..., :3] = _a[..., :3] * (1 - _fs[..., None]) + _ol * _fs[..., None]
    os.makedirs(os.path.join(HERE, 'parts_work'), exist_ok=True); Image.fromarray(_a.astype(np.uint8), 'RGBA').save(os.path.join(HERE, 'parts_work/torso.png')); P['torso']['file'] = 'parts_work/torso.png'
TE = T('torsoErase', None)
if TE:   # 몸통 시트 조각의 가까운 소매 토막(크림 관·회색 구멍) 지움 — 원화엔 팔이 덮어 안 보이고, 달릴 때 팔 뒤로 관이 튀어나와 보였음 (16 네온 10-18 13:55)
    from PIL import ImageDraw as _D
    _t = Image.open(os.path.join(HERE, P['torso']['file'])).convert('RGBA'); _m = Image.new('L', (_t.width * 4, _t.height * 4), 255); _D.Draw(_m).polygon([(x * 4, y * 4) for x, y in TE], fill=0)
    _m = np.asarray(_m.resize(_t.size, Image.LANCZOS)).astype(np.float32) / 255; _a = np.asarray(_t).copy(); _a[..., 3] = (_a[..., 3] * _m).astype(np.uint8)
    os.makedirs(os.path.join(HERE, 'parts_work'), exist_ok=True); Image.fromarray(_a, 'RGBA').save(os.path.join(HERE, 'parts_work/torso.png')); P['torso']['file'] = 'parts_work/torso.png'
UF = T('armUfadeTop', 0)
if UF:   # 가까운 윗팔 소매 위 끝(회색 열린 구멍)을 흐리게 — 어깨갑 밑에서 소매가 시작(달릴 때 어깨 위로 구멍 테가 보였음)
    _u = np.asarray(Image.open(os.path.join(HERE, P['armU']['file'])).convert('RGBA')).copy(); _yy = np.arange(_u.shape[0])[:, None]
    _u[..., 3] = (_u[..., 3] * np.clip((_yy - UF) / 4, 0, 1)).astype(np.uint8)
    UB = T('armUcutBottom', 0)
    if UB:
        _xx = np.arange(_u.shape[1])[None, :]; _xs = np.nonzero(_u[UB, :, 3] > 100)[0]; _cx, _hw = (_xs.min() + _xs.max()) / 2, (_xs.max() - _xs.min()) / 2 + 1
        _ye = UB + 7 * np.clip(1 - ((_xx - _cx) / _hw) ** 2, 0, 1)   # 둥근 끝(가운데가 더 김)
        _u[..., 3] = (_u[..., 3] * np.clip((_ye - _yy) / 3, 0, 1)).astype(np.uint8)   # 아래(팔꿈치 쪽 열린 구멍)도 잘라 짧게 — 그림이 뼈(upperRun 55)보다 길어 팔꿈치 너머로 관 끝이 튀어나왔음
    Image.fromarray(_u, 'RGBA').save(os.path.join(HERE, 'parts_work/armU.png')); P['armU']['file'] = 'parts_work/armU.png'
for n_, ec_ in T('endCuts', {}).items():   # 소매 조각 끝의 회색 열린 구멍(관 끝) 지움: top = 위 끝 흐리게, bottom = 아래 끝 둥글게 자름 — 달릴 때 먼 팔꿈치가 수염 밑으로 나오며 관 끝이 보였음 (16 네온 10-18 14:05)
    if n_ not in P: continue
    _u = np.asarray(Image.open(os.path.join(HERE, P[n_]['file'])).convert('RGBA')).copy(); _yy = np.arange(_u.shape[0])[:, None]; _xx = np.arange(_u.shape[1])[None, :]
    if ec_.get('top'): _u[..., 3] = (_u[..., 3] * np.clip((_yy - ec_['top']) / 4, 0, 1)).astype(np.uint8)
    if ec_.get('bottom'):
        _b = ec_['bottom']; _xs = np.nonzero(_u[_b, :, 3] > 100)[0]; _cx, _hw = (_xs.min() + _xs.max()) / 2, (_xs.max() - _xs.min()) / 2 + 1
        _ye = _b + 7 * np.clip(1 - ((_xx - _cx) / _hw) ** 2, 0, 1); _u[..., 3] = (_u[..., 3] * np.clip((_ye - _yy) / 3, 0, 1)).astype(np.uint8)
    Image.fromarray(_u, 'RGBA').save(os.path.join(HERE, f'parts_work/{n_}.png')); P[n_]['file'] = f'parts_work/{n_}.png'
for n_, f_ in T('pieceScale', {}).items():   # 조각 하나만 키움(시트에서 원화보다 작게 그려진 조각) — 관절점(at) 기준
    if n_ in P: m_ = P[n_]['M'].copy(); at_ = A(P[n_]['at']); P[n_]['M'] = np.c_[m_[:, :2] * f_, at_ + f_ * (m_[:, 2] - at_)]
bones = [('root', None), ('hip', 'root'), ('skirt', 'hip'), ('cape', 'hip'), ('hips', 'hip'), ('pouch', 'hip'), ('torso', 'hip'),
         ('head', 'torso'), ('tuftL', 'head'), ('tuftR', 'head'), ('beard', 'head'), ('armU', 'torso'), ('armL', 'armU'), ('pauldron', 'torso'),
         ('armF', 'torso'), ('foreF', 'armF'), ('fistF', 'foreF'), ('weapon', 'fistF')] + ([('braid', 'head' if 'beard' in SKIP else 'beard')] if BR else []) + ([('braid', 'head'), ('braid2', 'head')] if BRS else [])
bones = [b_ for b_ in bones if b_[0] not in SKIP]
world = {'root': (ROOT, 0.0), 'hip': (WAIST, 0.0), 'skirt': (WAIST, 0.0), 'cape': (NECK, 0.0)}
parts = {}; out_bones = []
BAKE = {'fistF': 'foreF'}   # 손목 꺾임 0 (8 엔진 가정): 뼈 각도 = 팔뚝, 그 차이만큼 그림을 미리 돌려 저장
def save(name, file, M, at):
    s, phi = info(M); src = os.path.join(HERE, file); dst = name + '.png'
    if name in BAKE:
        th = world[BAKE[name]][1]; d_ = phi - th
        im = np.asarray(Image.open(src).convert('RGBA')); h, w = im.shape[:2]
        R = cv2.getRotationMatrix2D((w / 2, h / 2), -math.degrees(d_), 1.0); c2, s2 = abs(R[0, 0]), abs(R[0, 1]); nw, nh = int(h * s2 + w * c2) + 6, int(h * c2 + w * s2) + 6
        R[0, 2] += nw / 2 - w / 2; R[1, 2] += nh / 2 - h / 2
        Image.fromarray(cv2.warpAffine(im, R, (nw, nh), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0)), 'RGBA').save(os.path.join(PARTS, dst))
        M = (np.vstack([M, [0, 0, 1]]) @ np.linalg.inv(np.vstack([R, [0, 0, 1]])))[:2]; s, phi = info(M)
    else: shutil.copy(src, os.path.join(PARTS, dst))
    piv = inv(M, at); parts[name] = {'src': 'parts/' + dst, 'pivot': [round(float(piv[0]), 1), round(float(piv[1]), 1)], 'scale': round(s, 4)}
    P[name]['Mfinal'] = M
    return phi
for name, parent in bones:
    if name in P: phi = save(name, P[name]['file'], P[name]['M'], P[name]['at']); world[name] = (A(P[name]['at']), phi)
    if parent is None: out_bones.append({'name': 'root', 'parent': None, 'pos': [0, 0]}); continue
    (pw, pa), (cw_, ca) = world[parent], world[name]; dv = cw_ - pw; c, sn = math.cos(-pa), math.sin(-pa)
    b = {'name': name, 'parent': parent, 'pos': [round(c * dv[0] - sn * dv[1], 1), round(sn * dv[0] + c * dv[1], 1)]}
    if abs(ca - pa) > 1e-4: b['rot'] = round(ca - pa, 4)
    if name in P: b['part'] = name
    out_bones.append(b)

# 달리기 주먹(armLF): 그림 축을 armL 그림 축과 같게 돌려 저장 → 바꿔 그려도 팔뚝 방향 그대로
aL, bL = A(PT['armL'][0]), A(PT['armL'][1]); aLF, bLF = A(PT['armLF'][0]), A(PT['armLF'][1])
rot = math.atan2(bL[1] - aL[1], bL[0] - aL[0]) - math.atan2(bLF[1] - aLF[1], bLF[0] - aLF[0]) - T('armLbind', 0)
im = np.asarray(Image.open(os.path.join(HERE, 'cut/armLF.png')).convert('RGBA')); h, w = im.shape[:2]
Mr = cv2.getRotationMatrix2D((w / 2, h / 2), -math.degrees(rot), 1.0); cs2, sn2 = abs(Mr[0, 0]), abs(Mr[0, 1]); nw, nh = int(h * sn2 + w * cs2) + 6, int(h * cs2 + w * sn2) + 6
Mr[0, 2] += nw / 2 - w / 2; Mr[1, 2] += nh / 2 - h / 2
Image.fromarray(cv2.warpAffine(im, Mr, (nw, nh), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0)), 'RGBA').save(os.path.join(PARTS, 'armLF.png'))
pLF = ap(Mr, aLF); gLF = ap(Mr, T('armLFgripImg', [32, 75]))
FS = T('foreStretch', None)
if FS:   # 손~팔꿈치를 길게(DHL 10-18 00:21 '어깨·팔꿈치 그림과 딱 맞게'): 소매 줄(y0~y1)만 늘이고 주먹은 그대로, 위 끝 fadeTop 줄은 흐리게 → 윗팔 소매 끝과 겹쳐 이어짐
    q_ = np.asarray(Image.open(os.path.join(PARTS, 'armLF.png')).convert('RGBA')).astype(np.float32); y0_, y1_, add_ = FS['y0'], FS['y1'], FS['add']
    mid_ = cv2.resize(q_[y0_:y1_], (q_.shape[1], y1_ - y0_ + add_), interpolation=cv2.INTER_CUBIC)
    q2_ = np.concatenate([q_[:y0_], mid_, q_[y1_:]], 0); yy_ = np.arange(q2_.shape[0])[:, None]
    q2_[..., 3] *= np.clip((yy_ - FS.get('fadeFrom', 2)) / FS.get('fadeTop', 7), 0, 1)
    Image.fromarray(np.clip(q2_, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(PARTS, 'armLF.png'))
    sh_ = lambda v: v + add_ * min(1, max(0, (v - y0_) / (y1_ - y0_)))   # 늘인 줄 아래 점은 그만큼 내려감
    pLF = (pLF[0], sh_(pLF[1])); gLF = (gLF[0], sh_(gLF[1]))
    if False: gLF = (gLF[0], gLF[1] + add_ * min(1, (gLF[1] - y0_) / (y1_ - y0_)) if gLF[1] < y1_ else gLF[1] + add_)
if T('runOpenHand', False):   # 달릴 때도 서 있는 팔 모양(원화 편 장갑) 그대로 흔듦 — 주먹 팔(armLF)로 안 바꿈 (16 네온 DHL 10-18 12:45 '차라리 저 모양으로 움직이는 것'). 찌르기 다가갈 때도 편 손이 자루로 감 → grip = 손바닥 가운데
    if NR: parts['armL']['grip'] = [round(float(PT['armL'][1][0]), 1), round(float(PT['armL'][1][1]), 1)]
else: parts['armL']['alt'] = 'armLF'
parts['armLF'] = {'src': 'parts/armLF.png', 'pivot': [round(float(pLF[0]), 1), round(float(pLF[1]), 1)], 'scale': T('armLFscale', parts['armL']['scale']), 'grip': [round(float(gLF[0]), 1), round(float(gLF[1]), 1)]}

# 찌르기 손: handL(앞 주먹, 자루 토막 지움) / handR(뒤 팔뚝+주먹) — 봉 뼈 원점(먼 주먹이 쥔 점)에 붙고 자루 방향을 따라 돎
wphi = world['weapon'][1]
for nm in ['handL', 'handR']:
    hj = HJ[nm]; sd = hj['shaftDir']; shutil.copy(os.path.join(HERE, hj['file']), os.path.join(PARTS, nm + '.png'))
    parts[nm] = {'src': f'parts/{nm}.png', 'pivot': hj['grip'], 'scale': K, 'shaftDir': sd}
    out_bones.append({'name': nm, 'parent': 'weapon', 'pos': [0, 0], 'rot': round((-math.pi / 2) - math.atan2(sd[1], sd[0]) - wphi, 4), 'part': nm})
parts['handL']['wrist'] = T('handLwrist', [22, 6])                     # 앞 주먹 위 소매 테 가운데 (주먹을 위에서 감싸 쥠)
te = A(T('handLtoElbow', [-0.35, -0.94])); te /= np.linalg.norm(te); parts['handL']['toElbow'] = [round(float(te[0]), 3), round(float(te[1]), 3)]
parts['handR']['elbow'] = T('handRelbow', [4, 30])                     # 뒤 팔뚝 왼쪽 끝 (소매 끝)
kx = T('handRkeepX', 0)
if kx:   # 뒤 팔뚝이 시트에서 길게 그려짐(소매 ≈ 100px, 편 손 팔뚝 소매는 35px) → 주먹 쪽 소매만 남기고 왼쪽을 부드럽게 지움, 팔꿈치 = 남은 소매 끝
    p_ = os.path.join(PARTS, 'handR.png'); a_ = np.asarray(Image.open(p_).convert('RGBA')).copy(); xx_ = np.arange(a_.shape[1])[None, :]
    a_[..., 3] = (a_[..., 3] * np.clip((xx_ - kx + 4) / 6, 0, 1)).astype(np.uint8); ys_, xs_ = np.nonzero(a_[..., 3] > 0); x0_ = int(xs_.min())
    Image.fromarray(a_[:, x0_:], 'RGBA').save(p_); parts['handR']['pivot'] = [round(parts['handR']['pivot'][0] - x0_, 1), parts['handR']['pivot'][1]]
    parts['handR']['elbow'] = [round(kx + 4 - x0_, 1), T('handRelbow', [4, 30])[1]]
if T('grip2', False):   # 2차 쥔 손 시트(22:55): 앞 주먹 소매가 왼쪽 아래(8시, 팔뚝이 아래에서 옴) · 뒷손 팔뚝 9시 — grip2.py
    H2 = json.load(open(os.path.join(HERE, 'hands2.json')))
    for nm in ['handL', 'handR']:
        h2 = H2[nm]; shutil.copy(os.path.join(HERE, h2['file']), os.path.join(PARTS, nm + '.png'))
        parts[nm] = {'src': f'parts/{nm}.png', 'pivot': h2['grip'], 'scale': h2['scale'], 'shaftDir': h2['shaftDir']}
        for k_ in ['wrist', 'toElbow', 'elbow']:
            if k_ in h2: parts[nm][k_] = h2[k_]
    for k_, v_ in T('grip2Override', {}).items(): parts[k_.split('.')[0]][k_.split('.')[1]] = v_
    # 봉 키 찌르기(staff): 뒷주먹 = 주먹 + 소매 테만(시트에서 팔뚝이 안 보임), 손목 = 테 왼쪽 가운데 / 가까운 팔뚝 = 달리기 주먹 팔뚝의 소매만(armLS)
    if T('staffKey', None):
        kx2 = T('handR2keepX', 222); p_ = os.path.join(PARTS, 'handR.png'); a_ = np.asarray(Image.open(p_).convert('RGBA')).copy(); xx_ = np.arange(a_.shape[1])[None, :]
        a_[..., 3] = (a_[..., 3] * np.clip((xx_ - kx2) / 6, 0, 1)).astype(np.uint8); ys_, xs_ = np.nonzero(a_[..., 3] > 0); x0_ = int(xs_.min())
        Image.fromarray(a_[:, x0_:], 'RGBA').save(p_); pr = parts['handR']; pr['pivot'] = [round(pr['pivot'][0] - x0_, 1), pr['pivot'][1]]
        wr = T('handR2wrist', [229, 185]); pr['wrist'] = [round(wr[0] - x0_, 1), wr[1]]; pr.pop('elbow', None)
        if T('handRflip', False):   # 뒷손은 봉 위에서 뒤집어 쥠(엎어 쥐기, DHL 10-18 00:05): 자루 줄을 축으로 위아래 뒤집음 → 주먹 덩어리가 자루 위, 소매가 왼쪽 위(어깨 쪽)
            im_ = Image.open(p_).convert('RGBA'); h_ = im_.size[1]; im_.transpose(Image.FLIP_TOP_BOTTOM).save(p_)
            pr['pivot'] = [pr['pivot'][0], round(h_ - pr['pivot'][1], 1)]; pr['wrist'] = [pr['wrist'][0], round(h_ - pr['wrist'][1], 1)]
        sl = Image.open(os.path.join(HERE, 'cut', 'armLF.png')).convert('RGBA'); cutY = T('sleeveCutY', 40); sa = np.asarray(sl).copy()
        yy_ = np.arange(sa.shape[0])[:, None]; sa[..., 3] = (sa[..., 3] * np.clip((cutY - yy_) / 4, 0, 1)).astype(np.uint8)
        Image.fromarray(sa[:cutY + 1], 'RGBA').save(os.path.join(PARTS, 'armLS.png'))
        parts['armLS'] = {'src': 'parts/armLS.png', 'pivot': PT['armLF'][0], 'scale': parts['armLF']['scale'], 'noAxis': True, 'grip': [PT['armLF'][0][0] - 1, cutY - 3]}
        LSL = T('longSleeve', None)
        if LSL:   # 찌르기 팔뚝 = 달리기 팔뚝(armLF, 소매 늘인 것)의 소매만 (DHL 10-18 00:59 '손-팔꿈치-어깨가 다 나오게': 짧은 소매로는 팔이 접혀 숨었음)
            q_ = np.asarray(Image.open(os.path.join(PARTS, 'armLF.png')).convert('RGBA')).copy(); cy_ = LSL['cutY']; yy_ = np.arange(q_.shape[0])[:, None]
            q_[..., 3] = (q_[..., 3] * np.clip((cy_ - yy_) / 3, 0, 1)).astype(np.uint8); q_ = q_[:cy_ + 1]
            xs_ = np.nonzero(q_[cy_ - 4, :, 3] > 100)[0]; grip_ = [round((xs_.min() + xs_.max()) / 2, 1), cy_ - 3]; piv_ = list(parts['armLF']['pivot'])
            EC = LSL.get('elbowCap', 0)
            if EC:   # 팔꿈치 끝(DHL 10-18 01:33 '팔꿈치를 표기한 것처럼 길게'): 소매 위 끝(흐린 잘린 면)을 둥근 팔꿈치로 EC 줄 더 늘임 — 팔꿈치 관절보다 뒤로 튀어나온 둥근 끝 + 원화 선
                top_ = LSL.get('capFrom', 14); band_ = q_[top_:top_ + 12].astype(np.float32); W_ = q_.shape[1]
                xs2_ = np.nonzero(q_[top_ + 6, :, 3] > 100)[0]; x0_, x1_ = xs2_.min(), xs2_.max(); cx_, hw_ = (x0_ + x1_) / 2, (x1_ - x0_) / 2 + .5
                cap_ = np.zeros((EC, W_, 4), np.float32); xx2_ = np.arange(W_)[None, :] + .5; ry_ = (EC - np.arange(EC)[:, None] - .5) / EC
                ell_ = np.sqrt(np.clip(1 - ry_ ** 2, 0, 1)) * hw_; dist_ = ell_ - np.abs(xx2_ - cx_)   # 타원 안쪽까지 거리(가로)
                bp_ = q_[top_ + 4:top_ + 30][q_[top_ + 4:top_ + 30, :, 3] > 200][:, :3].astype(np.float32); L_ = bp_.mean(1)
                base_ = np.median(bp_[(L_ > np.percentile(L_, 35)) & (L_ < np.percentile(L_, 85))], 0); dk_ = base_ * .72   # 소매 천 색(밝은 무늬·선 뺀 가운데)
                sh_ = np.clip(1 - dist_ / max(hw_ * .45, 1), 0, 1)[..., None]; cap_[..., :3] = base_ * (1 - sh_) + dk_ * sh_   # 가장자리로 갈수록 어둡게(둥근 면)
                inside_ = dist_ > 0; cap_[..., 3] = np.clip(dist_ * 1.5, 0, 1) * 255
                edge_ = (dist_ < 3.2) | (ry_ * EC > EC - 3.2)   # 둘레 3px = 선
                edge_ = edge_ & inside_; cap_[edge_, :3] = np.array([30, 27, 14], np.float32)
                body_ = q_[top_:].astype(np.float32); body_[..., 3] = np.maximum(body_[..., 3], 0)
                q_ = np.concatenate([cap_, body_], 0).clip(0, 255).astype(np.uint8)
                piv_ = [piv_[0], round(piv_[1] - top_ + EC - LSL.get('capOver', 6), 1)]; grip_ = [grip_[0], grip_[1] - top_ + EC]
            Image.fromarray(q_, 'RGBA').save(os.path.join(PARTS, 'armLS.png'))
            parts['armLS'] = {'src': 'parts/armLS.png', 'pivot': piv_, 'scale': parts['armLF']['scale'], 'noAxis': True, 'grip': grip_}
        if T('handRflip', False) and T('handRtoElbow', None): parts['handR']['toElbow'] = T('handRtoElbow', None)   # 뒷주먹 소매 테가 향한 쪽(그림 기준, 뒤집은 뒤)
        if T('armLSscale', None) and 'armLS' in parts: parts['armLS']['scale'] = T('armLSscale', None)   # 찌르기 팔뚝 굵기 = 달릴 때 팔(원화 소매 약 105~120 리그)과 같게 (DHL 10-18 13:18 '손에서 팔꿈치까지 두께가 뛸 때와 달라')
        S3 = T('sleeveSheet', None)
        if S3:   # 찌르기 팔 소매 = 원화 무늬로 새로 받은 소매 시트(DHL 10-18 15:25, sheets/sleeve3.png: 팔뚝 가로·윗팔 세로, 둥근 팔꿈치 끝) — 조각 시트 소매(크림이 많음) 대신
            sh3 = np.asarray(Image.open(os.path.join(HERE, S3['file'])).convert('RGB')).astype(np.float32) if 'file' in S3 else None
            def _cut3(box):   # 자홍 빼기: 보라 기운(자홍 섞인 테두리)은 어두운 선 색으로 되돌리고 알파만 남김
                c_ = sh3[box[1]:box[3], box[0]:box[2]]; r_, g_, b_ = c_[..., 0], c_[..., 1], c_[..., 2]
                pur_ = (r_ - g_ > 40) & (b_ - g_ > 40); a_ = np.where(pur_, np.clip((255 - (r_ + b_) / 2) / 230, 0, 1), 1.0)
                rgb_ = np.where(pur_[..., None], np.array([24, 21, 16], np.float32), c_)
                return np.dstack([rgb_ * a_[..., None], a_ * 255])   # 미리 곱한 알파(줄일 때 가장자리 번짐 없음)
            def _fit3(pm, f):   # 미리 곱한 RGBA 를 f 배로 줄이고 되돌림
                h_, w_ = pm.shape[:2]; q = cv2.resize(pm, (max(1, round(w_ * f)), max(1, round(h_ * f))), interpolation=cv2.INTER_AREA)
                al = q[..., 3:4] / 255; q[..., :3] = np.where(al > 1e-3, q[..., :3] / np.maximum(al, 1e-3), 0); return np.clip(q, 0, 255).astype(np.uint8)
            Wd = S3.get('width', 110)   # 리그 굵기(달릴 때 원화 팔 약 110)
            def _pcut(fn):   # 조각 시트에서 자른 조각(이미 알파) → 미리 곱한 RGBA (스카이 sleeveF·sleeveU)
                q = np.asarray(Image.open(os.path.join(HERE, fn)).convert('RGBA')).astype(np.float32); q[..., :3] *= q[..., 3:4] / 255; return q
            fo3 = S3['fore']; pm = _pcut(fo3['file']) if 'file' in fo3 else _cut3(fo3['box']); pm = np.ascontiguousarray(np.rot90(pm, -1))   # 시계 방향 90° → 팔꿈치(둥근 끝) 위, 손목 아래
            xs_ = np.nonzero(pm[pm.shape[0] // 2, :, 3] > 128)[0]; f3 = Wd / (xs_.max() - xs_.min() + 1); q_ = _fit3(pm, f3)
            ys_, xs_ = np.nonzero(q_[..., 3] > 128); cx_ = (xs_.min() + xs_.max()) / 2; R_ = (xs_.max() - xs_.min()) / 2; top_ = ys_.min()
            piv_ = [round(float(cx_), 1), round(float(top_ + R_ * fo3.get('pivotK', 1.0)), 1)]   # 팔꿈치 관절 = 둥근 끝 원의 가운데(pivotK 1) — 윗팔 둥근 끝과 같은 원
            N2o = math.hypot(parts['armLS']['grip'][0] - parts['armLS']['pivot'][0], parts['armLS']['grip'][1] - parts['armLS']['pivot'][1]) * parts['armLS']['scale']   # 지금 팔뚝 길이(찌르기 팔꿈치 자리 그대로)
            gy_ = piv_[1] + fo3.get('len', N2o); end_ = int(round(gy_ + fo3.get('past', 12)))   # 손목(뒷주먹 테 밑) + past 만큼 더 — 그 아래는 부드럽게 자름
            yy_ = np.arange(q_.shape[0])[:, None]; q_[..., 3] = (q_[..., 3] * np.clip((end_ - yy_) / 3, 0, 1)).astype(np.uint8); q_ = q_[:end_ + 1]
            Image.fromarray(q_, 'RGBA').save(os.path.join(PARTS, 'armLS.png'))
            parts['armLS'] = {'src': 'parts/armLS.png', 'pivot': piv_, 'scale': 1.0, 'noAxis': True, 'grip': [piv_[0], round(float(gy_), 1)]}
            up3 = S3.get('upper')
            if up3:   # 윗팔(찌를 때만 armU 를 바꿈 — staffKey.upperSleeve): 어깨 = pivot, 팔꿈치 원 가운데까지 len. 위쪽(어깨 너머)은 fadeTop 부터 흐림
                pm = _pcut(up3['file']) if 'file' in up3 else _cut3(up3['box']); xs_ = np.nonzero(pm[pm.shape[0] // 2, :, 3] > 128)[0]; q_ = _fit3(pm, Wd / (xs_.max() - xs_.min() + 1))
                ys_, xs_ = np.nonzero(q_[..., 3] > 128); cx_ = (xs_.min() + xs_.max()) / 2; R_ = (xs_.max() - xs_.min()) / 2; ec_ = ys_.max() - R_   # 팔꿈치 원 가운데
                py_ = ec_ - up3.get('len', 75); y0_ = int(max(0, py_ - up3.get('above', 20)))
                yy_ = np.arange(q_.shape[0])[:, None]
                RT = up3.get('roundTop', 0)
                if RT:   # 위 끝(어깨 쪽)을 둥근 어깨 + 외곽선으로: 팔 IK 각도에 따라 위 끝 모서리가 어깨갑 옆(가슴 쪽)으로 나와 곧게 잘린 면이 보였음 (16 네온 10-18 16:45)
                    from scipy import ndimage as _nd
                    xx_ = np.arange(q_.shape[1])[None, :]; ry_ = R_ * RT; top_ = py_ - ry_ + 2
                    inside_ = (yy_ >= py_) | (((xx_ - cx_) / (R_ + .5)) ** 2 + ((yy_ - py_) / ry_) ** 2 <= 1)
                    sm_ = _nd.gaussian_filter(inside_.astype(np.float32), .7); q_[..., 3] = (q_[..., 3] * np.clip(sm_ * 1.6 - .3, 0, 1)).astype(np.uint8)
                    ed_ = inside_ & ~_nd.binary_erosion(inside_, iterations=4) & (yy_ < py_ + 2) & (q_[..., 3] > 30)
                    q_[ed_, :3] = np.array([24, 21, 16], np.uint8); y0_ = int(max(0, top_ - 3))
                else: q_[..., 3] = (q_[..., 3] * np.clip((yy_ - y0_) / 6, 0, 1)).astype(np.uint8)
                # 아래 둥근 끝(검은 팔꿈치 덮개)은 지움: 팔꿈치 원은 팔뚝 둥근 끝이 덮고, 윗팔 뼈 길이(57~99)가 그림(75)보다 짧을 땐 팔뚝 밑으로 삐져나왔음
                xx_ = np.arange(q_.shape[1])[None, :]; ye_ = ec_ - R_ * up3.get('cutK', .3) + R_ * .35 * np.sqrt(np.clip(1 - ((xx_ - cx_) / (R_ + 1)) ** 2, 0, 1))
                q_[..., 3] = (q_[..., 3] * np.clip((ye_ - yy_) / 3, 0, 1)).astype(np.uint8); q_ = q_[y0_:int(ec_ + 2)]
                Image.fromarray(q_, 'RGBA').save(os.path.join(PARTS, 'armUS.png'))
                # armU 그림 축 = 아래(+y) — 원래 armU 처럼 pivot 아래로 팔꿈치
                parts['armUS'] = {'src': 'parts/armUS.png', 'pivot': [round(float(cx_), 1), round(float(py_ - y0_), 1)], 'scale': 1.0}

# 다리: 허벅지·정강이 = 가까운/먼 다리 다른 그림(S.thighImg), 뼈 길이에 맞춰 늘이되 굵기는 K 그대로(w = K/길이 배율)
d2 = lambda a, b: float(np.linalg.norm(A(b) - A(a)))
TH = T('thigh', round((d2(J['nearHip'], J['nearKnee']) + d2(J['farHip'], J['farKnee'])) / 2, 1))
SH = T('shin', round((d2(J['nearKnee'], J['nearAnkle']) + d2(J['farKnee'], J['farAnkle'])) / 2, 1))
for n in ['thighN', 'thighF', 'shinN', 'shinF', 'bootN']: shutil.copy(os.path.join(HERE, f'cut/{n}.png'), os.path.join(PARTS, n + '.png')); parts[n] = {'src': f'parts/{n}.png', 'pivot': [0, 0], 'scale': 1}
parts['boot'] = {'src': 'parts/bootN.png', 'pivot': T('ankleImg', [19, 15]), 'scale': round(K * T('bootScale', 1), 4)}; del parts['bootN']; os.rename(os.path.join(PARTS, 'bootN.png'), os.path.join(PARTS, 'boot.png')); parts['boot']['src'] = 'parts/boot.png'
def limg(n, L): a, b = PT[n]; return {'part': n, 'a': a, 'b': b, 'w': round(K / (L / d2(a, b)) * T('legWidth', 1.0), 3)}
LH = round((J['nearHip'][1] + J['farHip'][1]) / 2 - WAIST[1], 1)
legs = {'hip': [0, LH], 'thigh': TH, 'shin': SH, 'thighImg': limg('thighN', TH), 'shinImg': limg('shinN', SH),
        'boot': {'part': 'boot', 'sole': T('sole', [[-18, 10], [-15, 12], [22, 12], [25, 9]]), 'ankleRange': T('ankleRange', [-0.45, 0.4])},
        'near': {'x': round(J['nearHip'][0] - WAIST[0], 1), 'shade': 0, 'thighImg': limg('thighN', TH), 'shinImg': limg('shinN', SH)},
        'far': {'x': round(J['farHip'][0] - WAIST[0], 1), 'shade': T('farShade', .22), 'thighImg': limg('thighF', TH), 'shinImg': limg('shinF', SH)}}
for s_, o_ in T('legs', {}).items(): legs[s_].update(o_) if isinstance(o_, dict) else legs.__setitem__(s_, o_)
idle = {'near': round(J['nearAnkle'][0] - J['nearHip'][0], 1), 'far': round(J['farAnkle'][0] - J['farHip'][0], 1)}
LIFT = T('idleLift', 0)
for b_ in out_bones:
    if b_['name'] == 'hip': b_['pos'][1] = round(b_['pos'][1] - LIFT, 1)
legs['hip'][1] = legs['hip'][1] + LIFT

# 그리는 순서 (6 표): 다리 < 바지 엉덩이 < 상체 < 주머니 · 먼 윗팔 < 상체 < 먼 팔뚝 < 옆머리 < 머리 < 수염 < 코·표정(headFront) < 봉 < 먼 주먹
#   < 앞 주먹(handL) < 가까운 윗팔 < 팔뚝·손 < 어깨갑 < 뒤 팔뚝+주먹(handR)
draw = ['cape', 'legFar', 'legNear', 'armF', 'hips', 'torso', 'pouch', 'foreF', 'tuftL', 'tuftR', 'head', 'beard', 'headFront',
        'weapon', 'fistF', 'handL', 'armU', 'armL', 'pauldron', 'handR']
wim = np.asarray(Image.open(os.path.join(PARTS, 'weapon.png')))[..., 3] > 128; ys2, xs2 = np.nonzero(wim); ytop = ys2.min()
row = np.nonzero(wim[ytop + 10])[0]
parts['weapon']['tips'] = [[float(row.min()), float(ytop + 6)], [float(row.max()), float(ytop + 6)]]
_mid = [((np.nonzero(r_)[0].min() + np.nonzero(r_)[0].max()) / 2) for r_ in wim[int(wim.shape[0] * .35):int(wim.shape[0] * .8)] if r_.any()]
parts['weapon']['pivot'][0] = round(float(np.median(_mid)), 1)   # 봉 뼈 원점을 자루 가운데 선 위로(손-자루 검사, 2026-10-17)
rig = {'name': 'carden-sky', 'version': 1, 'units': 'rig px (reference x2)', 'refOrigin': [round(ROOT[0] / 2, 1), round(ROOT[1] / 2, 1)], 'refScale': 2.0, 'refLift': 0,
       'parts': parts, 'bones': out_bones, 'legs': legs, 'draw': draw, 'hidden': ['handL', 'handR'], 'faces': {}, 'idleStance': T('idleStance', idle),
       'gait': T('gait', {}), 'weaponRaise': T('weaponRaise', 16),
       'releaseOpen': True, 'dropLift': T('dropLift', 12), 'follow': T('follow', [{'bone': 'pauldron', 'src': 'armU', 'k': .3}]),
       'rearBlend': T('rearBlend', .1), 'runSlide': T('runSlide', 110), 'upperRun': T('upperRun', None), 'hemGain': T('hemGain', None), 'seamInterior': T('seamInterior', None), 'carryDrop': T('carryDrop', None), 'weaponFloor': T('weaponFloor', None), 'footReach': T('footReach', None), 'runForeBend': T('runForeBend', -.35), 'wristRange': T('wristRange', .55), 'runTilt': T('runTilt', 0),
       'bounce': T('bounce', [{'bone': 'pouch', 'stiff': 220, 'damp': 8, 'y': .6, 'rot': .005, 'max': 10},
                             {'bone': 'tuftL', 'stiff': 160, 'damp': 7, 'y': .15, 'rot': -.006, 'max': 12}, {'bone': 'tuftR', 'stiff': 170, 'damp': 7, 'y': .15, 'rot': .006, 'max': 12},
                             {'bone': 'beard', 'stiff': 260, 'damp': 10, 'y': .1, 'rot': .002, 'max': 6}]),
       'metrics': {'bodyHeight': round(GROUND - J['hairTop'][1]), 'heightWithWeapon': round(GROUND - J['staffTop'][1] + T('weaponRaise', 16)),
                   'note': 'rig units. bodyHeight = 옆머리 위 ~ 발바닥(대기), 무기 제외', 'shaftWidth': 52, 'fistWidth': 76, 'forearmThickness': 60},
       'ui': {'attack': 'thrust', 'stillReady': {'t': .22, 'cut': .36}},
       'note': '26 스카이아크 카르덴. 16 네온 카르덴과 같은 뼈대·걸음·찌르기(나침반 머리 앞, 팔 길이 고정). 다른 점: 땋은 수염 두 갈래(braid·braid2), 먼 다리 더 벌림, 인사 없음'}
for k_ in ['legs']: pass
if T('swingReach', None) is not None: rig['gait']['swingReach'] = T('swingReach', 0)
# 표정: faces.py 결과 (얼굴 조각을 머리 그림 좌표로 옮긴 패치, 코와 함께 수염 위에 그림 = headFront)
if os.path.exists(os.path.join(HERE, 'faces_out.json')):
    FO = json.load(open(os.path.join(HERE, 'faces_out.json'))); hp = parts['head']['pivot']; hs = parts['head']['scale']
    for fn, o in FO['parts'].items():
        shutil.copy(os.path.join(HERE, 'parts_work', fn + '.png'), os.path.join(PARTS, fn + '.png'))
        parts[fn] = {'src': f'parts/{fn}.png', 'pivot': [round(hp[0] - o['x0'], 1), round(hp[1] - o['y0'], 1)], 'scale': hs}
    rig['faces'] = FO['faces']; rig['headFront'] = {'clip': FO['clip'], 'facesFree': True}
else: rig['draw'].remove('headFront')
if T('pantsSkirt', False):   # DHL 23:51: 벨트 아래 ~ 무릎(바지 윗부분)은 몸 — 서 있는 자세 엉덩이+허벅지를 한 장(tools/make_pants.py)으로 skirt 뼈에, 그 아래 정강이·부츠만 걷는 게 보임
    PJ = json.load(open(os.path.join(HERE, 'pants.json'))); shutil.copy(os.path.join(HERE, 'parts_work/pants.png'), os.path.join(PARTS, 'pants.png'))
    parts['pants'] = {'src': 'parts/pants.png', 'pivot': PJ['pivot'], 'scale': 1, 'mesh': {'cols': 8, 'rows': 6}}
    parts['skirt'] = parts['pants']
    for b_ in out_bones:
        if b_['name'] == 'skirt': b_['part'] = 'skirt'
    parts['skirt'] = dict(parts['pants'], src='parts/pants.png'); del parts['pants']
    for k_ in ['draw', 'drawStaff']:
        if k_ in rig: rig[k_] = ['skirt' if x == 'hips' else x for x in rig[k_]]
    rig['hemRun'] = T('hemRun', {'lift': 10, 'knee': .5, 'heel': .3, 'reach': .2}); rig['hemLimit'] = T('hemLimit', {'up': .25, 'x': .3})
    for sd_ in ['near', 'far']: legs[sd_]['thighImg'] = dict(legs[sd_]['thighImg'], w=0.001)   # 허벅지는 바지 그림 안 — 다리 그림은 정강이·부츠만
    if 'boot' in PJ:   # 부츠·정강이 = 원화에서 오린 그림(pants_ref.py), 배율 1(원화 2배 = 리그 단위)
        for n_ in ['bootR', 'shinR', 'shinP']: shutil.copy(os.path.join(HERE, f'parts_work/{n_}.png'), os.path.join(PARTS, n_ + '.png'))
        LS_ = T('lowerLegScale', 1)   # 걷는 다리(정강이·부츠) 굵기·크기 (DHL 10-18 00:26 '살짝만 크게')
        parts['boot'] = {'src': 'parts/bootR.png', 'pivot': PJ['boot']['ankle'], 'scale': LS_}
        parts['shinR'] = {'src': 'parts/shinR.png', 'pivot': [0, 0], 'scale': 1}
        legs['boot']['sole'] = PJ['boot']['sole']
        sa_, sb_ = PJ['shin']['a'], PJ['shin']['b']; il_ = float(np.hypot(sb_[0] - sa_[0], sb_[1] - sa_[1]))
        LP = T('legsPants', None)   # 허벅지가 바지 속이면 다리 뿌리를 바지 아래쪽(가랑이 아래·바짓단 위)으로, 짧은 다리: 정강이가 거의 서서 걸음
        if LP:
            legs['hip'][1] = LP['hipY'] + T('idleLift', 0); legs['thigh'] = LP['thigh']; legs['shin'] = LP['shin']; legs['near']['x'] = LP['nearX']; legs['far']['x'] = LP['farX']
            for sd_ in ['near', 'far']: legs[sd_]['thighImg'] = dict(legs[sd_]['thighImg'], w=0.001)
        if T('shinTube', False) and 'shinP' in PJ:   # 정강이 = 바지 천 통(바짓단에서 부츠까지 이어짐, DHL 10-18 01:19)
            parts['shinP'] = {'src': 'parts/shinP.png', 'pivot': [0, 0], 'scale': 1}; sa_, sb_ = PJ['shinP']['a'], PJ['shinP']['b']; il_ = float(np.hypot(sb_[0] - sa_[0], sb_[1] - sa_[1]))
            for sd_ in ['near', 'far']: legs[sd_]['shinImg'] = {'part': 'shinP', 'a': sa_, 'b': sb_, 'w': round(il_ / legs['shin'] * T('shinTubeW', 1.0), 3)}
            legs['tube'] = {'part': 'shinP', 'a': sa_, 'b': sb_, 'k': T('shinTubeW', 1.0)}   # 다리 = 엉덩이→발목 곧은 바지 통(무릎 안 꺾임) + 부츠
        else:
            for sd_ in ['near', 'far']: legs[sd_]['shinImg'] = {'part': 'shinR', 'a': sa_, 'b': sb_, 'w': round(il_ / legs['shin'] * LS_, 3)}
    rig['bounce'] = [q for q in rig['bounce'] if q['bone'] != 'pouch']   # 주머니는 바지 그림에도 있음 → 출렁이면 두 겹
WV = T('wave', None)
if WV:   # 인사(손 흔들기, DHL 10-18 02:02) — 8 니콜과 같은 엔진 경로(waveImg): 봉이 사라지고 먼 팔(봉 팔)이 올라와 편 손을 흔듦
    # 그림 = 조각 시트의 먼 윗팔 소매(armF) · 먼 팔뚝 소매(foreF) · 편 장갑 손(waveHand, 손바닥이 보는 쪽·엄지 왼쪽 = 왼손 손바닥)
    sA, sB = A(PT['armF'][0]), A(PT['armF'][1]); fE, fW = A(PT['foreF'][0]), A(PT['foreF'][1])
    if WV.get('foreWristY'): fW = A([fW[0], WV['foreWristY']])   # 손목 점을 소매 끝보다 위로 → 소매 끝(손목 살이 보이는 입구)이 장갑 밑으로 들어감 (DHL 10-18 09:34 '팔과 손 연결 자연스럽게')
    hW, hT = A(WV.get('wristImg', [45, 84])), A(WV.get('tipImg', [42, 2])); kH = K * WV.get('handScale', 1.0); kU = K * WV.get('upperScale', 1.0); kF = K * WV.get('foreScale', 1.0)
    for nm, src, piv, sc in [('waveSleeve', 'cut/armF.png', sA, kU), ('waveFore', 'cut/foreF.png', fE, kF), ('waveHandW', 'cut/waveHand.png', hW, kH)]:
        shutil.copy(os.path.join(HERE, src), os.path.join(PARTS, nm + '.png')); parts[nm] = {'src': f'parts/{nm}.png', 'pivot': [round(float(piv[0]), 1), round(float(piv[1]), 1)], 'scale': round(sc, 4)}
    HC = WV.get('handCutY')
    if HC:   # 장갑 소매 테의 아래쪽 '열린 입구'(안쪽 타원) 를 잘라 냄 — 장갑 테 = 소매와 같은 올리브 천이라 소매 위에 겹치면 한 팔로 이어짐(입구 두 개가 마주 보이지 않게)
        q_ = np.asarray(Image.open(os.path.join(PARTS, 'waveHandW.png')).convert('RGBA')).copy(); yy_ = np.arange(q_.shape[0])[:, None]
        q_[..., 3] = (q_[..., 3] * np.clip((HC - yy_) / WV.get('handCutFade', 3), 0, 1)).astype(np.uint8); Image.fromarray(q_, 'RGBA').save(os.path.join(PARTS, 'waveHandW.png'))
    if WV.get('hideSleeve'):   # 먼 윗팔 소매는 수염·몸 뒤 — 밖으로 삐져나온 토막이 '뒤의 그림'처럼 보여 안 그림(팔뚝 팔꿈치 끝이 몸 뒤로 들어감)
        q_ = np.asarray(Image.open(os.path.join(PARTS, 'waveSleeve.png')).convert('RGBA')).copy(); q_[..., 3] = 0; Image.fromarray(q_, 'RGBA').save(os.path.join(PARTS, 'waveSleeve.png'))
    EX = WV.get('elbowExt', 0)
    if EX:   # 팔꿈치를 길게(DHL 10-18 02:17 '뒤의 이미지가 보이지 않게'): 팔뚝 소매의 팔꿈치 쪽(둥근 끝 아래 줄 a~b)만 EX 줄 늘여 관절 뒤로 튀어나오게 → 수염 옆 윗팔 소매 토막을 덮음. 팔꿈치 관절·손목 자리는 그대로
        q_ = np.asarray(Image.open(os.path.join(PARTS, 'waveFore.png')).convert('RGBA')).astype(np.float32); a_, b_ = WV.get('extBand', [5, 20])
        mid_ = cv2.resize(q_[a_:b_], (q_.shape[1], b_ - a_ + EX), interpolation=cv2.INTER_CUBIC)
        Image.fromarray(np.concatenate([q_[:a_], mid_, q_[b_:]], 0).clip(0, 255).astype(np.uint8), 'RGBA').save(os.path.join(PARTS, 'waveFore.png'))
        fE = fE + A([0, EX]); fW = fW + A([0, EX]); parts['waveFore']['pivot'] = [round(float(fE[0]), 1), round(float(fE[1]), 1)]
    parts['waveSleeve']['elbow'] = [round(float(sB[0]), 1), round(float(sB[1]), 1)]; parts['waveFore']['wrist'] = [round(float(fW[0]), 1), round(float(fW[1]), 1)]; parts['waveHandW']['tip'] = [round(float(hT[0]), 1), round(float(hT[1]), 1)]
    armFb = next(b for b in out_bones if b['name'] == 'armF')
    out_bones.append({'name': 'wSleeve', 'parent': 'torso', 'pos': list(armFb['pos']), 'part': 'waveSleeve'})
    out_bones.append({'name': 'wFore', 'parent': 'wSleeve', 'pos': [round(float((sB - sA)[0] * kU), 1), round(float((sB - sA)[1] * kU), 1)], 'part': 'waveFore'})
    out_bones.append({'name': 'wHand', 'parent': 'wFore', 'pos': [round(float((fW - fE)[0] * kF), 1), round(float((fW - fE)[1] * kF), 1)], 'part': 'waveHandW'})
    ang_ = lambda v: round(math.atan2(v[1], v[0]), 4)
    rig['waveImg'] = {'upper': ang_(sB - sA), 'fore': ang_(fW - fE), 'hand': ang_(hT - hW), 'handRest': WV.get('handRest', -0.357), 'shoulderShift': WV.get('shoulderShift', [0, 0]),
                      'up': WV.get('up', 1.15), 'fore0': WV.get('fore0', -1.2), 'openAt': WV.get('openAt', .45), 'openWa': WV.get('openWa', .05), 'note': '먼 팔(봉 팔) 손 흔들기: 소매는 상체 뒤, 팔뚝은 수염 옆, 편 손은 맨 앞'}
    rig['drawWave'] = WV.get('draw') or ['cape', 'legFar', 'legNear', 'armF', 'wSleeve', 'skirt' if T('pantsSkirt', False) else 'hips', 'torso', 'pouch', 'foreF', 'tuftL', 'tuftR', 'head', 'beard', 'headFront',
                                          'weapon', 'fistF', 'wFore', 'handL', 'armU', 'armL', 'pauldron', 'handR', 'wHand']
    rig['hidden'] = rig['hidden'] + ['wSleeve', 'wFore', 'wHand']; rig['ui']['touch'] = 'wave'
    SP_ = WV.get('splitY')
    if SP_ is not None:   # 팔뚝을 둘로(DHL 10-18 09:50 '손목 쪽은 좋다, 팔꿈치 쪽은 수염 아래로'): 손목 쪽 = 수염 앞(wFore), 팔꿈치 쪽 = 수염 뒤(wCuff 뼈 — 엔진이 인사 동안 wSleeve 와 같이 켜고 끔)
        q_ = np.asarray(Image.open(os.path.join(PARTS, 'waveFore.png')).convert('RGBA')).copy()
        Image.fromarray(q_, 'RGBA').save(os.path.join(PARTS, 'waveForeLo.png'))   # 뒤 조각 = 팔뚝 전체(수염 밖으로 나온 곳은 앞 조각과 같은 그림)
        yy_ = np.arange(q_.shape[0])[:, None]; fd_ = WV.get('splitFade', 8)
        q_[..., 3] = (q_[..., 3] * np.clip((yy_ - (SP_ - fd_ / 2)) / fd_, 0, 1)).astype(np.uint8)   # 앞 조각 = 손목 쪽만(팔꿈치 쪽은 부드럽게 사라짐)
        Image.fromarray(q_, 'RGBA').save(os.path.join(PARTS, 'waveFore.png'))
        parts['waveForeLo'] = dict(parts['waveFore']); parts['waveForeLo']['src'] = 'parts/waveForeLo.png'
        out_bones.append({'name': 'wCuff', 'parent': 'wFore', 'pos': [0, 0], 'part': 'waveForeLo'})
        rig['hidden'] = rig['hidden'] + ['wCuff']
        if 'wCuff' not in rig['drawWave']: rig['drawWave'].insert(rig['drawWave'].index(WV.get('splitAfter', 'pouch')) + 1, 'wCuff')
for nm_ in ['handL', 'handR']:   # 검사용(audit_extra 손-자루): 쥔 손의 자루 점 = 쥔 점(pivot) — 없으면 그림 가운데로 재서 소맷단까지 든 넓은 뒷손이 자루에서 떨어진 것처럼 나옴 (26 스카이 10-19 01:58)
    if nm_ in parts: parts[nm_]['shaft'] = list(parts[nm_]['pivot'])
th = T('thrustFull', None)
if th: rig['actions'] = {'thrust': th}
if T('staffKey', None): rig['staffKey'] = T('staffKey', None)
if T('staffKey', None): rig['drawStaff'] = ['cape', 'legFar', 'legNear', 'armF', 'skirt' if T('pantsSkirt', False) else 'hips', 'torso', 'pouch', 'foreF', 'tuftL', 'tuftR', 'head', 'beard', 'headFront', 'weapon', 'armU', 'armL', 'pauldron', 'fistF', 'handL', 'handR']   # 봉 찌르기: 봉 < 가까운 팔 < 주먹 (DHL 10-18 00:21 '앞 팔이 무기 위로' — 23:50 의 '팔 < 봉'에서 바꿈)
if T('gameRef', None): rig['gameRef'] = T('gameRef', None)
DSO = T('drawStaffOrder', None)
if DSO and 'drawStaff' in rig:   # 찌르기 팔 그리는 순서: 팔뚝(팔꿈치) > 어깨갑 > 윗팔 (DHL 10-18 12:45 '팔꿈치 레이어가 어깨보다 앞으로' — 이전부터 반복 지적, 메모)
    i0 = rig['drawStaff'].index('weapon'); rig['drawStaff'] = rig['drawStaff'][:i0] + DSO
for k_ in ['draw', 'drawStaff', 'drawWave']:
    if k_ in rig:
        rig[k_] = [x for x in rig[k_] if x not in SKIP]
        if BR and 'braid' not in rig[k_]: rig[k_].insert(rig[k_].index('beard' if 'beard' in rig[k_] else 'head') + 1, 'braid')
        if BRS and 'braid' not in rig[k_]: i_ = rig[k_].index('head') + 1; rig[k_][i_:i_] = ['braid', 'braid2']
rig['bounce'] = [q for q in rig['bounce'] if q['bone'] not in SKIP] + ([BR['bounce']] if BR and BR.get('bounce') else []) + (BRS.get('bounce', []) if BRS else [])   # 게임 그림(characters/char_0006.png) 위 발 자리 — 도감 칸에서 몸(골반)이 가운데 오게
_h = hashlib.sha1()
for _f in sorted(os.listdir(PARTS)): _h.update(_f.encode()); _h.update(open(os.path.join(PARTS, _f), 'rb').read())
_h.update(json.dumps(rig, sort_keys=True).encode()); rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(PK, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(PK, 'rig.def.js'), 'w').write("window.MR_RIG_DEFS=window.MR_RIG_DEFS||{};window.MR_RIG_DEFS['carden-sky']=" + json.dumps(rig, ensure_ascii=False, separators=(',', ':')) + ";\n")
print('ok', len(parts), 'parts; EN', EN.round(1), 'EF', EF.round(1), 'WF', WF.round(1), 'L1,L2', round(L1, 1), round(L2, 1), 'd', round(float(d), 1), 'thigh', TH, 'shin', SH, 'legs', legs['near']['x'], legs['far']['x'], 'idle', idle)
