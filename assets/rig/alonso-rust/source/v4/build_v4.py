"""알론소 v4 리그 조립 (2026-10-17, 오른쪽 3/4 새 시트).
입력: work/ (조각 + match_result.json, 기준 = 통합 시트 키 포즈 1 대기를 2배로 키운 work/ref1024.png)
출력: OUT/rig.json + OUT/parts/*.png
실행: cd v4 && python3 -I build_v4.py OUTDIR
좌표: 기준(ref2) 픽셀 → 리그 단위 = (ref2 - O) * F.  F는 몸 높이(머리카락 중간~발바닥)를 753 리그 단위로 맞춘 값.
"""
import json, math, os, shutil, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'work')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..'); os.makedirs(os.path.join(OUT, 'parts'), exist_ok=True)
match = json.load(open(os.path.join(W, 'match_result.json')))
O = np.array([395., 748.])          # 뿌리: 두 발 가운데 땅
F = 753 / 658                        # 리그 단위 / ref2 px (머리카락 중간 y≈90 ~ 발바닥 y≈748)

def sim2(p1, p2, r1, r2):            # 두 점 대응 → 닮음변환 (조각 px → ref2 px)
    p1, p2, r1, r2 = map(np.array, (p1, p2, r1, r2)); vp = p2 - p1; vr = r2 - r1
    s = np.linalg.norm(vr) / np.linalg.norm(vp); phi = math.atan2(vr[1], vr[0]) - math.atan2(vp[1], vp[0])
    c, sn = math.cos(phi) * s, math.sin(phi) * s; M = np.array([[c, -sn, 0], [sn, c, 0]]); M[:, 2] = r1 - M[:, :2] @ p1; return M
def srt(s, deg, piv_piece, at_ref):  # 배율·회전·위치 (조각 점 piv → 기준 점 at)
    a = math.radians(deg); c, sn = math.cos(a) * s, math.sin(a) * s; M = np.array([[c, -sn, 0], [sn, c, 0]]); M[:, 2] = np.array(at_ref) - M[:, :2] @ np.array(piv_piece); return M
fromMatch = lambda n: np.array(match[n]['M'])
info = lambda M: (math.hypot(M[0, 0], M[1, 0]), math.atan2(M[1, 0], M[0, 0]))
inv = lambda M, r: np.linalg.solve(M[:, :2], np.array(r, float) - M[:, 2])
app = lambda M, p: M[:, :2] @ np.array(p, float) + M[:, 2]
unit = lambda v: np.array(v, float) / np.linalg.norm(v)

# ---------------- 기준(ref2) 관절 ----------------
HIP = (395, 520); NECK = (412, 326)
SH_N = (322, 362)                    # 가까운 어깨 (칼 메는 팔, 어깨갑 안)
SH_F = (466, 388)                    # 먼 어깨 (자유 팔, 몸 뒤)
TIP = np.array([8., 16.]); UAX = unit((455, 384))          # 칼끝 → 폼멜 방향 (키 포즈 대기, 약 40.2°)
SW_S = 595 / 413                     # 칼 조각(칼끝 425 ↔ 폼멜 12) → 키 포즈 길이
GRIP_T = 511                         # 칼끝에서 쥔 점까지 (ref2 px)
GRIP = TIP + UAX * GRIP_T
parts = {}
parts['torso'] = dict(file='a07.png', M=fromMatch('torso'), at=HIP)
Ms = fromMatch('skirt') @ np.array([[1, 0, -5.5], [0, 1, 0], [0, 0, 1]])  # 치마를 가로 1.1배 넓힌 그림(a08w, 110→121px): 가운데를 맞춰 양옆으로 5.5px씩 넓어짐 → 상체 밑단 술 아래를 덮음
parts['skirt'] = dict(file='a08w.png', M=Ms, at=(400, 478), mesh={'cols': 8, 'rows': 6})
parts['pouch'] = dict(file='a09.png', M=fromMatch('pouch'), at=(470, 470))
parts['head'] = dict(file='head3q.png', M=srt(1.0, 0, (150, 250), NECK), at=NECK)
parts['pauldronF'] = dict(file='a10.png', M=fromMatch('pauldronN'), at=SH_N)
# 칼: 조각 축 y=51, 칼끝 x=425, 폼멜 x=12 → 키 포즈 칼끝·폼멜
POM = TIP + UAX * (413 * SW_S)
parts['weapon'] = dict(file='a12.png', M=sim2((425, 51), (12, 51), TIP, POM), at=GRIP)
# 메는 손(가까운 팔 팔뚝+주먹 한 장, fix f19): 손잡이 축(잘린 끝→폼멜) (65,18)→(190,80), 쥔 점 (130,50), 팔꿈치 (35,180)
ax_piece = math.degrees(math.atan2(62, 125)); ax_ref = math.degrees(math.atan2(UAX[1], UAX[0]))
CARRY_S = 0.74
Mc = srt(CARRY_S, ax_ref - ax_piece, (130, 50), GRIP)
EL_N = app(Mc, (35, 180))
parts['foreF'] = dict(file='f19c.png', M=Mc, at=EL_N)
# 가까운 윗팔(a13): 어깨 (40,14) → 팔꿈치 (58,100)
parts['armF'] = dict(file='a13.png', M=sim2((40, 14), (58, 100), SH_N, EL_N), at=SH_N)
# 먼 팔: 윗팔(a14) 어깨 (38,15) → 팔꿈치 (55,108), 배율 .96 / 팔뚝+주먹(a15) 팔꿈치 (22,12) → 주먹 중심 (70,95)
ARM_S = 0.96
import subprocess
AX = lambda *a: json.loads(subprocess.check_output([sys.executable, '-I', os.path.join(HERE, 'axis_piece.py'), *map(str, a)]))
FU = AX('work/farUp.png', 75, 45, 190, 222, 0.6, 'work/farUpA.png'); FH = AX('work/farHang.png', 85, 80, 195, 390, 0.46, 'work/farHangA.png'); FS = AX('pieces/farB/q04.png', 50, 235, 330, 95, 0.46, 'work/farSwingA.png')
Lup = np.linalg.norm(np.subtract((55, 108), (38, 15))) * ARM_S
EL_F = np.array(SH_F) + unit((497 - 466, 468 - 388)) * Lup
parts['armU'] = dict(file='farUpA.png', M=sim2(FU['joint'], FU['end'], SH_F, EL_F), at=SH_F)   # 먼 팔 전용 시트(왼팔) 윗팔
Lfo = np.linalg.norm(np.subtract((70, 95), (22, 12))) * ARM_S
FIST_F = EL_F + unit(np.subtract((514, 562), EL_F)) * Lfo
parts['armL'] = dict(file='farHangA.png', M=sim2(FH['joint'], FH['end'], EL_F, FIST_F), at=EL_F)   # 먼 팔 늘어뜨린 주먹 (손가락이 앞을 봄)
parts['pauldron'] = dict(file='a11.png', M=srt(1.0, 8, (40, 30), (SH_F[0] - 4, SH_F[1] - 18)), at=SH_F)
# 목도리: 위 고리(scarfTop) / 꼬리(cape, 메시) — a06 를 y=58 에서 나눔
sc = Image.open(os.path.join(W, 'a06.png')).convert('RGBA'); sw, sh_ = sc.size; CUT = 58
sc.crop((0, 0, sw, CUT + 6)).save(os.path.join(W, 'scarf_top.png')); sc.crop((0, CUT - 4, sw, sh_)).save(os.path.join(W, 'scarf_tail.png'))
parts['scarf'] = dict(file='scarf_top.png', M=srt(0.95, -6, (57, 30), (425, 352)), at=(425, 352))
parts['cape'] = dict(file='scarf_tail.png', M=srt(0.9, 68, (57, 4), (378, 346)), at=(378, 346), mesh={'cols': 6, 'rows': 7})

bones = [('root', None), ('hip', 'root'), ('torso', 'hip'), ('skirt', 'hip'), ('pouch', 'torso'), ('cape', 'torso'), ('scarf', 'torso'), ('head', 'torso'),
         ('armU', 'torso'), ('armL', 'armU'), ('pauldron', 'torso'),
         ('armF', 'torso'), ('foreF', 'armF'), ('fistF', 'foreF'), ('weapon', 'foreF'), ('pauldronF', 'torso')]
world = {'root': (O.copy(), 0.0), 'hip': (np.array(HIP, float), 0.0), 'fistF': (np.array(GRIP), 0.0)}
R = lambda p: [round(float((p[0] - O[0]) * F), 1), round(float((p[1] - O[1]) * F), 1)]
def_parts = {}; out_bones = []
for name, parent in bones:
    if name in parts:
        p = parts[name]; s, phi = info(p['M']); piv = inv(p['M'], p['at']); world[name] = (np.array(p['at'], float), phi)
        fn = name + '.png'; shutil.copy(os.path.join(W, p['file']), os.path.join(OUT, 'parts', fn))
        d = {'src': 'parts/' + fn, 'pivot': [round(float(piv[0]), 1), round(float(piv[1]), 1)], 'scale': round(s * F, 4)}
        if 'mesh' in p: d['mesh'] = p['mesh']
        def_parts[name] = d
    if parent is None: out_bones.append({'name': 'root', 'parent': None, 'pos': [0, 0]}); continue
    (pw, pa), (cw, ca) = world[parent], world[name]
    dv = (cw - pw) * F; c, sn = math.cos(-pa), math.sin(-pa); loc = [c * dv[0] - sn * dv[1], sn * dv[0] + c * dv[1]]
    b = {'name': name, 'parent': parent, 'pos': [round(loc[0], 1), round(loc[1], 1)]}
    if abs(ca - pa) > 1e-4: b['rot'] = round(ca - pa, 4)
    if name in parts: b['part'] = name
    out_bones.append(b)
# ---------------- 칼: 그림을 세로(칼끝 위)로 돌려 저장 → 무기 뼈 각도 = 칼끝 방향 + 90° (창과 같은 규칙) ----------------
sw = Image.open(os.path.join(W, 'a12.png')).convert('RGBA'); SWW = sw.width
sw.rotate(90, expand=True).save(os.path.join(OUT, 'parts', 'weapon.png'))
rot = lambda p: [p[1], SWW - 1 - p[0]]                      # (x,y) → 세로 그림 좌표
gx_piece = 425 - GRIP_T / SW_S                              # 칼끝에서 쥔 점까지 (조각 px)
def_parts['weapon'] = {'src': 'parts/weapon.png', 'pivot': rot((gx_piece, 51)), 'scale': round(SW_S * F, 4), 'tip': rot((425, 51)),
                       'tips': [rot((412, 44)), rot((412, 58))], 'guard': rot((116, 51)), 'pommel': rot((12, 51))}
# 메기 자세: 무기 뼈는 foreF 자식 — 세계 각도 = 칼끝 방향(-UAX) + 90°
for bb in out_bones:
    if bb['name'] == 'weapon':
        aw = math.atan2(-UAX[1], -UAX[0]) + math.pi / 2; pa = world['foreF'][1]; bb['rot'] = round(aw - pa, 4)   # 12:50: 칼 각도는 메는 손 그림의 손잡이 방향 그대로(돌리면 손 그림 속 손잡이와 칼 손잡이가 2개로 보임 — DHL 12:44)
# ---------------- 쥔 손 조각 (strip_grips.py 결과) ----------------
GJ = json.load(open(os.path.join(W, 'grips.json')))
cp = def_parts['foreF']; carryFore = math.hypot(cp['pivot'][0] - 130, cp['pivot'][1] - 50) * cp['scale']   # 메는 손 팔뚝 길이(리그 단위)
for n, g in GJ.items():
    shutil.copy(os.path.join(W, n + '_s.png'), os.path.join(OUT, 'parts', n + '.png'))
    k = carryFore / g['forearm']
    def_parts[n] = {'src': f'parts/{n}.png', 'pivot': g['elbow'], 'elbow': g['elbow'], 'grip': g['grip'], 'wrist': g['grip'], 'shaftDir': g['shaftDir'], 'scale': round(k, 4)}
# 윗팔 조각에 어깨(pivot)·팔꿈치 점
def_parts['armF']['elbow'] = [58, 100]; def_parts['armU']['elbow'] = FU['end']
def_parts['armL']['fist'] = FH['end']
# 달릴 때: 앞으로 흔든 주먹(손등이 보임) — 같은 '팔꿈치→주먹 아래로 곧게' 규칙으로 정리한 그림, 길이를 늘어뜨린 팔과 같게
shutil.copy(os.path.join(W, 'farSwingA.png'), os.path.join(OUT, 'parts', 'armLF.png'))
kS = def_parts['armL']['scale'] * (FH['end'][1] - FH['joint'][1]) / (FS['end'][1] - FS['joint'][1])
def_parts['armLF'] = {'src': 'parts/armLF.png', 'pivot': FS['joint'], 'scale': round(kS, 4), 'fist': FS['end']}
def_parts['armL']['alt'] = 'armLF'
def_parts['foreF'].update({'grip': [130, 50], 'wrist': [130, 50], 'shaftDir': [-0.896, -0.444], 'elbow': [35, 180]})
print('carryFore', round(carryFore, 1), {n: def_parts[n]['scale'] for n in GJ})
# ---------------- 위로 든 윗팔 (조각 시트 2 r11·r12) — 내려찍기 준비(머리 위) 때 바꿔 끼움 ----------------
R2 = os.path.join(os.path.dirname(W), 'pieces', 'rig2')
for n, f in [('armFup', 'r11.png'), ('armUup', 'r12.png')]: shutil.copy(os.path.join(R2, f), os.path.join(OUT, 'parts', n + '.png'))
def_parts['armFup'] = {'src': 'parts/armFup.png', 'pivot': [78, 190], 'elbow': [60, 42], 'scale': 0.5}   # 어깨(아래 초록 소매 끝) → 팔꿈치(위 피부 끝)
def_parts['armUup'] = {'src': 'parts/armUup.png', 'pivot': [56, 190], 'elbow': [74, 42], 'scale': 0.5}
shutil.copy(os.path.join(R2, 'r13.png'), os.path.join(OUT, 'parts', 'torsoTurn.png'))
# 화면 쪽으로 튼 상체(r13): 벨트 버클(140,150)·목 위(125,8) 기준으로 기존 상체(버클 102,92 · 목 85,8)와 같은 크기(0.59배), 골반 점 = 버클에서 같은 거리
def_parts['torsoTurn'] = {'src': 'parts/torsoTurn.png', 'pivot': [94, 209], 'scale': round(def_parts['torso']['scale'] * 0.59, 4), 'hides': ['pouch']}   # r13에 주머니가 그려져 있음 → 주머니 조각 숨김
# ---------------- 쥔 팔 시트 3 (12:59): 머리 위(up)·내려찍기(dn) 쥔 팔뚝 — grip3.py 결과, 칼에 그대로 붙임(rigid) ----------------
G3 = json.load(open(os.path.join(W, 'grips3.json')))
for n, g in G3.items():
    shutil.copy(os.path.join(W, n + '_s.png'), os.path.join(OUT, 'parts', n + '.png'))
    def_parts[n] = {'src': f'parts/{n}.png', 'pivot': g['elbow'], 'elbow': g['elbow'], 'grip': g['grip'], 'wrist': g['grip'], 'shaftDir': g['shaftDir'], 'scale': g['scale']}
# DHL 14:40: 먼 손(gFdn)은 엄지가 손잡이 아래 → '다른 손'처럼 보임. 칼 축(손잡이 중심선)으로 뒤집어 엄지를 위로, 손가락 끝은 아래로 감싸게(18 앞 주먹과 같은 처리)
#   뒤집은 그림 gFdnT: 쥔 점·칼 축은 그대로라 칼에 붙는 자리 변화 없음. 팔꿈치도 같이 뒤집힘(팔뚝이 축 반대쪽으로) → 정식 조각 받기 전까지 임시
def mirror_grip(src, dst):
    g = G3[src]; im = Image.open(os.path.join(W, src + '_s.png')).convert('RGBA'); gp = np.array(g['grip']); u = np.array(g['shaftDir']) / np.linalg.norm(g['shaftDir'])
    M = 2 * np.outer(u, u) - np.eye(2); refl = lambda q: gp + M @ (np.array(q, float) - gp)
    cs = np.array([refl(c) for c in [(0, 0), (im.width, 0), (0, im.height), (im.width, im.height)]]); off = np.floor(cs.min(0)) - 4; size = (np.ceil(cs.max(0)) - off + 4).astype(int)
    t = gp - M @ gp; A = (M[0, 0], M[0, 1], M[0, 0] * off[0] + M[0, 1] * off[1] + t[0], M[1, 0], M[1, 1], M[1, 0] * off[0] + M[1, 1] * off[1] + t[1])
    im.transform(tuple(size), Image.AFFINE, A, resample=Image.BICUBIC).save(os.path.join(OUT, 'parts', dst + '.png'))
    R = lambda q: [round(float(v), 1) for v in (refl(q) - off)]
    el = R(g['elbow']); def_parts[dst] = {'src': f'parts/{dst}.png', 'pivot': el, 'elbow': el, 'grip': R(g['grip']), 'wrist': R(g['grip']), 'shaftDir': g['shaftDir'], 'scale': g['scale'], 'fist': R(g['fist'])}
    return R, off
R_FT, _ = mirror_grip('gFdn', 'gFdnT')
# DHL 16:59: 휘두를 때 먼 주먹 정식 조각(k03 — 엄지 손잡이 위·칼날 쪽, 손가락 끝 4개 아래 한 줄, 손등 패치·털 소매). 뒤집은 임시 gFdnT 대신
#   축 = 손잡이 양 끝 토막 단면 가운데 (300,549)→(1380,886.5), 칼날 쪽 = 오른쪽 아래. 쥔 점 = 손가락 4개 가운데를 축에 내린 점(793,703)
#   크기 0.125 = 손가락 간격(128px)을 gFdn(16 리그 단위)과 같게. 주먹 밖 손잡이 토막은 지움(칼 그림의 손잡이가 보이게). 팔꿈치는 털 소매 쪽으로 136
def swing_fist():
    im = np.asarray(Image.open(os.path.join(HERE, 'pieces', 'grip4', 'k03_swing_fist.png')).convert('RGBA')).copy()
    g0 = np.array([300.0, 549.0]); u = np.array([1080.0, 337.5]); u /= np.linalg.norm(u); nrm = np.array([-u[1], u[0]])
    yy, xx = np.mgrid[0:im.shape[0], 0:im.shape[1]]; t = (xx - g0[0]) * u[0] + (yy - g0[1]) * u[1]; nv = (xx - g0[0]) * nrm[0] + (yy - g0[1]) * nrm[1]
    cut = (np.abs(nv) < 84) & ((t < 250) | (t > 800))
    im[..., 3] = np.where(cut, 0, im[..., 3]).astype(np.uint8)
    Image.fromarray(im.astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'parts', 'gFsw.png'))
    grip = np.array([793.0, 703.0]); d = np.array([400.0, 220.0]) - grip; d /= np.linalg.norm(d); el = grip + d * 136 / 0.125
    def_parts['gFsw'] = {'src': 'parts/gFsw.png', 'pivot': [round(float(el[0]), 1), round(float(el[1]), 1)], 'elbow': [round(float(el[0]), 1), round(float(el[1]), 1)],
                         'grip': [793.0, 703.0], 'wrist': [793.0, 703.0], 'shaftDir': [round(float(u[0]), 4), round(float(u[1]), 4)], 'scale': 0.125}
swing_fist()
# DHL 15:56: 먼 손 세로 손잡이 쥔 팔(엄지 위, 칼날 12시, 팔뚝 5시) — 칼을 다시 메러 얼굴 앞으로 올릴 때(0.75~0.79) 몸 앞에 보이는 먼 팔
#   쥔 점 = 손잡이 축(x 433.5) 위 손가락 4개 가운데(y 500), 팔꿈치 = 둥근 피부 끝 중심, 크기 = 손가락 간격을 gFdn과 같게(0.22)
shutil.copy(os.path.join(HERE, 'pieces', 'grip4', 'k02_vertical.png'), os.path.join(OUT, 'parts', 'gFrise.png'))
def_parts['gFrise'] = {'src': 'parts/gFrise.png', 'pivot': [925.0, 991.0], 'elbow': [925.0, 991.0], 'grip': [433.5, 500.0], 'wrist': [433.5, 500.0], 'shaftDir': [0.0, -1.0], 'scale': 0.22}
_fr = np.array([R_FT(c) for c in [(195, 298), (420, 298), (195, 503), (420, 503)]]); FIST_DN_T = [388, int(_fr[:, 1].min()), int(_fr[:, 0].max()) - 387, int(np.ptp(_fr[:, 1])) + 1]   # 왼쪽 끝은 털 소매 빼고 장갑부터(그림 보고 정함)
# ---------------- 다리 (IK) ----------------
for n, f in [('thigh', 'thigh.png'), ('shin', 'f20.png'), ('boot', 'a30f.png'), ('bootB', 'a30.png')]: shutil.copy(os.path.join(W, f), os.path.join(OUT, 'parts', n + '.png'))
TH, SHN = 64 * F, 72 * F
def_parts['thigh'] = {'src': 'parts/thigh.png', 'pivot': [150, 45], 'scale': 1}
def_parts['shin'] = {'src': 'parts/shin.png', 'pivot': [120, 60], 'scale': 1}
BOOT_S = 0.95 * F
def_parts['boot'] = {'src': 'parts/boot.png', 'pivot': [30, 34], 'scale': round(BOOT_S, 4)}
def_parts['bootB'] = {'src': 'parts/bootB.png', 'pivot': [30, 34], 'scale': round(BOOT_S, 4)}
legs = {'hip': [0, round(25 * F, 1)], 'thigh': round(TH, 1), 'shin': round(SHN, 1),
        'thighImg': {'part': 'thigh', 'a': [152, 42], 'b': [72, 196], 'w': 1.0},
        'shinImg': {'part': 'shin', 'a': [118, 58], 'b': [86, 158], 'w': 0.95},
        'thighFirst': True, 'boot': {'part': 'boot', 'back': 'bootB', 'sole': [[-28, 68], [-25, 74], [65, 74], [73, 62]], 'ankleRange': [-0.45, 0.75]},
        'near': {'x': round(-60 * F, 1), 'hipX': round(-15 * F, 1), 'runX': -10, 'shade': 0}, 'far': {'x': round(50 * F, 1), 'hipX': round(12.5 * F, 1), 'runX': 10, 'shade': 0.3}}   # DHL 12:26 B안 확정: 엉덩이 관절은 튜닉 안쪽(발 자리의 1/4), 달릴 때 발은 몸 가운데 줄(runX)
draw = ['cape', 'pauldron', 'armU', 'armL', 'legFar', 'legNear', 'torso', 'skirt', 'pouch', 'scarf', 'head', 'armF', 'pauldronF', 'weapon', 'foreF']   # DHL 13:59: 칼과 칼 든 손은 맨 앞
rig = {'name': 'alonso-rust', 'version': 4, 'units': 'rig px (reference x2)', 'refOrigin': [float(O[0]), float(O[1])], 'refScale': F, 'refLift': 0,
       'parts': def_parts, 'bones': out_bones, 'legs': legs, 'draw': draw, 'hidden': [], 'faces': {},
       'metrics': {'bodyHeight': 753, 'note': 'rig units; 머리카락 중간~발바닥, 무기 제외'},
       'armPhase': 0.5, 'hemOpenSides': True, 'seamInterior': True, 'hemLimit': {'up': 0.2, 'x': 0.14}, 'hemRun': {'lift': 4, 'knee': 0.28, 'heel': 0.24, 'reach': 0, 'kneeX': 0.3}, 'gait': {'heelKick': 0.85, 'kneeLift': 0.9, 'swingReach': -0.05, 'swingAng': 0.15, 'landAng': 0}, 'carrySwing': 0.35, 'wristRange': 0.2, 'ui': {'attack': 'smash', 'touch': 'hop'},
       'note': '1번 알론소 v4 (2026-10-17, 오른쪽 3/4 새 시트). 가까운 팔(armF→foreF=메는 손 한 장)이 칼을 어깨에 멤, 먼 팔(armU→armL 팔뚝+주먹 한 장)이 자유롭게 흔듦. 내려찍기는 손 시트 받은 뒤.'}
# ---------------- 표정 (align_faces_v4.py: 기준 머리와 같은 크기·좌표의 얼굴 패치) ----------------
FN = ['happy', 'effort', 'shout', 'angry', 'focus', 'sad', 'grimace', 'relaxed', 'surprised']
for n in FN + ['blink_half', 'blink_closed']:
    shutil.copy(os.path.join(W, f'face_{n}.png'), os.path.join(OUT, 'parts', f'face_{n}.png'))
    def_parts[f'face_{n}'] = {'src': f'parts/face_{n}.png', 'pivot': def_parts['head']['pivot'], 'scale': def_parts['head']['scale']}
rig['faces'] = {n: f'face_{n}' for n in FN}
rig['faceInfo'] = {'closedEyes': ['happy', 'grimace'], 'note': '표정 머리 12장을 기준 3/4 머리에 ECC 정렬, 얼굴 타원만 오림(머리카락·머리띠·외곽선은 기준 머리)'}
rig['blinkFaces'] = {'half': 'face_blink_half', 'closed': 'face_blink_closed'}
rig['swordGrip'] = {'maxWrist': 0.35, 'tipDepth': 6,
    'near': {'upper': 'armF', 'carry': 'foreF', 'pieces': ['gN49', 'gN90'], 'sPref': 25, 'sSig': 20, 'sMin': 0, 'sMax': 55, 'shMin': -3.15, 'shMax': 3.15, 'pieceCost': 0.05, 'bendMin': -2.65},
    'far': {'upper': 'armU', 'pieces': ['gF34', 'gF46'], 'sPref': -40, 'sSig': 25, 'sMin': -95, 'sMax': 0, 'shMin': -3.15, 'shMax': 3.15, 'pieceCost': 0.05}}
rig['drawSword'] = ['cape', 'pauldron', 'legFar', 'legNear', 'torso', 'skirt', 'pouch', 'scarf', 'head', 'armF', 'pauldronF', 'weapon', 'farFistDn', 'foreF']   # DHL 14:19: 휘두름·타격 때 먼 팔은 안 그리고(꺾여 보임) 칼을 쥔 먼 주먹만 칼 위에
rig['headFront'] = {'clip': [[60, 267], [55, 182], [72, 152], [108, 118], [148, 62], [172, 0], [343, 0], [343, 267]]}   # 머리 그림 px: 얼굴·귀·앞머리(오른쪽) — 칼 손잡이는 이 뒤로, 칼날은 뒷머리(왼쪽 뾰족 머리) 위로
rig['ui'] = {'attack': 'smash', 'touch': 'hop'}
rig['drawSwordUp'] = ['cape', 'pauldron', 'legFar', 'legNear', 'torso', 'skirt', 'pouch', 'scarf', 'head', 'armU', 'armL', 'armF', 'pauldronF', 'weapon', 'farFist', 'foreF']   # DHL 19:57 ①: 들어 올리는 중(0.1~0.3) 두 팔 모두 얼굴보다 앞, 칼·쥔 손 맨 앞
rig['drawSwordGrab'] = ['cape', 'pauldron', 'legFar', 'legNear', 'torso', 'skirt', 'pouch', 'scarf', 'head', 'armF', 'pauldronF', 'weapon', 'farFist', 'foreF']   # DHL 19:57 ②③: 공격 시작(0~0.1) 먼 손은 바로 손잡이를 쥐고 팔 없이 주먹만
rig['drawSwordUp2'] = ['cape', 'pauldron', 'legFar', 'legNear', 'torso', 'skirt', 'pouch', 'scarf', 'head', 'armF', 'pauldronF', 'weapon', 'farFist', 'foreF']   # DHL 19:57 ④: 머리 위(0.3~0.41) 앞쪽(먼) 팔은 주먹만
rig['headFront_face'] = {'clip': [[95, 267], [88, 170], [105, 135], [150, 118], [240, 108], [300, 112], [318, 170], [300, 267]]}   # 머리 그림 px: 얼굴(이마~턱)만
rig['overlays'] = {'farFist': {'bone': 'armL', 'rect': [140, 0, 340, 290]}, 'farFistDn': {'bone': 'armL', 'rect': [0, 0, 1536, 1024]}, 'farFistRise': {'bone': 'armL', 'rect': [300, 330, 340, 322]}}   # gFup·gFdn 그림의 주먹 부분   # gFup 그림의 주먹 부분(머리 위 준비 때만 씀)
rig['drawSwordRel'] = ['cape', 'pauldron', 'armU', 'armL', 'legFar', 'legNear', 'torso', 'skirt', 'pouch', 'scarf', 'head', 'armF', 'pauldronF', 'weapon', 'foreF']   # 먼 손 놓은 뒤: 먼 팔 몸 뒤, 칼과 가까운 손 맨 앞
rig['drawSwordRise'] = ['cape', 'pauldron', 'legFar', 'legNear', 'torso', 'skirt', 'pouch', 'scarf', 'head', 'armF', 'pauldronF', 'weapon', 'farFistRise', 'foreF']   # DHL 19:57 ⑥: 다시 멜 때(0.75~0.79) 먼 팔은 주먹만
# 내려찍기 v5 1차 (12:58): 키 기반(rigid) — 쥔 팔뚝 그림은 칼에 고정, 그림은 구간마다 고정(튀지 않음). 준비 = 동작 시트 m12(주먹 머리 위), 타격 = m13
rig['actions'] = {'smash': {'kind': 'sword', 'rigid': True, 'ankleRange': [-0.45, 1.1], 'dur': 0.9, 'hitAt': 0.46, 'hitStop': 0.07, 'cancelAt': 0.62,
    'reach': [[0, 0, 'io'], [0.04, 1], [0.79, 1, 'io'], [0.9, 0]],   # DHL 19:57 ③: 먼 손이 시작하자마자 손잡이를 쥠   # 14:40: 얼굴 앞(0.75~0.79)까지 쥐고 있다가 놓음   # DHL 14:20: 칼이 얼굴 근처까지 올라올 때까지 두 손으로 들고, 그 뒤 먼 손을 놓음   # DHL 14:07: 들어 올릴 때 먼 손이 이미 손잡이를 쥠   # reachPiece: 먼 손은 처음부터 쥔 팔뚝 그림으로 주먹 자리→손잡이(튐 없음), 타격 뒤 손잡이→제자리로 내림
    'reachPiece': True,
    'w': [[0, 0, 'io'], [0.3, 1], [0.62, 1, 'io'], [0.85, 0]],
    'gx': [[0, -5], [0.3, 10, 'i'], [0.38, 10, 'i'], [0.42, 60, 'o'], [0.46, 110], [1, 110]],   # 머리 위 칼을 머리 가운데로 → 먼 팔뚝이 얼굴 오른쪽으로 내려옴(DHL 14:07 스케치)
    'gy': [[0, -405], [0.3, -385, 'io'], [0.38, -393, 'i'], [0.42, -300, 'o'], [0.46, -40, 'o'], [0.5, -52, 'io'], [0.57, -40], [1, -40]],   # 15:10 타격 뒤 칼이 땅에서 살짝 튀었다 가라앉음(무게)
    'sa': [[0, -2.71], [0.3, -2.95, 'io'], [0.38, -3.06, 'i'], [0.42, -1.4, 'o'], [0.46, 0.44, 'o'], [0.5, 0.37, 'io'], [0.57, 0.44], [1, 0.44]],   # 15:10 머리 위에서 한 번 더 젖혔다(준비) 휘두름
    'sN': [[0, 0, 'io'], [0.16, 40], [0.41, 40], [0.42, 38], [0.68, 38], [0.69, 25], [0.77, 25], [0.78, 0]],
    'sF': [[0, -55], [0.41, -55], [0.42, -30]],   # 머리 위: 먼 손은 폼멜 쪽 끝
    'nPiece': [[0, 'foreF'], [0.12, 'gNup'], [0.41, 'gNdn'], [0.68, 'gN49'], [0.78, 'foreF']],   # 복귀: 팔꿈치가 어깨 아래·윗팔 길이에 오는 그림만(13:44 gNup은 팔꿈치가 얼굴 위로 올라가 바꿈)   # 메는 손↔머리 위 손은 팔꿈치 차이 19뿐 → 들어 올릴 때 머리 위 손을 거쳐 메기로(큰 바뀜은 휘두름·들어 올림 시작 순간에만)
    'fPiece': [[0, 'gFup'], [0.41, 'gFsw'], [0.75, 'gFrise'], [0.79, 'gFdn']],   # 14:40 엄지 위로 뒤집은 그림   # gFup은 손잡이 토막을 양쪽 다 지운 그림 → 칼에서 먼 흔들던 주먹 자리에서도 토막이 안 보임
    'nUpper': [[0, 'armF'], [0.14, 'armFup'], [0.41, 'armF']],
    'fUpper': [[0, 'armU'], [0.14, 'armUup'], [0.41, 'armU']],
    'order': [[0, 'drawSwordGrab'], [0.1, 'drawSwordUp'], [0.3, 'drawSwordUp2'], [0.41, 'drawSword'], [0.75, 'drawSwordRise'], [0.79, 'drawSwordRel']],   # 14:40: 얼굴 앞에서만 먼 팔뚝이 몸 앞에 보임 → 놓을 때는 몸 뒤로(놓는 그림 바꿈이 몸에 가려짐)
    'tPiece': [[0, 'torso'], [0.13, 'torsoTurn'], [0.41, 'torso']],
    'hipX': [[0, 0, 'io'], [0.32, -14, 's'], [0.46, 40], [0.6, 40, 'io'], [0.85, 0]],
    'hipY': [[0, 0, 'io'], [0.3, 24, 's'], [0.38, 30, 's'], [0.46, 55, 'o'], [0.5, 61, 'io'], [0.6, 51, 'io'], [0.85, 0]],   # 15:10 타격 때 몸이 한 번 더 눌림
    'lean': [[0, 0, 'io'], [0.32, -0.08, 's'], [0.46, 0.5], [0.6, 0.46, 'io'], [0.85, 0]],
    'head': [[0, 0, 'io'], [0.32, 0.08, 's'], [0.46, -0.2], [0.6, -0.18, 'io'], [0.85, 0]],
    'breath': [[0, 0, 'io'], [0.3, 1, 'o'], [0.46, -0.5, 'io'], [0.8, 0]],
    'farDx': [[0, 0, 'io'], [0.38, 0, 's'], [0.46, 100], [0.65, 100, 'io'], [0.85, 0]],
    'farLift': [[0, 0], [0.36, 0, 'io'], [0.41, 22, 'io'], [0.46, 0], [0.65, 0, 'io'], [0.75, 14, 'io'], [0.85, 0]],
    'nearDx': [[0, 0, 'io'], [0.38, 0, 'io'], [0.47, -60], [0.65, -60, 'io'], [0.85, 0]],   # 다리 길이 안에서 뒷다리를 곧게 뻗음(시트 m13은 다리를 2배 길게 그림 → 방향만 따름)
    'shake': [[0, 0], [0.46, 0, 'lin'], [0.47, 1], [0.56, 0]],
    'face': [[0, 'effort'], [0.3, 'shout'], [0.56, 'focus'], [0.76, None]]}}
# ---------------- 목도리 긴 꼬리 2개 (시트 2 r15·r16, 15:25) — 동작 시트처럼 늘 뒤로 날림. 짧게 늘어진 예전 꼬리(cape)는 안 그림 ----------------
#   r15: 왼쪽 끝이 찢긴 끝(자유 끝), 오른쪽 뾰족한 끝이 매듭 쪽 → 그대로. r16: 오른쪽 끝이 아래로 처진 자유 끝 → 좌우 뒤집어 왼쪽으로 날리게
#   크기: 매듭(r14) 폭 192px ↔ 지금 목도리 고리 폭 124 → 0.65배인데, 동작 시트 꼬리(목→끝 약 300·폭 넓음)에 맞춰 0.95배
for n, src, flip in [('tailA', 'r15', False), ('tailB', 'r16', True)]:
    im = Image.open(os.path.join(HERE, 'pieces', 'rig2', src + '.png')).convert('RGBA')
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    im.save(os.path.join(OUT, 'parts', n + '.png'))
    al = np.array(im)[..., 3] > 40; xs = np.where(al.any(0))[0]; x1 = int(xs.max()); ys = np.where(al[:, x1 - 25:x1 + 1].any(1))[0]
    rig['parts'][n] = {'src': f'parts/{n}.png', 'pivot': [float(x1 - 8), float((ys.min() + ys.max()) / 2)], 'scale': 0.95, 'mesh': {'cols': 8, 'rows': 2}}
    rig['_tailLen_' + n] = round(float(x1 - xs.min()) * 0.95, 1)
rig['bones'].append({'name': 'tailA', 'parent': 'torso', 'pos': [-14.0, -204.0], 'rot': -0.12, 'part': 'tailA'})
rig['bones'].append({'name': 'tailB', 'parent': 'torso', 'pos': [-8.0, -192.0], 'rot': -0.32, 'part': 'tailB'})
rig['streamers'] = [{'bone': 'tailA', 'part': 'tailA', 'len': rig.pop('_tailLen_tailA'), 'amp': 11, 'freq': 7.5, 'phase': 0, 'droop': 0.3, 'sag': 20, 'wind': 0.7, 'lag': 0.35},
                    {'bone': 'tailB', 'part': 'tailB', 'len': rig.pop('_tailLen_tailB'), 'amp': 15, 'freq': 6.6, 'phase': 1.9, 'droop': 0.4, 'sag': 26, 'wind': 0.65, 'lag': 0.45}]
for k in [k for k in rig if k == 'draw' or k.startswith('drawSword')]:
    L = rig[k]; i = L.index('cape'); rig[k] = L[:i] + ['tailB', 'tailA'] + L[i + 1:]
# 게임 연결 (2026-10-17 DHL "러스트 니콜 기준으로 게임에 반영" + 20:36 기준): 도감·시작 선택 = 대기 → 클릭 → 전투와 같은 내려찍기 → 대기,
#  스킬 컷인 = 내려찍은 자세(cutHold .58초) 유지. version = 그림 해시 (게임이 그림 주소에 ?v= 로 붙여 캐시를 깸)
rig['ui'] = {'attack': 'smash', 'touch': 'hop'}
rig['cutHold'] = 0.58
rig['gameRef'] = {'refOrigin': [292.0, 477.5], 'refScale': 2.0, 'refLift': 0, 'note': '게임 그림(characters/char_0001.png 512px) 위 발 자리·배율. x 292 = 도감 칸에서 몸이 가운데(2026-10-17 21:06 DHL). refOrigin·refScale은 v4 시트(ref2) 기준이라 편집기용'}
import hashlib
_h = hashlib.md5(json.dumps({k: v for k, v in rig.items() if k != 'version'}, sort_keys=True).encode())
for fn in sorted(os.listdir(os.path.join(OUT, 'parts'))): _h.update(fn.encode()); _h.update(open(os.path.join(OUT, 'parts', fn), 'rb').read())
rig['version'] = _h.hexdigest()[:8]
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(OUT, 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['alonso-rust']=" + json.dumps(rig, ensure_ascii=False) + ";\n")
print('ok', len(def_parts), 'parts; GRIP', GRIP.round(1), 'EL_N', EL_N.round(1), 'EL_F', EL_F.round(1), 'FIST_F', FIST_F.round(1))
