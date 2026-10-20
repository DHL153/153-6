# 22 스카이 둘시네 조각 시트(프롬프트 1: 3072², 자홍 배경, 5×5 칸에 25조각) 자르기 (12 cut12 복사) — 키잉·덩어리 = 6 카르덴 cut_sheet, 이름 = 칸 번호(프롬프트 1 순서)
#   python3 -I cut12.py [sheets/sheet1.png] → pieces/<이름>.png + pieces/index.json   (10-20 07:40 시트 오기 전에 가짜 시트로 시험)
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'carden-rust', 'source'))
from cut_sheet import key, blobs
HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = ['pose', 'head', 'face_neutral', 'face_happy', 'face_angry', 'face_focus', 'face_shout', 'face_effort', 'blink_half', 'blink_closed',
         'pony', 'hammer', 'torso', 'padN', 'hips', 'flap', 'fistN', 'gFv', 'gFh', 'thighN', 'thighF', 'bootN', 'bootF', 'kneeN', 'kneeF']
GRID = 5
if __name__ == '__main__':
    fn = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'sheets', 'sheet1.png')
    out = os.environ.get('PIECES', os.path.join(HERE, 'pieces'))
    src = np.asarray(Image.open(fn).convert('RGB')); H, W = src.shape[:2]; cw, ch = W / GRID, H / GRID
    rgba, alpha = key(src)
    bs = [b for b in blobs(alpha, minpx=60) if b['px'] > 60]
    def cell(b):   # 긴 조각(망치)은 위 끝이 든 칸
        y = b['y0'] + ch * .3 if b['y1'] - b['y0'] > ch * .9 else b['cy']; return int(min(GRID - 1, y // ch)), int(min(GRID - 1, b['cx'] // cw))
    cells = {}
    for b in bs: cells.setdefault(cell(b), []).append(b)
    order = sorted(cells)
    print('cells', len(order), [(rc, len(v), [v_['px'] for v_ in v]) for rc, v in cells.items() if len(v) > 1])
    assert len(order) == len(NAMES), (len(order), order)
    os.makedirs(out, exist_ok=True); idx = {}
    for nm, rc in zip(NAMES, order):
        grp = cells[rc]; m = np.logical_or.reduce([b['mask'] for b in grp]); ys, xs = np.nonzero(m); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        p = rgba[y0:y1, x0:x1].copy(); p[..., 3] = (p[..., 3] * m[y0:y1, x0:x1]).astype(np.uint8)
        Image.fromarray(p, 'RGBA').save(os.path.join(out, nm + '.png')); idx[nm] = [int(x0), int(y0), int(x1 - x0), int(y1 - y0)]
    json.dump(idx, open(os.path.join(out, 'index.json'), 'w'), ensure_ascii=False, indent=0)
    for k, v in idx.items(): print(f'{k:13s} at ({v[0]},{v[1]}) size {v[2]}×{v[3]}')
