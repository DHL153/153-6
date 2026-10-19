# 9 러스트 팔로메 조각 시트 1(27칸, 3072×2560, 자홍 배경, 6×5 칸) 자르기 — 키잉·덩어리 = 6 카르덴 cut_sheet, 이름 = 칸 번호(프롬프트 1 순서)
# python3 -I cut9.py  → pieces/<이름>.png + pieces/index.json + review/cut_overview.png
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'carden-rust', 'source'))
from cut_sheet import key, blobs
NAMES = ['pose', 'head', 'beard', 'face_neutral', 'face_happy', 'face_angry', 'face_focus', 'face_shout', 'face_effort', 'blink_half', 'blink_closed',
         'torso', 'hips', 'pauldron', 'upperN', 'foreN', 'fistN', 'upperF', 'foreF', 'legN', 'legF', 'thighN', 'thighF', 'bootN', 'bootF', 'sword', 'handOpen']
COLS, ROWS = 6, 5
if __name__ == '__main__':
    src = np.asarray(Image.open(os.path.join(HERE, 'sheets', 'parts1.png')).convert('RGB')); H, W = src.shape[:2]; cw, ch = W / COLS, H / ROWS
    rgba, alpha = key(src)
    bs = [b for b in blobs(alpha, minpx=30) if b['px'] > 30]
    def cell(b):   # 긴 조각(칼)은 위 끝이 든 칸
        y = b['y0'] + ch * .3 if b['y1'] - b['y0'] > ch * .9 else b['cy']; return int(min(ROWS - 1, y // ch)), int(min(COLS - 1, b['cx'] // cw))
    cells = {}
    for b in bs: cells.setdefault(cell(b), []).append(b)
    order = sorted(cells)
    print('cells', len(order), [(rc, len(v), [v_['px'] for v_ in v]) for rc, v in cells.items() if len(v) > 1])
    assert len(order) == len(NAMES), (len(order), order)
    os.makedirs(os.path.join(HERE, 'pieces'), exist_ok=True); idx = {}
    ov = Image.fromarray(np.dstack([src, np.full(src.shape[:2], 255, np.uint8)]), 'RGBA').convert('RGB'); d = ImageDraw.Draw(ov)
    for nm, rc in zip(NAMES, order):
        grp = cells[rc]; m = np.logical_or.reduce([b['mask'] for b in grp]); ys, xs = np.nonzero(m); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        p = rgba[y0:y1, x0:x1].copy(); p[..., 3] = (p[..., 3] * m[y0:y1, x0:x1]).astype(np.uint8)
        Image.fromarray(p, 'RGBA').save(os.path.join(HERE, 'pieces', nm + '.png')); idx[nm] = [int(x0), int(y0), int(x1 - x0), int(y1 - y0)]
        d.rectangle([x0, y0, x1, y1], outline=(0, 255, 0), width=3); d.text((x0, max(0, y0 - 14)), nm, fill=(255, 255, 255))
    json.dump(idx, open(os.path.join(HERE, 'pieces', 'index.json'), 'w'), ensure_ascii=False, indent=0)
    ov.resize((W // 2, H // 2)).save(os.path.join(HERE, 'review', 'cut_overview.png'))
    for k, v in idx.items(): print(f'{k:13s} at ({v[0]},{v[1]}) size {v[2]}×{v[3]}')
