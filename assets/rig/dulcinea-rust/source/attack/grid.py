# 칸 그림에 좌표 격자: python3 attack/grid.py a2 x0,y0,x1,y1 k out.png
import sys
from PIL import Image, ImageDraw
n, box, k, out = sys.argv[1], [int(v) for v in sys.argv[2].split(',')], float(sys.argv[3]), sys.argv[4]
im = Image.open(f'atk_frames/{n}.png').convert('RGBA') if not n.endswith('.png') else Image.open(n).convert('RGBA')
bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); a = bg.crop(box).convert('RGB')
a = a.resize((int(a.width * k), int(a.height * k)), Image.LANCZOS); d = ImageDraw.Draw(a)
st = 20 if (box[2] - box[0]) <= 300 else 50
for x in range((box[0] // st + 1) * st, box[2], st):
    X = (x - box[0]) * k; d.line([(X, 0), (X, a.height)], fill=(255, 0, 0) if x % 100 == 0 else (255, 160, 160)); d.text((X + 2, 2), str(x), fill=(200, 0, 0))
for y in range((box[1] // st + 1) * st, box[3], st):
    Y = (y - box[1]) * k; d.line([(0, Y), (a.width, Y)], fill=(0, 0, 255) if y % 100 == 0 else (160, 160, 255)); d.text((2, Y + 2), str(y), fill=(0, 0, 200))
a.save(out)
