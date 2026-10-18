#!/usr/bin/env python3
"""장면 프레임들을 한 장으로 (실제 크기 1/2, 땅선 표시). python3 sheet.py PKG scene t1,t2,.. out.png [cols]"""
import sys, os, glob, subprocess
from PIL import Image, ImageDraw
pkg, scene, ts, out = sys.argv[1:5]; cols = int(sys.argv[5]) if len(sys.argv) > 5 else 6
here = os.path.dirname(os.path.abspath(__file__)); tmp = out + '_f'
for f in glob.glob(tmp + '_*.png'): os.remove(f)
subprocess.run([sys.executable, os.path.join(here, 'render.py'), pkg, tmp, scene, ts, '1300', '1150', '650', '1100', '1'], check=True, stdout=subprocess.DEVNULL)
fs = sorted(glob.glob(tmp + '_*.png')); tl = ts.split(',')
W, H = 650, 575; rows = (len(fs) + cols - 1) // cols; o = Image.new('RGB', (W * cols, H * rows), (255, 255, 255)); d = ImageDraw.Draw(o)
for i, f in enumerate(fs):
    im = Image.open(f); bg = Image.new('RGBA', im.size, (250, 244, 214, 255)); bg.alpha_composite(im); t = bg.convert('RGB').resize((W, H), Image.LANCZOS)
    x, y = (i % cols) * W, (i // cols) * H; o.paste(t, (x, y)); d.line([(x, y + 550), (x + W, y + 550)], fill=(120, 120, 120)); d.text((x + 6, y + 4), f'{scene} t={tl[i]}', fill=(0, 0, 0))
    os.remove(f)
o.save(out); print(out)
