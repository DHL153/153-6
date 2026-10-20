"""17 네온 루시아 — 원화 격자 확대(눈대중 측정용) : python3 -I grid17.py 그림 x0 y0 x1 y1 배율 출력"""
import sys
from PIL import Image, ImageDraw, ImageFont
p, x0, y0, x1, y1, k, out = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
im = Image.open(p).convert('RGBA').crop((x0, y0, x1, y1)); W, H = im.size
bg = Image.new('RGBA', (W, H), (255, 255, 255, 255)); bg.alpha_composite(im); im = bg.resize((W * k, H * k), Image.NEAREST)
d = ImageDraw.Draw(im); f = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 12)
for x in range((x0 // 10) * 10, x1 + 1, 10):
    X = (x - x0) * k; d.line([(X, 0), (X, H * k)], fill=(255, 0, 0, 255) if x % 50 == 0 else (255, 170, 170, 255), width=1)
    if x % 50 == 0: d.text((X + 2, 2), str(x), fill=(200, 0, 0), font=f)
for y in range((y0 // 10) * 10, y1 + 1, 10):
    Y = (y - y0) * k; d.line([(0, Y), (W * k, Y)], fill=(0, 0, 255, 255) if y % 50 == 0 else (170, 170, 255, 255), width=1)
    if y % 50 == 0: d.text((2, Y + 2), str(y), fill=(0, 0, 200), font=f)
im.convert('RGB').save(out)
