# 23 스카이아크 산초 조각 시트 1(33칸, 3072², 자홍 배경, 6×6 칸) 자르기 — 키잉·덩어리 = 6 카르덴 cut_sheet, 이름 = 칸 번호(프롬프트 1 순서)
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'carden-rust', 'source'))
from cut_sheet import key, blobs
HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = ['pose', 'head', 'face_neutral', 'face_happy', 'face_angry', 'face_focus', 'face_shout', 'face_effort', 'blink_half', 'blink_closed',
         'torso', 'hips', 'padN', 'tailA', 'upperN', 'foreN', 'upperF', 'foreF', 'gNv', 'gNh', 'gFv', 'gFh',
         'thighN', 'thighF', 'kneeN', 'kneeF', 'shinN', 'shinF', 'bootN', 'bootF', 'sword', 'pony', 'tailB']   # 13 과 다른 곳: 14 = 목도리 위 꼬리(13 은 먼 어깨판) · 32 포니테일 · 33 목도리 아래 꼬리 (19:13 받은 33칸 시트 — 32칸 시트와 14·33칸만 다름)
if __name__ == '__main__':
    src = np.asarray(Image.open(os.path.join(HERE, 'sheets', 'sheet1.png')).convert('RGB')); H, W = src.shape[:2]; cw, ch = W / 6, H / 6
    rgba, alpha = key(src)
    bs = [b for b in blobs(alpha, minpx=30) if b['px'] > 30]   # 작은 조각(주먹·정강이 650~900px)
    def cell(b):   # 긴 조각(칼)은 위 끝이 든 칸
        y = b['y0'] + ch * .3 if b['y1'] - b['y0'] > ch * .9 else b['cy']; return int(min(5, y // ch)), int(min(5, b['cx'] // cw))
    cells = {}
    for b in bs: cells.setdefault(cell(b), []).append(b)
    order = sorted(cells)
    print('cells', len(order), [(rc, len(v), [v_['px'] for v_ in v]) for rc, v in cells.items() if len(v) > 1])
    assert len(order) == len(NAMES), (len(order), order)
    os.makedirs(os.path.join(HERE, 'pieces'), exist_ok=True); idx = {}
    for nm, rc in zip(NAMES, order):
        grp = cells[rc]; m = np.logical_or.reduce([b['mask'] for b in grp]); ys, xs = np.nonzero(m); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        p = rgba[y0:y1, x0:x1].copy(); p[..., 3] = (p[..., 3] * m[y0:y1, x0:x1]).astype(np.uint8)
        Image.fromarray(p, 'RGBA').save(os.path.join(HERE, 'pieces', nm + '.png')); idx[nm] = [int(x0), int(y0), int(x1 - x0), int(y1 - y0)]
    json.dump(idx, open(os.path.join(HERE, 'pieces', 'index.json'), 'w'), ensure_ascii=False, indent=0)
    for k, v in idx.items(): print(f'{k:13s} at ({v[0]},{v[1]}) size {v[2]}×{v[3]}')
