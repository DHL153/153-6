# 대기 = 원화 확인: shot.py 'ov=2&k=0.5&pre=1' → 왼쪽 원화 · 오른쪽 리그 (1:1), 부품별 차이 — python3 -I tools/idlediff.py [쿼리 더함]
import subprocess, sys, os
import numpy as np
from PIL import Image
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
q = 'ov=2&k=0.5&pre=1' + (('&' + sys.argv[1]) if len(sys.argv) > 1 else '')
subprocess.run(['python3', os.path.join(S, 'tools', 'shot.py'), q, os.path.join(S, 'review', 'idle_cmp.png')], check=True, capture_output=True)
im = np.array(Image.open(os.path.join(S, 'review', 'idle_cmp.png')).convert('RGB')).astype(int); half = im.shape[1] // 2
a = im[:, :half]; b = im[:, half:half * 2]; d = np.abs(a - b).max(2)
LAB = np.load(os.path.join(S, 'work', 'labels.npy')); import json; names = json.load(open(os.path.join(S, 'work', 'label_names.json')))
print('all mean', round(float(np.abs(a - b).mean()), 2), ' >40px', int((d > 40).sum()))
for i, n in enumerate(names): m = LAB == i + 1; print(f'  {n:9s} mean {d[m].mean():6.1f}  >40 {int((d[m] > 40).sum())}')
print('  background >40', int((d[LAB == 0] > 40).sum()))
Image.fromarray(np.clip(d * 3, 0, 255).astype(np.uint8)).save(os.path.join(S, 'review', 'idle_diff.png'))
