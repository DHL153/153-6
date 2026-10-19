# 공격 전체 필름: python3 tools/strip_atk.py out.png [dt=0.025] — render_atk 를 불러 작은 칸으로
import subprocess, sys, os, numpy as np
from PIL import Image
out = sys.argv[1]; dt = float(sys.argv[2]) if len(sys.argv) > 2 else .025
TS = [round(x, 3) for x in np.arange(0, .95 + 1e-6, dt)]
tmp = out.replace('.png', '_raw.png'); env = dict(os.environ, SC='.45')
subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'render_atk.py'), tmp, ','.join(map(str, TS)), '', 'overlay'], check=True, env=env)
im = Image.open(tmp); w, h = 900, 1000; n = len(TS); tiles = []
for i in range(n):
    t = im.crop(((i % 4) * w + 180, (i // 4) * h + 420, (i % 4) * w + 700, (i // 4) * h + 940)); tiles.append(t.resize((260, 260)))
cols = 10; rows = (n + cols - 1) // cols; c = Image.new('RGB', (260 * cols, 260 * rows), 'white')
for i, t in enumerate(tiles): c.paste(t, ((i % cols) * 260, (i // cols) * 260))
c.save(out); os.remove(tmp); print('strip', n, c.size)
