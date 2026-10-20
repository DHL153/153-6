# 7 루시아 공격 먼 팔 전/후 진행 그림(편집 툴·DHL 보고용, 10-20 v1.2 — DHL 22:44 '공격의 이 팔이 이상 · 각지지 않게 · 원본 팔 · 얇은 것도 이상')
#   먼저: tools/rig_shots.py 전PREFIX "t1,…" 1.0 (전 리그) · tools/rig_shots.py 후PREFIX "t1,…" 1.0 (지금 리그)
#   python3 -I tools/progress7_arm.py 전PREFIX 후PREFIX "t1,t2,…" OUT.jpg [제목]   (캔버스 1400, 땅 y1300 — 팔 둘레 x 600~1060 · y 700~1260)
import sys, os
from PIL import Image, ImageDraw, ImageFont
pb, pa, T, out = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4]; title = sys.argv[5] if len(sys.argv) > 5 else ''
FT = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 26); FS = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 19)
NAVY = (40, 56, 96); x0, y0, x1, y1 = 600, 700, 1060, 1260; W = 2000; tw = W // len(T); s = tw / (x1 - x0); th = int((y1 - y0) * s)
B = Image.new('RGB', (W, 48 + 2 * (th + 34)), (232, 236, 242)); d = ImageDraw.Draw(B); d.text((10, 6), title, fill=(30, 40, 60), font=FT)
for r, (p, lab) in enumerate(((pb, 'v1.1 (전) — 윗팔 = 민무늬 갈색 관(가늘고 각짐)'), (pa, 'v1.2 (후) — 윗팔 = 원화 소매 그대로 · 들어 올릴 때만 같은 무늬 곧은 소매 · 둥근 팔꿈치'))):
    Y = 48 + r * (th + 34); d.text((10, Y + 4), lab, fill=(30, 40, 60), font=FS)
    for c, t in enumerate(T):
        im = Image.open(f'{p}_{float(t):.3f}.png').convert('RGBA').crop((x0, y0, x1, y1)); bg = Image.new('RGBA', im.size, NAVY + (255,)); bg.alpha_composite(im)
        B.paste(bg.resize((tw, th), Image.LANCZOS).convert('RGB'), (c * tw, Y + 34)); d.text((c * tw + 6, Y + 38), f'{t}초', fill=(255, 220, 0), font=FS)
B.save(out, quality=88); print(out, B.size)
