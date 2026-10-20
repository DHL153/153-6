# 원화 부분 확대 + 10px 격자(좌표 읽기용): python3 -I tools/gridzoom.py x0 y0 x1 y1 k out.png [원화]
import sys, os
from PIL import Image, ImageDraw
x0, y0, x1, y1, k = map(int, sys.argv[1:6]); out = sys.argv[6]
HERE = os.path.dirname(os.path.abspath(__file__)); ART = sys.argv[7] if len(sys.argv) > 7 else os.path.join(HERE, '..', 'ref512.png')
im = Image.open(ART).convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
c = bg.crop((x0, y0, x1, y1)).convert('RGB').resize(((x1 - x0) * k, (y1 - y0) * k), Image.LANCZOS); d = ImageDraw.Draw(c)
for v in range((x0 // 10 + 1) * 10, x1, 10):
    X = (v - x0) * k; col = (255, 0, 0) if v % 50 == 0 else (255, 175, 175); d.line([(X, 0), (X, c.height)], fill=col, width=1)
    if v % 50 == 0: d.text((X + 2, 2), str(v), fill=(220, 0, 0))
for v in range((y0 // 10 + 1) * 10, y1, 10):
    Y = (v - y0) * k; col = (255, 0, 0) if v % 50 == 0 else (255, 175, 175); d.line([(0, Y), (c.width, Y)], fill=col, width=1)
    if v % 50 == 0: d.text((2, Y + 2), str(v), fill=(220, 0, 0))
c.save(out)
