"""rig.json v2 → v3: 새 조각(parts_v3.json)과 '창 먼저 + 두 손 자루 위(spearGrip)' 설정을 넣는다.
실행: cd source && python3 -I apply_v3.py   (v2 원본은 source/rig_v2.json 에 보관)"""
import json, os, shutil, math, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__)); RJ = os.path.join(HERE, '..', 'rig.json')
if not os.path.exists(os.path.join(HERE, 'rig_v2.json')): shutil.copy(RJ, os.path.join(HERE, 'rig_v2.json'))
d = json.load(open(os.path.join(HERE, 'rig_v2.json'))); g = json.load(open(os.path.join(HERE, 'parts_v3.json')))
P = d['parts']
def hand(name, key):
    q = g[key]; return dict(src=q['src'], pivot=q['elbow'], scale=q['scale'], grip=q['grip'], wrist=q['grip'], shaftDir=q['shaftDir'], elbow=q['elbow'])
# 뒷손: 기본 그림 이름 = armL (팀원 audit 이 parts.armL 을 찾음), 나머지 각도는 swap
for old in ['armL', 'fistN', 'foreF', 'armU']: P.pop(old, None)
P['handN0'] = hand('handN0', 'handN0'); P['armL'] = hand('armL', 'handN1'); P['handN2'] = hand('handN2', 'handN2')
P['armU3'] = dict(src=g['armU3']['src'], pivot=g['armU3']['shoulder'], elbow=g['armU3']['elbow'], scale=g['armU3']['scale'])
P['foreF'] = hand('foreF', 'handF0'); P['handF1'] = hand('handF1', 'handF1'); P['handF2'] = hand('handF2', 'handF2')
t = g['armTH']; P['armTH'] = dict(src=t['src'], pivot=t['shoulder'], scale=t['scale'], grip=t['grip'], shaftDir=t['shaftDir'], elbow=t['elbow'])
P['armF']['elbow'] = [round(45 + 48 / .55, 1), round(30 + 83.3 / .55, 1)]       # v2 뼈 길이 그대로 (먼 윗팔은 몸 뒤)
P['torso'] = dict(src=g['torso3']['src'], pivot=g['torso3']['pivot'], scale=g['torso3']['scale'])
P['pouch'] = dict(src=g['pouch3']['src'], pivot=g['pouch3']['pivot'], scale=g['pouch3']['scale'])
P['weapon'].update(pivot=[g['weapon']['axisX'], g['weapon']['gripRow']])
B = {b['name']: b for b in d['bones']}
B['armU']['part'] = 'armU3'; B['armL']['part'] = 'armL'; B['foreF']['part'] = 'foreF'
B['weapon'].update(parent='root', pos=[0, 0], rot=0)
del B['fistN']
bones = [b for b in d['bones'] if b['name'] != 'fistN']
bones.insert([b['name'] for b in bones].index('cape'), dict(name='pouch', parent='torso', pos=[0, 0], part='pouch'))
bones.append(dict(name='armTH', parent='torso', pos=[-80, -117], part='armTH'))
d['bones'] = bones
d['hidden'] = ['fistF', 'armTH']
# 찌른 팔(TH): 원본 그림에서 자루가 팔뚝 앞을 지나므로 팔은 창 뒤, 주먹만 창 앞 (v3.1)
import numpy as np
from PIL import Image as _I
from measure import masks as _masks
_a, _al, _br, _sk = _masks(os.path.join(HERE, '..', 'parts', 'armTH.png')); _ys, _xs = np.nonzero(_sk)
d['overlays'] = {'armTHfist': {'bone': 'armTH', 'rect': [int(_xs.min()) - 10, int(_ys.min()) - 12, int(np.ptp(_xs)) + 24, int(np.ptp(_ys)) + 26]}}
d['draw'] = ['cape', 'armF', 'pauldronF', 'legFar', 'legNear', 'torso', 'skirt', 'pouch', 'pony', 'head', 'armTH', 'weapon', 'foreF', 'fistF', 'armU', 'armL', 'pauldron', 'armTHfist']
d.pop('drawSmash', None); d.pop('twoHand', None); d.pop('smashHand2', None); d.pop('smashShoulder', None)
# 다리: L 시트 측정 (엉덩이 관절 높이 기준 배율) 허벅지 111 · 정강이 122
d['legs']['thigh'] = 111; d['legs']['shin'] = 122
# 창 먼저 + 두 손: 원본(마이룸) 앞손 쥔 점 = 몸통 기준 (178.1,-132.0), 각도 -30.96°; 손 간격 331 (원본 실측)
RAISE = float(os.environ.get('SKY_RAISE', '40'))   # 창 들어 올림(몸통 기준 위로, 리그 단위) — DHL 요청 2026-10-16
d['spearGrip'] = {
    'carry': {'x': 178.1, 'y': -132.0 - RAISE, 'a': round(math.radians(-30.96), 4)},
    'carryRun': {'x': 182.0, 'y': -126.0 - RAISE, 'a': round(math.radians(-24.0) - .28, 4)},     # K-달리기 24° (달릴 때 몸 숙임 .28 을 뺀 몸통 기준 각도)
    'tiltFollow': 1, 'maxWrist': .35,
    'far': {'pieces': ['foreF', 'handF1', 'handF2'], 'sPref': 0, 'sSig': 25, 'sMin': -300, 'sMax': 25, 'dMax': 50},
    'near': {'pieces': ['handN0', 'armL', 'handN2'], 'upper': 'armU3', 'sPref': -331, 'sSig': 70, 'sMin': -480, 'sMax': -90, 'restUp': 2.24, 'pauldronFollow': .35, 'dMin': float(os.environ.get('SKY_DMIN', '115'))},
    'th': {'piece': 'armTH'},
}
A_ = d['actions']['spearThrust']; A_['kind'] = 'spear'
for k in ('sh',): A_.pop(k, None)
A_['th'] = [[0, 0], [.19, 0, 'io'], [.24, 1], [.58, 1, 'io'], [.68, 0]]
A_['gx'] = [[0, 178, 'io'], [.18, 160, 's'], [.3, 330, 'o'], [.42, 320, 'io'], [.62, 230, 'io'], [.8, 178]]
A_['gy'] = [[0, -132 - RAISE, 'io'], [.18, -85 - RAISE * .6, 's'], [.3, -62 - RAISE * .4, 'o'], [.42, -64 - RAISE * .4, 'io'], [.62, -110 - RAISE * .8, 'io'], [.8, -132 - RAISE]]
A_['sa'] = [[0, -0.54, 'io'], [.18, -.42, 's'], [.3, -.06, 'o'], [.42, -.08, 'io'], [.62, -.45, 'io'], [.8, -.54]]              # 찌른 순간 뒷팔 = TH 한 장
A_['gap'] = [[0, 331, 'io'], [.18, 300, 's'], [.3, 230, 'o'], [.5, 230, 'io'], [.72, 331]]
d['hemLimit'] = {'up': .45, 'x': .6}
d['skirtFollow'] = .5
d['gait']['kneeLift'] = .95   # 다리 길이 실측(허벅지 111·정강이 122)에서 무릎 150° 넘지 않게 (1.12 → 무릎 155°)
d['version'] = 3
d['note'] = '28번 니콜 스카이 v3 (2026-10-16). 창 먼저 + 두 손은 자루를 따라 미끄러지며 시트 그림 그대로 쥠(spearGrip). 뒷손=N 시트 3각도, 앞손=F 시트 3각도, 찌른 순간 뒷팔=TH 한 장. 상체=T(허리 아래 늘림)+주머니는 치마 위.'
json.dump(d, open(RJ, 'w'), ensure_ascii=False, indent=1)
open(os.path.join(HERE, '..', 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['nicole-sky']=" + json.dumps(d, ensure_ascii=False, separators=(',', ':')) + ';\n')
print('ok', len(d['bones']), 'bones', len(P), 'parts')
