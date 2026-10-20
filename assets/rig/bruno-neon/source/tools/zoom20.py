"""20 네온 브루노 — 시각별 확대 그림(어두운 배경): python3 zoom20.py idle|run '0.2,0.233,...' 출력.png [k=1] [crop=x0,y0,x1,y1(원화 px)]
  idle = 서서 공격, run = 달리다 공격(달리기 120프레임 뒤), 시각 0 미만이면 대기·달리기 그대로(-1 = 공격 없음)
"""
import sys, os, subprocess
from PIL import Image, ImageDraw
H = os.path.dirname(os.path.abspath(__file__))
mode, ts, out = sys.argv[1], [float(x) for x in sys.argv[2].split(',')], sys.argv[3]
K = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0; crop = [int(v) for v in sys.argv[5].split(',')] if len(sys.argv) > 5 else [-60, 0, 560, 520]
PAD = 200; tiles = []
for t in ts:
    q = f'mode={mode}&k={K}&bgc=34343e&oy={2 * PAD}&ox={2 * PAD}&cw={2 * PAD}&pre={120 if mode == "run" else 90}'
    if t >= 0: q += f'&atk=smash&apre={round(t * 60)}'
    p = out + f'.{t}.png'; subprocess.run(['python3', os.path.join(H, 'shot.py'), q, p], check=True, capture_output=True)
    im = Image.open(p); s = 2 * K
    box = (int((crop[0] + PAD) * s), int((crop[1] + PAD) * s), int((crop[2] + PAD) * s), int((crop[3] + PAD) * s))
    tl = im.crop(box); d = ImageDraw.Draw(tl); d.text((6, 4), f'{mode} t={t:.3f}', fill=(255, 255, 0)); tiles.append(tl); os.remove(p)
cols = min(4, len(tiles)); rows = (len(tiles) + cols - 1) // cols; w, h = tiles[0].size
W = Image.new('RGB', (cols * w + (cols - 1) * 6, rows * h + (rows - 1) * 6), (255, 255, 255))
for i, tl in enumerate(tiles): W.paste(tl, ((i % cols) * (w + 6), (i // cols) * (h + 6)))
W.save(out); print('저장', out, W.size)
