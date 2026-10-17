"""18 네온 니콜 리그 조립 (8 러스트 니콜 rust-fork-girl v15 구조 1:1) — 2026-10-17
입력: cut/*.png(조각), parts_work/*.png(자루 토막 지운 손), sift_result.json·fix_result.json(조각→기준 배치), joints.json, hands.json
출력: ../rig.json, ../parts/*.png, ../rig.def.js
단위: 기준 그림 ref1024(= 512 마이룸 그림의 2배) 픽셀 = 리그 단위. 뿌리(root) = 발바닥 선 위 한 점.
실행: cd source && python3 -I build_neon.py
"""
import json, math, os, shutil
import numpy as np, cv2
from PIL import Image
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from limbs import ends
HERE = os.path.dirname(os.path.abspath(__file__)); PK = os.path.join(HERE, '..'); PARTS = os.path.join(PK, 'parts')
os.makedirs(PARTS, exist_ok=True)
S = json.load(open(os.path.join(HERE, 'sift_result.json'))); F = json.load(open(os.path.join(HERE, 'fix_result.json')))
J = json.load(open(os.path.join(HERE, 'joints.json'))); HJ = json.load(open(os.path.join(HERE, 'hands.json')))
TUNE = json.load(open(os.path.join(HERE, 'tune.json'))) if os.path.exists(os.path.join(HERE, 'tune.json')) else {}
A = np.array; ap = lambda m, p: m[:, :2] @ A(p, float) + m[:, 2]
inv = lambda m, r: np.linalg.solve(m[:, :2], A(r, float) - m[:, 2])
def info(m): return math.hypot(m[0, 0], m[1, 0]), math.atan2(m[1, 0], m[0, 0])
def simT(s, phi, src, dst):                       # 배율 s, 회전 phi 로 조각 점 src → 기준 점 dst
    c, sn = math.cos(phi) * s, math.sin(phi) * s; m = A([[c, -sn, 0], [sn, c, 0]], float); m[:, 2] = A(dst) - m[:, :2] @ A(src, float); return m
def seg(s, a, b, P, Q):                          # 조각 선분 a→b 방향을 P→Q 방향에 맞추고 a→P (배율 s 고정)
    phi = math.atan2(Q[1] - P[1], Q[0] - P[0]) - math.atan2(b[1] - a[1], b[0] - a[0]); return simT(s, phi, a, P)
def T(name, default): return TUNE.get(name, default)

SARM = S['armL']['s']                            # 팔 조각 배율(1차 시트 같은 줄) ≈ 1.236
GROUND = 1012.0
H = A(J['H']); NECK = A(J['NECK']); EN = A(J['EN']); G = A(J['G'])
ROOT = A([H[0] - 34, GROUND])

P = {}   # 이름 -> dict(file, M, at(관절, 기준 좌표))
P['torso'] = dict(file='cut/torso.png', M=A(S['torso']['M']), at=H)
P['skirt'] = dict(file=T('coatFile', 'cut/coatBack.png'), M=A(S['coat']['M']))   # 2026-10-17: 코트 뒤판(트임 뒤 안감 포함). 앞자락은 coatFlap
cw = Image.open(os.path.join(HERE, 'cut/coat.png')).size; P['skirt']['at'] = ap(P['skirt']['M'], (cw[0] / 2, 18))
P['collarBack'] = None
P['head'] = dict(file='cut/head.png', M=A(S['head']['M']), at=NECK)
P['collar'] = dict(file='parts_work/collar.png', M=A(S['collar']['M']))
cs_ = Image.open(os.path.join(HERE, 'cut/collar.png')).size; P['collar']['at'] = ap(P['collar']['M'], (cs_[0] / 2, cs_[1] / 2))
P['collarBack'] = dict(file='parts_work/collarBack.png', M=P['collar']['M'], at=P['collar']['at'])
SN0 = A(J['SN']); LU = 59.9 * SARM; SN = EN + (SN0 - EN) / np.linalg.norm(SN0 - EN) * LU
P['pauldron'] = dict(file='cut/pauldron.png', M=A(S['pauldron']['M']), at=SN)
SF = A(J['SF']) + A(T('SFoff', [0, 0]))
P['pauldronF'] = dict(file='cut/pauldronF.png', M=A(F['pauldronF']['M']), at=SF)
(aU, _), (bU, _) = ends(os.path.join(HERE, 'cut/armU.png'))[0]; aU, bU = (aU, bU) if aU[1] < bU[1] else (bU, aU)
P['armU'] = dict(file='cut/armU.png', M=seg(SARM, aU, bU, SN, EN), at=SN)
P['armL'] = dict(file='cut/armL.png', M=A(S['armL']['M']), at=EN)
# 먼 팔: 어깨 SF → 손목(먼 주먹 그림의 커프 가운데) 두 관절 IK, 팔꿈치 아래
MF = A(S['fistF']['M']) @ A([[1, 0, HJ['fistF']['off'][0]], [0, 1, HJ['fistF']['off'][1]], [0, 0, 1]], float)
WR_IMG = A(T('fistWristImg', [62 - HJ['fistF']['off'][0], 112 - HJ['fistF']['off'][1]]))
WF = ap(MF, WR_IMG)
(aF, _), (bF, _) = ends(os.path.join(HERE, 'cut/armF.png'))[0]; aF, bF = (aF, bF) if aF[1] < bF[1] else (bF, aF)
(aO, _), (bO, _) = ends(os.path.join(HERE, 'cut/foreF.png'))[0]; aO, bO = (aO, bO) if aO[1] < bO[1] else (bO, aO)
L1 = np.linalg.norm(bF - aF) * SARM; L2 = np.linalg.norm(bO - aO) * SARM
d = np.linalg.norm(WF - SF); dd = min(d, (L1 + L2) * .995); base = math.atan2(WF[1] - SF[1], WF[0] - SF[0])
al = math.acos(np.clip((L1 * L1 + dd * dd - L2 * L2) / (2 * L1 * dd), -1, 1))
E1 = SF + L1 * A([math.cos(base + al), math.sin(base + al)]); E2 = SF + L1 * A([math.cos(base - al), math.sin(base - al)])
EF = E1 if E1[1] > E2[1] else E2
P['armF'] = dict(file='cut/armF.png', M=seg(SARM, aF, bF, SF, EF), at=SF)
P['foreF'] = dict(file='cut/foreF.png', M=seg(SARM, aO, bO, EF, WF), at=EF)
P['fistF'] = dict(file=HJ['fistF']['file'], M=MF, at=WF)
# 창: 새 창 그림(weaponW)을 0.42배로 줄여 저장, 리그 배율 0.8. 세로 기준 그림과 같은 선(자루 가운데 x=753.3, 위끝 y=3)
wim = Image.open(os.path.join(HERE, 'cut/weaponW.png')); wa = np.asarray(wim)[..., 3] > 128; ys, xs = np.nonzero(wa)
x0, y0, x1, y1 = xs.min() - 6, ys.min() - 6, xs.max() + 7, ys.max() + 7; f = .42
wsmall = wim.crop((x0, y0, x1, y1)); wsmall = wsmall.resize((round(wsmall.width * f), round(wsmall.height * f)), Image.LANCZOS)
os.makedirs(os.path.join(HERE, 'parts_work'), exist_ok=True); wsmall.save(os.path.join(HERE, 'parts_work/weapon.png'))
kW = (1007 - 3) / (3031 - 41) / f
cx = (1024.2 - x0) * f; top = (41 - y0) * f
MW = A([[kW, 0, 753.3 - cx * kW], [0, kW, 3 - top * kW - T('weaponRaise', 16)]], float)
P['weapon'] = dict(file='parts_work/weapon.png', M=MW, at=G)
# 꼬리: 허리 뒤에서 아래로, 원화처럼 뒤로 살짝 펼침
tw = Image.open(os.path.join(HERE, 'cut/tails.png')).size
TROOT = A(T('tailsRoot', [438, 640])); P['cape'] = dict(file='cut/tails.png', M=simT(T('tailsScale', .98), T('tailsRot', .5), (tw[0] / 2, 10), TROOT), at=TROOT)
for nm in ['pouchA', 'pouchB']:
    m = A(S[nm]['M']); sz = Image.open(os.path.join(HERE, f'cut/{nm}.png')).size; P[nm] = dict(file=f'cut/{nm}.png', M=m, at=ap(m, (sz[0] / 2, sz[1] * .3)))

bones = [('root', None), ('hip', 'root'), ('skirt', 'hip'), ('cape', 'hip'), ('torso', 'hip'), ('pouchA', 'skirt'), ('pouchB', 'skirt'),
         ('collarBack', 'torso'), ('collar', 'torso'), ('head', 'torso'), ('armU', 'torso'), ('armL', 'armU'), ('pauldron', 'torso'), ('pauldronF', 'torso'),
         ('armF', 'torso'), ('foreF', 'armF'), ('fistF', 'foreF'), ('weapon', 'fistF')]
world = {'root': (ROOT, 0.0), 'hip': (H, 0.0)}
parts = {}; out_bones = []
BAKE = {'fistF': 'foreF'}   # 뼈 각도를 부모와 같게(쉬는 자세 손목 꺾임 0 — 8 니콜 엔진 가정) 하고 그 차이만큼 그림을 미리 돌려 저장
def save(name, file, M, at):
    s, phi = info(M); src = os.path.join(HERE, file); dst = name + '.png'
    if name in BAKE:
        th = world[BAKE[name]][1]; d_ = phi - th
        im = np.asarray(Image.open(src).convert('RGBA')); h, w = im.shape[:2]
        R = cv2.getRotationMatrix2D((w / 2, h / 2), -math.degrees(d_), 1.0); c2, s2 = abs(R[0, 0]), abs(R[0, 1]); nw, nh = int(h * s2 + w * c2) + 6, int(h * c2 + w * s2) + 6
        R[0, 2] += nw / 2 - w / 2; R[1, 2] += nh / 2 - h / 2
        Image.fromarray(cv2.warpAffine(im, R, (nw, nh), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0)), 'RGBA').save(os.path.join(PARTS, dst))
        M = M @ np.linalg.inv(np.vstack([R, [0, 0, 1]]))[:2] if False else (np.vstack([M, [0, 0, 1]]) @ np.linalg.inv(np.vstack([R, [0, 0, 1]])))[:2]
        s, phi = info(M); piv = inv(M, at); BAKEM[name] = (R, M)
    else:
        shutil.copy(src, os.path.join(PARTS, dst)); piv = inv(M, at)
    parts[name] = {'src': 'parts/' + dst, 'pivot': [round(float(piv[0]), 1), round(float(piv[1]), 1)], 'scale': round(s, 4)}
    return phi
BAKEM = {}
for name, parent in bones:
    if name in P: phi = save(name, P[name]['file'], P[name]['M'], P[name]['at']); world[name] = (A(P[name]['at'], float), phi)
    if parent is None: out_bones.append({'name': 'root', 'parent': None, 'pos': [0, 0]}); continue
    (pw, pa), (cw_, ca) = world[parent], world[name]; dv = cw_ - pw; c, sn = math.cos(-pa), math.sin(-pa)
    b = {'name': name, 'parent': parent, 'pos': [round(c * dv[0] - sn * dv[1], 1), round(sn * dv[0] + c * dv[1], 1)]}
    if abs(ca - pa) > 1e-4: b['rot'] = round(ca - pa, 4)
    if name in P: b['part'] = name
    out_bones.append(b)
parts['skirt']['mesh'] = {'cols': 8, 'rows': 9}; parts['cape']['mesh'] = {'cols': 6, 'rows': 7}
# 코트 앞자락: 뒤판과 같은 뼈·배율, 그림 위치만 옮김(sheets/coatSplit 에서 맞춘 평행이동 motion/flapM.npy, 겹침 IoU 0.997)
FLM = np.load(os.path.join(HERE, 'motion', 'flapM.npy')); FOFF = [float(FLM[0, 2]), float(FLM[1, 2])]
shutil.copy(os.path.join(HERE, 'cut/coatFlap.png'), os.path.join(PARTS, 'coatFlap.png'))
sp_ = parts['skirt']['pivot']; parts['coatFlap'] = {'src': 'parts/coatFlap.png', 'pivot': [round(sp_[0] - FOFF[0], 1), round(sp_[1] - FOFF[1], 1)], 'scale': parts['skirt']['scale'], 'mesh': {'cols': 3, 'rows': 9}}
out_bones.append({'name': 'coatFlap', 'parent': 'skirt', 'pos': [0, 0], 'part': 'coatFlap'})

# 달리기 주먹(armLF): 그림 축을 armL 그림 축과 같게 돌려 저장 → 바꿔 그려도 팔뚝 방향이 그대로
def axis(fn):
    (a, _), (b, _) = ends(fn)[0]; a, b = (a, b) if a[1] < b[1] else (b, a); return a, b
aL, bL = axis(os.path.join(HERE, 'cut/armL.png')); aLF, bLF = axis(os.path.join(HERE, 'cut/armLF.png'))
rot = math.atan2(bL[1] - aL[1], bL[0] - aL[0]) - math.atan2(bLF[1] - aLF[1], bLF[0] - aLF[0])
im = np.asarray(Image.open(os.path.join(HERE, 'cut/armLF.png')).convert('RGBA')); h, w = im.shape[:2]
Mr = cv2.getRotationMatrix2D((w / 2, h / 2), -math.degrees(rot), 1.0); cs2, sn2 = abs(Mr[0, 0]), abs(Mr[0, 1]); nw, nh = int(h * sn2 + w * cs2) + 6, int(h * cs2 + w * sn2) + 6
Mr[0, 2] += nw / 2 - w / 2; Mr[1, 2] += nh / 2 - h / 2
Image.fromarray(cv2.warpAffine(im, Mr, (nw, nh), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0, 0)), 'RGBA').save(os.path.join(PARTS, 'armLF.png'))
pLF = ap(Mr, aLF); gLF = ap(Mr, T('armLFgripImg', [34, 125]))
parts['armL']['alt'] = 'armLF'
parts['armLF'] = {'src': 'parts/armLF.png', 'pivot': [round(float(pLF[0]), 1), round(float(pLF[1]), 1)], 'scale': parts['armL']['scale'], 'grip': [round(float(gLF[0]), 1), round(float(gLF[1]), 1)]}

# 팔꿈치 두꺼움 정리(DHL 14:09 추천 2): 팔뚝 그림 윗부분(관절 위 검은 소매)이 윗팔의 검은 아래 토막과 겹쳐 팔꿈치가 굵어 보임
# → 팔뚝 그림을 관절점 위 keep px 까지만 남기고 feather px 동안 부드럽게 지움 (윗팔 끝 둥근 마개가 관절을 덮음)
_tr = T('armLtrim', None)
if _tr:
    _u = np.array(bL, float) - np.array(aL, float); _u /= np.linalg.norm(_u)
    if _u[1] < 0: _u = -_u                                   # 팔뚝 축: 관절 → 손 (아래)
    for _nm in ['armL', 'armLF']:
        _p = os.path.join(PARTS, _nm + '.png'); _a = np.asarray(Image.open(_p).convert('RGBA')).copy(); _h, _w = _a.shape[:2]
        _pv = np.array(parts[_nm]['pivot'], float); _yy, _xx = np.mgrid[0:_h, 0:_w]
        _t = (_xx - _pv[0]) * _u[0] + (_yy - _pv[1]) * _u[1]
        _k = np.clip((_t + _tr['keep'] + _tr['feather']) / _tr['feather'], 0, 1); _k = _k * _k * (3 - 2 * _k)
        _a[..., 3] = (_a[..., 3] * _k).astype(np.uint8); Image.fromarray(_a, 'RGBA').save(_p)

# 찌르기 손: handL(앞 주먹만, 8 방식) / handR(뒤 팔뚝+주먹 한 장) — 창 뼈 원점(먼 주먹이 쥔 점)에 붙고 자루 방향을 따라 돎
wphi = world['weapon'][1]
G2 = T('grip2', None)   # 쥔 손 2차 시트(14:14, 자루 수평·엄지 위·빛 왼쪽 위): {'scale': SARM 대비 배율}
for nm in ['handL', 'handR']:
    hj = HJ[nm + '2'] if G2 else HJ[nm]; sd = hj['shaftDir']; shutil.copy(os.path.join(HERE, hj['file']), os.path.join(PARTS, nm + '.png'))
    parts[nm] = {'src': f'parts/{nm}.png', 'pivot': hj['grip'], 'scale': round(SARM * (G2['scale'] if G2 else 1), 4), 'shaftDir': sd}
    r_ = (-math.pi / 2) - math.atan2(sd[1], sd[0]) - wphi
    out_bones.append({'name': nm, 'parent': 'weapon', 'pos': [0, 0], 'rot': round(r_, 4), 'part': nm})
off = HJ['handL2' if G2 else 'handL']['off']; wL = A(T('handL2wristCut' if G2 else 'handLwristCut', [98, 63])) - off; parts['handL']['wrist'] = [round(float(wL[0]), 1), round(float(wL[1]), 1)]
if T('handLflip', False) and not G2:   # 앞(먼) 주먹 좌우 손 반대 → 자루 축 기준 위아래 뒤집기: 엄지가 위(창끝 쪽)로 (DHL 13:13 '반대 손 모양')
    pim = Image.open(os.path.join(PARTS, 'handL.png')); hh = pim.height; pim.transpose(Image.FLIP_TOP_BOTTOM).save(os.path.join(PARTS, 'handL.png'))
    pl = parts['handL']; pl['pivot'] = [pl['pivot'][0], round(hh - pl['pivot'][1], 1)]; pl['shaftDir'] = [pl['shaftDir'][0], -pl['shaftDir'][1]]
    # wrist(팔뚝이 붙는 점)는 그대로 둠: 팔뚝은 여전히 왼쪽 아래에서 들어옴 → 창·뒷손 자리 변화 없음
    py0 = hh - pl['pivot'][1]; pl['wrist'] = [pl['wrist'][0], round(pl['wrist'][1] - py0 + pl['pivot'][1], 1)]   # 쥔 점 기준 같은 자리
    for b_ in out_bones:
        if b_['name'] == 'handL': sd_ = pl['shaftDir']; b_['rot'] = round((-math.pi / 2) - math.atan2(sd_[1], sd_[0]) - wphi, 4)
te = A(T('handL2toElbow' if G2 else 'handLtoElbow', [-63, 37]), float); te /= np.linalg.norm(te); parts['handL']['toElbow'] = [round(float(te[0]), 3), round(float(te[1]), 3)]
off = HJ['handR2' if G2 else 'handR']['off']; eR = A(T('handR2elbowCut' if G2 else 'handRelbowCut', [47, 39])) - off; parts['handR']['elbow'] = [round(float(eR[0]), 1), round(float(eR[1]), 1)]

# 손 흔들기(시트 20번대): 먼 팔 소매(윗팔) · 팔뚝 · 편 손
(sA, _), (sB, _) = axis(os.path.join(HERE, 'cut/waveSleeve.png')), (None, None)
sA, sB = axis(os.path.join(HERE, 'cut/waveSleeve.png'))
fo = ends(os.path.join(HERE, 'cut/waveFore.png'))[0]; fE, fW = (fo[0][0], fo[1][0]) if fo[0][0][1] > fo[1][0][1] else (fo[1][0], fo[0][0])   # 팔꿈치 = 아래 끝
hW = A(T('waveWristImg', [38, 74])); hT = A(T('waveTipImg', [43, 5]))
for nm, src, piv in [('waveSleeve', 'cut/waveSleeve.png', sA), ('waveFore', 'cut/waveFore.png', fE), ('waveHandW', 'cut/waveHandW.png', hW)]:
    shutil.copy(os.path.join(HERE, src), os.path.join(PARTS, nm + '.png')); parts[nm] = {'src': f'parts/{nm}.png', 'pivot': [round(float(piv[0]), 1), round(float(piv[1]), 1)], 'scale': round(SARM, 4)}
parts['waveSleeve']['elbow'] = [round(float(sB[0]), 1), round(float(sB[1]), 1)]; parts['waveFore']['wrist'] = [round(float(fW[0]), 1), round(float(fW[1]), 1)]; parts['waveHandW']['tip'] = [round(float(hT[0]), 1), round(float(hT[1]), 1)]
armFb = next(b for b in out_bones if b['name'] == 'armF')
out_bones.append({'name': 'wSleeve', 'parent': 'torso', 'pos': armFb['pos'], 'part': 'waveSleeve'})
out_bones.append({'name': 'wFore', 'parent': 'wSleeve', 'pos': [round(float((sB - sA)[0] * SARM), 1), round(float((sB - sA)[1] * SARM), 1)], 'part': 'waveFore'})
out_bones.append({'name': 'wHand', 'parent': 'wFore', 'pos': [round(float((fW - fE)[0] * SARM), 1), round(float((fW - fE)[1] * SARM), 1)], 'part': 'waveHandW'})
ang = lambda v: round(math.atan2(v[1], v[0]), 4)
waveImg = {'upper': ang(sB - sA), 'fore': ang(fW - fE), 'hand': ang(hT - hW), 'handRest': -0.357, 'shoulderShift': T('waveShoulderShift', [0, 18]), 'up': 1.15, 'fore0': -1.2,
           'note': '먼 팔(창 팔) 손 흔들기: 소매는 상체 뒤, 먼 어깨갑(pauldronF)이 어깨를 덮음'}

# 다리: 허벅지·정강이 그림을 뼈 길이에 맞춰 늘림(두께는 w), 부츠 = 1차 시트 부츠(배율 ≈ 1.18)
(tA, tWd), (tB, _) = ends(os.path.join(HERE, 'cut/thigh.png'))[0]; tA, tB = (tA, tB) if tA[1] < tB[1] else (tB, tA)
(nA, nWd), (nB, _) = ends(os.path.join(HERE, 'cut/shin.png'))[0]; nA, nB = (nA, nB) if nA[1] < nB[1] else (nB, nA)
for n in ['thigh', 'shin', 'boot']: shutil.copy(os.path.join(HERE, f'cut/{n}.png'), os.path.join(PARTS, n + '.png'))
kB = T('bootScale', 1.177); ank = T('ankleImg', [45, 30])
parts['thigh'] = {'src': 'parts/thigh.png', 'pivot': [round(float(tA[0]), 1), round(float(tA[1]), 1)], 'scale': 1}
parts['shin'] = {'src': 'parts/shin.png', 'pivot': [round(float(nA[0]), 1), round(float(nA[1]), 1)], 'scale': 1}
parts['boot'] = {'src': 'parts/boot.png', 'pivot': ank, 'scale': kB}
LH = T('legHipY', 70); thighL = T('thigh', 128); shinL = T('shin', 130)
sT = thighL / np.linalg.norm(tB - tA); sS = shinL / np.linalg.norm(nB - nA)
legs = {'hip': [0, LH], 'thigh': thighL, 'shin': shinL,
        'thighImg': {'part': 'thigh', 'a': [round(float(tA[0]), 1), round(float(tA[1]), 1)], 'b': [round(float(tB[0]), 1), round(float(tB[1]), 1)], 'w': round(T('thighWidth', 74) / (tWd * sT), 3)},
        'shinImg': {'part': 'shin', 'a': [round(float(nA[0]), 1), round(float(nA[1]), 1)], 'b': [round(float(nB[0]), 1), round(float(nB[1]), 1)], 'w': round(T('shinWidth', 54) / (nWd * sS), 3)},
        'boot': {'part': 'boot', 'sole': T('sole', [[-38, 50], [-30, 58], [45, 58], [66, 50]]), 'ankleRange': T('ankleRange', [-0.62, 0.45])},
        'near': {'x': T('nearX', 24), 'shade': 0}, 'far': {'x': T('farX', -34), 'shade': T('farShade', 0.16)}}

# 서 있을 때 골반이 다리 때문에 내려가는 양(hipDrop)만큼 몸을 미리 올려 둠 → 서 있는 자세가 원화와 같은 높이 (다리 관절 위치는 그대로)
LIFT = T('idleLift', 14)
for b_ in out_bones:
    if b_['name'] == 'hip': b_['pos'][1] = round(b_['pos'][1] - LIFT, 1)
legs['hip'][1] = legs['hip'][1] + LIFT
# 무기는 두 주머니보다 앞 (DHL 13:04) · 가까운 팔은 윗팔(어깨 쪽) 뒤, 팔뚝·손 앞 — 8 러스트 니콜처럼 (DHL 13:10)
draw = ['cape', 'legFar', 'legNear', 'armF', 'torso', 'collarBack', 'pauldronF', 'skirt', 'coatFlap', 'pouchB', 'pouchA', 'weapon', 'foreF', 'fistF', 'handL', 'armU', 'armL', 'pauldron', 'handR', 'head', 'collar']
drawWave = ['cape', 'legFar', 'legNear', 'armF', 'wSleeve', 'torso', 'collarBack', 'pauldronF', 'skirt', 'coatFlap', 'pouchB', 'pouchA', 'weapon', 'foreF', 'fistF', 'handL', 'wFore', 'armU', 'armL', 'pauldron', 'handR', 'head', 'collar', 'wHand']
wt = ap(np.linalg.inv(np.vstack([MW, [0, 0, 1]]))[:2], (0, 0))
# 집게 두 날 끝(창 그림 좌표): 위 끝 줄에서 왼쪽·오른쪽 덩어리 가운데
wa2 = np.asarray(Image.open(os.path.join(HERE, 'parts_work/weapon.png')))[..., 3] > 128; ys2, xs2 = np.nonzero(wa2); ytop = ys2.min()
row = np.nonzero(wa2[ytop + 6])[0]; mid = (row.min() + row.max()) / 2
tips = [[round(float(row[row < mid].mean()), 1), float(ytop + 4)], [round(float(row[row > mid].mean()), 1), float(ytop + 4)]]
parts['weapon']['tips'] = tips
rig = {'name': 'nicole-neon', 'version': 1,   # version 은 아래에서 조각 그림 내용 해시로 덮어씀(캐시 방지)
       'units': 'rig px (reference x2)', 'refOrigin': [round(ROOT[0] / 2, 1), round(ROOT[1] / 2, 1)], 'refScale': 2.0, 'refLift': 0,
       'parts': parts, 'bones': out_bones, 'legs': legs, 'draw': draw, 'drawWave': drawWave,
       'hidden': ['handL', 'handR', 'wSleeve', 'wFore', 'wHand'], 'faces': {}, 'waveImg': waveImg,
       'hemRun': T('hemRun', {'lift': 22, 'knee': 1.2, 'heel': .9, 'reach': .4}),
       'hemLimit': T('hemLimit', {'up': .32, 'x': .45}),
       'flap': {'part': 'coatFlap', 'off': FOFF, **T('flap', {'openX': 46, 'openY': 18, 'knee': .012, 'kneeUp': .008, 'lunge': .009})},
       'releaseOpen': True, 'dropLift': T('dropLift', 16), 'hemRest': True, 'idleStance': T('idleStance', {'near': 40, 'far': -80}),
       'follow': [{'bone': 'pauldronF', 'src': 'armF', 'k': .35}],
       'rearBlend': T('rearBlend', .1),   # 뒷손 팔꿈치 뒤→팔 뻗음 바뀔 때 0.1초 동안 미끄러짐
       'bounce': T('bounce', [{'bone': 'pouchA', 'stiff': 210, 'damp': 8, 'y': .6, 'rot': .005, 'max': 12}, {'bone': 'pouchB', 'stiff': 240, 'damp': 9, 'y': .5, 'rot': -.004, 'max': 10}]),   # 파우치 출렁임 (DHL 14:09 추천 3)
       'runForeBend': T('runForeBend', -0.45), 'wristRange': T('wristRange', .55), 'runTilt': T('runTilt', 0),
       'metrics': {'bodyHeight': round(GROUND - 226), 'heightWithWeapon': round(GROUND - 3), 'note': 'rig units. bodyHeight = 머리카락 위 ~ 발바닥(대기), 무기 제외',
                   'shaftWidth': 34, 'fistWidth': 70, 'forearmThickness': 50},
       'ui': {'attack': 'thrust', 'touch': 'wave', 'stillReady': {'t': .22, 'cut': .36}},   # 도감·시작 선택·컷인 = 8 러스트 니콜과 같은 방식 (자기 찌르기로)
       'note': '18 네온 니콜. 8 러스트 니콜(rust-fork-girl v15)과 같은 뼈대·동작. 다른 점: 칼라(collar)·먼 어깨갑(pauldronF, 먼 팔을 35% 따라 돎)·코트 꼬리(cape, 허리 뼈)·파우치 2개(코트 위 고정)·그린 깜빡임'}
# 표정·깜빡임 패치: 머리 뼈에 같은 pivot·배율로 겹침 (faces_raw.json = faces.py 결과)
FR = json.load(open(os.path.join(HERE, 'faces_raw.json'))); hp = parts['head']['pivot']; hs = parts['head']['scale']
for fn, o in FR['parts'].items():
    shutil.copy(os.path.join(HERE, 'parts_work', fn + '.png'), os.path.join(PARTS, fn + '.png'))
    parts[fn] = {'src': f'parts/{fn}.png', 'pivot': [round(hp[0] - o['x0'], 1), round(hp[1] - o['y0'], 1)], 'scale': hs}
rig['faces'] = FR['faces']; rig['blinkFaces'] = {'half': 'blink_half', 'closed': 'blink_closed'}
rig['faceInfo'] = {'closedEyes': ['happy', 'grimace'], 'note': '표정 시트 10칸에서 얼굴(피부+먼 눈)만 오려 기준 머리에 ECC 정렬. 머리카락·윤곽은 항상 기준 머리'}
for k in []:
    if os.path.exists(os.path.join(HERE, 'faces.json')):
        fj = json.load(open(os.path.join(HERE, 'faces.json')))
        if k in fj: rig[k] = fj[k]
if os.path.exists(os.path.join(HERE, 'faces.json')):
    for n, p in json.load(open(os.path.join(HERE, 'faces.json')))['parts'].items(): parts[n] = p
AB = json.load(open(os.path.join(HERE, 'actions_base.json')))
th = dict(AB['thrust']); th['slide'] = T('thrustSlide', [[0, 0, 'io'], [.18, 90, 's'], [.30, 130, 'o'], [.42, 130, 'io'], [.62, 60, 'io'], [.79, 0]])
for k, v in T('thrustOverride', {}).items(): th[k] = v
if T('thrustFull', None): th = T('thrustFull', None)   # 동작 시트(motion1)에 맞춘 찌르기 (tools/fit.py)
rig['actions'] = {'thrust': th}
import hashlib as _hl   # 조각 그림이 바뀌면 version 이 바뀜 → 게임이 ?v= 로 새 그림을 받음 (같은 version 이면 브라우저·exe 캐시의 옛 손 그림 + 새 쥔 점이 섞여 손이 어긋남, 2026-10-17)
_h = _hl.sha1()
for _f in sorted(os.listdir(PARTS)): _h.update(_f.encode()); _h.update(open(os.path.join(PARTS, _f), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(PK, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(PK, 'rig.def.js'), 'w').write("window.MR_RIG_DEFS=window.MR_RIG_DEFS||{};window.MR_RIG_DEFS['nicole-neon']=" + json.dumps(rig, ensure_ascii=False, separators=(',', ':')) + ";\n")
print('ok', len(parts), 'parts; EF', EF.round(1), 'WF', WF.round(1), 'L1,L2', round(L1, 1), round(L2, 1), 'd', round(d, 1))
