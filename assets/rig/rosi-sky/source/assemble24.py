# 24 스카이 로시 v1 rig.json: 4 러스트 로시 v1.1 rig.json 을 바탕으로 뼈 자리(새 원화 J)·조각(build24·faces24)·다리·탄띠 사슬·총구만 바꿈 (10-21 11:30, 14 assemble14 에서)
#  python3 -I assemble24.py → ../rig.json · ../rig.def.js
import json, os, copy
import numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); W = os.path.join(H, 'work'); PD = os.path.join(R, 'parts')
base = json.load(open(os.path.join(R, '..', 'rosi-rust', 'rig.json')))
B = json.load(open(os.path.join(W, 'build24_parts.json'))); F = json.load(open(os.path.join(W, 'faces24.json')))
J = {k: tuple(v) for k, v in B['J'].items()}; O = J['root']
d = copy.deepcopy(base)
d['name'] = 'rosi-sky'; d['title'] = '24 스카이 로시 (4 러스트 로시 v1.1 리그 구조)'; d['version'] = '1.0'
d['refOrigin'] = list(O); d['refScale'] = 2.0; d['refLift'] = 0
d['metrics'] = {'bodyHeight': 738, 'note': 'head top (cap y91) to sole (y460 ground), idle, gun excluded; scale = screen px / bodyHeight'}
# ---------- 뼈: 부모 기준 위치 = (J[자식] − J[부모]) × 2 ----------
for b in d['bones']:
    n = b['name']
    if b['parent'] is None: b['pos'] = [0, 0]; continue
    p = b['parent']; b['pos'] = [round((J[n][0] - J[p][0]) * 2, 1), round((J[n][1] - J[p][1]) * 2, 1)]
# 조각 (안 쓰는 러스트 조각 = 베일·뒷면·칼라·장갑·팔뚝 따로 — 네온은 팔뚝·장갑이 총 묶음 안)
DROP = ['cape', 'capeFill', 'collar', 'gloveN', 'gloveF', 'cuffN', 'foreOrigF', 'foreN', 'foreF', 'gripBackN', 'handBackN', 'neck', 'skirt', 'torso', 'torsoFill', 'gun', 'head', 'pack', 'sleeveN', 'sleeveF', 'link', 'thigh', 'shin', 'boot']
for k in list(d['parts']):
    if k in DROP or k.startswith('face_') or k.startswith('blink_'): d['parts'].pop(k)
d['parts'].update(B['parts']); d['parts'].update(F['parts'])
USE = {'chest': 'torso', 'torsoFill': 'torsoFill', 'skirt': 'skirt', 'neckP': 'neck', 'head': 'head', 'pack': 'pack', 'shoulderN': 'sleeveN', 'shoulderF': 'sleeveF', 'gun': 'gun'}
for b in d['bones']:
    b.pop('part', None)
    if b['name'] in USE: b['part'] = USE[b['name']]
d['jointMap'] = {k: list(J[k]) for k in ['hip', 'torso', 'chest', 'neck', 'head', 'shoulderN', 'elbowN', 'wristN', 'shoulderF', 'elbowF', 'wristF']}
d['draw'] = ['pack', 'belt', 'legFar', 'legNear', 'skirt', 'torsoFill', 'chest', 'gun', 'shoulderF', 'neckP', 'head', 'shoulderN']   # 소매(어깨판 + 크림 소매)는 총 묶음(팔뚝) 위 — 원화처럼 소매 입구가 팔뚝 위(10-21 12:45) · 먼 소매 = 목·머리 뒤(14 DHL 09:09)
d['overlays'] = {}
# 서 있는 발 = 새 원화 부츠 자리(가까운 발목 x ≈ 180 · 먼 288) — 다리가 길어(골반~발목 83px) 14 처럼 뒤꿈치가 들리지 않음
d['idleStance'] = {'near': -48.0, 'far': 40.0}
# 치마 자리 = 허리띠·골반(바지) — 천 흔들림 없음
d['parts']['skirt'].pop('mesh', None)
# ---------- 다리 (시트 14 허벅지 = 부푼 바지 위 · 15 정강이 = 바지 아래 + 주름 단 · 16 부츠) — 시트 배율이 머리와 달라 원화 다리 크기에 맞춤 ----------
#  원화(512): 다리 뿌리 (210,350)·(268,350) → 무릎 y ≈ 398 → 발목 (180,433)·(288,428) · 바지 폭 ≈ 50 · 부츠 길이 57 · 높이 35~45
def piece(n, crop=None):
    im = Image.open(os.path.join(H, 'pieces', n + '.png')).convert('RGBA')
    if crop: im = im.crop(crop)
    return im
th = piece('14_thigh', (0, 0, 248, 330)); th.save(os.path.join(PD, 'thigh.png'))      # 아래 주름 단은 뺌(정강이 조각이 단을 그림)
sh = piece('15_shin'); sh.save(os.path.join(PD, 'shin.png'))
bt = piece('16_boot'); bt.save(os.path.join(PD, 'boot.png'))
d['parts']['thigh'] = {'src': 'parts/thigh.png', 'pivot': [124, 40], 'scale': 1}
d['parts']['shin'] = {'src': 'parts/shin.png', 'pivot': [100, 150], 'scale': 1}
d['parts']['boot'] = {'src': 'parts/boot.png', 'pivot': [118, 88], 'scale': .294}
L = d['legs']; L['hip'] = [0, 12]; L['near']['x'] = -60; L['far']['x'] = 56
L['thigh'] = 96.0; L['shin'] = 92.0; L.pop('thighFirst', None)   # 허벅지(부푼 바지)가 정강이 위를 덮음(무릎 꺾일 때 틈 없음)
L['thighImg'] = {'part': 'thigh', 'a': [124, 40], 'b': [120, 300], 'w': 1.22}
L['shinImg'] = {'part': 'shin', 'a': [100, 150], 'b': [96, 330], 'w': 1.05}   # 무릎 위 150px 은 허벅지 밑으로 들어감
L['boot'] = {'part': 'boot', 'sole': [[-86, 170], [0, 174], [150, 180], [262, 172]], 'toeX': 180.0, 'ankleRange': L['boot']['ankleRange'], 'idleDorsi': L['boot']['idleDorsi']}
# ---------- 탄띠 = 시트 17 탄 한 발 사슬 (러스트 탄띠 _drawChain 그대로: 그림 x = 탄띠 따라, 탄두(−y) = 곡선 안쪽 — 원화도 탄두가 안쪽) ----------
lk = piece('17_hose'); lk.save(os.path.join(PD, 'link.png'))
d['parts']['link'] = {'src': 'parts/link.png', 'pivot': [79, 160], 'scale': .36}   # 탄 길이 289 × .36 = 104 = 원화 탄띠 폭 52px
HOSE512 = [(62, 230), (58, 242), (55, 254), (53, 266), (53, 278), (55, 290), (58, 302), (63, 313), (69, 323), (77, 332), (86, 340), (96, 347), (107, 352), (119, 356), (132, 358), (145, 359), (156, 360), (166, 360), (174, 360)]   # 탄띠 가운데 선(원화 512) = 바깥 외곽선(가운데 (128,270) 에서 방사) − 탄 길이 반 25 — 10-21 11:50 다시 잼
rig = lambda p: [round((p[0] - O[0]) * 2, 1), round((p[1] - O[1]) * 2, 1)]
C = d['carry']; Bt = C['belt']
pk = B['info']['pack']; gn = B['info']['gun']
Bt.update({'links': ['link'], 'spacing': 40, 'path': [rig(p) for p in HOSE512], 'chestRest': rig(J['chest']),
           'from': [HOSE512[0][0] * 4 - pk[0], HOSE512[0][1] * 4 - pk[1]], 'to': [HOSE512[-1][0] * 4 - gn[0], HOSE512[-1][1] * 4 - gn[1]], 'linkScale': [1, 1], 'reverse': False})
# 총구·총열 방향(총 조각 px) — 새 원화 세 총구 가운데 (441,373) · 총열 뒤 (370,367)
C['fire']['muzzle'] = [441 * 4 - gn[0], 373 * 4 - gn[1]]; C['fire']['bore'] = [370 * 4 - gn[0], 367 * 4 - gn[1]]
# rigidFore: 팔꿈치 점(손잡이 기준) = 새 원화 팔꿈치 − 손목
C['rigidFore'] = {'shoulderN': [round((J['elbowN'][0] - J['gripN'][0]) * 2, 1), round((J['elbowN'][1] - J['gripN'][1]) * 2, 1)],
                  'shoulderF': [round((J['elbowF'][0] - J['gripF'][0]) * 2, 1), round((J['elbowF'][1] - J['gripF'][1]) * 2, 1)]}
C['capeAmp'] = 0
# 얼굴
d['faces'] = {'wink': 'face_wink', 'shout': 'face_shout', 'focus': 'face_focus', 'happy': 'face_happy', 'angry': 'face_angry', 'sad': 'face_sad', 'surprised': 'face_surprised', 'grimace': 'face_surprised'}
d['blinkFaces'] = {'half': 'blink_half', 'closed': 'blink_closed'}
d['faceNote'] = '10-21 DHL 조각 시트 머리 9장 → tools/faces24.py: 시트 기본 머리(2번)를 원화 얼굴에 맞추고(ECC .93), 칸마다 2번 머리카락에 맞춤(.97~.98) — 표정 7 = 얼굴 전체, 깜빡임 2 = 눈만'
d['gameNote'] = '24 스카이 로시 v1(10-21): 4 러스트·14 네온 로시 v1.1 과 같은 동작·반응·걸음(rig.json actions·gait·ui 그대로), 조각만 스카이'
for k in ['gaitNote', 'hidden', 'segs']: d.pop(k, None) if k == 'gaitNote' else None
json.dump(d, open(os.path.join(R, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
hdr = "// 자동 생성: rig.json을 JS로 감싼 것 (file:// 에서도 fetch 없이 읽히게). 원본은 같은 폴더의 rig.json — 바꾸면 다시 만들 것\n"
open(os.path.join(R, 'rig.def.js'), 'w').write(hdr + "window.MR_RIG_DEFS=window.MR_RIG_DEFS||{};window.MR_RIG_DEFS['rosi-sky']=" + json.dumps(d, ensure_ascii=False, separators=(',', ':')) + ";\n")
print('bones', {b['name']: b['pos'] for b in d['bones']}); print('belt', Bt['from'], Bt['to'], 'fire', C['fire']['muzzle'], C['fire']['bore'], 'rigidFore', C['rigidFore'])
