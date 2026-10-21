"""17 네온 루시아 — 새 원화(0번 합격, ref512.png) 관절·도끼 점 → ../measure17.json + ../review/measure17.png
  점 = 원화 격자 확대(grid17.py — 몸 4배 · 먼 팔 4·6배 · 다리 4배 · 방패 3배)에서 읽음
  먼 팔(갑옷이라 살 없음): 어깨 = 큰 크림 어깨갑 가운데 밑(윗팔 뿌리, 안 보임) · 팔꿈치 = 회색 네모 판 아래 짙은 소매(금 줄) 끝 = 크림 팔뚝 갑 왼쪽 아래 끝
    · 손목 = 회색 손목 고리 가운데 · 쥔 점 G = 자루 축 위 주먹 가운데 높이(y 289)
  도끼 자루 축 = 주먹 위 y 245 가운데 423 → 주먹 아래 y 330 가운데 444 (불투명 줄 가운데, 외곽선 포함)
  다리: 엉덩이 = 허리 판 밑(안 보임) · 무릎 = 짙은 회색 네모 무릎판과 금색 둥근 관절 사이 · 발목 = 부츠 옆 리벳(부츠 목)
  가까운 팔 = 방패 뒤(손잡이 쥔 손 안 보임 — DHL 10-21 09:43) → 점 없음, 리그는 빈 뼈
실행: python3 -I measure17.py
"""
import json, os, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
RA = Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA')
M = {'art': 'char_0017.png (ref512.png, DHL 10-21 09:54)', 'sole_y': 450, 'hatTop': [292, 180],
     'O': [290, 450], 'HIP': [298, 352], 'NECK': [295, 282],          # 뿌리 = 두 발 가운데 땅 · 골반 = 허리띠 버클 가운데 · 목 = 목 가리개 안(머리 회전 중심)
     'far': {'SH': [355, 283], 'EL': [367, 335], 'WR': [405, 306], 'G': [433.9, 289]},
     'axe': {'shaftTop': [423, 245], 'shaftLow': [444, 330], 'pommelBottomY': 377, 'topY': 52},
     'legs': {'near': {'hip': [240, 360], 'knee': [231, 390], 'ankle': [225, 428]}, 'far': {'hip': [316, 362], 'knee': [344, 393], 'ankle': [348, 428]}},
     'rust7': {'SH_F': [355, 290], 'EL_F': [389, 337], 'WR_F': [411, 311], 'G': [434.5, 294], 'legs': {'near': [[245, 362], [231, 393], [207, 430]], 'far': [[310, 362], [349, 392], [342, 430]]}}}
d_ = lambda a, b: round(math.hypot(a[0] - b[0], a[1] - b[1]), 1)
f = M['far']; f['len'] = {'upper': d_(f['SH'], f['EL']), 'fore': d_(f['EL'], f['WR']), 'wrist_to_G': d_(f['WR'], f['G'])}
ax = M['axe']; ax['deg_from_vertical'] = round(math.degrees(math.atan2(ax['shaftLow'][0] - ax['shaftTop'][0], ax['shaftLow'][1] - ax['shaftTop'][1])), 1)
for sd in ('near', 'far'):
    g = M['legs'][sd]; g['len'] = {'thigh': d_(g['hip'], g['knee']), 'shin': d_(g['knee'], g['ankle'])}
r = M['rust7']; r['len'] = {'upper': d_(r['SH_F'], r['EL_F']), 'fore': d_(r['EL_F'], r['WR_F']), 'wrist_to_G': d_(r['WR_F'], r['G']),
                            'near': [d_(*r['legs']['near'][:2]), d_(*r['legs']['near'][1:])], 'far': [d_(*r['legs']['far'][:2]), d_(*r['legs']['far'][1:])]}
M['bodyH'] = M['sole_y'] - M['hatTop'][1]
json.dump(M, open(os.path.join(SRC, 'measure17.json'), 'w'), ensure_ascii=False, indent=1)
# 확인 그림(2배)
W = Image.new('RGBA', (512, 512), (235, 238, 245, 255)); W.alpha_composite(RA); W = W.convert('RGB').resize((1024, 1024), Image.LANCZOS); d = ImageDraw.Draw(W)
P = lambda p: (2 * p[0], 2 * p[1])
def dot(p, c):
    x, y = P(p); d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=(0, 0, 0), fill=c)
d.line([P(f['SH']), P(f['EL']), P(f['WR']), P(f['G'])], fill=(30, 90, 230), width=4)
for k in ('SH', 'EL', 'WR', 'G'): dot(f[k], (30, 90, 230))
d.line([P(ax['shaftTop']), P(ax['shaftLow'])], fill=(0, 180, 200), width=2)
for sd in ('near', 'far'):
    g = M['legs'][sd]; d.line([P(g['hip']), P(g['knee']), P(g['ankle'])], fill=(150, 60, 200), width=4)
    for k in ('hip', 'knee', 'ankle'): dot(g[k], (150, 60, 200))
for k, c in (('HIP', (230, 30, 30)), ('NECK', (230, 120, 0)), ('O', (0, 160, 0))): dot(M[k], c)
d.line([(0, 2 * M['sole_y']), (1024, 2 * M['sole_y'])], fill=(0, 160, 0), width=1)
os.makedirs(os.path.join(SRC, 'review'), exist_ok=True); W.save(os.path.join(SRC, 'review', 'measure17.png'))
print('far', f['len'], 'axe', ax['deg_from_vertical'], '° · legs', {sd: M['legs'][sd]['len'] for sd in ('near', 'far')}, '· bodyH', M['bodyH'])
print('rust7', r['len'])
