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
# 앞손 = 원본 그림의 손 그대로 (DHL 2026-10-18 "이 손을 그대로"): orig_hand.py 가 원본에서 팔뚝+손을 오림. 팔뚝은 창 뒤, 손가락만 창 앞(fingersF)
OH = os.environ.get('SKY_OH', '1') == '1'
if OH:
    oh = json.load(open(os.path.join(HERE, 'orig_hand.json')))
    P['foreF'] = dict(src=oh['src'], pivot=oh['pivot'], scale=oh['scale'], grip=oh['grip'], wrist=oh['wrist'], shaftDir=oh['shaftDir'], elbow=oh['elbow'])
    P['fingersF'] = dict(src=oh['fingers'], pivot=oh['pivot'], scale=oh['scale'])
    for _k in ('handF1', 'handF2'): P.pop(_k, None)
t = g['armTH']; P['armTH'] = dict(src=t['src'], pivot=t['shoulder'], scale=t['scale'], grip=t['grip'], shaftDir=t['shaftDir'], elbow=t['elbow'])
P['armF']['elbow'] = [round(45 + 48 / .55, 1), round(30 + 83.3 / .55, 1)]       # v2 뼈 길이 그대로 (먼 윗팔은 몸 뒤)
if os.environ.get('SKY_OH', '1') == '1':   # 원본 손: 원본처럼 팔뚝이 자루와 거의 나란해지려면 먼 윗팔 뼈가 짧아야 함 (대기 때 손목 꺾임 0이 되는 길이, 리그 단위)
    _L = float(os.environ.get('SKY_OH_UL', '68')); _v = [48 / .55, 83.3 / .55]; _n = math.hypot(*_v) * .55
    P['armF']['elbow'] = [round(45 + _v[0] * _L / _n, 1), round(30 + _v[1] * _L / _n, 1)]
P['torso'] = dict(src=g['torso3']['src'], pivot=g['torso3']['pivot'], scale=g['torso3']['scale'])
# 허리 (DHL 2026-10-16 "상체·하체가 붙어 있지 않음"): 원본엔 치마 남색 허리띠가 안 보이고 벨트 바로 아래서 치마 판이 시작.
#  → 상체를 치마 위에 그리고, 상체는 벨트 아래 TCUT px에서 자름(T 시트의 늘린 튜닉이 앞치마처럼 보이지 않게), 치마는 SKUP만큼 올려 허리띠를 벨트 뒤로 숨김
TCUT = int(os.environ.get('SKY_TCUT', '676')); SKUP = float(os.environ.get('SKY_SKUP', '12'))
import numpy as _np
from PIL import Image as _Im
_t = _np.asarray(_Im.open(os.path.join(HERE, '..', 'parts', 'torso3.png')).convert('RGBA')).copy()
_keep = _np.asarray(_Im.open(os.path.join(HERE, '..', 'parts', 'pouch3.png')).convert('RGBA'))[..., 3] > 0   # 주머니 자리는 남김 (주머니는 따로 치마 위에 다시 그림)
_rows = _np.arange(_t.shape[0])[:, None]; _fade = _np.clip((TCUT + 6 - _rows) / 6, 0, 1)
_t[..., 3] = (_t[..., 3] * _np.where(_keep, 1, _fade)).astype(_np.uint8)
_Im.fromarray(_t, 'RGBA').save(os.path.join(HERE, '..', 'parts', 'torsoC.png')); P['torso']['src'] = 'parts/torsoC.png'
P['torsoFull'] = dict(src=g['torso3']['src'], pivot=g['torso3']['pivot'], scale=g['torso3']['scale'])
P['pouch'] = dict(src=g['pouch3']['src'], pivot=g['pouch3']['pivot'], scale=g['pouch3']['scale'])
GSHIFT = float(os.environ.get('SKY_GSHIFT', '120'))   # 앞손이 쥐는 자리를 창 뒤끝 쪽으로 (리그 단위) = 두 손이 자루를 따라 내려감 (DHL 2026-10-16)
P['weapon'].update(pivot=[g['weapon']['axisX'], round(g['weapon']['gripRow'] + GSHIFT / P['weapon']['scale'], 1)])
B = {b['name']: b for b in d['bones']}
B['armU']['part'] = 'armU3'; B['armL']['part'] = 'armL'; B['foreF']['part'] = 'foreF'
B['weapon'].update(parent='root', pos=[0, 0], rot=0)
del B['fistN']
bones = [b for b in d['bones'] if b['name'] != 'fistN']
bones.insert([b['name'] for b in bones].index('cape'), dict(name='pouch', parent='torso', pos=[0, 0], part='pouch'))
bones.append(dict(name='armTH', parent='torso', pos=[-80, -117], part='armTH'))
bones.insert([b['name'] for b in bones].index('torso') + 1, dict(name='torsoUnder', parent='torso', pos=[0, 0], part='torsoFull'))   # 늘린 튜닉 전체를 치마 밑에 한 번 더 (몸을 숙여도 벨트 옆 빈틈 없음)
if OH: bones.insert([b['name'] for b in bones].index('foreF') + 1, dict(name='fingersF', parent='foreF', pos=[0, 0], part='fingersF'))
d['bones'] = bones
d['hidden'] = ['fistF', 'armTH']
# 찌른 팔(TH): 원본 그림에서 자루가 팔뚝 앞을 지나므로 팔은 창 뒤, 주먹만 창 앞 (v3.1)
import numpy as np
from PIL import Image as _I
from measure import masks as _masks
_a, _al, _br, _sk = _masks(os.path.join(HERE, '..', 'parts', 'armTH.png')); _ys, _xs = np.nonzero(_sk)
d['overlays'] = {'armTHfist': {'bone': 'armTH', 'rect': [int(_xs.min()) - 10, int(_ys.min()) - 12, int(np.ptp(_xs)) + 24, int(np.ptp(_ys)) + 26]}}
d['draw'] = ['cape', 'armF', 'pauldronF', 'legFar', 'legNear'] + ['torsoUnder', 'skirt', 'torso'] + ['pouch', 'pony', 'head', 'armTH', 'weapon', 'foreF', 'fistF', 'armU', 'armL', 'pauldron', 'armTHfist']
if OH: d['draw'] = [n for n in d['draw'] if n != 'foreF']; d['draw'].insert(d['draw'].index('weapon'), 'foreF'); d['draw'].insert(d['draw'].index('weapon') + 1, 'fingersF')
d.pop('drawSmash', None); d.pop('twoHand', None); d.pop('smashHand2', None); d.pop('smashShoulder', None)
# 다리: L 시트 측정 (엉덩이 관절 높이 기준 배율) 허벅지 111 · 정강이 122
d['legs']['thigh'] = 111; d['legs']['shin'] = 122
# 창 먼저 + 두 손: 원본(마이룸) 앞손 쥔 점 = 몸통 기준 (178.1,-132.0), 각도 -30.96°; 손 간격 331 (원본 실측)
RAISE = float(os.environ.get('SKY_RAISE', '40'))   # 창 들어 올림(몸통 기준 위로, 리그 단위) — DHL 요청 2026-10-16
d['spearGrip'] = {
    'carry': {'x': 178.1, 'y': -132.0 - RAISE, 'a': round(math.radians(-30.96), 4)},
    'carryRun': {'x': 182.0, 'y': -126.0 - RAISE, 'a': round(math.radians(-24.0) - .28, 4)},     # K-달리기 24° (달릴 때 몸 숙임 .28 을 뺀 몸통 기준 각도)
    'tiltFollow': 1, 'maxWrist': .35,
    'far': {'pieces': ['foreF'] if OH else ['foreF', 'handF1', 'handF2'], 'sPref': float(os.environ.get('SKY_FPREF', '0')), 'sSig': 25, 'sMin': -300, 'sMax': 25, 'dMax': 50},
    'near': {'pieces': ['handN0', 'armL', 'handN2'], 'upper': 'armU3', 'sPref': float(os.environ.get('SKY_NPREF', '-360')), 'sSig': float(os.environ.get('SKY_NSIG', '70')), 'sMin': -560, 'sMax': -90, 'restUp': 2.24, 'pauldronFollow': .35, 'dMin': float(os.environ.get('SKY_DMIN', '115'))},
    'th': {'piece': 'armTH'},
}
A_ = d['actions']['spearThrust']; A_['kind'] = 'spear'
for k in ('sh',): A_.pop(k, None)
A_['th'] = [[0, 0], [.19, 0, 'io'], [.24, 1], [.58, 1, 'io'], [.68, 0]]
A_['gx'] = [[0, 178, 'io'], [.18, 160, 's'], [.3, 330, 'o'], [.42, 320, 'io'], [.62, 230, 'io'], [.8, 178]]
A_['gy'] = [[0, -132 - RAISE, 'io'], [.18, -85 - RAISE * .6, 's'], [.3, -62 - RAISE * .4, 'o'], [.42, -64 - RAISE * .4, 'io'], [.62, -110 - RAISE * .8, 'io'], [.8, -132 - RAISE]]
A_['sa'] = [[0, -0.54, 'io'], [.18, -.42, 's'], [.3, -.06, 'o'], [.42, -.08, 'io'], [.62, -.45, 'io'], [.8, -.54]]              # 찌른 순간 뒷팔 = TH 한 장
A_['gap'] = [[0, 346, 'io'], [.18, 310, 's'], [.3, 230, 'o'], [.5, 230, 'io'], [.72, 346]]
d['hemLimit'] = {'up': .45, 'x': .6}
d['skirtFollow'] = float(os.environ.get('SKY_SF', '.9'))   # DHL: 허리가 몸에 붙지 않고 떠 보임 → 치마 윗단이 상체 기울기를 거의 그대로 따라감
for _b in d['bones']:
    if _b['name'] == 'skirt': _b['pos'] = [_b['pos'][0], _b['pos'][1] - SKUP]
d['hemLungeRel'] = True
d['hemRun'].update(lungeK=float(os.environ.get('SKY_LK', '.6')), lungeX=.4, kneeX=.45, actKnee=.35)
d['skirtStretch'] = float(os.environ.get('SKY_STR', '.07'))   # DHL: 치마가 더 내려와야 (올린 12 + 조금 더)   # 앞발이 나가도 앞자락이 얇게 늘어난 쐐기가 되지 않게   # 2026-10-16 DHL: 준비 자세에서 치마 앞자락이 뾰족하게 들리던 문제
# 망토: 단추 달린 위 띠(그림 x≈240~350, y≈0~30)가 목 뒤에 붙도록 — 기준점을 띠 오른쪽 끝으로, 뼈는 목 뒤 (DHL: 망토가 떠 있음)
P['cape']['pivot'] = [float(os.environ.get('SKY_CPX', '345')), 14]
for _b in d['bones']:
    if _b['name'] == 'cape': _b['pos'] = [float(os.environ.get('SKY_CBX', '-30')), float(os.environ.get('SKY_CBY', '-150'))]
d['gait']['kneeLift'] = .95   # 다리 길이 실측(허벅지 111·정강이 122)에서 무릎 150° 넘지 않게 (1.12 → 무릎 155°)
# 눈 깜빡임: B-깜빡임 시트(DHL) → build_blink.py 로 만든 얼굴 패치. 기준 머리 좌표 원점에서 head pivot 기준으로 변환
_br = json.load(open(os.path.join(HERE, 'blink_report.json'))); _hp = P['head']['pivot']
for _n in ('half', 'closed'):
    P['blink_' + _n] = dict(src=f'parts/blink_{_n}.png', pivot=[round(_hp[0] - _br[_n][0], 1), round(_hp[1] - _br[_n][1], 1)], scale=P['head']['scale'])
d['blinkFaces'] = {'half': 'blink_half', 'closed': 'blink_closed'}
d['version'] = 3
d['note'] = '28번 니콜 스카이 v3 (2026-10-16). 창 먼저 + 두 손은 자루를 따라 미끄러지며 시트 그림 그대로 쥠(spearGrip). 뒷손=N 시트 3각도, 앞손=F 시트 3각도, 찌른 순간 뒷팔=TH 한 장. 상체=T(허리 아래 늘림)+주머니는 치마 위.'
json.dump(d, open(RJ, 'w'), ensure_ascii=False, indent=1)
open(os.path.join(HERE, '..', 'rig.def.js'), 'w').write("// 자동 생성: rig.json을 JS로 감싼 것. 원본은 같은 폴더의 rig.json\nwindow.MR_RIG_DEFS=window.MR_RIG_DEFS||{};\nwindow.MR_RIG_DEFS['nicole-sky']=" + json.dumps(d, ensure_ascii=False, separators=(',', ':')) + ';\n')
print('ok', len(d['bones']), 'bones', len(P), 'parts')
