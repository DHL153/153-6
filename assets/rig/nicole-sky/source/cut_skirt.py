"""치마 오른쪽(앞쪽) 윗부분 다듬기 → parts/skirt.png
기록
- 2026-10-17 1차: DHL "옷이 없어야 할 부분에 있어요" → 앞쪽 바깥 자락(크림 띠+남색 자락)을 통째로 잘라냄.
  DHL 원본 그림을 다시 보여주며 "자연스럽게 떨어져야" → 원본에는 그 자락이 있음. 잘라낸 건 잘못된 해석.
- 2026-10-17 2차(지금): 자락은 모두 살리고, 원본과 달랐던 '허리 오른쪽 끝이 벨트 밖으로 각지게 튀어나온 부분'만 고침.
  원본은 바깥 선이 벨트 끝에서 시작해 밑단까지 한 줄로 비스듬히 내려옴. 치마 그림은 허리띠가 벨트보다 약 25px 넓어
  모서리가 벨트 밖으로 나와 있었음 → 오른쪽을 허리 쪽만 안으로 모으고(밑단으로 갈수록 0) 판 무늬는 비율 그대로 유지.
실행: cd source && python3 -I cut_skirt.py
"""
import os, numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
D0 = float(os.environ.get('SKY_SKD', '26'))     # 허리 맨 위에서 오른쪽 끝을 안으로 당기는 양(px)
Y1 = float(os.environ.get('SKY_SKY1', '190'))   # 이 높이까지 당김이 0으로 줄어듦 (밑단 모양은 원본 그대로)
X0 = 205                                         # 이보다 왼쪽(가운데 크림 판 왼쪽)은 그대로
src = np.asarray(Image.open(os.path.join(HERE, 'skirt_v2_full.png')).convert('RGBA')).astype(np.float32)
H, W = src.shape[:2]
pm = src.copy(); pm[..., :3] *= pm[..., 3:4] / 255          # 가장자리 색 번짐 막기(미리 곱한 알파로 보간)
al = src[..., 3] > 100
mapx = np.tile(np.arange(W, dtype=np.float32), (H, 1)); mapy = np.tile(np.arange(H, dtype=np.float32)[:, None], (1, W))
for y in range(H):
    t = max(0.0, 1 - y / Y1)
    xs = np.nonzero(al[y])[0]
    if t <= 0 or not len(xs): continue
    xr = xs.max() + 2; d = D0 * t ** 1.6
    u = np.clip((np.arange(W) - X0) / max(xr - X0, 1), 0, 1); w = u * u * (3 - 2 * u)
    fwd = np.arange(W) - d * w                                  # 원본 x → 새 x (단조 증가)
    mapx[y] = np.interp(np.arange(W), fwd, np.arange(W)).astype(np.float32)
out = cv2.remap(pm, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
a = out[..., 3:4]; out[..., :3] = np.where(a > 0, out[..., :3] * 255 / np.maximum(a, 1e-3), 0)
Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA').save(os.path.join(HERE, '..', 'parts', 'skirt.png'))
print('ok', 'D0', D0, 'Y1', Y1)
