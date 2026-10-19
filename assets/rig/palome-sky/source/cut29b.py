# 29 스카이 팔로메 추가 조각 시트 2(4칸, 3072×1024, 10-20 07:57) 자르기 → pieces/p2_<이름>.png
#   검수: 1번 = 첨부 1 과 다른 자세·다른 디자인(두 손 세운 칼, 어두운 갑옷) → 불합격 · 2번 먼 윗팔 합격(길이 둥근 끝 빼고 약 80 = 원화 어깨~팔꿈치, 아래 끝은 열린 소매 — 토시 밑에 숨김)
#   3번 먼 어깨 = 작은 판 조각(요청과 다름) → 불합격 · 4번 가까운 윗팔 = 남색 소매(둥근 끝 빼고 약 74, 원화 87 의 0.85 — 위 끝이 큰 어깨갑 밑이라 늘이지 않고 씀)
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
