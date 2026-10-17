"""21 스카이아크 알론소 리그 조립 (2026-10-17 밤 시작, 1 러스트 알론소 v4 구조 기준).
입력: pieces/ (조각 시트 A, 이름 붙인 것) + work/ (손질한 그림) + ref512.png(원화 = 게임 char_0021)
출력: ../rig.json, ../rig.def.js, ../parts/*.png
실행: cd source && python3 -I build_sky.py
좌표: 원화 512px 좌표로 적고(P), ref1024(=리그 단위, F=1)로 바꿔 씀.
"""
import json, math, os, shutil, hashlib
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); PC = os.path.join(HERE, 'pieces'); W = os.path.join(HERE, 'work'); OUT = os.path.join(HERE, '..')
os.makedirs(os.path.join(OUT, 'parts'), exist_ok=True)
P2 = lambda x, y: np.array([2.0 * x, 2.0 * y])          # 원화 512 → ref1024 (리그 단위)
O = P2(360, 477)                                         # 뿌리: 두 발 가운데 땅 (가까운 발바닥 높이)
def sim2(p1, p2, r1, r2):                                # 조각 두 점 → 기준 두 점 (닮음)
    p1, p2, r1, r2 = map(lambda v: np.array(v, float), (p1, p2, r1, r2)); vp = p2 - p1; vr = r2 - r1
    s = np.linalg.norm(vr) / np.linalg.norm(vp); phi = math.atan2(vr[1], vr[0]) - math.atan2(vp[1], vp[0])
    c, sn = math.cos(phi) * s, math.sin(phi) * s; M = np.array([[c, -sn, 0], [sn, c, 0]]); M[:, 2] = r1 - M[:, :2] @ p1; return M
def srt(s, deg, piv, at):                                # 배율(ref1024)·회전·조각 점 → 기준 점
    a = math.radians(deg); c, sn = math.cos(a) * s, math.sin(a) * s; M = np.array([[c, -sn, 0], [sn, c, 0]]); M[:, 2] = np.array(at, float) - M[:, :2] @ np.array(piv, float); return M
info = lambda M: (math.hypot(M[0, 0], M[1, 0]), math.atan2(M[1, 0], M[0, 0]))
inv = lambda M, r: np.linalg.solve(M[:, :2], np.array(r, float) - M[:, 2])
app = lambda M, p: M[:, :2] @ np.array(p, float) + M[:, 2]
unit = lambda v: np.array(v, float) / np.linalg.norm(v)
img = lambda p: Image.open(p).convert('RGBA')

# ---------------- 손질한 그림 만들기 ----------------
# 칼: 원화처럼 손잡이를 길게 (DHL 22:45 '원화대로 긴 손잡이') — 손잡이 감은 무늬 한 주기(y 440~461)를 6번 더 이어 붙임
sw = np.array(img(os.path.join(PC, 'sword.png'))); SEG = sw[440:461]; REP = 6
long_sw = np.vstack([sw[:461]] + [SEG] * REP + [sw[461:]]); Image.fromarray(long_sw).save(os.path.join(W, 'sword_long.png')); Image.fromarray(long_sw).save(os.path.join(W, 'sword_full.png'))
EXT = 21 * REP
SW_TIP = (78, 2); SW_GUARD = (78, 375); SW_POM = (76, 600 + EXT); SW_GRIP = (77, 495 + EXT)   # 쥔 점 = 늘린 손잡이 아래쪽(폼멜 고리 위)
# 앞자락: 원화의 짧은 앞자락에 맞춰 세로 0.72배
sf = img(os.path.join(PC, 'skirtF.png')); sf.resize((sf.width, int(sf.height * 0.72)), Image.LANCZOS).save(os.path.join(W, 'skirtF_sq.png'))
# 가까운(자유) 팔: 팔뚝+주먹 한 장(foreFhang)을 팔뚝·주먹으로 나눔 (원화 주먹이 커서 주먹만 더 크게)
fh = np.array(img(os.path.join(PC, 'foreFhang.png'))); yy, xx = np.mgrid[0:fh.shape[0], 0:fh.shape[1]]
ax0, ax1 = np.array([30., 22.]), np.array([68., 128.]); u = unit(ax1 - ax0); t = (xx - ax0[0]) * u[0] + (yy - ax0[1]) * u[1]
cutT = np.dot(np.array([68., 118.]) - ax0, u)
a = fh.copy(); a[..., 3] = np.where(t < cutT + 4, a[..., 3], 0); Image.fromarray(a).save(os.path.join(W, 'nearFore.png'))
b = fh.copy(); b[..., 3] = np.where(t >= cutT - 2, b[..., 3], 0); Image.fromarray(b).save(os.path.join(W, 'nearFist.png'))
# 메는(먼) 팔: carry_nohilt(손잡이 토막 지운 것)을 팔뚝·주먹으로 나눔 (x 182 기준)
cn = np.array(img(os.path.join(W, 'carry_nohilt.png')))
a = cn.copy(); a[:, 186:, 3] = 0; Image.fromarray(a).save(os.path.join(W, 'carryFore.png'))
b = cn.copy(); b[:, :176, 3] = 0; Image.fromarray(b).save(os.path.join(W, 'carryFist.png'))

# 메는 손 (DHL 23:38 "원화·시트와 다르게 나왔어요"): 시트 메는 손은 쥔 각도·토시 모양이 원화와 달라 → 원화에서 주먹·손잡이 끝·폼멜·토시를 그대로 오려 씀
#  (서 있기·달리기 동안 메는 손은 칼과 함께 거의 고정이라 원화 한 장이 가장 정확. 공격 때는 쥔 손 조각으로 바꿈)
from PIL import ImageDraw
_ref = img(os.path.join(HERE, 'ref512.png')); _m = Image.new('L', _ref.size, 0)
ImageDraw.Draw(_m).polygon([(423, 236), (446, 233), (463, 239), (477, 251), (491, 257), (505, 260), (512, 283), (501, 303), (486, 297), (474, 287), (459, 285), (457, 300), (449, 312), (435, 318), (420, 315), (413, 301), (417, 285), (423, 270)], fill=255)
_c = _ref.copy(); _c.putalpha(Image.fromarray(np.minimum(np.array(_ref)[..., 3], np.array(_m)))); _c.crop((405, 225, 512, 325)).save(os.path.join(W, 'carryArt.png'))
# 칼: 폼멜은 원화 조각(carryArt)이 그림 → 칼 그림은 손잡이 끝(폼멜 고리 위)에서 자름
_sl = np.array(img(os.path.join(W, 'sword_long.png'))); _sl[515 + EXT:, :, 3] = 0; Image.fromarray(_sl).save(os.path.join(W, 'sword_long.png'))
# 칼을 칼날(+날밑 고리, y<429)과 손잡이 감은 부분(y 423~)으로 나눔 — 공격 때 칼날이 손 쪽으로 미끄러져 긴 손잡이가 짧아짐(엔진 hiltSlide). 서 있을 땐 둘이 겹쳐 원래 그림 그대로
_bl = _sl.copy(); _bl[429:, :, 3] = 0; Image.fromarray(_bl).save(os.path.join(W, 'sword_blade.png'))
_hw = _sl.copy(); _hw[:423, :, 3] = 0; Image.fromarray(_hw).save(os.path.join(W, 'sword_wrap.png'))
# ---------------- 원화 관절 (512 → ref1024) ----------------
HIP = P2(362, 360); NECK = P2(375, 246)
SH_N, EL_N, WR_N = P2(294, 262), P2(273, 306), P2(268, 345)       # 가까운(자유) 팔: 어깨(어깨갑 안)·팔꿈치·손목
GRIP = P2(442, 262)                                                # 메는 손 쥔 점
SW_T, SW_P = P2(9, 46), P2(496, 281)                               # 원화 칼끝·폼멜
UAX = unit(SW_P - SW_T)                                            # 칼끝 → 폼멜
WR_F = P2(440, 292); EL_F = P2(432, 352); SH_F = P2(418, 290)     # 메는 팔: 손목(토시 끝)·팔꿈치(코트 뒤)·어깨

parts = {}
parts['torso'] = dict(file=os.path.join(PC, 'torso.png'), M=srt(1.45, 2, (112, 131), P2(393, 330)), at=HIP)
parts['skirt'] = dict(file=os.path.join(W, 'skirtF_sq.png'), M=srt(1.45, 0, (126, 25), P2(393, 333)), at=P2(362, 332))
parts['skirtB'] = dict(file=os.path.join(PC, 'skirtB.png'), M=srt(1.45, 0, (100, 25), P2(362, 335)), at=P2(360, 332))
HM = np.array(json.load(open(os.path.join(W, 'match.json')))['head']['M'])
parts['head'] = dict(file=os.path.join(PC, 'head.png'), M=HM, at=NECK)
parts['braid'] = dict(file=os.path.join(PC, 'braid.png'), M=sim2((62, 12), (28, 190), P2(288, 200), P2(260, 250)), at=P2(288, 200))
parts['pauldron'] = dict(file=os.path.join(PC, 'pauldronA.png'), M=srt(0.95, 6, (80, 60), P2(298, 262)), at=SH_N)
# 가까운 팔
parts['armU'] = dict(file=os.path.join(PC, 'armNdown.png'), M=sim2((50, 22), (50, 155), SH_N, EL_N), at=SH_N)
parts['armL'] = dict(file=os.path.join(W, 'nearFore.png'), M=sim2((30, 22), (68, 128), EL_N, WR_N), at=EL_N)
_, rotL = info(parts['armL']['M'])
parts['fistN'] = dict(file=os.path.join(W, 'nearFist.png'), M=srt(1.24, math.degrees(rotL), (68, 128), WR_N), at=WR_N)
# 메는 팔 (몸 뒤) + 주먹은 얼굴 앞(overlay 대신 따로 뼈)
parts['armF'] = dict(file=os.path.join(PC, 'armFdown.png'), M=sim2((48, 20), (48, 145), SH_F, EL_F), at=SH_F)
parts['foreF'] = dict(file=os.path.join(W, 'carryFore.png'), M=sim2((35, 60), (180, 70), EL_F, WR_F), at=EL_F)
# 주먹: 손잡이 축(조각 57°)을 원화 칼 축에 맞춤
ax_piece = math.degrees(math.atan2(130, 85)); ax_ref = math.degrees(math.atan2(UAX[1], UAX[0]))
parts['fistF'] = dict(file=os.path.join(W, 'carryArt.png'), M=srt(2.0, 0, (0, 0), P2(405, 225)), at=GRIP)   # 원화 오림 (512 → 리그 ×2)
# 칼: 칼끝·폼멜 → 원화 칼끝·폼멜
parts['weapon'] = dict(file=os.path.join(W, 'sword_blade.png'), M=sim2(SW_TIP, SW_POM, SW_T, SW_P), at=GRIP)
parts['hiltW'] = dict(file=os.path.join(W, 'sword_wrap.png'), M=sim2(SW_TIP, SW_POM, SW_T, SW_P), at=GRIP)

bones = [('root', None), ('hip', 'root'), ('skirtB', 'hip'), ('torso', 'hip'), ('skirt', 'hip'), ('head', 'torso'), ('braid', 'head'),
         ('armF', 'torso'), ('foreF', 'armF'), ('fistF', 'foreF'), ('weapon', 'fistF'), ('hiltW', 'weapon'),
         ('armU', 'torso'), ('armL', 'armU'), ('fistN', 'armL'), ('pauldron', 'torso'),
         ('cape', 'torso'), ('scarf', 'torso'), ('pouch', 'torso'), ('pauldronF', 'torso')]   # 그림 없는 뼈: 엔진이 이름으로 찾음(러스트 알론소 구조)
world = {'root': (O.copy(), 0.0), 'hip': (np.array(HIP, float), 0.0)}
R = lambda p: [round(float(p[0] - O[0]), 1), round(float(p[1] - O[1]), 1)]
def_parts = {}; out_bones = []
for name, parent in bones:
    if name in parts:
        p = parts[name]; s, phi = info(p['M']); piv = inv(p['M'], p['at']); world[name] = (np.array(p['at'], float), phi)
        fn = name + '.png'; shutil.copy(p['file'], os.path.join(OUT, 'parts', fn))
        d = {'src': 'parts/' + fn, 'pivot': [round(float(piv[0]), 1), round(float(piv[1]), 1)], 'scale': round(s, 4)}
        if 'mesh' in p: d['mesh'] = p['mesh']
        def_parts[name] = d
    if parent is None: out_bones.append({'name': 'root', 'parent': None, 'pos': [0, 0]}); continue
    if world.get(name) is None and name not in parts: world[name] = world[parent]
    (pw, pa), (cw, ca) = world[parent], world[name]
    dv = cw - pw; c, sn = math.cos(-pa), math.sin(-pa); loc = [c * dv[0] - sn * dv[1], sn * dv[0] + c * dv[1]]
    bb = {'name': name, 'parent': parent, 'pos': [round(loc[0], 1), round(loc[1], 1)]}
    if abs(ca - pa) > 1e-4: bb['rot'] = round(ca - pa, 4)
    if name in parts: bb['part'] = name
    out_bones.append(bb)
# 칼 조각 정보 (세로 그림, 칼끝 위)
def_parts['weapon'].update({'tip': list(SW_TIP), 'tips': [[72, 8], [84, 8]], 'guard': list(SW_GUARD), 'pommel': list(SW_POM)})
# 팔 조각 관절 점
def_parts['armU']['elbow'] = [50, 155]; def_parts['armL']['fist'] = [80, 160]; def_parts['armF']['elbow'] = [48, 145]
# ---------------- 표정 (머리 그림 크기 캔버스, 앞머리를 위에 다시 그림 — work/face_*.png) ----------------
FN = ['effort', 'shout', 'focus', 'happy', 'surprised', 'grimace']
for n in FN + ['half', 'closed', 'neutral']:
    shutil.copy(os.path.join(W, f'face_{n}.png'), os.path.join(OUT, 'parts', f'face_{n}.png'))
    def_parts[f'face_{n}'] = {'src': f'parts/face_{n}.png', 'pivot': def_parts['head']['pivot'], 'scale': def_parts['head']['scale']}
# ---------------- 다리 (IK) ----------------
# 원화: 가까운 엉덩이(335,365)·무릎(318,400)·발목(292,441) / 먼 엉덩이(385,365)·무릎(418,406)·발목(420,438)
TH, SHN = 2 * 44.0, 2 * 46.0
LEG_S = 0.9
for n in ['thighN', 'shinN', 'thighF', 'shinF', 'boot', 'knee']: shutil.copy(os.path.join(PC, n + '.png'), os.path.join(OUT, 'parts', n + '.png'))
def_parts['thighN'] = {'src': 'parts/thighN.png', 'pivot': [60, 25], 'scale': 1}; def_parts['thighF'] = {'src': 'parts/thighF.png', 'pivot': [60, 25], 'scale': 1}
def_parts['shinN'] = {'src': 'parts/shinN.png', 'pivot': [50, 22], 'scale': 1}; def_parts['shinF'] = {'src': 'parts/shinF.png', 'pivot': [50, 22], 'scale': 1}
BOOT_S = 0.78
def_parts['boot'] = {'src': 'parts/boot.png', 'pivot': [52, 22], 'scale': BOOT_S}
def_parts['knee'] = {'src': 'parts/knee.png', 'pivot': [57, 50], 'scale': 0.8}
legs = {'hip': [0, 2 * 5.0], 'thigh': TH, 'shin': SHN,
        'thighImg': {'part': 'thighN', 'a': [60, 25], 'b': [60, 185], 'w': 1.85},
        'shinImg': {'part': 'shinN', 'a': [50, 22], 'b': [55, 195], 'w': 1.75},
        'thighFirst': True, 'kneeImg': {'part': 'knee', 'mix': 0.5, 'dx': 6, 'dy': 0, 'rot': 0}, 'boot': {'part': 'boot', 'sole': [[-40, 82], [-35, 86], [120, 86], [130, 76]], 'ankleRange': [-0.45, 0.75]},
        'near': {'x': -110.0, 'hipX': -34.0, 'runX': -10, 'shade': 0, 'thighImg': {'part': 'thighN', 'a': [60, 25], 'b': [60, 185], 'w': 1.85}, 'shinImg': {'part': 'shinN', 'a': [50, 22], 'b': [55, 195], 'w': 1.75}},
        'far': {'x': 100.0, 'hipX': 30.0, 'runX': 10, 'shade': 0.25, 'thighImg': {'part': 'thighF', 'a': [60, 25], 'b': [60, 185], 'w': 1.85}, 'shinImg': {'part': 'shinF', 'a': [50, 22], 'b': [55, 195], 'w': 1.75}}}
# 걸음 (23:19 DHL '삐그덕'): 다리 뿌리를 발 자리의 1/4 안쪽(hipX −34/+30), 서 있는 발은 다리 길이 안(x −110/+100, 원화 −136/+120은 다리 180으로 안 닿아 발이 뜸)으로 — 원화 간격(±50)이면 먼 발이 엉덩이 뒤에 착지·땅에 1프레임만 닿아 절뚝임.
#  다리(180)가 짧아 보폭·무릎 들기·뒤꿈치 차기를 줄임(무릎 튐 27°→15°/프레임, 굽힘 ≤138°)
# 그리는 순서 (뒤 → 앞): 망토 꼬리 · 메는 팔(몸 뒤) · 뒷자락 · 다리 · 몸통 · 앞자락 · 칼(머리 뒤로 지나감) · 땋은 머리 · 머리 · 가까운 팔 · 어깨갑 · 메는 주먹(얼굴 앞)
draw = ['tailB', 'tailA', 'skirtB', 'legFar', 'legNear', 'torso', 'skirt', 'hiltW', 'weapon', 'braid', 'head', 'armU', 'armL', 'fistN', 'pauldron', 'fistF']
rig = {'name': 'alonso-sky', 'version': 1, 'units': 'rig px (원화 512 ×2)', 'refOrigin': [float(O[0]), float(O[1])], 'refScale': 1.0, 'refLift': 0,
       'parts': def_parts, 'bones': out_bones, 'legs': legs, 'draw': draw, 'hidden': [], 'faces': {n: f'face_{n}' for n in FN},
       'blinkFaces': {'half': 'face_half', 'closed': 'face_closed'},
       'metrics': {'bodyHeight': 2 * (477 - 88), 'note': 'rig units; 머리카락 중간(y88)~발바닥(477) ×2, 무기 제외'},
       'armPhase': 0.5, 'gait': {'heelKick': 0.3, 'kneeLift': 0.5, 'strideBase': 45, 'strideK': 0.12, 'swingReach': -0.05, 'swingAng': 0.15, 'landAng': 0}, 'carrySwing': 0.25, 'wristRange': 0.2,
       'ui': {'attack': 'smash', 'touch': 'hop'},
       'gameRef': {'refOrigin': [273.7, float(O[1] / 2)], 'refScale': 2.0, 'refLift': 0, 'note': '게임 그림 char_0021.png(512) 발 높이 = 원화. x 273.7 = 도감 칸(fitArt 중심 275.7)에서 골반(hip x 4)이 가운데 (2026-10-18 02:20 DHL "도감 위치 가운데")'},
       'note': '21 스카이아크 알론소 (2026-10-17 밤, v1 대기 조립). 칼 = 원화 자리(칼날 머리 뒤·손잡이 얼굴 앞), 메는 팔은 몸 뒤·주먹만 얼굴 앞.'}
# ---------------- 망토 꼬리 2개 (streamers) ----------------
for n, src in [('tailA', 'capeA'), ('tailB', 'capeB')]:
    im = img(os.path.join(PC, src + '.png')); im.save(os.path.join(OUT, 'parts', n + '.png'))
    al = np.array(im)[..., 3] > 40; xs = np.where(al.any(0))[0]; x1 = int(xs.max()); ys = np.where(al[:, x1 - 25:x1 + 1].any(1))[0]
    rig['parts'][n] = {'src': f'parts/{n}.png', 'pivot': [float(x1 - 8), float((ys.min() + ys.max()) / 2)], 'scale': 1.5, 'mesh': {'cols': 8, 'rows': 2}}
    rig['_len_' + n] = round(float(x1 - xs.min()) * 1.5, 1)
tw = world['torso']; tl = lambda p: (lambda dv: [round(math.cos(-tw[1]) * dv[0] - math.sin(-tw[1]) * dv[1], 1), round(math.sin(-tw[1]) * dv[0] + math.cos(-tw[1]) * dv[1], 1)])(np.array(p) - tw[0])
rig['bones'].append({'name': 'tailA', 'parent': 'torso', 'pos': tl(P2(312, 262)), 'rot': -0.05, 'part': 'tailA'})
rig['bones'].append({'name': 'tailB', 'parent': 'torso', 'pos': tl(P2(312, 290)), 'rot': -0.45, 'part': 'tailB'})
rig['streamers'] = [{'bone': 'tailA', 'part': 'tailA', 'len': rig.pop('_len_tailA'), 'amp': 10, 'freq': 7.2, 'phase': 0, 'droop': 0.25, 'sag': 18, 'wind': 0.7, 'lag': 0.35},
                    {'bone': 'tailB', 'part': 'tailB', 'len': rig.pop('_len_tailB'), 'amp': 13, 'freq': 6.4, 'phase': 1.9, 'droop': 0.35, 'sag': 24, 'wind': 0.65, 'lag': 0.45}]
rig['hemOpenSides'] = True   # 치마 폭 바깥의 다리는 밑단 높이에서 잘리지 않게(런지·뒤로 뻗은 다리) — 알론소 v4와 같은 옵션
exec(open(os.path.join(HERE, 'attack_sky.py'), encoding='utf-8').read())   # 내려찍기 (쥔 팔 조각 합성 + 키)
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(os.path.join(OUT, 'parts'))): _h.update(fn.encode()); _h.update(open(os.path.join(OUT, 'parts', fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json (source/build_sky.py)\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['alonso-sky']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(def_parts), 'parts, version', rig['version'])
