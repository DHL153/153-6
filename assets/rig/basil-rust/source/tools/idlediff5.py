"""5 러스트 바실 — 대기 리그 vs 원화 차이(숨쉬기 여러 위상, 깜빡임 없는 장면) — python3 -I idlediff5.py [출력.png]
  shot.py 로 k=0.5(= 원화 512) 어두운 배경(34343e) 렌더 → 원화와 RGB 차(알파 곱)·알파 IoU·차이 큰 곳 그림
"""
import sys, os, subprocess
import numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(H)
RA = np.array(Image.open(os.path.join(S, 'ref512.png')).convert('RGBA')).astype(float)
out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/idlediff5.png'; rows = []
for pre in (1, 40, 80, 120, 160):
    p = out + f'.{pre}.png'; subprocess.run(['python3', os.path.join(H, 'shot.py'), f'mode=idle&k=0.5&bgc=34343e&pre={pre}&expr=neutral', p], check=True, capture_output=True)
    B = np.array(Image.open(p).convert('RGB')).astype(float)[:512, :512]; bg0 = np.array([52, 52, 62.])
    pa = RA[..., :3] * RA[..., 3:4] / 255 + bg0 * (1 - RA[..., 3:4] / 255); d = np.abs(pa - B).max(-1)
    a1, a2 = RA[..., 3] > 128, np.abs(B - bg0).max(-1) > 30; iou = (a1 & a2).sum() / max(1, (a1 | a2).sum())
    rows.append((pre, float(d.mean()), float(iou), int((d > 60).sum()), d, B))
    print(f'pre {pre:3d}: 평균 차 {d.mean():.2f} · IoU {iou:.4f} · 차 > 60 px {int((d > 60).sum())}')
best = min(rows, key=lambda r: r[1]); d = best[4]
v = np.zeros((512, 1024, 3), np.uint8); bgc = np.array([52, 52, 62.])
v[:, :512] = (RA[..., :3] * RA[..., 3:4] / 255 + bgc * (1 - RA[..., 3:4] / 255)).astype(np.uint8)
r = best[5].copy(); r[d > 60] = (255, 40, 40); v[:, 512:] = r.astype(np.uint8)
Image.fromarray(v).save(out); print('그림', out, '(오른쪽 = 리그, 빨강 = 차 > 60)')
