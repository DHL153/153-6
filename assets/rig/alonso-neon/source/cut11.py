# 11 네온 알론소 조각 시트(7칸, 자홍 배경) 자르기 — 키잉·덩어리는 6 카르덴 cut_sheet.py 함수 그대로, 순서는 줄(세로 가운데 묶음) → 왼쪽→오른쪽
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'carden-rust', 'source'))
from cut_sheet import key, blobs
HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = ['head', 'face_neutral', 'face_effort', 'face_shout', 'face_focus', 'face_happy', 'face_surprised',
         'face_grimace', 'face_closed', 'face_half', 'torso', 'torsoTurn', 'hips', 'pauldronN',
         'pauldronF', 'armNdown', 'armNup', 'armFdown', 'armFup', 'foreN', 'foreF',
         'gNv', 'gNh', 'gNu', 'gNd', 'gFv', 'gFh', 'gFu',
         'gFd', 'gBoth', 'thighN', 'thighF', 'shinN', 'shinF', 'kneeN',
         'kneeF', 'boot', 'bootHeel', 'sword']
if __name__ == '__main__':
    rgba, alpha = key(np.asarray(Image.open(os.path.join(HERE, 'sheets', 'sheet1.png')).convert('RGB')))
    bs = blobs(alpha)
    bs.sort(key=lambda b: b['cy']); rows = []
    for b in bs:   # 줄 묶기: 줄 위·아래 범위가 겹치면 같은 줄 (칼처럼 긴 조각은 위 끝 기준)
        y = b['y0'] + 60 if b['y1'] - b['y0'] > 250 else b['cy']
        for r in rows:
            if abs(r["y"] - y) < 110: r['b'].append(b); break
        else: rows.append({'y': y, 'b': [b]})
    order = [b for r in sorted(rows, key=lambda r: r['y']) for b in sorted(r['b'], key=lambda b: b['cx'])]
    print('pieces', len(order), 'rows', [len(r['b']) for r in sorted(rows, key=lambda r: r['y'])])
    os.makedirs(os.path.join(HERE, 'pieces'), exist_ok=True); idx = {}
    for i, b in enumerate(order):
        nm = NAMES[i] if i < len(NAMES) else f'extra{i}'
        p = rgba[b['y0']:b['y1'], b['x0']:b['x1']].copy(); p[..., 3] = (p[..., 3] * b['mask'][b['y0']:b['y1'], b['x0']:b['x1']]).astype(np.uint8)
        Image.fromarray(p, 'RGBA').save(os.path.join(HERE, 'pieces', nm + '.png')); idx[nm] = [int(b['x0']), int(b['y0']), int(b['x1'] - b['x0']), int(b['y1'] - b['y0'])]
    json.dump(idx, open(os.path.join(HERE, 'pieces', 'index.json'), 'w'), ensure_ascii=False, indent=0)
