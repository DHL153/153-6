#!/usr/bin/env python3
"""6 카르덴 '측정 대역 리그'(proxy, 2026-10-17 21:30) — 조각 시트가 오기 전 연구용.
원화(char_0006)에서 잰 관절점(measure/joints_ref.json)으로 8 러스트 니콜과 같은 뼈대를 세우고, 조각 대신 색 막대(캡슐)를 붙인다.
목적: 짧은 다리·넓은 발·긴 봉에서 엔진(달리기·찌르기·뒷손 잡기)이 어떻게 움직이는지 미리 재고, 필요한 opt-in·동작 키를 찾는 것.
게임·편집 툴에는 올리지 않는다(그림이 아님).  실행: python3 -I proxy/build_proxy.py → proxy/pkg/ (rig.json + parts + rig.js 복사)
"""
import json, math, os, shutil
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); RIG = os.path.dirname(os.path.dirname(SRC))
J = json.load(open(os.path.join(SRC, 'measure', 'joints_ref.json')))
OUT = os.environ.get('OUT') or os.path.join(HERE, 'pkg'); PARTS = os.path.join(OUT, 'parts'); os.makedirs(PARTS, exist_ok=True)
S = 2.0                                                    # 리그 단위 = 원화 px × 2 (니콜과 같음)
O = [(J['nearSole'][0] + J['farSole'][0]) / 2, max(J['nearSole'][1], J['farSole'][1])]   # 기준점 = 두 발 가운데 땅
W = lambda k: [(J[k][0] - O[0]) * S, (J[k][1] - O[1]) * S]  # 원화 점 → 리그 단위(root 기준)

def capsule(name, length, width, color, pivot_top=True, extra=None):
    """세로 캡슐(위 끝 = 회전축). 반환: 파트 정의"""
    w, h = int(width + 6), int(length + width + 6)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, w - 3, h - 3), radius=width / 2, fill=color, outline=(30, 20, 15, 255), width=3)
    if extra: extra(d, w, h)
    im.save(os.path.join(PARTS, name + '.png'))
    return {'src': f'parts/{name}.png', 'pivot': [w / 2, 3 + width / 2], 'scale': 1}

def blob(name, w, h, color, pivot, outline=(30, 20, 15, 255)):
    im = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0)); ImageDraw.Draw(im).ellipse((3, 3, w - 3, h - 3), fill=color, outline=outline, width=3)
    im.save(os.path.join(PARTS, name + '.png')); return {'src': f'parts/{name}.png', 'pivot': pivot, 'scale': 1}

d2 = lambda a, b: math.hypot(b[0] - a[0], b[1] - a[1])
ang = lambda a, b: math.atan2(-(b[0] - a[0]), b[1] - a[1])        # 세로(아래) 그림을 a→b 로 돌리는 각

# ---- 월드(리그 단위) 관절
waist, neck = W('waist'), W('neck'); sN, eN, hN = W('nearShoulder'), W('nearElbow'), W('nearHand')
sF, eF, fF = W('farShoulder'), W('farElbow'), W('farFist'); top, bot = W('staffTop'), W('staffBottom')
COL = dict(torso=(110, 120, 70, 255), arm=(95, 105, 60, 255), glove=(55, 45, 40, 255), head=(220, 160, 120, 255), beard=(140, 140, 145, 230),
           leg=(70, 62, 58, 255), boot=(120, 80, 50, 255), staff=(130, 85, 55, 255))
parts = {}
TW = abs(sF[0] - sN[0]) * .8; TL = d2(neck, waist)
im = Image.new('RGBA', (int(TW) + 6, int(TL) + 30), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle((3, 3, TW + 3, TL + 27), radius=40, fill=COL['torso'], outline=(30, 20, 15, 255), width=3)
im.save(os.path.join(PARTS, 'torso.png')); parts['torso'] = {'src': 'parts/torso.png', 'pivot': [TW / 2 + 3, 3], 'scale': 1}
parts['head'] = blob('head', 280, 220, COL['head'], [130, 210])   # 대머리+옆머리 폭 대략 (목 = 아래쪽)
parts['beard'] = blob('beard', 290, 230, COL['beard'], [120, 20])
parts['pauldron'] = blob('pauldron', 110, 90, (120, 70, 45, 255), [55, 40])
LU, LF = d2(sN, eN), d2(eN, hN)
parts['armU'] = capsule('armU', LU, 46, COL['arm'])
parts['armL'] = capsule('armL', LF, 40, COL['glove']); parts['armL']['alt'] = 'armLF'
parts['armLF'] = capsule('armLF', LF, 40, COL['glove']); parts['armLF']['grip'] = [parts['armLF']['pivot'][0], parts['armLF']['pivot'][1] + LF]
parts['armF'] = capsule('armF', d2(sF, eF), 44, COL['arm']); parts['foreF'] = capsule('foreF', d2(eF, fF), 38, COL['arm'])
parts['fistF'] = blob('fistF', 76, 90, COL['glove'], [38, 45])
SL = d2(top, bot)                                            # 봉 길이 (리그 단위)
def staff_draw(dr, w, h):
    for k in range(3): dr.ellipse((w / 2 - 40, 60 + k * 44, w / 2 + 40, 92 + k * 44), fill=(225, 210, 175, 255), outline=(30, 20, 15, 255), width=3)
    dr.rectangle((w / 2 - 30, h - 70, w / 2 + 30, h - 8), outline=(30, 20, 15, 255), width=5)
wim = capsule('weapon', SL, 26, COL['staff'], extra=staff_draw)
grip_from_top = d2(top, fF)                                  # 손 쥔 점: 위 끝에서 아래로
parts['weapon'] = {'src': 'parts/weapon.png', 'pivot': [wim['pivot'][0], wim['pivot'][1] + grip_from_top], 'scale': 1,
                   'tips': [[wim['pivot'][0] - 30, 8], [wim['pivot'][0] + 30, 8]]}
# 찌르기 손 2장 (자루 수평 = shaftDir [1,0]): handL 앞 주먹, handR 뒤 팔뚝+주먹
im = Image.new('RGBA', (90, 120), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); dr.ellipse((8, 8, 82, 82), fill=COL['glove'], outline=(30, 20, 15, 255), width=3)
dr.rounded_rectangle((10, 60, 50, 116), radius=18, fill=COL['arm'], outline=(30, 20, 15, 255), width=3); im.save(os.path.join(PARTS, 'handL.png'))
parts['handL'] = {'src': 'parts/handL.png', 'pivot': [45, 45], 'scale': 1, 'shaftDir': [1, 0], 'wrist': [30, 96], 'toElbow': [-0.6, 0.8]}
im = Image.new('RGBA', (int(LF) + 70, 90), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
dr.rounded_rectangle((4, 25, int(LF) + 20, 70), radius=20, fill=COL['arm'], outline=(30, 20, 15, 255), width=3)
dr.ellipse((int(LF) - 10, 8, int(LF) + 64, 82), fill=COL['glove'], outline=(30, 20, 15, 255), width=3); im.save(os.path.join(PARTS, 'handR.png'))
parts['handR'] = {'src': 'parts/handR.png', 'pivot': [LF + 27, 45], 'scale': 1, 'shaftDir': [1, 0], 'elbow': [8, 48]}
# 다리: 허벅지·정강이 길이 = 두 다리 평균
TH = (d2(W('nearHip'), W('nearKnee')) + d2(W('farHip'), W('farKnee'))) / 2; SH = (d2(W('nearKnee'), W('nearAnkle')) + d2(W('farKnee'), W('farAnkle'))) / 2
parts['thigh'] = capsule('thigh', TH, 62, COL['leg']); parts['shin'] = capsule('shin', SH, 54, COL['leg'])
im = Image.new('RGBA', (130, 60), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle((3, 3, 127, 57), radius=16, fill=COL['boot'], outline=(30, 20, 15, 255), width=3)
im.save(os.path.join(PARTS, 'boot.png')); parts['boot'] = {'src': 'parts/boot.png', 'pivot': [45, 14], 'scale': 1}

# ---- 뼈대 (월드 → 부모 기준 지역 좌표, 그림은 세로 아래가 기본)
bones = []; WR = {}
def bone(name, parent, pos_w, rot_w=0.0, part=None):
    if parent is None: lp, lr = pos_w, rot_w
    else:
        pp, pr = WR[parent]; dx, dy = pos_w[0] - pp[0], pos_w[1] - pp[1]; c, s_ = math.cos(-pr), math.sin(-pr)
        lp, lr = [c * dx - s_ * dy, s_ * dx + c * dy], rot_w - pr
    WR[name] = (pos_w, rot_w); b = {'name': name, 'parent': parent, 'pos': [round(lp[0], 1), round(lp[1], 1)]}
    if abs(lr) > 1e-4: b['rot'] = round(lr, 4)
    if part: b['part'] = part
    bones.append(b)
bone('root', None, [0, 0]); bone('hip', 'root', waist); bone('skirt', 'hip', waist); bone('torso', 'hip', waist, ang(waist, neck) + math.pi, 'torso')
bones[-1]['pos'] = [0.0, 0.0]
# torso 그림: 위 끝(목)이 회전축이 아니라 허리가 축 → 캡슐을 뒤집어 쓰는 대신 torso 파트 축을 아래 끝으로
parts['torso']['pivot'] = [parts['torso']['pivot'][0], TL + 3]
WR['torso'] = (waist, 0.0); bones[-1].pop('rot', None)
bone('cape', 'torso', neck)                                   # 망토 없음(엔진이 뼈를 씀) — 그림 없음
bone('head', 'torso', neck, 0.0, 'head'); bone('beard', 'head', [neck[0] + 60, neck[1] - 20], 0.0, 'beard')
bone('armU', 'torso', sN, ang(sN, eN), 'armU'); bone('armL', 'armU', eN, ang(eN, hN), 'armL'); bone('pauldron', 'torso', sN, 0.0, 'pauldron')
bone('armF', 'torso', sF, ang(sF, eF), 'armF'); bone('foreF', 'armF', eF, ang(eF, fF), 'foreF'); bone('fistF', 'foreF', fF, 0.0, 'fistF')
bone('weapon', 'fistF', fF, 0.0, 'weapon')
for nm in ['handL', 'handR']: bone(nm, 'weapon', fF, -math.pi / 2, nm)
LEGS = {'hip': [0, round(W('nearHip')[1] / 2 + W('farHip')[1] / 2 - waist[1], 1)], 'thigh': round(TH, 1), 'shin': round(SH, 1),
        'thighImg': {'part': 'thigh', 'a': parts['thigh']['pivot'], 'b': [parts['thigh']['pivot'][0], parts['thigh']['pivot'][1] + TH], 'w': 1},
        'shinImg': {'part': 'shin', 'a': parts['shin']['pivot'], 'b': [parts['shin']['pivot'][0], parts['shin']['pivot'][1] + SH], 'w': 1},
        'boot': {'part': 'boot', 'sole': [[-40, 40], [-36, 46], [80, 46], [84, 40]], 'ankleRange': [-0.45, 0.45]},
        'near': {'x': round(W('nearHip')[0] - waist[0], 1), 'shade': 0}, 'far': {'x': round(W('farHip')[0] - waist[0], 1), 'shade': .3}}
idle = {'near': round(W('nearAnkle')[0] - W('nearHip')[0], 1), 'far': round(W('farAnkle')[0] - W('farHip')[0], 1)}
rig = {'name': 'carden-proxy', 'version': 'proxy1', 'units': 'rig px (reference x2)', 'refOrigin': O, 'refScale': S, 'refLift': 0,
       'parts': parts, 'bones': bones, 'legs': LEGS, 'idleStance': idle,
       'draw': ['legFar', 'legNear', 'armF', 'foreF', 'torso', 'weapon', 'fistF', 'handL', 'armL', 'armU', 'pauldron', 'handR', 'head', 'beard'],
       'hidden': ['handL', 'handR'], 'faces': {}, 'metrics': {'bodyHeight': round((O[1] - J['hairTop'][1]) * S), 'note': 'proxy'},
       'ui': {'attack': 'thrust', 'touch': 'hop'}, 'note': '측정 대역 리그 — 연구용, 게임에 쓰지 않음'}
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
import sys
TUNE = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}
for k, v in TUNE.items():
    if k == 'legs':
        for s_, o_ in v.items(): rig['legs'][s_].update(o_) if isinstance(o_, dict) else rig['legs'].__setitem__(s_, o_)
    elif k == 'weaponRaise': rig['parts']['weapon']['pivot'][1] += v * S   # 봉을 손 안에서 위로 (원화 px)
    else: rig[k] = v
ENG = os.environ.get('ENGINE') or os.path.join(RIG, 'rig.js')   # 알론소 opt-in(runX·swingReach) 이 든 편집 툴 엔진을 쓸 때 ENGINE=경로
shutil.copy(ENG, os.path.join(OUT, 'rig.js'))
json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), ensure_ascii=False, indent=1)
print('proxy ok  thigh', round(TH), 'shin', round(SH), 'upper', round(LU), 'fore', round(LF), 'staff', round(SL), 'legs', LEGS['near']['x'], LEGS['far']['x'], 'idle', idle, 'body', rig['metrics']['bodyHeight'])
