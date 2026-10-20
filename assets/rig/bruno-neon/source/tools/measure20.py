"""20 네온 브루노 — 새 원화(0번 합격, ref512.png) 관절·철퇴 점 → ../measure20.json + ../review/measure20.png   (2026-10-21 01:10)
  팔·다리 점 = 원화 4배 격자(팔)·3배 격자(다리)에서 읽음 — 어깨 = 어깨갑 밑 윗팔 뿌리, 팔꿈치 = 윗팔(맨살)·팔뚝(크림 토시)이 꺾이는 곳 가운데,
  손목 = 토시 위 끝(금 리벳 띠) 가운데, 주먹 = 장갑 가운데, 무릎 = 무릎 가시판 가운데, 발목 = 부츠 목 가운데(10 measure10 과 같은 규칙)
  어깨 = 어깨갑 가운데 밑(가까운 (207,314) · 먼 (283,330)) — 윗팔 위 끝 둥근 원(반지름 12)이 어느 각에서도 어깨갑에 덮이게(seg20 어깨갑 칸에서 읽음, 처음 값 (200,318)·(289,336) = 어깨갑 가장자리)
  철퇴 공 가운데 = check_art20(옛 원화 공과 SIFT) 값, 가시 끝 반지름 = 64 × 공 배율
실행: python3 -I measure20.py
"""
import json, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
RA = Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA')
M = {'art': 'char_0020.png (ref512.png, DHL 10-21 01:00)', 'sole_y': 496, 'hairTop': [236, 157],
     'near': {'SH': [207, 314], 'EL': [150, 306], 'WR': [149, 262], 'fist': [141, 241], 'ball': [102, 71], 'ballR': 52},
     'far': {'SH': [283, 330], 'EL': [325, 350], 'WR': [339, 316], 'fist': [351, 293], 'ball': [454, 133], 'ballR': 52},
     'hip': [252, 376], 'neck': [264, 318],   # 골반 = 허리띠 가운데, 목 = 턱 아래 지퍼 깃 위(머리 조각 축) — 격자에서 읽음
     'legs': {'near': {'hip': [228, 386], 'knee': [211, 423], 'ankle': [188, 465]}, 'far': {'hip': [268, 388], 'knee': [303, 421], 'ankle': [318, 467]}}}
d_ = lambda a, b: round(math.hypot(a[0] - b[0], a[1] - b[1]), 1)
for sd in ('near', 'far'):
    s = M[sd]; s['len'] = {'upper': d_(s['SH'], s['EL']), 'fore_to_wrist': d_(s['EL'], s['WR']), 'fore_to_fist': d_(s['EL'], s['fist']), 'fist_to_ball': d_(s['fist'], s['ball'])}
    ax = (s['ball'][0] - s['fist'][0], s['ball'][1] - s['fist'][1]); s['axis_deg_from_vertical'] = round(math.degrees(math.atan2(ax[0], -ax[1])), 1)
for sd in ('near', 'far'):
    g = M['legs'][sd]; g['len'] = {'thigh': d_(g['hip'], g['knee']), 'shin': d_(g['knee'], g['ankle'])}
M['bodyH'] = M['sole_y'] - M['hairTop'][1]
M['gameTop_est'] = {'note': '게임 전투 칸 위 끝 ≈ 땅 − 1.81 × 몸 키(9·19 팔로메 game_top 실측 비율) — 게임에 넣기 전 game_top.py 로 다시 잼(실수 36)', 'y': round(M['sole_y'] - 1.81 * M['bodyH'], 1)}
M['arm_over_body'] = round((M['near']['len']['upper'] + M['near']['len']['fore_to_fist']) / M['bodyH'], 3)
json.dump(M, open(os.path.join(SRC, 'measure20.json'), 'w'), ensure_ascii=False, indent=1)
# 확인 그림(2배)
W = Image.new('RGBA', (512, 512), (235, 238, 245, 255)); W.alpha_composite(RA); W = W.convert('RGB').resize((1024, 1024), Image.LANCZOS); d = ImageDraw.Draw(W)
P = lambda p: (2 * p[0], 2 * p[1])
for sd, c in (('near', (230, 30, 30)), ('far', (30, 90, 230))):
    s = M[sd]; d.line([P(s['SH']), P(s['EL']), P(s['WR']), P(s['fist'])], fill=c, width=4); d.line([P(s['fist']), P(s['ball'])], fill=c, width=2)
    for k in ('SH', 'EL', 'WR', 'fist', 'ball'): x, y = P(s[k]); d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=(0, 0, 0), fill=c)
    x, y = P(s['ball']); r = 2 * s['ballR']; d.ellipse([x - r, y - r, x + r, y + r], outline=c, width=2)
    g = M['legs'][sd]; d.line([P(g['hip']), P(g['knee']), P(g['ankle'])], fill=(150, 60, 200), width=4)
    for k in ('hip', 'knee', 'ankle'): x, y = P(g[k]); d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=(0, 0, 0), fill=(150, 60, 200))
d.line([(0, 2 * M['sole_y']), (1024, 2 * M['sole_y'])], fill=(0, 160, 0), width=1)
os.makedirs(os.path.join(SRC, 'review'), exist_ok=True); W.save(os.path.join(SRC, 'review', 'measure20.png'))
print(json.dumps({sd: M[sd]['len'] | {'axis': M[sd]['axis_deg_from_vertical']} for sd in ('near', 'far')}, ensure_ascii=False))
print({sd: M['legs'][sd]['len'] for sd in ('near', 'far')}, 'bodyH', M['bodyH'], 'arm/body', M['arm_over_body'])
