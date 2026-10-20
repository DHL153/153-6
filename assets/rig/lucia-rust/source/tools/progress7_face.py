# 7 루시아 공격 먼 팔 전/후 진행 그림(편집 툴·DHL 보고용, 10-21 v1.4 — DHL 10-20 23:58 '공격할때 눈 감지 않도록')
#   먼저: tools/rig_shots.py 전PREFIX "t1,…" 1.0 (전 리그) · tools/rig_shots.py 후PREFIX "t1,…" 1.0 (지금 리그)
#   python3 -I tools/progress7_arm.py 전PREFIX 후PREFIX "t1,t2,…" OUT.jpg [제목]   (캔버스 1400, 땅 y1300 — 머리 둘레 기본 x 560~900 · y 760~1060, X0·Y0·X1·Y1 로 바꿈)
import sys, os
from PIL import Image, ImageDraw, ImageFont
pb, pa, T, out = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4]; title = sys.argv[5] if len(sys.argv) > 5 else ''
FT = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 26); FS = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 19)
NAVY = (40, 56, 96); x0, y0, x1, y1 = int(os.environ.get('X0', 560)), int(os.environ.get('Y0', 760)), int(os.environ.get('X1', 900)), int(os.environ.get('Y1', 1060)); W = 2000; tw = W // len(T); s = tw / (x1 - x0); th = int((y1 - y0) * s)
B = Image.new('RGB', (W, 48 + 2 * (th + 34)), (232, 236, 242)); d = ImageDraw.Draw(B); d.text((10, 6), title, fill=(30, 40, 60), font=FT)
for r, (p, lab) in enumerate(((pb, 'v1.3 (전) — 집중(눈꺼풀 반) → 힘줌(두 눈 꽉 감음) → 외침 → 집중'), (pa, 'v1.4 (후) — 화남(눈 뜸) → 외침(눈 크게) → 화남 · 공격 내내 눈 뜸'))):
    Y = 48 + r * (th + 34); d.text((10, Y + 4), lab, fill=(30, 40, 60), font=FS)
    for c, t in enumerate(T):
        im = Image.open(f'{p}_{float(t):.3f}.png').convert('RGBA').crop((x0, y0, x1, y1)); bg = Image.new('RGBA', im.size, NAVY + (255,)); bg.alpha_composite(im)
        B.paste(bg.resize((tw, th), Image.LANCZOS).convert('RGB'), (c * tw, Y + 34)); d.text((c * tw + 6, Y + 38), f'{t}초', fill=(255, 220, 0), font=FS)
B.save(out, quality=88); print(out, B.size)
