# 원화 구역 격자 확대: python3 -I grid.py x0 y0 x1 y1 배율 out.png [그림=../ref512.png]
import sys, os
from PIL import Image, ImageDraw
x0, y0, x1, y1, k = map(int, sys.argv[1:6]); out = sys.argv[6]; src = sys.argv[7] if len(sys.argv) > 7 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref512.png')
a = Image.open(src).convert('RGBA'); bg = Image.new('RGBA', a.size, (255, 255, 255, 255)); bg.alpha_composite(a)
c = bg.crop((x0, y0, x1, y1)).convert('RGB').resize(((x1 - x0) * k, (y1 - y0) * k), Image.NEAREST); d = ImageDraw.Draw(c)
for x in range((x0 // 10) * 10, x1 + 1, 10):
    if x < x0: continue
    d.line([((x - x0) * k, 0), ((x - x0) * k, c.height)], fill=(255, 0, 0) if x % 50 == 0 else (255, 170, 170)); d.text(((x - x0) * k + 2, 2), str(x), fill=(200, 0, 0))
for y in range((y0 // 10) * 10, y1 + 1, 10):
    if y < y0: continue
    d.line([(0, (y - y0) * k), (c.width, (y - y0) * k)], fill=(0, 0, 255) if y % 50 == 0 else (170, 170, 255)); d.text((2, (y - y0) * k + 2), str(y), fill=(0, 0, 200))
c.save(out)
