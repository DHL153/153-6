#!/usr/bin/env python3
"""조각 ↔ 원화 같은 부위를 같은 배율로 나란히 (검수 규칙 4·6·14: 비교 그림 없이 합격 금지)
python3 -I side.py review/side_hands.png fistF:fistF handL:battle_lead ...
  왼쪽 이름 = cut/<이름>.png, 오른쪽 = 원화 부위 이름(REGION) — 배율은 시트 봉 길이 ÷ 원화 봉 길이(봉이 없으면 머리 폭)로 맞춤
"""
import json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
REF = Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA'); BAT = Image.open(os.path.join(HERE, 'battle_ref.png')).convert('RGBA')
# 원화(ref512) 부위 상자 — measure/joints_ref.json 과 같은 날 격자로 읽음. battle_* 는 전투 그림(battle_ref)에서
REGION = {'head': (190, 140, 330, 260), 'beard': (210, 240, 365, 365), 'torso': (150, 250, 360, 395), 'pauldron': (105, 250, 200, 305),
          'armL': (65, 325, 165, 420), 'fistF': (375, 255, 445, 350), 'hips': (200, 380, 300, 435), 'legN': (135, 400, 225, 500),
          'legF': (260, 400, 335, 495), 'weapon': (380, 8, 465, 500), 'tufts': (95, 140, 360, 240),
          'battle_lead': (300, 160, 400, 260), 'battle_rear': (140, 330, 260, 420)}
idx = json.load(open(os.path.join(HERE, 'cut', '_index.json')))
it = idx['items']
k = (it['weapon']['len'] / 484.0) if 'weapon' in it else (it['head']['box'][2] / 140.0)   # 시트 px ÷ 원화 px
tiles = []
for pair in sys.argv[2:]:
    a, b = pair.split(':'); P = Image.open(os.path.join(HERE, 'cut', a + '.png')).convert('RGBA'); P = P.resize((max(1, round(P.width / k * 2)), max(1, round(P.height / k * 2))), Image.LANCZOS)
    src = BAT if b.startswith('battle_') else REF; R = src.crop(REGION[b]); R = R.resize((R.width * 2, R.height * 2), Image.LANCZOS)
    h = max(P.height, R.height) + 24; t = Image.new('RGBA', (P.width + R.width + 30, h), (245, 240, 225, 255))
    t.alpha_composite(P, (5, 20)); t.alpha_composite(R, (P.width + 25, 20)); d = ImageDraw.Draw(t); d.text((5, 3), f'{a} (시트)', fill=(0, 0, 0)); d.text((P.width + 25, 3), f'{b} (원화)', fill=(0, 0, 0))
    tiles.append(t)
W = max(t.width for t in tiles); H = sum(t.height for t in tiles) + 6 * len(tiles); o = Image.new('RGB', (W, H), 'white'); y = 0
for t in tiles: o.paste(t, (0, y)); y += t.height + 6
o.save(os.path.join(HERE, sys.argv[1])); print(sys.argv[1], 'scale', round(k, 3))
