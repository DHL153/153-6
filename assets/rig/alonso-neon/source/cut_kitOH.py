# 11 머리 위 키트 시트(kitOH_v1, 20:38 DHL, 자홍 배경) 자르기 — 전체 자세 1 · 가까운 팔(은색 토시) 1 · 먼 팔(맨살) 1 · 칼 1
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'carden-rust', 'source'))
from cut_sheet import key, blobs
HERE = os.path.dirname(os.path.abspath(__file__))
if __name__ == '__main__':
    rgba, alpha = key(np.asarray(Image.open(os.path.join(HERE, 'sheets', 'kitOH_v1.png')).convert('RGB')))
    bs = [b for b in blobs(alpha) if (b['x1'] - b['x0']) * (b['y1'] - b['y0']) > 4000]
    bs.sort(key=lambda b: b['cx']); print([(b['x0'], b['y0'], b['x1'], b['y1']) for b in bs])
    names = ['kitPose', 'kitArmN', 'kitArmF', 'kitSword']
    os.makedirs(os.path.join(HERE, 'pieces', 'kitOH'), exist_ok=True); idx = {}
    for nm, b in zip(names, bs):
        p = rgba[b['y0']:b['y1'], b['x0']:b['x1']].copy(); p[..., 3] = (p[..., 3] * b['mask'][b['y0']:b['y1'], b['x0']:b['x1']]).astype(np.uint8)
        Image.fromarray(p, 'RGBA').save(os.path.join(HERE, 'pieces', 'kitOH', nm + '.png')); idx[nm] = [int(b['x0']), int(b['y0']), int(b['x1'] - b['x0']), int(b['y1'] - b['y0'])]
    json.dump(idx, open(os.path.join(HERE, 'pieces', 'kitOH', 'index.json'), 'w'), indent=0); print(idx)
