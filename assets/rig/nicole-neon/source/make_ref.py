"""원화(sheet0) → 512 마이룸 그림(char_0018 후보) + ref1024(리그 기준, 512의 2배).  python3 -I make_ref.py
8 니콜 char_0008 과 같은 틀: 창 끝~발끝이 세로 1..506, 가로 가운데."""
import os, json
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
im = Image.open(os.path.join(HERE, 'cut', 'sheet0_keyed.png'))
A = np.asarray(im)[..., 3] > 128
ys, xs = np.where(A); y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
s = 505 / (y1 - y0 + 1)
w = round(im.width * s); h = round(im.height * s)
sm = im.resize((w, h), Image.LANCZOS)
ox = round(256 - (x0 + x1) / 2 * s); oy = round(1 - y0 * s)
out = Image.new('RGBA', (512, 512), (0, 0, 0, 0)); out.alpha_composite(sm, (ox, oy)) if ox >= 0 and oy >= 0 else out.paste(sm, (ox, oy), sm)
out.save(os.path.join(HERE, 'ref512.png'))
big = im.resize((round(im.width * s * 2), round(im.height * s * 2)), Image.LANCZOS)
ref = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0)); ref.paste(big, (ox * 2, oy * 2), big); ref.save(os.path.join(HERE, 'ref1024.png'))
B = np.asarray(out)[..., 3] > 128
# 몸 기둥(창 제외): 창은 오른쪽 세로 막대 → 몸 영역 = 창 x 범위 왼쪽
col = B.sum(0); 
info = dict(scale=s, ox=ox, oy=oy, sheetToRef1024=[s * 2, ox * 2, oy * 2])
json.dump(info, open(os.path.join(HERE, 'ref_info.json'), 'w'), indent=1); print(info)
