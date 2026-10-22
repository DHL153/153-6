"""5 러스트 바실 — 원화(char_0005 = ref512.png) 관절·건틀릿 점 → ../measure5.json + ../review/measure5.png
  점 = 원화 2~4배 격자에서 읽음. 두 팔은 거의 다 큰 쇠 건틀릿(팔뚝까지 감싼 통) 속 — 보이는 건 가까운 어깨 살·먼 윗팔 살뿐.
  주먹 = 건틀릿 주먹 덩어리 가운데, 손목 = 건틀릿 갈색 가죽 소매 테 가운데, 팔꿈치 = 소매 테 뒤 끝(추정 — 프롬프트 2·3 지운 원화에서 다시 봄)
실행: python3 -I measure5.py
"""
import json, os, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
RA = Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA')
M = {'art': 'char_0005.png (ref512.png)', 'sole_y': 480, 'hairTop': [205, 37], 'hip': [262, 368], 'neck': [262, 262], 'pony': [178, 112],
     'near': {'SH': [152, 218], 'EL': [160, 258], 'WR': [140, 272], 'fist': [92, 300], 'gaunt': [[13, 300], [35, 245], [100, 215], [140, 215], [165, 232], [190, 285], [215, 345], [225, 390], [160, 395], [80, 385], [25, 345]]},
     'far': {'SH': [305, 215], 'EL': [340, 238], 'WR': [365, 245], 'fist': [440, 272], 'gaunt': [[338, 205], [370, 185], [440, 180], [500, 215], [508, 300], [470, 345], [400, 365], [360, 350], [345, 300], [335, 250]]},
     'legs': {'near': {'hip': [222, 392], 'knee': [172, 425], 'ankle': [150, 455]}, 'far': {'hip': [285, 392], 'knee': [305, 425], 'ankle': [307, 455]}}}
d_ = lambda a, b: round(math.hypot(a[0] - b[0], a[1] - b[1]), 1)
for sd in ('near', 'far'):
    s = M[sd]; s['len'] = {'upper': d_(s['SH'], s['EL']), 'fore_to_fist': d_(s['EL'], s['fist'])}
    g = M['legs'][sd]; g['len'] = {'thigh': d_(g['hip'], g['knee']), 'shin': d_(g['knee'], g['ankle'])}
M['bodyH'] = M['sole_y'] - M['hairTop'][1]
M['gameTop_est'] = {'note': '게임 전투 칸 위 끝 ≈ 땅 − 1.81 × 몸 키 — 공격 키를 짜기 전 game_top.py 로 다시 잼(36)', 'y': round(M['sole_y'] - 1.81 * M['bodyH'], 1)}
json.dump(M, open(os.path.join(SRC, 'measure5.json'), 'w'), ensure_ascii=False, indent=1)
W = Image.new('RGBA', (512, 512), (235, 238, 245, 255)); W.alpha_composite(RA); W = W.convert('RGB').resize((1024, 1024), Image.LANCZOS); d = ImageDraw.Draw(W)
P = lambda p: (2 * p[0], 2 * p[1])
for sd, c in (('near', (230, 30, 30)), ('far', (30, 90, 230))):
    s = M[sd]; d.polygon([P(p) for p in s['gaunt']], outline=c); d.line([P(s['SH']), P(s['EL']), P(s['WR']), P(s['fist'])], fill=c, width=4)
    for k in ('SH', 'EL', 'WR', 'fist'): x, y = P(s[k]); d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=(0, 0, 0), fill=c)
    g = M['legs'][sd]; d.line([P(g['hip']), P(g['knee']), P(g['ankle'])], fill=(150, 60, 200), width=4)
d.line([(0, 2 * M['sole_y']), (1024, 2 * M['sole_y'])], fill=(0, 160, 0))
W.save(os.path.join(SRC, 'review', 'measure5.png'))
print({sd: M[sd]['len'] for sd in ('near', 'far')}, {sd: M['legs'][sd]['len'] for sd in ('near', 'far')}, 'bodyH', M['bodyH'], 'gameTop', M['gameTop_est']['y'])
