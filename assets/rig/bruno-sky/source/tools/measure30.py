"""30 스카이 브루노 — 새 원화(0번 합격, ref512.png) 관절·도끼 점 → ../measure30.json + ../review/measure30.png   (measure20 구조)
  팔·다리 점 = 원화 5배 격자(팔)·3배 격자(다리)에서 읽음 — 어깨 = 어깨갑(가까운 은색)·소매(먼 남색) 밑 윗팔 뿌리, 팔꿈치 = 주황 맨살 팔꿈치 가운데,
  손목 = 갈색 토시 위 크림 감기·장갑 목 가운데, 주먹 = 장갑 가운데, 무릎 = 은색 무릎판 가운데, 발목 = 부츠 목(금 버클 끈 위) 가운데
  윗팔은 러스트처럼 거의 다 소매·어깨갑 속(보이는 건 팔꿈치 둘레 맨살뿐) — 10 v1.2 의 '소매 입구 ±25°' 규칙을 씀
  도끼 소켓 가운데 = check_art30(옛 원화 도끼 머리와 SIFT) 값
실행: python3 -I measure30.py
"""
import json, os, math
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
RA = Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA')
M = {'art': 'char_0030.png (ref512.png, DHL 10-21 17:44)', 'sole_y': 497, 'hairTop': [210, 156],
     'near': {'SH': [200, 318], 'EL': [162, 325], 'WR': [141, 268], 'fist': [144, 241], 'head': [91, 75], 'pommel': [151, 278]},
     'far': {'SH': [298, 335], 'EL': [318, 340], 'WR': [342, 318], 'fist': [348, 292], 'head': [436, 145], 'pommel': [337, 322]},
     'hip': [265, 372], 'neck': [282, 318], 'pony': [226, 203],   # 골반 = 허리띠 가운데(버클), 목 = 복면 아래 깃 위(머리 조각 축), 포니테일 = 남색 끈 묶은 곳
     'legs': {'near': {'hip': [236, 388], 'knee': [210, 418], 'ankle': [183, 458]}, 'far': {'hip': [280, 388], 'knee': [308, 417], 'ankle': [318, 463]}}}
d_ = lambda a, b: round(math.hypot(a[0] - b[0], a[1] - b[1]), 1)
for sd in ('near', 'far'):
    s = M[sd]; s['len'] = {'upper': d_(s['SH'], s['EL']), 'fore_to_wrist': d_(s['EL'], s['WR']), 'fore_to_fist': d_(s['EL'], s['fist']), 'fist_to_head': d_(s['fist'], s['head'])}
    ax = (s['head'][0] - s['fist'][0], s['head'][1] - s['fist'][1]); s['axis_deg_from_vertical'] = round(math.degrees(math.atan2(ax[0], -ax[1])), 1)
for sd in ('near', 'far'):
    g = M['legs'][sd]; g['len'] = {'thigh': d_(g['hip'], g['knee']), 'shin': d_(g['knee'], g['ankle'])}
M['bodyH'] = M['sole_y'] - M['hairTop'][1]
M['gameTop_est'] = {'note': '게임 전투 칸 위 끝 ≈ 땅 − 1.81 × 몸 키(9·19 팔로메 game_top 실측 비율) — 게임에 넣기 전 game_top.py 로 다시 잼(실수 36)', 'y': round(M['sole_y'] - 1.81 * M['bodyH'], 1)}
M['arm_over_body'] = round((M['near']['len']['upper'] + M['near']['len']['fore_to_fist']) / M['bodyH'], 3)
json.dump(M, open(os.path.join(SRC, 'measure30.json'), 'w'), ensure_ascii=False, indent=1)
W = Image.new('RGBA', (512, 512), (235, 238, 245, 255)); W.alpha_composite(RA); W = W.convert('RGB').resize((1024, 1024), Image.LANCZOS); d = ImageDraw.Draw(W)
P = lambda p: (2 * p[0], 2 * p[1])
for sd, c in (('near', (230, 30, 30)), ('far', (30, 90, 230))):
    s = M[sd]; d.line([P(s['SH']), P(s['EL']), P(s['WR']), P(s['fist'])], fill=c, width=4); d.line([P(s['fist']), P(s['head'])], fill=c, width=2)
    for k in ('SH', 'EL', 'WR', 'fist', 'head'): x, y = P(s[k]); d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=(0, 0, 0), fill=c)
    g = M['legs'][sd]; d.line([P(g['hip']), P(g['knee']), P(g['ankle'])], fill=(150, 60, 200), width=4)
    for k in ('hip', 'knee', 'ankle'): x, y = P(g[k]); d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=(0, 0, 0), fill=(150, 60, 200))
d.line([(0, 2 * M['sole_y']), (1024, 2 * M['sole_y'])], fill=(0, 160, 0), width=1)
os.makedirs(os.path.join(SRC, 'review'), exist_ok=True); W.save(os.path.join(SRC, 'review', 'measure30.png'))
print(json.dumps({sd: M[sd]['len'] | {'axis': M[sd]['axis_deg_from_vertical']} for sd in ('near', 'far')}, ensure_ascii=False))
print({sd: M['legs'][sd]['len'] for sd in ('near', 'far')}, 'bodyH', M['bodyH'], 'arm/body', M['arm_over_body'])
