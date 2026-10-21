# 14 네온 로시 v1 rig.json: 4 러스트 로시 v1.1 rig.json 을 바탕으로 뼈 자리(새 원화 J)·조각(build14·faces14)·다리·호스 사슬·총구만 바꿈 (10-21 09:00)
#  python3 -I assemble14.py → ../rig.json · ../rig.def.js
import json, os, copy
import numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); W = os.path.join(H, 'work'); PD = os.path.join(R, 'parts')
base = json.load(open(os.path.join(R, '..', 'rosi-rust', 'rig.json')))
B = json.load(open(os.path.join(W, 'build14_parts.json'))); F = json.load(open(os.path.join(W, 'faces14.json')))
J = {k: tuple(v) for k, v in B['J'].items()}; O = J['root']
d = copy.deepcopy(base)
d['name'] = 'rosi-neon'; d['title'] = '14 네온 로시 (4 러스트 로시 v1.1 리그 구조)'; d['version'] = '1.0'
d['refOrigin'] = list(O); d['refScale'] = 2.0; d['refLift'] = 0
d['metrics'] = {'bodyHeight': 722, 'note': 'head top (hair tip y84) to sole (y445), idle, gun excluded; scale = screen px / bodyHeight'}
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
d['draw'] = ['pack', 'belt', 'legFar', 'legNear', 'skirt', 'torsoFill', 'chest', 'shoulderF', 'neckP', 'head', 'shoulderN', 'gun']   # 먼 소매(어깨판) = 목·머리 뒤(DHL 10-21 09:09 '어깨 갑주를 머리 뒤로' — 연사 0.28초 젖힐 때 턱 앞에 그려졌음)
d['overlays'] = {}
# 서 있는 발 = 새 원화 부츠 자리(가까운 발목 x 182 · 먼 290)
d['idleStance'] = {'near': -10.0, 'far': 44.0}   # 가까운 발 = 러스트와 같은 자리(발이 다리 뿌리보다 12px 넘게 뒤면 정강이가 누워 뒤꿈치가 들림 — 10-21 측정), 먼 발 = 새 원화 부츠 자리(발목 x 290)
# 치마 자리 = 허리띠·골반(바지) — 천 흔들림 없음
d['parts']['skirt'].pop('mesh', None)
# ---------- 다리 (시트 14 허벅지 · 15 정강이(무릎판, 발목판 위에서 자름) · 16 부츠) ----------
def piece(n, crop=None):
    im = Image.open(os.path.join(H, 'pieces', n + '.png')).convert('RGBA')
    if crop: im = im.crop(crop)
    return im
th = piece('14_thigh'); th.save(os.path.join(PD, 'thigh.png'))
sh = piece('15_shin'); sh = sh.crop((0, 34, sh.width, 252)); sh.save(os.path.join(PD, 'shin.png'))   # 무릎판 위 검은 덮개·발목판 뺌
bt = piece('16_boot'); bt.save(os.path.join(PD, 'boot.png'))
d['parts']['thigh'] = {'src': 'parts/thigh.png', 'pivot': [104, 110], 'scale': 1}
d['parts']['shin'] = {'src': 'parts/shin.png', 'pivot': [95, 61], 'scale': 1}
d['parts']['boot'] = {'src': 'parts/boot.png', 'pivot': [100, 45], 'scale': .35}
L = d['legs']; L['thigh'] = 48.0; L['shin'] = 62.0; L['thighFirst'] = True
L['thighImg'] = {'part': 'thigh', 'a': [104, 120], 'b': [110, 258], 'w': 1.1}
L['shinImg'] = {'part': 'shin', 'a': [95, 61], 'b': [96, 209], 'w': 1.12}
L['boot'] = {'part': 'boot', 'sole': [[-70, 127], [20, 131], [140, 137], [170, 132]], 'toeX': 120.0, 'ankleRange': L['boot']['ankleRange'], 'idleDorsi': L['boot']['idleDorsi']}
# ---------- 호스 = 시트 17 한 마디 사슬 (러스트 탄띠 _drawChain 그대로) ----------
hz = piece('17_hose', (88, 16, 170, 161)); hz.save(os.path.join(PD, 'link.png'))
d['parts']['link'] = {'src': 'parts/link.png', 'pivot': [41, 72], 'scale': .45}
# 베이지 고리 = 원화 호스 고리(1254 x 100–212 · y 658–720, 호스가 세로로 지나는 곳)를 사슬 방향으로 돌림(그림 x = 호스 따라, −y = 곡선 안쪽)
ra = np.array(Image.open(os.path.join(H, 'sheets/art_v1_0730.png')).convert('RGBA'))[658:720, 100:212]; ring = np.rot90(ra, 1).copy()
Image.fromarray(ring).save(os.path.join(PD, 'ring.png'))
d['parts']['ring'] = {'src': 'parts/ring.png', 'pivot': [31, 56], 'scale': round(1024 / 1254, 4)}
HOSE512 = [(86, 226), (76, 236), (70.2, 245), (63.3, 261.3), (60.4, 279.3), (62.1, 296), (68.6, 311.1), (80, 323.4), (94.7, 329.9), (111, 333.2), (127.4, 335.6), (146, 337), (156, 338)]
rig = lambda p: [round((p[0] - O[0]) * 2, 1), round((p[1] - O[1]) * 2, 1)]
C = d['carry']; Bt = C['belt']
pk = B['info']['pack']; gn = B['info']['gun']
Bt.update({'links': ['ring', 'link', 'link', 'link'], 'spacing': 31, 'path': [rig(p) for p in HOSE512], 'chestRest': rig(J['chest']),
           'from': [HOSE512[0][0] * 4 - pk[0], HOSE512[0][1] * 4 - pk[1]], 'to': [HOSE512[-1][0] * 4 - gn[0], HOSE512[-1][1] * 4 - gn[1]], 'linkScale': [1, 1], 'reverse': False})
# 총구·총열 방향(총 조각 px) — 러스트와 같은 자리(새 원화 총구 494·390)
C['fire']['muzzle'] = [494 * 4 - gn[0], 390 * 4 - gn[1]]; C['fire']['bore'] = [418 * 4 - gn[0], 381 * 4 - gn[1]]
# rigidFore: 팔꿈치 점(손잡이 기준) = 새 원화 팔꿈치 − 손목
C['rigidFore'] = {'shoulderN': [round((J['elbowN'][0] - J['gripN'][0]) * 2, 1), round((J['elbowN'][1] - J['gripN'][1]) * 2, 1)],
                  'shoulderF': [round((J['elbowF'][0] - J['gripF'][0]) * 2, 1), round((J['elbowF'][1] - J['gripF'][1]) * 2, 1)]}
C['capeAmp'] = 0
# 얼굴
d['faces'] = {'wink': 'face_wink', 'shout': 'face_shout', 'focus': 'face_focus', 'happy': 'face_happy', 'angry': 'face_angry', 'sad': 'face_sad', 'surprised': 'face_surprised', 'grimace': 'face_surprised'}
d['blinkFaces'] = {'half': 'blink_half', 'closed': 'blink_closed'}
d['faceNote'] = '10-21 07:59 DHL 조각 시트 머리 9장 → tools/faces14.py: 시트 기본 머리(2번)를 원화 얼굴에 맞추고(ECC .93), 칸마다 2번 머리카락에 맞춤(.97~.98) — 표정 7 = 얼굴 전체, 깜빡임 2 = 눈만'
d['gameNote'] = '14 네온 로시 v1(10-21): 4 러스트 로시 v1.1 과 같은 동작·반응·걸음(rig.json actions·gait·ui 그대로), 조각만 네온'
for k in ['gaitNote', 'hidden', 'segs']: d.pop(k, None) if k == 'gaitNote' else None
json.dump(d, open(os.path.join(R, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
hdr = "// 자동 생성: rig.json을 JS로 감싼 것 (file:// 에서도 fetch 없이 읽히게). 원본은 같은 폴더의 rig.json — 바꾸면 다시 만들 것\n"
open(os.path.join(R, 'rig.def.js'), 'w').write(hdr + "window.MR_RIG_DEFS=window.MR_RIG_DEFS||{};window.MR_RIG_DEFS['rosi-neon']=" + json.dumps(d, ensure_ascii=False, separators=(',', ':')) + ";\n")
print('bones', {b['name']: b['pos'] for b in d['bones']}); print('belt', Bt['from'], Bt['to'], 'fire', C['fire']['muzzle'], C['fire']['bore'], 'rigidFore', C['rigidFore'])
