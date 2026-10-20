# 29 스카이 팔로메 추가 조각 시트 2(4칸, 3072×1024, 10-20 07:57) 자르기 → pieces/p2_<이름>.png
#   (10-20 08:09 DHL: 07:57 시트는 네온 팔로메 것이었음 → 09:00 스카이 시트로 다시: 1번 = 원화 IoU 0.993, 2·4번 윗팔 합격(둥근 끝 사이 86·82 ≈ 원화 80·87), 3번 어깨 = 시트 3 과 같은 그림)
import os, sys, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'carden-rust', 'source'))
from cut_sheet import key, blobs
src = np.asarray(Image.open(os.path.join(HERE, 'sheets', 'parts2.png')).convert('RGB')); rgba, alpha = key(src)
bs = sorted([b for b in blobs(alpha, minpx=30) if b['px'] > 200], key=lambda b: b['cx'])
for nm, b in zip(['pose2', 'upperF2', 'shoulderF2', 'upperN2'], bs):
    m = b['mask']; ys, xs = np.nonzero(m); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    p = rgba[y0:y1, x0:x1].copy(); p[..., 3] = (p[..., 3] * m[y0:y1, x0:x1]).astype(np.uint8)
    Image.fromarray(p, 'RGBA').save(os.path.join(HERE, 'pieces', f'p2_{nm}.png')); print(nm, x1 - x0, y1 - y0)
